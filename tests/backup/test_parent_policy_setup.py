#!/usr/bin/env python3
"""Check ACL fixture error classification in both issue-12 policy runners."""
import errno
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


TESTS = Path(__file__).resolve().parents[1]


def load_policy(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


POLICIES = (
    load_policy("backup_parent_policy", TESTS / "backup/parent_policy.py"),
    load_policy("confinement_parent_policy", TESTS / "confinement/parent_policy.py"),
)


class ParentPolicySetupTests(unittest.TestCase):
    def test_foreign_fixture_is_created_by_actor_without_chown(self):
        policy = POLICIES[0]
        with tempfile.TemporaryDirectory() as temp:
            data = Path(temp)
            target = data / "target"
            calls = []
            def fake_run(*args, **kwargs):
                calls.append((args, kwargs))
                self.assertEqual(data.stat().st_mode & 0o777, 0o777)
                target.write_bytes(policy.OLD)
                return type("Result", (), {"returncode": 0, "stderr": ""})()
            with mock.patch.object(policy.subprocess, "run", side_effect=fake_run), \
                 mock.patch.object(policy.os, "chown", side_effect=AssertionError("chown used")):
                policy.create_foreign_target(data, target, data.stat().st_uid)
            self.assertEqual(len(calls), 1)
            self.assertEqual(data.stat().st_mode & 0o777, 0o755)

    def test_distinct_actor_uses_an_id_mapped_in_both_tables(self):
        policy = POLICIES[0]
        self.assertEqual(policy.select_distinct_id("0 1000 1\n100000 100000 65536\n",
                                                   "0 1000 1\n100000 100000 65536\n"), 100000)
        self.assertEqual(policy.select_distinct_id("0 1000 1\n1 100000 65536\n",
                                                   "0 1000 1\n1 100000 65536\n"), 1)
        with self.assertRaises(policy.PrerequisiteError):
            policy.select_distinct_id("0 1000 1\n1 100000 10\n",
                                      "0 1000 1\n20 100000 10\n")

    def test_uid_mapping_is_conservative_when_unknown(self):
        for policy in POLICIES:
            with self.subTest(policy=policy.__name__):
                with mock.patch.object(policy, "Path") as path:
                    path.return_value.read_text.return_value = "0 1000 1\n"
                    self.assertFalse(policy.named_uid_mapped(100000))
                    path.return_value.read_text.return_value = "0 1000 1\n100000 100000 65536\n"
                    self.assertTrue(policy.named_uid_mapped(100000))
                    path.return_value.read_text.return_value = "invalid\n"
                    self.assertTrue(policy.named_uid_mapped(100000))

    def test_only_setup_prerequisites_are_reclassified(self):
        for policy in POLICIES:
            for number, mapped, prerequisite in (
                (errno.EINVAL, False, True),
                (errno.EINVAL, True, False),
                (errno.ENOTSUP, True, True),
                (errno.EIO, False, False),
            ):
                with self.subTest(policy=policy.__name__, errno=number, mapped=mapped):
                    fault = OSError(number, "synthetic ACL setup fault")
                    with mock.patch.object(policy.os, "setxattr", side_effect=fault), \
                         mock.patch.object(policy, "named_uid_mapped", return_value=mapped):
                        if prerequisite:
                            with self.assertRaises(policy.PrerequisiteError) as caught:
                                policy.set_named_writer_acl(Path("unused"), 100000)
                            self.assertIs(caught.exception.__cause__, fault)
                            self.assertIn(f"Errno {number}", str(caught.exception))
                        else:
                            with self.assertRaises(OSError) as caught:
                                policy.set_named_writer_acl(Path("unused"), 100000)
                            self.assertIs(caught.exception, fault)

    def test_missing_prerequisite_still_exits_failure(self):
        for policy in POLICIES:
            with self.subTest(policy=policy.__name__), tempfile.TemporaryDirectory() as temp:
                output = Path(temp) / "report"
                binary = Path(policy.__file__).resolve()
                with mock.patch.object(policy.sys, "argv", [policy.__file__, "--binary", str(binary),
                                                            "--out", str(output), "--only", "acl-writer"]), \
                     mock.patch.object(policy.subprocess, "run"), \
                     mock.patch.object(policy, "run_case",
                                       side_effect=policy.PrerequisiteError("[Errno 22] fixture setup")):
                    self.assertEqual(policy.main(), 1)
                row = json.loads((output / "report.json").read_text())["cases"][0]
                self.assertEqual(row["status"], "missing-prerequisite")
                self.assertIn("Errno 22", row["error"])


if __name__ == "__main__":
    unittest.main()
