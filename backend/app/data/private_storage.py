"""Provider-independent private object adapter; never enabled by configuration.

Providers supply private blob transport AND transactional metadata. The latter
owns quota reservation, immutable version consumption and lifecycle tombstones.
No production provider or credentials are selected by this module.
"""
from dataclasses import dataclass, replace
from hashlib import sha256
from secrets import token_urlsafe
from time import time
from typing import Protocol
import logging

from backend.app.data.storage import (ObjectReference, ObjectUnavailable,
    UploadAuthorization, DownloadAuthorization, TOKEN, TTL, MAX_OBJECT, MAX_SESSION, MAX_TOTAL)
from backend.app.data.workbook import MIME, MAX_FILE, parse

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Record:
    key: str
    owner: str  # server-derived hash, never a browser-declared owner
    blob: str
    kind: str
    size: int
    digest: str
    expires: float
    state: str = 'ready'


class PrivateBlobs(Protocol):
    def put(self, key: str, content: bytes, content_type: str) -> None: ...
    def read(self, key: str, max_bytes: int) -> tuple[bytes, str]:
        """Bounded private read; reject oversized streams without buffering all bytes."""
        ...
    def authorize_put(self, key: str, *, expires: float, size: int,
                      content_type: str, digest: str) -> str:
        """One-key write-only HTTPS authorization; enforce expiry, MIME, size/hash.

        Must not grant read/list, create permanent public URLs or expose credentials.
        """
        ...
    def authorize_get(self, key: str, *, expires: float, content_type: str,
                      filename: str) -> str:
        """Read-only HTTPS grant for this immutable private object and expiry.

        No listing, permanent public access or browser credentials. Enforce the
        signed content type/disposition and stop access on deletion/expiry.
        """
        ...
    def seal(self, key: str) -> None:
        """Revoke outstanding upload grants and freeze the uploaded version.

        Idempotent, including missing objects. Keep a deny-write tombstone until
        every issued grant expires so a late PUT cannot recreate deleted bytes.
        """
        ...
    def delete(self, key: str) -> None:
        """Idempotent, including for absent or incomplete uploads."""
        ...


class AtomicMetadata(Protocol):
    def read(self, key: str) -> Record | None: ...
    def create(self, record: Record, *, session_limit: int, total_limit: int) -> None:
        """Atomically reserve quota, reject collisions and publish a new record."""
        ...
    def swap(self, expected: Record, replacement: Record) -> None:
        """Serializable state CAS, retaining the same key/blob/owner/size.

        Compare the complete expected record and reject expired versions. Used
        for writing → ready and pending → finalizing, never to publish new bytes.
        """
        ...
    def promote(self, expected: Record, staged: Record, kind: str) -> None:
        """One transaction checks both records, consumes expected, and changes
        staged.kind to kind. Tombstone ONLY the old blob; preserve staged bytes.
        """
        ...
    def retire(self, expected: Record) -> None:
        """CAS deletion + durable blob-cleanup tombstone; retry cleanup after crashes."""
        ...
    def expired(self, now: float) -> list[Record]: ...
    def owned(self, owner_hash: str) -> list[Record]: ...
    def garbage(self) -> list[str]: ...
    def cleaned(self, blob: str) -> None: ...


class PrivateStorage:
    driver = 'object'
    def __init__(self, blobs: PrivateBlobs, metadata: AtomicMetadata, *, clock=time, ttl=TTL):
        self.blobs, self.metadata, self.clock, self.ttl = blobs, metadata, clock, ttl

    def _owner(self, owner):
        if not TOKEN.fullmatch(owner): raise ObjectUnavailable('Session is unavailable.')
        return sha256(owner.encode()).hexdigest()

    def _record(self, owner, reference, kind=None):
        row = self.metadata.read(reference.object_id)
        if (reference.driver != 'object' or row is None or row.owner != self._owner(owner)
                or row.expires <= self.clock() or (kind is not None and row.kind != kind)):
            raise ObjectUnavailable('Object is unavailable or expired in this session.')
        return row

    def _new(self, owner, kind, size, digest, state='ready'):
        if size < 0 or size > MAX_OBJECT: raise ObjectUnavailable('Object exceeds size limit.')
        return Record(token_urlsafe(32), self._owner(owner), token_urlsafe(32),
                      kind, size, digest, self.clock()+self.ttl, state)

    def _reserve(self, row):
        self.metadata.create(row, session_limit=MAX_SESSION, total_limit=MAX_TOTAL)

    def put(self, owner, content, kind):
        # Reserve before writing so a crashed write still has an expiring record.
        row = self._new(owner, kind, len(content), sha256(content).hexdigest(), 'writing')
        self._reserve(row)
        try:
            self.blobs.put(row.blob, content, 'application/octet-stream')
            self.metadata.swap(row, replace(row, state='ready'))
        except BaseException:
            self.metadata.retire(row); self._garbage(); raise
        return ObjectReference(object_id=row.key, driver='object')

    def get(self, owner, reference, kind):
        row = self._record(owner, reference, kind)
        if row.state != 'ready': raise ObjectUnavailable('Object is not finalized.')
        content, mime = self.blobs.read(row.blob, row.size)
        if (len(content) != row.size or sha256(content).hexdigest() != row.digest
                or mime != 'application/octet-stream'):
            raise ObjectUnavailable('Object integrity check failed.')
        return content

    def replace(self, owner, reference, content, kind):
        old = self._record(owner, reference, kind)
        if old.state != 'ready': raise ObjectUnavailable('Object is not finalized.')
        # Stage an unpublished replacement. Metadata CAS is the commit point;
        # failed writers retire their new blob and cannot resurrect an old token.
        staged = self.put(owner, content, 'replacement')
        row = self._record(owner, staged, 'replacement')
        try:
            self.metadata.promote(old, row, kind)
        except BaseException:
            self.metadata.retire(row); self._garbage(); raise
        self._garbage()
        return staged

    def delete(self, owner, reference):
        self.metadata.retire(self._record(owner, reference)); self._garbage()

    def reset(self, owner):
        for row in self.metadata.owned(self._owner(owner)):
            try: self.metadata.retire(row)
            except ObjectUnavailable: pass  # another writer already consumed it
        self._garbage()

    def authorize_download(self, owner, reference, kind):
        formats={'accepted_workbook':(MIME,'accepted.xlsx'),
                 'accepted_snapshot':('application/gzip','accepted.plan.json.gz')}
        if kind not in formats: raise ObjectUnavailable('Only accepted files support downloads.')
        row=self._record(owner,reference,kind)
        self.get(owner,reference,kind)  # verify bytes/hash, not only provider metadata
        self.blobs.seal(row.blob)
        mime,filename=formats[kind];expiry=min(row.expires,self.clock()+60)
        url=self.blobs.authorize_get(row.blob,expires=expiry,content_type=mime,filename=filename)
        if not url.startswith('https://'):raise ObjectUnavailable('Private download requires HTTPS.')
        return DownloadAuthorization(reference=reference,download_url=url,expires_at=expiry,
            content_type=mime,bytes=row.size,sha256=row.digest)

    def authorize_upload(self, owner, *, size, content_type, digest):
        if content_type != MIME or not 0 < size <= MAX_FILE or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ObjectUnavailable('Unsupported workbook type, size or integrity hash.')
        row = self._new(owner, 'upload', size, digest, 'pending')
        row = replace(row, expires=min(row.expires, self.clock()+300))
        self._reserve(row)
        try:
            url = self.blobs.authorize_put(row.blob, expires=row.expires, size=size,
                                          content_type=MIME, digest=digest)
            if not url.startswith('https://'): raise ObjectUnavailable('Private upload requires HTTPS.')
        except BaseException:
            self.metadata.retire(row); self._garbage(); raise
        return UploadAuthorization(reference=ObjectReference(object_id=row.key,driver='object'),
            upload_url=url, expires_at=row.expires, max_bytes=size, content_type=MIME)

    def finalize_upload(self, owner, reference):
        pending = self._record(owner, reference, 'upload')
        if pending.state != 'pending': raise ObjectUnavailable('Upload is not pending.')
        claimed = replace(pending, state='finalizing')
        self.metadata.swap(pending, claimed)
        try:
            self.blobs.seal(claimed.blob)
            content, mime = self.blobs.read(claimed.blob, claimed.size)
            if mime != MIME or len(content) != claimed.size or sha256(content).hexdigest() != claimed.digest:
                raise ObjectUnavailable('Uploaded workbook integrity check failed.')
            # Parse centrally: MIME is insufficient. Includes XLSX structure,
            # archive expansion, cell/formula/row limits and dataset validation.
            return parse(content, 'data.xlsx')
        finally:
            self.metadata.retire(claimed); self._garbage()

    def _garbage(self, *, strict=False):
        # Metadata is already committed. Cleanup must never hide its returned
        # reference or undo the transition; failed work stays durably queued.
        failures = 0
        try:
            pending = self.metadata.garbage()
        except Exception:
            pending = []
            failures += 1
        for blob in pending:
            try:
                self.blobs.seal(blob)
                self.blobs.delete(blob)
                self.metadata.cleaned(blob)
            except Exception:
                failures += 1
        if failures:
            # Bounded operational evidence, without provider messages or IDs.
            logger.warning('private_cleanup_deferred failures=%d', failures)
            if strict:
                raise OSError('Private object cleanup remains queued.')

    def sweep(self):
        for row in self.metadata.expired(self.clock()):
            try: self.metadata.retire(row)
            except ObjectUnavailable: pass
        self._garbage(strict=True)
