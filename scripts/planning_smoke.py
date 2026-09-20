"""Actual production API, full dimensions, independent server replay and money agreement."""
import argparse
import json
import traceback
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


def run_smoke(url):
    """Report before checking gates; a bad request must not conceal later evidence."""
    previous={}; failures=[]
    for size,count in [('fixture',40),('full',240)]:
        for run in ['first','repeat']:
            label=f'{size} {run}'
            start=perf_counter()
            try:
                req=Request(url+'/api/plan/sample?include_stock=true',data=json.dumps({'size':size}).encode(),headers={'Content-Type':'application/json'})
                with urlopen(req,timeout=60) as response:
                    status=response.status; raw=response.read()
                elapsed=perf_counter()-start
                result=json.loads(raw); p=result['proposed']; r=p['replay']; s=r['summary']
                signature=stable_plan(result)
                comparison=('matched' if signature==previous[size] else 'MISMATCH') if size in previous else 'reference'
                if run=='repeat' and size not in previous: comparison='unavailable: first response failed'
                if run=='first': previous[size]=signature
                stages=','.join(f'{x["name"]}:{x["status"]}' for x in result['stages'])
                lines=sum(Decimal(str(x['value'])) for x in p['purchases'])
                payments=sum(Decimal(str(x['amount'])) for x in r['payments'])
                headrooms=[min(w[key] for w in r['cash']) for key in ('commitment_headroom','payment_headroom','transfer_headroom')]
                print(f'{label}: HTTP {elapsed:.3f}s (status {status}); engine {result["elapsed_ms"]:.1f}ms; {len(raw):,} bytes; '
                      f'{len(result["forecasts"])} series; {len(r["stock"]):,} stock rows; {result["status"]}; challenger budget {result["challenger_budget_seconds"]:.3f}s; stages [{stages}]; '
                      f'{len(p["purchases"])} purchases; {len(p["movements"])} movements; replay {r["feasible"]}; failures {r["failures"]}; '
                      f'commitments SAR {s["commitments"]:.2f} / lines SAR {lines:.2f} (match {lines==Decimal(str(s["commitments"]))}); '
                      f'payments SAR {s["payments"]:.2f} / ledger SAR {payments:.2f} (match {payments==Decimal(str(s["payments"]))}); '
                      f'determinism {comparison}; min headroom commitment/payment/transfer SAR {headrooms[0]:.2f}/{headrooms[1]:.2f}/{headrooms[2]:.2f}',flush=True)
                # Each gate runs after diagnostics; collect independent failures too.
                checks=[
                    ('HTTP status',status==200),
                    ('forecast dimensions',len(result['forecasts'])==count),
                    ('stock dimensions',len(r['stock'])==56*(count+count//4)),
                    ('response size/history', 'demand_history' not in result and len(raw)<4_500_000),
                    ('Exceeded documented 10-second live sample target',elapsed<10),
                    ('Repeated actions/totals/explanations changed or unavailable',run=='first' or comparison=='matched'),
                ]
                failures.extend(f'{label}: {name}' for name,passed in checks if not passed)
                try:
                    validate_plan(result)
                except AssertionError as error:
                    failures.append(f'{label}: validated-plan acceptance: {error or "assertion failed (see traceback)"}')
                    traceback.print_exc()
            except Exception as error:
                # Malformed responses and transport errors are failures, never skips.
                failures.append(f'{label}: {type(error).__name__}: {error}')
                print(f'{label}: REQUEST/RESPONSE ERROR after {perf_counter()-start:.3f}s: {type(error).__name__}: {error}',flush=True)
                traceback.print_exc()
    if failures:
        print('Planning HTTP smoke FAILED:\n'+'\n'.join(f'- {failure}' for failure in failures),flush=True)
    else:
        print('Planning HTTP smoke passed; first/repeat are per dataset in this process, not proof of Vercel cold starts.')
    return failures


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',default='http://127.0.0.1:8000')
    args=parser.parse_args()
    if run_smoke(args.url):
        raise SystemExit(1)


if __name__=='__main__':
    main()
