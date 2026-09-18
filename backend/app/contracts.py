"""Normalized base-unit/SAR contracts. Dates are Asia/Riyadh business dates."""
from datetime import date
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, model_validator

SCHEMA_VERSION = "1.0.0"
ENGINE_VERSION = "0.1.0"
NonNegative = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Positive = Annotated[float, Field(gt=0, allow_inf_nan=False)]
Units = Annotated[int, Field(ge=0, strict=True)]
Pack = Annotated[int, Field(gt=0, strict=True)]
ID = Annotated[str, Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")]
Weekday = Annotated[int, Field(ge=0, le=6)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Product(Contract):
    sku: ID
    name: str
    base_unit: Literal["unit"] = "unit"
    case_size: Pack
    volume_per_unit: Positive
    cost_per_base_unit: NonNegative
    net_price_per_base_unit: NonNegative
    category: str
    active_from: date
    active_to: date | None = None


class Location(Contract):
    location_id: ID
    name: str
    kind: Literal["dc", "store"]
    storage_volume: Positive
    open_weekdays: list[Weekday] = Field(min_length=1, max_length=7)


class Assortment(Contract):
    sku: ID
    location_id: ID
    ranged_from: date
    ranged_to: date | None = None
    service_class: Literal["A", "B", "C"]
    must_stock: bool
    launch_daily_units: NonNegative | None = None
    launch_known_at: AwareDatetime | None = None
    launch_reason: str | None = None


class Observation(Contract):
    sku: ID
    location_id: ID
    day: date
    sales_units: NonNegative | None
    is_open: bool
    stock_available: bool | None
    event_id: ID | None = None
    available_at: AwareDatetime


class Inventory(Contract):
    sku: ID
    location_id: ID
    as_of: date
    on_hand: Units
    blocked: Units
    reserved: Units
    book_unit_cost: NonNegative


class OpenOrder(Contract):
    external_id: ID
    sku: ID
    supplier_id: ID
    destination: ID
    remaining_units: Units
    order_date: date
    dispatch_date: date
    arrival_date: date
    status: Literal["confirmed", "dispatched", "received"]
    cost_per_base_unit: NonNegative


class OpenTransfer(Contract):
    external_id: ID
    sku: ID
    source: ID
    destination: ID
    remaining_units: Units
    dispatch_date: date
    arrival_date: date
    status: Literal["confirmed", "dispatched", "received"]


class Supplier(Contract):
    supplier_id: ID
    name: str
    minimum_order_value: NonNegative
    shared_daily_capacity: NonNegative | None = None
    shared_capacity_unit: Literal["base_units", "volume"] | None = None


class SupplierOffer(Contract):
    offer_id: ID
    supplier_id: ID
    sku: ID
    valid_from: date
    valid_to: date
    price_per_base_unit: NonNegative
    case_size: Pack
    moq_units: Units
    lead_time_days: Annotated[int, Field(ge=1, le=14)]
    dispatch_weekdays: list[Weekday] = Field(min_length=1, max_length=7)
    order_weekdays: list[Weekday] = Field(min_length=1, max_length=7)
    deposit_fraction: Annotated[float, Field(ge=0, le=1)]
    balance_days_after_receipt: Annotated[int, Field(ge=0, le=30)]


class SupplierCapacity(Contract):
    supplier_id: ID
    sku: ID
    dispatch_date: date
    available_units: Units
    shared_limit_reference: ID | None = None


class TransferLane(Contract):
    source: ID
    destination: ID
    transit_days: Literal[1, 2]
    dispatch_weekdays: list[Weekday] = Field(min_length=1, max_length=7)
    capacity_units: Units | None
    grouped_dispatch_fee: NonNegative
    pack_units: Pack
    allowed_skus: list[ID]


class Payable(Contract):
    external_id: ID
    linked_external_id: ID
    due_date: date
    amount: NonNegative


class Budget(Contract):
    week_start: date
    new_commitment_cap: NonNegative
    payment_ceiling: NonNegative
    transfer_budget: NonNegative


class Event(Contract):
    event_id: ID
    scope: Literal["sku", "category", "store"]
    scope_id: str
    start: date
    end: date
    kind: Literal["uplift", "replacement"]
    value: NonNegative
    reason: str = Field(min_length=1)
    known_at: AwareDatetime


class Settings(Contract):
    as_of: date
    history_days: Annotated[int, Field(ge=1, le=420)] = 420
    timezone: Literal["Asia/Riyadh"] = "Asia/Riyadh"
    currency: Literal["SAR"] = "SAR"
    visible_days: Literal[28] = 28
    horizon_days: Literal[56] = 56
    release_days: Literal[7] = 7
    review_period_days: Literal[7] = 7
    protection_days: Annotated[int, Field(ge=1, le=28)] = 14
    buffer_percentile: Annotated[float, Field(ge=0, le=100)] = 90
    fallback_buffer_days: NonNegative = 3
    annual_holding_rate: NonNegative = 0.2
    class_targets: dict[str, float] = Field(default_factory=lambda: {"A": .98, "B": .95, "C": .90})
    funding_mode: Literal["funded", "unfunded_exploration"] = "funded"

    @model_validator(mode="after")
    def valid_targets(self):
        if set(self.class_targets) != {"A", "B", "C"} or any(not 0 <= v <= 1 for v in self.class_targets.values()):
            raise ValueError("Class targets must contain A, B and C fractions between zero and one")
        return self


class Dataset(Contract):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    dataset_id: ID
    synthetic: bool
    products: list[Product] = Field(min_length=1, max_length=60)
    locations: list[Location] = Field(min_length=2, max_length=5)
    assortment: list[Assortment] = Field(min_length=1, max_length=240)
    demand_history: list[Observation] = Field(max_length=100800)
    inventory: list[Inventory] = Field(max_length=300)
    suppliers: list[Supplier] = Field(max_length=12)
    supplier_offers: list[SupplierOffer] = Field(max_length=720)
    supplier_capacity: list[SupplierCapacity] = Field(max_length=40320)
    transfer_lanes: list[TransferLane] = Field(max_length=20)
    open_orders: list[OpenOrder] = Field(max_length=5000)
    open_transfers: list[OpenTransfer] = Field(max_length=5000)
    payables: list[Payable] = Field(max_length=10000)
    budgets: list[Budget] = Field(max_length=30)
    events: list[Event] = Field(max_length=100)
    settings: Settings
    declared_empty: list[Literal["open_orders", "open_transfers", "payables"]]


class DatasetDimensions(Contract):
    products: int = Field(ge=1, le=60)
    locations: int = Field(ge=2, le=5)
    assortment: int = Field(ge=1, le=240)
    history_rows: int = Field(ge=0, le=100800)


class DatasetProvenance(Contract):
    source: Literal["bundled_fixture", "bundled_full", "uploaded", "portable"]
    sample_size: Literal["fixture", "full"] | None = None
    dataset_id: str
    dataset_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    dimensions: DatasetDimensions

    @model_validator(mode="after")
    def source_matches_size(self):
        expected = {"bundled_fixture": "fixture", "bundled_full": "full"}.get(self.source)
        if expected != self.sample_size:
            if expected is not None or self.sample_size is not None:
                raise ValueError("Only bundled datasets have a matching sample size.")
        return self


class Issue(Contract):
    severity: Literal["error", "warning"]
    code: str
    message: str
    count: int = 1


class ForecastRequest(Contract):
    dataset: Dataset
    sku: ID
    location_id: ID


class SampleRequest(Contract):
    size: Literal["fixture", "full"] = "fixture"
    sku: ID = "SKU001"
    location_id: ID = "S1"


Method = Literal["seasonal_naive", "weekday_mean", "weighted_weekday_mean"]


class Metrics(Contract):
    horizon: int
    windows: int
    complete_windows: int
    valid_observations: int
    excluded_observations: int
    excluded_by_reason: dict[str, int]
    absolute_error: float | None
    actual_units: float
    wape: float | None
    signed_bias_units: float | None
    signed_bias_pct: float | None
    mean_absolute_quantity_error: float | None
    mean_quantity_bias: float | None


class WindowRecord(Contract):
    origin: date
    horizon: int
    complete: bool
    valid_observations: int
    excluded_by_reason: dict[str, int]
    actual_units: float
    forecast_units: float
    absolute_error: float
    signed_error: float
    underforecast_units: float | None


class CandidateRecord(Contract):
    method: Method
    metrics: list[Metrics]
    windows: list[WindowRecord]


class ForecastDay(Contract):
    day: date
    baseline_units: float | None
    forecast_units: float | None
    provisional_tail: bool
    fallback: str | None
    event_id: str | None
    reason: str | None


class HistoryDay(Contract):
    day: date
    observed_sales: float | None
    training_estimate: float | None
    status: str


class BufferEvidence(Contract):
    units: float | None
    method: Literal["empirical_underforecast", "days_of_demand", "unavailable"]
    protection_days: int
    percentile: float
    sample_count: int
    fallback_days: float | None
    note: str


class ForecastResult(Contract):
    schema_version: str = SCHEMA_VERSION
    engine_version: str = ENGINE_VERSION
    run_id: str
    input_hash: str
    dataset_id: str
    synthetic: bool
    as_of: date
    sku: str
    product_name: str
    location_id: str
    location_name: str
    selected_method: Method
    status: Literal["evaluated", "provisional", "unavailable"]
    selection_reason: str
    selection_cutoff: date
    improvement_pct: float | None
    selection: list[CandidateRecord]
    final_check: list[CandidateRecord]
    forecast: list[ForecastDay]
    history: list[HistoryDay]
    visible_units: float | None
    tail_units: float | None
    buffer: BufferEvidence
    warnings: list[Issue]
    elapsed_ms: float
    evaluation_policy: str


class SampleCatalog(Contract):
    dataset_id: str
    as_of: date
    products: list[Product]
    locations: list[Location]
    history_rows: int
    warnings: list[Issue]


class APIError(Contract):
    code: str
    message: str
    issues: list[Issue] = []
