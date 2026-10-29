#!/usr/bin/env python3
"""Regression tests for the wrap-undo evidence checker.

The checker must fail closed: a report that claims completeness but
records zero matches, failed per-side assertions, a wrong reference, a
wrong candidate or wrong scenario inputs has to be rejected. These tests
build a valid report and then break one property at a time.
"""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import check_wrap_undo as checker  # noqa: E402


def valid_report():
    cases = json.loads(checker.SUITE.read_text())
    hashes = checker.scenario_hashes(cases)
    results = {}
    for tid in checker.EXPECTED_IDS:
        results[tid] = {
            "match": True,
            "declared_deviation": False,
            "deviation_id": None,
            "accepted": True,
            "reference_checks": True,
            "candidate_checks": True,
            "differences": [],
        }
    return {
        "environment": {},
        "build_flags": "default",
        "reference_commit": checker.REFERENCE_COMMIT,
        "reference_sha256": checker.REFERENCE_SHA256,
        "candidate_sha256": "a" * 64,
        "reference_status": 0,
        "candidate_status": 0,
        "scenario_sha256": hashes["runner"],
        "candidate_build": {
            "reference_commit": checker.REFERENCE_COMMIT,
            "source_sha256": checker.source_fingerprint(),
            "features": "",
        },
        "results": results,
        "summary": {
            "recorded": len(checker.EXPECTED_IDS),
            "matches": len(checker.EXPECTED_IDS),
            "accepted": len(checker.EXPECTED_IDS),
        },
    }


class WrapUndoCheckerTest(unittest.TestCase):
    def setUp(self):
        self.report = valid_report()
        self.hashes = checker.scenario_hashes(json.loads(checker.SUITE.read_text()))

    def problems(self, report=None):
        return checker.report_problems(
            report if report is not None else self.report,
            self.hashes,
            checker.source_fingerprint(),
        )

    def test_valid_report_is_accepted(self):
        self.assertEqual(self.problems(), [])

    def test_manifest_has_no_problems(self):
        cases = json.loads(checker.SUITE.read_text())
        self.assertEqual(checker.manifest_problems(cases), [])

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


if __name__ == "__main__":
    unittest.main()
