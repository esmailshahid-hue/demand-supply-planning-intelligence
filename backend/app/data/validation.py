"""Cross-row checks for normalized data; workbook parsing is a later pass."""
from collections import Counter
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from backend.app.contracts import Dataset, Issue


def event_matches(event, product, location_id):
    return ((event.scope == "sku" and event.scope_id == product.sku)
            or (event.scope == "category" and event.scope_id == product.category)
            or (event.scope == "store" and event.scope_id == location_id))


def validate_dataset(data: Dataset) -> list[Issue]:
    issues = []
    def add(code, message, count=1, severity="error"):
        if count:
            issues.append(Issue(severity=severity, code=code, message=message, count=count))
    def unique(rows, fields, table):
        duplicates = sum(n - 1 for n in Counter(tuple(getattr(r, f) for f in fields) for r in rows).values() if n > 1)
        add("duplicate_key", f"{table}: duplicate primary keys.", duplicates)
    tables = [
        ("products", ["sku"]), ("locations", ["location_id"]),
        ("assortment", ["sku", "location_id"]), ("demand_history", ["sku", "location_id", "day"]),
        ("inventory", ["sku", "location_id"]), ("suppliers", ["supplier_id"]),
        ("supplier_offers", ["offer_id"]), ("supplier_capacity", ["supplier_id", "sku", "dispatch_date"]),
        ("transfer_lanes", ["source", "destination"]), ("open_orders", ["external_id"]),
        ("open_transfers", ["external_id"]), ("payables", ["external_id"]),
        ("budgets", ["week_start"]), ("events", ["event_id"]),
    ]
    for table, fields in tables:
        unique(getattr(data, table), fields, table)
    products = {p.sku: p for p in data.products}
    locations = {l.location_id: l for l in data.locations}
    suppliers = {s.supplier_id: s for s in data.suppliers}
    events = {e.event_id: e for e in data.events}
    assortments = {(a.sku, a.location_id): a for a in data.assortment}
    as_of = data.settings.as_of
    add("network", "Exactly one DC and one to four stores are supported.", int(sum(l.kind == "dc" for l in data.locations) != 1))
    for name, fields in tables:
        for row in getattr(data, name):
            if hasattr(row, "sku") and row.sku not in products:
                add("unknown_sku", f"{name}: SKU reference does not exist.")
            for field in ("location_id", "source", "destination"):
                if hasattr(row, field) and getattr(row, field) not in locations:
                    add("unknown_location", f"{name}: location reference does not exist.")
            if hasattr(row, "supplier_id") and row.supplier_id not in suppliers:
                add("unknown_supplier", f"{name}: supplier reference does not exist.")
    for p in data.products:
        add("active_dates", "Product active dates are reversed.", int(p.active_to is not None and p.active_to < p.active_from))
    for a in data.assortment:
        add("range_dates", "Assortment dates are reversed.", int(a.ranged_to is not None and a.ranged_to < a.ranged_from))
        add("dc_demand", "Only stores may have retail assortment/demand.", int(a.location_id in locations and locations[a.location_id].kind != "store"))
        add("launch_metadata", "Launch estimates require a reason and knowledge timestamp.", int(a.launch_daily_units is not None and (a.launch_known_at is None or not a.launch_reason)))
    missing = censored = delayed = 0
    for row in data.demand_history:
        add("unknown_assortment", "Demand row has no matching store assortment.", int((row.sku, row.location_id) not in assortments))
        add("history_dates", "History must lie in the declared history period before as-of.", int(not as_of - timedelta(days=data.settings.history_days) <= row.day < as_of))
        add("observation_time", "A daily observation cannot be available before its day has ended in Riyadh.", int(row.available_at.astimezone(ZoneInfo("Asia/Riyadh")).date() <= row.day))
        add("unknown_event", "Demand row references an unknown event.", int(row.event_id is not None and row.event_id not in events))
        if row.event_id in events and row.sku in products:
            event = events[row.event_id]
            add("event_reference", "Demand event reference conflicts with scope or dates.", int(not (event.start <= row.day <= event.end and event_matches(event, products[row.sku], row.location_id))))
        missing += int(row.is_open and (row.sales_units is None or row.stock_available is None))
        censored += int(row.is_open and row.stock_available is False and row.sales_units is not None)
        delayed += int(row.is_open and row.available_at >= datetime.combine(as_of, time(), ZoneInfo("Asia/Riyadh")))
    # Absent rows also remain unknown; do not manufacture zeros.
    observed_keys = {(r.sku, r.location_id, r.day) for r in data.demand_history}
    absent = 0
    for a in data.assortment:
        if a.sku not in products or a.location_id not in locations:
            continue
        p, loc = products[a.sku], locations[a.location_id]
        day = max(as_of - timedelta(days=data.settings.history_days), a.ranged_from, p.active_from)
        end = min(as_of, (a.ranged_to + timedelta(days=1)) if a.ranged_to else as_of, (p.active_to + timedelta(days=1)) if p.active_to else as_of)
        while day < end:
            absent += int(day.weekday() in loc.open_weekdays and (a.sku, a.location_id, day) not in observed_keys)
            day += timedelta(days=1)
    add("missing_history", "Open ranged history contains unknown or absent observations; these are not zeros.", missing + absent, "warning")
    add("censored_history", "Stockout-censored sales are lower bounds. Training estimates are never scored as actual demand.", censored, "warning")
    add("delayed_history", "Observations not yet available at the as-of midnight are excluded, including from the final check.", delayed, "warning")
    for row in data.inventory:
        add("negative_usable_stock", "On-hand minus blocked minus reserved must be nonnegative.", int(row.on_hand < row.blocked + row.reserved))
        add("conflicting_snapshot", "All stock snapshots must match the dataset as-of date.", int(row.as_of != as_of))
    for name in ("open_orders", "open_transfers", "payables"):
        add("undeclared_empty", f"Empty {name} must be explicitly declared.", int(not getattr(data, name) and name not in data.declared_empty))
        add("conflicting_empty", f"{name} is declared empty but contains records.", int(bool(getattr(data, name)) and name in data.declared_empty))
    external_ids = [r.external_id for r in data.open_orders + data.open_transfers]
    add("duplicate_external_id", "PO and movement external IDs must be globally unique.", len(external_ids) - len(set(external_ids)))
    for r in data.open_orders + data.open_transfers:
        add("transaction_dates", "Dispatch/arrival dates are reversed or instantaneous.", int(r.arrival_date <= r.dispatch_date))
        if hasattr(r, "order_date"):
            add("transaction_dates", "Order cannot follow dispatch.", int(r.order_date > r.dispatch_date))
            add("direct_to_store", "Supplier purchases must arrive at the DC.", int(r.destination in locations and locations[r.destination].kind != "dc"))
        add("received_stock", "Received transactions have zero remaining units and an arrival no later than as-of.", int(r.status == "received" and (r.remaining_units != 0 or r.arrival_date > as_of)))
        add("overdue_receipt", "Unreceived arrivals before as-of require a corrected arrival date.", int(r.status != "received" and r.arrival_date < as_of))
        add("arrival_envelope", "Open receipts beyond the 56-day horizon require an extended model.", int(r.arrival_date >= as_of + timedelta(days=56)))
    for p in data.payables:
        add("unknown_payable_link", "Payable must link to a supplied PO or movement, including received records.", int(p.linked_external_id not in external_ids))
    for s in data.suppliers:
        add("capacity_unit", "A shared capacity and its unit must both be supplied or both be unknown.", int((s.shared_daily_capacity is None) != (s.shared_capacity_unit is None)))
    for o in data.supplier_offers:
        add("offer_dates", "Offer validity dates are reversed.", int(o.valid_to < o.valid_from))
        add("pack_conversion", "Offer pack must match the product base-unit case conversion; MOQ must be a case multiple.", int(o.sku in products and (o.case_size != products[o.sku].case_size or o.moq_units % o.case_size != 0)))
    for c in data.supplier_capacity:
        add("shared_reference", "Capacity shared limit reference must identify its supplier with a declared limit.", int(c.shared_limit_reference is not None and (c.shared_limit_reference != c.supplier_id or c.supplier_id not in suppliers or suppliers[c.supplier_id].shared_daily_capacity is None)))
    add("unknown_capacity", "Missing supplier/lane capacity is unknown, never unlimited; planning must validate dated coverage.", int(not data.supplier_capacity or any(l.capacity_units is None for l in data.transfer_lanes)), "warning")
    for lane in data.transfer_lanes:
        add("lane", "Transfer lane must have different endpoints and valid SKU restrictions.", int(lane.source == lane.destination or any(s not in products for s in lane.allowed_skus)))
    for b in data.budgets:
        add("budget_week", "Budget week_start must be a Monday.", int(b.week_start.weekday() != 0))
    last_due = max([as_of + timedelta(days=89)] + [p.due_date for p in data.payables])
    required_weeks = set()
    day = as_of
    while day <= last_due:
        required_weeks.add(day - timedelta(days=day.weekday()))
        day += timedelta(days=1)
    missing_weeks = required_weeks - {b.week_start for b in data.budgets}
    add("funding_coverage", "Funding must cover at least 90 days and all declared payable dates.", len(missing_weeks), "error" if data.settings.funding_mode == "funded" else "warning")
    if data.settings.funding_mode == "unfunded_exploration":
        add("unfunded", "Unfunded exploration: no funded plan acceptance is permitted.", severity="warning")
    for b in data.budgets:
        due = sum(p.amount for p in data.payables if b.week_start <= p.due_date < b.week_start + timedelta(days=7))
        add("existing_payment_breach", "Existing obligations exceed a weekly payment ceiling.", int(due > b.payment_ceiling), "error" if data.settings.funding_mode == "funded" else "warning")
    for e in data.events:
        add("event_dates", "Event end cannot precede start.", int(e.end < e.start))
        valid_scope = e.scope_id in (products if e.scope == "sku" else {p.category for p in data.products} if e.scope == "category" else {l.location_id for l in data.locations if l.kind == "store"})
        add("event_scope", "Event scope must refer to an existing SKU, category or store.", int(not valid_scope))
    for a in data.assortment:
        if a.sku not in products:
            continue
        matching = [e for e in data.events if event_matches(e, products[a.sku], a.location_id)]
        for i, e in enumerate(matching):
            for other in matching[i + 1:]:
                add("overlapping_events", "Overlapping event/override rules affect the same SKU-store-date.", int(max(e.start, other.start) <= min(e.end, other.end)))
    # Aggregate repeated issues to keep API errors bounded and avoid raw-row disclosure.
    grouped = {}
    for issue in issues:
        key = (issue.severity, issue.code, issue.message)
        if key in grouped:
            grouped[key].count += issue.count
        else:
            grouped[key] = issue
    return list(grouped.values())
