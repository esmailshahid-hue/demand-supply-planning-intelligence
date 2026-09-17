"""Opt-in component timings using the production sample route; no plan caching.

Run inside the production image:
  docker run --rm planning-pass1 python -m scripts.planning_profile
Timings are wall clock, not cProfile-inflated. HTTP smoke remains the latency gate.
"""
import json
import platform
from collections import defaultdict
from contextlib import ExitStack
from functools import wraps
from time import perf_counter
from unittest.mock import patch

from pydantic import TypeAdapter
from backend.app import main as api
from backend.app.planning import engine
from backend.app.planning.contracts import PlanResult, PlanSampleRequest
from scripts.planning_smoke import stable_plan, validate_plan


def main():
    started=perf_counter()
    from backend.app.planning import optimizer
    print(json.dumps({'platform':platform.platform(),'python':platform.python_version(),
        'optimizer_cold_import_s':perf_counter()-started}),flush=True)
    adapter=TypeAdapter(PlanResult)
    totals=defaultdict(float);counts=defaultdict(int)
    def timed(name,fn):
        @wraps(fn)
        def call(*args,**kwargs):
            start=perf_counter()
            try:return fn(*args,**kwargs)
            finally:
                totals[name]+=perf_counter()-start;counts[name]+=1
        return call
    with ExitStack() as stack:
        for module,attr,name in [(engine,'network_forecasts','forecast'),(engine,'benchmark','benchmark'),
                (engine,'replay','replay'),(engine,'_explanations','explanations'),
                (optimizer,'optimize','joint_total'),(optimizer.Model,'solve','matrix_and_solve'),
                (optimizer,'milp','scipy_solve'),(api,'sample','sample_input')]:
            stack.enter_context(patch.object(module,attr,timed(name,getattr(module,attr))))
        previous={}
        for size in ('fixture','full'):
            for run in ('first','repeat'):
                totals.clear();counts.clear();start=perf_counter()
                result=api.sample_plan(PlanSampleRequest(size=size))
                route_seconds=perf_counter()-start
                start=perf_counter();raw=adapter.dump_json(result);serialization=perf_counter()-start
                value=json.loads(raw);signature=stable_plan(value)
                comparison='reference' if run=='first' else ('matched' if signature==previous[size] else 'MISMATCH')
                previous[size]=signature
                phases=dict(totals)
                phases['joint_construction']=totals['joint_total']-totals['matrix_and_solve']
                phases['matrix_preparation']=totals['matrix_and_solve']-totals['scipy_solve']
                phases['other_validation_context_selection']=route_seconds-sum(totals[k] for k in ('sample_input','forecast','benchmark','replay','explanations','joint_total'))
                print(json.dumps({'size':size,'run':run,'route_s':route_seconds,'serialization_s':serialization,
                    'phases_s':phases,'replay_calls':counts['replay'],'bytes':len(raw),'status':result.status,
                    'stages':[s.model_dump() for s in result.stages],'determinism':comparison}),flush=True)
                validate_plan(value)
                assert comparison!='MISMATCH'


if __name__=='__main__':
    main()
