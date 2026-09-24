"""Orchestration only: real forecasts -> benchmark/joint model -> independent replay."""
from backend.app.diagnostics import timed, measure
from hashlib import sha256
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from math import ceil
from time import perf_counter
from uuid import uuid4
from backend.app.data.validation import validate_dataset
from backend.app.planning.contracts import PlanResult, PolicyResult, Failure, SolverStage, ShortageEvidence
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
    # Benchmark notes describe rejected construction attempts. They remain useful
    # advanced diagnostics, but are not causal evidence for a final-plan shortage.
    exceptions=list(ctx.exceptions.values()) if p==bp and m==bm else []
    if solver_failure is not None:
        exceptions.append(solver_failure)
    if verified.feasible:
        _attach_shortage_evidence(verified,_shortage_causes(ctx,verified,p,m))
    for move in m:
        opposite=next((t for t in m if t.sku==move.sku and t.source==move.destination and t.destination==move.source and t.dispatch_date<move.dispatch_date),None)
        if opposite:
            exceptions.append(Failure(code='LATER_RETURN_MOVEMENT',message=f'Stock moved on {opposite.dispatch_date} returns on {move.dispatch_date}; it was retained only under dated demand/buffer objectives and rechecked for donor protection. Inspect the daily ledger.',sku=move.sku,location_id=move.source,day=move.dispatch_date,action_id=move.action_id))
    return exceptions


def _attach_shortage_evidence(result, causes):
    """Attach at most two truthful evidence records per service/window.

    Daily analysis is kept in memory. Equivalent adjacent findings are coalesced;
    if the cause changes too often, the remaining quantity becomes an explicitly
    bounded/uncertain summary instead of a large or fabricated payload.
    """
    by_day={(cause.sku,cause.location_id,cause.day):cause for cause in causes}
    shortage_rows={}
    for row in result.stock:
        if row.unmet>EPS:
            shortage_rows.setdefault((row.sku,row.location_id),[]).append(row)
    origin=result.stock[0].day
    uncertain={'UNCERTAIN_SHORTAGE_ATTRIBUTION','TRANSFER_ALTERNATIVE_REQUIRES_REOPTIMIZATION'}
    labels={
        'SUPPLY_TIMING_LIMITATION':'No new purchase path could arrive in time',
        'DATED_SUPPLIER_SKU_CAPACITY':'Dated SKU availability blocked each tested timely purchase path',
        'SHARED_SUPPLIER_CAPACITY':'Shared supplier capacity blocked each tested timely purchase path',
        'RECEIVING_CAPACITY_LIMIT':'Receiving space blocked each tested timely purchase path',
        'LANE_CAPACITY_LIMIT':'Lane capacity blocked each tested timely replenishment path',
        'PURCHASE_COMMITMENT_AUTHORITY':'Weekly commitment authority blocked each tested timely purchase path',
        'PURCHASE_PAYMENT_CAPACITY':'Weekly payment capacity blocked each tested timely purchase path',
        'TRANSFER_FUNDING_LIMIT':'Transfer funding blocked each tested timely replenishment path',
        'GROUPED_SUPPLIER_MINIMUM':'The grouped supplier minimum enlarged every otherwise viable timely line into another hard limit',
        'TRANSFER_ALTERNATIVE_REQUIRES_REOPTIMIZATION':'A timely transfer alternative existed, so no single shortage cause was established',
        'UNCERTAIN_SHORTAGE_ATTRIBUTION':'The selected constrained policy left demand uncovered; no single cause was established',
    }
    for service in result.service:
        rows=shortage_rows.get((service.sku,service.location_id),[])
        if not rows:
            service.reason_codes=[];service.reason_summary=None;service.shortage_evidence=[]
            continue
        records=[]
        for window,start_index,end_index in [('visible',0,27),('tail',28,55)]:
            window_rows=[row for row in rows if start_index<=(row.day-origin).days<=end_index]
            groups=[]
            for row in window_rows:
                cause=by_day.get((service.sku,service.location_id,row.day))
                code=cause.code if cause else 'UNCERTAIN_SHORTAGE_ATTRIBUTION'
                supplier=cause.supplier_id if cause else None
                if groups and row.day==groups[-1][3].day+timedelta(days=1) and (code,supplier)==groups[-1][0]:
                    groups[-1][3]=row;groups[-1][2]+=row.unmet
                else:
                    groups.append([(code,supplier),row,row.unmet,row,cause])
            bounded=groups[:1]
            if len(groups)>2:
                remainder=groups[1:]
                quantity=sum(group[2] for group in remainder)
                first=remainder[0][1];last=remainder[-1][3]
                records.append(ShortageEvidence(window=window,start_date=first.day,end_date=last.day,quantity=quantity,
                    status='bounded_summary',reason_codes=['ATTRIBUTION_LIMIT'],
                    detail=f'{quantity:.1f} additional {window} units were uncovered across {sum(1 for row in window_rows if first.day<=row.day<=last.day)} dated shortage rows. Causes varied; inspect the selected SKU/store stock evidence because no common blocker is asserted for this bounded remainder.'))
            elif len(groups)==2:
                bounded=groups
            for signature,first,quantity,last,cause in bounded:
                code=signature[0];status='uncertain' if code in uncertain else 'established_limit'
                records.append(ShortageEvidence(window=window,start_date=first.day,end_date=last.day,quantity=quantity,status=status,
                    reason_codes=[code],detail=cause.message if cause else 'The final replay proves the dated shortage, but bounded attribution established no single cause.'))
        records.sort(key=lambda item:(item.start_date,item.end_date,item.reason_codes))
        service.shortage_evidence=records
        service.reason_codes=sorted({'DATED_SUPPLY_SHORTFALL',*(code for item in records for code in item.reason_codes if code!='ATTRIBUTION_LIMIT')})
        first=next((item for item in records if item.window=='visible'),records[0])
        first_code=next(code for code in first.reason_codes if code!='ATTRIBUTION_LIMIT')
        service.reason_summary=(f'{labels[first_code]} on {first.start_date}.' if first.start_date==first.end_date
            else f'{labels[first_code]} from {first.start_date} to {first.end_date}.')
        # This is a reconciliation invariant, not presentation rounding.
        if abs(sum(item.quantity for item in records)-(service.unmet+service.tail_unmet))>EPS:
            raise RuntimeError('Shortage evidence does not reconcile to replayed service.')


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
    """Return one bounded, dated finding for every replayed shortage day.

    A hard-limit claim is emitted only when all tested timely single-action paths
    fail the same dated check and no timely funded stock transfer is available.
    Passing these local checks is not treated as proof of a globally feasible
    improvement because later stock, reserve and funding effects require a replan.
    """
    causes=[];cash={row.week_start:row for row in result.cash}
    stock={(row.sku,row.location_id,row.day):row for row in result.stock}
    shortage_rows={}
    for row in result.stock:
        if row.unmet>EPS:
            shortage_rows.setdefault((row.sku,row.location_id),[]).append(row)
    peak_volume={}
    for row in result.stock:
        key=row.location_id,row.day
        peak_volume[key]=peak_volume.get(key,0.)+(row.opening+row.receipts+ctx.unavailable[row.sku,row.location_id])*ctx.products[row.sku].volume_per_unit
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
    offers_by_sku={}
    for offer in ctx.data.supplier_offers:
        offers_by_sku.setdefault(offer.sku,[]).append(offer)
    inbound_by_series={}
    for lane in ctx.data.transfer_lanes:
        for sku in lane.allowed_skus:
            inbound_by_series.setdefault((sku,lane.destination),[]).append(lane)

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

    def transfer_fee_ok(lane,dispatch):
        group=lane.source,lane.destination,dispatch
        existing_group=group in lane_used or any(t.status=='confirmed' and (t.source,t.destination,t.dispatch_date)==group for t in ctx.data.open_transfers)
        fee=0 if existing_group else cents(lane.grouped_dispatch_fee)
        row=cash.get(week(dispatch))
        return bool(row and row.payment_headroom is not None and row.transfer_headroom is not None
            and cents(row.payment_headroom)>=fee and cents(row.transfer_headroom)>=fee)

    checks=('commitment','payment','transfer','sku_capacity','shared_capacity','dc_receiving','lane_capacity','store_receiving')
    blocker_codes=(
        ('sku_capacity','DATED_SUPPLIER_SKU_CAPACITY'),
        ('shared_capacity','SHARED_SUPPLIER_CAPACITY'),
        ('dc_receiving','RECEIVING_CAPACITY_LIMIT'),
        ('lane_capacity','LANE_CAPACITY_LIMIT'),
        ('store_receiving','RECEIVING_CAPACITY_LIMIT'),
        ('commitment','PURCHASE_COMMITMENT_AUTHORITY'),
        ('payment','PURCHASE_PAYMENT_CAPACITY'),
        ('transfer','TRANSFER_FUNDING_LIMIT'),
    )

    for service in result.service:
        if service.unmet+service.tail_unmet<=EPS:
            continue
        service_shortages=shortage_rows.get((service.sku,service.location_id),[])
        if not service_shortages:continue
        offers=offers_by_sku.get(service.sku,[])
        inbound_lanes=inbound_by_series.get((service.sku,service.location_id),[])
        lanes=[lane for lane in inbound_lanes if lane.source==ctx.dc]
        purchase_paths=[];future_arrivals=[]
        for offer in offers:
            base=max(offer.case_size,ceil(offer.moq_units/offer.case_size)*offer.case_size)
            for lane in lanes:
                for i in range(56):
                    dates=path_dates(offer,lane,i)
                    if dates is None:continue
                    supplier_dispatch,dc_arrival,lane_dispatch,store_arrival=dates
                    future_arrivals.append(store_arrival)
                    supplier=ctx.suppliers[offer.supplier_id];order_day=ctx.day(i)
                    existing=ordered_value.get((offer.supplier_id,order_day),0)
                    unit_price=cents(offer.price_per_base_unit);minimum_gap=max(0,cents(supplier.minimum_order_value)-existing)
                    required=max(base,ceil(minimum_gap/max(unit_price,1)/offer.case_size)*offer.case_size)
                    evidence=[]
                    for units in (base,required):
                        value,flows,commitment_ok,payment_ok,transfer_ok=money_evidence(offer,order_day,dc_arrival,lane_dispatch,lane,units)
                        dispatch_index=(supplier_dispatch-ctx.start).days;lane_index=(lane_dispatch-ctx.start).days
                        sku_headroom=ctx.capacity.get((offer.supplier_id,offer.sku,dispatch_index),0)-purchased.get((offer.supplier_id,offer.sku,supplier_dispatch),0)
                        multiplier=ctx.products[offer.sku].volume_per_unit if supplier.shared_capacity_unit=='volume' else 1
                        shared_headroom=supplier.shared_daily_capacity-shared_used.get((offer.supplier_id,supplier_dispatch),0)
                        lane_headroom=lane.capacity_units-ctx.lane_used[lane.source,lane.destination,lane_index]-lane_used.get((lane.source,lane.destination,lane_dispatch),0)
                        volume=ctx.products[offer.sku].volume_per_unit
                        evidence.append(dict(units=units,value=value,flows=flows,commitment=commitment_ok,payment=payment_ok,transfer=transfer_ok,
                            sku_capacity=sku_headroom+EPS>=units,shared_capacity=shared_headroom+EPS>=units*multiplier,
                            dc_receiving=peak_volume.get((lane.source,dc_arrival),0.)+units*volume<=ctx.locations[lane.source].storage_volume+EPS,
                            lane_capacity=lane_headroom+EPS>=lane.pack_units,
                            store_receiving=peak_volume.get((lane.destination,store_arrival),0.)+lane.pack_units*volume<=ctx.locations[lane.destination].storage_volume+EPS))
                    purchase_paths.append((offer,order_day,store_arrival,base,required,evidence))
        for row in service_shortages:
            first=row.day;quantity=row.unmet;span=str(first)
            transfer_options=[]
            for lane in inbound_lanes:
                for i in range(max(0,(first-ctx.start).days+1)):
                    dispatch=ctx.day(i);arrival=dispatch+timedelta(days=lane.transit_days)
                    if arrival>first or dispatch.weekday() not in lane.dispatch_weekdays or dispatch.weekday() not in ctx.locations[lane.source].open_weekdays or arrival.weekday() not in ctx.locations[lane.destination].open_weekdays:continue
                    donor=stock.get((service.sku,lane.source,dispatch));available=max(0.,donor.closing-(ctx.reserve.get((service.sku,lane.source,i),0) if ctx.locations[lane.source].kind=='store' else 0)) if donor else 0
                    headroom=lane.capacity_units-ctx.lane_used[lane.source,lane.destination,i]-lane_used.get((lane.source,lane.destination,dispatch),0)
                    volume=ctx.products[service.sku].volume_per_unit
                    receiving=peak_volume.get((lane.destination,arrival),0.)+lane.pack_units*volume<=ctx.locations[lane.destination].storage_volume+EPS
                    if min(available,headroom)>=lane.pack_units and receiving and transfer_fee_ok(lane,dispatch):
                        transfer_options.append((dispatch,arrival,available,headroom,lane))
            candidates=[candidate for candidate in purchase_paths if candidate[2]<=first]
            scope=dict(sku=service.sku,location_id=service.location_id,day=first)
            if transfer_options:
                dispatch,arrival,available,headroom,_=max(transfer_options,key=lambda item:min(item[2],item[3]))
                causes.append(Failure(code='TRANSFER_ALTERNATIVE_REQUIRES_REOPTIMIZATION',message=f'{quantity:.1f} units were short on {span}; an observed transfer option could dispatch on {dispatch} and arrive {arrival}, with {available:.1f} donor units and {headroom:.1f} lane units available. This is an alternative, not proof that allocation caused the shortage.',**scope))
                continue
            if not candidates:
                earliest=min((arrival for arrival in future_arrivals if arrival>first),default=None)
                detail=f'; the earliest valid purchase-to-store path arrives {earliest}' if earliest else '; no valid path exists in the modeled horizon'
                causes.append(Failure(code='SUPPLY_TIMING_LIMITATION',message=f'{quantity:.1f} units were short on {span}{detail}. No funded stock transfer was available by that date. This is a dated purchasing-timing limit, not a claim that every form of replenishment was impossible.',**scope))
                continue
            base_checks=[entry[5][0] for entry in candidates];required_checks=[entry[5][1] for entry in candidates]
            if any(all(item[key] for key in checks) for item in required_checks):
                causes.append(Failure(code='UNCERTAIN_SHORTAGE_ATTRIBUTION',message=f'{quantity:.1f} units were short on {span}, while a timely incremental path passed the bounded stock, calendar, receiving, capacity, grouped-minimum and funding checks. Later stock, donor-reserve and funding effects were not reoptimized, so no single cause is established.',**scope))
                continue
            minimum_blocked=[]
            for offer,order_day,arrival,base,required,evidence in candidates:
                base_ok=all(evidence[0][key] for key in checks)
                required_ok=all(evidence[1][key] for key in checks)
                if required>base and base_ok and not required_ok:minimum_blocked.append((offer,order_day,base,required,evidence[1]['value']))
            if minimum_blocked and all(not all(item[key] for key in checks) for item in required_checks):
                offer,order_day,base,required,value=min(minimum_blocked,key=lambda item:item[4])
                existing=ordered_value.get((offer.supplier_id,order_day),0)/100
                causes.append(Failure(code='GROUPED_SUPPLIER_MINIMUM',message=f'{quantity:.1f} units were short on {span}; a {base}-unit timely line was otherwise feasible, but the supplier/order-date group had SAR {existing:.2f} already and required {required} units (SAR {value/100:.2f}) to satisfy the remaining grouped minimum. The larger qualifying line failed another dated hard limit.',supplier_id=offer.supplier_id,**scope))
                continue
            blocker=next(((key,code) for key,code in blocker_codes if all(not item[key] for item in base_checks)),None)
            if blocker:
                key,code=blocker
                if code=='PURCHASE_COMMITMENT_AUTHORITY':
                    smallest=min(item['value'] for item in base_checks)/100
                    best=max((cash.get(week(entry[1])).commitment_headroom or 0) for entry in candidates if cash.get(week(entry[1])))
                    message=f'{quantity:.1f} units were short on {span}; every timely base line required at least SAR {smallest:.2f} against at most SAR {best:.2f} remaining weekly commitment authority.'
                elif code=='PURCHASE_PAYMENT_CAPACITY':
                    requirement=min(max(item['flows'].values(),default=0) for item in base_checks)/100
                    message=f'{quantity:.1f} units were short on {span}; every timely base line exceeded a weekly payment limit. The smallest grouped same-week requirement was SAR {requirement:.2f}; deposits, balances, existing obligations and transfer fees were counted once by funding week.'
                else:
                    label={'DATED_SUPPLIER_SKU_CAPACITY':'dated SKU availability','SHARED_SUPPLIER_CAPACITY':'dated shared supplier capacity','RECEIVING_CAPACITY_LIMIT':'dated receiving space','LANE_CAPACITY_LIMIT':'dated lane capacity','TRANSFER_FUNDING_LIMIT':'dated transfer funding'}[code]
                    message=f'{quantity:.1f} units were short on {span}; every tested timely base line failed its {label} check.'
                causes.append(Failure(code=code,message=message,**scope))
                continue
            causes.append(Failure(code='UNCERTAIN_SHORTAGE_ATTRIBUTION',message=f'{quantity:.1f} units were short on {span}. The tested timely paths failed different bounded checks, so no single cause was established; a globally feasible improvement would require replanning later stock, reserves and funding.',**scope))
    return causes
