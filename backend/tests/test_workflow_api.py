from fastapi.testclient import TestClient
from backend.app.main import app,sample
from backend.app.data.workbook import template
from backend.app.data.storage import store


def upload(client,size):
    response=client.put('/api/workflow/import',content=template(sample(size)[0]),headers={
        'X-Server-Processing':'confirmed','X-Filename':size+'.xlsx'})
    assert response.status_code==200,response.text
    return response.json()['reference']['object_id']


def test_upload_same_plan_private_session_stale_export_and_cleanup():
    with TestClient(app) as client, TestClient(app) as stranger:
        client.get('/api/workflow/session');stranger.get('/api/workflow/session')
        before=len(store.records)
        invalid=client.put('/api/workflow/import',content=b'bad',headers={'X-Server-Processing':'confirmed','X-Filename':'bad.xlsx'})
        assert invalid.status_code==422 and len(store.records)==before
        content=template(sample('fixture')[0])
        imported=client.put('/api/workflow/import',content=content,headers={'X-Server-Processing':'confirmed','X-Filename':'fixture.xlsx'})
        assert imported.status_code==200
        source={'X-Dataset-Ref':imported.json()['reference']['object_id']}
        assert not any(row[1]=='upload' for row in store.records.values())
        assert stranger.get('/api/sample',headers=source).status_code==404
        original=client.post('/api/plan/sample',json={'size':'fixture'}).json()
        uploaded=client.post('/api/plan/sample',json={'size':'fixture'},headers=source).json()
        assert original['input_hash']==uploaded['input_hash']
        assert original['proposed']==uploaded['proposed']
        assert original['exceptions']==uploaded['exceptions']
        ref=uploaded['review_id'];review=client.get('/api/workflow/review/'+ref).json()
        assert client.get('/api/workflow/review/'+ref+'/download/workbook').status_code==409
        action=uploaded['proposed']['purchases'][0]
        changed=client.post('/api/workflow/review/'+ref+'/decision',json={'revision':review['revision'],'action_id':action['action_id'],'status':'rejected'}).json()
        assert changed['state']=='stale'
        assert client.get('/api/workflow/review/'+ref).status_code==404
        assert client.post('/api/workflow/review/'+changed['reference']+'/accept',json={'revision':changed['revision'],'acknowledge_shortfalls':True}).status_code==409
        assert client.get('/api/workflow/review/'+changed['reference']+'/download/snapshot').status_code==409
        assert client.delete('/api/workflow/session').json()=={'reset':True}
        assert client.get('/api/sample',headers=source).status_code==404


def test_hosted_upload_block_does_not_break_sample(monkeypatch):
    monkeypatch.setenv('VERCEL','1')
    with TestClient(app) as client:
        assert client.get('/api/workflow/session').json()['enabled'] is False
        assert client.put('/api/workflow/import',content=b'bad').status_code==503
        assert client.get('/api/sample').status_code==200
        assert client.get('/api/workflow/template/blank').status_code==200


def test_full_upload_provenance_survives_plan_scenarios_evidence_and_wrong_size():
    with TestClient(app) as client:
        client.get('/api/workflow/session')
        bundled=client.post('/api/plan/sample',json={'size':'full'}).json()
        full_ref=upload(client,'full');headers={'X-Dataset-Ref':full_ref}
        # The private reference is authoritative; the deliberately wrong fixture
        # label cannot replace its 60-product dataset.
        planned=client.post('/api/plan/sample',json={'size':'fixture'},headers=headers)
        assert planned.status_code==200,planned.text
        planned=planned.json();source=planned['provenance']
        assert source['source']=='uploaded' and source['sample_size'] is None
        assert source['dimensions']=={'products':60,'locations':5,'assortment':240,'history_rows':99160}
        assert source['dataset_hash']==planned['input_hash']==bundled['input_hash']
        assert [{k:v for k,v in row.items() if k!='run_id'} for row in planned['forecasts']]==[
            {k:v for k,v in row.items() if k!='run_id'} for row in bundled['forecasts']]
        assert planned['proposed']==bundled['proposed']
        capture=client.post('/api/scenarios/capture',headers=headers,json={'size':'fixture','dataset_hash':planned['input_hash'],
            'purchases':planned['proposed']['purchases'],'movements':planned['proposed']['movements']})
        assert capture.status_code==200,capture.text
        baseline=capture.json()
        assert baseline['baseline']['size'] is None and baseline['baseline']['provenance']==source
        compared=client.post('/api/scenarios/compare',headers=headers,json={'baseline':baseline['baseline'],'scenario':{}})
        assert compared.status_code==200,compared.text
        compared=compared.json()
        assert compared['provenance']==source
        assert compared['original']['summary']==planned['proposed']['replay']['summary']
        assert compared['replanned']['purchases']==planned['proposed']['purchases']
        evidence=client.post(f"/api/workflow/review/{planned['review_id']}/detail",json={'sku':'SKU001','location_id':'S1'})
        assert evidence.status_code==200,evidence.text
        assert evidence.json()['provenance']==source
        fixture_ref=upload(client,'fixture')
        mismatch=client.post('/api/scenarios/compare',headers={'X-Dataset-Ref':fixture_ref},json={'baseline':baseline['baseline'],'scenario':{}})
        assert mismatch.status_code==422 and mismatch.json()['code']=='invalid_scenario'
        fixture_plan=client.post('/api/plan/sample',headers={'X-Dataset-Ref':fixture_ref},json={'size':'full'}).json()
        assert fixture_plan['provenance']['source']=='uploaded'
        assert fixture_plan['provenance']['sample_size'] is None
        assert fixture_plan['provenance']['dimensions']['products']==10
        assert client.delete('/api/workflow/session').json()=={'reset':True}
        assert client.get('/api/sample',headers=headers).status_code==404


def test_reopened_snapshot_uses_portable_provenance():
    with TestClient(app) as client:
        client.get('/api/workflow/session')
        reference=upload(client,'fixture');headers={'X-Dataset-Ref':reference}
        planned=client.post('/api/plan/sample',headers=headers,json={'size':'full'}).json()
        review=client.get('/api/workflow/review/'+planned['review_id']).json()
        accepted=client.post('/api/workflow/review/'+review['reference']+'/accept',json={
            'revision':review['revision'],'acknowledge_shortfalls':True})
        assert accepted.status_code==200,accepted.text
        accepted=accepted.json()
        portable=client.get('/api/workflow/review/'+accepted['reference']+'/download/snapshot').content
        reopened=client.put('/api/workflow/snapshot',content=portable,headers={'X-Server-Processing':'confirmed'})
        assert reopened.status_code==200,reopened.text
        reopened=reopened.json();source=reopened['provenance']
        assert reopened['state']=='read_only' and source['source']=='portable' and source['sample_size'] is None
        assert source['dimensions']['products']==10
        plan=client.get('/api/workflow/review/'+reopened['reference']+'/plan').json()
        assert plan['provenance']==source and plan['input_hash']==source['dataset_hash']
        captured=client.post('/api/scenarios/capture',headers={'X-Dataset-Ref':reopened['dataset_ref']},json={
            'size':None,'dataset_hash':plan['input_hash'],'purchases':plan['proposed']['purchases'],'movements':plan['proposed']['movements']})
        assert captured.status_code==200,captured.text
        assert captured.json()['baseline']['provenance']==source


def test_missing_private_reference_fails_clearly():
    with TestClient(app) as client:
        client.get('/api/workflow/session')
        response=client.post('/api/plan/sample',headers={'X-Dataset-Ref':'x'*43},json={'size':'fixture'})
        assert response.status_code==404
        assert 'unavailable' in response.json()['message'].lower()
