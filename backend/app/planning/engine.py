"""Orchestration only: real forecasts -> benchmark/joint model -> independent replay."""
from backend.app.diagnostics import timed, measure
from hashlib import sha256
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from math import ceil
from time import perf_counter
from uuid import uuid4
from backend.app.data.validation import validate_dataset
from backend.app.planning.contracts import PlanResult, PolicyResult, Failure, SolverStage
from backend.app.planning.inputs import Inputs, network_forecasts, planning_input_failures
from backend.app.planning.benchmark import benchmark
from backend.app.planning.evidence import purchase_evidence_targets
from backend.app.simulation.replay import replay, EPS, cents, week

JOINT_BUDGET_SECONDS = 2.0
FULL_SAMPLE_JOINT_BUDGET_SECONDS = 0.0

ASSUMPTIONS = [
    'The live joint challenger has a two-second fixture sub-budget within the 30-second request limit. At 240 series its live sub-budget is unavailable because measured preparation and validated fallback work consume the 10-second response target. Incomplete or unattempted solves use the independently validated deterministic benchmark; no optimality is claimed.',
    'Receive, serve local expected demand, dispatch, then close stock. Unserved demand is lost, never backlogged.',
    'Only days 1–7 are release candidates. Later actions remain planned; days 29–56 depend on provisional forecasts.',
    'Store buffers use the unchanged Pass 1 evaluator at calendar-adjusted review plus replenishment protection periods. No independent DC buffer or retail demand is added.',
    'Donor reserve uses next-seven-day maximum cumulative net demand plus buffer, only confirmed receipts. Past day 56, repeat the final forecast week.',
    'SupplierCapacity is remaining availability for new orders. Existing transfers consume lane capacity; their unpaid fees must already be in Payables.',
    'Orders dispatch on the first allowed day on/after order; receipt follows lead time and the DC receiving calendar. Transfers have exact lane transit days.',
    'SAR line amounts and deposits round half-up to cents; balance is line value minus deposit. Transfer fee applies once per source/destination/dispatch date.',
    'Commitment caps are remaining authority for new orders. Payment ceilings include existing obligations, deposits, balances and new movement fees through at least day 90.',
    'Projected unit fill measures modeled fulfilled units / expected demand; it is not achieved service. Revenue exposure is modeled, not proven lost revenue.',
    'Inventory investment uses declared opening/receipt costs and weighted-average donor value on transfer, including blocked/reserved stock. No tax, revenue cash or receivables forecast.',
    'Benchmark orders up to review/protection needs, allocates by earliest shortage then must-stock/class priority and stable SKU/store IDs. Supplier MOV can conservatively prevent a single-line benchmark order.',
]


def joint_budget_seconds(series_count):
    return JOINT_BUDGET_SECONDS if series_count <= 40 else FULL_SAMPLE_JOINT_BUDGET_SECONDS


def plan(data, runtime_seconds=30, *, prepared_forecasts=None, validated_issues=None, review=None):
    start=perf_counter(); deadline=start+runtime_seconds
    kwargs=dict(run_id=str(uuid4()),input_hash=sha256(data.model_dump_json().encode()).hexdigest(),dataset_id=data.dataset_id,
        synthetic=data.synthetic,as_of=data.settings.as_of,payment_through=max([data.settings.as_of+timedelta(days=89)]+[p.due_date for p in data.payables]),assumptions=ASSUMPTIONS)
    kwargs['challenger_budget_seconds']=joint_budget_seconds(len(data.assortment))
    issues=validate_dataset(data) if validated_issues is None else validated_issues
    failures=planning_input_failures(data)
    if any(i.severity=='error' for i in issues) or failures:
        return PlanResult(**kwargs,status='invalid_inputs',issues=issues,failures=failures,elapsed_ms=(perf_counter()-start)*1000)
    try:
        demand,buffers,trace,failures=network_forecasts(data,deadline) if prepared_forecasts is None else prepared_forecasts
    except TimeoutError:
        failures=[Failure(code='forecast_runtime',message='Network forecast exceeded the overall planning budget. No partial network plan is executable.')]
        trace=[]
    if failures:
        return PlanResult(**kwargs,status='invalid_inputs',forecasts=trace,issues=issues,failures=failures,elapsed_ms=(perf_counter()-start)*1000)
    ctx=Inputs(data,demand,buffers,review)
    def check_review(ledger,purchases,movements):
        ledger.failures.extend(ctx.review.failures(purchases,movements))
        ledger.feasible=not ledger.failures
        return ledger
    no=replay(data,demand,buffers,include_stock=False)
    try:
        bp,bm=benchmark(ctx,deadline-1)
    except TimeoutError:
        bp,bm=[],[]
        ctx.explain('BENCHMARK_TIME_LIMIT','Benchmark exhausted the shared runtime budget; no partial recommendation is accepted.')
    br=check_review(replay(data,demand,buffers,bp,bm,include_stock=False),bp,bm)
    stages=[]
    solver_failure=None
    # Leave time for independent replay, serialization and safe fallback after solver termination.
    joint_budget = joint_budget_seconds(len(ctx.assortment))
    solve_deadline=min(deadline-2,perf_counter()+joint_budget)
    if joint_budget > 0 and perf_counter()<solve_deadline:
        from backend.app.planning.optimizer import optimize
        try:
            p,m,stages=optimize(ctx,solve_deadline)
            candidate=no  # Incomplete incumbents are never selected or replayed.
        except RuntimeError:
            p,m,candidate=[],[],no
            stages=[SolverStage(name='joint_model',status='error',elapsed_ms=0)]
            solver_failure=Failure(code='SOLVER_EXECUTION_ERROR',message='The joint optimizer could not complete because its solver runtime failed. No partial optimizer actions were accepted.')
    else:
        p,m=[],[];candidate=no
        stages=[SolverStage(name='joint_model',status='not_attempted' if joint_budget <= 0 else 'time_limit',elapsed_ms=0)]
    priorities=[priority for priority in ('must_stock','A','B','C')
        if any(a.must_stock if priority=='must_stock' else not a.must_stock and a.service_class==priority
               for a in ctx.assortment.values())]
    required=[f'{window}_{priority}' for window in ('visible','tail') for priority in priorities]
    required+=['weekly_buffer_deficit','commitment_movement_holding','stable_action_ties']
    complete=([s.name for s in stages]==required and
        all(s.status=='optimal' and (s.gap is None or s.gap==0) for s in stages))
    if not complete and all(s.status=='optimal' for s in stages):
        stages.append(SolverStage(name='joint_completion_check',status='incomplete',elapsed_ms=0))
    if complete:
        candidate=check_review(replay(data,demand,buffers,p,m,include_stock=False),p,m)
    # An incomplete incumbent is deliberately not selected: its actions can
    # depend on solver timing. The benchmark is calculated before the challenger.
    if not complete or not candidate.feasible:
        complete=False
        if br.feasible and (review is not None or not no.feasible or _score(br,ctx)[:8]<=_score(no,ctx)[:8]):
            p,m,candidate=bp,bm,br
            fallback='benchmark'
        elif no.feasible and not ctx.review.failures([],[]):
            p,m,candidate=[],[],no
            fallback='no_new_actions'
        else:
            p,m,candidate=bp,bm,br
            fallback='invalid'
        stages.append(SolverStage(name='independent_fallback',status=fallback,elapsed_ms=0))
    verified=check_review(replay(data,demand,buffers,p,m),p,m)
    exceptions=_explanations(ctx,verified,p,m,complete,solver_failure,bp,bm)
    # Compact ledgers: retain the proposed daily series; comparisons retain totals and service detail.
    status=('feasible' if complete else 'feasible_fallback') if verified.feasible else 'invalid_plan'
    kwargs['payment_through']=max(kwargs['payment_through'],max((x.due_date for x in verified.payments),default=kwargs['payment_through']))
    targets=purchase_evidence_targets(data,verified,p)
    return PlanResult(**kwargs,status=status,proposed=PolicyResult(name='Joint staged plan' if complete else ('Validated constrained plan' if p==bp and m==bm else 'Validated no-new-action projection'),purchases=p,movements=m,replay=verified,evidence_targets=targets),
        benchmark=PolicyResult(name='Constrained order-up-to benchmark',purchases=bp,movements=bm,replay=br),
        no_action=PolicyResult(name='No new actions',purchases=[],movements=[],replay=no),forecasts=trace,stages=stages,
        issues=issues,failures=verified.failures,exceptions=exceptions,elapsed_ms=(perf_counter()-start)*1000)


@timed('explanations')
def _explanations(ctx,verified,p,m,complete,solver_failure,bp,bm):
    exceptions=list(ctx.exceptions.values()) if p==bp and m==bm else []
    if solver_failure is not None:
        exceptions.append(solver_failure)
    if complete:
        exceptions.extend(_shortage_causes(ctx,verified,p,m))
    for service in verified.service:
        if service.unmet+service.tail_unmet>EPS:
            exceptions.append(Failure(code='DATED_SUPPLY_SHORTFALL',message=f'{service.unmet:.1f} visible and {service.tail_unmet:.1f} provisional-tail units remain uncovered after dated receipts, allocations and funding limits.',sku=service.sku,location_id=service.location_id))
            service.reason_codes=sorted({e.code for e in exceptions if (e.sku is None or e.sku==service.sku) and (e.location_id is None or e.location_id==service.location_id)})
    for move in m:
        opposite=next((t for t in m if t.sku==move.sku and t.source==move.destination and t.destination==move.source and t.dispatch_date<move.dispatch_date),None)
        if opposite:
            exceptions.append(Failure(code='LATER_RETURN_MOVEMENT',message=f'Stock moved on {opposite.dispatch_date} returns on {move.dispatch_date}; it was retained only under dated demand/buffer objectives and rechecked for donor protection. Inspect the daily ledger.',sku=move.sku,location_id=move.source,day=move.dispatch_date,action_id=move.action_id))
    return exceptions


def _score(result,ctx):
    if not result.feasible:return (float('inf'),)
    values=[]
    for tail in (False,True):
        for priority in ('must_stock','A','B','C'):
            total=0.
            for loc in ctx.locations:
                for cls in 'ABC':
                    members=[s for s in result.service if s.location_id==loc and s.service_class==cls and (s.must_stock if priority=='must_stock' else not s.must_stock and cls==priority)]
                    demand=sum(sum(ctx.demand[s.sku,s.location_id][28:]) if tail else s.demand for s in members)
                    unmet=sum(s.tail_unmet if tail else s.unmet for s in members)
                    total+=max(0.,unmet-(1-ctx.data.settings.class_targets[cls])*demand)
            values.append(round(total,5))
    values.extend([result.summary.weekly_buffer_deficit,result.summary.commitments+result.summary.movement_expense])
    return tuple(values)


def _shortage_causes(ctx, result, purchases, movements):
    """Explain each shortage interval using supply that could arrive by then.

    The replay ledger is authoritative for shortage timing and remaining stock.
    A saturated constraint is reported as a cause only when every timely path
    fails it; otherwise the result is explicitly an observed, uncertain tradeoff.
    """
    causes=[];cash={row.week_start:row for row in result.cash}
    stock={(row.sku,row.location_id,row.day):row for row in result.stock}
    purchased={};shared_used={};ordered_value={};lane_used={}
    for action in purchases:
        key=action.supplier_id,action.sku,action.dispatch_date
        purchased[key]=purchased.get(key,0)+action.units
        ordered_value[action.supplier_id,action.order_date]=ordered_value.get((action.supplier_id,action.order_date),0)+cents(action.value)
        supplier=ctx.suppliers[action.supplier_id]
        amount=action.units*(ctx.products[action.sku].volume_per_unit if supplier.shared_capacity_unit=='volume' else 1)
        shared_used[action.supplier_id,action.dispatch_date]=shared_used.get((action.supplier_id,action.dispatch_date),0)+amount
    for action in movements:
        lane_used[action.source,action.destination,action.dispatch_date]=lane_used.get((action.source,action.destination,action.dispatch_date),0)+action.units

    def intervals(rows):
        # Daily evidence avoids attributing a later-arriving path to demand
        # that was already lost earlier in a longer stockout interval.
        return [[row] for row in sorted(rows,key=lambda value:value.day)]

    def path_dates(offer,lane,order_index):
        timing=ctx.timing(offer,order_index)
        if timing is None:return None
        supplier_dispatch,dc_index=timing
        lane_dispatch=ctx.day(dc_index)
        for _ in range(28):
            arrival=lane_dispatch+timedelta(days=lane.transit_days)
            if (lane_dispatch.weekday() in lane.dispatch_weekdays
                    and lane_dispatch.weekday() in ctx.locations[lane.source].open_weekdays
                    and arrival.weekday() in ctx.locations[lane.destination].open_weekdays):
                return ctx.day(supplier_dispatch),ctx.day(dc_index),lane_dispatch,arrival
            lane_dispatch+=timedelta(days=1)
        return None

    def money_evidence(offer,order_day,dc_arrival,lane_dispatch,lane,units):
        value=cents(Decimal(str(offer.price_per_base_unit))*units)
        deposit=int((Decimal(value)*Decimal(str(offer.deposit_fraction))).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
        flows={}
        for due,amount in [(order_day,deposit),(dc_arrival+timedelta(days=offer.balance_days_after_receipt),value-deposit)]:
            flows[week(due)]=flows.get(week(due),0)+amount
        group=lane.source,lane.destination,lane_dispatch
        existing_group=group in lane_used or any(t.status=='confirmed' and (t.source,t.destination,t.dispatch_date)==group for t in ctx.data.open_transfers)
        fee=0 if existing_group else cents(lane.grouped_dispatch_fee)
        flows[week(lane_dispatch)]=flows.get(week(lane_dispatch),0)+fee
        payment_ok=all((row:=cash.get(funding_week)) is not None and row.payment_headroom is not None
            and cents(row.payment_headroom)>=amount for funding_week,amount in flows.items())
        order_cash=cash.get(week(order_day));commitment_ok=bool(order_cash and order_cash.commitment_headroom is not None
            and cents(order_cash.commitment_headroom)>=value)
        fee_cash=cash.get(week(lane_dispatch));transfer_ok=bool(fee_cash and fee_cash.transfer_headroom is not None
            and cents(fee_cash.transfer_headroom)>=fee)
        return value,flows,commitment_ok,payment_ok,transfer_ok

    for service in result.service:
        if service.unmet+service.tail_unmet<=EPS:
            continue
        shortage_rows=[row for row in result.stock if row.sku==service.sku and row.location_id==service.location_id and row.unmet>EPS]
        if not shortage_rows:continue
        offers=[o for o in ctx.data.supplier_offers if o.sku==service.sku]
        inbound_lanes=[lane for lane in ctx.data.transfer_lanes if lane.destination==service.location_id and service.sku in lane.allowed_skus]
        lanes=[lane for lane in inbound_lanes if lane.source==ctx.dc]
        for interval in intervals(shortage_rows):
            first,last=interval[0].day,interval[-1].day;quantity=sum(row.unmet for row in interval)
            span=str(first) if first==last else f'{first} to {last}'
            transfer_options=[]
            for lane in inbound_lanes:
                for i in range(max(0,(first-ctx.start).days+1)):
                    dispatch=ctx.day(i);arrival=dispatch+timedelta(days=lane.transit_days)
                    if arrival>first or dispatch.weekday() not in lane.dispatch_weekdays or dispatch.weekday() not in ctx.locations[lane.source].open_weekdays or arrival.weekday() not in ctx.locations[lane.destination].open_weekdays:continue
                    donor=stock.get((service.sku,lane.source,dispatch));available=max(0.,donor.closing-(ctx.reserve.get((service.sku,lane.source,i),0) if ctx.locations[lane.source].kind=='store' else 0)) if donor else 0
                    headroom=lane.capacity_units-ctx.lane_used[lane.source,lane.destination,i]-lane_used.get((lane.source,lane.destination,dispatch),0)
                    if min(available,headroom)>=lane.pack_units:transfer_options.append((dispatch,arrival,available,headroom,lane))
            candidates=[];future_arrivals=[]
            for offer in offers:
                base=max(offer.case_size,ceil(offer.moq_units/offer.case_size)*offer.case_size)
                for lane in lanes:
                    for i in range(56):
                        dates=path_dates(offer,lane,i)
                        if dates is None:continue
                        supplier_dispatch,dc_arrival,lane_dispatch,store_arrival=dates
                        future_arrivals.append(store_arrival)
                        if store_arrival>last:continue
                        supplier=ctx.suppliers[offer.supplier_id];existing=ordered_value.get((offer.supplier_id,ctx.day(i)),0)
                        unit_price=cents(offer.price_per_base_unit);minimum_gap=max(0,cents(supplier.minimum_order_value)-existing)
                        required=max(base,ceil(minimum_gap/max(unit_price,1)/offer.case_size)*offer.case_size)
                        evidence=[]
                        for units in (base,required):
                            value,flows,commitment_ok,payment_ok,transfer_ok=money_evidence(offer,ctx.day(i),dc_arrival,lane_dispatch,lane,units)
                            sku_headroom=ctx.capacity.get((offer.supplier_id,offer.sku,(supplier_dispatch-ctx.start).days),0)-purchased.get((offer.supplier_id,offer.sku,supplier_dispatch),0)
                            multiplier=ctx.products[offer.sku].volume_per_unit if supplier.shared_capacity_unit=='volume' else 1
                            shared_headroom=supplier.shared_daily_capacity-shared_used.get((offer.supplier_id,supplier_dispatch),0)
                            lane_headroom=lane.capacity_units-ctx.lane_used[lane.source,lane.destination,(lane_dispatch-ctx.start).days]-lane_used.get((lane.source,lane.destination,lane_dispatch),0)
                            evidence.append(dict(units=units,value=value,flows=flows,commitment=commitment_ok,payment=payment_ok,transfer=transfer_ok,
                                sku_capacity=sku_headroom+EPS>=units,shared_capacity=shared_headroom+EPS>=units*multiplier,lane_capacity=lane_headroom+EPS>=lane.pack_units))
                        candidates.append((offer,ctx.day(i),store_arrival,base,required,evidence))
            scope=dict(sku=service.sku,location_id=service.location_id,day=first)
            if transfer_options:
                dispatch,arrival,available,headroom,_=max(transfer_options,key=lambda item:min(item[2],item[3]))
                causes.append(Failure(code='TRANSFER_ALTERNATIVE_REQUIRES_REOPTIMIZATION',message=f'{quantity:.1f} units were short on {span}; an observed transfer option could dispatch on {dispatch} and arrive {arrival}, with {available:.1f} donor units and {headroom:.1f} lane units available. This is an alternative, not proof that allocation caused the shortage.',**scope))
            if not candidates:
                earliest=min(future_arrivals,default=None)
                detail=f'; the earliest valid purchase-to-store path arrives {earliest}' if earliest else '; no valid path exists in the modeled horizon'
                causes.append(Failure(code='SUPPLY_TIMING_LIMITATION',message=f'{quantity:.1f} units were short on {span}{detail}. This observed timing limitation prevents a new purchase from explaining away this interval.',**scope))
                continue
            required_checks=[entry[5][1] for entry in candidates]
            if all(not item['sku_capacity'] for item in required_checks):
                causes.append(Failure(code='DATED_SUPPLIER_SKU_CAPACITY',message=f'{quantity:.1f} units were short on {span}; every purchase path arriving by {last} lacked capacity for its required executable quantity.',**scope))
            if all(not item['shared_capacity'] for item in required_checks):
                causes.append(Failure(code='SHARED_SUPPLIER_CAPACITY',message=f'{quantity:.1f} units were short on {span}; every timely path lacked shared supplier capacity for its required executable quantity.',**scope))
            if all(not item['commitment'] for item in required_checks):
                smallest=min(item['value'] for item in required_checks)/100
                best=max((cash.get(week(entry[1])).commitment_headroom or 0) for entry in candidates if cash.get(week(entry[1])))
                causes.append(Failure(code='PURCHASE_COMMITMENT_AUTHORITY',message=f'{quantity:.1f} units were short on {span}; every timely executable line required at least SAR {smallest:.2f} against at most SAR {best:.2f} remaining weekly commitment authority.',**scope))
            if all(not item['payment'] for item in required_checks):
                requirement=min(max((sum(amount for funding,amount in item['flows'].items() if funding==target) for target in item['flows']),default=0) for item in required_checks)/100
                causes.append(Failure(code='PURCHASE_PAYMENT_CAPACITY',message=f'{quantity:.1f} units were short on {span}; every timely path exceeded at least one weekly payment limit. The smallest grouped same-week requirement was SAR {requirement:.2f}; deposits, balances, existing obligations and transfer fees were counted once by funding week.',**scope))
            minimum_blocked=[]
            for offer,order_day,arrival,base,required,evidence in candidates:
                base_ok=all(evidence[0][key] for key in ('commitment','payment','transfer','sku_capacity','shared_capacity','lane_capacity'))
                required_ok=all(evidence[1][key] for key in ('commitment','payment','transfer','sku_capacity','shared_capacity','lane_capacity'))
                if required>base and base_ok and not required_ok:minimum_blocked.append((offer,order_day,base,required,evidence[1]['value']))
            if minimum_blocked and not any(all(item[key] for key in ('commitment','payment','transfer','sku_capacity','shared_capacity','lane_capacity')) for item in required_checks):
                offer,order_day,base,required,value=min(minimum_blocked,key=lambda item:item[4])
                existing=ordered_value.get((offer.supplier_id,order_day),0)/100
                causes.append(Failure(code='GROUPED_SUPPLIER_MINIMUM',message=f'{quantity:.1f} units were short on {span}; a {base}-unit timely line was otherwise feasible, but the supplier/order-date group had SAR {existing:.2f} already and required {required} units (SAR {value/100:.2f}) to satisfy the remaining grouped minimum. The larger qualifying line failed another dated hard limit.',supplier_id=offer.supplier_id,**scope))
            if any(all(item[key] for key in ('commitment','payment','transfer','sku_capacity','shared_capacity','lane_capacity')) for item in required_checks):
                causes.append(Failure(code='UNCERTAIN_SHORTAGE_ATTRIBUTION',message=f'{quantity:.1f} units were short on {span}, while at least one timely incremental supply path passed the tested stock, calendar, capacity, grouped-minimum and funding checks. The shortage reflects the completed plan trade-offs; no single binding cause is proven.',**scope))
    unique={}
    for cause in causes:unique[cause.code,cause.sku,cause.location_id,cause.day]=cause
    return list(unique.values())
