#!/usr/bin/env python3
"""Check issue #14 citation disposition and harness failure accounting."""

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "spec"

FORMER = {
    "CLI-001": {"TEST-CLI-P003", "TEST-CLI-P042", "TEST-KEY-RESTR-001"},
    "CLI-004": {"TEST-CLI-P009"},
    "CLI-014": {"TEST-RC-PREC-001"},
    "CLI-020": {"TEST-KEY-MODPRES-001"},
    "CLI-050": {"TEST-FILE-EXIT-002"},
    "KEY-003": {"TEST-KEY-TABLE-001"},
    "INPUT-014": {"TEST-INPUT-020"},
}


def run(*args):
    return subprocess.run(
        [sys.executable, *map(str, args)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def check_citations():
    found = set()
    for path in sorted(SPEC.glob("[0-9][0-9]-*.md")):
        text = path.read_text()
        blocks = re.split(r"(?=^### [A-Z][A-Z0-9-]+ —)", text, flags=re.M)
        for block in blocks:
            match = re.match(r"### ([A-Z][A-Z0-9-]+) —", block)
            if match and match.group(1) in FORMER:
                found.add(match.group(1))
                forbidden = FORMER[match.group(1)]
                remaining = [name for name in forbidden if name in block]
                assert not remaining, (path, match.group(1), remaining)
    assert found == set(FORMER), (found, set(FORMER))
    audit = json.loads((SPEC / "evidence/audit.json").read_text())
    assert not audit["problems"], audit["problems"]
    assert not any(name in warning for warning in audit["warnings"]
                   for names in FORMER.values() for name in names), audit["warnings"]
    print("citations: nine former names absent from their normative blocks")


def check_failure_accounting():
    with tempfile.TemporaryDirectory(prefix="naro-issue14-") as temporary:
        base = Path(temporary)
        reference, candidate = base / "reference", base / "candidate"
        reference.mkdir()
        candidate.mkdir()
        missing = run(SPEC / "tools/compare_runs.py", reference, candidate,
                      "TEST-ISSUE-14-MISSING")
        assert missing.returncode == 1 and "invalid or missing evidence" in missing.stdout
        print("missing comparison: DIFF, exit 1")

        cases = [
            ("INFRA", [], {"exit_status": 0}, base / "absent-binary", "ERROR", 1),
            ("RECORDED", [{"wait_exit": 3}], {}, Path("/usr/bin/true"), "RECORDED", 0),
            ("ASSERTION-FAIL", [{"wait_exit": 3}], {"exit_status": 99},
             Path("/usr/bin/true"), "FAIL", 1),
            ("FAILED-STEP", [{"wait": {"text": "never", "timeout": 0.1}}],
             {"exit_status": 0}, Path("/usr/bin/true"), "FAIL", 1),
        ]
        for suffix, steps, expect, binary, expected_status, expected_exit in cases:
            test_id = "TEST-ISSUE-14-" + suffix
            scenario = base / (suffix + ".json")
            scenario.write_text(json.dumps(
                {"id": test_id, "steps": steps, "expect": expect, "lang": "C"}))
            output = base / (suffix + "-out")
            output.mkdir()
            result = run(SPEC / "tools/nanoharness.py", scenario, "--binary", binary,
                         "--out", output)
            summary = json.loads((output / "last-summary.json").read_text())
            assert result.returncode == expected_exit, (suffix, result.stdout, result.stderr)
            assert summary[0][0:2] == [test_id, expected_status], summary
            if suffix == "FAILED-STEP":
                recorded = json.loads((output / test_id / "result.json").read_text())
                assert recorded["checks"][0]["pass"]
                assert recorded["step_checks"] == [{"step": 0, "pass": False}]
            print(f"{suffix.lower()}: {expected_status}, exit {expected_exit}")


if __name__ == "__main__":
    check_citations()
    check_failure_accounting()
