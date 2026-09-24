"""One process serves the calculation API and compiled React UI; no user-row persistence."""
from time import perf_counter
from backend.app.bootstrap import STARTED as _import_started
_main_import_started = perf_counter()
from backend.app.diagnostics import timed, measure
from functools import lru_cache
from pathlib import Path
from threading import BoundedSemaphore, RLock
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.contracts import APIError, ENGINE_VERSION, SCHEMA_VERSION, ForecastRequest, ForecastResult, SampleCatalog, SampleRequest
from backend.app.data.sample import generate_sample
from backend.app.data.validation import validate_dataset
from backend.app.forecasting.engine import forecast
from backend.app.planning.contracts import PlanRequest, PlanResult, PlanSampleRequest
from backend.app.planning.engine import plan
from backend.app.planning.presentation import decisions
_workflow_import_started = perf_counter()
from backend.app.data.workflow_api import dataset_for, attach_draft, imported_constraints, install as install_workflow
from backend.app.diagnostics import startup_measurement, instrument_response_fields
startup_measurement('workflow_import', perf_counter()-_workflow_import_started)

MAX_BODY_BYTES = 32 * 1024 * 1024
calculation_slot = BoundedSemaphore(1)
_sample_lock = RLock()
_setup_started = perf_counter()
_construction_started = perf_counter()
app = FastAPI(title="Demand and Supply Planning Intelligence", version=ENGINE_VERSION,
              description="Synthetic portfolio. Evaluated forecasts and independently validated purchasing, allocation and payment plans.")
startup_measurement('fastapi_construction', perf_counter()-_construction_started)


class BodyLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        length = headers.get(b"content-length", b"0")
        if not length.isdigit() or int(length) > MAX_BODY_BYTES:
            response = JSONResponse(status_code=413, content={"code": "body_limit", "message": "Request exceeds the 32 MiB limit.", "issues": []})
            return await response(scope, receive, send)
        chunks, total = [], 0
        with measure('request_body'):
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                total += len(message.get("body", b""))
                if total > MAX_BODY_BYTES:
                    response = JSONResponse(status_code=413, content={"code": "body_limit", "message": "Request exceeds the 32 MiB limit.", "issues": []})
                    return await response(scope, receive, send)
                chunks.append(message.get("body", b""))
                if not message.get("more_body", False):
                    break
        delivered = False
        async def limited_receive():
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
        await self.app(scope, limited_receive, send)


app.add_middleware(BodyLimit)
from backend.app.diagnostics import TimingHeaders
app.add_middleware(TimingHeaders)


@app.exception_handler(RequestValidationError)
async def schema_error(request: Request, exc):
    # Pydantic's default response echoes invalid inputs. Return paths/types only, never rows.
    issues = [{"severity": "error", "code": "schema", "message": ".".join(map(str, e["loc"])) + ": " + e["type"], "count": 1} for e in exc.errors()[:30]]
    return JSONResponse(status_code=422, content={"code": "invalid_schema", "message": "Request does not match the supported contract.", "issues": issues})


@lru_cache(maxsize=2)
@timed('sample_input')
def _sample(size):
    from backend.app.planning.preparation import register
    data = generate_sample(size)
    issues = validate_dataset(data)
    register(size, data)
    return data, issues


def sample(size):
    # lru_cache permits duplicate concurrent misses. Publish one exact bundled
    # object so initial catalog/forecast requests agree with reuse registration.
    with _sample_lock:
        return _sample(size)


def calculate(data, sku, location_id, issues=None):
    if not calculation_slot.acquire(blocking=False):
        return JSONResponse(status_code=429, headers={"Retry-After": "2"}, content=APIError(code="busy", message="A calculation is running. Please retry shortly.").model_dump())
    try:
        issues = validate_dataset(data) if issues is None else issues
        if any(i.severity == "error" for i in issues):
            return JSONResponse(status_code=422, content=APIError(code="invalid_dataset", message="Resolve data validation errors before calculation.", issues=issues).model_dump())
        if not any(a.sku == sku and a.location_id == location_id for a in data.assortment):
            return JSONResponse(status_code=422, content=APIError(code="unknown_series", message="Select an existing SKU-store assortment; the DC has no retail demand.").model_dump())
        return forecast(data, sku, location_id, issues)
    except TimeoutError:
        return JSONResponse(status_code=503, content=APIError(code="runtime_budget", message="Calculation exceeded its 30-second budget; no partial result is presented.").model_dump())
    finally:
        calculation_slot.release()


@app.get("/api/health")
def health():
    return {"status": "ok", "engine_version": ENGINE_VERSION, "schema_version": SCHEMA_VERSION, "capabilities": ["forecast", "planning"]}


@app.get("/api/sample", response_model=SampleCatalog)
def catalog(request: Request, size: Literal["fixture", "full"] = "fixture"):
    data, issues, _ = dataset_for(request,size)
    issues = validate_dataset(data) if issues is None else issues
    return SampleCatalog(dataset_id=data.dataset_id, as_of=data.settings.as_of, products=data.products,
                         locations=[l for l in data.locations if l.kind == "store"], history_rows=len(data.demand_history), warnings=issues)


ERRORS = {422: {"model": APIError}, 429: {"model": APIError}, 503: {"model": APIError}}


@app.post("/api/forecast/sample", response_model=ForecastResult, responses=ERRORS)
def sample_forecast(request: SampleRequest, http: Request):
    data, issues, _ = dataset_for(http,request.size)
    return calculate(data, request.sku, request.location_id, issues)


@app.post("/api/forecast", response_model=ForecastResult, responses=ERRORS)
def custom_forecast(request: ForecastRequest):
    return calculate(request.dataset, request.sku, request.location_id)


@timed('planning')
def calculate_plan(data, issues=None, review=None):
    if not calculation_slot.acquire(blocking=False):
        return JSONResponse(status_code=429, headers={'Retry-After': '2'}, content=APIError(code='busy', message='A calculation is running. Please retry shortly.').model_dump())
    try:
        return plan(data,validated_issues=issues,review=review)
    finally:
        calculation_slot.release()


@app.post('/api/plan/sample', response_model=PlanResult, responses=ERRORS)
@timed('route')
def sample_plan(request: PlanSampleRequest, http: Request, include_stock: bool = False):
    data, issues, context = dataset_for(http,request.size)
    result=calculate_plan(data,issues,imported_constraints(http))
    if isinstance(result,PlanResult):
        with measure('response_construction'):
            result=result.model_copy(update={'provenance':context})
            return decisions(attach_draft(http,data,result,context),include_stock)
    return result


@app.post('/api/plan', response_model=PlanResult, responses=ERRORS)
def custom_plan(request: PlanRequest, include_stock: bool = False):
    result=calculate_plan(request.dataset)
    return decisions(result,include_stock) if isinstance(result,PlanResult) else result


# Stateless sample scenario APIs use the same admission control as planning.
_scenario_import_started = perf_counter()
from backend.app.scenarios.contracts import BaselineResult, ScenarioRequest, ScenarioResult, DetailRequest, ScenarioDetail, CaptureRequest
from backend.app.scenarios.engine import baseline_result, compare, detail, capture
startup_measurement('scenario_import', perf_counter()-_scenario_import_started)


def scenario_call(fn, request, http=None):
    if not calculation_slot.acquire(blocking=False):
        return JSONResponse(status_code=429, headers={'Retry-After':'2'}, content={'message':'A calculation is running. Please retry shortly.'})
    try:
        size=request.size if isinstance(request, (PlanSampleRequest,CaptureRequest)) else request.baseline.size
        if http is not None:
            data,issues,context=dataset_for(http,size)
        else:
            data,issues=sample(size);context=None
        review=imported_constraints(http) if http is not None else None
        if isinstance(request, PlanSampleRequest): return fn(size,data,validated_issues=issues,review=review,context=context)
        if fn is compare:return fn(data,request,review=review,context=context)
        return fn(data,request,context=context)
    except ValueError as error:
        return JSONResponse(status_code=422,content={'code':'invalid_scenario','message':str(error)})
    except TimeoutError:
        return JSONResponse(status_code=503,content={'code':'scenario_runtime','message':'Scenario exceeded its calculation budget. No partial plan is executable.'})
    finally:
        calculation_slot.release()


@app.post('/api/scenarios/baseline',response_model=BaselineResult,responses=ERRORS)
def scenario_baseline(request: PlanSampleRequest, http: Request):
    return scenario_call(baseline_result,request,http)


@app.post('/api/scenarios/capture',response_model=BaselineResult,responses=ERRORS)
def scenario_capture(request: CaptureRequest, http: Request):
    return scenario_call(capture,request,http)


@app.post('/api/scenarios/compare',response_model=ScenarioResult,responses=ERRORS)
def scenario_compare(request: ScenarioRequest, http: Request):
    return scenario_call(compare,request,http)


@app.post('/api/scenarios/detail',response_model=ScenarioDetail,responses=ERRORS)
def scenario_detail(request: DetailRequest, http: Request):
    return scenario_call(detail,request,http)


install_workflow(app)

DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
# backend/app -> repository root is parents[2].
if DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")


@app.get("/", include_in_schema=False)
def index():
    if not (DIST / "index.html").is_file():
        return JSONResponse(status_code=503, content={"message": "Frontend not built. Run npm ci && npm run build in frontend/."})
    return FileResponse(DIST / "index.html")


instrument_response_fields(app)
startup_measurement('fastapi_setup', perf_counter()-_setup_started)
startup_measurement('application_import', perf_counter()-_main_import_started)
startup_measurement('module_bootstrap', perf_counter()-_import_started)
