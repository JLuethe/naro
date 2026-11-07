#!/usr/bin/env python3
"""Failure-path evidence check for the direct PTY runner."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from backlog import run_case


class BacklogTraceTest(unittest.TestCase):
    def test_failed_editor_retains_complete_raw_trace(self):
        with tempfile.TemporaryDirectory(prefix="issue14-pty-failure-") as temp:
            root = Path(temp)
            editor = root / "editor"
            editor.write_text("#!/bin/sh\nprintf 'EARLY-EXIT-TRACE\\n'\nexit 7\n")
            editor.chmod(0o700)
            source = root / "source.txt"
            source.write_text("fixture\n")
            raw_path = root / "failure.raw"
            result = run_case(editor, source, root, 0, 1.0, raw_path)
            raw = raw_path.read_bytes()
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["teardown"], "already_exited_after_failure")
            self.assertTrue(result["raw_complete"])
            self.assertIn(b"EARLY-EXIT-TRACE", raw)
            self.assertEqual(result["raw_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(result["raw_bytes"], len(raw))
            self.assertIn("pty_eof", [event["name"] for event in result["events"]])


if __name__ == "__main__":
    unittest.main()
