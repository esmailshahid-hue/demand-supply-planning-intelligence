"""Private expiring objects, with a provider-neutral interface and local-only driver.

No durable plan history. A production driver must implement equivalent ownership,
expiry, size and deletion guarantees before hosted uploads can be enabled.
"""
import atexit
from hashlib import sha256
import os
from pathlib import Path
import re
import shutil
from secrets import token_urlsafe
from tempfile import TemporaryDirectory, gettempdir
from threading import RLock, Thread, Event
from time import time
from typing import Protocol, Literal
from pydantic import Field
from backend.app.contracts import Contract

TTL = 3600
MAX_OBJECT = 64 * 1024 * 1024
MAX_SESSION = 128 * 1024 * 1024
MAX_TOTAL = 512 * 1024 * 1024
TOKEN = re.compile(r'^[A-Za-z0-9_-]{32,80}$')


class ObjectReference(Contract):
    object_id: str = Field(pattern=TOKEN.pattern)
    driver: Literal['local', 'object'] = 'local'


class UploadAuthorization(Contract):
    reference: ObjectReference
    upload_url: str
    method: Literal['PUT'] = 'PUT'
    expires_at: float
    max_bytes: int
    content_type: str


class DownloadAuthorization(Contract):
    reference: ObjectReference
    download_url: str
    method: Literal['GET'] = 'GET'
    expires_at: float
    content_type: str
    bytes: int
    sha256: str


class Storage(Protocol):
    driver: str
    def put(self, owner: str, content: bytes, kind: str) -> ObjectReference: ...
    def get(self, owner: str, reference: ObjectReference, kind: str) -> bytes: ...
    def delete(self, owner: str, reference: ObjectReference) -> None: ...
    def sweep(self) -> None: ...
    def replace(self, owner: str, reference: ObjectReference, content: bytes, kind: str) -> ObjectReference: ...
    def reset(self, owner: str) -> None: ...


class ObjectUnavailable(ValueError):
    pass


class LocalStorage:
    """Process-private temp directory; worker restart discards all local sessions."""
    driver = 'local'
    def __init__(self, *, ttl=TTL, clock=time):
        self.directory = TemporaryDirectory(prefix='planning-session-')
        self.root = Path(self.directory.name)
        self.ttl, self.clock = ttl, clock
        self.records = {}
        self.lock = RLock()

    def put(self, owner, content, kind):
        if not TOKEN.fullmatch(owner) or len(content) > MAX_OBJECT:
            raise ObjectUnavailable('Object exceeds supported limits or session is unavailable.')
        with self.lock:
            self.sweep()
            owner_hash = sha256(owner.encode()).hexdigest()
            if sum(r[3] for r in self.records.values() if r[0] == owner_hash) + len(content) > MAX_SESSION:
                raise ObjectUnavailable('Session storage limit reached. Reset this session before importing more data.')
            if sum(r[3] for r in self.records.values()) + len(content) > MAX_TOTAL:
                raise ObjectUnavailable('Local temporary storage is full. Retry after expired sessions are cleaned up.')
            key = token_urlsafe(32)
            path = self.root / key
            try:
                with path.open('xb') as stream:
                    os.chmod(path, 0o600); stream.write(content)
                self.records[key] = (owner_hash, kind, self.clock()+self.ttl, len(content))
            except BaseException:
                path.unlink(missing_ok=True)
                raise
            return ObjectReference(object_id=key)

    def _record(self, owner, reference):
        self.sweep()
        row = self.records.get(reference.object_id)
        if reference.driver != 'local' or not row or row[0] != sha256(owner.encode()).hexdigest():
            raise ObjectUnavailable('Object is unavailable or expired in this session. Import again.')
        return row

    def get(self, owner, reference, kind):
        with self.lock:
            row = self._record(owner, reference)
            if row[1] != kind: raise ObjectUnavailable('Object type does not match this operation.')
            return (self.root / reference.object_id).read_bytes()

    def delete(self, owner, reference):
        with self.lock:
            self._record(owner, reference)
            (self.root / reference.object_id).unlink(missing_ok=True)
            del self.records[reference.object_id]

    def replace(self, owner, reference, content, kind):
        # The old opaque token is the compare-and-swap version. Only one writer
        # may consume it, and failure must leave the old value readable.
        with self.lock:
            self.get(owner, reference, kind)
            fresh = self.put(owner, content, kind)
            self.delete(owner, reference)
            return fresh

    def reset(self, owner):
        with self.lock:
            for key, row in list(self.records.items()):
                if row[0] == sha256(owner.encode()).hexdigest():
                    (self.root / key).unlink(missing_ok=True); del self.records[key]

    def sweep(self):
        with self.lock:
            for key, row in list(self.records.items()):
                if row[2] <= self.clock():
                    (self.root / key).unlink(missing_ok=True); del self.records[key]

    def close(self):
        with self.lock:
            self.records.clear(); self.directory.cleanup()


def configuration():
    choice = os.getenv('PLANNING_UPLOAD_STORAGE', 'local' if not os.getenv('VERCEL') else 'disabled')
    if choice != 'local' or os.getenv('VERCEL'):
        return {'enabled': False, 'driver': 'disabled', 'message': 'Hosted uploads and accepted files are blocked pending an authorized private object-storage driver and lifecycle verification. Bundled samples remain available.'}
    return {'enabled': True, 'driver': 'local', 'message': 'Local temporary storage: workbook bytes are deleted after parsing. Normalized data, drafts and accepted files expire after one hour; cleanup runs every 30 seconds, on reset and on normal process exit. Download accepted files before leaving.'}


store = LocalStorage()
_stop = Event()
def sweep_abandoned():
    # Recover expired local directories left by a crashed process. Only this
    # service's private naming prefix, current UID and old directories qualify.
    for path in list(Path(gettempdir()).glob('planning-session-*'))+list(Path(gettempdir()).glob('planning-import-*')):
        try:
            if path != store.root and not path.is_symlink() and path.is_dir() and path.stat().st_uid==os.getuid() and path.stat().st_mtime<time()-TTL:
                shutil.rmtree(path)
        except OSError:
            pass
def _cleanup():
    while not _stop.wait(30):
        store.sweep();sweep_abandoned()
Thread(target=_cleanup, daemon=True, name='planning-object-cleanup').start()
def _close():
    _stop.set(); store.close()
atexit.register(_close)
