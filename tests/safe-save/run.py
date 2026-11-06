#!/usr/bin/env python3
"""Run real save syscall faults in disposable Linux fixtures.
Pass the executable from cargo test --no-run --message-format=json.
--out must be fresh. No terminal, credentials, or user documents are used.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import subprocess

OLD = b"original data must survive\n"
NEW = b"replacement\n"
PRE = ("open", "zero", "eio", "enospc", "partial-eio", "file-sync", "close", "rename", "metadata")
SUCCESS = ("none", "short", "eintr", "sync-eintr", "read-eintr")
CRASH = ("exit-write", "exit-file-sync", "exit-close", "exit-rename", "exit-committed", "exit-dir-sync")


def run_case(binary, preload, root, mode, fault, kind):
    data = root / "data"
    data.mkdir(parents=True)
    target = data / "target"
    sentinel = data / ".naro-save-unrelated"
    sentinel.write_bytes(b"unrelated")
    if kind not in ("new", "collision"):
        target.write_bytes(OLD)
        target.chmod(0o640)
        os.utime(target, ns=(1_000_000_000, 2_000_000_000))
    if kind == "group":
        group = next(g for g in os.getgroups() if g != os.getgid())
        os.chown(target, -1, group)
    if kind == "hardlink":
        os.link(target, data / "other")
    if kind in ("symlink", "dangling"):
        target.rename(data / "other")
        target.symlink_to("other" if kind == "symlink" else "missing")
    attrs = {}
    if kind == "xattr":
        attrs["user.naro-test"] = b"fixture metadata\0binary"
    if kind == "acl":
        attrs["system.posix_acl_access"] = struct.pack("<I", 2) + b"".join(
            struct.pack("<HHI", t, p, u) for t, p, u in
            ((1, 6, 0xffffffff), (2, 4, os.getuid()+1), (4, 4, 0xffffffff),
             (16, 4, 0xffffffff), (32, 0, 0xffffffff)))
    for name, value in attrs.items():
        os.setxattr(target, name, value)
    before = target.stat() if target.exists() else None
    env = dict(os.environ, LD_PRELOAD=str(preload), NARO_SAVE_FIXTURE=str(root),
               NARO_SAVE_MODE=str(mode), NARO_SAVE_FAULT=fault)
    if kind == "collision":
        env["NARO_SAVE_COLLISION"] = "1"
    proc = subprocess.run([str(binary), "--exact", "files::safe_save_tests::fixture_save", "--nocapture"],
                          env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10, umask=0o027)
    (root / "process.log").write_bytes(proc.stdout)
    result = (root / "result").read_text() if (root / "result").exists() else ""
    events = (root / "events").read_text().splitlines() if (root / "events").exists() else []
    if kind == "collision":
        target = Path((root / "destination").read_text())
    crash = fault in CRASH
    rejected = kind in ("symlink", "dangling") or (kind in ("new", "collision") and mode == 2)
    committed = not rejected and (fault in SUCCESS or fault in ("dir-sync", "exit-committed", "exit-dir-sync"))
    assert proc.returncode == (99 if crash and not rejected else 0), (proc.returncode, proc.stdout)
    expected = NEW if mode == 0 or kind in ("new", "collision") else OLD + NEW if mode == 1 else NEW + OLD
    if rejected:
        assert result.startswith("error "), result
        if kind in ("symlink", "dangling"):
            assert target.is_symlink()
            assert (data / "other").read_bytes() == OLD
        else:
            assert not target.exists()
    elif committed:
        assert target.read_bytes() == expected
        assert stat.S_IMODE(target.stat().st_mode) == 0o640
        if before:
            after = target.stat()
            assert (after.st_uid, after.st_gid) == (before.st_uid, before.st_gid)
            assert after.st_ino != before.st_ino
            assert after.st_mtime_ns != before.st_mtime_ns
        for name, value in attrs.items():
            assert os.getxattr(target, name) == value
        if fault in SUCCESS:
            assert result.startswith("ok "), result
            assert ("modified=false" if mode == 0 else "modified=true") in result
            for event in ("file-sync", "close", "rename", "committed", "dir-sync"):
                assert event in events, events
            assert events.index("file-sync") < events.index("close") < events.index("rename") < events.index("dir-sync"), events
        elif not crash:
            assert result.startswith("error ") and "modified=true" in result, result
            assert "File replaced, but durability is uncertain" in result, result
    else:
        if before:
            assert target.read_bytes() == OLD, (fault, target.read_bytes())
            assert target.stat().st_ino == before.st_ino
            assert target.stat().st_mtime_ns == before.st_mtime_ns
        else:
            assert not target.exists()
        if not crash:
            assert result.startswith("error ") and "modified=true" in result, result
    if kind == "hardlink":
        assert (data / "other").read_bytes() == OLD
        assert (data / "other").stat().st_ino == before.st_ino
    assert sentinel.read_bytes() == b"unrelated"
    leftovers = [p for p in data.iterdir() if p.name.startswith(".naro-save-") and p != sentinel and p != target]
    if not crash:
        assert not leftovers, leftovers
    for path in leftovers:
        assert path.is_file() and not path.is_symlink()
    return {"result": result.strip(), "events": events, "crash_temp_count": len(leftovers)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--binary", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--regression-only", action="store_true")
    args = ap.parse_args()
    binary = args.binary.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    out = args.out.resolve()
    preload = out / "faults.so"
    command = ["cc", "-shared", "-fPIC", "-Wall", "-Wextra", "-Werror", str(Path(__file__).with_name("faults.c")), "-ldl", "-o", str(preload)]
    subprocess.run(command, check=True)
    cases = []
    skips = []
    for mode in range(3):
        kinds = ("existing",) if args.regression_only else ("existing", "new", "hardlink", "symlink", "dangling", "xattr", "acl", "group", "collision")
        for kind in kinds:
            if kind == "group" and not any(g != os.getgid() for g in os.getgroups()):
                skips.append({"mode": mode, "kind": kind, "reason": "no supplementary group available"})
                continue
            faults = ("file-sync",) if args.regression_only else SUCCESS + PRE + ("dir-sync",) + CRASH
            if not args.regression_only:
                if mode and kind not in ("new", "collision", "symlink", "dangling"):
                    faults += ("read-eio",)
                if kind in ("xattr", "acl"):
                    faults += ("xattr",)
            for fault in faults:
                if (kind in ("symlink", "dangling") or (kind in ("new", "collision") and mode == 2)) and fault != "none":
                    continue
                if fault == "read-eintr" and (not mode or kind in ("new", "collision")):
                    continue
                row = {"mode": mode, "kind": kind, "fault": fault}
                try:
                    row.update(run_case(binary, preload, out / f"mode{mode}-{kind}-{fault}", mode, fault, kind))
                    row["status"] = "pass"
                except Exception as error:
                    row.update(status="fail", error=repr(error))
                cases.append(row)
                print(f"{row['status']}: {mode} {kind} {fault}" + (f" {row['error']}" if "error" in row else ""), flush=True)
    report = {"binary": str(binary), "sha256": hashlib.sha256(binary.read_bytes()).hexdigest(), "compiler_command": command,
              "cases": cases, "skips": skips, "passed": sum(r["status"] == "pass" for r in cases), "total": len(cases)}
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"{report['passed']}/{report['total']} passed")
    return int(report["passed"] != report["total"])


if __name__ == "__main__":
    raise SystemExit(main())
