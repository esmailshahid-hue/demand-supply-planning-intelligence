"""TEST ONLY provider doubles. Never imported/configured by the application.

Replace this factory with an authorized provider's isolated test namespace to
run the same conformance cases. Locks below model serializable provider calls;
they are NOT an implementation for production serverless metadata.
"""
from dataclasses import replace
from threading import RLock
from backend.app.data.private_storage import PrivateStorage
from backend.app.data.storage import ObjectUnavailable, MAX_SESSION, MAX_TOTAL

class Blobs:
    def __init__(self): self.objects={}; self.fail_write=False; self.fail_delete=False; self.sealed=set()
    def put(self,key,content,content_type):
        if self.fail_write: raise OSError('injected write failure')
        if key in self.sealed: raise ObjectUnavailable('Upload authorization revoked')
        self.objects[key]=(content,content_type)
    def read(self,key,max_bytes):
        if key not in self.objects: raise ObjectUnavailable('Missing blob')
        data,mime=self.objects[key]
        if len(data)>max_bytes: raise ObjectUnavailable('Oversized blob')
        return data,mime
    def authorize_put(self,key,**kwargs): return 'https://private-upload.test/'+key
    def authorize_get(self,key,**kwargs):return 'https://private-download.test/'+key
    def seal(self,key):self.sealed.add(key)
    def delete(self,key):
        if self.fail_delete: raise OSError('injected cleanup failure')
        self.objects.pop(key,None)

class Metadata:
    def __init__(self): self.rows={};self.tombstones=set();self.lock=RLock()
    def _check(self,row):
        if self.rows.get(row.key)!=row: raise ObjectUnavailable('Concurrent or stale revision')
    def _quota(self,row,session_limit=MAX_SESSION,total_limit=MAX_TOTAL):
        if sum(r.size for r in self.rows.values() if r.owner==row.owner)+row.size>session_limit or sum(r.size for r in self.rows.values())+row.size>total_limit:
            raise ObjectUnavailable('Quota exceeded')
    def read(self,key):
        with self.lock: return self.rows.get(key)
    def create(self,row,**limits):
        with self.lock:
            if row.key in self.rows: raise ObjectUnavailable('Duplicate')
            self._quota(row,**limits); self.rows[row.key]=row
    def swap(self,expected,replacement):
        with self.lock:
            self._check(expected)
            assert replacement.key==expected.key and replacement.blob==expected.blob
            self.rows[expected.key]=replacement
    def promote(self,expected,staged,kind):
        with self.lock:
            self._check(expected);self._check(staged)
            assert expected.owner==staged.owner and staged.state=='ready' and staged.kind=='replacement'
            self.rows.pop(expected.key);self.tombstones.add(expected.blob)
            self.rows[staged.key]=replace(staged,kind=kind)
    def retire(self,row):
        with self.lock:
            self._check(row);self.rows.pop(row.key);self.tombstones.add(row.blob)
    def expired(self,now):
        with self.lock:return [r for r in self.rows.values() if r.expires<=now]
    def owned(self,owner):
        with self.lock:return [r for r in self.rows.values() if r.owner==owner]
    def garbage(self):
        with self.lock:return list(self.tombstones)
    def cleaned(self,key):
        with self.lock:self.tombstones.discard(key)

def provider(clock):
    return PrivateStorage(Blobs(),Metadata(),clock=clock)
