"""Hand arithmetic and adversarial reconstruction, independent of optimizer variables."""
from datetime import date, timedelta
from time import perf_counter
import pytest
from backend.app.contracts import Dataset, OpenTransfer, Payable, OpenOrder
from backend.app.planning.contracts import Movement
from backend.app.planning.inputs import Inputs, planning_input_failures
from backend.app.planning.benchmark import benchmark
from backend.app.planning.optimizer import optimize
from backend.app.simulation.replay import replay


def hand_data():
    start=date(2026,9,14)
    return Dataset.model_validate(dict(dataset_id='hand',synthetic=True,
        products=[dict(sku='X',name='Hand fixture',case_size=10,volume_per_unit=1,cost_per_base_unit=10,net_price_per_base_unit=12,category='test',active_from=start-timedelta(days=420))],
        locations=[dict(location_id=l,name=l,kind='dc' if l=='DC' else 'store',storage_volume=10000,open_weekdays=list(range(7))) for l in ['DC','A','B']],
        assortment=[dict(sku='X',location_id=l,ranged_from=start-timedelta(days=420),service_class='A',must_stock=True) for l in ['A','B']],
        demand_history=[],inventory=[dict(sku='X',location_id=l,as_of=start,on_hand=q,blocked=0,reserved=0,book_unit_cost=10) for l,q in [('DC',0),('A',20),('B',100)]],
        suppliers=[dict(supplier_id='S',name='S',minimum_order_value=0,shared_daily_capacity=1000,shared_capacity_unit='base_units')],
        supplier_offers=[dict(offer_id='O',supplier_id='S',sku='X',valid_from=start,valid_to=start+timedelta(days=55),price_per_base_unit=10,case_size=10,moq_units=10,lead_time_days=2,dispatch_weekdays=list(range(7)),order_weekdays=list(range(7)),deposit_fraction=.5,balance_days_after_receipt=30)],
        supplier_capacity=[dict(supplier_id='S',sku='X',dispatch_date=start+timedelta(days=i),available_units=1000,shared_limit_reference='S') for i in range(56)],
        transfer_lanes=[dict(source=src,destination=dst,transit_days=t,dispatch_weekdays=list(range(7)),capacity_units=1000,grouped_dispatch_fee=20,pack_units=10,allowed_skus=['X']) for src,dst,t in [('DC','A',1),('DC','B',1),('B','A',2)]],
        open_orders=[],open_transfers=[],payables=[],budgets=[dict(week_start=start+timedelta(days=7*i),new_commitment_cap=100000,payment_ceiling=100000,transfer_budget=10000) for i in range(14)],
        events=[],settings=dict(as_of=start,fallback_buffer_days=0,annual_holding_rate=0),declared_empty=['open_orders','open_transfers','payables']))


def hand_demand(h=7):
    return {('X','A'):[10.]*7+[0.]*(h-7),('X','B'):[5.]*7+[0.]*(h-7)}


def test_exact_three_hand_alternatives():
    data=hand_data(); demand=hand_demand();ctx=Inputs(data,hand_demand(56),{})
    none=replay(data,demand,{},horizon=7)
    transfer=ctx.movement(data.transfer_lanes[2],'X',0,50)
    moved=replay(data,demand,{},movements=[transfer],horizon=7)
    order=ctx.purchase(data.supplier_offers[0],0,40)
    dispatch=ctx.movement(data.transfer_lanes[0],'X',2,40)
    bought=replay(data,demand,{},[order],[dispatch],horizon=7)
    for result,expected in [(none,(50,65,0,0)),(moved,(0,15,0,20)),(bought,(10,65,400,220))]:
        assert result.feasible, result.failures
        s=result.summary
        assert (s.unmet,s.ending_stock,s.commitments,s.visible_payments)==expected
    assert bought.summary.later_payments==200
    assert bought.payments[-1].due_date==data.settings.as_of+timedelta(days=32)


def test_independent_replay_rejects_second_receiver_and_early_stock():
    data=hand_data();data.inventory[0].on_hand=40
    ctx=Inputs(data,hand_demand(56),{})
    moves=[ctx.movement(l,'X',0,30) for l in data.transfer_lanes[:2]]
    result=replay(data,hand_demand(),{},movements=moves,horizon=7)
    assert 'stock_overallocated' in {f.code for f in result.failures}
    data.inventory[0].on_hand=0
    order=ctx.purchase(data.supplier_offers[0],0,40)
    result=replay(data,hand_demand(),{},[order],moves[:1],horizon=7)
    assert 'stock_overallocated' in {f.code for f in result.failures}


def test_donor_increase_late_receipt_and_conditional_no_transfer():
    data=hand_data();demand=hand_demand();demand['X','B']=[12.]*7
    ctx=Inputs(data,hand_demand(56),{})
    move=ctx.movement(data.transfer_lanes[2],'X',0,50)
    assert 'donor_reserve' in {f.code for f in replay(data,demand,{},movements=[move],horizon=7).failures}
    data.inventory[2].on_hand=0
    assert replay(data,demand,{},horizon=7).feasible  # reserve only binds on dispatch
    data.inventory[2].on_hand=60
    data.open_transfers=[OpenTransfer(external_id='late',sku='X',source='DC',destination='B',remaining_units=100,dispatch_date=data.settings.as_of-timedelta(days=1),arrival_date=data.settings.as_of+timedelta(days=6),status='dispatched')]
    assert 'donor_reserve' in {f.code for f in replay(data,demand,{},movements=[move],horizon=7).failures}


def test_rounding_capacity_and_each_cash_period():
    data=hand_data();ctx=Inputs(data,hand_demand(56),{});o=ctx.purchase(data.supplier_offers[0],0,40)
    data.budgets[0].new_commitment_cap=399
    assert 'commitment_cap' in {f.code for f in replay(data,hand_demand(),{},[o],horizon=7).failures}
    data.budgets[0].new_commitment_cap=400
    data.budgets[4].payment_ceiling=199
    r=replay(data,hand_demand(),{},[o],horizon=7)
    assert 'payment_ceiling' in {f.code for f in r.failures} and r.cash[4].payment_headroom==-1
    data.supplier_capacity[0].available_units=30
    assert 'supplier_capacity' in {f.code for f in replay(data,hand_demand(),{},[o],horizon=7).failures}
    bad=o.model_copy(update={'units':41,'value':410})
    assert 'purchase_pack_moq' in {f.code for f in replay(data,hand_demand(),{},[bad],horizon=7).failures}


def test_existing_obligations_and_reservations_count_once():
    data=hand_data();start=data.settings.as_of
    data.inventory[0].on_hand=70;data.inventory[0].reserved=20;data.inventory[0].blocked=10
    data.open_transfers=[OpenTransfer(external_id='T',sku='X',source='DC',destination='A',remaining_units=20,dispatch_date=start-timedelta(days=1),arrival_date=start+timedelta(days=1),status='dispatched')]
    data.payables=[Payable(external_id='bill',linked_external_id='T',due_date=start,amount=90)]
    data.budgets[0].payment_ceiling=100
    ctx=Inputs(data,hand_demand(56),{});o=ctx.purchase(data.supplier_offers[0],0,10)
    r=replay(data,hand_demand(),{},horizon=7)
    assert r.feasible
    assert r.summary.commitments==0 and r.summary.payments==90
    assert r.stock[0].opening==40
    assert r.summary.ending_stock==105  # 120 store + 40 usable DC + 20 transit - 75 served
    assert 'payment_ceiling' in {f.code for f in replay(data,hand_demand(),{},[o],horizon=7).failures}
    assert replay(data,hand_demand(),{},[o],horizon=7).cash[0].commitments==100


def test_validator_grouped_fees_shared_supplier_storage_and_duplicate_actions():
    data=hand_data();ctx=Inputs(data,hand_demand(56),{});o=ctx.purchase(data.supplier_offers[0],0,40)
    data.suppliers[0].minimum_order_value=500
    assert 'supplier_minimum' in {f.code for f in replay(data,hand_demand(),{},[o],horizon=7).failures}
    data.suppliers[0].minimum_order_value=0;data.suppliers[0].shared_daily_capacity=30
    assert 'shared_supplier_capacity' in {f.code for f in replay(data,hand_demand(),{},[o],horizon=7).failures}
    data.locations[0].storage_volume=30
    assert 'receiving_volume' in {f.code for f in replay(data,hand_demand(),{},[o],horizon=7).failures}
    assert 'duplicate_action' in {f.code for f in replay(data,hand_demand(),{},[o,o],horizon=7).failures}
    movement=ctx.movement(data.transfer_lanes[0],'X',2,13)
    assert 'movement_pack' in {f.code for f in replay(data,hand_demand(),{},[o],[movement],horizon=7).failures}


def test_benchmark_constraints_shortage_and_determinism():
    data=hand_data();data.inventory[0].on_hand=30;data.inventory[1].on_hand=0;data.inventory[2].on_hand=0
    for b in data.budgets:b.new_commitment_cap=99
    demand={('X','A'):[10.]*56,('X','B'):[10.]*56}
    ctx=Inputs(data,demand,{})
    p,m=benchmark(ctx)
    assert not p  # one case costs 100; never round after funding validation
    assert (p,m)==benchmark(ctx)
    assert sum(t.units for t in m)==30
    assert m[0].destination=='A'
    r=replay(data,demand,{},p,m)
    assert r.feasible and r.summary.unmet==530


def test_joint_solver_hand_fixture_and_timeout():
    data=hand_data();ctx=Inputs(data,hand_demand(56),{})
    p,m,stages=optimize(ctx,perf_counter()+8)
    r=replay(data,hand_demand(56),{},p,m)
    assert r.feasible,r.failures
    assert r.summary.unmet==0
    assert r.summary.commitments==0
    assert r.summary.movement_expense==20
    assert all(s.status=='optimal' for s in stages)
    p,m,stages=optimize(ctx,perf_counter()-1)
    assert not p and not m and stages[0].status=='time_limit'


def test_missing_capacity_and_snapshot_are_not_zero_or_unlimited():
    data=hand_data();data.inventory.pop();data.supplier_capacity.pop(0)
    assert {'missing_snapshot','missing_capacity'} <= {f.code for f in planning_input_failures(data)}


def test_adequate_stock_zero_demand_and_pooled_service():
    data=hand_data()
    for row in data.inventory: row.on_hand=1000
    r=replay(data,hand_demand(56),{})
    assert r.feasible and r.summary.unmet==0 and r.summary.commitments==0
    assert all(g.target_shortfall==0 for g in r.service_groups)
    zero=replay(data,{('X','A'):[0.]*56,('X','B'):[0.]*56},{})
    assert zero.feasible and zero.summary.fill_pct is None and zero.summary.unmet==0
    assert zero.summary.ending_inventory_investment==30000


def test_locked_transfer_and_received_po_payable_once():
    data=hand_data();start=data.settings.as_of;data.inventory[0].on_hand=40
    data.open_transfers=[OpenTransfer(external_id='locked',sku='X',source='DC',destination='A',remaining_units=20,dispatch_date=start,arrival_date=start+timedelta(days=1),status='confirmed')]
    data.open_orders=[OpenOrder(external_id='received',sku='X',supplier_id='S',destination='DC',remaining_units=0,order_date=start-timedelta(days=5),dispatch_date=start-timedelta(days=5),arrival_date=start-timedelta(days=3),cost_per_base_unit=10,status='received')]
    data.payables=[Payable(external_id='balance',linked_external_id='received',due_date=start,amount=100)]
    r=replay(data,hand_demand(),{},horizon=7)
    assert r.feasible,r.failures
    assert r.stock[0].dispatched==20 and r.stock[0].closing==20
    assert r.summary.unmet==30 and r.summary.ending_stock==85
    assert r.summary.commitments==0 and r.summary.payments==100
    data.budgets[0].payment_ceiling=99
    assert replay(data,hand_demand(),{},horizon=7).cash[0].payment_headroom==-1


def test_multiple_skus_share_dispatch_fee_capacity_and_supplier_minimum():
    data=hand_data();data.products.append(data.products[0].model_copy(update={'sku':'Y'}))
    data.inventory.extend(row.model_copy(update={'sku':'Y'}) for row in list(data.inventory))
    data.supplier_offers.append(data.supplier_offers[0].model_copy(update={'sku':'Y','offer_id':'Y'}))
    data.supplier_capacity.extend(c.model_copy(update={'sku':'Y'}) for c in list(data.supplier_capacity))
    for lane in data.transfer_lanes: lane.allowed_skus.append('Y')
    data.inventory[0].on_hand=40;data.inventory[3].on_hand=40
    ctx=Inputs(data,hand_demand(56),{})
    moves=[ctx.movement(data.transfer_lanes[0],sku,0,20) for sku in ['X','Y']]
    r=replay(data,hand_demand(),{},movements=moves,horizon=7)
    assert r.feasible and r.summary.movement_expense==20
    data.transfer_lanes[0].capacity_units=30
    assert 'lane_capacity' in {f.code for f in replay(data,hand_demand(),{},movements=moves,horizon=7).failures}
    data.suppliers[0].minimum_order_value=400
    orders=[ctx.purchase(offer,0,20) for offer in data.supplier_offers]
    assert replay(data,hand_demand(),{},orders,horizon=7).feasible  # 2 x 200 satisfies grouped MOV
    data.suppliers[0].shared_daily_capacity=30
    assert 'shared_supplier_capacity' in {f.code for f in replay(data,hand_demand(),{},orders,horizon=7).failures}


def test_cents_same_week_installments_and_corrupt_dates_or_value():
    data=hand_data();o=data.supplier_offers[0]
    o.price_per_base_unit=1.01;o.deposit_fraction=.333;o.balance_days_after_receipt=0
    ctx=Inputs(data,hand_demand(56),{});purchase=ctx.purchase(o,0,10)
    r=replay(data,hand_demand(),{},[purchase],horizon=7)
    assert [p.amount for p in r.payments]==[3.36,6.74]
    assert r.cash[0].new_payments==10.10
    data.budgets[0].payment_ceiling=10.09
    assert 'payment_ceiling' in {f.code for f in replay(data,hand_demand(),{},[purchase],horizon=7).failures}
    bad=purchase.model_copy(update={'arrival_date':data.settings.as_of+timedelta(days=1),'value':1})
    assert {'purchase_timing','purchase_value'} <= {f.code for f in replay(data,hand_demand(),{},[bad],horizon=7).failures}


def test_tail_day29_demand_and_payments_beyond_day90():
    data=hand_data()
    for row in data.inventory:row.on_hand=0
    demand={('X','A'):[0.]*28+[10.]+[0.]*27,('X','B'):[0.]*56}
    ctx=Inputs(data,demand,{})
    order=ctx.purchase(data.supplier_offers[0],26,10)
    move=ctx.movement(data.transfer_lanes[0],'X',28,10)
    r=replay(data,demand,{},[order],[move])
    assert r.feasible and r.summary.unmet==0 and r.summary.tail_unmet==10
    # A day-29 DC receipt plus day-30 store receipt cannot cover day-29 store demand.
    assert r.summary.visible_commitments==100 and r.summary.tail_commitments==0
    data.payables=[Payable(external_id='later',linked_external_id='external-obligation',due_date=data.settings.as_of+timedelta(days=105),amount=25)]
    r=replay(data,demand,{})
    assert 'funding_coverage' in {f.code for f in r.failures}
    assert r.payments[-1].amount==25


def test_optimizer_shared_stock_and_case_budget_remain_hard():
    data=hand_data()
    for row in data.inventory:row.on_hand=0
    data.inventory[0].on_hand=30
    for b in data.budgets:b.new_commitment_cap=99
    demand={('X','A'):[10.]*56,('X','B'):[10.]*56}
    ctx=Inputs(data,demand,{})
    p,m,stages=optimize(ctx,perf_counter()+8)
    r=replay(data,demand,{},p,m)
    assert r.feasible,r.failures
    assert not p and sum(x.units for x in m)<=30
    assert r.summary.unmet>=530


def test_network_uses_unchanged_forecast_and_trace(dataset):
    from backend.app.planning.inputs import network_forecasts
    from backend.app.forecasting.engine import forecast
    demand,buffers,trace,failures=network_forecasts(dataset,perf_counter()+10)
    assert not failures and len(trace)==40
    t=next(t for t in trace if (t.sku,t.location_id)==('SKU001','S1'))
    settings=dataset.settings.model_copy(update={'protection_days':t.buffer.protection_days})
    direct=forecast(dataset.model_copy(update={'settings':settings}),'SKU001','S1')
    assert demand['SKU001','S1']==[f.forecast_units for f in direct.forecast]
    assert t.method==direct.selected_method and t.buffer==direct.buffer
    assert buffers['SKU001','S1']==direct.buffer.units


def test_api_validation_busy_and_validated_timeout_fallback(dataset,monkeypatch):
    from fastapi.testclient import TestClient
    from backend.app.main import app,calculation_slot
    from backend.app.planning.contracts import SolverStage
    monkeypatch.setattr('backend.app.planning.optimizer.optimize',lambda *args:([],[],[SolverStage(name='visible_must_stock',status='time_limit',elapsed_ms=0)]))
    client=TestClient(app)
    response=client.post('/api/plan/sample',json={'size':'fixture'})
    assert response.status_code==200
    r=response.json()
    assert r['status']=='feasible_fallback' and r['proposed']['replay']['feasible']
    assert not r['failures'] and r['exceptions']
    assert len(r['forecasts'])==40 and 'demand_history' not in r
    assert r['proposed']['replay']['summary']['commitments']==sum(p['value'] for p in r['proposed']['purchases'])
    invalid=dataset.model_copy(update={'inventory':dataset.inventory[1:]})
    r=client.post('/api/plan',json={'dataset':invalid.model_dump(mode='json')}).json()
    assert r['status']=='invalid_inputs' and r['proposed'] is None
    calculation_slot.acquire()
    try:
        assert client.post('/api/plan/sample',json={}).status_code==429
    finally:calculation_slot.release()


def test_existing_group_fee_is_not_charged_twice():
    data=hand_data();start=data.settings.as_of;data.inventory[0].on_hand=40
    data.open_transfers=[OpenTransfer(external_id='locked',sku='X',source='DC',destination='A',remaining_units=20,dispatch_date=start,arrival_date=start+timedelta(days=1),status='confirmed')]
    data.payables=[Payable(external_id='fee',linked_external_id='locked',due_date=start,amount=20)]
    ctx=Inputs(data,hand_demand(56),{})
    move=ctx.movement(data.transfer_lanes[0],'X',0,20)
    r=replay(data,hand_demand(),{},movements=[move],horizon=7)
    assert r.feasible and r.summary.payments==20 and r.summary.movement_expense==0
    assert r.stock[0].dispatched==40


def test_opposing_actions_and_invalid_calendars_fail_independently():
    data=hand_data();data.transfer_lanes.append(data.transfer_lanes[2].model_copy(update={'source':'A','destination':'B'}))
    data.inventory[1].on_hand=1000;data.inventory[2].on_hand=1000
    ctx=Inputs(data,hand_demand(56),{})
    moves=[ctx.movement(l,'X',0,10) for l in data.transfer_lanes[2:]]
    assert 'opposing_movements' in {f.code for f in replay(data,hand_demand(),{},movements=moves,horizon=7).failures}
    data.transfer_lanes[2].dispatch_weekdays=[1]
    assert 'movement_timing' in {f.code for f in replay(data,hand_demand(),{},movements=moves[:1],horizon=7).failures}


def test_zero_price_orders_do_not_consume_commitment_authority():
    data=hand_data();data.supplier_offers[0].price_per_base_unit=0
    for row in data.inventory:row.on_hand=0
    for b in data.budgets:b.new_commitment_cap=0
    demand={('X','A'):[10.]*56,('X','B'):[10.]*56}
    ctx=Inputs(data,demand,{})
    p,m=benchmark(ctx)
    assert p and all(o.value==0 for o in p)
    r=replay(data,demand,{},p,m)
    assert r.feasible and r.summary.commitments==0


def test_disjoint_calendars_report_invalid_inputs_without_looping(dataset):
    from backend.app.planning.inputs import network_forecasts
    data=dataset.model_copy(deep=True)
    next(l for l in data.locations if l.kind=='dc').open_weekdays=[0]
    for lane in data.transfer_lanes:
        if lane.source=='DC':lane.dispatch_weekdays=[1]
    _,_,_,failures=network_forecasts(data,perf_counter()+10)
    assert 'unreachable_lane_calendar' in {f.code for f in failures}
