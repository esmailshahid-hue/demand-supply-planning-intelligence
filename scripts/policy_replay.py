"""Offline, closed-loop weekly policy evaluation. Never imported by the API.

Only realized sales become later observations; future truth is passed solely to
the execution simulator, after each origin's actions have been fixed. Evaluate
four weekly releases, carrying stock, transit, committed orders and obligations.
The known funding calendar is extended at setup with its final declared limits
so later 56-day plans retain the required 90-day cash coverage. Offers/capacity,
forecasts, constraints, release windows and solver budgets are unchanged.
"""
import argparse
from collections import defaultdict
from datetime import datetime, time, timedelta
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter
from zoneinfo import ZoneInfo

from backend.app.contracts import Observation, OpenOrder, OpenTransfer, Payable
from backend.app.data.sample import generate_bundle
from backend.app.planning.engine import plan
from backend.app.planning.inputs import Inputs, network_forecasts
from backend.app.simulation.replay import cents, replay, week


def initial_state(data):
    data = data.model_copy(deep=True)
    # Ex ante evaluation-calendar assumption, identical for both policies.
    last = max(data.budgets, key=lambda b: b.week_start)
    data.budgets += [last.model_copy(update={'week_start': last.week_start + timedelta(days=7*i)}) for i in (1, 2, 3)]
    return data


def execute_week(data, policy, demand, buffers, truth):
    """Realize releases without oracle dispatch decisions or negative stock.

    Check the complete selected policy using the independent production replay
    first. At dispatch, cancel a whole new movement if observed stock cannot
    preserve the *origin forecast* donor reserve. Never borrow future receipts,
    partially dispatch a line, or use tomorrow's truth to protect the donor.
    Such cancellations are disclosed execution deviations, not feasible actions.
    """
    verified = replay(data, demand, buffers, policy.purchases, policy.movements)
    assert verified.feasible, [f.model_dump(mode='json') for f in verified.failures]
    start = data.settings.as_of
    stop = start + timedelta(days=7)
    ctx = Inputs(data, demand, buffers)
    purchases = [p for p in policy.purchases if p.order_date < stop]
    candidates = [m for m in policy.movements if m.dispatch_date < stop]
    offers = {o.offer_id: o for o in data.supplier_offers}
    products = {p.sku: p for p in data.products}
    locations = {l.location_id: l for l in data.locations}
    lanes = {(l.source, l.destination): l for l in data.transfer_lanes}
    stock = dict(ctx.initial)
    values = {(r.sku, r.location_id): stock[r.sku, r.location_id]*r.book_unit_cost for r in data.inventory}
    orders = [o for o in data.open_orders if o.status != 'received']
    orders += [OpenOrder(external_id=f'{start}-{p.action_id}', sku=p.sku, supplier_id=p.supplier_id,
        destination=p.destination, remaining_units=p.units, order_date=p.order_date,
        dispatch_date=p.dispatch_date, arrival_date=p.arrival_date, status='confirmed',
        cost_per_base_unit=offers[p.offer_id].price_per_base_unit) for p in purchases]
    transfers = [t for t in data.open_transfers if t.status != 'received']
    assert all(t.status == 'dispatched' for t in transfers), 'Evaluation requires already-dispatched carry-in transfers'
    receipts = defaultdict(list)
    for o in orders:
        receipts[o.arrival_date].append((o.sku, o.destination, o.remaining_units, o.remaining_units*o.cost_per_base_unit))
    for t in transfers:
        receipts[t.arrival_date].append((t.sku, t.destination, t.remaining_units,
            t.remaining_units*next(r.book_unit_cost for r in data.inventory if (r.sku,r.location_id)==(t.sku,t.source))))
    initial = sum(stock.values()) + sum(t.remaining_units for t in transfers)
    transit = sum(t.remaining_units for t in transfers)
    external = served = total = inventory_days = 0
    observations = []; executed = []; cancelled = []
    transfer_arrivals = defaultdict(int)
    for t in transfers: transfer_arrivals[t.arrival_date] += t.remaining_units
    for i in range(7):
        day = start + timedelta(days=i)
        for sku, loc, units, value in receipts[day]:
            stock[sku,loc] += units; values[sku,loc] += value
        external += sum(o.remaining_units for o in orders if o.arrival_date == day)
        transit -= transfer_arrivals[day]
        for loc in locations:
            assert sum((stock[sku,loc]+ctx.unavailable[sku,loc])*products[sku].volume_per_unit for sku in products) <= locations[loc].storage_volume+1e-5, 'Realized receiving capacity exceeded'
        for a in data.assortment:
            key = a.sku, a.location_id
            qty = truth[a.sku,a.location_id,day.isoformat()]
            is_open = day.weekday() in locations[a.location_id].open_weekdays and a.ranged_from <= day and (a.ranged_to is None or day <= a.ranged_to)
            if not is_open: qty = 0
            filled = min(qty, stock[key]); cost = values[key]/stock[key] if stock[key] else 0
            values[key] -= cost*filled; stock[key] -= filled
            total += qty; served += filled
            event = next((e.event_id for e in data.events if e.start <= day <= e.end and
                ((e.scope=='sku' and e.scope_id==a.sku) or (e.scope=='store' and e.scope_id==a.location_id) or
                 (e.scope=='category' and e.scope_id==products[a.sku].category))), None)
            observations.append(Observation(sku=a.sku, location_id=a.location_id, day=day, sales_units=filled,
                is_open=is_open, stock_available=filled==qty, event_id=event,
                available_at=datetime.combine(day+timedelta(days=1),time(1),ZoneInfo('Asia/Riyadh'))))
        for m in sorted((m for m in candidates if m.dispatch_date==day), key=lambda m:m.action_id):
            key = m.sku,m.source
            if stock[key]-m.units < ctx.reserve[*key,i]-1e-5:
                cancelled.append({'action_id':m.action_id,'day':str(day),'reason':'observed stock / origin donor reserve'})
                continue
            value = m.units*values[key]/stock[key]
            stock[key] -= m.units; values[key] -= value; transit += m.units
            receipts[m.arrival_date].append((m.sku,m.destination,m.units,value))
            transfer_arrivals[m.arrival_date] += m.units
            executed.append(m)
            transfers.append(OpenTransfer(external_id=f'{start}-{m.action_id}',sku=m.sku,source=m.source,
                destination=m.destination,remaining_units=m.units,dispatch_date=m.dispatch_date,arrival_date=m.arrival_date,status='dispatched'))
        assert min(stock.values()) >= 0
        assert abs(sum(stock.values())+transit-(initial+external-served)) < 1e-5
        inventory_days += sum(stock.values())+transit+sum(ctx.unavailable.values())
    ids = {p.action_id for p in purchases}
    flows = [p for p in verified.payments if p.kind in ('deposit','balance') and p.reference in ids]
    groups = {(m.source,m.destination,m.dispatch_date) for m in executed}
    fees = {g:cents(lanes[g[0],g[1]].grouped_dispatch_fee) for g in groups}
    pending = [p for p in data.payables if p.due_date >= stop]
    pending += [Payable(external_id=f'{start}-{p.reference}-{p.kind}',linked_external_id=f'{start}-{p.reference}',
        due_date=p.due_date,amount=p.amount) for p in flows if p.due_date >= stop]
    due = defaultdict(int)
    for p in data.payables: due[week(p.due_date)] += cents(p.amount)
    for p in flows: due[week(p.due_date)] += cents(p.amount)
    for g,amount in fees.items(): due[week(g[2])] += amount
    budgets = {b.week_start:b for b in data.budgets}
    assert all(amount <= cents(budgets[w].payment_ceiling) for w,amount in due.items())
    committed = sum(cents(p.value) for p in purchases)
    assert committed <= cents(budgets[week(start)].new_commitment_cap)
    assert sum(fees.values()) <= cents(budgets[week(start)].transfer_budget)
    result = data.model_copy(deep=True)
    result.settings = data.settings.model_copy(update={'as_of':stop})
    result.inventory = [r.model_copy(update={'as_of':stop,'on_hand':int(stock[r.sku,r.location_id])+r.blocked+r.reserved,
        'book_unit_cost':values[r.sku,r.location_id]/stock[r.sku,r.location_id] if stock[r.sku,r.location_id] else r.book_unit_cost}) for r in data.inventory]
    result.demand_history = [r for r in data.demand_history+observations if r.day >= stop-timedelta(days=420)]
    # Retain received IDs: an arrived purchase may still have an unpaid balance.
    result.open_orders = [o for o in data.open_orders if o.status == 'received'] + [o.model_copy(update={
        'status':'received' if o.arrival_date < stop else 'dispatched' if o.dispatch_date < stop else 'confirmed',
        'remaining_units':0 if o.arrival_date < stop else o.remaining_units}) for o in orders]
    result.open_transfers = [t for t in transfers if t.arrival_date >= stop]
    result.payables = pending
    result.declared_empty = [name for name in ('open_orders','open_transfers','payables') if not getattr(result,name)]
    return result, {'origin':str(start),'demand_units':total,'fulfilled_units':served,'unmet_units':total-served,
        'fill_pct':100*served/total if total else None,'average_inventory_units':inventory_days/7,
        'commitments_sar':committed/100,'payments_in_week_sar':due[week(start)]/100,
        'movement_expense_sar':sum(fees.values())/100,'future_payables_sar':sum(cents(p.amount) for p in pending)/100,
        'dated_funding_feasible':True,'independent_origin_replay':verified.feasible,'stock_conservation':True,
        'cash_weeks':[{'week_start':str(w),'payments_sar':amount/100,
            'payment_headroom_sar':(cents(budgets[w].payment_ceiling)-amount)/100} for w,amount in sorted(due.items())],
        'released_purchases':[p.model_dump(mode='json') for p in purchases],
        'released_movements':[m.model_dump(mode='json') for m in executed],'cancelled_movements':cancelled}


def evaluate(size='fixture', seed=97, weeks=4):
    assert 1 <= weeks <= 4
    bundle = generate_bundle(size,seed)
    truth = {(r['sku'],r['location_id'],r['day']):r['true_demand'] for r in bundle.truth}
    states = {name:initial_state(bundle.inputs) for name in ('proposed','benchmark')}
    records = {name:[] for name in states}
    for _ in range(weeks):
        for name,data in states.items():
            prepared = network_forecasts(data,perf_counter()+30)
            result = plan(data,prepared_forecasts=prepared)
            assert result.status in ('feasible','feasible_fallback'), (name,result.status,result.failures,result.issues)
            policy = getattr(result,name)
            states[name], record = execute_week(data,policy,prepared[0],prepared[1],truth)
            record.update(input_hash=result.input_hash,status=result.status,
                origin_actions_equal_benchmark=result.proposed.purchases==result.benchmark.purchases and result.proposed.movements==result.benchmark.movements)
            records[name].append(record)
            print(f'{name} {record["origin"]}: fill {record["fill_pct"]:.2f}%; unmet {record["unmet_units"]}; funding feasible; cancelled {len(record["cancelled_movements"])}',flush=True)
    summary = {}
    for name,rows in records.items():
        summary[name] = {key:sum(r[key] for r in rows) for key in ('demand_units','fulfilled_units','unmet_units','commitments_sar','payments_in_week_sar','movement_expense_sar')}
        summary[name].update(fill_pct=100*summary[name]['fulfilled_units']/summary[name]['demand_units'],
            average_inventory_units=sum(r['average_inventory_units'] for r in rows)/weeks,
            final_future_payables_sar=rows[-1]['future_payables_sar'],cancelled_movements=sum(len(r['cancelled_movements']) for r in rows))
        s = summary[name]
        assert cents(s['commitments_sar']) + sum(cents(p.amount) for p in bundle.inputs.payables) + cents(s['movement_expense_sar']) == cents(s['payments_in_week_sar']) + cents(s['final_future_payables_sar'])
        s['financial_reconciliation'] = True
    return {'dataset':bundle.inputs.dataset_id,'seed':seed,'weeks':weeks,'period_start':str(bundle.inputs.settings.as_of),
        'period_end':str(bundle.inputs.settings.as_of+timedelta(days=weeks*7-1)),
        'truth_sha256':sha256(json.dumps(bundle.truth,sort_keys=True).encode()).hexdigest(),
        'method':'Weekly releases; observed-stock execution guard; three extra funding weeks fixed ex ante at last declared ceilings.',
        'summary':summary,'weekly':records,'policy_actions_equal':all(
            all(a[k]==b[k] for k in ('released_purchases','released_movements','cancelled_movements'))
            for a,b in zip(records['proposed'],records['benchmark']))}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--size',choices=('fixture','full'),default='fixture')
    parser.add_argument('--seed',type=int,default=97); parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(); result = evaluate(args.size,args.seed)
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'summary':result['summary'],'policy_actions_equal':result['policy_actions_equal']},indent=2))
