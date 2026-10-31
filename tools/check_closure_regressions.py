#!/usr/bin/env python3
"""Require all recent exact-match suites and reopen their complete evidence.

No executable found in an evidence bundle is run. Reference identity is supplied
by the caller's frozen environment reference, never by a suite report itself.
"""
import argparse
import json
from pathlib import Path

from check_wrap_undo import (
    ROOT, report_problems, sha256, source_fingerprint,
)

SUITES = {"wrap-undo": 58, "filter": 6, "release-fixes": 15, "step3-gaps": 40}


def validate_suite(directory, suite, candidate_sha256, source_sha256,
                   reference_sha256, scenario_root=None):
    """Return (report, problems), including missing/malformed evidence failures."""
    scenario_root = scenario_root or ROOT / "tests/follow-up/scenarios"
    path = scenario_root / (suite + ".json")
    report = None
    try:
        cases = json.loads(path.read_text())
        ids = [case["id"] for case in cases]
        if len(ids) != SUITES[suite] or len(set(ids)) != len(ids):
            return None, ["scenario inventory count or uniqueness mismatch"]
        if any(not isinstance(tid, str) or not tid.startswith("TEST-")
               or "/" in tid or "\\" in tid for tid in ids):
            return None, ["unsafe scenario ID"]
        report = json.loads((directory / "report.json").read_text())
        hashes = {"runner": sha256((json.dumps(cases, indent=1) + "\n").encode())}
        problems = report_problems(
            report, hashes, source_sha256, directory, suite=path,
            expected_ids=ids, reference_sha256=reference_sha256,
        )
        if not isinstance(report, dict) or report.get("candidate_sha256") != candidate_sha256:
            problems.append("candidate differs from frozen closure executable")
        return report, problems
    except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError) as exc:
        return report, [f"missing or invalid suite evidence: {exc}"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args()
    try:
        candidate = sha256(args.binary.read_bytes())
        reference = sha256(args.reference.read_bytes())
    except OSError as exc:
        parser.exit(1, f"missing frozen executable: {exc}\n")
    source = source_fingerprint()
    failed = False
    for suite in SUITES:
        _, problems = validate_suite(args.base / suite, suite, candidate, source, reference)
        print(json.dumps({"suite": suite, "pass": not problems, "problems": problems}))
        failed |= bool(problems)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
