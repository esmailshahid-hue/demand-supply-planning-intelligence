"""Compact stateless sample comparisons; no history or daily ledgers in requests."""
from datetime import date
from typing import Literal
from pydantic import Field
from backend.app.contracts import Contract, ForecastResult, NonNegative, BufferEvidence
from backend.app.planning.contracts import Purchase, Movement, Summary, CashWeek, Failure, Service, StockDay, Payment, ForecastTrace, SolverStage, EvidenceTarget

class Uplift(Contract):
    scope: Literal['sku','category','store']
    scope_id: str
    start: date
    end: date
    percent: float = Field(ge=0, le=500)

class Delay(Contract):
    supplier_id: str
    days: int = Field(ge=1, le=14, strict=True)
    existing_order_ids: list[str] = Field(default_factory=list, max_length=100)
    future_paths: bool = False

class Availability(Contract):
    supplier_id: str
    start: date
    end: date
    remaining_fraction: float = Field(ge=0, le=1)

class Funding(Contract):
    week_start: date
    commitment: NonNegative | None = None
    payment: NonNegative | None = None

class ScenarioDefinition(Contract):
    uplifts: list[Uplift] = Field(default_factory=list, max_length=20)
    delays: list[Delay] = Field(default_factory=list, max_length=12)
    availability: list[Availability] = Field(default_factory=list, max_length=20)
    funding: list[Funding] = Field(default_factory=list, max_length=30)

class Actions(Contract):
    purchases: list[Purchase] = Field(default_factory=list, max_length=5000)
    movements: list[Movement] = Field(default_factory=list, max_length=10000)

class BaselineSnapshot(Actions):
    size: Literal['fixture','full']
    dataset_hash: str
    version: Literal['sample-scenarios-1'] = 'sample-scenarios-1'
    snapshot_id: str

class Outcome(Actions):
    policy: Literal['original','frozen','replanned']
    assumptions_hash: str
    action_hash: str
    feasible: bool
    status: str
    summary: Summary | None
    cash: list[CashWeek]
    failures: list[Failure]
    shortages: list[Service]
    explanations: list[Failure] = []
    stages: list[SolverStage] = []
    evidence_targets: list[EvidenceTarget] = []

class ActionChange(Contract):
    kind: Literal['purchase','movement']
    change: Literal['added','removed','changed']
    business_key: str
    before: Purchase | Movement | None = None
    after: Purchase | Movement | None = None

class ScenarioRequest(Contract):
    baseline: BaselineSnapshot
    scenario: ScenarioDefinition = Field(default_factory=ScenarioDefinition)

class ScenarioResult(Contract):
    baseline_id: str
    scenario_hash: str
    definition: ScenarioDefinition
    changes: list[str]
    original: Outcome
    frozen: Outcome
    replanned: Outcome
    shock_delta: dict[str,float | None]
    replan_delta: dict[str,float | None]
    forecast_versions: dict[str,str]
    action_changes: list[ActionChange]
    elapsed_ms: float
    note: str = 'Deltas are later minus earlier: frozen − original (shock), replanned − frozen (replanning). Invalid policies have unavailable outcome metrics. Cash shows attempted obligations even when infeasible.'

class BaselineResult(Contract):
    baseline: BaselineSnapshot
    original: Outcome
    as_of: date
    suppliers: list[str]
    supplier_options: list['SupplierOption']
    categories: list[str]
    existing_orders: list[dict[str,str]]
    weeks: list[Funding]
    elapsed_ms: float


class SupplierOption(Contract):
    supplier_id: str
    name: str
    existing_order_ids: list[str]
    future_paths: bool

class DetailRequest(ScenarioRequest):
    policy: Literal['original','frozen','replanned']
    actions: Actions | None = None
    expected_action_hash: str | None = None
    expected_scenario_hash: str | None = None
    sku: str
    location_id: str
    action_id: str | None = None

class Adjustment(Contract):
    day: date
    original: float
    adjusted: float
    reason: str

class ScenarioDetail(Contract):
    baseline_id: str
    scenario_hash: str
    assumptions_hash: str
    action_hash: str
    policy: str
    feasible: bool
    failures: list[Failure]
    forecast: ForecastResult
    forecast_version: str
    policy_buffer: BufferEvidence
    adjustments: list[Adjustment]
    stock: list[StockDay]
    cash: list[CashWeek]
    payments: list[Payment]
    purchases: list[Purchase]
    movements: list[Movement]
    confirmed_receipts: list[dict[str,str]]
    shortages: list[Service]
    elapsed_ms: float
    note: str = 'Stock is pooled by SKU/location. Related receipts and movements are evidence of shared availability, not one-to-one dependencies. Invalid policies suppress stock/service arithmetic; cash retains attempted obligations.'

class CaptureRequest(Actions):
    size: Literal['fixture','full']
    dataset_hash: str
