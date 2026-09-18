"""Small private-reference API for local workbook/review workflows."""
import gzip
import json
from secrets import token_urlsafe
from typing import Literal
from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from pydantic import Field
from backend.app.contracts import Contract, Dataset, SampleCatalog
from backend.app.data.storage import store, configuration, TOKEN, ObjectReference, ObjectUnavailable
from backend.app.data.workbook import template, parse, WorkbookError, WorkbookIssue, MAX_FILE, MIME
from backend.app.data.accepted import create_snapshot, snapshot_bytes, read_snapshot, export_workbook
from backend.app.planning.contracts import PlanResult
from backend.app.planning.review import Draft, ReviewConflict, new_draft, decide, regenerate, accept
from backend.app.scenarios.engine import dataset_hash
from backend.app.scenarios.contracts import ScenarioRequest, DetailRequest, Actions, ScenarioDetail
from backend.app.planning.constraints import ReviewConstraints, business_key
from backend.app.data.reconciliation import Execution, reconcile
from fastapi.concurrency import run_in_threadpool

router=APIRouter(prefix='/api/workflow')
COOKIE='planning_session'


def owner(request):
    value=request.cookies.get(COOKIE,'')
    if not TOKEN.fullmatch(value): raise HTTPException(401,'Start a private workbook session first.')
    return value


def available():
    if not configuration()['enabled']: raise HTTPException(503,configuration()['message'])


def encoded(value):
    return gzip.compress(json.dumps(value,separators=(',',':')).encode(),mtime=0)


def load(request,reference,kind):
    if not TOKEN.fullmatch(reference): raise ObjectUnavailable('Object is unavailable or expired.')
    return json.loads(gzip.decompress(store.get(owner(request),ObjectReference(object_id=reference),kind)))


def dataset_for(request,size='fixture'):
    reference=request.headers.get('X-Dataset-Ref')
    if reference:
        available()
        return Dataset.model_validate(load(request,reference,'dataset')['dataset']), None
    from backend.app.main import sample
    return sample(size)


def attach_draft(request,data,result):
    # Review session persistence is never substituted for a live calculation.
    if not configuration()['enabled'] or not TOKEN.fullmatch(request.cookies.get(COOKIE,'')):
        return result
    draft=new_draft(data,result)
    apply_imported(draft,request)
    source={'size':'full' if len(data.products)>10 else 'fixture','dataset_ref':request.headers.get('X-Dataset-Ref')}
    ref=store.put(owner(request),encoded({'source':source,'draft':draft.model_dump(mode='json')}),'draft')
    return result.model_copy(update={'review_id':ref.object_id})


def apply_imported(draft,request):
    result=draft.result
    draft.input_source='uploaded' if request.headers.get('X-Dataset-Ref') else 'bundled'
    imported=imported_constraints(request)
    if imported is not None:
        draft.execution_rejections=sorted(imported.rejected)
        draft.execution_remainders=[a.model_copy(deep=True) for a in imported.purchases+imported.movements]
        from backend.app.planning.review import Decision
        from datetime import datetime,timezone
        record=load(request,request.headers['X-Dataset-Ref'],'dataset')
        for action in imported.purchases+imported.movements:
            draft.decisions.append(Decision(source_run_id=result.run_id,input_hash=result.input_hash,assumption_version=draft.assumption_version,
                action_type='purchase' if hasattr(action,'offer_id') else 'movement',business_key=business_key(action),original=action,original_quantity=action.units,
                reviewed_quantity=action.units,status='accepted',timestamp=datetime.now(timezone.utc),note='Unconfirmed remainder from supplied accepted snapshot.',disposition='retained' if result.proposed and result.proposed.replay.feasible else 'conflicted'))
        for raw in record.get('rejected_actions',[]):
            from backend.app.planning.contracts import Purchase,Movement
            action=(Purchase if 'offer_id' in raw else Movement).model_validate(raw)
            draft.decisions.append(Decision(source_run_id=result.run_id,input_hash=result.input_hash,assumption_version=draft.assumption_version,
                action_type='purchase' if hasattr(action,'offer_id') else 'movement',business_key=business_key(action),original=action,original_quantity=action.units,
                status='rejected',timestamp=datetime.now(timezone.utc),note='Confirmed transaction replaces this proposal.',disposition='retained'))


def imported_constraints(request):
    reference=request.headers.get('X-Dataset-Ref')
    if not reference: return None
    record=load(request,reference,'dataset')
    raw=record.get('constraints')
    if raw is None: return None
    from backend.app.planning.contracts import Purchase,Movement
    return ReviewConstraints(purchases=[Purchase.model_validate(a) for a in raw['purchases']],movements=[Movement.model_validate(a) for a in raw['movements']],rejected=set(raw['rejected']))


class ImportResult(Contract):
    reference: ObjectReference | None = None
    catalog: SampleCatalog | None = None
    issues: list[WorkbookIssue]
    measurements: dict = Field(default_factory=dict)
    input_hash: str | None = None


class ReviewView(Contract):
    reference: str
    revision: str
    state: str
    decisions: list[dict]
    failures: list[dict]
    accepted_version: str | None = None
    measurements: dict = Field(default_factory=dict)
    dataset_ref: str | None = None


class DecisionRequest(Contract):
    revision: str
    action_id: str
    status: Literal['accepted','rejected','edited_quantity','draft']
    quantity: int | None = Field(default=None,strict=True)
    note: str = Field(default='',max_length=1000)


class RevisionRequest(Contract):
    revision: str
    acknowledge_shortfalls: bool = False


def view(reference,draft,measurements=None):
    return ReviewView(reference=reference,revision=draft.revision,state=draft.state,
        decisions=[d.model_dump(mode='json') for d in draft.decisions],
        failures=[f.model_dump(mode='json') for f in draft.failures],accepted_version=draft.accepted_version,measurements=measurements or {})


def draft_for(request,reference):
    available();record=load(request,reference,'draft');draft=Draft.model_validate(record['draft'])
    if 'snapshot' in record:
        data=Dataset.model_validate(record['snapshot']['dataset'])
    elif record['source'].get('dataset_ref'):
        data=Dataset.model_validate(load(request,record['source']['dataset_ref'],'dataset')['dataset'])
    else:
        from backend.app.main import sample
        data=sample(record['source']['size'])[0]
    return record,draft,data


def save_draft(request,reference,record,draft,**extra):
    record={**record,**extra,'draft':draft.model_dump(mode='json')}
    ref=store.put(owner(request),encoded(record),'draft')
    # Previous draft tokens become invalid, preventing acceptance of stale revisions.
    store.delete(owner(request),ObjectReference(object_id=reference))
    return ref.object_id


@router.get('/session')
def session(request:Request,response:Response):
    if not TOKEN.fullmatch(request.cookies.get(COOKIE,'')):
        response.set_cookie(COOKIE,token_urlsafe(32),httponly=True,samesite='strict',secure=request.url.scheme=='https',max_age=3600)
    return {**configuration(),'max_file_bytes':MAX_FILE,'max_expanded_bytes':160*1024*1024,'max_rows':170000,'max_skus':60,'max_locations':5,'max_suppliers':12}


@router.delete('/session')
def reset(request:Request):
    store.reset(owner(request));return {'reset':True}


@router.get('/template/{size}')
def download_template(size:Literal['blank','fixture']):
    from backend.app.main import sample
    content=template(None if size=='blank' else sample(size)[0])
    return Response(content,media_type=MIME,headers={'Content-Disposition':f'attachment; filename="planning-{size}.xlsx"','Cache-Control':'no-store'})


@router.put('/import',response_model=ImportResult)
async def import_workbook(request:Request):
    available();session=owner(request)
    if request.headers.get('X-Server-Processing')!='confirmed': raise HTTPException(422,'Confirm server processing before uploading.')
    content=await request.body()
    if len(content)>MAX_FILE: raise HTTPException(413,'Workbook exceeds 16 MiB.')
    upload=store.put(session,content,'upload')
    try:
        from urllib.parse import unquote
        data,issues,measurements=await run_in_threadpool(parse,store.get(session,upload,'upload'),unquote(request.headers.get('X-Filename','data.xlsx')))
        record={'dataset':data.model_dump(mode='json'),'warnings':[i.model_dump() for i in issues]}
        if measurements['reconciliation']:
            accepted_ref=request.headers.get('X-Accepted-Ref')
            if not accepted_ref: raise WorkbookError([WorkbookIssue(sheet='Reconciliation',field='external_id',code='missing_accepted_snapshot',guidance='Supply the portable accepted snapshot before reconciling execution IDs.')])
            previous=load(request,accepted_ref,'draft')
            if 'snapshot' not in previous: raise WorkbookError([WorkbookIssue(sheet='Reconciliation',field='external_id',code='unaccepted_snapshot',guidance='Reconciliation requires an accepted portable snapshot.')])
            from backend.app.data.accepted import AcceptedSnapshot
            snapshot=AcceptedSnapshot.model_validate(previous['snapshot'])
            locks,evidence=reconcile(data,snapshot,[Execution.model_validate(r) for r in measurements['reconciliation']])
            record['constraints']={'purchases':[a.model_dump(mode='json') for a in locks.purchases],'movements':[a.model_dump(mode='json') for a in locks.movements],'rejected':sorted(locks.rejected)}
            record['rejected_actions']=[a.model_dump(mode='json') for a in snapshot.draft.result.proposed.purchases+snapshot.draft.result.proposed.movements if business_key(a) in locks.rejected]
            measurements['reconciliation']=evidence
        elif any(a.external_id.startswith('DSP-') for a in data.open_orders+data.open_transfers):
            raise WorkbookError([WorkbookIssue(sheet='Reconciliation',field='external_id',code='missing_execution',guidance='Exported DSP identifiers require explicit Reconciliation rows and the accepted snapshot.')])
        ref=store.put(session,encoded(record),'dataset')
        measurements['upload_body_bytes']=len(content)
        return ImportResult(reference=ref,catalog=SampleCatalog(dataset_id=data.dataset_id,as_of=data.settings.as_of,products=data.products,locations=[l for l in data.locations if l.kind=='store'],history_rows=len(data.demand_history),warnings=[]),issues=issues,measurements=measurements,input_hash=dataset_hash(data))
    except WorkbookError as error:
        return JSONResponse(status_code=422,content={'issues':[i.model_dump() for i in error.issues],'message':str(error)})
    except ReviewConflict as error:
        return JSONResponse(status_code=422,content={'issues':[WorkbookIssue(sheet='Reconciliation',field='external_id',code=f.code,guidance=f.message).model_dump() for f in error.failures],'message':'Reconciliation failed. Correct the explicit execution evidence.'})
    finally:
        store.delete(session,upload)


@router.get('/review/{reference}',response_model=ReviewView)
def review_view(reference:str,request:Request):
    _,draft,_=draft_for(request,reference);return view(reference,draft)


@router.get('/review/{reference}/plan',response_model=PlanResult)
def review_plan(reference:str,request:Request):
    _,draft,_=draft_for(request,reference)
    return draft.result.model_copy(update={'review_id':reference})


@router.post('/review/{reference}/decision',response_model=ReviewView)
def decision(reference:str,body:DecisionRequest,request:Request):
    with store.lock:
        record,draft,data=draft_for(request,reference)
        next_draft=decide(draft,data,body.revision,body.action_id,body.status,body.quantity,body.note)
        ref=save_draft(request,reference,record,next_draft)
        return view(ref,next_draft)


def guarded(function):
    from backend.app.main import calculation_slot
    if not calculation_slot.acquire(blocking=False): raise HTTPException(429,'A calculation is running.',headers={'Retry-After':'2'})
    try: return function()
    finally: calculation_slot.release()


@router.post('/review/{reference}/regenerate',response_model=ReviewView)
def rerun(reference:str,body:RevisionRequest,request:Request):
    def calculate():
        with store.lock:
            record,draft,data=draft_for(request,reference)
            next_draft=regenerate(draft,data,body.revision)
            ref=save_draft(request,reference,record,next_draft)
            return view(ref,next_draft)
    return guarded(calculate)


@router.post('/review/{reference}/accept',response_model=ReviewView)
def final_accept(reference:str,body:RevisionRequest,request:Request):
    def calculate():
        with store.lock:
            record,draft,data=draft_for(request,reference)
            accepted,_,versions=accept(draft,data,body.revision,body.acknowledge_shortfalls)
            try: snapshot=create_snapshot(data,accepted,versions)
            except ValueError as error: raise HTTPException(422,str(error)) from error
            binary,raw_size=snapshot_bytes(snapshot);workbook=export_workbook(snapshot)
            ref=save_draft(request,reference,record,accepted,snapshot=snapshot.model_dump(mode='json'))
            return view(ref,accepted,{'snapshot_compressed_bytes':len(binary),'snapshot_uncompressed_bytes':raw_size,'export_bytes':len(workbook)})
    return guarded(calculate)


@router.get('/review/{reference}/download/{kind}')
def download(reference:str,kind:Literal['workbook','snapshot'],request:Request):
    record,draft,_=draft_for(request,reference)
    if draft.state not in ('accepted','read_only') or 'snapshot' not in record: raise HTTPException(409,'Current plan is stale or not finally accepted.')
    from backend.app.data.accepted import AcceptedSnapshot
    snapshot=AcceptedSnapshot.model_validate(record['snapshot'])
    content=export_workbook(snapshot) if kind=='workbook' else snapshot_bytes(snapshot)[0]
    suffix='xlsx' if kind=='workbook' else 'plan.json.gz'
    return Response(content,media_type=MIME if kind=='workbook' else 'application/gzip',headers={'Content-Disposition':f'attachment; filename="accepted-{draft.accepted_version}.{suffix}"','Cache-Control':'no-store'})


@router.put('/snapshot',response_model=ReviewView)
async def reopen(request:Request):
    available()
    if request.headers.get('X-Server-Processing')!='confirmed': raise HTTPException(422,'Confirm server processing before importing.')
    try: snapshot=read_snapshot(await request.body())
    except ValueError as error: raise HTTPException(422,str(error)) from error
    draft=snapshot.draft.model_copy(update={'state':'read_only'})
    ref=store.put(owner(request),encoded({'draft':draft.model_dump(mode='json'),'snapshot':snapshot.model_dump(mode='json')}),'draft')
    source=store.put(owner(request),encoded({'dataset':snapshot.dataset.model_dump(mode='json')}),'dataset')
    return view(ref.object_id,draft).model_copy(update={'dataset_ref':source.object_id})


@router.post('/review/{reference}/new-draft',response_model=ReviewView)
def fork(reference:str,body:RevisionRequest,request:Request):
    record,draft,data=draft_for(request,reference)
    if draft.revision!=body.revision: raise HTTPException(409,'Draft version changed.')
    next_draft=new_draft(data,draft.result.model_copy(update={'review_id':None}),draft.scenario)
    next_draft.execution_rejections=list(draft.execution_rejections)
    next_draft.execution_remainders=[a.model_copy(deep=True) for a in draft.execution_remainders]
    next_draft.input_source='portable'
    next_draft.state='stale' # Explicit fresh solve/replay is required after reopening.
    source=store.put(owner(request),encoded({'dataset':data.model_dump(mode='json')}),'dataset')
    ref=store.put(owner(request),encoded({'source':{'dataset_ref':source.object_id},'draft':next_draft.model_dump(mode='json')}),'draft')
    return view(ref.object_id,next_draft)


@router.post('/scenario',response_model=PlanResult)
def scenario_draft(body:ScenarioRequest,request:Request):
    available()
    def calculate():
        from backend.app.scenarios.engine import prepare
        from backend.app.planning.engine import plan
        data,_=dataset_for(request,body.baseline.size)
        changed,definition,_,_,prepared,_=prepare(data,body)
        result=plan(changed,prepared_forecasts=prepared,review=imported_constraints(request))
        draft=new_draft(data,result,definition)
        apply_imported(draft,request)
        ref=store.put(owner(request),encoded({'source':{'size':body.baseline.size,'dataset_ref':request.headers.get('X-Dataset-Ref')},'draft':draft.model_dump(mode='json')}),'draft')
        return result.model_copy(update={'review_id':ref.object_id})
    return guarded(calculate)


class EvidenceRequest(Contract):
    sku: str
    location_id: str
    action_id: str | None = None


@router.post('/review/{reference}/detail',response_model=ScenarioDetail)
def review_detail(reference:str,body:EvidenceRequest,request:Request):
    def calculate():
        from backend.app.scenarios.engine import snapshot,detail,actions_of,digest
        _,draft,data=draft_for(request,reference)
        if not draft.result.proposed: raise HTTPException(409,'No policy available for inspection.')
        actions=actions_of(draft.result.proposed)
        selected=DetailRequest(baseline=snapshot('fixture',data,Actions()),scenario=draft.scenario,policy='replanned',actions=actions,expected_action_hash=digest(actions),**body.model_dump())
        return detail(data,selected)
    return guarded(calculate)


def install(app):
    app.include_router(router)
    @app.exception_handler(ObjectUnavailable)
    async def missing(request,error): return JSONResponse(status_code=404,content={'message':str(error)})
    @app.exception_handler(ReviewConflict)
    async def conflict(request,error): return JSONResponse(status_code=409,content={'message':str(error),'failures':[f.model_dump(mode='json') for f in error.failures]})
