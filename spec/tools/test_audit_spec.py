#!/usr/bin/env python3
"""Fixture tests for the specification audit's test-ID extraction.

The audit turns the citations of a requirement block into the inventory in
`data/requirements.csv`. A citation that names a family of cases (a glob or
a path prefix) is not a case ID, and the inventory may only list cases that
exist: a citation of a planned case or of a range endpoint is resolved
against the recorded inventory and reported as a warning instead.
"""
import csv
import json
import sys
import unittest
from pathlib import Path

SPEC = Path(__file__).resolve().parents[1]
ROOT = SPEC.parent
sys.path.insert(0, str(SPEC / "tools"))

import audit_spec  # noqa: E402


def recorded_ids():
    ids = set()
    for path in sorted((SPEC / "evidence/scenarios").glob("*.json")):
        data = json.loads(path.read_text())
        for scenario in (data if isinstance(data, list) else [data]):
            ids.add(scenario["id"])
    follow_up = ROOT / "tests/follow-up/scenarios"
    if follow_up.is_dir():
        for path in sorted(follow_up.glob("*.json")):
            data = json.loads(path.read_text())
            for scenario in (data if isinstance(data, list) else [data]):
                ids.add(scenario["id"])
    for name in ("follow-up-tests.csv", "root-console-tests.csv",
                 "closure-tests.csv", "tiny-tests.csv"):
        path = SPEC / "data" / name
        if not path.exists():
            continue
        with path.open(newline="") as f:
            for row in csv.DictReader(f):
                ids.add(row["test_id"])
    return ids


class CitedTestIdsTest(unittest.TestCase):
    def test_case_id_with_a_suffix_is_captured(self):
        self.assertEqual(
            audit_spec.cited_test_ids("case TEST-NEXT-UNDO-WRAP-001-MID here"),
            ["TEST-NEXT-UNDO-WRAP-001-MID"],
        )

    def test_several_ids_are_captured_in_order(self):
        self.assertEqual(
            audit_spec.cited_test_ids("TEST-UNDO-001, TEST-UNDO-002."),
            ["TEST-UNDO-001", "TEST-UNDO-002"],
        )

    def test_glob_citation_is_not_an_id(self):
        self.assertEqual(audit_spec.cited_test_ids("see `evidence/runs/TEST-CLI-*`"), [])

    def test_path_prefix_citation_is_not_an_id(self):
        self.assertEqual(
            audit_spec.cited_test_ids("See TEST-NEXT-EDIT/RC/IO in the matrix."),
            [],
        )

    def test_range_endpoint_is_a_candidate(self):
        # The endpoint is resolved against the recorded inventory later; it
        # must be captured so that a range over real cases keeps them.
        self.assertEqual(
            audit_spec.cited_test_ids("cases TEST-CLI-001…007"),
            ["TEST-CLI-001"],
        )

    def test_compound_case_list_keeps_the_first_id(self):
        self.assertEqual(
            audit_spec.cited_test_ids("runtime TEST-UNDO-001/-002"),
            ["TEST-UNDO-001"],
        )

    def test_sentence_period_does_not_drop_the_id(self):
        self.assertEqual(audit_spec.cited_test_ids("TEST-UNDO-003."), ["TEST-UNDO-003"])


class AuditInventoryTest(unittest.TestCase):
    def test_inventory_lists_only_recorded_cases(self):
        known = recorded_ids()
        with (SPEC / "data/requirements.csv").open(newline="") as f:
            for row in csv.DictReader(f):
                for tid in row["explicit_test_ids"].split():
                    self.assertIn(tid, known, "%s cites %s" % (row["requirement"], tid))

    def test_inventory_has_no_hard_wrap_range_endpoint(self):
        text = (SPEC / "data/requirements.csv").read_text()
        self.assertNotIn("TEST-NEXT-UNDO-WRAP-001 ", text)
        self.assertNotIn(" TEST-NEXT-UNDO-WRAP-001,", text)


if __name__ == "__main__":
    unittest.main()
