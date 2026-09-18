from fastapi.testclient import TestClient
from backend.app.main import app,sample
from backend.app.data.workbook import template
from backend.app.data.storage import store


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
