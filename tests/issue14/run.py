#!/usr/bin/env python3
"""Issue #14 candidate runtime assertions, scoped to supplied exact binaries."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "spec/tools"))
from candidate_expectations import expected_cli_output

PINNED_REFERENCE_SHA256 = "b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2"
PINNED_PROBES_SHA256 = "85dab2e030c5db211a92977e8c91da028189690e3f9709cb8267399d87c90749"
HOOK_IDS = {
    "TEST-ISSUE14-KEYS-DEFAULT", "TEST-ISSUE14-KEYS-RNANO",
    "TEST-ISSUE14-KEYS-RESTRICTED", "TEST-ISSUE14-KEYS-MODERN-PRESERVE",
    "TEST-ISSUE14-RC-ONLY", "TEST-ISSUE14-RC-CLI-WINS",
    "TEST-ISSUE14-RC-RESTRICTED", "TEST-ISSUE14-KEYS-C",
    "TEST-ISSUE14-KEYS-MODERN", "TEST-ISSUE14-KEYS-MODERN-VT220",
    "TEST-ISSUE14-KEYS-PRESERVE", "TEST-ISSUE14-KEYS-SAVEONEXIT",
    "TEST-ISSUE14-KEYS-VIEW",
}

EXTRA_DEFAULT = {
    "C": ("default-C", ["-I"], "C", "xterm-256color"),
    "MODERN": ("default-modern", ["-I", "--modernbindings"], "en_US.UTF-8", "xterm-256color"),
    "MODERN-VT220": ("default-modern-vt220", ["-I", "--modernbindings"], "en_US.UTF-8", "vt220"),
    "PRESERVE": ("default-preserve", ["-I", "--preserve"], "en_US.UTF-8", "xterm-256color"),
    "SAVEONEXIT": ("default-saveonexit", ["-I", "--saveonexit"], "en_US.UTF-8", "xterm-256color"),
    "VIEW": ("default-view", ["-I", "--view"], "en_US.UTF-8", "xterm-256color"),
}


def key_case(case_id, args, lang="en_US.UTF-8", term="xterm-256color"):
    return {"id": case_id, "argv0": "nano", "args": args, "lang": lang,
            "term": term, "env": {"NARO_ISSUE14_SNAPSHOT": "$FX/snapshot.txt"},
            "steps": [{"wait_exit": 5}, {"capture_file": "snapshot.txt"}],
            "expect": {"exit_status": 0}}


def cancellation_case():
    # A finite two-megabyte line keeps the candidate's literal scan active
    # long enough to deliver ^C and X in the same PTY burst.  No generated
    # fixture is committed or sent to an external service.
    return {"id": "TEST-ISSUE14-SEARCH-CANCEL-BURST", "args": ["-I", "f.txt"],
            "files": {"work/f.txt": {"text": "a" * 2_000_000 + "\n"}},
            "steps": [{"wait": {"text": "f.txt"}}, {"keys": ["^W"]},
                      {"text": "zzzz"}, {"keys": ["Enter"]}, {"hex": "0358"},
                      {"wait": {"text": "Cancelled", "timeout": 3}},
                      {"keys": ["^X"]}, {"wait_exit": 5}],
            "expect": {"exit_status": 0}}


def rebound_cancel_case():
    case = cancellation_case()
    case["id"] = "TEST-ISSUE14-SEARCH-REBOUND-CANCEL"
    case["args"] = ["--rcfile=$FX/home/cancel.rc", "f.txt"]
    case["files"]["home/cancel.rc"] = {
        "text": "unbind ^C search\nbind ^G cancel search\n"}
    case["steps"][4] = {"hex": "0758"}
    return case


def unbound_control_c_case():
    case = rebound_cancel_case()
    case["id"] = "TEST-ISSUE14-SEARCH-UNBOUND-CONTROL-C"
    case["steps"][4] = {"hex": "0358"}
    case["steps"][5] = {"wait": {"text": "not found", "timeout": 4}}
    return case


def decoded_cancel_case(case_id, rc, burst, should_cancel):
    case = cancellation_case()
    case["id"] = case_id
    case["args"] = ["--rcfile=$FX/home/cancel.rc", "f.txt"]
    case["files"]["home/cancel.rc"] = {"text": rc}
    case["steps"][4] = {"hex": burst}
    if not should_cancel:
        case["steps"][5] = {"wait": {"text": "not found", "timeout": 4}}
    return case


def decoded_cancel_cases():
    meta_rc = "unbind ^C search\nbind M-G cancel search\n"
    return [
        decoded_cancel_case("TEST-ISSUE14-META-G-PLAIN-G", meta_rc, "6758", False),
        decoded_cancel_case("TEST-ISSUE14-META-G-ACTUAL", meta_rc, "1b6758", True),
        decoded_cancel_case("TEST-ISSUE14-META-LEFT-CANCEL",
                            "unbind ^C search\nbind M-Left cancel search\n",
                            "1b5b313b334458", True),
        decoded_cancel_case("TEST-ISSUE14-RAW-F1-CANCEL",
                            "unbind ^C search\nbind F1 cancel search\nset rawsequences\n",
                            "1b4f5058", True),
    ]


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def snapshot(result):
    encoded = result["captured_files"]["snapshot.txt"][0]
    require(not encoded.startswith("ERROR:"), encoded)
    values, keys, strings = {}, [], {}
    for line in base64.b64decode(encoded).decode().splitlines():
        parts = line.split(" ")
        if parts[0] == "key":
            require(len(parts) == 7, "malformed key row: " + line)
            keys.append((int(parts[1]), int(parts[2]), int(parts[3]),
                         parts[4], bytes.fromhex(parts[5]).decode(), int(parts[6])))
        elif parts[0] == "string":
            strings[parts[1]] = bytes.fromhex(parts[2]).decode()
        else:
            values[parts[0]] = int(parts[1])
    require(keys, "empty candidate key table")
    return values, keys, strings


def table(name):
    raw = json.loads((ROOT / "spec/evidence/tables" / (name + ".json")).read_text())
    require(raw["keys"], "empty reference table")
    return [(k["order"], k["keycode"], k["menus_mask"], k["func"],
             k["keystr"], k.get("toggle", 0)) for k in raw["keys"]]


def run_harness(cases, binary, out):
    manifest = out / "scenarios.json"
    manifest.write_text(json.dumps(cases, indent=2) + "\n")
    cmd = [sys.executable, str(ROOT / "spec/tools/nanoharness.py"),
           str(manifest), "--binary", str(binary), "--out", str(out / "runs")]
    completed = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    print(completed.stdout, end="")
    require(completed.returncode == 0, "harness exit %d: %s" %
            (completed.returncode, completed.stderr))
    summary = json.loads((out / "runs/last-summary.json").read_text())
    require(len(summary) == len(cases), "harness omitted a case")
    require(all(row[1] == "PASS" and row[2] > 0 for row in summary),
            "harness had non-passing/empty assertion")
    results = {}
    for case in cases:
        result = json.loads((out / "runs" / case["id"] / "result.json").read_text())
        require(result["steps_ok"] and all(c["pass"] for c in result["checks"]),
                case["id"] + " failed a step or expectation")
        results[case["id"]] = result
    return results


def cli(binary, argv0, args, home):
    env = {"HOME": str(home), "LC_ALL": "C", "LANG": "C", "TERM": "xterm-256color",
           "PATH": "/usr/bin:/bin"}
    return subprocess.run([argv0, *args], executable=binary, cwd=home, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def build_info(path, features):
    proc = subprocess.run([path], env={"NARO_BUILD_INFO": "1"},
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    require(proc.returncode == 0 and not proc.stderr, f"build info failed: {path}")
    info = json.loads(proc.stdout)
    require(info["features"] == features, f"wrong features in {path}: {info['features']}")
    require(info["reference_commit"] == "6ed285c3ec7a1d228def4d4e7021c6ba269f620c",
            "wrong reference revision")
    return info


def recorded_cli_oracles():
    path = ROOT / "spec/evidence/cli/cli-probes.json"
    require(hashlib.sha256(path.read_bytes()).hexdigest() == PINNED_PROBES_SHA256,
            "recorded CLI oracle changed")
    data = json.loads(path.read_text())
    require(data["reference_commit"] == "6ed285c3ec7a1d228def4d4e7021c6ba269f620c",
            "recorded CLI oracle reference changed")
    return {row["id"]: row for row in data["results"]}


def check_cli(binary, reference, out):
    home = out / "home"
    home.mkdir()
    probes = recorded_cli_oracles()
    base_stdout = probes["CLI-P-001"]["stdout"]
    restricted_stdout = probes["CLI-P-003"]["stdout"]
    require(base_stdout != restricted_stdout, "recorded help controls collapsed")
    for name in ("nano", "rnano", "rvi", "xnano", "Rnano"):
        if reference:
            ref = cli(reference, name, ["--help"], home)
            expected = (ref.returncode, ref.stdout.decode(), ref.stderr)
            oracle = restricted_stdout if name in ("rvi", "rnano") else base_stdout
            require(expected == (0, oracle, b""), name + " differs from pinned help oracle")
        else:
            oracle = restricted_stdout if name in ("rvi", "rnano") else base_stdout
            expected = (0, oracle, b"")
        got = cli(binary, name, ["--help"], home)
        expect = expected_cli_output(expected[1]).encode()
        require((got.returncode, got.stdout, got.stderr) ==
                (expected[0], expect, expected[2]), name + " help differs")
    print("CLI invocation-name help: five pinned reference-projected cases PASS")
    diagnostics = [("CLI-P-009", ["--bogus"]), ("CLI-P-018", ["--s"]),
                   ("CLI-P-016", ["-T"])]
    for probe_id, args in diagnostics:
        oracle = probes[probe_id]
        require(oracle["argv0"] == "nano" and oracle["args"] == args,
                "pinned diagnostic probe changed: " + probe_id)
        got = cli(binary, "nano", args, home)
        require((got.returncode, got.stdout, got.stderr) ==
                (oracle["exit_status"], oracle["stdout"].encode(), oracle["stderr"].encode()),
                "diagnostic differs: " + repr(args))
    if reference:
        for args in (["-^"], ["--view=x"]):
            ref = cli(reference, "nano", args, home)
            got = cli(binary, "nano", args, home)
            require((got.returncode, got.stdout, got.stderr) ==
                    (ref.returncode, ref.stdout, ref.stderr),
                    "additional diagnostic differs: " + repr(args))
    print("CLI diagnostics: %d exact reference cases PASS" % (5 if reference else 3))


def check_snapshots(results):
    snaps = {name: snapshot(result) for name, result in results.items()}
    profiles = {
        "TEST-ISSUE14-KEYS-DEFAULT": "default-utf8",
        "TEST-ISSUE14-KEYS-RNANO": "default-rnano",
        "TEST-ISSUE14-KEYS-RESTRICTED": "default-restricted",
    }
    for suffix, (profile, _args, _lang, _term) in EXTRA_DEFAULT.items():
        profiles["TEST-ISSUE14-KEYS-" + suffix] = profile
    for case, profile in profiles.items():
        actual = snaps[case][1]
        expected = table(profile)
        require(actual == expected, case + " full ordered key table differs")
        print(f"{case}: {len(actual)} ordered key rows PASS")
    require(snaps["TEST-ISSUE14-KEYS-RNANO"][1] ==
            snaps["TEST-ISSUE14-KEYS-RESTRICTED"][1],
            "invocation and explicit restricted tables differ")
    modern = [row for row in table("default-modern") if
              not (row[1] == 19 and row[2] == 128 or
                   row[1] == 17 and row[2] == 32)]
    modern = [(index, *row[1:]) for index, row in enumerate(modern)]
    require(snaps["TEST-ISSUE14-KEYS-MODERN-PRESERVE"][1] == modern,
            "modern/preserve ordered table differs")
    print(f"modern/preserve: {len(modern)} ordered key rows PASS")

    rc, _, strings = snaps["TEST-ISSUE14-RC-ONLY"]
    require(bool(rc["flags"] & (1 << 10)), "rc autoindent absent")
    require((rc["tab"], rc["fill"], rc["guide"], strings.get("wordchars")) ==
            (7, 44, 12, "RC"), "rc-only values differ")
    cli, _, strings = snaps["TEST-ISSUE14-RC-CLI-WINS"]
    require(bool(cli["flags"] & (1 << 10)), "CLI autoindent did not win")
    require((cli["tab"], cli["fill"], cli["guide"], strings.get("wordchars")) ==
            (3, 20, 4, "CLI"), "CLI numeric/string values did not win")
    restricted, _, strings = snaps["TEST-ISSUE14-RC-RESTRICTED"]
    require(not (restricted["flags"] & sum(1 << n for n in (28, 26, 27))),
            "restricted mode did not clear history/backup flags")
    require("operatingdir" not in strings, "restricted rc operatingdir survived")
    print("RC precedence: rc-only, CLI boolean/numeric/string, restricted cleanup PASS")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--binary", type=Path, required=True, help="production candidate ELF")
    ap.add_argument("--hooks-binary", type=Path, required=True, help="test-hooks candidate ELF")
    reference_group = ap.add_mutually_exclusive_group(required=True)
    reference_group.add_argument("--reference", type=Path, help="pinned GNU nano ELF")
    reference_group.add_argument("--recorded-oracles", action="store_true",
                                 help="use pinned recorded CLI probes; no live GNU ELF")
    ap.add_argument("--tiny-hooks-binary", type=Path,
                    help="optional tiny test-hooks ELF for four tiny reference tables")
    ap.add_argument("--out", type=Path, required=True, help="new evidence directory")
    args = ap.parse_args()
    for name in ("binary", "hooks_binary") + (("reference",) if args.reference else ()):
        path = getattr(args, name).resolve()
        require(path.is_file(), f"missing {name}: {path}")
        setattr(args, name, path)
    if args.reference:
        require(hashlib.sha256(args.reference.read_bytes()).hexdigest() == PINNED_REFERENCE_SHA256,
                "GNU reference ELF SHA-256 differs from pinned corpus build")
    prod_info = build_info(args.binary, "")
    hook_info = build_info(args.hooks_binary, "test-hooks")
    for field in ("version", "revision", "source_sha256", "rustc"):
        require(prod_info[field] == hook_info[field], f"candidate build identity differs: {field}")
    args.out.mkdir(parents=True, exist_ok=False)
    identities = {name: {"path": str(getattr(args, name)),
                         "sha256": hashlib.sha256(getattr(args, name).read_bytes()).hexdigest()}
                  for name in ("binary", "hooks_binary") + (("reference",) if args.reference else ())}
    if not args.reference:
        identities["reference"] = {"path": "spec/evidence/cli/cli-probes.json",
                                   "sha256": PINNED_PROBES_SHA256, "mode": "recorded-oracles"}
    identities["binary"]["build_info"] = prod_info
    identities["hooks_binary"]["build_info"] = hook_info
    (args.out / "artifacts.json").write_text(json.dumps(identities, indent=2) + "\n")
    print(json.dumps(identities, indent=2))
    cases = json.loads((ROOT / "tests/issue14/scenarios.json").read_text())
    cases.extend(key_case("TEST-ISSUE14-KEYS-" + suffix, options, lang, term)
                 for suffix, (_profile, options, lang, term) in EXTRA_DEFAULT.items())
    require({case["id"] for case in cases if case["id"] in HOOK_IDS} == HOOK_IDS,
            "hook scenario set incomplete")
    check_cli(args.binary, args.reference, args.out)
    production = [case for case in cases if case["id"] not in HOOK_IDS]
    production.extend([cancellation_case(), rebound_cancel_case(), unbound_control_c_case(),
                       *decoded_cancel_cases()])
    require(production, "no production scenarios")
    (args.out / "production").mkdir()
    production_results = run_harness(production, args.binary, args.out / "production")
    cancelled = production_results["TEST-ISSUE14-SEARCH-CANCEL-BURST"]
    expected_bytes = b"a" * 2_000_000 + b"\n"
    actual_file = cancelled["fixture"]["work/f.txt"]
    require(actual_file["size"] == len(expected_bytes) and
            actual_file["sha256"] == hashlib.sha256(expected_bytes).hexdigest(),
            "search cancellation changed original file")
    print("Production search ^C cancels and discards trailing same-burst X PASS")
    rebound = production_results["TEST-ISSUE14-SEARCH-REBOUND-CANCEL"]
    rebound_file = rebound["fixture"]["work/f.txt"]
    require(rebound_file["size"] == len(expected_bytes) and
            rebound_file["sha256"] == hashlib.sha256(expected_bytes).hexdigest(),
            "rebound search cancellation changed original file")
    unbound = production_results["TEST-ISSUE14-SEARCH-UNBOUND-CONTROL-C"]
    unbound_file = unbound["fixture"]["work/f.txt"]
    require(unbound_file["size"] == len(expected_bytes) and
            unbound_file["sha256"] == hashlib.sha256(expected_bytes).hexdigest(),
            "unbound ^C search case changed original file")
    unbound_raw = (args.out / "production/runs/TEST-ISSUE14-SEARCH-UNBOUND-CONTROL-C/raw-output.bin").read_bytes()
    require(b"Cancelled" not in unbound_raw and b"not found" in unbound_raw,
            "unbound ^C was treated as Cancel or search did not finish")
    print("Production rebound ^G cancels; unbound ^C allows search completion PASS")
    for case in decoded_cancel_cases():
        result = production_results[case["id"]]
        path = args.out / "production/runs" / case["id"] / "raw-output.bin"
        raw = path.read_bytes()
        should_cancel = case["id"] != "TEST-ISSUE14-META-G-PLAIN-G"
        require((b"Cancelled" in raw) == should_cancel,
                case["id"] + " decoded cancellation result differs")
        file = result["fixture"]["work/f.txt"]
        require(file["size"] == len(expected_bytes) and
                file["sha256"] == hashlib.sha256(expected_bytes).hexdigest(),
                case["id"] + " changed the original file")
    print("Production plain g, Meta+g, Meta+Left, raw F1 binding cases PASS")
    timed = production_results["TEST-ISSUE14-QUICKBLANK-TIMEOUT"]["snapshots"]
    message = "\n".join(row["text"] for row in timed["message"]["rows"])
    cleared = "\n".join(row["text"] for row in timed["cleared"]["rows"])
    require('"missing" not found' in message, "quickblank message absent initially")
    require('"missing" not found' not in cleared,
            "quickblank message survived 1.2 second timed wait")
    print("Production quickblank message clears after timed wait PASS")
    (args.out / "hooks").mkdir()
    hooks = run_harness([case for case in cases if case["id"] in HOOK_IDS],
                        args.hooks_binary, args.out / "hooks")
    check_snapshots(hooks)
    if args.tiny_hooks_binary:
        tiny = args.tiny_hooks_binary.resolve()
        require(tiny.is_file(), "missing tiny hooks binary")
        tiny_info = build_info(tiny, "test-hooks,tiny")
        for field in ("version", "revision", "source_sha256", "rustc"):
            require(prod_info[field] == tiny_info[field], f"tiny build identity differs: {field}")
        identities["tiny_hooks_binary"] = {
            "path": str(tiny), "sha256": hashlib.sha256(tiny.read_bytes()).hexdigest(),
            "build_info": tiny_info}
        (args.out / "artifacts.json").write_text(json.dumps(identities, indent=2) + "\n")
        tiny_profiles = {
            "C": ("tiny-C", [], "C"),
            "UTF8": ("tiny-utf8", [], "en_US.UTF-8"),
            "MODERN": ("tiny-modern", ["--modernbindings"], "en_US.UTF-8"),
            "RESTRICTED": ("tiny-restricted", ["--restricted"], "en_US.UTF-8"),
        }
        tiny_cases = [key_case("TEST-ISSUE14-TINY-" + suffix, options, lang)
                      for suffix, (_profile, options, lang) in tiny_profiles.items()]
        (args.out / "tiny").mkdir()
        tiny_results = run_harness(tiny_cases, tiny, args.out / "tiny")
        for suffix, (profile, _options, _lang) in tiny_profiles.items():
            actual = snapshot(tiny_results["TEST-ISSUE14-TINY-" + suffix])[1]
            expected = table(profile)
            require(actual == expected, profile + " complete ordered table differs")
            print(f"{profile}: {len(actual)} ordered key rows PASS")
    print("Issue #14 selected runtime assertions PASS; scope: exact artifacts.json")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, KeyError, ValueError) as exc:
        print("FAIL:", exc, file=sys.stderr)
        sys.exit(1)
