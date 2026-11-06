#!/usr/bin/env python3
"""Exercise emergency-save UI and disk outcomes in private PTYs (Linux).

Requires a test-hooks build and reuses the fixture-bounded safe-save syscall
interposer. Every output directory must be new. No installed editor is used.
"""
import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import pty
import select
import signal
import stat
import subprocess
import time

REPO = Path(__file__).resolve().parents[2]
OLD = b"original\n"
NEW = b"Xoriginal\n"
SUCCESS = ("none", "short", "eintr", "sync-eintr")
ERRORS = {"open": "create", "eio": "write", "enospc": "write",
          "zero": "write", "partial-eio": "write", "file-sync": "file sync",
          "close": "file close", "dir-sync": "directory sync"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(binary, preload, root, fault, trigger, kind, tiny):
    data = root / "data"
    data.mkdir(parents=True)
    (root / "home").mkdir()
    hook = root / "hook"
    hook.mkdir()
    original = data / "f.txt"
    original.write_bytes(OLD)
    if kind == "collision":
        (data / "f.txt.save").write_bytes(b"older recovery\n")
    args = [str(binary)] + ([] if tiny else ["-I"])
    if kind == "restricted":
        args.append("--restricted")
    if kind != "nameless":
        args.append("f.txt" if kind == "relative" else str(original))
    env = dict(os.environ, TERM="xterm-256color", LC_ALL="C.UTF-8",
               HOME=str(root / "home"), XDG_CONFIG_HOME=str(root / "home"),
               LD_PRELOAD=str(preload), NARO_SAVE_FIXTURE=str(root),
               NARO_SAVE_FAULT=fault, NARO_TEST_PANIC_DIR=str(hook))
    trace = bytearray()
    stderr_path = root / "stderr"
    pid, master = pty.fork()
    if pid == 0:
        os.chdir(data)
        fd = os.open(stderr_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.dup2(fd, 2)
        os.close(fd)
        os.execve(binary, args, env)
    status = None

    def drain():
        if select.select([master], [], [], 0.02)[0]:
            try:
                trace.extend(os.read(master, 65536))
            except OSError as error:
                if error.errno != errno.EIO:
                    raise

    try:
        deadline = time.monotonic() + 8
        while b"^X" not in trace and time.monotonic() < deadline:
            drain()
        assert b"^X" in trace, "editor startup timeout"
        if kind != "unmodified":
            os.write(master, b"X")
            while not (hook / "ready").exists() and time.monotonic() < deadline:
                drain()
            assert (hook / "ready").exists(), "modified acknowledgment timeout"
        if trigger == "panic":
            (hook / "trigger").write_text("panic\n")
        else:
            os.kill(pid, getattr(signal, trigger))
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            drain()
            waited, code = os.waitpid(pid, os.WNOHANG)
            if waited:
                status = os.waitstatus_to_exitcode(code)
                break
        assert status is not None, "editor exit timeout"
    finally:
        if status is None:
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)
        os.close(master)
        (root / "terminal.raw").write_bytes(trace)
    stderr = stderr_path.read_text()
    events = (root / "events").read_text().splitlines() if (root / "events").exists() else []
    target = data / (f"nano.{pid}.save" if kind == "nameless" else
                     "f.txt.save.1" if kind == "collision" else "f.txt.save")
    checks = {}
    checks["exit-status"] = status == 1
    checks["fatal-diagnostic"] = ("Sorry! NARO crashed!" if trigger == "panic" else
                                   "Received SIGHUP or SIGTERM") in stderr
    checks["original-preserved"] = original.read_bytes() == OLD
    skipped = kind in ("restricted", "unmodified")
    checks["recovery-exists"] = target.exists() == (not skipped and fault != "open")
    if target.exists():
        expected = (b"" if fault in ("eio", "enospc", "zero") else
                    NEW[:2] if fault == "partial-eio" else
                    b"X\n" if kind == "nameless" else NEW)
        checks["recovery-bytes"] = target.read_bytes() == expected
        checks["private-permissions"] = stat.S_IMODE(target.stat().st_mode) == 0o600
    if skipped:
        checks["silent-skip"] = "Buffer written to" not in stderr and "Emergency save failed" not in stderr
    elif fault in SUCCESS:
        checks["success-ui"] = f"Buffer written to {target.name if kind in ('relative', 'nameless') else target}" in stderr
        checks["no-error-ui"] = "Emergency save failed" not in stderr
        stages = [event for event in events if event in ("write", "file-sync", "close", "dir-sync")]
        checks["durability-order"] = all(stage in stages for stage in ("write", "file-sync", "close", "dir-sync")) and stages.index("write") < stages.index("file-sync") < stages.index("close") < stages.index("dir-sync")
    else:
        checks["no-success-ui"] = "Buffer written to" not in stderr
        checks["stage-error-ui"] = "Emergency save failed for" in stderr and f"({ERRORS[fault]})" in stderr
        checks["uncertainty-ui"] = "may be incomplete or not durable" in stderr
        event = {"open": "open", "eio": "write", "enospc": "write", "zero": "write",
                 "partial-eio": "write", "file-sync": "file-sync", "close": "close", "dir-sync": "dir-sync"}[fault]
        checks["fault-reached"] = event in events
    if kind == "collision":
        checks["older-recovery-preserved"] = (data / "f.txt.save").read_bytes() == b"older recovery\n"
    return dict(fault=fault, trigger=trigger, kind=kind, exit_status=status,
                checks=checks, passed=all(checks.values()), stderr=stderr, events=events,
                recovery_sha256=digest(target) if target.exists() else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--regression-only", action="store_true")
    parser.add_argument("--tiny", action="store_true", help="tiny has no rcfile or -I option")
    args = parser.parse_args()
    binary = args.binary.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    preload = out / "faults.so"
    compile_command = ["cc", "-shared", "-fPIC", "-Wall", "-Wextra", "-o", str(preload),
                       str(REPO / "tests/safe-save/faults.c"), "-ldl"]
    subprocess.run(compile_command, check=True)
    cases = [(fault, trigger, "named") for trigger in ("panic", "SIGHUP", "SIGTERM")
             for fault in (*SUCCESS, *ERRORS)]
    cases += [("none", "panic", kind) for kind in ("relative", "nameless", "collision", "restricted")]
    cases += [("none", "SIGTERM", "unmodified")]
    if args.regression_only:
        cases = [(fault, "panic", "named") for fault in ("file-sync", "dir-sync", "close")]
    results = []
    for fault, trigger, kind in cases:
        name = f"{trigger}-{kind}-{fault}"
        result = run_case(binary, preload, out / name, fault, trigger, kind, args.tiny)
        results.append(dict(name=name, **result))
        print(f"{name}: {'PASS' if result['passed'] else 'FAIL'}", flush=True)
    report = dict(binary=str(binary), binary_sha256=digest(binary), tiny=args.tiny,
                  driver_sha256=digest(Path(__file__)), compile_command=compile_command,
                  interposer_source_sha256=digest(REPO / "tests/safe-save/faults.c"),
                  interposer_sha256=digest(preload), passed=sum(r["passed"] for r in results),
                  total=len(results), results=results)
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"{report['passed']}/{report['total']} passed")
    raise SystemExit(0 if report["passed"] == report["total"] else 1)


if __name__ == "__main__":
    main()
