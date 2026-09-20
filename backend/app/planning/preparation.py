"""Bounded, process-local reuse of deterministic bundled forecast inputs only.

No recommendations, replay ledgers, uploaded datasets or review state are cached.
Only exact server-registered sample objects qualify, and their complete current
hash must still match registration. Misses use the unchanged forecasting path.
"""
from copy import deepcopy
from hashlib import sha256
from threading import RLock
from time import perf_counter
from uuid import uuid4

from backend.app.contracts import ENGINE_VERSION, SCHEMA_VERSION
from backend.app.diagnostics import measure

FORECAST_VERSION = 'weekday-evaluation-1'
PREPARATION_VERSION = 'calendar-protection-56-28-7-v1'
_samples = {}
_values = {}
_lock = RLock()


def register(size, data):
    if size not in ('fixture', 'full'):
        raise ValueError('Only bundled sample sizes can be registered')
    with _lock:
        old = _samples.get(size)
        if old is not None:
            _values.pop(id(old[0]), None)
        _samples[size] = (data, sha256(data.model_dump_json().encode()).hexdigest())


def clear():
    """Drop derived preparation only; used for miss/equivalence measurements."""
    with _lock:
        _values.clear()


def prepare(data, deadline, calculate):
    if perf_counter() >= deadline:
        raise TimeoutError('Network forecast budget exhausted')
    with _lock:
        registered = next((row for row in _samples.values() if row[0] is data), None)
    if registered is None:
        return calculate(data, deadline)
    with measure('forecast_identity'):
        current = sha256(data.model_dump_json().encode()).hexdigest()
    if current != registered[1]:
        return calculate(data, deadline)
    key = (current, ENGINE_VERSION, SCHEMA_VERSION, FORECAST_VERSION, PREPARATION_VERSION)
    with _lock:
        entry = _values.get(id(data))
    if entry is not None and entry[0] == key:
        with measure('forecast_reuse'):
            result = deepcopy(entry[1])
            # Calculation IDs remain fresh; only deterministic forecast inputs
            # are reused. Scenario forecast identities exclude incidental UUIDs.
            for trace in result[2]:
                trace.run_id = str(uuid4())
        if perf_counter() >= deadline:
            raise TimeoutError('Network forecast budget exhausted')
        return result
    result = calculate(data, deadline)
    if not result[3]:
        with _lock:
            # Registration is bounded to fixture/full; never retain custom data.
            if any(row[0] is data for row in _samples.values()):
                _values[id(data)] = (key, deepcopy(result))
    return result
