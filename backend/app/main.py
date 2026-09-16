"""One process serves the calculation API and compiled React UI; no user-row persistence."""
from functools import lru_cache
from pathlib import Path
from threading import BoundedSemaphore
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.contracts import APIError, ENGINE_VERSION, SCHEMA_VERSION, ForecastRequest, ForecastResult, SampleCatalog, SampleRequest
from backend.app.data.sample import generate_sample
from backend.app.data.validation import validate_dataset
from backend.app.forecasting.engine import forecast

MAX_BODY_BYTES = 32 * 1024 * 1024
calculation_slot = BoundedSemaphore(1)
app = FastAPI(title="Demand and Supply Planning Intelligence", version=ENGINE_VERSION,
              description="Synthetic portfolio. Forecasts only in Pass 1. Operational inputs are processed on the server.")


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


@app.exception_handler(RequestValidationError)
async def schema_error(request: Request, exc):
    # Pydantic's default response echoes invalid inputs. Return paths/types only, never rows.
    issues = [{"severity": "error", "code": "schema", "message": ".".join(map(str, e["loc"])) + ": " + e["type"], "count": 1} for e in exc.errors()[:30]]
    return JSONResponse(status_code=422, content={"code": "invalid_schema", "message": "Request does not match the supported contract.", "issues": issues})


@lru_cache(maxsize=2)
def sample(size):
    data = generate_sample(size)
    return data, validate_dataset(data)


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
    return {"status": "ok", "engine_version": ENGINE_VERSION, "schema_version": SCHEMA_VERSION, "capabilities": ["forecast"]}


@app.get("/api/sample", response_model=SampleCatalog)
def catalog(size: Literal["fixture", "full"] = "fixture"):
    data, issues = sample(size)
    return SampleCatalog(dataset_id=data.dataset_id, as_of=data.settings.as_of, products=data.products,
                         locations=[l for l in data.locations if l.kind == "store"], history_rows=len(data.demand_history), warnings=issues)


ERRORS = {422: {"model": APIError}, 429: {"model": APIError}, 503: {"model": APIError}}


@app.post("/api/forecast/sample", response_model=ForecastResult, responses=ERRORS)
def sample_forecast(request: SampleRequest):
    data, issues = sample(request.size)
    return calculate(data, request.sku, request.location_id, issues)


@app.post("/api/forecast", response_model=ForecastResult, responses=ERRORS)
def custom_forecast(request: ForecastRequest):
    return calculate(request.dataset, request.sku, request.location_id)


DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
# backend/app -> repository root is parents[2].
if DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")


@app.get("/", include_in_schema=False)
def index():
    if not (DIST / "index.html").is_file():
        return JSONResponse(status_code=503, content={"message": "Frontend not built. Run npm ci && npm run build in frontend/."})
    return FileResponse(DIST / "index.html")
