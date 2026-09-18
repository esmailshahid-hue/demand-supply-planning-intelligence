"""Immutable transformations and three-policy comparison over the existing engine."""
from datetime import timedelta
from hashlib import sha256
import json
from math import floor
from time import perf_counter
from backend.app.planning.engine import plan
from backend.app.planning.inputs import Inputs, network_forecasts
from backend.app.planning.evidence import purchase_evidence_targets
from backend.app.simulation.replay import replay
from backend.app.forecasting.engine import forecast
from backend.app.scenarios.contracts import (Actions, BaselineSnapshot, Outcome, BaselineResult, Funding, ActionChange, ScenarioResult, Adjustment, ScenarioDetail, SupplierOption)


def digest(value):
    if hasattr(value,'model_dump'):value=value.model_dump(mode='json')
    return sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def dataset_hash(data):return sha256(data.model_dump_json().encode()).hexdigest()
def actions_of(policy):return Actions(purchases=policy.purchases,movements=policy.movements)

def snapshot(size,data,actions):
    body=dict(size=size,dataset_hash=dataset_hash(data),version='sample-scenarios-1',**actions.model_dump(mode='json'))
    return BaselineSnapshot(**body,snapshot_id=digest(body))


def check_snapshot(data,base):
    if base.dataset_hash!=dataset_hash(data) or base.snapshot_id!=digest(base.model_dump(mode='json',exclude={'snapshot_id'})):
        raise ValueError('Baseline snapshot does not match its sample version or action checksum. Reload the baseline.')


def normalize(data,definition):
    # All outputs are new objects; shared sample inputs are never mutated.
    d=definition.model_copy(deep=True)
    start=data.settings.as_of;end=start+timedelta(days=55)
    products={p.sku:p for p in data.products};suppliers={s.supplier_id for s in data.suppliers}
    stores={l.location_id for l in data.locations if l.kind=='store'}
    seen=set()
    def span(a,b):
        if not start<=a<=b<=end:raise ValueError('Effective dates must lie within the complete 56-day horizon.')
    for u in d.uplifts:
        span(u.start,u.end)
        valid={'sku':set(products),'category':{p.category for p in data.products},'store':stores}
        if u.scope_id not in valid[u.scope]:raise ValueError('Unknown demand scope identifier.')
        for a in data.assortment:
            if matches(u,products[a.sku],a.location_id):
                for i in range((u.end-u.start).days+1):
                    key=a.sku,a.location_id,u.start+timedelta(days=i)
                    if key in seen:raise ValueError('Overlapping demand changes affect the same SKU/store/day.')
                    seen.add(key)
    seen=set()
    orders={o.external_id:o for o in data.open_orders}
    for change in d.delays:
        if change.supplier_id not in suppliers or change.supplier_id in seen:raise ValueError('Unknown or repeated delayed supplier.')
        seen.add(change.supplier_id)
        if not change.future_paths and not change.existing_order_ids:raise ValueError('Select existing orders or future purchasing paths for the delay.')
        if len(set(change.existing_order_ids))!=len(change.existing_order_ids):raise ValueError('Duplicate existing order selection.')
        for oid in change.existing_order_ids:
            if oid not in orders or orders[oid].supplier_id!=change.supplier_id or orders[oid].status=='received':raise ValueError('Delay must select unreceived orders belonging to that supplier.')
        change.existing_order_ids.sort()
    seen=set()
    for change in d.availability:
        span(change.start,change.end)
        if change.supplier_id not in suppliers:raise ValueError('Unknown availability supplier.')
        for i in range((change.end-change.start).days+1):
            key=change.supplier_id,change.start+timedelta(days=i)
            if key in seen:raise ValueError('Overlapping remaining-availability changes.')
            seen.add(key)
    seen=set();weeks={b.week_start for b in data.budgets}
    for f in d.funding:
        if f.week_start not in weeks or f.week_start in seen:raise ValueError('Unknown or repeated funding week.')
        if f.commitment is None and f.payment is None:raise ValueError('Specify a commitment limit or payment ceiling.')
        for amount in (f.commitment,f.payment):
            if amount is not None and abs(amount*100-round(amount*100))>1e-7:raise ValueError('Funding amounts must use SAR-cent precision.')
        seen.add(f.week_start)
    for field in ('uplifts','delays','availability','funding'):
        setattr(d,field,sorted(getattr(d,field),key=lambda x:json.dumps(x.model_dump(mode='json'),sort_keys=True)))
    return d


def matches(u,product,location):
    return {'sku':product.sku,'category':product.category,'store':location}[u.scope]==u.scope_id


def transform(data,definition):
    definition=normalize(data,definition);changed=data.model_copy(deep=True);changes=[]
    end=data.settings.as_of+timedelta(days=55)
    locations={l.location_id:l for l in changed.locations}
    for delay in definition.delays:
        for order in changed.open_orders:
            if order.external_id in delay.existing_order_ids:
                arrival=order.arrival_date+timedelta(days=delay.days)
                while arrival.weekday() not in locations[order.destination].open_weekdays:arrival+=timedelta(days=1)
                if arrival>end:raise ValueError('Delayed existing receipt exceeds day 56; requested delay is unsupported.')
                changes.append(f'{order.external_id}: receipt {order.arrival_date} → {arrival}; fixed payables unchanged.')
                order.arrival_date=arrival
        if delay.future_paths:
            for offer in changed.supplier_offers:
                if offer.supplier_id==delay.supplier_id:
                    if offer.lead_time_days+delay.days>14:raise ValueError('Delayed future lead time exceeds the supported 14-day offer envelope.')
                    offer.lead_time_days+=delay.days
            changes.append(f'{delay.supplier_id}: all new purchasing paths ordered from {data.settings.as_of} through {end} have +{delay.days} lead days; receiving calendars and receipt-relative balances apply.')
    for change in definition.availability:
        for row in changed.supplier_capacity:
            if row.supplier_id==change.supplier_id and change.start<=row.dispatch_date<=change.end:
                row.available_units=floor(row.available_units*change.remaining_fraction)
        changes.append(f'{change.supplier_id}: {100*change.remaining_fraction:g}% remaining availability for new purchases dispatched {change.start}–{change.end}; confirmed inbound unchanged.')
    for f in definition.funding:
        b=next(b for b in changed.budgets if b.week_start==f.week_start)
        if f.commitment is not None:b.new_commitment_cap=f.commitment
        if f.payment is not None:b.payment_ceiling=f.payment
        changes.append(f'Week {f.week_start}: commitment {b.new_commitment_cap:g} SAR; payments {b.payment_ceiling:g} SAR; existing obligations retained once.')
    for u in definition.uplifts:changes.append(f'{u.scope} {u.scope_id}: +{u.percent:g}% {u.start}–{u.end}, once on expected demand; historical evaluation unchanged.')
    return changed,definition,changes


def adjust_forecasts(data,definition,prepared):
    demand,buffers,traces,failures=prepared
    demand={key:list(values) for key,values in demand.items()};buffers=dict(buffers)
    traces=[t.model_copy(deep=True) for t in traces];products={p.sku:p for p in data.products}
    for u in definition.uplifts:
        for key,values in demand.items():
            if matches(u,products[key[0]],key[1]):
                for i in range(56):
                    if u.start<=data.settings.as_of+timedelta(days=i)<=u.end:values[i]*=1+u.percent/100
    for t in traces:
        key=t.sku,t.location_id
        if t.buffer.method=='days_of_demand':
            buffers[key]=sum(demand[key][:28])/28*data.settings.fallback_buffer_days
            t.buffer.units=buffers[key]
    return demand,buffers,traces,failures


def assumptions(data,prepared):
    d,b,_,_=prepared
    return digest({'dataset':dataset_hash(data),'demand':{'/'.join(k):v for k,v in d.items()},'buffers':{'/'.join(k):v for k,v in b.items()}})


def frozen_actions(data,definition,actions):
    result=actions.model_copy(deep=True);ctx=Inputs(data,{},{});
    delayed={d.supplier_id for d in definition.delays if d.future_paths}
    for p in result.purchases:
        if p.supplier_id in delayed:
            offer=next(o for o in data.supplier_offers if o.offer_id==p.offer_id)
            timing=ctx.timing(offer,(p.order_date-data.settings.as_of).days)
            if timing is None:raise ValueError('A frozen purchase receipt would exceed day 56; requested delay is unsupported.')
            p.dispatch_date,p.arrival_date=ctx.day(timing[0]),ctx.day(timing[1])
    return result


def outcome(policy,hash_,actions,ledger,status,data,failures=(),explanations=(),stages=()):
    failures=list(failures)+ledger.failures
    feasible=ledger.feasible and not failures
    return Outcome(policy=policy,assumptions_hash=hash_,action_hash=digest(actions),**actions.model_dump(),feasible=feasible,
        status=status if feasible else 'invalid_plan',summary=ledger.summary if feasible else None,cash=ledger.cash,
        failures=failures,shortages=[s for s in ledger.service if s.unmet+s.tail_unmet>0] if feasible else [],explanations=list(explanations),stages=list(stages),
        evidence_targets=purchase_evidence_targets(data,ledger,actions.purchases) if feasible else [])


def capture(data,request):
    from types import SimpleNamespace
    if dataset_hash(data)!=request.dataset_hash:raise ValueError('Sample version changed; recalculate the baseline.')
    started=perf_counter();prepared=network_forecasts(data,started+30)
    if prepared[3]:raise ValueError('Baseline forecast unavailable.')
    actions=Actions(purchases=request.purchases,movements=request.movements)
    ledger=replay(data,*prepared[:2],actions.purchases,actions.movements)
    if not ledger.feasible:raise ValueError('Captured baseline actions fail independent replay.')
    result=SimpleNamespace(proposed=SimpleNamespace(purchases=actions.purchases,movements=actions.movements,replay=ledger),status='validated_snapshot',exceptions=[],stages=[])
    return baseline_result(request.size,data,result,started)


def baseline_result(size,data,result=None,started=None,validated_issues=None):
    started=perf_counter() if started is None else started
    result=plan(data,validated_issues=validated_issues) if result is None else result
    if not result.proposed or not result.proposed.replay.feasible:raise ValueError('Sample baseline is not independently feasible.')
    base=snapshot(size,data,actions_of(result.proposed))
    # Baseline identifier is the immutable original assumption/action version.
    original=outcome('original',base.dataset_hash,actions_of(result.proposed),result.proposed.replay,result.status,data,explanations=result.exceptions,stages=result.stages)
    orders=[o for o in data.open_orders if o.status!='received']
    supplier_options=[]
    for supplier in sorted(data.suppliers,key=lambda row:row.supplier_id):
        existing=sorted(o.external_id for o in orders if o.supplier_id==supplier.supplier_id)
        future=any(o.supplier_id==supplier.supplier_id for o in data.supplier_offers) and any(
            row.supplier_id==supplier.supplier_id and data.settings.as_of<=row.dispatch_date<=data.settings.as_of+timedelta(days=55)
            for row in data.supplier_capacity)
        supplier_options.append(SupplierOption(supplier_id=supplier.supplier_id,name=supplier.name,
            existing_order_ids=existing,future_paths=future))
    return BaselineResult(baseline=base,original=original,as_of=data.settings.as_of,suppliers=[s.supplier_id for s in data.suppliers],
        supplier_options=supplier_options,categories=sorted({p.category for p in data.products}),existing_orders=[{'id':o.external_id,'supplier':o.supplier_id,'arrival':str(o.arrival_date)} for o in orders],
        weeks=[Funding(week_start=b.week_start,commitment=b.new_commitment_cap,payment=b.payment_ceiling) for b in data.budgets],elapsed_ms=(perf_counter()-started)*1000)


def prepare(data,request):
    check_snapshot(data,request.baseline)
    changed,definition,changes=transform(data,request.scenario)
    deadline=perf_counter()+30
    original=network_forecasts(data,deadline)
    if original[3]:raise ValueError('Baseline forecast unavailable.')
    raw=network_forecasts(changed,deadline) if any(d.future_paths for d in definition.delays) else original
    if raw[3]:raise ValueError('Scenario exceeds supported forecasting/protection envelope: '+raw[3][0].message)
    adjusted=adjust_forecasts(changed,definition,raw)
    hash_=digest({'baseline':request.baseline.snapshot_id,'definition':definition.model_dump(mode='json'),'assumptions':assumptions(changed,adjusted)})
    return changed,definition,changes,original,adjusted,hash_


def delta(before,after):
    keys=('fill_pct','fulfilled','unmet','commitments','payments','ending_inventory_investment','movement_expense','tail_unmet')
    return {k:(getattr(after.summary,k)-getattr(before.summary,k) if before.summary and after.summary and getattr(before.summary,k) is not None and getattr(after.summary,k) is not None else None) for k in keys}


def action_diff(before,after):
    changes=[]
    for kind,field in [('purchase','purchases'),('movement','movements')]:
        def key(a):return (a.sku,a.supplier_id,a.offer_id,a.destination,str(a.order_date)) if kind=='purchase' else (a.sku,a.source,a.destination,str(a.dispatch_date))
        old={key(a):a for a in getattr(before,field)};new={key(a):a for a in getattr(after,field)}
        for k in sorted(old.keys()|new.keys()):
            a,b=old.get(k),new.get(k)
            if a and b and a.model_dump(exclude={'action_id','reason'})==b.model_dump(exclude={'action_id','reason'}):continue
            changes.append(ActionChange(kind=kind,change='added' if not a else 'removed' if not b else 'changed',business_key='/'.join(k),before=a,after=b))
    return changes


def forecast_versions(prepared):
    demand,_,traces,_=prepared
    return {f'{t.sku}/{t.location_id}':digest({'input':t.input_hash,'method':t.method,'buffer':t.buffer.model_dump(mode='json'),'demand':demand[t.sku,t.location_id]}) for t in traces}


def compare(data,request):
    start=perf_counter();changed,definition,changes,base_forecasts,scenario_forecasts,hash_=prepare(data,request)
    original_actions=Actions(purchases=request.baseline.purchases,movements=request.baseline.movements)
    original_replay=replay(data,*base_forecasts[:2],original_actions.purchases,original_actions.movements)
    if not original_replay.feasible:raise ValueError('Baseline actions fail independent replay under original assumptions. Reload baseline.')
    frozen=frozen_actions(changed,definition,original_actions)
    frozen_replay=replay(changed,*scenario_forecasts[:2],frozen.purchases,frozen.movements)
    planned=plan(changed,runtime_seconds=max(.01,30-(perf_counter()-start)),prepared_forecasts=scenario_forecasts)
    new=actions_of(planned.proposed) if planned.proposed else Actions()
    new_replay=planned.proposed.replay if planned.proposed else replay(changed,*scenario_forecasts[:2],include_stock=False)
    original=outcome('original',request.baseline.dataset_hash,original_actions,original_replay,'validated_snapshot',data)
    frozen_out=outcome('frozen',hash_,frozen,frozen_replay,'validated_frozen',changed)
    replanned=outcome('replanned',hash_,new,new_replay,planned.status,changed,planned.failures if planned.proposed is None else (),planned.exceptions,planned.stages)
    return ScenarioResult(baseline_id=request.baseline.snapshot_id,scenario_hash=hash_,definition=definition,changes=changes,
        original=original,frozen=frozen_out,replanned=replanned,shock_delta=delta(original,frozen_out),replan_delta=delta(frozen_out,replanned),
        forecast_versions=forecast_versions(scenario_forecasts),action_changes=action_diff(frozen,new),elapsed_ms=(perf_counter()-start)*1000)


def detail(data,request):
    start=perf_counter();changed,definition,_,original,adjusted,hash_=prepare(data,request)
    if request.expected_scenario_hash and request.expected_scenario_hash!=hash_:raise ValueError('Scenario detail assumptions changed; rerun the scenario.')
    actions=Actions(purchases=request.baseline.purchases,movements=request.baseline.movements)
    selected=data if request.policy=='original' else changed
    prepared=original if request.policy=='original' else adjusted
    if request.policy=='frozen':actions=frozen_actions(changed,definition,actions)
    if request.policy=='replanned':
        if request.actions is None:raise ValueError('Replanned detail requires the calculated action snapshot.')
        actions=request.actions
    if request.expected_action_hash and request.expected_action_hash!=digest(actions):raise ValueError('Action snapshot changed; rerun calculation.')
    if request.action_id and request.action_id not in {a.action_id for a in actions.purchases+actions.movements}:raise ValueError('Unknown action.')
    trace=next((t for t in prepared[2] if t.sku==request.sku and t.location_id==request.location_id),None)
    if trace is None:raise ValueError('Select a ranged SKU/store forecast.')
    projected=selected.model_copy(update={'demand_history':[r for r in selected.demand_history if (r.sku,r.location_id)==(request.sku,request.location_id)],'settings':selected.settings.model_copy(update={'protection_days':trace.buffer.protection_days})})
    fc=forecast(projected,request.sku,request.location_id)
    values=prepared[0][request.sku,request.location_id]
    adjustments=[Adjustment(day=p.day,original=p.forecast_units,adjusted=values[i],reason='Dated scenario uplift applied once after the underlying forecast.') for i,p in enumerate(fc.forecast) if p.forecast_units!=values[i]]
    ledger=replay(selected,*prepared[:2],actions.purchases,actions.movements)
    purchases=[p for p in actions.purchases if p.sku==request.sku];moves=[m for m in actions.movements if m.sku==request.sku]
    references={p.action_id for p in purchases}|{f'{m.source}-{m.destination}-{m.dispatch_date}' for m in moves}
    existing={p.external_id for p in selected.payables if p.linked_external_id in {o.external_id for o in selected.open_orders+selected.open_transfers if o.sku==request.sku}}
    return ScenarioDetail(baseline_id=request.baseline.snapshot_id,scenario_hash=hash_,assumptions_hash=request.baseline.dataset_hash if request.policy=='original' else hash_,action_hash=digest(actions),policy=request.policy,
        feasible=ledger.feasible,failures=ledger.failures,forecast=fc,forecast_version=forecast_versions(prepared)[f'{request.sku}/{request.location_id}'],policy_buffer=trace.buffer,adjustments=adjustments,
        stock=[r for r in ledger.stock if r.sku==request.sku] if ledger.feasible else [],cash=ledger.cash,payments=[p for p in ledger.payments if p.reference in references|existing],
        purchases=purchases,movements=moves,confirmed_receipts=[{'id':o.external_id,'destination':o.destination,'arrival':str(o.arrival_date),'units':str(o.remaining_units)} for o in selected.open_orders+selected.open_transfers if o.sku==request.sku and o.status!='received'],
        shortages=[s for s in ledger.service if s.sku==request.sku] if ledger.feasible else [],elapsed_ms=(perf_counter()-start)*1000)
