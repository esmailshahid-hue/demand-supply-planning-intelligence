from datetime import datetime,timezone
from io import BytesIO
from time import perf_counter
import gzip,json
import pytest
from openpyxl import load_workbook
from backend.tests.test_planning import hand_data,hand_demand
from backend.app.planning.inputs import Inputs
from backend.app.planning.constraints import ReviewConstraints,business_key
from backend.app.planning.benchmark import benchmark
from backend.app.planning.optimizer import optimize
from backend.app.planning.engine import plan
from backend.app.planning.review import new_draft,decide,regenerate,accept,ReviewConflict,constraints
from backend.app.simulation.replay import replay,cents
from backend.app.data.accepted import create_snapshot,snapshot_bytes,read_snapshot,export_workbook
from backend.app.data.reconciliation import reconcile,Execution
from backend.app.contracts import OpenOrder


@pytest.fixture
def small():
    data=hand_data()
    for a in data.assortment:
        a.launch_daily_units=10 if a.location_id=='A' else 5
        a.launch_known_at=datetime(2026,1,1,tzinfo=timezone.utc);a.launch_reason='Known launch estimate'
    return data


@pytest.fixture
def draft(small):return new_draft(small,plan(small))


def test_accept_reject_and_exact_edit_regenerate(small,draft):
    p=draft.result.proposed.purchases[0]
    d=decide(draft,small,draft.revision,p.action_id,'accepted')
    assert d.state=='stale' and draft.state=='draft'
    with pytest.raises(ReviewConflict):accept(d,small,d.revision,True)
    r=regenerate(d,small,d.revision)
    assert r.state=='draft'
    assert next(a for a in r.result.proposed.purchases if business_key(a)==business_key(p)).units==p.units
    edited=decide(r,small,r.revision,p.action_id,'edited_quantity',p.units+10)
    re=regenerate(edited,small,edited.revision)
    assert re.state=='draft'
    assert next(a for a in re.result.proposed.purchases if business_key(a)==business_key(p)).units==p.units+10
    rejected=decide(draft,small,draft.revision,p.action_id,'rejected')
    rr=regenerate(rejected,small,rejected.revision)
    assert rr.state=='draft' and rr.result.proposed.replay.feasible
    assert all(business_key(a)!=business_key(p) for a in rr.result.proposed.purchases)


@pytest.mark.parametrize('quantity',[0,1,15,-10])
def test_invalid_pack_moq_edits(small,draft,quantity):
    with pytest.raises(ReviewConflict):decide(draft,small,draft.revision,draft.result.proposed.purchases[0].action_id,'edited_quantity',quantity)


def test_stale_versions_and_conflicting_locks(small,draft):
    p=draft.result.proposed.purchases[0]
    with pytest.raises(ReviewConflict):decide(draft,small,'old',p.action_id,'accepted')
    d=decide(draft,small,draft.revision,p.action_id,'edited_quantity',100000)
    r=regenerate(d,small,d.revision)
    assert r.state=='stale' and not r.result.proposed.replay.feasible
    assert any(f.code=='supplier_capacity' for f in r.failures)
    with pytest.raises(ReviewConflict):accept(r,small,r.revision,True)


@pytest.mark.parametrize('alternative',[False,True])
def test_rejected_purchase_never_preserves_infeasible_movement(alternative):
    data=hand_data();demand=hand_demand(56)
    for row in data.inventory:row.on_hand=50 if alternative and row.location_id=='DC' else 0
    # No alternate purchasing availability: only the reviewed candidate supplies stock.
    for row in data.supplier_capacity:row.available_units=0
    ctx=Inputs(data,demand,{})
    p=ctx.purchase(data.supplier_offers[0],0,50)
    m=ctx.movement(data.transfer_lanes[0],'X',2,40)
    constraints=ReviewConstraints(movements=[m],rejected={business_key(p)})
    ctx=Inputs(data,demand,{},constraints);purchases,movements=benchmark(ctx)
    checked=replay(data,demand,{},purchases,movements)
    assert checked.feasible is alternative
    assert not any(business_key(a)==business_key(p) for a in purchases)


@pytest.mark.parametrize('failure',['timeout','error'])
def test_solver_failure_cannot_drop_locks(small,draft,monkeypatch,failure):
    import backend.app.planning.optimizer as module
    p=draft.result.proposed.purchases[0]
    def failed(*args):
        if failure=='error':raise RuntimeError('solver')
        from backend.app.planning.contracts import SolverStage
        return [],[],[SolverStage(name='test',status='time_limit',elapsed_ms=0)]
    monkeypatch.setattr(module,'optimize',failed)
    d=decide(draft,small,draft.revision,p.action_id,'accepted');r=regenerate(d,small,d.revision)
    assert r.state=='draft' and r.result.status=='feasible_fallback'
    assert not ReviewConstraints(purchases=[p]).failures(r.result.proposed.purchases,r.result.proposed.movements)


def test_export_snapshot_and_immutable_acceptance(small,draft):
    # This hand fixture is fully covered; acknowledgement is only required for
    # an actual service/buffer shortfall, never merely because it is a fallback.
    accepted,checked,versions=accept(draft,small,draft.revision,True)
    snapshot=create_snapshot(small,accepted,versions)
    zipped,raw=snapshot_bytes(snapshot);assert raw>len(zipped)
    assert read_snapshot(zipped)==snapshot
    value=json.loads(gzip.decompress(zipped));value['dataset']['dataset_id']='corrupt'
    with pytest.raises(ValueError,match='checksum'):read_snapshot(gzip.compress(json.dumps(value).encode()))
    value['version']='unsupported'
    with pytest.raises(ValueError):read_snapshot(gzip.compress(json.dumps(value).encode()))
    with pytest.raises(ReviewConflict):decide(accepted,small,accepted.revision,accepted.result.proposed.purchases[0].action_id,'rejected')
    wb=load_workbook(BytesIO(export_workbook(snapshot)),read_only=True,data_only=False)
    def rows(name):
        rows=list(wb[name].values);return [dict(zip(rows[0],r)) for r in rows[1:]]
    purchases=rows('PurchaseActions');payments=rows('PaymentSchedule');cash=rows('WeeklyFunding')
    assert sum(cents(float(p['value'])) for p in purchases)==cents(checked.summary.commitments)
    assert sum(cents(float(p['amount'])) for p in payments)==cents(checked.summary.payments)
    assert [p['units'] for p in purchases]==[p.units for p in accepted.result.proposed.purchases]
    for actual,expected in zip(cash,checked.cash):
        for field in ('commitments','total_payments','commitment_headroom','payment_headroom','movement_fees'):
            assert float(actual[field])==getattr(expected,field)
    assert {p['external_id'] for p in purchases}=={snapshot.external_ids[p.action_id] for p in accepted.result.proposed.purchases}
    movements=rows('MovementActions')
    assert [(r['action_id'],r['units']) for r in movements]==[(m.action_id,m.units) for m in accepted.result.proposed.movements]
    assert [r['fee_group'] for r in movements]==[f'{m.source}-{m.destination}-{m.dispatch_date}' for m in accepted.result.proposed.movements]
    assert [(r['reference'],r['kind'],float(r['amount']),r['due_date']) for r in payments]==[(p.reference,p.kind,p.amount,str(p.due_date)) for p in checked.payments]
    for actual,expected in zip(rows('ServiceMetrics'),checked.service):
        assert actual['sku']==expected.sku and actual['location_id']==expected.location_id
        assert float(actual['unmet'])==expected.unmet
    wb.close()


def test_shortfall_requires_acknowledgement(small):
    for row in small.inventory:row.on_hand=0
    for row in small.supplier_capacity:row.available_units=0
    draft=new_draft(small,plan(small))
    assert draft.result.proposed.replay.summary.unmet>0
    with pytest.raises(ReviewConflict) as error:accept(draft,small,draft.revision,False)
    assert error.value.failures[0].code=='shortfall_acknowledgement'


@pytest.mark.parametrize('partial',[False,True])
def test_confirmed_external_replaces_proposal_idempotently(small,draft,partial):
    accepted,_,versions=accept(draft,small,draft.revision,True);snapshot=create_snapshot(small,accepted,versions)
    p=accepted.result.proposed.purchases[0];external=snapshot.external_ids[p.action_id]
    units=p.units//20*10 if partial else p.units
    data=small.model_copy(deep=True)
    data.open_orders.append(OpenOrder(external_id=external,sku=p.sku,supplier_id=p.supplier_id,destination=p.destination,remaining_units=units,order_date=p.order_date,dispatch_date=p.dispatch_date,arrival_date=p.arrival_date,status='confirmed',cost_per_base_unit=10))
    data.declared_empty.remove('open_orders')
    execution=Execution(external_id=external,confirmed_units=units,executed_units=0)
    locks,records=reconcile(data,snapshot,[execution]);again,evidence=reconcile(data,snapshot,[execution])
    assert records==evidence and locks==again
    assert records[0]['open_units']+records[0]['remaining_proposal_units']==p.units
    if partial:assert locks.purchases[0].units==p.units-units
    else:assert business_key(p) in locks.rejected and not locks.purchases
    with pytest.raises(ReviewConflict):reconcile(data,snapshot,[execution,execution])
    data.open_orders[0].remaining_units+=10
    with pytest.raises(ReviewConflict):reconcile(data,snapshot,[execution])


def test_reconciliation_remainders_cannot_be_restored_or_increased(small,draft):
    p=draft.result.proposed.purchases[0]
    remainder=p.model_copy(update={'units':20,'value':200})
    draft.execution_remainders=[remainder]
    with pytest.raises(ReviewConflict,match='conflicts'):
        decide(draft,small,draft.revision,p.action_id,'accepted')
    edited=decide(draft,small,draft.revision,p.action_id,'edited_quantity',20)
    assert constraints(edited,small).purchases[0].units==20
    cleared=decide(edited,small,edited.revision,p.action_id,'draft')
    assert constraints(cleared,small).purchases[0].units==20
    rejected=decide(edited,small,edited.revision,p.action_id,'rejected')
    assert business_key(p) in constraints(rejected,small).rejected
    assert not constraints(rejected,small).purchases


def test_scenario_review_keeps_pass3_forecast_versions(small):
    from backend.app.scenarios.engine import prepare,snapshot
    from backend.app.scenarios.contracts import ScenarioRequest,ScenarioDefinition,Funding,Actions
    scenario=ScenarioDefinition(funding=[Funding(week_start=small.budgets[0].week_start,commitment=5000)])
    request=ScenarioRequest(baseline=snapshot('fixture',small,Actions()),scenario=scenario)
    changed,definition,_,_,prepared,_=prepare(small,request)
    draft=new_draft(small,plan(changed,prepared_forecasts=prepared),definition)
    accepted,_,_=accept(draft,small,draft.revision,True)
    assert accepted.state=='accepted'


def test_final_acceptance_rejects_changed_ledger(small,draft):
    draft.result.proposed.replay.cash[0].payment_headroom+=1
    with pytest.raises(ReviewConflict) as error:accept(draft,small,draft.revision,True)
    assert any(f.code=='replay_mismatch' for f in error.value.failures)


def test_explicit_reconciliation_required_and_dispatched_transfer(small,draft):
    from backend.app.contracts import OpenTransfer
    accepted,_,versions=accept(draft,small,draft.revision,True)
    snapshot=create_snapshot(small,accepted,versions)
    m=accepted.result.proposed.movements[0];external=snapshot.external_ids[m.action_id]
    data=small.model_copy(deep=True)
    data.open_transfers=[OpenTransfer(external_id=external,sku=m.sku,source=m.source,destination=m.destination,remaining_units=m.units,dispatch_date=m.dispatch_date,arrival_date=m.arrival_date,status='dispatched')]
    with pytest.raises(ReviewConflict):reconcile(data,snapshot,[])
    locked,records=reconcile(data,snapshot,[Execution(external_id=external,confirmed_units=m.units,executed_units=0)])
    assert not locked.movements and business_key(m) in locked.rejected
    assert records[0]['open_units']==m.units and records[0]['remaining_proposal_units']==0


def test_received_purchase_is_stock_and_only_explicit_unpaid_balance(small,draft):
    from datetime import timedelta
    from backend.app.contracts import Payable
    accepted,_,versions=accept(draft,small,draft.revision,True)
    snapshot=create_snapshot(small,accepted,versions)
    p=accepted.result.proposed.purchases[0];external=snapshot.external_ids[p.action_id]
    data=small.model_copy(deep=True)
    data.settings.as_of=p.arrival_date
    for row in data.inventory:
        row.as_of=p.arrival_date
        if row.location_id==p.destination:row.on_hand+=p.units
    data.open_orders=[OpenOrder(external_id=external,sku=p.sku,supplier_id=p.supplier_id,destination=p.destination,remaining_units=0,order_date=p.order_date,dispatch_date=p.dispatch_date,arrival_date=p.arrival_date,status='received',cost_per_base_unit=10)]
    data.payables=[Payable(external_id='UNPAID',linked_external_id=external,due_date=p.arrival_date+timedelta(days=30),amount=100)]
    data.declared_empty=['open_transfers']
    locks,records=reconcile(data,snapshot,[Execution(external_id=external,confirmed_units=p.units,executed_units=p.units)])
    assert business_key(p) in locks.rejected and not locks.purchases
    checked=replay(data,{('X','A'):[0.]*56,('X','B'):[0.]*56},{})
    assert checked.feasible and checked.summary.commitments==0
    assert [(payment.kind,payment.amount) for payment in checked.payments]==[('existing',100)]
    assert all(day.receipts==0 for day in checked.stock)
    assert records[0]['remaining_proposal_units']==0


def test_joint_solver_honors_exact_purchase_lock_and_candidate_rejection():
    data=hand_data();demand=hand_demand(56);initial=Inputs(data,demand,{})
    purchase=initial.purchase(data.supplier_offers[0],0,40)
    rejected=initial.movement(data.transfer_lanes[2],'X',0,50)
    locks=ReviewConstraints(purchases=[purchase],rejected={business_key(rejected)})
    purchases,movements,stages=optimize(Inputs(data,demand,{},locks),perf_counter()+8)
    assert all(s.status=='optimal' for s in stages)
    assert not locks.failures(purchases,movements)
    assert replay(data,demand,{},purchases,movements).feasible
