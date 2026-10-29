#!/usr/bin/env python3
"""Regression tests for the wrap-undo evidence checker.

The checker must fail closed: a report that claims completeness but
records zero matches, failed per-side assertions, a wrong reference, a
wrong candidate or wrong scenario inputs has to be rejected. These tests
build a valid report and then break one property at a time.
"""
import copy
import base64
import tempfile
import json
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import check_wrap_undo as checker  # noqa: E402


def valid_artifacts(directory, cases):
    """Small complete evidence fixture; no reference installation or replay needed."""
    ref, cand = b"reference fixture", b"candidate fixture"
    for name, data in (("reference.bin", ref), ("candidate.bin", cand)):
        (directory / name).write_bytes(data)
    for name in ("scenarios.json", "reference-scenarios.json", "candidate-scenarios.json"):
        (directory / name).write_text(json.dumps(cases, indent=1) + "\n")
    report = {
        "reference_commit": checker.REFERENCE_COMMIT,
        "reference_sha256": checker.sha256(ref),
        "candidate_sha256": checker.sha256(cand),
        "verification_sha256": checker.verification_fingerprint(),
        "reference_status": 0, "candidate_status": 0,
        "scenario_sha256": checker.scenario_hashes(cases)["runner"],
        "candidate_build": {"reference_commit": checker.REFERENCE_COMMIT,
                            "source_sha256": checker.source_fingerprint(), "features": ""},
        "results": {},
        "summary": dict.fromkeys(("recorded", "matches", "accepted"), len(cases)),
    }
    screen = {"rows": [{"text": "ok", "attrs": []}],
              "cursor": {"x": 2, "y": 0, "visible": True}, "modes": {}}
    def entry(raw):
        return {"type": "file", "mode": "0o644", "nlink": 1, "size": len(raw),
                "sha256": checker.sha256(raw), "b64": base64.b64encode(raw).decode()}
    for case in cases:
        tid = case["id"]
        for side in ("reference", "candidate"):
            d = directory / side / tid
            d.mkdir(parents=True)
            raw = b"terminal trace"
            (d / "raw-output.bin").write_bytes(raw)
            run = {
                "scenario": tid, "reference_commit": checker.REFERENCE_COMMIT,
                "binary_sha256": report[side + "_sha256"],
                "scenario_sha256": checker.sha256(json.dumps(
                    case, sort_keys=True, separators=(",", ":")).encode()),
                "cwd": "/tmp/fixture/fx/work", "env": {}, "notes": [],
                "fixture": {"work/f.txt": entry(b"ok\n")},
                "initial_fixture": {"work/f.txt": entry(b"\n")},
                "temp_files": {}, "captured_files": {"work/f.txt": ["b2sK"]},
                "inputs": [{"hex": "6f6b"}], "snapshots": {"edited": screen},
                "after_exit_screen": screen, "trace_final_modes": {},
                "helper_statuses": [], "exit_status": 0, "exit_signal": None,
                "stderr": "", "steps_ok": True,
                "step_checks": [{"step": i, "pass": True} for i in range(len(case["steps"]))],
                "raw_output_sha256": checker.sha256(raw), "raw_output_bytes": len(raw),
            }
            runner = checker.Run(case, "unused", "unused")
            runner.root = "/tmp/fixture/fx"
            run["checks"] = runner.check(run)
            (d / "result.json").write_text(json.dumps(run))
        report["results"][tid] = {"match": True, "accepted": True,
                                  "reference_checks": True, "candidate_checks": True,
                                  "differences": [], "declared_deviation": False,
                                  "deviation_id": None}
    return report


class WrapUndoCheckerTest(unittest.TestCase):
    def setUp(self):
        self.real_cases = json.loads(checker.SUITE.read_text())
        self.real_ids = checker.EXPECTED_IDS
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        cases = [{"id": f"TEST-NEXT-UNDO-WRAP-{n:03}-FIXTURE",
                  "files": {"work/f.txt": {"hex": "0a"}},
                  "steps": [{"text": "ok"}, {"snapshot": "edited"},
                            {"capture_file": "work/f.txt"}, {"wait_exit": 5}],
                  "expect": {"exit_status": 0, "temp_empty": True,
                             "files": {"work/f.txt": {"hex": "6f6b0a"}}},
                  "note": "Synthetic evidence validator fixture"} for n in (1, 2)]
        suite = self.directory / "suite.json"
        suite.write_text(json.dumps(cases))
        for name, value in (("SUITE", suite), ("EXPECTED_IDS", [c["id"] for c in cases]),
                            ("REFERENCE_SHA256", checker.sha256(b"reference fixture"))):
            patcher = patch.object(checker, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.report = valid_artifacts(self.directory, cases)
        self.hashes = checker.scenario_hashes(cases)

    def problems(self, report=None):
        return checker.report_problems(
            report if report is not None else self.report,
            self.hashes, checker.source_fingerprint(), self.directory,
        )

    def recording(self, change, side="candidate"):
        path = self.directory / side / checker.EXPECTED_IDS[0] / "result.json"
        run = json.loads(path.read_text())
        change(run)
        path.write_text(json.dumps(run))

    def test_valid_report_is_accepted(self):
        self.assertEqual(self.problems(), [])

    def test_manifest_has_no_problems(self):
        with patch.object(checker, "EXPECTED_IDS", self.real_ids):
            self.assertEqual(checker.manifest_problems(self.real_cases), [])

    def test_zero_matches_are_rejected(self):
        report = copy.deepcopy(self.report)
        report["summary"]["matches"] = 0
        report["summary"]["accepted"] = 0
        for value in report["results"].values():
            value["match"] = False
            value["accepted"] = False
            value["reference_checks"] = False
            value["candidate_checks"] = False
        problems = self.problems(report)
        self.assertTrue(problems)
        self.assertTrue(any("not an exact match" in p for p in problems))
        self.assertTrue(any("summary matches" in p for p in problems))

    def test_failed_side_checks_are_rejected(self):
        report = copy.deepcopy(self.report)
        first = sorted(report["results"])[0]
        report["results"][first]["reference_checks"] = False
        report["results"][first]["candidate_checks"] = False
        problems = self.problems(report)
        self.assertTrue(any("checks did not pass" in p for p in problems))

    def test_wrong_reference_commit_is_rejected(self):
        report = copy.deepcopy(self.report)
        report["reference_commit"] = "wrong-reference"
        self.assertTrue(self.problems(report))

    def test_wrong_reference_binary_is_rejected(self):
        report = copy.deepcopy(self.report)
        report["reference_sha256"] = "0" * 64
        self.assertTrue(any("pinned" in p for p in self.problems(report)))

    def test_wrong_candidate_binary_is_rejected(self):
        report = copy.deepcopy(self.report)
        report["candidate_sha256"] = "not-a-digest"
        self.assertTrue(self.problems(report))

    def test_wrong_scenario_hash_is_rejected(self):
        report = copy.deepcopy(self.report)
        report["scenario_sha256"] = "0" * 64
        self.assertTrue(any("scenario_sha256" in p for p in self.problems(report)))

    def test_stale_candidate_source_is_rejected(self):
        report = copy.deepcopy(self.report)
        report["candidate_build"]["source_sha256"] = "0" * 64
        self.assertTrue(any("source fingerprint" in p for p in self.problems(report)))

    def test_nondefault_candidate_features_are_rejected(self):
        report = copy.deepcopy(self.report)
        report["candidate_build"]["features"] = "tiny"
        self.assertTrue(any("default profile" in p for p in self.problems(report)))

    def test_nonzero_harness_status_is_rejected(self):
        report = copy.deepcopy(self.report)
        report["candidate_status"] = 1
        self.assertTrue(any("candidate_status" in p for p in self.problems(report)))

    def test_missing_and_extra_results_are_rejected(self):
        report = copy.deepcopy(self.report)
        dropped = sorted(report["results"])[0]
        del report["results"][dropped]
        report["results"]["TEST-NEXT-UNDO-WRAP-999-GHOST"] = {
            "match": True,
            "declared_deviation": False,
            "deviation_id": None,
            "accepted": True,
            "reference_checks": True,
            "candidate_checks": True,
            "differences": [],
        }
        problems = self.problems(report)
        self.assertTrue(any("missing recordings" in p for p in problems))
        self.assertTrue(any("unexpected recordings" in p for p in problems))

    def test_recorded_differences_are_rejected(self):
        report = copy.deepcopy(self.report)
        first = sorted(report["results"])[0]
        report["results"][first]["differences"] = [{"field": "fixture"}]
        self.assertTrue(any("difference" in p for p in self.problems(report)))

    def test_declared_deviation_is_rejected(self):
        report = copy.deepcopy(self.report)
        first = sorted(report["results"])[0]
        report["results"][first]["declared_deviation"] = True
        report["results"][first]["deviation_id"] = "TEST-NEXT-X"
        problems = self.problems(report)
        self.assertTrue(any("deviation" in p for p in problems))

    def test_inconsistent_summary_is_rejected(self):
        report = copy.deepcopy(self.report)
        report["summary"]["recorded"] = 0
        self.assertTrue(any("summary recorded" in p for p in self.problems(report)))

    def test_missing_candidate_build_is_rejected(self):
        report = copy.deepcopy(self.report)
        del report["candidate_build"]
        self.assertTrue(self.problems(report))

    def test_malformed_manifest_is_rejected(self):
        cases = json.loads(checker.SUITE.read_text())
        cases[0]["id"] = "TEST-NEXT-UNDO-WRAP-001-DUP"
        self.assertTrue(checker.manifest_problems(cases))

    def test_manifest_rejects_a_removed_case(self):
        cases = json.loads(checker.SUITE.read_text())
        cases.pop()
        self.assertTrue(checker.manifest_problems(cases))

    def test_manifest_rejects_a_duplicated_case(self):
        cases = json.loads(checker.SUITE.read_text())
        cases.append(copy.deepcopy(cases[0]))
        self.assertTrue(checker.manifest_problems(cases))

    def test_manifest_rejects_a_tampered_fixture(self):
        cases = json.loads(checker.SUITE.read_text())
        cases[0]["files"]["work/f.txt"]["hex"] = "nothex"
        self.assertTrue(checker.manifest_problems(cases))

    def test_source_fingerprint_matches_the_build_convention(self):
        fingerprint = checker.source_fingerprint()
        self.assertIsNotNone(fingerprint)
        self.assertEqual(len(fingerprint), 64)

    def test_standalone_report_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            problems = checker.report_problems(self.report, self.hashes,
                                               checker.source_fingerprint(), Path(d))
        self.assertTrue(any("required executable" in p for p in problems))

    def test_missing_evidence_directory_is_rejected(self):
        self.assertTrue(checker.report_problems(self.report, self.hashes,
                                               checker.source_fingerprint()))

    def test_each_required_artifact_is_required(self):
        tid = checker.EXPECTED_IDS[0]
        names = ["candidate.bin", "reference.bin", "scenarios.json",
                 "candidate-scenarios.json", "reference-scenarios.json",
                 f"candidate/{tid}/result.json", f"reference/{tid}/result.json",
                 f"candidate/{tid}/raw-output.bin"]
        for name in names:
            with self.subTest(name=name):
                path = self.directory / name
                raw = path.read_bytes()
                path.unlink()
                self.assertTrue(self.problems())
                path.write_bytes(raw)

    def test_well_formed_wrong_candidate_hash_is_rejected(self):
        self.report["candidate_sha256"] = "a" * 64
        self.assertTrue(any("hash mismatch" in p for p in self.problems()))

    def test_missing_features_are_rejected(self):
        del self.report["candidate_build"]["features"]
        self.assertTrue(any("default profile" in p for p in self.problems()))

    def test_unavailable_source_fingerprint_is_rejected(self):
        self.assertTrue(any("cannot compute" in p for p in checker.report_problems(
            self.report, self.hashes, None, self.directory)))

    def test_wrong_tool_identity_is_rejected(self):
        self.report["verification_sha256"] = "0" * 64
        self.assertTrue(any("tools fingerprint" in p for p in self.problems()))

    def test_frozen_scenario_tampering_is_rejected(self):
        path = self.directory / "scenarios.json"
        cases = json.loads(path.read_text())
        cases[0]["steps"][0]["text"] = "tampered"
        path.write_text(json.dumps(cases))
        self.assertTrue(any("scenario" in p for p in self.problems()))

    def test_side_scenario_tampering_is_rejected(self):
        (self.directory / "candidate-scenarios.json").write_text("[]")
        self.assertTrue(any("candidate-scenarios" in p for p in self.problems()))

    def test_per_case_identity_is_checked(self):
        for key in ("binary_sha256", "scenario_sha256", "scenario", "reference_commit"):
            with self.subTest(key=key):
                path = self.directory / "candidate" / checker.EXPECTED_IDS[0] / "result.json"
                raw = path.read_bytes()
                self.recording(lambda r: r.update({key: "wrong"}))
                self.assertTrue(any("identity mismatch" in p for p in self.problems()))
                path.write_bytes(raw)

    def test_nested_failed_assertions_are_not_hidden_by_report(self):
        self.recording(lambda r: r["checks"][0].update({"pass": False}))
        self.assertTrue(any("recorded checks" in p for p in self.problems()))

    def test_false_nested_pass_flags_are_recomputed(self):
        self.recording(lambda r: r.update(exit_status=99))
        self.assertTrue(any("recomputed expectations failed" in p for p in self.problems()))

    def test_missing_and_failed_steps_are_rejected(self):
        self.recording(lambda r: r.update(step_checks=[]))
        self.assertTrue(any("step checks" in p for p in self.problems()))

    def test_changed_snapshot_is_recompared(self):
        self.recording(lambda r: r["snapshots"]["edited"]["rows"][0].update(text="changed"))
        self.assertTrue(any("recomputed comparison" in p for p in self.problems()))

    def test_snapshot_omission_on_both_sides_is_rejected(self):
        for side in ("reference", "candidate"):
            self.recording(lambda r: r.update(snapshots={}), side)
        self.assertTrue(any("snapshot membership" in p for p in self.problems()))

    def test_corrupt_inline_file_metadata_is_rejected(self):
        self.recording(lambda r: r["fixture"]["work/f.txt"].update(b64=""))
        self.assertTrue(any("byte metadata mismatch" in p for p in self.problems()))

    def test_raw_trace_tampering_is_rejected(self):
        (self.directory / "candidate" / checker.EXPECTED_IDS[0] / "raw-output.bin").write_bytes(b"wrong")
        self.assertTrue(any("raw-output.bin hash" in p for p in self.problems()))

    def test_malformed_recording_is_rejected(self):
        self.recording(lambda r: r.update(fixture=None))
        self.assertTrue(self.problems())

    def test_status_booleans_are_rejected(self):
        self.report["candidate_status"] = False
        self.assertTrue(self.problems())

    def test_bad_manifest_field_types_fail_cleanly(self):
        cases = json.loads(checker.SUITE.read_text())
        for key, value in (("id", []), ("files", []), ("expect", None), ("steps", {})):
            with self.subTest(key=key):
                bad = copy.deepcopy(cases)
                bad[0][key] = value
                self.assertTrue(checker.manifest_problems(bad))

    def test_missing_deviation_flag_is_rejected(self):
        del self.report["results"][checker.EXPECTED_IDS[0]]["declared_deviation"]
        self.assertTrue(self.problems())

    def test_identical_wrong_inputs_on_both_sides_are_rejected(self):
        for side in ("reference", "candidate"):
            self.recording(lambda r: r.update(inputs=[{"hex": "bad"}]), side)
        self.assertTrue(any("input bytes/order" in p for p in self.problems()))


if __name__ == "__main__":
    unittest.main()
