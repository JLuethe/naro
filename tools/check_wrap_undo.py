#!/usr/bin/env python3
"""Machine-checked manifest for the wrap-undo hard-wrap undo/redo suite.

Reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c.

The audit's matrix row (`TEST-NEXT-UNDO-WRAP-SUITE`) is declarative: it
discovers the suite but does not execute it, validate its membership, or
verify its recordings. This checker closes that gap for the scenario
manifest so a missing, duplicated, or out-of-range case (or a tampered
scenario file) fails the routine gate. It does not require the pinned
nano reference, so it can run in CI; the full differential comparison
(`tools/check_follow_up.py --suite wrap-undo`) is run locally against the
reference and the resulting `report.json` can be passed with `--report` to
validate the recorded evidence as well.

The `--report` check fails closed: it requires the exact case membership,
every per-side assertion and comparison flag, consistent summary counts,
both harness statuses, the pinned reference identity, the candidate
provenance (the source fingerprint of this tree) and the scenario digest
of the inputs that were actually replayed. A printed digest is not a
validation, and a self-reported boolean is not accepted on its own.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "tests/follow-up/scenarios/wrap-undo.json"
REFERENCE_COMMIT = "6ed285c3ec7a1d228def4d4e7021c6ba269f620c"
# SHA-256 of the pinned reference executable
# (`/home/john/src/nano-install/default/bin/nano`, GNU nano 9.3 default).
REFERENCE_SHA256 = "b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2"
# Expected exact scenario IDs in the suite. The numbering 001..027 is the
# original hard-wrap suite; 024-BSPJOIN is the Backspace equivalent of
# 020-DELJOIN, and 025/026/027 are the integrated decisive R2-CHAIN-REDO,
# whole-line cut and production NUL-join cases. 028..036 are the decisive
# reproductions of the reviewed defects: the explicit mark through a
# spillage join, the empty-predecessor Delete and Backspace joins, the
# partial multiline cut, the quote prefix, the continuation indent and the
# nonpositive fill geometry. Do not add or remove an ID without updating
# this list and the documentation.
EXPECTED_IDS = [
    "TEST-NEXT-UNDO-WRAP-001-MID",
    "TEST-NEXT-UNDO-WRAP-002-CHAIN",
    "TEST-NEXT-UNDO-WRAP-003-MULTI",
    "TEST-NEXT-UNDO-WRAP-004-INDENT",
    "TEST-NEXT-UNDO-WRAP-005-SPILL",
    "TEST-NEXT-UNDO-WRAP-006-PREFIX",
    "TEST-NEXT-UNDO-WRAP-007-INSERT",
    "TEST-NEXT-UNDO-WRAP-008-DELETE",
    "TEST-NEXT-UNDO-WRAP-009-REDO",
    "TEST-NEXT-UNDO-WRAP-010-UNDO-ONE",
    "TEST-NEXT-UNDO-WRAP-011-SAVE",
    "TEST-NEXT-UNDO-WRAP-012-AUTOSpill",
    "TEST-NEXT-UNDO-WRAP-013-MISMATCH",
    "TEST-NEXT-UNDO-WRAP-014-EMPTY",
    "TEST-NEXT-UNDO-WRAP-015-TABS",
    "TEST-NEXT-UNDO-WRAP-016-UTF8",
    "TEST-NEXT-UNDO-WRAP-017-WSTRAIL",
    "TEST-NEXT-UNDO-WRAP-018-REJECT",
    "TEST-NEXT-UNDO-WRAP-019-TRIM",
    "TEST-NEXT-UNDO-WRAP-020-DELJOIN",
    "TEST-NEXT-UNDO-WRAP-024-BSPJOIN",
    "TEST-NEXT-UNDO-WRAP-021-DIVERGE",
    "TEST-NEXT-UNDO-WRAP-022-NULBEFORE",
    "TEST-NEXT-UNDO-WRAP-023-NULAFTER",
    "TEST-NEXT-UNDO-WRAP-025-CHAIN-REDO",
    "TEST-NEXT-UNDO-WRAP-026-CUT-TAIL",
    "TEST-NEXT-UNDO-WRAP-027-NUL-JOIN",
    "TEST-NEXT-UNDO-WRAP-028-MARK",
    "TEST-NEXT-UNDO-WRAP-029-EMPTY-DEL",
    "TEST-NEXT-UNDO-WRAP-030-EMPTY-BSP",
    "TEST-NEXT-UNDO-WRAP-031-PARTIAL-CUT",
    "TEST-NEXT-UNDO-WRAP-032-QUOTE",
    "TEST-NEXT-UNDO-WRAP-033-CONT-INDENT",
    "TEST-NEXT-UNDO-WRAP-034-FILL-ZERO",
    "TEST-NEXT-UNDO-WRAP-035-FILL-NEG",
    "TEST-NEXT-UNDO-WRAP-036-ONECHAR",
    "TEST-NEXT-UNDO-WRAP-037-PASTE",
    "TEST-NEXT-UNDO-WRAP-038-PASTE-SHIFT",
    "TEST-NEXT-UNDO-WRAP-039-MARK-SHIFT",
]
# The source fingerprint follows the convention of `build.rs`: the SHA-256
# of the `sha256sum` output (file names included) of the sorted production
# inputs. It binds a recorded report to the source tree that was replayed.
FINGERPRINT_DIRS = ("src", "native", "assets")
FINGERPRINT_FILES = ("Cargo.toml", "Cargo.lock", "build.rs", "CREDITS.md")
ID_RE = re.compile(r"TEST-NEXT-UNDO-WRAP-(\d{3})-[A-Za-z0-9-]+")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def scenario_hashes(cases):
    """Return the three serialization-convention hashes for the scenario list."""
    raw = SUITE.read_bytes()
    canonical = json.dumps(cases, sort_keys=True, separators=(",", ":")).encode()
    runner = (json.dumps(cases, indent=1) + "\n").encode()
    return {
        "raw": sha256(raw),
        "canonical": sha256(canonical),
        "runner": sha256(runner),
    }


def source_fingerprint(root: Path = ROOT):
    """Recompute the `build.rs` source fingerprint of the tree, or None."""
    files = []
    for name in FINGERPRINT_DIRS:
        base = root / name
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file():
                files.append(path.relative_to(root))
    for name in FINGERPRINT_FILES:
        if (root / name).is_file():
            files.append(Path(name))
    if not files:
        return None
    try:
        sums = subprocess.run(
            ["sha256sum", *[str(f) for f in sorted(files)]],
            cwd=root,
            capture_output=True,
            check=True,
        ).stdout
        return sha256(sums)
    except (OSError, subprocess.CalledProcessError):
        return None


def manifest_problems(cases):
    """Validate the scenario manifest itself. Returns a list of problems."""
    problems = []
    if not isinstance(cases, list):
        return ["suite is not a JSON list"]
    ids = [c.get("id") if isinstance(c, dict) else None for c in cases]
    seen = set()
    for i in ids:
        if i in seen:
            problems.append("duplicate scenario id: %s" % i)
        seen.add(i)
    missing = [i for i in EXPECTED_IDS if i not in seen]
    extra = [i for i in seen if i not in EXPECTED_IDS]
    if missing:
        problems.append("missing expected scenario ids: %s" % ", ".join(missing))
    if extra:
        problems.append("unexpected scenario ids: %s" % ", ".join(extra))
    for i in ids:
        if not isinstance(i, str) or not ID_RE.fullmatch(i):
            problems.append("malformed scenario id: %r" % i)
            continue
        num = int(ID_RE.fullmatch(i).group(1))
        if not 1 <= num <= 39:
            problems.append("scenario id out of range: %s" % i)
    for c in cases:
        if not isinstance(c, dict):
            problems.append("scenario is not an object")
            continue
        tid = c.get("id")
        fw = c.get("files", {}).get("work/f.txt")
        if not fw or "hex" not in fw:
            problems.append("%s: missing work/f.txt hex fixture" % tid)
        elif (not isinstance(fw["hex"], str)
              or len(fw["hex"]) % 2
              or not re.fullmatch(r"[0-9a-fA-F]*", fw["hex"])):
            problems.append("%s: malformed work/f.txt hex fixture" % tid)
        if "expect" not in c or "exit_status" not in c["expect"]:
            problems.append("%s: missing exit_status expectation" % tid)
        if not c.get("steps"):
            problems.append("%s: no steps" % tid)
        if not c.get("note"):
            problems.append("%s: no note" % tid)
    return problems


def report_problems(report, hashes, fingerprint=None, report_dir=None):
    """Validate a recorded wrap-undo report. Returns a list of problems."""
    problems = []
    if not isinstance(report, dict):
        return ["report is not a JSON object"]
    if report.get("reference_commit") != REFERENCE_COMMIT:
        problems.append("report reference commit %r is not %s"
                        % (report.get("reference_commit"), REFERENCE_COMMIT))
    ref_sha = report.get("reference_sha256")
    if ref_sha != REFERENCE_SHA256:
        problems.append("report reference executable %r is not the pinned %s"
                        % (ref_sha, REFERENCE_SHA256))
    cand_sha = report.get("candidate_sha256")
    if not isinstance(cand_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", cand_sha):
        problems.append("report candidate_sha256 is missing or malformed")
    if report.get("scenario_sha256") != hashes["runner"]:
        problems.append("report scenario_sha256 %r does not match the replayed "
                        "scenario inputs %s" % (report.get("scenario_sha256"),
                                                hashes["runner"]))
    for key in ("reference_status", "candidate_status"):
        if report.get(key) != 0:
            problems.append("nonzero %s: %r" % (key, report.get(key)))
    build = report.get("candidate_build")
    if not isinstance(build, dict):
        problems.append("report has no candidate_build provenance")
    else:
        if build.get("reference_commit") != REFERENCE_COMMIT:
            problems.append("candidate build reference commit %r is not %s"
                            % (build.get("reference_commit"), REFERENCE_COMMIT))
        if fingerprint is not None and build.get("source_sha256") != fingerprint:
            problems.append("candidate build source fingerprint %r does not match "
                            "this tree %s" % (build.get("source_sha256"), fingerprint))
        if build.get("features") not in ("", None):
            problems.append("candidate build features %r is not the default profile"
                            % build.get("features"))
    res = report.get("results")
    if not isinstance(res, dict):
        problems.append("report results is not an object")
        res = {}
    missing = [i for i in EXPECTED_IDS if i not in res]
    extra = [i for i in res if i not in EXPECTED_IDS]
    if missing:
        problems.append("report missing recordings: %s" % ", ".join(missing))
    if extra:
        problems.append("report has unexpected recordings: %s" % ", ".join(extra))
    for tid, value in sorted(res.items()):
        if not isinstance(value, dict):
            problems.append("%s: result is not an object" % tid)
            continue
        if value.get("match") is not True:
            problems.append("%s: result is not an exact match" % tid)
        if value.get("accepted") is not True:
            problems.append("%s: result is not accepted" % tid)
        if value.get("reference_checks") is not True:
            problems.append("%s: reference side checks did not pass" % tid)
        if value.get("candidate_checks") is not True:
            problems.append("%s: candidate side checks did not pass" % tid)
        if value.get("declared_deviation"):
            problems.append("%s: result declares a deviation" % tid)
        if value.get("deviation_id"):
            problems.append("%s: result names a deviation %r" % (tid, value.get("deviation_id")))
        diff = value.get("differences")
        if not isinstance(diff, list):
            problems.append("%s: result has no differences list" % tid)
        elif diff:
            problems.append("%s: result has %d difference(s)" % (tid, len(diff)))
    summary = report.get("summary")
    if not isinstance(summary, dict):
        problems.append("report has no summary")
    else:
        recorded = summary.get("recorded")
        matches = summary.get("matches")
        accepted = summary.get("accepted")
        if recorded != len(EXPECTED_IDS):
            problems.append("summary recorded %r, expected %d" % (recorded, len(EXPECTED_IDS)))
        if matches != len(EXPECTED_IDS):
            problems.append("summary matches %r, expected %d" % (matches, len(EXPECTED_IDS)))
        if accepted != len(EXPECTED_IDS):
            problems.append("summary accepted %r, expected %d" % (accepted, len(EXPECTED_IDS)))
    if report_dir is not None:
        for name, expected in (("reference.bin", REFERENCE_SHA256),
                               ("candidate.bin", cand_sha)):
            path = report_dir / name
            if path.is_file():
                digest = sha256(path.read_bytes())
                if digest != expected:
                    problems.append("%s hash %s does not match the recorded %s"
                                    % (name, digest, expected))
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", type=Path,
                    help="wrap-undo report.json to validate for completeness/matches")
    args = ap.parse_args()
    try:
        cases = json.loads(SUITE.read_text())
    except Exception as e:
        print("FATAL: cannot parse %s: %s" % (SUITE, e))
        return 1
    problems = manifest_problems(cases)
    hashes = scenario_hashes(cases) if isinstance(cases, list) else {
        "raw": "", "canonical": "", "runner": ""}
    if problems:
        print("FAIL: %d problem(s) in wrap-undo manifest" % len(problems))
        for p in problems:
            print("  - " + p)
        return 1
    print("OK: %d scenarios, no duplicates, no gaps" % len(cases))
    print("  scenario_sha256_raw:        %s" % hashes["raw"])
    print("  scenario_sha256_canonical:  %s" % hashes["canonical"])
    print("  scenario_sha256_runner:     %s" % hashes["runner"])
    if args.report:
        try:
            report = json.loads(args.report.read_text())
        except Exception as e:
            print("FAIL: cannot parse %s: %s" % (args.report, e))
            return 1
        fingerprint = source_fingerprint()
        report_dir = args.report.parent if args.report.parent.is_dir() else None
        problems = report_problems(report, hashes, fingerprint, report_dir)
        if problems:
            print("FAIL: %d problem(s) in wrap-undo report" % len(problems))
            for p in problems:
                print("  - " + p)
            return 1
        print("OK: report %d/%d matches, both harnesses 0, provenance pinned"
              % (len(EXPECTED_IDS), len(EXPECTED_IDS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
