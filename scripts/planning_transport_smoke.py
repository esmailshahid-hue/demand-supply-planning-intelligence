"""Additional compact-response gate; the original complete-ledger gate stays intact."""
import argparse
import json
from time import perf_counter
from urllib.request import Request, urlopen
from scripts.planning_smoke import stable_plan, validate_plan


def run(url):
    failures=[]
    def call(path,body,limit=10):
        start=perf_counter()
        with urlopen(Request(url+path,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'}),timeout=60) as response:
            ready=perf_counter();raw=response.read();status=response.status;timings=response.headers.get('Server-Timing','unavailable')
        finished=perf_counter();elapsed=finished-start;value=json.loads(raw)
        print(json.dumps({'path':path,'size':body.get('size'),'http_s':elapsed,'first_byte_s':ready-start,
            'body_read_s':finished-ready,'bytes':len(raw),'status':status,'engine_ms':value.get('elapsed_ms'),
            'phases':timings}),flush=True)
        assert status==200 and len(raw)<4_500_000
        if elapsed>=limit:failures.append(f'{path}: {elapsed:.3f}s exceeded {limit}s')
        return value
    for size,count in [('fixture',40),('full',240)]:
        full=call('/api/plan/sample?include_stock=true',{'size':size},10)
        validate_plan(full)
        authoritative=full['proposed']['replay']['stock'];assert len(authoritative)==56*(count+count//4)
        expected=stable_plan(full)
        for name in ('proposed','benchmark','no_action'):expected[name]['replay']['stock']=[]
        previous=None;previous_detail=None
        for label in ('first','repeat'):
            value=call('/api/plan/sample',{'size':size},10);validate_plan(value)
            assert value['stock_detail']=='on_demand' and value['stock_row_count']==len(authoritative)
            assert stable_plan(value)==expected
            assert previous is None or stable_plan(value)==previous
            previous=stable_plan(value);p=value['proposed']
            base=call('/api/scenarios/capture',{'size':size,'dataset_hash':value['input_hash'],
                'purchases':p['purchases'],'movements':p['movements']})
            detail=call('/api/scenarios/detail',{'baseline':base['baseline'],'policy':'original',
                'sku':'SKU001','location_id':'S1','expected_action_hash':base['original']['action_hash']})
            assert detail['stock']==[r for r in authoritative if r['sku']=='SKU001']
            assert detail['cash']==p['replay']['cash'] and detail['provenance']==value['provenance']
            signature={k:detail[k] for k in ('stock','cash','payments','purchases','movements','baseline_id','scenario_hash','action_hash','forecast_version')}
            assert previous_detail is None or signature==previous_detail
            previous_detail=signature
            print(f'{size} {label}: compact/full actions, totals, explanations and scoped replay match; requested detail deterministic',flush=True)
    assert not failures,failures
    print('Compact planning transport smoke passed; complete-ledger gate remains separate.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:8000')
    run(parser.parse_args().url)
