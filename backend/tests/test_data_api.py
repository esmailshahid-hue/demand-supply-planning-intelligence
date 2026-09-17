from datetime import timedelta
from hashlib import sha256
from fastapi.testclient import TestClient
import pytest
from backend.app.contracts import Dataset
from backend.app.data.sample import generate_bundle, generate_sample
from backend.app.data.validation import validate_dataset
from backend.app.main import app, calculation_slot, MAX_BODY_BYTES

client = TestClient(app)


def codes(data):
    return {i.code for i in validate_dataset(data) if i.severity == "error"}


def test_fixture_is_reproducible_valid_and_truth_is_separate(dataset):
    bundle = generate_bundle()
    assert bundle.inputs == dataset
    assert generate_sample(seed=98) != dataset
    assert not codes(dataset)
    payload = dataset.model_dump_json()
    assert "true_demand" not in payload and "validation_labels" not in payload
    assert any(r["day"] >= dataset.settings.as_of.isoformat() for r in bundle.truth)
    assert max(r.day for r in dataset.demand_history) < dataset.settings.as_of
    with pytest.raises(ValueError):
        Dataset.model_validate({**dataset.model_dump(), "truth":bundle.truth})


def test_full_sample_dimensions_and_cases_are_operational_inputs():
    bundle = generate_bundle("full")
    d = bundle.inputs
    assert (len(d.products),len(d.locations),len(d.suppliers)) == (60,5,12)
    assert len(d.demand_history) == 99160
    assert not codes(d)
    assert len(bundle.validation_labels) == 10
    assert any(c.sku == "SKU004" and c.available_units == 0 for c in d.supplier_capacity)
    assert next(o for o in d.supplier_offers if o.sku=="SKU006").moq_units == 600
    assert any(e.start == d.settings.as_of+timedelta(days=28) for e in d.events)
    assert any(p.linked_external_id == "PO-RECEIVED-001" for p in d.payables)
    assert len(d.model_dump_json().encode()) < MAX_BODY_BYTES


@pytest.mark.parametrize("mutation,expected", [
    (lambda d: d.demand_history.append(d.demand_history[0]), "duplicate_key"),
    (lambda d: setattr(d.inventory[0],"blocked",99999), "negative_usable_stock"),
    (lambda d: setattr(d.inventory[0],"as_of",d.settings.as_of-timedelta(days=1)), "conflicting_snapshot"),
    (lambda d: setattr(d.demand_history[0],"sku","MISSING"), "unknown_sku"),
    (lambda d: d.budgets.clear(), "funding_coverage"),
    (lambda d: d.declared_empty.clear(), "undeclared_empty"),
    (lambda d: setattr(d.supplier_offers[0],"case_size",7), "pack_conversion"),
    (lambda d: setattr(d.suppliers[0],"shared_capacity_unit",None), "capacity_unit"),
    (lambda d: setattr(d.open_orders[0],"arrival_date",d.settings.as_of+timedelta(days=57)), "arrival_envelope"),
    (lambda d: d.events.append(d.events[0].model_copy(update={"event_id":"OVERLAP"})), "overlapping_events"),
    (lambda d: setattr(d.open_orders[1],"remaining_units",10), "received_stock"),
])
def test_block_invalid_data(dataset,mutation,expected):
    mutation(dataset)
    assert expected in codes(dataset)


def test_absent_rows_warn_but_zero_sales_do_not(dataset):
    dataset.demand_history = [r for r in dataset.demand_history if r.sku != "SKU001"]
    warning = next(i for i in validate_dataset(dataset) if i.code == "missing_history")
    assert warning.count >= 420*4
    dataset.settings.funding_mode = "unfunded_exploration"
    dataset.budgets = []
    assert "funding_coverage" not in codes(dataset)
    assert any(i.code == "unfunded" for i in validate_dataset(dataset))


def test_real_api_result_and_unique_recalculation_ids():
    first = client.post("/api/forecast/sample", json={}).json()
    second = client.post("/api/forecast/sample", json={}).json()
    assert len(first["forecast"]) == 56
    assert first["visible_units"] == sum(p["forecast_units"] for p in first["forecast"][:28])
    assert first["run_id"] != second["run_id"]
    assert first["input_hash"] == second["input_hash"]
    assert first["selection"] == second["selection"]
    assert "truth" not in first


def test_custom_api_validates_and_does_not_mutate_input(dataset):
    digest = sha256(dataset.model_dump_json().encode()).hexdigest()
    result = client.post("/api/forecast",json={"dataset":dataset.model_dump(mode="json"),"sku":"SKU001","location_id":"S1"})
    assert result.status_code == 200
    assert result.json()["input_hash"] == digest
    assert sha256(dataset.model_dump_json().encode()).hexdigest() == digest
    dataset.inventory[0].blocked = 99999
    result = client.post("/api/forecast",json={"dataset":dataset.model_dump(mode="json"),"sku":"SKU001","location_id":"S1"})
    assert result.status_code == 422
    assert result.json()["code"] == "invalid_dataset"


def test_api_bounds_unknown_series_busy_and_safe_errors():
    assert client.post("/api/forecast/sample",json={"sku":"MISSING"}).status_code == 422
    assert client.post("/api/forecast/sample",json={"location_id":"DC"}).status_code == 422
    response = client.post("/api/forecast/sample",json={"private_row":"DO_NOT_ECHO"})
    assert response.status_code == 422
    assert "DO_NOT_ECHO" not in response.text
    assert client.post("/api/forecast",content=b"{}",headers={"Content-Length":str(MAX_BODY_BYTES+1)}).status_code == 413
    assert client.get("/api/sample?size=unknown").status_code == 422
    calculation_slot.acquire()
    try:
        assert client.post("/api/forecast/sample",json={}).status_code == 429
    finally:
        calculation_slot.release()
    assert client.get("/api/not-real").status_code == 404


def test_health_and_schema():
    assert client.get("/api/health").json()["capabilities"] == ["forecast", "planning"]
    assert "/api/forecast" in client.get("/openapi.json").json()["paths"]
