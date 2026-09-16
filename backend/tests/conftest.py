from datetime import timedelta
import pytest
from backend.app.contracts import Observation
from backend.app.data.sample import generate_sample
from backend.app.forecasting.engine import midnight


@pytest.fixture
def dataset():
    return generate_sample()


@pytest.fixture
def regular(dataset):
    """Independent constant-demand evidence; no built-in sample outcomes used."""
    rows = []
    origin = dataset.settings.as_of
    for i in range(420):
        day = origin - timedelta(days=420-i)
        rows.append(Observation(sku="SKU001", location_id="S1", day=day, sales_units=10,
                                is_open=True, stock_available=True, available_at=midnight(day+timedelta(days=1))))
    dataset.demand_history = rows
    dataset.events = []
    return dataset
