"""A failed blob cleanup must not hide a committed authoritative reference."""
from concurrent.futures import ThreadPoolExecutor
from secrets import token_urlsafe
from threading import Barrier
import pytest
from fastapi.testclient import TestClient
from backend.app.data.storage import ObjectUnavailable
from backend.app.data.private_storage import PrivateStorage
from backend.tests.private_provider_harness import provider


def test_committed_replacement_returns_readable_reference_and_retries(caplog):
    store=provider(lambda:100.);owner=token_urlsafe(32)
    old=store.put(owner,b'original','draft');blob=store.metadata.read(old.object_id).blob
    store.blobs.fail_delete=True
    new=store.replace(owner,old,b'committed replacement','draft')
    assert store.get(owner,new,'draft')==b'committed replacement'
    with pytest.raises(ObjectUnavailable):store.get(owner,old,'draft')
    assert blob in store.metadata.garbage() and blob in store.blobs.objects
    assert 'private_cleanup_deferred failures=1' in caplog.text
    assert all(value not in caplog.text for value in (old.object_id,new.object_id,blob,owner))
    store.blobs.fail_delete=False;store.sweep()
    assert blob not in store.blobs.objects and not store.metadata.garbage()
    assert store.get(owner,new,'draft')==b'committed replacement'


def test_two_replacement_writers_still_have_one_winner_when_cleanup_fails():
    first=provider(lambda:100.);owner=token_urlsafe(32)
    second=PrivateStorage(first.blobs,first.metadata,clock=first.clock)
    old=first.put(owner,b'old','draft');barrier=Barrier(2)
    promote=first.metadata.promote
    def simultaneous(*args):barrier.wait();return promote(*args)
    first.metadata.promote=simultaneous;first.blobs.fail_delete=True
    def replace(store,value):
        try:return store.replace(owner,old,value,'draft')
        except ObjectUnavailable:return None
    with ThreadPoolExecutor(2) as pool:
        a=pool.submit(replace,first,b'a');b=pool.submit(replace,second,b'b')
        winners=[r for r in (a.result(),b.result()) if r is not None]
    assert len(winners)==1 and first.get(owner,winners[0],'draft') in (b'a',b'b')
    with pytest.raises(ObjectUnavailable):first.get(owner,old,'draft')
    assert len(first.metadata.garbage())==2  # old blob and losing staged write
    first.blobs.fail_delete=False;first.sweep()
    assert not first.metadata.garbage() and len(first.blobs.objects)==1


@pytest.mark.parametrize('operation',['delete','reset'])
def test_committed_retirement_succeeds_with_durable_cleanup(operation):
    store=provider(lambda:100.);owner=token_urlsafe(32)
    ref=store.put(owner,b'accepted bytes','accepted_workbook');row=store.metadata.read(ref.object_id)
    store.blobs.fail_delete=True
    if operation=='delete':store.delete(owner,ref)
    else:store.reset(owner)
    with pytest.raises(ObjectUnavailable):store.authorize_download(owner,ref,'accepted_workbook')
    assert row.blob in store.metadata.garbage()
    with pytest.raises(OSError):store.sweep()  # scheduled cleanup still reports failure
    store.blobs.fail_delete=False;store.sweep()
    assert not store.metadata.garbage() and not store.blobs.objects


def test_upload_finalization_preserves_success_and_original_validation_failure():
    from backend.app.main import sample
    from backend.app.data.workbook import template, WorkbookError
    from backend.tests.test_private_storage import grant
    store=provider(lambda:100.);owner=token_urlsafe(32);data=sample('fixture')[0]
    auth,row=grant(store,owner,template(data));store.blobs.fail_delete=True
    restored,_,_=store.finalize_upload(owner,auth.reference)
    assert restored==data and row.blob in store.metadata.garbage()
    with pytest.raises(ObjectUnavailable):store.finalize_upload(owner,auth.reference)
    bad,badrow=grant(store,owner,b'not an XLSX')
    with pytest.raises(WorkbookError):store.finalize_upload(owner,bad.reference)
    assert badrow.blob in store.metadata.garbage()
    store.blobs.fail_delete=False;store.sweep()
    assert not store.metadata.garbage() and not store.blobs.objects


def test_committed_review_api_returns_new_reference_despite_cleanup_failure(monkeypatch):
    from backend.app.main import app
    from backend.app.data import workflow_api
    store=provider(lambda:100.)
    monkeypatch.setattr(workflow_api,'store',store)
    monkeypatch.setattr(workflow_api,'configuration',lambda:{'enabled':True,'driver':'object'})
    with TestClient(app) as client:
        client.get('/api/workflow/session')
        plan=client.post('/api/plan/sample',json={'size':'fixture'}).json()
        old=plan['review_id'];review=client.get(f'/api/workflow/review/{old}').json()
        # A cached bundled forecast cannot bypass the private run binding.
        detail={'sku':'SKU001','location_id':'S1','expected_run_id':plan['run_id']}
        evidence=client.post(f'/api/workflow/review/{old}/detail',json=detail).json()
        assert evidence['plan_run_id']==plan['run_id'] and evidence['review_revision']==review['revision']
        assert client.post(f'/api/workflow/review/{old}/detail',json={**detail,'expected_run_id':'wrong'}).status_code==409
        blob=store.metadata.read(old).blob;store.blobs.fail_delete=True
        response=client.post(f'/api/workflow/review/{old}/decision',json={
            'revision':review['revision'],'action_id':plan['proposed']['purchases'][0]['action_id'],'status':'rejected'})
        assert response.status_code==200,response.text
        new=response.json()['reference']
        assert client.get(f'/api/workflow/review/{new}').json()['state']=='stale'
        assert client.get(f'/api/workflow/review/{old}').status_code==404
        assert client.post(f'/api/workflow/review/{new}/detail',json=detail).status_code==409
        assert blob in store.metadata.garbage()
        store.blobs.fail_delete=False;store.sweep()
        assert not store.metadata.garbage() and blob not in store.blobs.objects
        assert client.get(f'/api/workflow/review/{new}').status_code==200
