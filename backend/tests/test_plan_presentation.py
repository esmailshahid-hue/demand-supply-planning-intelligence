"""Compact decisions preserve full replay, and scoped details use exact actions."""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app, sample
from backend.app.planning.engine import plan
from backend.app.planning.presentation import decisions
from backend.app.scenarios.engine import snapshot, actions_of, detail, digest, provenance
from backend.app.scenarios.contracts import DetailRequest

@pytest.mark.parametrize('size',['fixture','full'])
def test_lazy_ledger_matches_complete_replay_without_mutating_authority(size):
    data=sample(size)[0];full=plan(data);compact=decisions(full)
    assert compact.stock_detail=='on_demand' and not compact.proposed.replay.stock
    assert compact.stock_row_count==len(full.proposed.replay.stock)==56*len(data.inventory)
    assert len(compact.model_dump_json())<len(full.model_dump_json())*.45
    assert decisions(full,True) is full
    for name in ('proposed','benchmark','no_action'):
        expected=getattr(full,name).model_dump(exclude={'replay':{'stock'}})
        assert getattr(compact,name).model_dump(exclude={'replay':{'stock'}})==expected
    base=snapshot(size,data,actions_of(full.proposed))
    request=DetailRequest(baseline=base,policy='original',sku='SKU001',location_id='S1',
                          expected_action_hash=digest(actions_of(full.proposed)))
    first=detail(data,request);second=detail(data,request)
    assert first.stock==second.stock==[r for r in full.proposed.replay.stock if r.sku=='SKU001']
    assert first.cash==full.proposed.replay.cash
    assert first.provenance==provenance(data,'bundled_'+size,size)
    with pytest.raises(ValueError):detail(data,request.model_copy(update={'expected_action_hash':'wrong'}))
    with pytest.raises(ValueError):detail(data,request.model_copy(update={'baseline':base.model_copy(update={'dataset_hash':'wrong'})}))
    with pytest.raises(ValueError):detail(data,request.model_copy(update={'expected_scenario_hash':'wrong'}))


def test_main_route_projects_only_after_persisting_full_review():
    from backend.app.data.workflow_api import load, draft_for
    from backend.app.data.storage import store, ObjectReference
    import gzip,json
    with TestClient(app) as client:
        client.get('/api/workflow/session')
        response=client.post('/api/plan/sample',json={'size':'fixture'});assert response.status_code==200
        value=response.json();ref=value['review_id']
        stored=json.loads(gzip.decompress(store.get(client.cookies['planning_session'],ObjectReference(object_id=ref),'draft')))
        assert value['stock_detail']=='on_demand' and not value['proposed']['replay']['stock']
        assert len(stored['draft']['result']['proposed']['replay']['stock'])==2800
        review=client.get(f'/api/workflow/review/{ref}').json()
        changed=client.post(f'/api/workflow/review/{ref}/decision',json={'revision':review['revision'],
            'action_id':value['proposed']['purchases'][0]['action_id'],'status':'rejected'}).json()
        body={'sku':'SKU001','location_id':'S1'}
        assert client.post(f'/api/workflow/review/{ref}/detail',json=body).status_code==404
        assert client.post(f'/api/workflow/review/{changed["reference"]}/detail',json=body).status_code==409
