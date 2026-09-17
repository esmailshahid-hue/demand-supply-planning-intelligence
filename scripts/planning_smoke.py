"""Actual production API, full dimensions, independent server replay and money agreement."""
import argparse
import json
from decimal import Decimal
from time import perf_counter
from urllib.request import Request, urlopen

parser=argparse.ArgumentParser()
parser.add_argument('--url',default='http://127.0.0.1:8000')
args=parser.parse_args()
for size,count in [('fixture',40),('full',240)]:
    for run in ['first','repeat']:
        start=perf_counter()
        req=Request(args.url+'/api/plan/sample',data=json.dumps({'size':size}).encode(),headers={'Content-Type':'application/json'})
        with urlopen(req,timeout=60) as response:
            assert response.status==200
            raw=response.read()
        elapsed=perf_counter()-start
        result=json.loads(raw); p=result['proposed']; r=p['replay']; s=r['summary']
        assert result['status'] in ('feasible','feasible_fallback'),result['failures']
        assert r['feasible'] and not r['failures']
        assert len(result['forecasts'])==count
        assert len(r['stock'])==56*(count+count//4)
        assert 'demand_history' not in result and len(raw)<4_500_000
        assert sum(Decimal(str(x['value'])) for x in p['purchases'])==Decimal(str(s['commitments']))
        assert sum(Decimal(str(x['amount'])) for x in r['payments'])==Decimal(str(s['payments']))
        assert all(min(w['payment_headroom'],w['commitment_headroom'],w['transfer_headroom'])>=0 for w in r['cash'])
        assert elapsed<60,'Exceeded configured 60-second Function ceiling'
        print(f'{size} {run}: HTTP {elapsed:.3f}s; engine {result["elapsed_ms"]:.1f}ms; {len(raw):,} bytes; {result["status"]}; {len(p["purchases"])} purchases; {len(p["movements"])} movements',flush=True)
print('Planning HTTP smoke passed; first/repeat are per dataset in this process, not proof of Vercel cold starts.')
