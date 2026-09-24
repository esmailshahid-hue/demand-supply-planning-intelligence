"""Versioned review drafts. Decisions constrain a fresh solve, never mutate a ledger."""
from datetime import datetime, timezone
from decimal import Decimal
from time import perf_counter
from typing import Literal
from uuid import uuid4
from pydantic import Field
from backend.app.contracts import Contract, Dataset
from backend.app.planning.contracts import PlanResult, Purchase, Movement, Failure
from backend.app.planning.constraints import ReviewConstraints, business_key
from backend.app.planning.engine import plan
from backend.app.planning.inputs import network_forecasts
from backend.app.scenarios.contracts import ScenarioDefinition
from backend.app.scenarios.engine import dataset_hash, digest, transform, adjust_forecasts, forecast_versions
from backend.app.simulation.replay import replay, cents


class Decision(Contract):
    source_run_id: str
    input_hash: str
    assumption_version: str
    action_type: Literal['purchase', 'movement']
    business_key: str
    original: Purchase | Movement
    original_quantity: int
    reviewed_quantity: int | None = None
    status: Literal['draft', 'accepted', 'rejected', 'edited_quantity', 'stale']
    timestamp: datetime
    note: str = Field(default='', max_length=1000)
    disposition: Literal['pending', 'retained', 'conflicted', 'unnecessary'] = 'pending'


class Draft(Contract):
    revision: str
    state: Literal['draft', 'stale', 'accepted', 'read_only'] = 'draft'
    base_input_hash: str
    assumption_version: str
    scenario: ScenarioDefinition = Field(default_factory=ScenarioDefinition)
    result: PlanResult
    decisions: list[Decision] = Field(default_factory=list)
    failures: list[Failure] = Field(default_factory=list)
    accepted_version: str | None = None
    acknowledged_shortfalls: bool = False
    execution_rejections: list[str] = Field(default_factory=list)
    execution_remainders: list[Purchase | Movement] = Field(default_factory=list)
    input_source: Literal['bundled','uploaded','portable'] = 'bundled'


class ReviewConflict(ValueError):
    def __init__(self, failures):
        self.failures = failures
        super().__init__('Resolve the reviewed-action conflicts before acceptance.')


def prepare(data, scenario):
    changed, definition, _ = transform(data, scenario)
    # Match Pass 3: only future-path changes require a different forecast envelope.
    raw = network_forecasts(changed if any(d.future_paths for d in definition.delays) else data, perf_counter()+30)
    prepared = adjust_forecasts(changed, definition, raw)
    if prepared[3]: raise ReviewConflict(prepared[3])
    return changed, prepared


def new_draft(data, result, scenario=None):
    definition = scenario or ScenarioDefinition()
    return Draft(revision=str(uuid4()), base_input_hash=dataset_hash(data), assumption_version=digest({'input': dataset_hash(data), 'scenario': definition.model_dump(mode='json')}), scenario=definition, result=result)


def ensure_current(draft, revision, data):
    if draft.revision != revision or draft.base_input_hash != dataset_hash(data):
        raise ReviewConflict([Failure(code='stale_review', message='Dataset or draft version changed. Create a new draft and review again.')])
    if draft.state in ('accepted', 'read_only'):
        raise ReviewConflict([Failure(code='immutable_accepted', message='Accepted versions are read-only. Explicitly create a new draft first.')])


def decide(draft, data, revision, action_id, status, quantity=None, note=''):
    ensure_current(draft, revision, data)
    if status not in ('accepted', 'rejected', 'edited_quantity', 'draft'):
        raise ReviewConflict([Failure(code='review_status', message='Choose a supported review state.')])
    actions = draft.result.proposed
    action = next((a for a in actions.purchases+actions.movements if a.action_id == action_id), None) if actions else None
    if action is None:
        action = next((d.original for d in draft.decisions if d.original.action_id == action_id), None)
    if action is None: raise ReviewConflict([Failure(code='unknown_action', message='Select an action from this draft.')])
    changed, _, _ = transform(data, draft.scenario)
    edited = action.model_copy(deep=True)
    if status == 'edited_quantity':
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
            raise ReviewConflict([Failure(code='review_quantity', message='Reviewed quantity must be a positive integer; it is never rounded.')])
        edited.units = quantity
        if isinstance(edited, Purchase):
            offer = next(o for o in changed.supplier_offers if o.offer_id == edited.offer_id)
            if quantity % offer.case_size or quantity < offer.moq_units:
                raise ReviewConflict([Failure(code='purchase_pack_moq', message=f'Use a multiple of {offer.case_size} and at least {offer.moq_units} base units.', action_id=action_id)])
            edited.value = cents(Decimal(str(offer.price_per_base_unit))*quantity)/100
        else:
            lane = next(l for l in changed.transfer_lanes if (l.source,l.destination) == (edited.source,edited.destination))
            if quantity % lane.pack_units:
                raise ReviewConflict([Failure(code='movement_pack', message=f'Use a multiple of {lane.pack_units} base units.', action_id=action_id)])
    result = draft.model_copy(deep=True)
    key = business_key(action)
    if key in draft.execution_rejections:
        raise ReviewConflict([Failure(code='confirmed_execution',message='This proposal was replaced by a confirmed transaction and cannot be restored by a review decision.')])
    remainder = next((a for a in draft.execution_remainders if business_key(a) == key), None)
    if remainder is not None and status in ('accepted', 'edited_quantity') and edited.units > remainder.units:
        raise ReviewConflict([Failure(code='confirmed_execution',message='Reviewed quantity exceeds the explicitly unconfirmed remainder. Import updated reconciliation evidence first.')])
    previous = next((d for d in result.decisions if d.business_key == key), None)
    original = previous.original if previous else action
    result.decisions = [d for d in result.decisions if d.business_key != key]
    if status != 'draft':
        result.decisions.append(Decision(source_run_id=draft.result.run_id, input_hash=draft.result.input_hash,
            assumption_version=draft.assumption_version, action_type='purchase' if isinstance(action,Purchase) else 'movement',
            business_key=key, original=original, original_quantity=original.units,
            reviewed_quantity=edited.units if status == 'edited_quantity' else action.units if status == 'accepted' else None,
            status=status, timestamp=datetime.now(timezone.utc), note=note))
    result.state='stale'; result.revision=str(uuid4()); result.failures=[]
    for d in result.decisions: d.disposition='pending'
    return result


def constraints(draft, data):
    result=ReviewConstraints(rejected=set(draft.execution_rejections))
    overridden = {d.business_key for d in draft.decisions if d.status != 'draft'}
    for action in draft.execution_remainders:
        if business_key(action) not in overridden:
            (result.purchases if isinstance(action, Purchase) else result.movements).append(action.model_copy(deep=True))
    for decision in draft.decisions:
        if decision.assumption_version != draft.assumption_version or decision.status == 'stale':
            raise ReviewConflict([Failure(code='stale_review', message='Review assumptions changed; review this decision again.')])
        if decision.status == 'rejected': result.rejected.add(decision.business_key); continue
        if decision.status == 'draft': continue
        action=decision.original.model_copy(deep=True)
        action.units=decision.reviewed_quantity or decision.original_quantity
        if isinstance(action,Purchase):
            offer=next(o for o in data.supplier_offers if o.offer_id==action.offer_id)
            action.value=cents(Decimal(str(offer.price_per_base_unit))*action.units)/100
            result.purchases.append(action)
        else: result.movements.append(action)
    return result


def regenerate(draft, data, revision):
    ensure_current(draft,revision,data)
    changed,prepared=prepare(data,draft.scenario)
    locked=constraints(draft,changed)
    result=draft.model_copy(deep=True)
    result.result=plan(changed,prepared_forecasts=prepared,review=locked)
    result.failures=list(result.result.failures)
    result.state='draft' if result.result.proposed and result.result.proposed.replay.feasible and not result.failures else 'stale'
    result.revision=str(uuid4())
    for decision in result.decisions:
        decision.disposition='retained' if result.state=='draft' else 'conflicted'
    return result


def accept(draft,data,revision,acknowledge=False):
    ensure_current(draft,revision,data)
    if draft.state!='draft' or draft.failures or not draft.result.proposed or draft.result.status not in ('feasible','feasible_fallback'):
        raise ReviewConflict([Failure(code='unaccepted_plan',message='Regenerate a current, independently valid draft before final acceptance.')])
    changed,prepared=prepare(data,draft.scenario)
    if dataset_hash(changed)!=draft.result.input_hash:
        raise ReviewConflict([Failure(code='stale_input',message='Plan input differs from the current scenario/dataset.')])
    actions=draft.result.proposed
    failures=constraints(draft,changed).failures(actions.purchases,actions.movements)
    checked=replay(changed,*prepared[:2],actions.purchases,actions.movements)
    failures+=checked.failures
    explanation_fields={'reason_codes','reason_summary','shortage_evidence'}
    if (checked.model_dump(exclude={'service'}) != actions.replay.model_dump(exclude={'service'})
            or [s.model_dump(exclude=explanation_fields) for s in checked.service] != [s.model_dump(exclude=explanation_fields) for s in actions.replay.service]):
        failures.append(Failure(code='replay_mismatch',message='Independent replay no longer equals displayed totals and obligations. Regenerate.'))
    versions=forecast_versions(prepared)
    expected={f'{t.sku}/{t.location_id}':t for t in draft.result.forecasts}
    if set(expected)!=set(versions) or any(expected[f'{t.sku}/{t.location_id}'].input_hash!=t.input_hash or expected[f'{t.sku}/{t.location_id}'].method!=t.method or expected[f'{t.sku}/{t.location_id}'].buffer!=t.buffer for t in prepared[2]):
        failures.append(Failure(code='stale_forecast',message='Forecast versions changed. Regenerate before acceptance.'))
    if failures: raise ReviewConflict(failures)
    s=checked.summary
    if (s.unmet+s.tail_unmet+s.weekly_buffer_deficit>1e-5) and not acknowledge:
        raise ReviewConflict([Failure(code='shortfall_acknowledgement',message='Review and explicitly acknowledge the remaining service/buffer shortfalls. Hard constraints have passed.')])
    result=draft.model_copy(deep=True)
    result.state='accepted';result.accepted_version=str(uuid4());result.revision=str(uuid4());result.acknowledged_shortfalls=acknowledge
    return result, checked, versions
