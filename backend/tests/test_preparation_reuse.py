"""Cache misses/hits preserve calculations; only exact bundled inputs qualify."""
from copy import deepcopy
from time import perf_counter
import pytest
from backend.app.main import sample
from backend.app.planning import inputs, preparation


def test_concurrent_initial_requests_share_the_registered_sample(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from backend.app import main
    main._sample.cache_clear()
    original=main.generate_sample;calls=[];barrier=Barrier(2)
    def generate(size):calls.append(size);return original(size)
    monkeypatch.setattr(main,'generate_sample',generate)
    def load():barrier.wait();return main.sample('fixture')[0]
    with ThreadPoolExecutor(2) as pool:
        a=pool.submit(load);b=pool.submit(load);first,second=a.result(),b.result()
    assert first is second is main.sample('fixture')[0]
    assert calls==['fixture'] and preparation._samples['fixture'][0] is first


def stable(result):
    demand, buffers, traces, failures = result
    return demand, buffers, [t.model_dump(exclude={'run_id'}) for t in traces], failures


@pytest.mark.parametrize('size', ['fixture', 'full'])
def test_preparation_hits_are_equivalent_isolated_and_versioned(size, monkeypatch):
    data = sample(size)[0]
    preparation.clear()
    original = inputs._network_forecasts
    calls = []
    def calculate(data, deadline):
        calls.append(data)
        return original(data, deadline)
    monkeypatch.setattr(inputs, '_network_forecasts', calculate)
    def run(data=data):return inputs.network_forecasts(data, perf_counter()+30)
    first = run(); second = run()
    assert len(calls) == 1 and stable(first) == stable(second)
    assert first[2][0].run_id != second[2][0].run_id
    expected = deepcopy(stable(first))
    first[0]['SKU001', 'S1'][0] += 100
    second[2][0].buffer.units += 100
    assert stable(run()) == expected
    # Equal content reconstructed for an uploaded/reviewed dataset is not an
    # eligible registered sample object, even if its ID/synthetic flag matches.
    custom = data.model_copy(deep=True)
    assert stable(run(custom)) == expected
    assert stable(run(custom)) == expected and len(calls) == 3
    # Every identity component invalidates reuse, not only dataset_id.
    for name in ('ENGINE_VERSION', 'SCHEMA_VERSION', 'FORECAST_VERSION', 'PREPARATION_VERSION'):
        with monkeypatch.context() as changed:
            changed.setattr(preparation, name, getattr(preparation, name)+'-changed')
            before = len(calls)
            assert stable(run()) == expected and len(calls) == before+1
    before = len(calls)
    cost = data.inventory[0].book_unit_cost
    try:
        data.inventory[0].book_unit_cost += .01
        run(); run()
        assert len(calls) == before+2  # mutated shared object cannot hit or publish
    finally:
        data.inventory[0].book_unit_cost = cost
        preparation.clear()
    with pytest.raises(TimeoutError):inputs.network_forecasts(data, perf_counter()-1)


def test_scoped_evidence_checks_identities_even_when_preparation_is_reused():
    from backend.app.scenarios.engine import capture, detail, digest
    from backend.app.scenarios.contracts import CaptureRequest, DetailRequest
    from backend.app.planning.engine import plan
    data = sample('fixture')[0]; preparation.clear()
    result = plan(data)
    baseline = capture(data, CaptureRequest(size='fixture',dataset_hash=result.input_hash,
        purchases=result.proposed.purchases,movements=result.proposed.movements))
    request = DetailRequest(baseline=baseline.baseline,policy='original',sku='SKU001',location_id='S1',
                            expected_action_hash=baseline.original.action_hash)
    hit = detail(data, request)
    preparation.clear(); miss = detail(data, request)
    fields = ('stock','cash','payments','baseline_id','scenario_hash','action_hash','forecast_version','provenance')
    assert all(getattr(hit,k)==getattr(miss,k) for k in fields)
    assert hit.stock == [r for r in result.proposed.replay.stock if r.sku=='SKU001']
    assert hit.cash == result.proposed.replay.cash
    for key in ('expected_action_hash','expected_scenario_hash'):
        with pytest.raises(ValueError):detail(data,request.model_copy(update={key:'wrong'}))
    changed = request.baseline.model_copy(update={'dataset_hash':'wrong'})
    with pytest.raises(ValueError):detail(data,request.model_copy(update={'baseline':changed}))
