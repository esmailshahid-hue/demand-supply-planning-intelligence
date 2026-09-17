"""Orchestration only: real forecasts -> benchmark/joint model -> independent replay."""
from hashlib import sha256
from datetime import timedelta
from time import perf_counter
from uuid import uuid4
from backend.app.data.validation import validate_dataset
from backend.app.planning.contracts import PlanResult, PolicyResult, Failure, SolverStage
from backend.app.planning.inputs import Inputs, network_forecasts, planning_input_failures, _valid_path_arrival
from backend.app.planning.benchmark import benchmark
from backend.app.simulation.replay import replay, EPS
from backend.app.simulation.replay import week

ASSUMPTIONS = [
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


def plan(data, runtime_seconds=30):
    start=perf_counter(); deadline=start+runtime_seconds
    kwargs=dict(run_id=str(uuid4()),input_hash=sha256(data.model_dump_json().encode()).hexdigest(),dataset_id=data.dataset_id,
        synthetic=data.synthetic,as_of=data.settings.as_of,payment_through=max([data.settings.as_of+timedelta(days=89)]+[p.due_date for p in data.payables]),assumptions=ASSUMPTIONS)
    issues=validate_dataset(data)
    failures=planning_input_failures(data)
    if any(i.severity=='error' for i in issues) or failures:
        return PlanResult(**kwargs,status='invalid_inputs',issues=issues,failures=failures,elapsed_ms=(perf_counter()-start)*1000)
    try:
        demand,buffers,trace,failures=network_forecasts(data,deadline)
    except TimeoutError:
        failures=[Failure(code='forecast_runtime',message='Network forecast exceeded the overall planning budget. No partial network plan is executable.')]
        trace=[]
    if failures:
        return PlanResult(**kwargs,status='invalid_inputs',forecasts=trace,issues=issues,failures=failures,elapsed_ms=(perf_counter()-start)*1000)
    ctx=Inputs(data,demand,buffers)
    no=replay(data,demand,buffers,include_stock=False)
    try:
        bp,bm=benchmark(ctx,deadline-1)
    except TimeoutError:
        bp,bm=[],[]
        ctx.explain('BENCHMARK_TIME_LIMIT','Benchmark exhausted the shared runtime budget; no partial recommendation is accepted.')
    br=replay(data,demand,buffers,bp,bm,include_stock=False)
    stages=[]
    solver_failure=None
    # Leave time for independent replay, serialization and safe fallback after solver termination.
    solve_deadline=deadline-2
    if perf_counter()<solve_deadline:
        from backend.app.planning.optimizer import optimize
        try:
            p,m,stages=optimize(ctx,solve_deadline)
            candidate=replay(data,demand,buffers,p,m,include_stock=False)
        except RuntimeError:
            p,m,candidate=[],[],no
            stages=[SolverStage(name='joint_model',status='error',elapsed_ms=0)]
            solver_failure=Failure(code='SOLVER_EXECUTION_ERROR',message='The joint optimizer could not complete because its solver runtime failed. No partial optimizer actions were accepted.')
    else:
        p,m=[],[];candidate=no
        stages=[SolverStage(name='joint_model',status='time_limit',elapsed_ms=0)]
    complete=bool(stages) and all(s.status=='optimal' for s in stages) and stages[-1].name=='stable_action_ties'
    # No incumbent can displace the independently feasible benchmark just on a solver flag.
    if solver_failure is not None and br.feasible:
        p,m,candidate=bp,bm,br
        complete=False
        stages.append(SolverStage(name='independent_fallback',status='benchmark',elapsed_ms=0))
    elif solver_failure is not None and no.feasible:
        p,m,candidate=[],[],no
        complete=False
        stages.append(SolverStage(name='independent_fallback',status='no_new_actions',elapsed_ms=0))
    elif solver_failure is not None:
        p,m,candidate=[],[],no
        complete=False
        stages.append(SolverStage(name='independent_fallback',status='invalid',elapsed_ms=0))
    elif not candidate.feasible or (not complete and _score(br,ctx)<_score(candidate,ctx)):
        p,m,candidate=bp,bm,br
        complete=False
        stages.append(SolverStage(name='independent_fallback',status='benchmark' if br.feasible else 'invalid',elapsed_ms=0))
    if not candidate.feasible and no.feasible:
        p,m,candidate=[],[],no
        complete=False
        stages.append(SolverStage(name='independent_fallback',status='no_new_actions',elapsed_ms=0))
    verified=replay(data,demand,buffers,p,m)
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
    # Compact ledgers: retain the proposed daily series; comparisons retain totals and service detail.
    status=('feasible' if complete else 'feasible_fallback') if verified.feasible else 'invalid_plan'
    kwargs['payment_through']=max(kwargs['payment_through'],max((x.due_date for x in verified.payments),default=kwargs['payment_through']))
    return PlanResult(**kwargs,status=status,proposed=PolicyResult(name='Joint staged plan' if complete else 'Validated incumbent / benchmark fallback',purchases=p,movements=m,replay=verified),
        benchmark=PolicyResult(name='Constrained order-up-to benchmark',purchases=bp,movements=bm,replay=br),
        no_action=PolicyResult(name='No new actions',purchases=[],movements=[],replay=no),forecasts=trace,stages=stages,
        issues=issues,failures=verified.failures,exceptions=exceptions,elapsed_ms=(perf_counter()-start)*1000)


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
    """Explain only limits that every dated purchase option actually hits."""
    causes=[];cash={row.week_start:row for row in result.cash}
    purchased={}
    shared_used={}
    for action in purchases:
        key=action.supplier_id,action.sku,action.dispatch_date
        purchased[key]=purchased.get(key,0)+action.units
        supplier=ctx.suppliers[action.supplier_id]
        amount=action.units*(ctx.products[action.sku].volume_per_unit if supplier.shared_capacity_unit=='volume' else 1)
        shared_used[action.supplier_id,action.dispatch_date]=shared_used.get((action.supplier_id,action.dispatch_date),0)+amount
    for service in result.service:
        if service.unmet+service.tail_unmet<=EPS:
            continue
        offers=[o for o in ctx.data.supplier_offers if o.sku==service.sku]
        lanes=[lane for lane in ctx.data.transfer_lanes if lane.source==ctx.dc and lane.destination==service.location_id and service.sku in lane.allowed_skus]
        candidates=[]
        for offer in offers:
            minimum=max(offer.case_size,((offer.moq_units+offer.case_size-1)//offer.case_size)*offer.case_size)
            for i in range(56):
                timing=ctx.timing(offer,i)
                if timing is None:
                    continue
                dispatch,arrival=timing
                store_arrivals=[_valid_path_arrival(ctx.data,offer,lane,ctx.day(i)) for lane in lanes]
                store_arrivals=[day for day in store_arrivals if day is not None and day<=ctx.day(55)]
                if arrival>=56 or not store_arrivals:
                    continue
                candidates.append((offer,i,dispatch,arrival,minimum))
        if not candidates:
            causes.append(Failure(code='SUPPLIER_LEAD_TIME',message='No valid supplier and lane path can reach this store within the modeled horizon for the uncovered series.',sku=service.sku,location_id=service.location_id))
            continue
        if all(ctx.capacity.get((o.supplier_id,o.sku,d),0)-purchased.get((o.supplier_id,o.sku,ctx.day(d)),0)<qty
                for o,i,d,a,qty in candidates):
            causes.append(Failure(code='DATED_SUPPLIER_SKU_CAPACITY',message='Every dated supplier option that can arrive within the horizon has less remaining SKU capacity than one executable case/MOQ.',sku=service.sku,location_id=service.location_id))
        if all(ctx.suppliers[o.supplier_id].shared_daily_capacity-shared_used.get((o.supplier_id,ctx.day(d)),0)
                < qty*(ctx.products[o.sku].volume_per_unit if ctx.suppliers[o.supplier_id].shared_capacity_unit=='volume' else 1)
                for o,i,d,a,qty in candidates):
            causes.append(Failure(code='SHARED_SUPPLIER_CAPACITY',message='Every dated supplier option has less shared daily supplier headroom than one executable case/MOQ.',sku=service.sku,location_id=service.location_id))
        commitment_blocked=True;payment_blocked=True;mov_blocked=True
        for offer,i,dispatch,arrival,minimum in candidates:
            order_week=week(ctx.day(i));row=cash.get(order_week)
            line_value=offer.price_per_base_unit*minimum
            supplier=ctx.suppliers[offer.supplier_id]
            required_commitment=max(line_value,supplier.minimum_order_value)
            if row and row.commitment_headroom is not None and row.commitment_headroom+EPS>=required_commitment:
                commitment_blocked=False
            deposit=line_value*offer.deposit_fraction
            balance_week=week(ctx.day(arrival)+timedelta(days=offer.balance_days_after_receipt))
            balance=cash.get(balance_week)
            if (row and balance and row.payment_headroom is not None and balance.payment_headroom is not None
                    and row.payment_headroom+EPS>=deposit and balance.payment_headroom+EPS>=line_value-deposit):
                payment_blocked=False
            if supplier.minimum_order_value<=line_value+EPS:
                mov_blocked=False
        if commitment_blocked:
            causes.append(Failure(code='PURCHASE_COMMITMENT_AUTHORITY',message='Remaining weekly purchase authority is below the smallest executable case/MOQ or grouped supplier minimum for every dated option.',sku=service.sku,location_id=service.location_id))
        if payment_blocked:
            causes.append(Failure(code='PURCHASE_PAYMENT_CAPACITY',message='Remaining deposit or balance payment capacity is below the smallest executable dated purchase option.',sku=service.sku,location_id=service.location_id))
        if mov_blocked and not commitment_blocked:
            causes.append(Failure(code='GROUPED_SUPPLIER_MINIMUM',message='The grouped supplier minimum value exceeds an otherwise fundable minimum line.',sku=service.sku,location_id=service.location_id))
    unique={}
    for cause in causes:
        unique[cause.code,cause.sku,cause.location_id]=cause
    return list(unique.values())
