#!/usr/bin/env python3
"""Run host qualification using an immutable, explicitly supplied frozen binary.

All source-checking and variant builds happen in a private checkout under --out.
The frozen source tree and default candidate are never build targets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
from frozen_process import make_private_tmux_tmpdir, remove_private_tmux_tmpdir, run_owned_process

CANONICAL_NANOSPEC_WORK = Path("/tmp/nanospec-work")

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=path, text=True).strip()


def required_identity_review_stages(python: str, candidate: Path, out: Path) -> list[tuple[str, list[str]]]:
    """Commands for collector-required source and frozen-binary review stages.

    The launcher executes this exact list, and its unit test inspects these
    commands so a successful checkpoint cannot omit an entire required stage.
    """
    return [
        ("rust-default", ["cargo", "test", "--locked", "--offline"]),
        ("identity-expectations-unit", [python, "spec/tools/test_candidate_expectations.py"]),
        ("branding", [python, "tools/check_branding.py", "--binary", str(candidate),
                      "--out", str(out / "branding")]),
        ("identity-layout", [python, "spec/tools/nanoharness.py", "tests/naro/identity-layout.json",
                             "--candidate-expectations", "--binary", str(candidate),
                             "--out", str(out / "identity-layout")]),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True, help="clean detached frozen source checkout")
    parser.add_argument("--binary", type=Path, required=True, help="frozen default-feature host candidate")
    parser.add_argument("--reference", type=Path, required=True, help="pinned host GNU nano executable")
    parser.add_argument("--root-reference", type=Path, required=True, help="pinned isolated-root GNU nano executable")
    parser.add_argument("--freeze-manifest", type=Path, required=True, help="freeze.json binding all inputs")
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory; must not exist")
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=3600)
    args = parser.parse_args()

    source = args.source_dir.resolve(strict=True)
    binary = args.binary.resolve(strict=True)
    reference = args.reference.resolve(strict=True)
    root_reference = args.root_reference.resolve(strict=True)
    freeze_manifest_path = args.freeze_manifest.resolve(strict=True)
    out = args.out.absolute()
    if out.resolve().is_relative_to(source):
        parser.error("--out must be outside the frozen source checkout")
    if out.exists():
        parser.error(f"preserve evidence: output already exists: {out}")
    if args.jobs < 1 or args.jobs > 64 or args.timeout < 10:
        parser.error("jobs must be 1..64 and timeout must be at least 10 seconds")

    manifest = json.loads(freeze_manifest_path.read_text(encoding="utf-8"))
    source_commit = manifest["source_commit"]
    if git(source, "rev-parse", "HEAD") != source_commit:
        parser.error("source HEAD does not match freeze manifest")
    if git(source, "status", "--porcelain", "--untracked-files=all"):
        parser.error("source checkout is not clean")
    source_tree = git(source, "rev-parse", "HEAD^{tree}")
    if source_tree != manifest.get("source_tree"):
        parser.error("source tree does not match freeze manifest")

    expected = {
        "binary": manifest["host_binary_sha256"],
        "reference": manifest["host_reference_sha256"],
        "root_reference": manifest["files"]["references/host-root/nano"],
    }
    actual = {"binary": sha256(binary), "reference": sha256(reference), "root_reference": sha256(root_reference)}
    if actual != expected:
        parser.error(f"input hash mismatch: actual={actual}, expected={expected}")
    info = json.loads(subprocess.check_output([str(binary)], env={**os.environ, "NARO_BUILD_INFO": "1"}, text=True))
    if info.get("revision") != source_commit or info.get("source_sha256") != manifest["production_source_sha256"]:
        parser.error("frozen candidate build info does not match source manifest")
    if info.get("features") != "":
        parser.error("default frozen candidate must have an empty feature list")

    out.mkdir(parents=True, exist_ok=False)
    for name, path in (("naro", binary), ("reference.bin", reference), ("root-reference.bin", root_reference)):
        shutil.copy2(path, out / name)
    work = out / "work"
    work.mkdir()
    tmux_tmpdir, tmux_owner = make_private_tmux_tmpdir()
    private_source = work / "source"
    subprocess.run(["git", "clone", "--no-hardlinks", "--no-checkout", str(source), str(private_source)], check=True)
    subprocess.run(["git", "-C", str(private_source), "checkout", "--detach", source_commit], check=True)
    if git(private_source, "status", "--porcelain", "--untracked-files=all"):
        raise SystemExit("private source checkout is not clean after creation")
    root_slot = private_source / "target/root-reference/install/bin/nano"
    root_slot.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out / "root-reference.bin", root_slot)

    env = os.environ.copy()
    env.update({
        "PATH": str(Path.home() / ".cargo/bin") + os.pathsep + env.get("PATH", ""),
        "CARGO_NET_OFFLINE": "true",
        "CARGO_TARGET_DIR": str(work / "target/checks"),
        "NANOSPEC_WORK": str(CANONICAL_NANOSPEC_WORK),
        "TMUX_TMPDIR": str(tmux_tmpdir),
        "PYTHONDONTWRITEBYTECODE": "1",
        "RUSTUP_TOOLCHAIN": env.get("RUSTUP_TOOLCHAIN", "stable-x86_64-unknown-linux-gnu"),
    })
    Path(env["NANOSPEC_WORK"]).mkdir(parents=True, exist_ok=True)
    candidate = out / "naro"
    nano = out / "reference.bin"
    package_version = subprocess.check_output(
        [sys.executable, "-c", "import tomllib;print(tomllib.load(open('Cargo.toml','rb'))['package']['version'])"],
        cwd=private_source, text=True,
    ).strip()
    report = {
        "schema": 1,
        "state": "running",
        "source_commit": source_commit,
        "source_tree": source_tree,
        "production_source_sha256": manifest["production_source_sha256"],
        "verification_sha256": manifest["verification_sha256"],
        "tmux_tmpdir": str(tmux_tmpdir),
        "tmux_owner_token": tmux_owner,
        "nanospec_work": str(CANONICAL_NANOSPEC_WORK),
        "binary_sha256": actual["binary"],
        "reference_sha256": actual["reference"],
        "root_reference_sha256": actual["root_reference"],
        "build": info,
        "candidate_build_info": info,
        "reference_runs": str(out / "reference"),
        "inputs": {name: {"path": str(path), "sha256": actual[name]} for name, path in (("binary", binary), ("reference", reference), ("root_reference", root_reference))},
        "checks": {},
    }

    def save() -> None:
        temp = out / "checkpoint.tmp"
        temp.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        temp.replace(out / "checkpoint.json")

    def run(name: str, command: list[str], *, cwd: Path = private_source, extra_env: dict[str, str] | None = None) -> None:
        report["active"] = name
        save()
        started = time.time()
        child_env = env | (extra_env or {})
        log_path = out / f"{name}.log"
        outcome = run_owned_process(command, cwd=cwd, env=child_env, log_path=log_path,
                                    timeout=args.timeout, tmux_tmpdir=tmux_tmpdir)
        status = int(outcome["status"])
        leftover = [item for item in outcome["owned_tmux_cleanup"]
                    if item.get("socket") and item.get("socket_removed") is False]
        if leftover and status == 0:
            status = 125
            outcome["cleanup_failure"] = leftover
        report["checks"][name] = {**outcome, "status": status,
                                  "seconds": round(time.time() - started, 2), "command": command}
        save()
        print(f"{name}: {status}", flush=True)
        if status:
            report["state"] = "failed"
            report["active"] = None
            save()
            raise SystemExit(status)

    def py(name: str, script: str, *argv: object) -> None:
        run(name, [sys.executable, script, *map(str, argv)])

    def py_env(name: str, script: str, *argv: object, extra_env: dict[str, str]) -> None:
        run(name, [sys.executable, script, *map(str, argv)], extra_env=extra_env)

    checks = [
        ("fmt", ["cargo", "fmt", "--check"]),
        ("clippy", ["cargo", "clippy", "--locked", "--offline", "--all-targets", "--all-features", "--", "-D", "warnings"]),
        ("rust", ["cargo", "test", "--locked", "--offline", "--all-features"]),
    ]
    for name, command in checks:
        run(name, command)
    for name, command in required_identity_review_stages(sys.executable, candidate, out):
        run(name, command)
    for name, script in (("comparator", "spec/tools/test_compare_runs.py"),
                         ("harness", "spec/tools/test_nanoharness.py"),
                         ("namespace", "spec/tools/test_namespace_exec.py"),
                         ("identity-review-unit", "spec/tools/test_identity_review.py")):
        py(name, script)
    for name, script in (("gate-evidence-unit", "tools/test_release_gate_evidence.py"),
                         ("console-identity-unit", "tools/test_console_identity.py"),
                         ("frozen-launcher-unit", "tools/test_frozen_launchers.py"),
                         ("frozen-process-unit", "tools/test_frozen_process.py")):
        py(name, script)
    run("console-unit", [sys.executable, "-m", "unittest", "discover", "-s", "tests/console", "-p", "test_*.py"])
    run("closure-unit", [sys.executable, "-m", "unittest", "discover", "-s", "tools", "-p", "test_closure_regressions.py"])

    cases = []
    for scenario_path in sorted((private_source / "spec/evidence/scenarios").glob("*.json")):
        for case in json.loads(scenario_path.read_text(encoding="utf-8")):
            if case.get("profile") == "tiny" or any(str(arg).startswith("/") for arg in case.get("args", [])) or case["id"] == "TEST-BROWSE-003":
                continue
            cases.append(case)
    if len(cases) != 303:
        parser.error(f"expected 303 selected default reference cases, found {len(cases)}")
    reference_cases = out / "reference-cases.json"
    reference_cases.write_text(json.dumps(cases, indent=1) + "\n", encoding="utf-8")
    report["fresh_reference_replay"] = {
        "case_count": len(cases),
        "scenario_sha256": sha256(reference_cases),
        "reference_runs": str(out / "reference"),
        "excluded": {"profile": "tiny", "absolute_arguments": True, "id": "TEST-BROWSE-003"},
    }
    save()
    py("reference-replay", "tools/replay_reference.py", "--scenarios", reference_cases,
       "--binary", nano, "--out", out / "reference")
    py_env("terminal", "tools/validate_parallel.py", "--binary", candidate,
           "--out", out / "terminal", "--jobs", args.jobs,
           extra_env={"NARO_REFERENCE_RUNS": str(out / "reference")})
    for suite in ("tools", "edges", "environments", "supplement", "backup", "fifo-eof",
                  "signal-SIGTERM", "signal-SIGHUP", "vt-ioctl", "root", "root-nohome-tilde"):
        extra = ["--reference", out / "root-reference.bin"] if suite.startswith("root") else ["--reference", nano]
        py(suite, "tools/check_follow_up.py", "--suite", suite, "--binary", candidate,
           *extra, "--out", out / suite)
    sys.path.insert(0, str(private_source / "tools"))
    from check_closure_regressions import SUITES
    for suite in SUITES:
        py(suite, "tools/check_follow_up.py", "--suite", suite,
           "--binary", candidate, "--reference", nano, "--out", out / suite)
    py("closure-regressions", "tools/check_closure_regressions.py", "--base", out,
       "--binary", candidate, "--reference", nano)
    py("extras", "tools/check_environment_extras.py", "--binary", candidate, "--reference", nano,
       "--out", out / "extras")
    py("cli", "tools/check_cli.py", "--binary", candidate, "--out", out / "cli")

    for variant, flags in (("hooks", ["--features", "test-hooks"]), ("credits", ["--release", "--features", "credits"])):
        target_dir = work / "variants" / variant
        run(f"{variant}-build", ["cargo", "build", "--locked", "--offline", *flags, "--target-dir", str(target_dir)],
            extra_env={"CARGO_TARGET_DIR": str(target_dir)})
        variant_binary = target_dir / ("release" if "--release" in flags else "debug") / "naro"
        variant_info = json.loads(subprocess.check_output([str(variant_binary)],
                                                         env=env | {"NARO_BUILD_INFO": "1"}, text=True))
        expected_features = "credits" if variant == "credits" else "test-hooks"
        if variant_info.get("revision") != source_commit or variant_info.get("source_sha256") != manifest["production_source_sha256"] or variant_info.get("features") != expected_features:
            raise SystemExit(f"{variant} variant identity mismatch: {variant_info}")
        report.setdefault("variant_builds", {})[variant] = {
            "path": str(variant_binary),
            "sha256": sha256(variant_binary),
            "features": variant_info["features"],
            "build_info": variant_info,
            "target_directory": str(target_dir),
        }
        save()
    py("panic", "spec/tools/nanoharness.py", "tests/follow-up/scenarios/panic.json",
       "--candidate-expectations", "--binary", work / "variants/hooks/debug/naro", "--out", out / "panic")
    py("extensions", "tools/check_extensions.py", "--default", candidate,
       "--credits", work / "variants/credits/release/naro", "--panic-runs", out / "panic",
       "--out", out / "extensions")
    py("large", "tools/check_large_files.py", "--binary", candidate, "--out", out / "large")
    py("package", "tools/package.py", "--binary", candidate, "--out", out / "package")
    archive = out / "package" / f"naro-{package_version}-x86_64-unknown-linux-gnu.tar.gz"
    source_archive = out / "package" / f"naro-{package_version}-source.tar.gz"
    py("package-check", "tools/check_package.py", "--archive", archive,
       "--source-archive", source_archive, "--out", out / "package-check")

    final_status = git(private_source, "status", "--porcelain", "--untracked-files=all")
    report["private_source_status_after_checks"] = final_status
    final_tmux_cleanup = run_owned_process(["true"], cwd=private_source, env=env,
                                           log_path=out / "tmux-final-cleanup.log", timeout=10,
                                           tmux_tmpdir=tmux_tmpdir)
    report["tmux_final_cleanup"] = final_tmux_cleanup
    if final_tmux_cleanup["status"] != 0 or any(item.get("socket_removed") is False for item in final_tmux_cleanup["owned_tmux_cleanup"]):
        report["state"] = "failed"
        report["active"] = None
        save()
        raise SystemExit(125)
    try:
        remove_private_tmux_tmpdir(tmux_tmpdir, tmux_owner)
    except Exception as error:
        report["state"] = "failed"
        report["active"] = None
        report["tmux_tmpdir_cleanup_error"] = f"{type(error).__name__}: {error}"
        save()
        raise SystemExit(125)
    report["tmux_tmpdir_removed"] = True
    report["state"] = "complete"
    report["active"] = None
    save()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
