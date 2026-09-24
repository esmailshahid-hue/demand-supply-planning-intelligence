"""Full precision reference hashes captured before changes at e51af6f.

These cover every action, explanation, stock/cash/service row, and all forecast
quantities for both sample sizes, rather than only the SKU001 demo result.
"""
import json
from hashlib import sha256
from time import perf_counter
import pytest
from backend.app.main import sample
from backend.app.planning.inputs import network_forecasts
from backend.app.planning.engine import plan
from scripts.planning_smoke import stable_plan


def authoritative(result):
    """Complete calculation evidence excluding only generated IDs/timing."""
    value=result.model_dump(mode='json')
    value.pop('run_id');value.pop('elapsed_ms')
    for trace in value['forecasts']:
        trace.pop('run_id')
    return value

@pytest.mark.parametrize('size,policy_hash,forecast_hash',[
 ('fixture','b98e5ac27b94117555bd5cc538db01348536df75674e2fd4afd441f61ee25dce','e3be2683a27701455fb8a8bdec87e36fa0e669f6c1cf2dedaecacd1e6dc4a489'),
 ('full','1cd6a43f6dc2fd7e19c289672a485cb709a827cb64626d03e82cdc7e2146706e','1fa197074db28021aabb89ad1826b088d0119bccad54546355978cd9d6ba4290')])
def test_full_precision_sample_equivalence(size,policy_hash,forecast_hash):
    def digest(value):return sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    data=sample(size)[0];prepared=network_forecasts(data,perf_counter()+30)
    assert digest(list(prepared[0].values()))==forecast_hash
    result=plan(data,prepared_forecasts=prepared)
    assert digest(stable_plan(result.model_dump(mode='json')))==policy_hash


@pytest.mark.parametrize('size',['fixture','full'])
def test_projected_hash_is_exact_complete_pydantic_identity(size):
    from backend.app.forecasting.identity import ProjectedIdentity
    data=sample(size)[0];identity=ProjectedIdentity(data)
    for a in data.assortment:
        history=[r for r in data.demand_history if (r.sku,r.location_id)==(a.sku,a.location_id)]
        settings=data.settings.model_copy(update={'protection_days':17})
        projected=data.model_copy(update={'demand_history':history,'settings':settings})
        assert identity.hash(history,settings)==sha256(projected.model_dump_json().encode()).hexdigest()
    changed=data.model_copy(deep=True)
    changed.products[0].name='Different dataset · منتج'
    changed.inventory[0].book_unit_cost+=.01
    assert ProjectedIdentity(changed).hash(changed.demand_history,changed.settings)==sha256(changed.model_dump_json().encode()).hexdigest()
    assert ProjectedIdentity(changed).hash(changed.demand_history,changed.settings)!=identity.hash(data.demand_history,data.settings)
    # No cache can contaminate a subsequent request using the original dataset.
    assert ProjectedIdentity(data).hash(data.demand_history,data.settings)==sha256(data.model_dump_json().encode()).hexdigest()


def test_optimized_full_cold_and_repeat_results_and_scenario_baseline_are_identical():
    """Covers stages, actions/terms, funding, service, explanations and replay."""
    from backend.app.planning import preparation
    from backend.app.scenarios.contracts import CaptureRequest
    from backend.app.scenarios.engine import capture
    data,issues=sample('full');preparation.clear()
    first=plan(data,validated_issues=issues)
    repeat=plan(data,validated_issues=issues)
    assert authoritative(first)==authoritative(repeat)
    assert first.status=='feasible_fallback'
    assert [stage.model_dump() for stage in first.stages]==[
        {'name':'joint_model','status':'not_attempted','elapsed_ms':0.0,'objective':None,'gap':None},
        {'name':'independent_fallback','status':'benchmark','elapsed_ms':0.0,'objective':None,'gap':None},
    ]
    baseline=capture(data,CaptureRequest(size='full',dataset_hash=first.input_hash,
        purchases=first.proposed.purchases,movements=first.proposed.movements))
    assert baseline.original.purchases==first.proposed.purchases
    assert baseline.original.movements==first.proposed.movements
    assert baseline.original.summary==first.proposed.replay.summary
    assert baseline.original.cash==first.proposed.replay.cash
    assert baseline.original.feasible and not baseline.original.failures
