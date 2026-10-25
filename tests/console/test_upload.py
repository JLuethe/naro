"""Exercise upload failure atomicity using only harness-owned temporary files."""
import base64
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from upload import Upload, CHUNK_SIZE, MAX_SIZE


class UploadTests(unittest.TestCase):
    def setUp(self):
        base = Path(os.environ.get('NANOSPEC_WORK', '/tmp/nanospec-work'))
        base.mkdir(parents=True, exist_ok=True)
        self.work = tempfile.TemporaryDirectory(prefix='TEST-VT-UPLOAD-', dir=base)
        self.root = Path(self.work.name) / 'fx'
        self.root.mkdir()
        self.binary = self.root / 'candidate'
        self.binary.write_bytes(b'old executable')
        self.upload = Upload(self.root)
        self.raw = b'new executable' * 10000

    def tearDown(self):
        self.upload.abort()
        self.work.cleanup()

    def begin(self, digest=None):
        return self.upload.begin('candidate', len(self.raw), digest or hashlib.sha256(self.raw).hexdigest())

    def send(self):
        for offset in range(0, len(self.raw), CHUNK_SIZE):
            part = self.raw[offset:offset + CHUNK_SIZE]
            self.assertEqual(self.upload.chunk(offset, base64.b64encode(part).decode()), {'offset': offset + len(part)})

    def test_success_replaces_only_after_verified_finish(self):
        self.begin(); self.send()
        self.assertEqual(self.binary.read_bytes(), b'old executable')
        self.assertEqual(self.upload.finish()['sha256'], hashlib.sha256(self.raw).hexdigest())
        self.assertEqual(self.binary.read_bytes(), self.raw)
        self.assertEqual(self.binary.stat().st_mode & 0o777, 0o755)

    def test_wrong_digest_preserves_binary(self):
        self.begin('0' * 64); self.send()
        with self.assertRaises(ValueError): self.upload.finish()
        self.assertEqual(self.binary.read_bytes(), b'old executable')
        self.assertIsNone(self.upload.pending)

    def test_incomplete_upload_preserves_binary(self):
        self.begin()
        with self.assertRaises(ValueError): self.upload.finish()
        self.assertEqual(self.binary.read_bytes(), b'old executable')

    def test_bad_chunks_abort_without_replacing(self):
        for offset, data in [(1, 'YQ=='), (0, '!'), (0, base64.b64encode(b'x' * (CHUNK_SIZE + 1)).decode())]:
            self.begin()
            with self.assertRaises(ValueError): self.upload.chunk(offset, data)
            self.assertIsNone(self.upload.pending)
            self.assertEqual(self.binary.read_bytes(), b'old executable')

    def test_abort_then_restart(self):
        self.begin(); self.upload.chunk(0, 'YQ=='); self.upload.abort()
        self.assertFalse(list(self.root.glob('.*.upload')))
        self.begin(); self.send(); self.upload.finish()
        self.assertEqual(self.binary.read_bytes(), self.raw)

    def test_invalid_begin(self):
        for name, size, digest in [('other', 1, '0'*64), ('candidate', 0, '0'*64), ('candidate', MAX_SIZE+1, '0'*64), ('candidate', 1, 'bad')]:
            with self.assertRaises(ValueError): self.upload.begin(name, size, digest)
            self.assertEqual(self.binary.read_bytes(), b'old executable')

if __name__ == '__main__': unittest.main()
