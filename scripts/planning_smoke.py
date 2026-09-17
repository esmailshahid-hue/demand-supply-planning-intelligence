"""Actual production API, full dimensions, independent server replay and money agreement."""
import argparse
import json
from decimal import Decimal
from time import perf_counter
from urllib.request import Request, urlopen

parser=argparse.ArgumentParser()
parser.add_argument('--url',default='http://127.0.0.1:8000')
args=parser.parse_args()
gate_failures=[]
for size,count in [('fixture',40),('full',240)]:
    for run in ['first','repeat']:
        start=perf_counter()
        req=Request(args.url+'/api/plan/sample',data=json.dumps({'size':size}).encode(),headers={'Content-Type':'application/json'})
        with urlopen(req,timeout=60) as response:
            assert response.status==200
            raw=response.read()
        elapsed=perf_counter()-start
        result=json.loads(raw); p=result['proposed']; r=p['replay']; s=r['summary']
        assert r['feasible'] and not r['failures']
        assert len(result['forecasts'])==count
        assert len(r['stock'])==56*(count+count//4)
        assert 'demand_history' not in result and len(raw)<4_500_000
        assert sum(Decimal(str(x['value'])) for x in p['purchases'])==Decimal(str(s['commitments']))
        assert sum(Decimal(str(x['amount'])) for x in r['payments'])==Decimal(str(s['payments']))
        assert all(min(w['payment_headroom'],w['commitment_headroom'],w['transfer_headroom'])>=0 for w in r['cash'])
        assert elapsed<60,'Exceeded configured 60-second Function ceiling'
        stages=','.join(f'{x["name"]}:{x["status"]}' for x in result['stages'])
        min_commit=min(w['commitment_headroom'] for w in r['cash'] if w['commitment_headroom'] is not None)
        min_payment=min(w['payment_headroom'] for w in r['cash'] if w['payment_headroom'] is not None)
        min_transfer=min(w['transfer_headroom'] for w in r['cash'] if w['transfer_headroom'] is not None)
        print(f'{size} {run}: HTTP {elapsed:.3f}s; engine {result["elapsed_ms"]:.1f}ms; {len(raw):,} bytes; '
              f'{len(result["forecasts"])} series; {len(r["stock"]):,} stock rows; {result["status"]}; stages [{stages}]; '
              f'{len(p["purchases"])} purchases; {len(p["movements"])} movements; replay {r["feasible"]}; '
              f'commitments SAR {s["commitments"]:.2f} = lines SAR {sum(Decimal(str(x["value"])) for x in p["purchases"]):.2f}; '
              f'payments SAR {s["payments"]:.2f} = ledger SAR {sum(Decimal(str(x["amount"])) for x in r["payments"]):.2f}; '
              f'min headroom commitment/payment/transfer SAR {min_commit:.2f}/{min_payment:.2f}/{min_transfer:.2f}',flush=True)
        expected=('feasible',) if size=='fixture' else ('feasible','feasible_fallback')
        if result['status'] not in expected:
            gate_failures.append((size,run,result['status'],result['stages'],result['failures']))
assert not gate_failures,gate_failures
print('Planning HTTP smoke passed; first/repeat are per dataset in this process, not proof of Vercel cold starts.')
