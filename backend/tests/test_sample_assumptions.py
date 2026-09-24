"""Versioned sample-funding calibration without changing operational inputs."""
import hashlib
import json
from time import perf_counter

import pytest
from pydantic import ValidationError

from backend.app.data.sample import generate_bundle
from backend.app.planning.engine import plan
from backend.app.planning.inputs import network_forecasts
from backend.app.scenarios.contracts import Actions, BaselineSnapshot
from backend.app.scenarios.engine import check_snapshot, snapshot


NON_FINANCIAL_HASHES = {
    'fixture': '4da4244905df654dc90da52de976f566f6bffffed55d6c8b826b12f31c66cc10',
    'full': '8d111f14946e4c1c80dad1a561e353141b1a66c169eebc9d73c316fcd9a0833c',
}
TRUTH_HASHES = {
    'fixture': '97b6fd0ac958e8a588983a044776a2cca8fcad6394cd7442055009e72c49e03c',
    'full': 'bef84137065ddbb1a935b10bbafd9c917537be286428eb11c64507c264779fa2',
}


def stable_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


@pytest.mark.parametrize('size', ['fixture','full'])
def test_sample_version_funding_and_nonfinancial_inputs(size):
    bundle=generate_bundle(size);data=bundle.inputs
    expected=(1500,15000,4000,18000,800) if size=='fixture' else (9000,30000,12000,30000,1200)
    c0,c1,p0,p1,transfer=expected
    assert data.dataset_id==f'sample-v2-{size}-97'
    assert [(b.new_commitment_cap,b.payment_ceiling,b.transfer_budget) for b in data.budgets]==[
        (c0 if i<2 else c1,p0 if i<2 else p1,transfer) for i in range(14)]
    nonfinancial=data.model_dump(mode='json');nonfinancial.pop('dataset_id');nonfinancial.pop('budgets')
    assert stable_hash(nonfinancial)==NON_FINANCIAL_HASHES[size]
    assert stable_hash(bundle.truth)==TRUTH_HASHES[size]


@pytest.mark.parametrize('size', ['fixture','full'])
def test_sample_plans_replay_with_financial_pressure_and_shortages(size):
    data=generate_bundle(size).inputs
    prepared=network_forecasts(data,perf_counter()+30)
    result=plan(data,prepared_forecasts=prepared)
    assert result.proposed and result.proposed.replay.feasible
    assert result.proposed.purchases==result.benchmark.purchases
    assert result.proposed.movements==result.benchmark.movements
    assert result.proposed.replay.summary.unmet>0 and result.proposed.replay.summary.tail_unmet>0
    assert any((w.commitment_headroom is not None and w.commitment_headroom<200) for w in result.proposed.replay.cash)
    assert any((w.payment_headroom is not None and w.payment_headroom<200) for w in result.proposed.replay.cash)


def test_previous_sample_snapshot_is_rejected_as_stale():
    current=generate_bundle('full').inputs
    previous=current.model_copy(update={'dataset_id':'sample-v1-full-97'})
    stale=snapshot('full',previous,Actions())
    with pytest.raises(ValueError,match='sample version'):
        check_snapshot(current,stale)
    stale_version=stale.model_dump(mode='json');stale_version['version']='sample-scenarios-1'
    with pytest.raises(ValidationError):
        BaselineSnapshot.model_validate(stale_version)
