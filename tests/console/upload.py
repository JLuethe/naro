"""Bounded, atomic executable uploads inside the disposable guest root."""
import base64
import hashlib
import os
import re
from pathlib import Path

MAX_SIZE = 64 * 1024 * 1024
CHUNK_SIZE = 64 * 1024


class Upload:
    def __init__(self, root):
        self.root = Path(root)
        self.pending = None

    def abort(self):
        if self.pending is not None:
            self.pending['file'].close()
            self.pending['path'].unlink(missing_ok=True)
            self.pending = None

    def begin(self, name, size, sha256):
        self.abort()
        if name not in ('reference', 'candidate'):
            raise ValueError('binary name')
        if type(size) is not int or not 0 < size <= MAX_SIZE:
            raise ValueError('upload size')
        if not isinstance(sha256, str) or not re.fullmatch('[0-9a-f]{64}', sha256):
            raise ValueError('upload digest')
        path = self.root / ('.' + name + '.upload')
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        self.pending = dict(path=path, file=os.fdopen(fd, 'wb'), name=name,
                            size=size, sha256=sha256, offset=0, digest=hashlib.sha256())
        return {'offset': 0}

    def chunk(self, offset, encoded):
        p = self.pending
        try:
            if p is None or type(offset) is not int or offset != p['offset']:
                raise ValueError('upload offset')
            if not isinstance(encoded, str) or len(encoded) > 4 * ((CHUNK_SIZE + 2) // 3):
                raise ValueError('upload chunk size')
            raw = base64.b64decode(encoded, validate=True)
            if not 0 < len(raw) <= CHUNK_SIZE or offset + len(raw) > p['size']:
                raise ValueError('upload chunk size')
            p['file'].write(raw)
            p['digest'].update(raw)
            p['offset'] += len(raw)
            return {'offset': p['offset']}
        except Exception:
            self.abort()
            raise

    def finish(self):
        p = self.pending
        try:
            if p is None or p['offset'] != p['size']:
                raise ValueError('upload incomplete')
            digest = p['digest'].hexdigest()
            if digest != p['sha256']:
                raise ValueError('upload digest mismatch')
            p['file'].flush()
            os.fsync(p['file'].fileno())
            p['file'].close()
            p['path'].chmod(0o755)
            p['path'].replace(self.root / p['name'])
            self.pending = None
            return {'sha256': digest, 'size': p['size']}
        except Exception:
            self.abort()
            raise
