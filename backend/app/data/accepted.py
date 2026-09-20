"""Accepted workbook and checksummed portable snapshot; no order execution."""
import gzip
from io import BytesIO
import json
from hashlib import sha256
from typing import Literal
from pydantic import Field
from backend.app.contracts import Contract, Dataset, SCHEMA_VERSION
from backend.app.data.workbook import append
from backend.app.planning.review import Draft
from backend.app.planning.constraints import business_key
from backend.app.scenarios.engine import digest, dataset_hash
from backend.app.simulation.replay import week, cents

SNAPSHOT_VERSION = 'accepted-plan-1'
MAX_SNAPSHOT = 64 * 1024 * 1024


class AcceptedSnapshot(Contract):
    version: Literal['accepted-plan-1'] = SNAPSHOT_VERSION
    dataset: Dataset
    draft: Draft
    forecast_versions: dict[str, str]
    external_ids: dict[str, str]
    checksum: str


def create_snapshot(data, draft, versions):
    if draft.state != 'accepted' or not draft.accepted_version or not draft.result.proposed or not draft.result.proposed.replay.feasible:
        raise ValueError('Only a finally accepted, independently valid plan can be exported.')
    actions = draft.result.proposed.purchases+draft.result.proposed.movements
    ids = {a.action_id: 'DSP-'+sha256((draft.accepted_version+business_key(a)).encode()).hexdigest()[:40] for a in actions}
    body = dict(version=SNAPSHOT_VERSION, dataset=data.model_dump(mode='json'), draft=draft.model_dump(mode='json'), forecast_versions=versions, external_ids=ids)
    result=AcceptedSnapshot(**body, checksum=digest(body))
    raw=result.model_dump_json().encode()
    if len(raw)>MAX_SNAPSHOT or len(gzip.compress(raw,mtime=0))>16*1024*1024:
        raise ValueError('Accepted snapshot exceeds the supported 64 MiB expanded / 16 MiB compressed portable limit.')
    return result


def snapshot_bytes(snapshot):
    raw = snapshot.model_dump_json().encode()
    return gzip.compress(raw, mtime=0), len(raw)


def read_snapshot(content):
    if len(content) > 16 * 1024 * 1024: raise ValueError('Compressed snapshot exceeds 16 MiB.')
    try:
        with gzip.GzipFile(fileobj=BytesIO(content)) as stream:
            raw = stream.read(MAX_SNAPSHOT+1)
        if len(raw)>MAX_SNAPSHOT: raise ValueError('Snapshot exceeds the 64 MiB expanded limit.')
        snapshot=AcceptedSnapshot.model_validate_json(raw)
    except Exception as error:
        raise ValueError('Unsupported, corrupted or oversized portable snapshot.') from error
    if snapshot.checksum != digest(snapshot.model_dump(mode='json',exclude={'checksum'})):
        raise ValueError('Snapshot checksum does not match its contents.')
    if snapshot.draft.state!='accepted' or not snapshot.draft.accepted_version or snapshot.draft.base_input_hash!=dataset_hash(snapshot.dataset):
        raise ValueError('Snapshot accepted version or dataset hash is inconsistent.')
    expected=create_snapshot(snapshot.dataset,snapshot.draft,snapshot.forecast_versions)
    if expected.external_ids!=snapshot.external_ids: raise ValueError('Snapshot export identifiers do not reconcile.')
    # Checksums are corruption checks, not signatures. Reopen is read-only; a new
    # editable draft must pass fresh calculation/replay before another acceptance.
    return snapshot


def export_workbook(snapshot):
    from openpyxl import Workbook
    draft=snapshot.draft
    if draft.state!='accepted' or not draft.result.proposed or not draft.result.proposed.replay.feasible:
        raise ValueError('Only a finally accepted plan can be exported.')
    policy=draft.result.proposed; ledger=policy.replay
    if sum(cents(p.value) for p in policy.purchases)!=cents(ledger.summary.commitments) or sum(cents(p.amount) for p in ledger.payments)!=cents(ledger.summary.payments):
        raise ValueError('Accepted action/payment totals do not reconcile.')
    wb=Workbook(write_only=True)
    def table(name,rows,headers):
        ws=wb.create_sheet(name);append(ws,headers)
        for row in rows:append(ws,[row.get(key) for key in headers])
    table('Summary',[{'metric':k,'value':v} for k,v in ledger.summary.model_dump().items()],['metric','value'])
    purchases=[]
    for action in policy.purchases:
        row=action.model_dump(mode='json');row['external_id']=snapshot.external_ids[action.action_id];row['commitment_week']=str(week(action.order_date))
        for kind in ('deposit','balance'):
            payment=next(p for p in ledger.payments if p.reference==action.action_id and p.kind==kind)
            row[kind+'_date']=str(payment.due_date);row[kind+'_amount']=payment.amount
        purchases.append(row)
    table('PurchaseActions',purchases,['action_id','external_id','sku','supplier_id','offer_id','destination','units','order_date','dispatch_date','arrival_date','value','commitment_week','deposit_date','deposit_amount','balance_date','balance_amount','reason'])
    movements=[dict(**a.model_dump(mode='json'),external_id=snapshot.external_ids[a.action_id],fee_group=f'{a.source}-{a.destination}-{a.dispatch_date}') for a in policy.movements]
    table('MovementActions',movements,['action_id','external_id','sku','source','destination','units','dispatch_date','arrival_date','fee_group','reason'])
    table('UnresolvedExceptions',[e.model_dump(mode='json') for e in draft.result.exceptions],['code','message','sku','location_id','supplier_id','day','action_id'])
    table('PaymentSchedule',[p.model_dump(mode='json') for p in ledger.payments],['reference','due_date','kind','amount'])
    table('WeeklyFunding',[w.model_dump(mode='json') for w in ledger.cash],list(type(ledger.cash[0]).model_fields) if ledger.cash else ['week_start'])
    table('ServiceMetrics',[s.model_dump(mode='json') for s in ledger.service],list(type(ledger.service[0]).model_fields) if ledger.service else ['sku'])
    table('ReviewDecisions',[d.model_dump(mode='json') for d in draft.decisions],['source_run_id','input_hash','assumption_version','action_type','business_key','original_quantity','reviewed_quantity','status','disposition','timestamp','note','original'])
    table('Assumptions',[{'key':f'policy_{i}','value':a} for i,a in enumerate(draft.result.assumptions)]+[{'key':'scenario','value':draft.scenario.model_dump(mode='json')},{'key':'acknowledged_shortfalls','value':draft.acknowledged_shortfalls}],['key','value'])
    metadata=dict(run_id=draft.result.run_id,accepted_version=draft.accepted_version,as_of=str(draft.result.as_of),input_hash=draft.result.input_hash,
        base_input_hash=draft.base_input_hash,assumption_version=draft.assumption_version,schema_version=SCHEMA_VERSION,engine_version=draft.result.engine_version,
        solver_status=draft.result.status,replay='passed',validator='passed',source=draft.input_source,synthetic=snapshot.dataset.synthetic,snapshot_checksum=snapshot.checksum)
    rows=[{'key':k,'value':v} for k,v in metadata.items()]
    rows += [{'key':'forecast_'+k,'value':v} for k,v in snapshot.forecast_versions.items()]
    rows += [{'key':'solver_'+str(i),'value':s.model_dump(mode='json')} for i,s in enumerate(draft.result.stages)]
    table('Metadata',rows,['key','value'])
    output=BytesIO();wb.save(output);return output.getvalue()
