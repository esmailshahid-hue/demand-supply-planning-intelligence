"""Actual production API, full dimensions, independent server replay and money agreement."""
import argparse
import json
from decimal import Decimal
from time import perf_counter
from urllib.request import Request, urlopen

def service_score(policy):
    groups=policy['replay']['service_groups']
    return tuple(round(sum(g['target_shortfall'] for g in groups
        if g['window']==window and (g['must_stock'] if priority=='must_stock'
        else not g['must_stock'] and g['service_class']==priority)),5)
        for window in ('visible','tail') for priority in ('must_stock','A','B','C'))


def stable_plan(result):
    return {key:result[key] for key in ('status','proposed','benchmark','no_action','exceptions')}


def validate_plan(result):
    proposed=result['proposed']; ledger=proposed['replay']
    assert ledger['feasible'] and not ledger['failures'] and not result['failures']
    assert proposed['purchases'] and proposed['movements'], 'Sample requires calculated actions'
    assert all(a['units']>0 for a in proposed['purchases']+proposed['movements'])
    stages=result['stages'];joint=[s for s in stages if s['name']!='independent_fallback']
    # Sample includes all four priority groups in each window.
    expected=[f'{window}_{priority}' for window in ('visible','tail')
        for priority in ('must_stock','A','B','C')]
    expected+=['weekly_buffer_deficit','commitment_movement_holding','stable_action_ties']
    completed=([s['name'] for s in joint]==expected
        and all(s['status']=='optimal' and (s['gap'] is None or s['gap']==0) for s in joint))
    if result['status']=='feasible':
        assert completed and len(stages)==len(joint), 'Unfinished joint plan labeled feasible'
    else:
        assert result['status']=='feasible_fallback'
        assert not completed
        assert any(s['status']!='optimal' for s in joint), 'Missing incomplete stage'
        assert stages[-1]['name']=='independent_fallback' and stages[-1]['status']=='benchmark'
        benchmark=result['benchmark']
        assert benchmark['replay']['feasible'] and not benchmark['replay']['failures']
        assert proposed['purchases']==benchmark['purchases']
        assert proposed['movements']==benchmark['movements']
        assert ledger['summary']==benchmark['replay']['summary']
        assert service_score(proposed)<=service_score(result['no_action'])
    assert sum(Decimal(str(a['value'])) for a in proposed['purchases'])==Decimal(str(ledger['summary']['commitments']))
    assert sum(Decimal(str(a['amount'])) for a in ledger['payments'])==Decimal(str(ledger['summary']['payments']))
    assert all(min(w[k] for k in ('payment_headroom','commitment_headroom','transfer_headroom'))>=0 for w in ledger['cash'])


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',default='http://127.0.0.1:8000')
    args=parser.parse_args()
    previous={}
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
            validate_plan(result)
            assert elapsed<10,'Exceeded documented 10-second live sample target'
            signature=stable_plan(result)
            if size in previous:assert signature==previous[size], 'Repeated actions/totals/explanations changed'
            previous[size]=signature
            stages=','.join(f'{x["name"]}:{x["status"]}' for x in result['stages'])
            min_commit=min(w['commitment_headroom'] for w in r['cash'] if w['commitment_headroom'] is not None)
            min_payment=min(w['payment_headroom'] for w in r['cash'] if w['payment_headroom'] is not None)
            min_transfer=min(w['transfer_headroom'] for w in r['cash'] if w['transfer_headroom'] is not None)
            print(f'{size} {run}: HTTP {elapsed:.3f}s; engine {result["elapsed_ms"]:.1f}ms; {len(raw):,} bytes; '
                  f'{len(result["forecasts"])} series; {len(r["stock"]):,} stock rows; {result["status"]}; stages [{stages}]; '
                  f'{len(p["purchases"])} purchases; {len(p["movements"])} movements; replay {r["feasible"]}; '
                  f'commitments SAR {s["commitments"]:.2f} = lines SAR {sum(Decimal(str(x["value"])) for x in p["purchases"]):.2f}; '
                  f'payments SAR {s["payments"]:.2f} = ledger SAR {sum(Decimal(str(x["amount"])) for x in r["payments"]):.2f}; '
                  f'determinism {"matched" if run=="repeat" else "reference"}; min headroom commitment/payment/transfer SAR {min_commit:.2f}/{min_payment:.2f}/{min_transfer:.2f}',flush=True)
    print('Planning HTTP smoke passed; first/repeat are per dataset in this process, not proof of Vercel cold starts.')

if __name__=='__main__':
    main()
