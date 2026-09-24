"""Reproducible fixture calculation traces over actual same-domain HTTP APIs.

Private review/export is exercised only when the server advertises that local
capability; its absence is reported, never bypassed. No orders are sent.
"""
import argparse
from datetime import date
from http.cookiejar import CookieJar
from io import BytesIO
import json
from pathlib import Path
from time import perf_counter
from urllib.request import HTTPCookieProcessor, Request, build_opener

from openpyxl import load_workbook
from backend.app.data.accepted import read_snapshot
from backend.app.data.sample import generate_sample
from backend.app.planning.inputs import Inputs, network_forecasts
from backend.app.simulation.replay import cents


def run(url):
    client=build_opener(HTTPCookieProcessor(CookieJar())); measurements=[]
    def call(path,body=None,raw=False):
        started=perf_counter()
        with client.open(Request(url+path,data=json.dumps(body).encode() if body is not None else None,
            headers={'Content-Type':'application/json'}),timeout=60) as response:
            payload=response.read()
        measurements.append({'path':path.split('/review/')[0] if '/review/' in path else path,
            'http_s':round(perf_counter()-started,3),'bytes':len(payload),'status':response.status})
        assert len(payload)<4_500_000
        return payload if raw else json.loads(payload)
    session=call('/api/workflow/session')
    f=call('/api/forecast/sample',{'size':'fixture','sku':'SKU001','location_id':'S1'})
    p=call('/api/plan/sample?include_stock=true',{'size':'fixture'}); policy=p['proposed']; ledger=policy['replay']
    assert ledger['feasible'] and not ledger['failures']
    purchase=next(a for a in policy['purchases'] if a['action_id']=='P-OFFER008-0')
    move=next(a for a in policy['movements'] if a['source']=='S2' and a['destination']=='S1')
    data=generate_sample(); demand,buffers,_,failures=network_forecasts(data,perf_counter()+30)
    assert not failures
    ctx=Inputs(data,demand,buffers)
    offer=next(o for o in data.supplier_offers if o.offer_id==purchase['offer_id'])
    assert purchase['units']%offer.case_size==0 and purchase['units']>=offer.moq_units
    assert cents(purchase['value'])==cents(purchase['units']*offer.price_per_base_unit)
    assert offer.valid_from<=date.fromisoformat(purchase['order_date'])<=offer.valid_to
    assert ctx.purchase(offer,0,purchase['units']).model_dump(mode='json')==purchase
    mday=date.fromisoformat(move['dispatch_date']); idx=(mday-data.settings.as_of).days
    donor=next(r for r in ledger['stock'] if (r['sku'],r['location_id'],r['day'])==(move['sku'],move['source'],str(mday)))
    receiver=next(r for r in ledger['stock'] if (r['sku'],r['location_id'],r['day'])==(move['sku'],move['destination'],move['arrival_date']))
    reserve=ctx.reserve[move['sku'],move['source'],idx]
    assert donor['closing']>=reserve and receiver['receipts']>=move['units']
    group=f'{move["source"]}-{move["destination"]}-{move["dispatch_date"]}'
    fee=[r for r in ledger['payments'] if r['reference']==group]; assert len(fee)==1
    installments=[r for r in ledger['payments'] if r['reference']==purchase['action_id']]
    assert sum(cents(r['amount']) for r in installments)==cents(purchase['value'])
    assert sum(cents(a['value']) for a in policy['purchases'])==cents(ledger['summary']['commitments'])
    assert sum(cents(r['amount']) for r in ledger['payments'])==cents(ledger['summary']['payments'])
    baseline=call('/api/scenarios/capture',{'size':'fixture','dataset_hash':p['input_hash'],
        'purchases':policy['purchases'],'movements':policy['movements']})
    assert baseline['original']['purchases']==policy['purchases'] and baseline['original']['movements']==policy['movements']
    definition={'funding':[{'week_start':str(data.settings.as_of),'commitment':2000,'payment':4500}]}
    scenario=call('/api/scenarios/compare',{'baseline':baseline['baseline'],'scenario':definition})
    assert scenario['original']['summary']==ledger['summary']
    assert scenario['frozen']['feasible'] and scenario['replanned']['feasible']
    assert scenario['frozen']['purchases']==policy['purchases'] and scenario['frozen']['movements']==policy['movements']
    for field,before,after in [('shock_delta','original','frozen'),('replan_delta','frozen','replanned'),('net_delta','original','replanned')]:
        for key,value in scenario[field].items():
            assert abs(value-(scenario[after]['summary'][key]-scenario[before]['summary'][key]))<1e-8
    review={'enabled':session['enabled'],'message':session['message']}
    if session['enabled']:
        r=call('/api/workflow/review/'+p['review_id']); old_ref=r['reference']
        r=call('/api/workflow/review/'+r['reference']+'/decision',{'revision':r['revision'],
            'action_id':purchase['action_id'],'status':'edited_quantity','quantity':120})
        assert r['state']=='stale'
        r=call('/api/workflow/review/'+r['reference']+'/regenerate',{'revision':r['revision']})
        assert r['state']=='draft' and r['reference']!=old_ref
        revised=call('/api/workflow/review/'+r['reference']+'/plan?include_stock=true')
        edited=next(a for a in revised['proposed']['purchases'] if a['action_id']==purchase['action_id'])
        assert edited['units']==120 and revised['provenance']==p['provenance']
        r=call('/api/workflow/review/'+r['reference']+'/accept',{'revision':r['revision'],'acknowledge_shortfalls':True})
        assert r['state']=='accepted'
        raw=call('/api/workflow/review/'+r['reference']+'/download/snapshot',raw=True)
        saved=read_snapshot(raw)
        assert saved.draft.result.proposed.model_dump(mode='json')==revised['proposed']
        workbook=load_workbook(BytesIO(call('/api/workflow/review/'+r['reference']+'/download/workbook',raw=True)),read_only=True)
        rows=workbook['PurchaseActions'].values; header=next(rows)
        exported=next(dict(zip(header,row)) for row in rows if row[0]==edited['action_id'])
        # Workbook floats are lossless decimal text by the existing sheet contract.
        assert exported['units']==edited['units'] and cents(exported['value'])==cents(edited['value'])
        summary=dict(list(workbook['Summary'].values)[1:])
        assert all(summary[k]==v for k,v in revised['proposed']['replay']['summary'].items() if v is None or not isinstance(v,float))
        assert all(float(summary[k])==v for k,v in revised['proposed']['replay']['summary'].items() if isinstance(v,float))
        workbook.close()
        review.update(action=edited,exported_action=exported,summary=revised['proposed']['replay']['summary'],
            provenance=revised['provenance'],replacement_reference_distinct=True,export_reconciled=True)
    return {'forecast':{k:f[k] for k in ('input_hash','selected_method','visible_units','improvement_pct','selection','final_check')},
        'purchase':purchase,'offer':offer.model_dump(mode='json'),'installments':installments,
        'movement':move,'donor_stock':donor,'origin_donor_reserve':reserve,'receiver_stock':receiver,'grouped_fee':fee,
        'cash':ledger['cash'],'summary':ledger['summary'],'scenario':{'definition':definition,
            'summaries':{k:scenario[k]['summary'] for k in ('original','frozen','replanned')},
            'shock_delta':scenario['shock_delta'],'replan_delta':scenario['replan_delta'],'net_delta':scenario['net_delta']},
        'review':review,'measurements':measurements}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:8000')
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=run(args.url);args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'measurements':result['measurements'],'review_enabled':result['review']['enabled'],
        'replan_delta':result['scenario']['replan_delta'],'net_delta':result['scenario']['net_delta'],'trace_reconciled':True},indent=2))
