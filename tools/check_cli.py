#!/usr/bin/env python3
"""Replay the frozen noninteractive CLI corpus into a caller-owned output path."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "spec/tools"))
from candidate_expectations import POLICY, expected_cli_output  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True, help="frozen default-feature NARO executable")
    parser.add_argument("--out", type=Path, required=True, help="new output directory; must not exist")
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    out = args.out.absolute()
    if out.resolve().is_relative_to(ROOT.resolve()):
        parser.error("--out must be outside the source checkout")
    if out.exists():
        parser.error(f"preserve evidence: output already exists: {out}")
    out.mkdir(parents=True, exist_ok=False)

    corpus = json.loads((ROOT / "spec/evidence/cli/cli-probes.json").read_text(encoding="utf-8"))
    scenarios, expected, skipped = [], {}, {}
    for row in corpus["results"]:
        if row["profile"] == "tiny":
            skipped[row["id"]] = "optional tiny profile"
            continue
        if any(value.startswith("/") for value in row["args"]):
            skipped[row["id"]] = "absolute path probe outside fixture"
            continue
        files = {}
        for key, data in corpus["rc_files"].items():
            name = {"$RC1": "rc1", "$RCBAD": "rcbad", "$RCVITAL": "rcvital", "$RCSYN": "rcsyn"}[key]
            files[f"work/{name}"] = {"text": data}
        if row["id"] == "CLI-P-043":
            files["home/.nanorc"] = {"text": 'syntax one "\\.one$"\ncolor red "a"\n'}
        test_id = "TEST-NARO-CLI-" + row["id"].split("-")[-1]
        scenarios.append({
            "id": test_id,
            "argv0": row["argv0"],
            "args": [value.replace("$TMP/", "$FX/work/") for value in row["args"]],
            "dirs": ["work/rcdir"],
            "files": files,
            "env": {},
            "stdin": "",
            "stdout_redirect": True,
            "hold_tty": True,
            "steps": [{"wait_exit": 5}],
            "expect": {"exit_status": row["exit_status"]},
        })
        expectation = dict(row)
        expectation["stdout"] = expected_cli_output(row["stdout"])
        expected[test_id] = expectation

    scenarios_path = out / "scenarios.json"
    scenarios_path.write_text(json.dumps(scenarios, indent=1) + "\n", encoding="utf-8")
    harness_out = out / "runs"
    command = [sys.executable, str(ROOT / "spec/tools/nanoharness.py"), str(scenarios_path),
               "--binary", str(binary), "--out", str(harness_out)]
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    status = subprocess.run(command, cwd=ROOT, env=env).returncode
    report = {
        "schema": 1,
        "identity_policy": POLICY,
        "oracle_projection": "expected stdout identity only; actual stdout outside reviewed identity projection and all stderr remain exact",
        "reference_commit": "6ed285c3ec7a1d228def4d4e7021c6ba269f620c",
        "binary_path": str(binary),
        "binary_sha256": sha256(binary),
        "scenario_sha256": sha256(scenarios_path),
        "skipped": skipped,
        "results": {},
        "command": command,
        "harness_status": status,
    }
    for test_id, row in expected.items():
        result_path = harness_out / test_id / "result.json"
        if not result_path.is_file():
            report["results"][test_id] = [{"field": "missing_result", "path": str(result_path)}]
            continue
        result = json.loads(result_path.read_text(encoding="utf-8"))
        differences = []
        for field in ("exit_status", "stdout", "stderr"):
            if result.get(field) != row[field]:
                differences.append({"field": field, "expected": row[field], "actual": result.get(field)})
        report["results"][test_id] = differences
    report["summary"] = {
        "compared": len(expected),
        "matches": sum(not differences for differences in report["results"].values()),
        "failed": sum(bool(differences) for differences in report["results"].values()),
        "skipped": len(skipped),
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], sort_keys=True))
    return status or int(bool(report["summary"]["failed"]))


if __name__ == "__main__":
    raise SystemExit(main())
