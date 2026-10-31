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
import base64
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "spec/tools"))
from compare_runs import compare, fixture_root  # noqa: E402
from nanoharness import Keys, Run  # noqa: E402
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
    "TEST-NEXT-UNDO-WRAP-040-MARK-SPLIT",
    "TEST-NEXT-UNDO-WRAP-041-MARK-EOF",
    "TEST-NEXT-UNDO-WRAP-042-MARK-PREFIX",
    "TEST-NEXT-UNDO-WRAP-043-MARK-BLANKS",
    "TEST-NEXT-UNDO-WRAP-044-TRAILING-SPACE",
    "TEST-NEXT-UNDO-WRAP-045-MARK-FWD",
    "TEST-NEXT-UNDO-WRAP-046-MARK-IN-PREFIX",
    "TEST-NEXT-UNDO-WRAP-047-SPLIT-MARK-0",
    "TEST-NEXT-UNDO-WRAP-048-SPLIT-MARK-8",
    "TEST-NEXT-UNDO-WRAP-049-SPLIT-MARK-12",
    "TEST-NEXT-UNDO-WRAP-050-SPLIT-MARK-14",
    "TEST-NEXT-UNDO-WRAP-051-PREFIX-MARK-0",
    "TEST-NEXT-UNDO-WRAP-052-PREFIX-MARK-1",
    "TEST-NEXT-UNDO-WRAP-053-PREFIX-MARK-4",
    "TEST-NEXT-UNDO-WRAP-054-PREFIX-MARK-6",
    "TEST-NEXT-UNDO-WRAP-055-PREFIX-MARK-7",
    "TEST-NEXT-UNDO-WRAP-056-MARK-UTF8",
    "TEST-NEXT-UNDO-WRAP-057-MARK-QUOTE",
    "TEST-NEXT-UNDO-WRAP-058-MARK-TRIM",
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
            return None
        for path in sorted(base.rglob("*")):
            if path.is_file():
                files.append(path.relative_to(root))
    for name in FINGERPRINT_FILES:
        if not (root / name).is_file():
            return None
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


VERIFICATION_FILES = (
    "tools/check_follow_up.py", "tools/check_wrap_undo.py",
    "tools/environment.py", "tools/follow_up_policy.py",
    "spec/tools/compare_runs.py", "spec/tools/nanoharness.py",
)


def verification_fingerprint():
    return sha256(b"".join(name.encode() + b"\0" + (ROOT / name).read_bytes()
                           + b"\0" for name in VERIFICATION_FILES))


def manifest_problems(cases):
    """Validate the scenario manifest itself. Returns a list of problems."""
    problems = []
    if not isinstance(cases, list):
        return ["suite is not a JSON list"]
    ids = [c.get("id") if isinstance(c, dict) else None for c in cases]
    seen = set()
    for i in ids:
        if not isinstance(i, str):
            problems.append("malformed scenario id: %r" % i)
            continue
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
        if not 1 <= num <= len(EXPECTED_IDS):
            problems.append("scenario id out of range: %s" % i)
    for c in cases:
        if not isinstance(c, dict):
            problems.append("scenario is not an object")
            continue
        tid = c.get("id")
        if (not isinstance(c.get("files"), dict)
                or not isinstance(c.get("expect"), dict)):
            problems.append(f"{tid}: missing files/expect object")
            continue
        fw = c["files"].get("work/f.txt")
        if not isinstance(fw, dict) or "hex" not in fw:
            problems.append("%s: missing work/f.txt hex fixture" % tid)
        elif (not isinstance(fw["hex"], str)
              or len(fw["hex"]) % 2
              or not re.fullmatch(r"[0-9a-fA-F]*", fw["hex"])):
            problems.append("%s: malformed work/f.txt hex fixture" % tid)
        if "expect" not in c or "exit_status" not in c["expect"]:
            problems.append("%s: missing exit_status expectation" % tid)
        if not isinstance(c.get("steps"), list) or not c["steps"]:
            problems.append("%s: no steps" % tid)
        if not c.get("note"):
            problems.append("%s: no note" % tid)
    return problems


def report_problems(report, hashes, fingerprint=None, report_dir=None, *,
                    suite=None, expected_ids=None, reference_sha256=None):
    """Validate exact-match evidence; defaults retain the pinned wrap contract.

    Closure supplies an explicit suite and independently frozen environment
    reference hash, since Ubuntu's reference executable differs from the host's.
    """
    suite = SUITE if suite is None else suite
    expected_ids = EXPECTED_IDS if expected_ids is None else expected_ids
    reference_sha256 = REFERENCE_SHA256 if reference_sha256 is None else reference_sha256
    problems = []
    if not isinstance(report, dict):
        return ["report is not a JSON object"]
    if report.get("reference_commit") != REFERENCE_COMMIT:
        problems.append("report reference commit %r is not %s"
                        % (report.get("reference_commit"), REFERENCE_COMMIT))
    if report.get("verification_sha256") != verification_fingerprint():
        problems.append("report verification tools fingerprint does not match this tree")
    ref_sha = report.get("reference_sha256")
    if ref_sha != reference_sha256:
        problems.append("report reference executable %r is not the pinned %s"
                        % (ref_sha, reference_sha256))
    cand_sha = report.get("candidate_sha256")
    if not isinstance(cand_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", cand_sha):
        problems.append("report candidate_sha256 is missing or malformed")
    if report.get("scenario_sha256") != hashes["runner"]:
        problems.append("report scenario_sha256 %r does not match the replayed "
                        "scenario inputs %s" % (report.get("scenario_sha256"),
                                                hashes["runner"]))
    for key in ("reference_status", "candidate_status"):
        if type(report.get(key)) is not int or report[key] != 0:
            problems.append("nonzero %s: %r" % (key, report.get(key)))
    if not isinstance(fingerprint, str) or not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
        problems.append("cannot compute this tree source fingerprint")
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
        if build.get("features") != "":
            problems.append("candidate build features %r is not the default profile"
                            % build.get("features"))
    res = report.get("results")
    if not isinstance(res, dict):
        problems.append("report results is not an object")
        res = {}
    missing = [i for i in expected_ids if i not in res]
    extra = [i for i in res if i not in expected_ids]
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
        if value.get("declared_deviation") is not False:
            problems.append("%s: result declares a deviation" % tid)
        if "deviation_id" not in value or value["deviation_id"] is not None:
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
        if type(recorded) is not int or recorded != len(expected_ids):
            problems.append("summary recorded %r, expected %d" % (recorded, len(expected_ids)))
        if type(matches) is not int or matches != len(expected_ids):
            problems.append("summary matches %r, expected %d" % (matches, len(expected_ids)))
        if type(accepted) is not int or accepted != len(expected_ids):
            problems.append("summary accepted %r, expected %d" % (accepted, len(expected_ids)))
    if report_dir is None:
        problems.append("report evidence directory is required")
    else:
        try:
            problems.extend(artifact_problems(report, hashes, Path(report_dir), suite=suite,
                                              expected_ids=expected_ids, reference_sha256=reference_sha256))
        except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError) as exc:
            problems.append(f"invalid evidence artifacts: {exc}")
    return problems


def artifact_problems(report, hashes, directory, *, suite=None,
                      expected_ids=None, reference_sha256=None):
    """Reopen evidence without executing any report-supplied executable."""
    suite = SUITE if suite is None else suite
    expected_ids = EXPECTED_IDS if expected_ids is None else expected_ids
    reference_sha256 = REFERENCE_SHA256 if reference_sha256 is None else reference_sha256
    problems = []

    def read_json(path):
        try:
            return json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            problems.append(f"{path}: missing or invalid JSON: {exc}")
            return None

    for side, expected in (("reference", reference_sha256),
                           ("candidate", report.get("candidate_sha256"))):
        path = directory / (side + ".bin")
        try:
            if sha256(path.read_bytes()) != expected:
                problems.append(f"{path.name}: executable hash mismatch")
        except OSError as exc:
            problems.append(f"{path.name}: required executable missing/unreadable: {exc}")

    cases = read_json(directory / "scenarios.json")
    if not isinstance(cases, list):
        return problems + ["frozen scenarios.json is not a list"]
    # Bind actual frozen bytes and parsed inputs to this checkout's suite.
    if sha256((json.dumps(cases, indent=1) + "\n").encode()) != hashes["runner"]:
        problems.append("frozen scenarios.json does not match this suite")
    if sha256((directory / "scenarios.json").read_bytes()) != report.get("scenario_sha256"):
        problems.append("frozen scenarios.json hash does not match report")
    try:
        if cases != json.loads(suite.read_text()):
            problems.append("frozen scenario contents differ from current suite")
    except (OSError, ValueError) as exc:
        return problems + [f"cannot read current suite: {exc}"]
    for side in ("reference", "candidate"):
        if read_json(directory / (side + "-scenarios.json")) != cases:
            problems.append(f"{side}-scenarios.json differs from frozen suite")
    # Do not follow IDs from untrusted JSON as filesystem paths.
    by_id = {c.get("id"): c for c in cases if isinstance(c, dict)
             and isinstance(c.get("id"), str)}
    if set(by_id) != set(expected_ids) or len(cases) != len(expected_ids):
        return problems + ["frozen scenario membership is not exact"]
    keys_by_term = {}
    for tid in expected_ids:
        case = by_id[tid]
        term = case.get("term", "tmux-256color")
        if term not in keys_by_term:
            keys_by_term[term] = Keys(term)
        runs = []
        for side in ("reference", "candidate"):
            path = directory / side / tid / "result.json"
            run = read_json(path)
            if not isinstance(run, dict):
                problems.append(f"{side}/{tid}: missing recording object")
                continue
            runs.append(run)
            try:
                problems.extend(recording_problems(run, case, side, report, path.parent, keys_by_term[term]))
            except (KeyError, TypeError, ValueError, IndexError, AttributeError) as exc:
                problems.append(f"{side}/{tid}: malformed recording: {exc}")
        if len(runs) == 2:
            try:
                diffs = compare(*runs)
                if diffs:
                    problems.append(f"{tid}: recomputed comparison has differences: "
                                    + ", ".join(d["field"] for d in diffs[:8]))
            except (KeyError, TypeError, ValueError, IndexError, AttributeError) as exc:
                problems.append(f"{tid}: cannot compare recordings: {exc}")
    return problems


def recording_problems(run, case, side, report, directory, keys):
    label = f"{side}/{case['id']}"
    problems = []
    for key, expected in (("scenario", case["id"]),
                          ("reference_commit", REFERENCE_COMMIT),
                          ("binary_sha256", report.get(side + "_sha256")),
                          ("scenario_sha256", sha256(json.dumps(
                              case, sort_keys=True, separators=(",", ":")).encode()))):
        if run.get(key) != expected:
            problems.append(f"{label}: {key} identity mismatch")
    if run.get("steps_ok") is not True:
        problems.append(f"{label}: steps did not pass")
    steps = run.get("step_checks")
    if (not isinstance(steps, list) or len(steps) != len(case["steps"])
            or any(not isinstance(c, dict) or type(c.get("step")) is not int
                   or c["step"] != i or c.get("pass") is not True
                   for i, c in enumerate(steps))):
        problems.append(f"{label}: incomplete or failed step checks")
    notes = run["notes"]
    if not isinstance(notes, list) or notes:
        problems.append(f"{label}: unexpected recording notes: {notes!r}")
    expected_snaps = {s["snapshot"] for s in case["steps"] if "snapshot" in s}
    if not isinstance(run.get("snapshots"), dict) or set(run["snapshots"]) != expected_snaps:
        problems.append(f"{label}: snapshot membership mismatch")
    for key in ("after_exit_screen", "initial_fixture", "fixture", "captured_files",
                "trace_final_modes", "env"):
        if not isinstance(run.get(key), dict):
            problems.append(f"{label}: missing {key}")
    for key in ("inputs", "checks", "helper_statuses"):
        if not isinstance(run.get(key), list):
            problems.append(f"{label}: missing {key}")
    if type(run.get("exit_status")) is not int or run["exit_status"] != 0 or run.get("exit_signal") is not None:
        problems.append(f"{label}: invalid exit status/signal")
    expected_inputs = []
    for step in case["steps"]:
        if "keys" in step:
            data = b"".join(keys.encode(k) for k in step["keys"])
        elif "text" in step:
            data = step["text"].encode()
        elif "hex" in step:
            data = bytes.fromhex(step["hex"])
        elif "paste" in step:
            data = b"\x1b[200~" + step["paste"].encode() + b"\x1b[201~"
        else:
            continue
        expected_inputs.append(data.hex())
    if [item["hex"] for item in run["inputs"]] != expected_inputs:
        problems.append(f"{label}: input bytes/order differ from frozen scenario")
    # Recompute expectations instead of accepting saved 'pass' flags.
    runner = Run(case, "unused", "unused")
    runner.root = fixture_root(run)
    if not runner.root:
        problems.append(f"{label}: cannot determine fixture root")
    checks = runner.check(run)
    if not checks or any(c["pass"] is not True for c in checks):
        problems.append(f"{label}: recomputed expectations failed")
    if checks != run.get("checks"):
        problems.append(f"{label}: recorded checks differ from recomputed expectations")
    # Inline bytes, sizes and hashes must agree even if both sides were edited.
    for key in ("fixture", "initial_fixture", "temp_files"):
        entries = run[key]
        if not isinstance(entries, dict):
            raise ValueError(f"invalid {key}")
        for name, entry in entries.items():
            if entry["type"] == "file" and "b64" in entry:
                raw = base64.b64decode(entry["b64"], validate=True)
                if entry.get("size") != len(raw) or entry.get("sha256") != sha256(raw):
                    problems.append(f"{label}: {key}/{name} byte metadata mismatch")
                if "text" in entry and entry["text"].encode() != raw:
                    problems.append(f"{label}: {key}/{name} text differs from bytes")
    path = directory / "raw-output.bin"
    try:
        raw = path.read_bytes()
        if run.get("raw_output_sha256") != sha256(raw) or run.get("raw_output_bytes") != len(raw):
            problems.append(f"{label}: raw-output.bin hash/size mismatch")
    except OSError as exc:
        problems.append(f"{label}: raw-output.bin missing/unreadable: {exc}")
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
