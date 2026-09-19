"""Withheld-demand evaluation has its own execution and information boundary."""
from datetime import timedelta
from types import SimpleNamespace

import pytest

from backend.tests.test_planning import hand_data, hand_demand
from backend.app.data.validation import validate_dataset
from backend.app.planning.inputs import Inputs
from scripts.policy_replay import execute_week, initial_state


def truth_for(data, a=10, b=5):
    return {('X',loc,str(data.settings.as_of+timedelta(days=i))):qty
            for loc,qty in [('A',a),('B',b)] for i in range(56)}


def policy(purchases=(), movements=()):
    return SimpleNamespace(purchases=list(purchases),movements=list(movements))


def test_realized_service_uses_truth_and_censored_sales_not_forecasts():
    data = initial_state(hand_data())
    demand = hand_demand(56)
    state, row = execute_week(data,policy(),demand,{},truth_for(data))
    assert row['demand_units']==105 and row['unmet_units']==50
    assert row['average_inventory_units']==pytest.approx(570/7)
    assert row['commitments_sar']==row['payments_in_week_sar']==0
    a = [r for r in state.demand_history if r.location_id=='A']
    assert [r.sales_units for r in a]==[10,10,0,0,0,0,0]
    assert a[2].stock_available is False
    assert a[-1].available_at.date()==state.settings.as_of  # midnight cannot see the 01:00 report
    _, different = execute_week(data,policy(),demand,{},truth_for(data,a=20))
    assert different['demand_units']==175 and different['unmet_units']==120


def test_future_truth_cannot_change_release_execution_or_next_origin_inputs():
    data=initial_state(hand_data()); demand=hand_demand(56); oracle=truth_for(data)
    changed=dict(oracle)
    for key in changed:
        if key[2]>=str(data.settings.as_of+timedelta(days=7)): changed[key]=99999
    first=execute_week(data,policy(),demand,{},oracle)
    assert first==execute_week(data,policy(),demand,{},changed)
    assert 'true_demand' not in first[0].model_dump_json()


def test_purchase_deposit_balance_and_received_identity_carry_once():
    data=initial_state(hand_data()); demand=hand_demand(56); ctx=Inputs(data,demand,{})
    purchase=ctx.purchase(data.supplier_offers[0],0,40)
    movement=ctx.movement(data.transfer_lanes[0],'X',2,40)
    state,row=execute_week(data,policy([purchase],[movement]),demand,{},truth_for(data))
    assert row['unmet_units']==10 and row['commitments_sar']==400
    assert row['payments_in_week_sar']==220 and row['movement_expense_sar']==20
    assert row['future_payables_sar']==200
    assert state.open_orders[0].status=='received' and state.open_orders[0].remaining_units==0
    assert state.payables[0].linked_external_id==state.open_orders[0].external_id
    assert state.payables[0].due_date==purchase.arrival_date+timedelta(days=30)
    assert not any(i.code in ('unknown_payable_link','conflicting_empty','received_stock') for i in validate_dataset(state))
    _,second=execute_week(state,policy(),{k:[0]*56 for k in demand},{},truth_for(state,a=0,b=0))
    assert second['commitments_sar']==second['payments_in_week_sar']==0
    assert second['future_payables_sar']==200


def test_realized_stock_guard_cancels_whole_movement_without_future_borrowing():
    data=initial_state(hand_data()); demand=hand_demand(56); ctx=Inputs(data,demand,{})
    movement=ctx.movement(data.transfer_lanes[2],'X',0,50)
    _,normal=execute_week(data,policy(movements=[movement]),demand,{},truth_for(data))
    assert normal['unmet_units']==0 and normal['average_inventory_units']==60
    oracle=truth_for(data); oracle['X','B',str(data.settings.as_of)]=90
    state,guarded=execute_week(data,policy(movements=[movement]),demand,{},oracle)
    assert len(guarded['cancelled_movements'])==1 and guarded['released_movements']==[]
    assert guarded['movement_expense_sar']==0
    assert min(r.on_hand for r in state.inventory)>=0 and guarded['stock_conservation']


def test_missing_oracle_fails_instead_of_substituting_forecast():
    data=initial_state(hand_data())
    with pytest.raises(KeyError): execute_week(data,policy(),hand_demand(56),{}, {})
