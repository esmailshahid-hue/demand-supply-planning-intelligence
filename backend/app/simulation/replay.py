"""Rebuild stock, capacity and SAR cash from inputs/actions, without solver variables."""
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from backend.app.planning.contracts import (
    CashWeek, Failure, Payment, Replay, Service, ServiceGroup, StockDay, Summary,
)

EPS = 1e-5


def cents(value):
    return int((Decimal(str(value)) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def week(day):
    return day - timedelta(days=day.weekday())


def replay(data, demand, buffers, purchases=(), movements=(), horizon=56, include_stock=True):
    """Demand is the immutable forecast boundary; all action quantities/timing are untrusted.

    Existing supplier capacity is declared *remaining availability for new orders*.
    Existing movements consume lane space; their invoiced fees live only in Payables.
    """
    start = data.settings.as_of
    end = start + timedelta(days=horizon - 1)
    visible_end = start + timedelta(days=min(28, horizon))
    products = {p.sku: p for p in data.products}
    locations = {l.location_id: l for l in data.locations}
    offers = {o.offer_id: o for o in data.supplier_offers}
    suppliers = {s.supplier_id: s for s in data.suppliers}
    lanes = {(l.source, l.destination): l for l in data.transfer_lanes}
    budgets = {b.week_start: b for b in data.budgets}
    capacity = {(c.supplier_id, c.sku, c.dispatch_date): c.available_units for c in data.supplier_capacity}
    failures, payments, ledger = [], [], []
    def fail(code, message, **scope):
        failures.append(Failure(code=code, message=message, **scope))
    receipts, dispatches, confirmed_receipts = defaultdict(float), defaultdict(float), defaultdict(float)
    stock, unavailable, cost = {}, {}, {}
    for p in products:
        for loc in locations:
            stock[p, loc] = 0.0
            unavailable[p, loc] = 0
            cost[p, loc] = products[p].cost_per_base_unit
    for row in data.inventory:
        key = row.sku, row.location_id
        stock[key] = row.on_hand - row.blocked - row.reserved
        unavailable[key] = row.blocked + row.reserved
        cost[key] = row.book_unit_cost
        if stock[key] < 0:
            fail('negative_usable_stock', 'Blocked and reserved stock exceed on hand.', sku=row.sku, location_id=row.location_id)
    initial_units = sum(stock.values())
    lane_used, supplier_used, shared_used = defaultdict(float), defaultdict(float), defaultdict(float)
    ordered_value, grouped_fees = defaultdict(int), {}
    order_groups = defaultdict(int)
    seen = {r.external_id for r in data.open_orders + data.open_transfers}
    transit_units = sum(t.remaining_units for t in data.open_transfers if t.status == 'dispatched')
    # Value moves at the donor's declared book cost; new purchase lots use offer cost.
    value = {k: stock[k] * cost[k] for k in stock}
    receipt_value = defaultdict(float)
    for o in data.open_orders:
        if o.status != 'received':
            key = o.sku, o.destination, o.arrival_date
            receipts[key] += o.remaining_units
            confirmed_receipts[key] += o.remaining_units
            receipt_value[key] += o.remaining_units * o.cost_per_base_unit
    for t in data.open_transfers:
        if t.status == 'received':
            continue
        key = t.sku, t.destination, t.arrival_date
        receipts[key] += t.remaining_units
        confirmed_receipts[key] += t.remaining_units
        if t.status == 'dispatched':
            receipt_value[key] += t.remaining_units * cost[t.sku, t.source]
            if t.dispatch_date >= start:
                fail('transaction_status', 'Dispatched transfer must have left stock before the as-of snapshot.', action_id=t.external_id)
        else:
            if t.dispatch_date < start:
                fail('transaction_status', 'Confirmed transfer requires an updated dispatch date.', action_id=t.external_id)
            lane = lanes.get((t.source,t.destination))
            if not lane or t.sku not in lane.allowed_skus:
                fail('lane_eligibility', 'Confirmed transfer requires an approved lane and SKU.', action_id=t.external_id)
            elif (t.remaining_units % lane.pack_units or t.arrival_date != t.dispatch_date+timedelta(days=lane.transit_days)
                  or t.dispatch_date.weekday() not in lane.dispatch_weekdays
                  or t.dispatch_date.weekday() not in locations[t.source].open_weekdays
                  or t.arrival_date.weekday() not in locations[t.destination].open_weekdays):
                fail('confirmed_transfer_rules', 'Confirmed transfer violates lane packs, transit or calendars; correct the locked input.', action_id=t.external_id)
            dispatches[t.sku, t.source, t.dispatch_date] += t.remaining_units
            lane_used[t.source, t.destination, t.dispatch_date] += t.remaining_units
    for p in data.payables:
        payments.append(Payment(reference=p.external_id, due_date=p.due_date, kind='existing', amount=cents(p.amount)/100))
        if p.due_date < start:
            fail('overdue_payable', 'An overdue unpaid obligation requires an explicit corrected due date.', day=p.due_date)
    for a in purchases:
        scope = dict(sku=a.sku, supplier_id=a.supplier_id, action_id=a.action_id, day=a.order_date)
        if a.action_id in seen:
            fail('duplicate_action', 'Action IDs must be unique across proposals and existing records.', **scope)
        seen.add(a.action_id)
        o = offers.get(a.offer_id)
        if not o or (o.sku, o.supplier_id) != (a.sku, a.supplier_id) or a.destination not in locations or locations[a.destination].kind != 'dc':
            fail('supplier_eligibility', 'Purchase must use its approved SKU offer and arrive at the DC.', **scope)
            continue
        dispatch = a.order_date
        for _ in range(7):
            if dispatch.weekday() in o.dispatch_weekdays:
                break
            dispatch += timedelta(days=1)
        arrival = dispatch + timedelta(days=o.lead_time_days)
        for _ in range(7):
            if arrival.weekday() in locations[a.destination].open_weekdays:
                break
            arrival += timedelta(days=1)
        if not (start <= a.order_date <= a.dispatch_date < a.arrival_date <= end) or a.dispatch_date != dispatch or a.arrival_date != arrival:
            fail('purchase_timing', 'Purchase dates conflict with dispatch, lead time, receiving calendar or model horizon.', **scope)
        if a.order_date.weekday() not in o.order_weekdays or not (o.valid_from <= a.order_date <= o.valid_to and o.valid_from <= a.dispatch_date <= o.valid_to):
            fail('offer_calendar', 'Order/dispatch must be within offer validity and order calendar.', **scope)
        if a.units <= 0 or a.units % o.case_size or a.units < o.moq_units:
            fail('purchase_pack_moq', 'Purchase must satisfy integer cases and conditional line MOQ.', **scope)
        total = cents(Decimal(str(o.price_per_base_unit)) * a.units)
        if cents(a.value) != total:
            fail('purchase_value', 'Displayed line value differs from quantity times offer price.', **scope)
        deposit = int((Decimal(total) * Decimal(str(o.deposit_fraction))).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
        payments.extend([Payment(reference=a.action_id, due_date=a.order_date, kind='deposit', amount=deposit/100),
                         Payment(reference=a.action_id, due_date=a.arrival_date + timedelta(days=o.balance_days_after_receipt), kind='balance', amount=(total-deposit)/100)])
        ordered_value[week(a.order_date)] += total
        order_groups[a.supplier_id, a.order_date] += total
        supplier_used[a.supplier_id, a.sku, a.dispatch_date] += a.units
        s = suppliers[a.supplier_id]
        shared_used[a.supplier_id, a.dispatch_date] += a.units * (products[a.sku].volume_per_unit if s.shared_capacity_unit == 'volume' else 1)
        key = a.sku, a.destination, a.arrival_date
        receipts[key] += a.units
        receipt_value[key] += total / 100
    for (sid, day), amount in order_groups.items():
        if amount < cents(suppliers[sid].minimum_order_value):
            fail('supplier_minimum', 'Grouped supplier-order value is below the supplier minimum.', supplier_id=sid, day=day)
    for (sid, sku, day), units in supplier_used.items():
        available = capacity.get((sid, sku, day))
        if available is None or units > available + EPS:
            fail('supplier_capacity', 'New orders exceed declared remaining dated availability, or it is unknown.', sku=sku, supplier_id=sid, day=day)
    for (sid, day), amount in shared_used.items():
        limit = suppliers[sid].shared_daily_capacity
        if limit is None or amount > limit + EPS:
            fail('shared_supplier_capacity', 'Shared supplier capacity is unknown or exceeded.', supplier_id=sid, day=day)
    movement_records = [t for t in data.open_transfers if t.status == 'confirmed'] + list(movements)
    committed_dispatch_groups = {(t.source,t.destination,t.dispatch_date) for t in data.open_transfers if t.status=='confirmed'}
    for a in movements:
        scope = dict(sku=a.sku, location_id=a.source, action_id=a.action_id, day=a.dispatch_date)
        if a.action_id in seen:
            fail('duplicate_action', 'Action IDs must be unique.', **scope)
        seen.add(a.action_id)
        lane = lanes.get((a.source, a.destination))
        if not lane or a.sku not in products or a.sku not in lane.allowed_skus:
            fail('lane_eligibility', 'Movement needs an approved lane and SKU.', **scope)
            continue
        if a.units <= 0 or a.units % lane.pack_units:
            fail('movement_pack', 'Movement is not an integer lane pack.', **scope)
        if (not start <= a.dispatch_date < a.arrival_date <= end or a.arrival_date != a.dispatch_date + timedelta(days=lane.transit_days)
                or a.dispatch_date.weekday() not in lane.dispatch_weekdays or a.dispatch_date.weekday() not in locations[a.source].open_weekdays
                or a.arrival_date.weekday() not in locations[a.destination].open_weekdays):
            fail('movement_timing', 'Movement violates transit, horizon or dispatch/receiving calendar.', **scope)
        dispatches[a.sku, a.source, a.dispatch_date] += a.units
        receipts[a.sku, a.destination, a.arrival_date] += a.units
        lane_used[a.source, a.destination, a.dispatch_date] += a.units
        group = a.source, a.destination, a.dispatch_date
        # Confirmed dispatch charges are already paid or explicitly in Payables.
        grouped_fees[group] = 0 if group in committed_dispatch_groups else cents(lane.grouped_dispatch_fee)
    for (src, dst, day), units in lane_used.items():
        lane = lanes.get((src, dst))
        if lane is None or lane.capacity_units is None or units > lane.capacity_units + EPS:
            fail('lane_capacity', 'Combined existing/new dispatch exceeds lane capacity, or capacity is unknown.', location_id=src, day=day)
    directions = {(t.sku, t.source, t.destination, t.dispatch_date) for t in movement_records}
    for sku, src, dst, day in sorted(directions):
        if (sku, dst, src, day) in directions:
            fail('opposing_movements', 'Opposing same-SKU movements on one day are prohibited.', sku=sku, location_id=src, day=day)
    for (src, dst, day), amount in sorted(grouped_fees.items()):
        payments.append(Payment(reference=f'{src}-{dst}-{day}', due_date=day, kind='movement', amount=amount/100))
    movements_by_day = defaultdict(list)
    for t in movement_records:
        if (t.source, t.destination) in lanes and t.sku in products:
            movements_by_day[t.dispatch_date].append(t)
    arrived_transfers = defaultdict(float)
    for t in list(data.open_transfers) + list(movements):
        if getattr(t, 'status', '') != 'received':
            arrived_transfers[t.arrival_date] += getattr(t, 'remaining_units', getattr(t, 'units', 0))
    service_totals = defaultdict(lambda: [0., 0., 0., 0.])
    fulfilled_total, external_received, buffer_deficit = 0., 0., 0.
    for i in range(horizon):
        day = start + timedelta(days=i)
        opening = dict(stock)
        for key in stock:
            rkey = (*key, day)
            stock[key] += receipts[rkey]
            value[key] += receipt_value[rkey]
        transit_units -= arrived_transfers[day]
        for loc, location in locations.items():
            peak = sum((stock[p, loc] + unavailable[p, loc]) * products[p].volume_per_unit for p in products)
            if peak > location.storage_volume + EPS:
                fail('receiving_volume', 'Receiving peak exceeds storage volume before local demand.', location_id=loc, day=day)
        served = {}
        for key in stock:
            qty = demand.get(key, [0.] * horizon)[i]
            served[key] = min(qty, max(0., stock[key]))
            unit_cost = value[key] / stock[key] if stock[key] > EPS else cost[key]
            value[key] -= served[key] * unit_cost
            stock[key] -= served[key]
            fulfilled_total += served[key]
            totals = service_totals[key]
            if i < 28:
                totals[0] += qty
                totals[1] += served[key]
            else:
                totals[2] += qty
                totals[3] += qty - served[key]
        # Reserve is a prior-input policy: next seven cumulative net needs, only confirmed receipts.
        for key in stock:
            sent = dispatches[*key, day]
            if not sent:
                continue
            if locations[key[1]].kind == 'store':
                cumulative = peak_need = 0.
                series = demand.get(key, [0.] * horizon)
                for j in range(i + 1, i + 8):
                    expected = series[j] if j < horizon else series[max(0, horizon-7) + (j-horizon) % min(7, horizon)]
                    cumulative += expected - confirmed_receipts[*key, start + timedelta(days=j)]
                    peak_need = max(peak_need, cumulative)
                reserve = peak_need + buffers.get(key, 0.)
                if stock[key] - sent < reserve - EPS:
                    fail('donor_reserve', 'Dispatch breaches the next-seven-day cumulative donor reserve plus buffer.', sku=key[0], location_id=key[1], day=day)
            if sent > stock[key] + EPS:
                fail('stock_overallocated', 'Dispatch exceeds stock remaining after local demand; future receipts cannot be borrowed.', sku=key[0], location_id=key[1], day=day)
        for t in movements_by_day[day]:
            key = t.sku, t.source
            units = getattr(t, 'remaining_units', getattr(t, 'units', 0))
            unit_cost = value[key] / stock[key] if stock[key] > EPS else cost[key]
            moved_value = units * unit_cost
            value[key] -= moved_value
            stock[key] -= units
            receipt_value[t.sku, t.destination, t.arrival_date] += moved_value
            transit_units += units
        for key in stock:
            qty = demand.get(key, [0.] * horizon)[i]
            if (i+1)%7==0 and locations[key[1]].kind=='store':
                buffer_deficit += max(0.,buffers.get(key,0.)-stock[key])
            if include_stock:
                ledger.append(StockDay(sku=key[0], location_id=key[1], day=day, opening=opening[key], receipts=receipts[*key, day],
                    demand=qty, fulfilled=served[key], unmet=qty-served[key], dispatched=dispatches[*key, day], closing=stock[key]))
        external_received = sum(o.remaining_units for o in data.open_orders if o.status != 'received' and o.arrival_date <= day) + sum(a.units for a in purchases if a.arrival_date <= day)
        expected_network = initial_units + sum(t.remaining_units for t in data.open_transfers if t.status == 'dispatched') + external_received - fulfilled_total
        if abs(sum(stock.values()) + transit_units - expected_network) > EPS:
            fail('stock_conservation', 'Network on-hand plus transit does not reconcile with receipts and fulfillment.', day=day)
    payment_end = max([start+timedelta(days=89)] + [p.due_date for p in payments])
    cash = []
    w = week(start)
    while w <= week(payment_end):
        b = budgets.get(w)
        rows = [p for p in payments if week(p.due_date) == w]
        existing = sum(cents(p.amount) for p in rows if p.kind == 'existing')
        new = sum(cents(p.amount) for p in rows if p.kind != 'existing')
        fees = sum(cents(p.amount) for p in rows if p.kind == 'movement')
        commit = ordered_value[w]
        if b is None:
            fail('funding_coverage', 'Missing commitment/payment/transfer limits prevent funded acceptance.', day=w)
        else:
            for code, used, cap in [('commitment_cap', commit, cents(b.new_commitment_cap)), ('payment_ceiling', existing+new, cents(b.payment_ceiling)), ('transfer_budget', fees, cents(b.transfer_budget))]:
                if used > cap:
                    fail(code, 'Dated financial usage exceeds the declared ceiling.', day=w)
        cash.append(CashWeek(week_start=w, commitments=commit/100, commitment_cap=b.new_commitment_cap if b else None,
            commitment_headroom=(cents(b.new_commitment_cap)-commit)/100 if b else None, existing_payments=existing/100, new_payments=new/100,
            total_payments=(existing+new)/100, payment_ceiling=b.payment_ceiling if b else None, payment_headroom=(cents(b.payment_ceiling)-existing-new)/100 if b else None,
            movement_fees=fees/100, transfer_budget=b.transfer_budget if b else None, transfer_headroom=(cents(b.transfer_budget)-fees)/100 if b else None))
        w += timedelta(days=7)
    if data.settings.funding_mode != 'funded':
        fail('unfunded', 'Unfunded exploration cannot be presented as an executable funded plan.')
    services = []
    for a in data.assortment:
        key = a.sku, a.location_id
        d, f, tail, missing = service_totals[key]
        start_stock = next((r.on_hand-r.blocked-r.reserved for r in data.inventory if (r.sku,r.location_id) == key), 0)
        known = sum(q for (sku,loc,day),q in confirmed_receipts.items() if (sku,loc)==key and start <= day <= end)
        services.append(Service(sku=a.sku, location_id=a.location_id, service_class=a.service_class, must_stock=a.must_stock,
            demand=d, fulfilled=f, unmet=d-f, tail_unmet=missing, fill_pct=100*f/d if d else None, target=data.settings.class_targets[a.service_class],
            buffer_units=buffers.get(key,0.), unconstrained_need=max(0.,d+tail+buffers.get(key,0.)-start_stock-known),
            reason_codes=['DATED_SUPPLY_SHORTFALL'] if d-f+missing > EPS else []))
    groups = []
    for loc, cls, must in sorted({(s.location_id,s.service_class,s.must_stock) for s in services}):
        members = [s for s in services if (s.location_id,s.service_class,s.must_stock)==(loc,cls,must)]
        for window in ('visible','tail'):
            gd = sum(s.demand if window=='visible' else service_totals[s.sku,s.location_id][2] for s in members)
            gf = sum(s.fulfilled if window=='visible' else service_totals[s.sku,s.location_id][2]-s.tail_unmet for s in members)
            target = data.settings.class_targets[cls]
            groups.append(ServiceGroup(location_id=loc,service_class=cls,must_stock=must,window=window,
                demand=gd,fulfilled=gf,target=target,target_shortfall=max(0.,target*gd-gf)))
    d = sum(s.demand for s in services)
    f = sum(s.fulfilled for s in services)
    commit = sum(ordered_value.values())/100
    visible_commit = sum(cents(a.value) for a in purchases if a.order_date < visible_end)/100
    total_pay = sum(cents(p.amount) for p in payments)/100
    visible_pay = sum(cents(p.amount) for p in payments if start <= p.due_date < visible_end)/100
    # No new movement can end outside the model; existing outstanding movement value is explicit.
    outstanding = sum(receipt_value[t.sku,t.destination,t.arrival_date] for t in data.open_transfers if t.status == 'dispatched' and t.arrival_date > end)
    # Next-review coverage repeats the final forecast week; DC covers only net store need.
    excess = 0.
    for sku in products:
        net_store_need = 0.
        for loc in locations:
            if locations[loc].kind!='store': continue
            target=sum(demand.get((sku,loc),[0.]*horizon)[-7:])+buffers.get((sku,loc),0.)
            excess+=max(0.,stock[sku,loc]-target)
            net_store_need+=max(0.,target-stock[sku,loc])
        excess+=max(0.,sum(stock[sku,l] for l in locations if locations[l].kind=='dc')-net_store_need)
    summary = Summary(demand=d, fulfilled=f, unmet=d-f, fill_pct=100*f/d if d else None,
        tail_demand=sum(v[2] for v in service_totals.values()), tail_unmet=sum(v[3] for v in service_totals.values()),
        commitments=commit, visible_commitments=visible_commit, tail_commitments=commit-visible_commit,
        payments=total_pay, visible_payments=visible_pay, later_payments=total_pay-visible_pay,
        movement_expense=sum(grouped_fees.values())/100, ending_stock=sum(stock.values())+transit_units,
        ending_inventory_investment=round(sum(value.values())+outstanding+sum(unavailable[k]*cost[k] for k in stock),2),
        revenue_exposure=round(sum(s.unmet*products[s.sku].net_price_per_base_unit for s in services),2),
        weekly_buffer_deficit=buffer_deficit,terminal_excess_units=excess)
    return Replay(feasible=not failures, failures=failures, summary=summary, cash=cash,
                  payments=sorted(payments,key=lambda p:(p.due_date,p.reference,p.kind)), service=services, service_groups=groups, stock=ledger)
