"""Deterministic store context for pooled-DC purchase evidence."""
from collections import defaultdict
from datetime import timedelta

from backend.app.planning.contracts import EvidenceTarget
from backend.app.simulation.replay import EPS


def purchase_evidence_targets(data, ledger, purchases):
    """Choose a store demand context from the selected policy's replay.

    Purchases arrive into pooled DC stock, so this never claims a dedicated
    store destination. A target is emitted only when a dated lane and a
    replay-backed shortage or replenishment need establish the relationship.
    """
    locations = {row.location_id: row for row in data.locations}
    services = {(row.sku, row.location_id): row for row in ledger.service}
    stock = defaultdict(list)
    for row in ledger.stock:
        stock[row.sku, row.location_id].append(row)
    targets = []
    for purchase in purchases:
        candidates = []
        for assortment in data.assortment:
            if assortment.sku != purchase.sku:
                continue
            lane = next((lane for lane in data.transfer_lanes
                if lane.source == purchase.destination
                and lane.destination == assortment.location_id
                and purchase.sku in lane.allowed_skus), None)
            if lane is None:
                continue
            dispatch = purchase.arrival_date
            arrival = None
            for _ in range(28):
                candidate = dispatch + timedelta(days=lane.transit_days)
                if (dispatch.weekday() in lane.dispatch_weekdays
                        and dispatch.weekday() in locations[lane.source].open_weekdays
                        and candidate.weekday() in locations[lane.destination].open_weekdays):
                    arrival = candidate
                    break
                dispatch += timedelta(days=1)
            if arrival is None or arrival > data.settings.as_of + timedelta(days=55):
                continue
            rows = sorted(stock[purchase.sku, assortment.location_id], key=lambda row: row.day)
            shortage = next((row for row in rows if row.day >= arrival and row.unmet > EPS), None)
            service = services.get((purchase.sku, assortment.location_id))
            candidates.append((assortment.location_id, arrival, shortage, service))
        shortages = [row for row in candidates if row[2] is not None]
        if shortages:
            location_id, _, shortage, _ = min(
                shortages, key=lambda row: (row[2].day, -row[2].unmet, row[0]))
            targets.append(EvidenceTarget(action_id=purchase.action_id, sku=purchase.sku,
                location_id=location_id, basis='earliest_shortage',
                shortage_date=shortage.day, affected_units=shortage.unmet))
            continue
        needs = [row for row in candidates if row[3] is not None and row[3].unconstrained_need > EPS]
        if needs:
            location_id, _, _, service = min(
                needs, key=lambda row: (-row[3].unconstrained_need, row[0]))
            targets.append(EvidenceTarget(action_id=purchase.action_id, sku=purchase.sku,
                location_id=location_id, basis='greatest_replenishment_need',
                affected_units=service.unconstrained_need))
            continue
        targets.append(EvidenceTarget(action_id=purchase.action_id, sku=purchase.sku,
            basis='no_store_association'))
    return targets
