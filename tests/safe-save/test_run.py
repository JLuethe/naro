"""Fail-closed accounting for the real safe-save fault runner."""
import contextlib
import errno
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


PATH = Path(__file__).with_name("run.py")
SPEC = importlib.util.spec_from_file_location("safe_save_run", PATH)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class FaultMatrixAccountingTests(unittest.TestCase):
    def invoke(self, directory, groups, *, regression_only=False, case_result=None):
        binary = directory / "fake-test-executable"
        binary.write_bytes(b"synthetic executable identity")
        out = directory / ("regression" if regression_only else "full")
        argv = [str(PATH), "--binary", str(binary), "--out", str(out)]
        if regression_only:
            argv.append("--regression-only")
        with (mock.patch.object(sys, "argv", argv),
              mock.patch.object(RUNNER.os, "getgroups", return_value=groups),
              mock.patch.object(RUNNER.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)),
              mock.patch.object(RUNNER, "run_case", side_effect=case_result) as cases,
              contextlib.redirect_stdout(io.StringIO())):
            status = RUNNER.main()
        return status, json.loads((out / "report.json").read_text()), cases.call_count

    def test_missing_supplementary_group_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            status, report, calls = self.invoke(Path(directory), [os.getgid()],
                                                case_result=lambda *args: {"result": "ok"})
        self.assertEqual(status, 1)
        self.assertTrue(report["complete"])
        self.assertEqual((report["expected"], report["total"], report["passed"],
                          report["missing_prerequisites"], calls), (659, 659, 565, 94, 565))
        self.assertEqual(len(report["skips"]), 94)
        self.assertTrue(all(r["kind"] == "group" and r["status"] == "missing-prerequisite"
                            for r in report["skips"]))

    def test_full_matrix_passes_only_when_every_case_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            status, report, calls = self.invoke(Path(directory), [os.getgid(), os.getgid() + 1000],
                                                case_result=lambda *args: {"result": "ok"})
        self.assertEqual(status, 0)
        self.assertEqual((report["expected"], report["total"], report["passed"],
                          report["missing_prerequisites"], calls), (659, 659, 659, 0, 659))

    def test_product_einval_is_failure_not_prerequisite(self):
        with tempfile.TemporaryDirectory() as directory:
            status, report, calls = self.invoke(Path(directory), [os.getgid()], regression_only=True,
                                                case_result=OSError(errno.EINVAL, "product fault"))
        self.assertEqual(status, 1)
        self.assertEqual((report["expected"], report["total"], report["passed"], calls), (3, 3, 0, 3))
        self.assertEqual({r["status"] for r in report["cases"]}, {"fail"})

    def test_fixture_setup_failure_is_reported_and_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            status, report, calls = self.invoke(
                Path(directory), [os.getgid()], regression_only=True,
                case_result=RUNNER.MissingFixturePrerequisite("default ACL setup: EINVAL"))
        self.assertEqual(status, 1)
        self.assertEqual((report["expected"], report["total"], report["passed"],
                          report["missing_prerequisites"], calls), (3, 3, 0, 3, 3))
        self.assertEqual({r["status"] for r in report["cases"]}, {"missing-prerequisite"})

    def test_only_fixture_setup_einval_is_missing_prerequisite(self):
        def setup_failure(*args):
            raise OSError(errno.EINVAL, "fixture ACL unsupported")

        with self.assertRaises(RUNNER.MissingFixturePrerequisite):
            RUNNER.fixture_metadata("access ACL setup", setup_failure)
        with self.assertRaises(OSError) as caught:
            RUNNER.fixture_metadata("access ACL setup", lambda: (_ for _ in ()).throw(
                OSError(errno.EIO, "I/O failure")))
        self.assertEqual(caught.exception.errno, errno.EIO)

    def test_acl_and_group_setup_einval_are_classified_before_editor_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (mock.patch.object(RUNNER.os, "setxattr", side_effect=OSError(errno.EINVAL, "ACL fixture")),
                  mock.patch.object(RUNNER.subprocess, "run") as editor):
                with self.assertRaisesRegex(RUNNER.MissingFixturePrerequisite, "default ACL setup"):
                    RUNNER.run_case(root / "unused", root / "unused.so", root / "default-acl", 0,
                                    "none", "new-default-acl")
                with self.assertRaisesRegex(RUNNER.MissingFixturePrerequisite, "access ACL setup"):
                    RUNNER.run_case(root / "unused", root / "unused.so", root / "access-acl", 0,
                                    "none", "acl")
                editor.assert_not_called()
            with (mock.patch.object(RUNNER.os, "getgroups", return_value=[os.getgid() + 1000]),
                  mock.patch.object(RUNNER.os, "chown", side_effect=OSError(errno.EINVAL, "group fixture")),
                  mock.patch.object(RUNNER.subprocess, "run") as editor):
                with self.assertRaisesRegex(RUNNER.MissingFixturePrerequisite, "supplementary group setup"):
                    RUNNER.run_case(root / "unused", root / "unused.so", root / "group", 0,
                                    "none", "group")
                editor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
