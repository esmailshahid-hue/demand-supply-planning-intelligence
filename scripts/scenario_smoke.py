"""Production stateless baseline/combined-shock/detail checks, full dimensions."""
import argparse
import json
from datetime import date,timedelta
from decimal import Decimal
from time import perf_counter
from urllib.request import Request,urlopen


def call(url,path,body):
    start=perf_counter();payload=json.dumps(body).encode();assert len(payload)<4_500_000
    with urlopen(Request(url+path,data=payload,headers={'Content-Type':'application/json'}),timeout=60) as r:
        raw=r.read();assert r.status==200
    elapsed=perf_counter()-start;value=json.loads(raw)
    print(f'{path}: HTTP {elapsed:.3f}s; engine {value["elapsed_ms"]:.1f}ms; request {len(payload):,} bytes; response {len(raw):,} bytes',flush=True)
    assert len(raw)<4_500_000 and elapsed<30
    return value


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:8000');args=parser.parse_args()
    for size,count in [('fixture',40),('full',240)]:
        print(size,flush=True)
        baseline=call(args.url,'/api/scenarios/baseline',{'size':size});saved=json.dumps(baseline,sort_keys=True)
        start=baseline['as_of'];end=str(date.fromisoformat(start)+timedelta(days=55))
        definition={'uplifts':[{'scope':'sku','scope_id':'SKU001','start':start,'end':str(date.fromisoformat(start)+timedelta(days=13)),'percent':30}],
            'availability':[{'supplier_id':'SUP01','start':start,'end':end,'remaining_fraction':0}],
            'funding':[{'week_start':start,'commitment':0}]}
        if baseline['existing_orders']:
            o=baseline['existing_orders'][0];definition['delays']=[{'supplier_id':o['supplier'],'days':3,'existing_order_ids':[o['id']],'future_paths':False}]
        previous=None
        for run in ('first','repeat'):
            result=call(args.url,'/api/scenarios/compare',{'baseline':baseline['baseline'],'scenario':definition})
            assert result['frozen']['assumptions_hash']==result['replanned']['assumptions_hash']==result['scenario_hash']
            assert result['original']['summary']==baseline['original']['summary']
            assert len(result['forecast_versions'])==count
            p=result['replanned'];assert p['feasible'] and not p['failures']
            assert sum(Decimal(str(x['value'])) for x in p['purchases'])==Decimal(str(p['summary']['commitments']))
            assert sum(Decimal(str(x['total_payments'])) for x in p['cash'])==Decimal(str(p['summary']['payments']))
            assert all(min(w[k] for k in ('payment_headroom','commitment_headroom','transfer_headroom'))>=0 for w in p['cash'])
            if not result['frozen']['feasible']:
                assert result['frozen']['summary'] is None and all(v is None for v in result['replan_delta'].values())
            signature={k:p[k] for k in ('purchases','movements','summary','cash','shortages','explanations')}
            if previous is not None:assert signature==previous
            previous=signature
            print(f'{size} {run}: frozen feasible {result["frozen"]["feasible"]}; frozen failures {len(result["frozen"]["failures"])}; replanned {p["status"]}; purchases/movements {len(p["purchases"])}/{len(p["movements"])}; commitments/payments {p["summary"]["commitments"]}/{p["summary"]["payments"]}; determinism {"matched" if run=="repeat" else "reference"}',flush=True)
        detail=call(args.url,'/api/scenarios/detail',{'baseline':baseline['baseline'],'scenario':definition,'policy':'replanned','actions':{'purchases':p['purchases'],'movements':p['movements']},'expected_action_hash':p['action_hash'],'expected_scenario_hash':result['scenario_hash'],'sku':'SKU001','location_id':'S1'})
        assert detail['feasible'] and len(detail['stock'])==280 and detail['cash']==p['cash']
        assert detail['forecast_version']==result['forecast_versions']['SKU001/S1']
        future=call(args.url,'/api/scenarios/compare',{'baseline':baseline['baseline'],'scenario':{'delays':[{'supplier_id':'SUP01','days':1,'future_paths':True}]}})
        assert future['replanned']['feasible']
        assert future['frozen']['assumptions_hash']==future['replanned']['assumptions_hash']
        old={a['action_id']:a for a in future['original']['purchases']}
        for action in future['frozen']['purchases']:
            assert action['units']==old[action['action_id']]['units']
            if action['supplier_id']=='SUP01':assert action['arrival_date']>old[action['action_id']]['arrival_date']
        print(f'{size} future-path delay: frozen feasible {future["frozen"]["feasible"]}; replanned {future["replanned"]["status"]}',flush=True)
        assert json.dumps(baseline,sort_keys=True)==saved
    print('Scenario smoke passed: independent feasibility, financial reconciliation, repeat determinism and scoped evidence.')


if __name__=='__main__':main()
