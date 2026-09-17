from datetime import date
from typing import Literal
from pydantic import Field
from backend.app.contracts import Contract, Dataset, BufferEvidence, Issue


class PlanRequest(Contract):
    dataset: Dataset


class PlanSampleRequest(Contract):
    size: Literal['fixture', 'full'] = 'fixture'


class Purchase(Contract):
    action_id: str
    offer_id: str
    sku: str
    supplier_id: str
    destination: str
    units: int = Field(gt=0, strict=True)
    order_date: date
    dispatch_date: date
    arrival_date: date
    value: float
    reason: str = 'Supply network demand and store protection buffers.'


class Movement(Contract):
    action_id: str
    sku: str
    source: str
    destination: str
    units: int = Field(gt=0, strict=True)
    dispatch_date: date
    arrival_date: date
    reason: str = 'Allocate dated shared stock to store demand within donor protection.'


class Failure(Contract):
    code: str
    message: str
    sku: str | None = None
    location_id: str | None = None
    supplier_id: str | None = None
    day: date | None = None
    action_id: str | None = None


class Payment(Contract):
    reference: str
    due_date: date
    kind: Literal['existing', 'deposit', 'balance', 'movement']
    amount: float


class CashWeek(Contract):
    week_start: date
    commitments: float
    commitment_cap: float | None
    commitment_headroom: float | None
    existing_payments: float
    new_payments: float
    total_payments: float
    payment_ceiling: float | None
    payment_headroom: float | None
    movement_fees: float
    transfer_budget: float | None
    transfer_headroom: float | None


class StockDay(Contract):
    sku: str
    location_id: str
    day: date
    opening: float
    receipts: float
    demand: float
    fulfilled: float
    unmet: float
    dispatched: float
    closing: float


class Service(Contract):
    sku: str
    location_id: str
    service_class: str
    must_stock: bool
    demand: float
    fulfilled: float
    unmet: float
    tail_unmet: float
    fill_pct: float | None
    target: float
    buffer_units: float
    unconstrained_need: float
    reason_codes: list[str]


class Summary(Contract):
    demand: float
    fulfilled: float
    unmet: float
    fill_pct: float | None
    tail_demand: float
    tail_unmet: float
    commitments: float
    visible_commitments: float
    tail_commitments: float
    payments: float
    visible_payments: float
    later_payments: float
    movement_expense: float
    ending_stock: float
    ending_inventory_investment: float
    revenue_exposure: float
    weekly_buffer_deficit: float
    terminal_excess_units: float


class ServiceGroup(Contract):
    location_id: str
    service_class: str
    must_stock: bool
    window: Literal['visible', 'tail']
    demand: float
    fulfilled: float
    target: float
    target_shortfall: float


class Replay(Contract):
    feasible: bool
    failures: list[Failure]
    summary: Summary
    cash: list[CashWeek]
    payments: list[Payment]
    service: list[Service]
    service_groups: list[ServiceGroup]
    stock: list[StockDay]


class PolicyResult(Contract):
    name: str
    purchases: list[Purchase]
    movements: list[Movement]
    replay: Replay


class ForecastTrace(Contract):
    sku: str
    location_id: str
    run_id: str
    input_hash: str
    method: str
    status: str
    buffer: BufferEvidence


class SolverStage(Contract):
    name: str
    status: str
    objective: float | None = None
    gap: float | None = None
    elapsed_ms: float


class PlanResult(Contract):
    run_id: str
    input_hash: str
    dataset_id: str
    synthetic: bool
    as_of: date
    horizon_days: int = 56
    visible_days: int = 28
    release_days: int = 7
    payment_through: date
    engine_version: str = 'planning-0.2.0'
    status: Literal['feasible', 'feasible_fallback', 'invalid_inputs', 'invalid_plan']
    proposed: PolicyResult | None = None
    benchmark: PolicyResult | None = None
    no_action: PolicyResult | None = None
    forecasts: list[ForecastTrace] = []
    stages: list[SolverStage] = []
    issues: list[Issue] = []
    failures: list[Failure] = []
    exceptions: list[Failure] = []
    assumptions: list[str] = []
    elapsed_ms: float
