from copy import deepcopy
from datetime import timedelta
from time import perf_counter
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.tests.test_planning import hand_data,hand_demand
from backend.app.contracts import OpenOrder,Payable
from backend.app.planning.inputs import Inputs
from backend.app.planning.evidence import purchase_evidence_targets
from backend.app.scenarios.contracts import *
from backend.app.scenarios.engine import *

@pytest.fixture
def hand(monkeypatch):
    data=hand_data();prepared=(hand_demand(56),{},[],[])
    monkeypatch.setattr('backend.app.scenarios.engine.network_forecasts',lambda *args:deepcopy(prepared))
    ctx=Inputs(data,*prepared[:2]);p=ctx.purchase(data.supplier_offers[0],0,40);m=ctx.movement(data.transfer_lanes[0],'X',2,40)
    base=snapshot('fixture',data,Actions(purchases=[p],movements=[m]))
    return data,base,prepared


def test_delay_preserves_decisions_moves_balance_and_suppresses_impossible_service(hand):
    data,base,_=hand;before=data.model_dump_json();actions=base.model_dump_json()
    definition=ScenarioDefinition(delays=[Delay(supplier_id='S',days=3,future_paths=True)])
    r=compare(data,ScenarioRequest(baseline=base,scenario=definition))
    old,new=r.original.purchases[0],r.frozen.purchases[0]
    assert (new.action_id,new.units,new.order_date,new.dispatch_date)==(old.action_id,old.units,old.order_date,old.dispatch_date)
    assert new.arrival_date==old.arrival_date+timedelta(days=3)
    assert r.frozen.movements==r.original.movements
    assert not r.frozen.feasible and r.frozen.summary is None and r.frozen.shortages==[]
    assert 'stock_overallocated' in {f.code for f in r.frozen.failures}
    assert all(v is None for v in r.shock_delta.values())
    transformed,_,_=transform(data,definition)
    ledger=replay(transformed,hand_demand(56),{},r.frozen.purchases,r.frozen.movements)
    assert [(p.kind,p.amount,p.due_date) for p in ledger.payments if p.reference==old.action_id]==[
        ('deposit',200,data.settings.as_of),('balance',200,old.arrival_date+timedelta(days=33))]
    assert r.frozen.assumptions_hash==r.replanned.assumptions_hash
    assert data.model_dump_json()==before and base.model_dump_json()==actions
    assert r.replanned.feasible
    changed,normalized,_=transform(data,definition)
    frozen=frozen_actions(changed,normalized,Actions(purchases=base.purchases,movements=base.movements))
    frozen_ledger=replay(changed,hand_demand(56),{},frozen.purchases,frozen.movements)
    replanned_actions=Actions(purchases=r.replanned.purchases,movements=r.replanned.movements)
    replanned_ledger=replay(changed,hand_demand(56),{},replanned_actions.purchases,replanned_actions.movements)
    assert r.frozen.evidence_targets==[]
    assert r.replanned.evidence_targets==purchase_evidence_targets(changed,replanned_ledger,replanned_actions.purchases)


def test_existing_delay_uses_calendar_and_leaves_fixed_payables_once(hand):
    data,_,_=hand;start=data.settings.as_of
    data.locations[0].open_weekdays=[0,1,2,3,4]
    data.open_orders=[OpenOrder(external_id='EX',sku='X',supplier_id='S',destination='DC',remaining_units=40,order_date=start,dispatch_date=start,arrival_date=start+timedelta(days=4),status='confirmed',cost_per_base_unit=10)]
    data.payables=[Payable(external_id='PAY',linked_external_id='EX',due_date=start+timedelta(days=6),amount=200)]
    before=data.model_dump_json()
    changed,_,_=transform(data,ScenarioDefinition(delays=[Delay(supplier_id='S',days=1,existing_order_ids=['EX'])]))
    assert changed.open_orders[0].arrival_date==start+timedelta(days=7)
    assert changed.payables==data.payables and changed.supplier_offers==data.supplier_offers
    ledger=replay(changed,hand_demand(56),{})
    assert len(ledger.payments)==1 and ledger.summary.payments==200
    assert ledger.payments[0].due_date==start+timedelta(days=6)
    assert data.model_dump_json()==before


def test_capacity_loss_invalidates_frozen_and_limits_replanning(hand):
    data,base,_=hand;s=data.settings.as_of
    definition=ScenarioDefinition(availability=[Availability(supplier_id='S',start=s,end=s+timedelta(days=55),remaining_fraction=0)])
    r=compare(data,ScenarioRequest(baseline=base,scenario=definition))
    assert 'supplier_capacity' in {f.code for f in r.frozen.failures}
    assert r.frozen.summary is None and r.replanned.feasible and not r.replanned.purchases


@pytest.mark.parametrize('field,code',[('commitment','commitment_cap'),('payment','payment_ceiling')])
def test_funding_limits_are_independent(hand,field,code):
    data,base,_=hand;s=data.settings.as_of
    r=compare(data,ScenarioRequest(baseline=base,scenario=ScenarioDefinition(funding=[Funding(week_start=s,**{field:0})])))
    failures={f.code for f in r.frozen.failures};assert code in failures
    assert ('payment_ceiling' if field=='commitment' else 'commitment_cap') not in failures
    assert r.replanned.feasible


def test_existing_obligations_above_ceiling_are_not_erased(hand):
    data,_,_=hand;s=data.settings.as_of
    data.payables=[Payable(external_id='PAY',linked_external_id='old',due_date=s,amount=50)]
    base=snapshot('fixture',data,Actions())
    r=compare(data,ScenarioRequest(baseline=base,scenario=ScenarioDefinition(funding=[Funding(week_start=s,payment=40)])))
    assert not r.frozen.feasible and not r.replanned.feasible and r.replanned.summary is None
    assert 'existing_payment_breach' in {f.code for f in r.replanned.failures}
    assert r.replanned.cash[0].existing_payments==50


def test_uplift_composition_scope_once_and_no_mutation(hand):
    data,_,prepared=hand;s=data.settings.as_of
    definition=ScenarioDefinition(uplifts=[Uplift(scope='store',scope_id='A',start=s,end=s+timedelta(days=1),percent=50)],funding=[Funding(week_start=s,commitment=100)],availability=[Availability(supplier_id='S',start=s,end=s,remaining_fraction=.5)])
    changed,normalized,_=transform(data,definition);adjusted=adjust_forecasts(changed,normalized,prepared)
    assert adjusted[0]['X','A'][:3]==[15,15,10]
    assert adjusted[0]['X','B']==prepared[0]['X','B']
    assert prepared[0]['X','A'][:3]==[10,10,10]
    assert changed.supplier_capacity[0].available_units==500 and data.supplier_capacity[0].available_units==1000
    assert adjust_forecasts(changed,normalized,prepared)[0]==adjusted[0]
    overlap=definition.model_copy(deep=True);overlap.uplifts.append(Uplift(scope='sku',scope_id='X',start=s,end=s,percent=5))
    with pytest.raises(ValueError,match='Overlapping'):transform(data,overlap)
    assert transform(data,ScenarioDefinition())[0]==data


@pytest.mark.parametrize('change',[
    {'uplifts':[{'scope':'sku','scope_id':'missing','start':'2026-09-14','end':'2026-09-15','percent':10}]},
    {'uplifts':[{'scope':'sku','scope_id':'X','start':'2026-09-13','end':'2026-09-15','percent':10}]},
    {'delays':[{'supplier_id':'S','days':14,'future_paths':True}]},
    {'delays':[{'supplier_id':'S','days':1,'existing_order_ids':['unknown']}]},
    {'funding':[{'week_start':'2026-09-15','payment':1}]},
    {'funding':[{'week_start':'2026-09-14','payment':1.001}]},
])
def test_unsupported_changes_are_rejected(hand,change):
    with pytest.raises(ValueError):transform(hand[0],ScenarioDefinition.model_validate(change))


def test_action_matching_uses_business_attributes(hand):
    _,base,_=hand;a=Actions(purchases=base.purchases,movements=base.movements);b=a.model_copy(deep=True)
    b.purchases[0].action_id='new-generated-id';assert action_diff(a,b)==[]
    b.purchases[0].units+=10
    assert action_diff(a,b)[0].change=='changed'


@pytest.fixture(scope='module')
def real_baseline():
    from backend.app.data.sample import generate_sample
    data=generate_sample();return data,baseline_result('fixture',data)


def test_real_noop_repeat_reset_and_snapshot_integrity(real_baseline):
    data,base=real_baseline;before=data.model_dump_json();snapshot_before=base.baseline.model_dump_json()
    r=compare(data,ScenarioRequest(baseline=base.baseline))
    assert r.original.summary==base.original.summary==r.frozen.summary==r.replanned.summary
    s=data.settings.as_of;definition=ScenarioDefinition(uplifts=[Uplift(scope='sku',scope_id='SKU001',start=s,end=s+timedelta(days=6),percent=30)])
    first=compare(data,ScenarioRequest(baseline=base.baseline,scenario=definition));again=compare(data,ScenarioRequest(baseline=base.baseline,scenario=definition))
    for key in ('purchases','movements','summary','cash','shortages','explanations'):
        assert getattr(first.replanned,key)==getattr(again.replanned,key)
    assert first.scenario_hash==again.scenario_hash and first.original.summary==base.original.summary
    assert data.model_dump_json()==before and base.baseline.model_dump_json()==snapshot_before
    assert first.frozen.assumptions_hash==first.replanned.assumptions_hash
    assert len(first.model_dump_json().encode())<4_500_000 and '"stock":' not in first.model_dump_json()
    bad=base.baseline.model_copy(deep=True);bad.purchases[0].units+=10
    with pytest.raises(ValueError,match='checksum'):compare(data,ScenarioRequest(baseline=bad))


def test_supplier_preset_metadata_identifies_one_usable_supplier(real_baseline):
    _,base=real_baseline
    supplier=next(option for option in base.supplier_options if option.existing_order_ids and option.future_paths)
    assert supplier.name and supplier.supplier_id
    assert all(order['supplier']==supplier.supplier_id for order in base.existing_orders if order['id'] in supplier.existing_order_ids)
    assert supplier.supplier_id in base.suppliers


def test_feasible_frozen_evidence_uses_frozen_policy_replay(real_baseline):
    data,base=real_baseline;s=data.settings.as_of
    definition=ScenarioDefinition(availability=[Availability(supplier_id='SUP01',start=s,end=s+timedelta(days=55),remaining_fraction=1)])
    result=compare(data,ScenarioRequest(baseline=base.baseline,scenario=definition))
    assert result.frozen.feasible
    changed,normalized,_=transform(data,definition)
    actions=frozen_actions(changed,normalized,Actions(purchases=base.baseline.purchases,movements=base.baseline.movements))
    prepared=adjust_forecasts(changed,normalized,network_forecasts(data,perf_counter()+30))
    ledger=replay(changed,*prepared[:2],actions.purchases,actions.movements)
    assert result.frozen.evidence_targets==purchase_evidence_targets(changed,ledger,actions.purchases)


def test_compact_detail_matches_comparison_forecast_cash_and_policy(real_baseline):
    data,base=real_baseline;s=data.settings.as_of
    definition=ScenarioDefinition(uplifts=[Uplift(scope='sku',scope_id='SKU001',start=s,end=s+timedelta(days=6),percent=30)])
    r=compare(data,ScenarioRequest(baseline=base.baseline,scenario=definition))
    d=detail(data,DetailRequest(baseline=base.baseline,scenario=definition,policy='replanned',actions=Actions(purchases=r.replanned.purchases,movements=r.replanned.movements),expected_action_hash=r.replanned.action_hash,expected_scenario_hash=r.scenario_hash,sku='SKU001',location_id='S1'))
    assert d.cash==r.replanned.cash and d.assumptions_hash==r.replanned.assumptions_hash
    assert d.forecast_version==r.forecast_versions['SKU001/S1']
    assert len(d.stock)==56*5 and all(s.sku=='SKU001' for s in d.stock)
    assert len(d.adjustments)==7 and d.adjustments[0].adjusted==pytest.approx(d.adjustments[0].original*1.3)
    assert len(d.model_dump_json().encode())<4_500_000
    # History/candidate evaluation must equal the unchanged underlying evaluator.
    baseline_detail=detail(data,DetailRequest(baseline=base.baseline,policy='original',sku='SKU001',location_id='S1'))
    assert baseline_detail.forecast.selection==d.forecast.selection
    assert baseline_detail.forecast.history==d.forecast.history


def test_api_session_isolation_and_invalid_amount(real_baseline):
    _,base=real_baseline;request=ScenarioRequest(baseline=base.baseline).model_dump(mode='json')
    a,b=TestClient(app),TestClient(app)
    broken=deepcopy(request);broken['scenario']['funding']=[{'week_start':'2026-09-14','payment':-1}]
    assert a.post('/api/scenarios/compare',json=broken).status_code==422
    original=b.post('/api/scenarios/compare',json=request)
    assert original.status_code==200 and original.json()['shock_delta']['unmet']==0


def test_normalization_order_and_overlap_validation(hand):
    data,_,_=hand;s=data.settings.as_of
    a=Uplift(scope='store',scope_id='A',start=s,end=s,percent=10)
    b=Uplift(scope='store',scope_id='B',start=s,end=s,percent=20)
    assert normalize(data,ScenarioDefinition(uplifts=[a,b]))==normalize(data,ScenarioDefinition(uplifts=[b,a]))
    capacity=Availability(supplier_id='S',start=s,end=s,remaining_fraction=.5)
    with pytest.raises(ValueError,match='Overlapping'):normalize(data,ScenarioDefinition(availability=[capacity,capacity]))
    with pytest.raises(ValueError,match='repeated'):normalize(data,ScenarioDefinition(funding=[Funding(week_start=s,payment=0),Funding(week_start=s,commitment=0)]))
    with pytest.raises(ValueError):Funding(week_start=s,payment=-1)
    data.open_orders=[OpenOrder(external_id='LATE',sku='X',supplier_id='S',destination='DC',remaining_units=1,order_date=s,dispatch_date=s,arrival_date=s+timedelta(days=55),status='confirmed',cost_per_base_unit=10)]
    with pytest.raises(ValueError,match='exceeds day 56'):transform(data,ScenarioDefinition(delays=[Delay(supplier_id='S',days=1,existing_order_ids=['LATE'])]))


def test_capture_reuses_actions_without_reoptimizing_and_detail_rejects_stale_versions(real_baseline,monkeypatch):
    data,base=real_baseline
    monkeypatch.setattr('backend.app.scenarios.engine.plan',lambda *args,**kwargs:pytest.fail('Capturing baseline must not reoptimize'))
    saved=capture(data,CaptureRequest(size='fixture',dataset_hash=dataset_hash(data),purchases=base.baseline.purchases,movements=base.baseline.movements))
    assert saved.baseline==base.baseline and saved.original.summary==base.original.summary
    with pytest.raises(ValueError,match='assumptions changed'):
        detail(data,DetailRequest(baseline=base.baseline,policy='original',sku='SKU001',location_id='S1',expected_scenario_hash='stale'))


@pytest.mark.parametrize('size,products,source',[('fixture',10,'bundled_fixture'),('full',60,'bundled_full')])
def test_bundled_snapshot_provenance_and_ids_are_deterministic(size,products,source):
    from backend.app.data.sample import generate_sample
    data=generate_sample(size);actions=Actions()
    first=snapshot(size,data,actions);second=snapshot(size,data,actions)
    assert first==second and first.snapshot_id==second.snapshot_id
    assert first.size==size and first.provenance.source==source
    assert first.provenance.sample_size==size
    assert first.provenance.dimensions.products==products


def test_invalid_frozen_detail_exposes_failures_without_invalid_stock_service(real_baseline):
    data,base=real_baseline;s=data.settings.as_of
    definition=ScenarioDefinition(availability=[Availability(supplier_id='SUP01',start=s,end=s+timedelta(days=55),remaining_fraction=0)])
    r=compare(data,ScenarioRequest(baseline=base.baseline,scenario=definition))
    d=detail(data,DetailRequest(baseline=base.baseline,scenario=definition,policy='frozen',expected_action_hash=r.frozen.action_hash,expected_scenario_hash=r.scenario_hash,sku='SKU001',location_id='S1'))
    assert not d.feasible and d.failures and not d.stock and not d.shortages
    assert d.cash==r.frozen.cash and d.forecast_version==r.forecast_versions['SKU001/S1']
