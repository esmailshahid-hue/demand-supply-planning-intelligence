"""Bounded timing headers with opt-in logs; never include input values or IDs."""
from collections import defaultdict
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from time import perf_counter
import os
import json
import logging

_PHASES = frozenset(('sample_construction', 'dataset_validation', 'sample_input',
    'protection_paths', 'buffers', 'forecast_contract', 'series_forecast',
    'network_forecast', 'independent_replay', 'benchmark', 'explanations', 'route',
    'dataset_context', 'review_attachment', 'planning', 'request_body',
    'response_validation', 'response_serialization', 'forecast_identity',
    'forecast_reuse', 'application_import', 'fastapi_setup', 'workflow_import',
    'fastapi_startup', 'response_ready', 'module_bootstrap',
    'fastapi_construction', 'scenario_import', 'request_validation',
    'input_normalization', 'response_construction'))
_startup = {}
logger = logging.getLogger(__name__)


def startup_measurement(name, seconds):
    if name in _PHASES:
        _startup[name] = seconds
        if os.getenv('PLANNING_DIAGNOSTICS') == '1':
            logger.warning('planning_startup %s', json.dumps({name: round(seconds*1000, 3)}))


def instrument_response_fields(app):
    """Low-overhead wrappers around installed FastAPI response fields.

    Retain the actual response validation and Pydantic serialization. No copied
    framework pipeline or global class patch; contracts and errors stay intact.
    """
    for route in app.routes:
        field = getattr(route, 'response_field', None)
        if field is None or getattr(field, '_planning_timed', False):
            continue
        for method, phase in (('validate', 'response_validation'),
                              ('serialize', 'response_serialization'),
                              ('serialize_json', 'response_serialization')):
            if hasattr(field, method):
                setattr(field, method, timed(phase)(getattr(field, method)))
        field._planning_timed = True

_active = ContextVar('planning_timings', default=None)

@contextmanager
def collect():
    totals=defaultdict(float);token=_active.set(totals)
    try:yield totals
    finally:_active.reset(token)

@contextmanager
def measure(name):
    totals=_active.get()
    if totals is None or name not in _PHASES:
        yield;return
    start=perf_counter()
    if name == 'route' and '_asgi_started' in totals:
        totals['request_validation'] += start - totals['_asgi_started']
    try:yield
    finally:totals[name]+=perf_counter()-start

def timed(name):
    def decorate(fn):
        @wraps(fn)
        def call(*args,**kwargs):
            with measure(name):return fn(*args,**kwargs)
        return call
    return decorate

class TimingHeaders:
    def __init__(self,app):self.app=app
    async def __call__(self,scope,receive,send):
        if scope['type']=='lifespan':
            started=None
            async def lifecycle_receive():
                nonlocal started
                message=await receive()
                if message['type']=='lifespan.startup':started=perf_counter()
                return message
            async def lifecycle_send(message):
                if message['type']=='lifespan.startup.complete' and started is not None:
                    startup_measurement('fastapi_startup',perf_counter()-started)
                await send(message)
            return await self.app(scope,lifecycle_receive,lifecycle_send)
        if scope['type']!='http':
            return await self.app(scope,receive,send)
        with collect() as totals:
            start=perf_counter()
            totals['_asgi_started']=start
            async def measured_send(message):
                if message['type']=='http.response.start':
                    # Inclusive nested phases are labeled separately; do not sum
                    # forecast + its buffer/contract sub-phases as independent work.
                    totals['response_ready']=perf_counter()-start
                    header=', '.join(f'{key};dur={value*1000:.3f}' for key,value in sorted({**_startup,**totals}.items()) if key in _PHASES)
                    message={**message,'headers':[*message.get('headers',[]),(b'server-timing',header.encode())]}
                await send(message)
            await self.app(scope,receive,measured_send)
            if os.getenv('PLANNING_DIAGNOSTICS') == '1':
                logger.warning('planning_request_complete %s', json.dumps({
                    'asgi_ms':round((perf_counter()-start)*1000,3),
                    'phases_ms':{k:round(v*1000,3) for k,v in totals.items() if k in _PHASES}},sort_keys=True))
