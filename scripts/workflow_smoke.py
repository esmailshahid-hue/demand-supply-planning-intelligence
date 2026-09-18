"""Production upload -> exact review -> replay -> acceptance -> portable exports."""
import argparse
from http.cookiejar import CookieJar
from urllib.request import build_opener,HTTPCookieProcessor,Request
from time import perf_counter
import json
from backend.app.data.sample import generate_sample
from backend.app.data.workbook import template,parse
from backend.app.data.accepted import read_snapshot
from backend.app.simulation.replay import cents


def run(url):
    client=build_opener(HTTPCookieProcessor(CookieJar()))
    def request(path,body=None,method=None,headers=None):
        started=perf_counter()
        raw=body if isinstance(body,bytes) else json.dumps(body).encode() if body is not None else None
        with client.open(Request(url+path,data=raw,method=method,headers={'Content-Type':'application/json',**(headers or {})}),timeout=90) as response:
            content=response.read()
        return content,round(perf_counter()-started,3)
    capabilities=json.loads(request('/api/workflow/session')[0]);assert capabilities['enabled'],capabilities['message']
    for size in ('fixture','full'):
        data=generate_sample(size);file=template(data);restored,_,metrics=parse(file);assert restored==data
        # Actual multipart encoding, although the chosen local driver sends raw XLSX.
        import httpx
        multipart=httpx.Request('POST',url+'/api/workflow/import',files={'file':(size+'.xlsx',file,'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}).read()
        uploaded,upload_seconds=request('/api/workflow/import',file,'PUT',{'X-Server-Processing':'confirmed','X-Filename':size+'.xlsx','Content-Type':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'})
        imported=json.loads(uploaded);source={'X-Dataset-Ref':imported['reference']['object_id']}
        authoritative=imported['provenance'];assert authoritative['source']=='uploaded' and authoritative['sample_size'] is None
        assert authoritative['dataset_hash']==imported['input_hash'] and authoritative['dimensions']=={
            'products':len(data.products),'locations':len(data.locations),'assortment':len(data.assortment),'history_rows':len(data.demand_history)}
        # Deliberately send the opposite bundled label. The private reference is authoritative.
        raw,planning_seconds=request('/api/plan/sample',{'size':'fixture' if size=='full' else 'full'},headers=source);planned=json.loads(raw)
        assert planned['proposed']['replay']['feasible'] and planned['review_id']
        assert planned['provenance']==authoritative
        review=json.loads(request('/api/workflow/review/'+planned['review_id'])[0]);action=planned['proposed']['purchases'][0]
        review=json.loads(request('/api/workflow/review/'+review['reference']+'/decision',{'revision':review['revision'],'action_id':action['action_id'],'status':'accepted'})[0]);assert review['state']=='stale'
        raw,review_seconds=request('/api/workflow/review/'+review['reference']+'/regenerate',{'revision':review['revision']});review=json.loads(raw)
        assert review['state']=='draft' and review['provenance']==authoritative,review['failures']
        regenerated=json.loads(request('/api/workflow/review/'+review['reference']+'/plan')[0])
        assert regenerated['provenance']==authoritative and regenerated['proposed']['replay']['feasible']
        trace=regenerated['forecasts'][0]
        evidence=json.loads(request('/api/workflow/review/'+review['reference']+'/detail',{
            'sku':trace['sku'],'location_id':trace['location_id'],'action_id':action['action_id']})[0])
        assert evidence['provenance']==authoritative
        accepted,accept_seconds=request('/api/workflow/review/'+review['reference']+'/accept',{'revision':review['revision'],'acknowledge_shortfalls':True});review=json.loads(accepted)
        assert review['provenance']==authoritative
        workbook,export_seconds=request('/api/workflow/review/'+review['reference']+'/download/workbook')
        portable,_=request('/api/workflow/review/'+review['reference']+'/download/snapshot')
        portable_repeat,_=request('/api/workflow/review/'+review['reference']+'/download/snapshot');assert portable_repeat==portable
        snapshot=read_snapshot(portable);policy=snapshot.draft.result.proposed;ledger=policy.replay
        assert snapshot.draft.result.provenance.model_dump(mode='json')==authoritative
        assert ledger.feasible and not ledger.failures
        assert sum(cents(p.value) for p in policy.purchases)==cents(ledger.summary.commitments)
        assert sum(cents(p.amount) for p in ledger.payments)==cents(ledger.summary.payments)
        assert next(p for p in policy.purchases if p.action_id==action['action_id']).units==action['units']
        assert len(set(snapshot.external_ids.values()))==len(policy.purchases)+len(policy.movements)
        reopened=json.loads(request('/api/workflow/snapshot',portable,'PUT',{'X-Server-Processing':'confirmed'})[0]);assert reopened['state']=='read_only'
        portable_source={**authoritative,'source':'portable','sample_size':None};assert reopened['provenance']==portable_source
        print(json.dumps({'size':size,**metrics,'multipart_bytes':len(multipart),'upload_http_s':upload_seconds,'planning_http_s':planning_seconds,'review_http_s':review_seconds,'accept_http_s':accept_seconds,'export_http_s':export_seconds,'export_bytes':len(workbook),**review['measurements'],
            'provenance':{'initial_plan':planned['provenance'],'regenerated_plan':regenerated['provenance'],'evidence':evidence['provenance'],
                'final_acceptance':review['provenance'],'downloaded_snapshot':snapshot.draft.result.provenance.model_dump(mode='json'),'portable_reopen':reopened['provenance']},
            'plan_status':regenerated['status'],'replay':ledger.feasible,'financial_reconciliation':True,'external_ids_unique':True,
            'snapshot_bytes':len(portable),'deterministic_snapshot_download':portable_repeat==portable,'snapshot_reopened':True}),flush=True)
    assert json.loads(request('/api/workflow/session',method='DELETE')[0])['reset']
    print('Private temporary session reset passed.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:8000');run(parser.parse_args().url)
