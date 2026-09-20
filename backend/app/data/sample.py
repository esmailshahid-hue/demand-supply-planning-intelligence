"""Deterministic sample generation. Oracle truth and case labels never enter Dataset."""
from backend.app.diagnostics import timed, measure
from dataclasses import dataclass
from datetime import date, timedelta
from random import Random

from backend.app.contracts import Dataset
from backend.app.forecasting.engine import midnight

SAMPLE_VERSION = "sample-v1"
AS_OF = date(2026, 9, 14)
CASES = {
    "uneven_stock": "SKU001", "censored_history": "SKU002", "dated_promotion": "SKU003",
    "supplier_shortage": "SKU004", "tight_funding": "network", "large_moq": "SKU006",
    "new_product": "SKU007", "late_inbound": "SKU008", "healthy_control": "SKU009",
    "day_29_demand": "SKU010",
}
NAMES = ["Basmati rice · 1 kg", "Still water · 1.5 L", "Arabic coffee · 250 g", "Chickpeas · 400 g",
         "Long-life milk · 1 L", "Olive oil · 500 mL", "Oat drink · 1 L", "Pasta · 500 g",
         "Tomato paste · 200 g", "Date biscuits · 300 g"]


@dataclass
class SyntheticBundle:
    inputs: Dataset
    truth: list[dict]
    validation_labels: dict[str, str]


def generate_bundle(size="fixture", seed=97):
    if size not in ("fixture", "full"):
        raise ValueError("size must be fixture or full")
    rng = Random(seed)
    n = 10 if size == "fixture" else 60
    start = AS_OF - timedelta(days=420)
    products, assortment, history, inventory, offers, capacity = [], [], [], [], [], []
    truth = []
    locations = [dict(location_id="DC", name="Riyadh distribution centre", kind="dc", storage_volume=10000, open_weekdays=list(range(7)))]
    locations += [dict(location_id=f"S{i}", name=name, kind="store", storage_volume=350, open_weekdays=list(range(7)))
                  for i, name in enumerate(["Al Olaya", "Al Malqa", "Al Rawdah", "Al Yasmin"], 1)]
    suppliers = [dict(supplier_id=f"SUP{i:02}", name=f"Sample supplier {i:02}", minimum_order_value=500,
                      shared_daily_capacity=5000, shared_capacity_unit="base_units") for i in range(1, 13)]
    events = [
        dict(event_id="PROMO_PAST", scope="sku", scope_id="SKU003", start=AS_OF-timedelta(days=70), end=AS_OF-timedelta(days=64),
             kind="uplift", value=1.6, reason="Synthetic coffee promotion", known_at=midnight(AS_OF-timedelta(days=90))),
        dict(event_id="PROMO_NEXT", scope="sku", scope_id="SKU003", start=AS_OF+timedelta(days=7), end=AS_OF+timedelta(days=13),
             kind="uplift", value=1.5, reason="Planned synthetic coffee promotion", known_at=midnight(AS_OF-timedelta(days=10))),
        dict(event_id="TAIL_EVENT", scope="sku", scope_id="SKU010", start=AS_OF+timedelta(days=28), end=AS_OF+timedelta(days=34),
             kind="uplift", value=2.0, reason="Synthetic demand beginning on day 29", known_at=midnight(AS_OF-timedelta(days=14))),
    ]
    for index in range(1, n + 1):
        sku = f"SKU{index:03}"
        case_size = 12 if index % 3 == 0 else 10
        cost = 3 + index % 12
        active_from = AS_OF - timedelta(days=10) if index == 7 else start
        products.append(dict(sku=sku, name=NAMES[index-1] if index <= 10 else f"Ambient packaged item {index:02}",
            case_size=case_size, volume_per_unit=.002, cost_per_base_unit=cost, net_price_per_base_unit=cost*1.35,
            category=["Pantry", "Beverages", "Snacks"][index % 3], active_from=active_from))
        supplier = f"SUP{(index - 1) % 12 + 1:02}"
        offers.append(dict(offer_id=f"OFFER{index:03}", supplier_id=supplier, sku=sku, valid_from=start,
            valid_to=AS_OF+timedelta(days=55), price_per_base_unit=cost, case_size=case_size,
            moq_units=case_size * (50 if index == 6 else 2), lead_time_days=14 if index == 8 else 4,
            dispatch_weekdays=list(range(7)), order_weekdays=list(range(7)), deposit_fraction=.5, balance_days_after_receipt=30))
        for offset in range(56):
            capacity.append(dict(supplier_id=supplier, sku=sku, dispatch_date=AS_OF+timedelta(days=offset),
                available_units=0 if index == 4 and offset < 14 else 600, shared_limit_reference=supplier))
        for loc_index, loc in enumerate(locations):
            on_hand = 300 if loc_index == 0 else 90
            if index == 1:
                on_hand = [100, 15, 320, 30, 180][loc_index]
            if index == 8:
                on_hand = 10
            inventory.append(dict(sku=sku, location_id=loc["location_id"], as_of=AS_OF,
                on_hand=on_hand, blocked=0, reserved=0, book_unit_cost=cost))
            if loc_index == 0:
                continue
            assortment.append(dict(sku=sku, location_id=loc["location_id"], ranged_from=active_from,
                service_class=["A", "B", "C"][(index-1) % 3], must_stock=index % 4 == 1,
                launch_daily_units=8 if index == 7 else None,
                launch_known_at=midnight(active_from-timedelta(days=7)) if index == 7 else None,
                launch_reason="Illustrative launch assumption, not measured accuracy" if index == 7 else None))
            # Generate latent demand before imposing stock availability or missing observations.
            latent = []
            for offset in range(476):
                day = start + timedelta(days=offset)
                base = (6 + index % 9 + loc_index) * (1.3 if day.weekday() in (3, 4) else .9)
                base *= 1 + .0006 * offset
                event = next((e for e in events if e["scope_id"] == sku and e["start"] <= day <= e["end"]), None)
                if event:
                    base *= event["value"]
                units = max(0, round(rng.gauss(base, base * .15)))
                if index == 11:
                    units = 0
                if index == 12:
                    units = units if rng.random() < .15 else 0
                if day < active_from:
                    units = 0
                latent.append((day, units, event))
                truth.append(dict(sku=sku, location_id=loc["location_id"], day=day.isoformat(), true_demand=units))
            for day, units, event in latent[:420]:
                if day < active_from:
                    continue
                offset = (day - start).days
                is_open = not (index == 5 and day.weekday() == 4 and offset < 100)
                available = not (index == 2 and offset % 21 in (0, 1, 2))
                stock = units if available else max(0, units // 3)
                missing = index == 5 and offset % 31 == 0
                sales = min(units, stock) if is_open else 0
                history.append(dict(sku=sku, location_id=loc["location_id"], day=day,
                    sales_units=None if missing else sales, is_open=is_open,
                    stock_available=None if missing else available,
                    event_id=event["event_id"] if event else None,
                    available_at=midnight(day + timedelta(days=1)) + timedelta(hours=1)))
    open_orders = [dict(external_id="PO-LATE-001", sku="SKU008", supplier_id="SUP08", destination="DC",
        remaining_units=400, order_date=AS_OF-timedelta(days=1), dispatch_date=AS_OF+timedelta(days=10),
        arrival_date=AS_OF+timedelta(days=13), status="confirmed", cost_per_base_unit=11),
        dict(external_id="PO-RECEIVED-001", sku="SKU009", supplier_id="SUP09", destination="DC", remaining_units=0,
        order_date=AS_OF-timedelta(days=20), dispatch_date=AS_OF-timedelta(days=16), arrival_date=AS_OF-timedelta(days=12),
        status="received", cost_per_base_unit=12)]
    payables = [dict(external_id="PAY-LATE-001", linked_external_id="PO-LATE-001", due_date=AS_OF+timedelta(days=43), amount=2200),
               dict(external_id="PAY-RECEIVED-001", linked_external_id="PO-RECEIVED-001", due_date=AS_OF+timedelta(days=18), amount=1200)]
    monday = AS_OF-timedelta(days=AS_OF.weekday())
    budgets = [dict(week_start=monday+timedelta(days=7*k), new_commitment_cap=1500 if k < 2 else 15000,
                    payment_ceiling=4000 if k < 2 else 18000, transfer_budget=800) for k in range(14)]
    lanes = [dict(source="DC", destination=f"S{i}", transit_days=1 if i < 3 else 2,
                  dispatch_weekdays=list(range(7)), capacity_units=1000, grouped_dispatch_fee=20,
                  pack_units=10, allowed_skus=[p["sku"] for p in products]) for i in range(1, 5)]
    lanes += [dict(source="S2", destination="S1", transit_days=2, dispatch_weekdays=list(range(7)),
                   capacity_units=300, grouped_dispatch_fee=20, pack_units=10, allowed_skus=[p["sku"] for p in products])]
    inputs = Dataset(dataset_id=f"{SAMPLE_VERSION}-{size}-{seed}", synthetic=True, products=products,
        locations=locations, assortment=assortment, demand_history=history, inventory=inventory, suppliers=suppliers,
        supplier_offers=offers, supplier_capacity=capacity, transfer_lanes=lanes, open_orders=open_orders,
        open_transfers=[], payables=payables, budgets=budgets, events=events, settings=dict(as_of=AS_OF), declared_empty=["open_transfers"])
    return SyntheticBundle(inputs=inputs, truth=truth, validation_labels=dict(CASES))


@timed('sample_construction')
def generate_sample(size="fixture", seed=97) -> Dataset:
    return generate_bundle(size, seed).inputs
