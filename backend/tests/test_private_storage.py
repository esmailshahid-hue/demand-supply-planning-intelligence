"""Provider boundary conformance, including two instances sharing backend state."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from secrets import token_urlsafe
from threading import Barrier
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
import pytest
from backend.app.data.storage import LocalStorage, ObjectUnavailable, ObjectReference
from backend.app.data.private_storage import PrivateStorage
from backend.app.data.workbook import MIME, MAX_FILE, WorkbookError, template
from backend.tests.private_provider_harness import provider

@pytest.fixture
def private():
    now=[100.]
    return provider(lambda:now[0]),now,token_urlsafe(32)

@pytest.mark.parametrize('kind',['local','private'])
def test_ownership_expiry_immutable_bytes_and_atomic_replacement(kind):
    now=[100.];owner=token_urlsafe(32)
    store=LocalStorage(clock=lambda:now[0]) if kind=='local' else provider(lambda:now[0])
    other=store if kind=='local' else PrivateStorage(store.blobs,store.metadata,clock=store.clock)
    try:
        ref=store.put(owner,b'accepted bytes','draft')
        assert other.get(owner,ref,'draft')==b'accepted bytes'
        for bad in (ObjectReference(object_id=token_urlsafe(32),driver=store.driver),):
            with pytest.raises(ObjectUnavailable):store.get(owner,bad,'draft')
        with pytest.raises(ObjectUnavailable):store.get(token_urlsafe(32),ref,'draft')
        with pytest.raises(ObjectUnavailable):store.get(owner,ref,'dataset')
        barrier=Barrier(2)
        def mutate(driver,value):
            barrier.wait()
            try:return driver.replace(owner,ref,value,'draft')
            except ObjectUnavailable:return None
        with ThreadPoolExecutor(2) as pool:
            a=pool.submit(mutate,store,b'one');b=pool.submit(mutate,other,b'two')
            winners=[r for r in (a.result(),b.result()) if r is not None]
        assert len(winners)==1
        with pytest.raises(ObjectUnavailable):store.get(owner,ref,'draft')
        assert other.get(owner,winners[0],'draft') in (b'one',b'two')
        now[0]+=3601
        with pytest.raises(ObjectUnavailable):store.get(owner,winners[0],'draft')
        store.sweep()
        if kind=='private':assert not store.blobs.objects and not store.metadata.rows
    finally:
        if kind=='local':store.close()

def grant(store,owner,content):
    auth=store.authorize_upload(owner,size=len(content),content_type=MIME,digest=sha256(content).hexdigest())
    row=store.metadata.read(auth.reference.object_id)
    store.blobs.put(row.blob,content,MIME)
    return auth,row

def test_verified_workbook_finalize_and_single_use(private):
    from backend.app.main import sample
    store,_,owner=private;data=sample('fixture')[0]
    auth,row=grant(store,owner,template(data))
    assert auth.expires_at==400 and auth.method=='PUT' and auth.reference.driver=='object'
    with pytest.raises(ObjectUnavailable):store.finalize_upload(token_urlsafe(32),auth.reference)
    restored,_,_=store.finalize_upload(owner,auth.reference)
    assert restored==data and row.blob not in store.blobs.objects
    with pytest.raises(ObjectUnavailable):store.finalize_upload(owner,auth.reference)
    with pytest.raises(ObjectUnavailable):store.blobs.put(row.blob,b'late PUT',MIME)

@pytest.mark.parametrize('corruption',['mime','size','hash','archive','missing'])
def test_failed_uploads_are_retired(private,corruption):
    store,_,owner=private
    raw=b'not a workbook'
    if corruption=='archive':
        out=BytesIO()
        with ZipFile(out,'w',ZIP_DEFLATED) as z:z.writestr('large.xml',b'0'*1_000_000)
        raw=out.getvalue()
    auth,row=grant(store,owner,raw)
    if corruption=='mime':store.blobs.put(row.blob,raw,'text/plain')
    if corruption=='size':store.blobs.put(row.blob,raw+b'x',MIME)
    if corruption=='hash':store.blobs.put(row.blob,b'x'*len(raw),MIME)
    if corruption=='missing':store.blobs.delete(row.blob)
    with pytest.raises((ObjectUnavailable,WorkbookError)):store.finalize_upload(owner,auth.reference)
    assert store.metadata.read(row.key) is None and row.blob not in store.blobs.objects

def test_authorization_limits_abandonment_and_cleanup_retry(private):
    store,now,owner=private
    for size,mime in [(MAX_FILE+1,MIME),(1,'text/plain'),(0,MIME)]:
        with pytest.raises(ObjectUnavailable):store.authorize_upload(owner,size=size,content_type=mime,digest='0'*64)
    auth,row=grant(store,owner,b'abandoned')
    now[0]+=301;store.blobs.fail_delete=True
    with pytest.raises(OSError):store.sweep()
    assert store.metadata.read(row.key) is None and row.blob in store.metadata.garbage()
    store.blobs.fail_delete=False;store.sweep()
    assert not store.blobs.objects and not store.metadata.garbage()

def test_integrity_write_failure_and_delete(private):
    store,_,owner=private
    store.blobs.fail_write=True
    with pytest.raises(OSError):store.put(owner,b'bytes','draft')
    assert not store.metadata.rows
    store.blobs.fail_write=False
    ref=store.put(owner,b'bytes','draft');row=store.metadata.read(ref.object_id)
    store.blobs.put(row.blob,b'other','application/octet-stream')
    with pytest.raises(ObjectUnavailable):store.get(owner,ref,'draft')
    store.delete(owner,ref)
    with pytest.raises(ObjectUnavailable):store.get(owner,ref,'draft')


def test_provider_composition_runs_existing_authoritative_review_workflow(private,monkeypatch):
    from backend.app.data import workflow_api
    from backend.tests.test_workflow_api import test_uploaded_provenance_survives_regeneration_acceptance_and_portable_reopen
    store,_,_=private
    monkeypatch.setattr(workflow_api,'store',store)
    # Test factory injection only; production configuration remains fail-closed.
    monkeypatch.setattr(workflow_api,'configuration',lambda:{'enabled':True,'driver':'object','message':'test provider'})
    test_uploaded_provenance_survives_regeneration_acceptance_and_portable_reopen('fixture','full')


def test_provider_composition_scenarios_and_dataset_isolation(private,monkeypatch):
    from backend.app.data import workflow_api
    from backend.tests.test_workflow_api import test_full_upload_provenance_survives_plan_scenarios_evidence_and_wrong_size
    store,_,_=private
    monkeypatch.setattr(workflow_api,'store',store)
    monkeypatch.setattr(workflow_api,'configuration',lambda:{'enabled':True,'driver':'object','message':'test provider'})
    test_full_upload_provenance_survives_plan_scenarios_evidence_and_wrong_size()


@pytest.mark.parametrize('kind',['accepted_workbook','accepted_snapshot'])
def test_private_accepted_download_authorization(private,kind):
    store,now,owner=private;raw=b'authoritative deterministic export'
    ref=store.put(owner,raw,kind)
    auth=store.authorize_download(owner,ref,kind)
    assert auth.method=='GET' and auth.expires_at==now[0]+60
    assert auth.sha256==sha256(raw).hexdigest() and auth.bytes==len(raw)
    assert store.get(owner,ref,kind)==store.get(owner,ref,kind)==raw
    with pytest.raises(ObjectUnavailable):store.authorize_download(token_urlsafe(32),ref,kind)
    with pytest.raises(ObjectUnavailable):store.authorize_download(owner,ref,'draft')
    store.delete(owner,ref)
    with pytest.raises(ObjectUnavailable):store.authorize_download(owner,ref,kind)
