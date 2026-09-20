"""Opt-in bounded timings. No input values, IDs, secrets or dynamic metric names."""
from collections import defaultdict
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from time import perf_counter
import os

_active = ContextVar('planning_timings', default=None)

@contextmanager
def collect():
    totals=defaultdict(float);token=_active.set(totals)
    try:yield totals
    finally:_active.reset(token)

@contextmanager
def measure(name):
    totals=_active.get()
    if totals is None:
        yield;return
    start=perf_counter()
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
        if scope['type']!='http' or os.getenv('PLANNING_DIAGNOSTICS')!='1':
            return await self.app(scope,receive,send)
        with collect() as totals:
            start=perf_counter()
            async def measured_send(message):
                if message['type']=='http.response.start':
                    # Inclusive nested phases are labeled separately; do not sum
                    # forecast + its buffer/contract sub-phases as independent work.
                    totals['response_ready']=perf_counter()-start
                    header=', '.join(f'{key};dur={value*1000:.3f}' for key,value in sorted(totals.items()))
                    message={**message,'headers':[*message.get('headers',[]),(b'server-timing',header.encode())]}
                await send(message)
            await self.app(scope,receive,measured_send)
