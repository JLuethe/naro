#!/usr/bin/env python3
"""Run real save syscall faults in disposable Linux fixtures.
Pass the executable from cargo test --no-run --message-format=json.
--out must be fresh. No terminal, credentials, or user documents are used.
"""
import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import subprocess

OLD = b"original data must survive\n"
NEW = b"replacement\n"
PRE = ("open", "zero", "eio", "enospc", "partial-eio", "file-sync", "close", "rename", "metadata", "source-close")
SUCCESS = ("none", "short", "eintr", "sync-eintr", "read-eintr")
CRASH = ("exit-write", "exit-file-sync", "exit-close", "exit-rename", "exit-committed", "exit-dir-sync",
         "exit-stage-sync", "exit-parent-sync", "exit-stage-remove", "exit-final-parent-sync")
POST = ("dir-sync", "stage-sync", "parent-sync", "stage-remove", "final-parent-sync", "directory-close")


class MissingFixturePrerequisite(Exception):
    """The disposable fixture cannot be constructed on this host."""


def fixture_metadata(operation, call, *args):
    try:
        return call(*args)
    except OSError as error:
        # These failures occur while constructing the synthetic ACL/group
        # fixture, before the editor or fault hook is launched. Never treat an
        # EINVAL from the product operation as a missing prerequisite.
        if error.errno in (errno.EINVAL, errno.ENOTSUP, errno.EOPNOTSUPP):
            raise MissingFixturePrerequisite(f"{operation}: {error}") from error
        raise


def planned_cases(regression_only):
    for mode in range(3):
        kinds = (("existing",) if regression_only else
                 ("existing", "new", "new-default-acl", "hardlink", "symlink", "dangling",
                  "xattr", "acl", "group", "collision"))
        for kind in kinds:
            faults = ("file-sync",) if regression_only else SUCCESS + PRE + POST + CRASH
            if not regression_only:
                if mode and kind not in ("new", "collision", "new-default-acl", "symlink", "dangling"):
                    faults += ("read-eio",)
                if kind in ("xattr", "acl"):
                    faults += ("xattr",)
            for fault in faults:
                if (kind in ("symlink", "dangling") or
                        (kind in ("new", "collision", "new-default-acl") and mode == 2)) and fault != "none":
                    continue
                if fault == "source-close" and kind in ("new", "collision", "new-default-acl"):
                    continue
                if fault == "read-eintr" and (not mode or kind in ("new", "collision", "new-default-acl")):
                    continue
                yield mode, kind, fault


def run_case(binary, preload, root, mode, fault, kind):
    data = root / "data"
    data.mkdir(parents=True)
    target = data / "target"
    new_kind = kind in ("new", "collision", "new-default-acl")
    direct_acl = None
    if kind == "new-default-acl":
        default_acl = struct.pack("<I", 2) + b"".join(
            struct.pack("<HHI", t, p, u) for t, p, u in
            ((1, 7, 0xffffffff), (2, 4, os.getuid()+1), (4, 5, 0xffffffff),
             (16, 5, 0xffffffff), (32, 0, 0xffffffff)))
        fixture_metadata("default ACL setup", os.setxattr, data, "system.posix_acl_default", default_acl)
        direct = data / "direct"
        direct.touch(mode=0o666)
        direct_acl = fixture_metadata("inherited ACL probe", os.getxattr, direct, "system.posix_acl_access")
        direct_mode = stat.S_IMODE(direct.stat().st_mode)
    sentinel = data / ".naro-save-unrelated"
    sentinel.write_bytes(b"unrelated")
    if not new_kind:
        target.write_bytes(OLD)
        target.chmod(0o640)
        os.utime(target, ns=(1_000_000_000, 2_000_000_000))
    if kind == "group":
        group = next(g for g in os.getgroups() if g != os.getgid())
        fixture_metadata("supplementary group setup", os.chown, target, -1, group)
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
        if name == "system.posix_acl_access":
            fixture_metadata("access ACL setup", os.setxattr, target, name, value)
        else:
            os.setxattr(target, name, value)
    before = target.stat() if target.exists() else None
    env = dict(os.environ, LD_PRELOAD=str(preload), NARO_SAVE_FIXTURE=str(root),
               NARO_SAVE_MODE=str(mode), NARO_SAVE_FAULT=fault)
    if kind == "collision":
        env["NARO_SAVE_COLLISION"] = "1"
    proc = subprocess.run([str(binary), "--exact", "files::safe_save_tests::fixture_save", "--ignored", "--nocapture"],
                          env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10, umask=0o027)
    (root / "process.log").write_bytes(proc.stdout)
    result = (root / "result").read_text() if (root / "result").exists() else ""
    events = (root / "events").read_text().splitlines() if (root / "events").exists() else []
    if kind == "collision":
        target = Path((root / "destination").read_text())
    crash = fault in CRASH
    rejected = kind in ("symlink", "dangling") or (new_kind and mode == 2)
    committed = not rejected and (fault in SUCCESS or fault in POST or fault.startswith("exit-") and fault not in
                 ("exit-write", "exit-file-sync", "exit-close", "exit-rename"))
    assert proc.returncode == (99 if crash and not rejected else 0), (proc.returncode, proc.stdout)
    expected = NEW if mode == 0 or new_kind else OLD + NEW if mode == 1 else NEW + OLD
    if rejected:
        assert result.startswith("error "), result
        if kind in ("symlink", "dangling"):
            assert target.is_symlink()
            assert (data / "other").read_bytes() == OLD
        else:
            assert not target.exists()
    elif committed:
        assert target.read_bytes() == expected
        assert stat.S_IMODE(target.stat().st_mode) == (direct_mode if direct_acl is not None else 0o640)
        if direct_acl is not None:
            assert os.getxattr(target, "system.posix_acl_access") == direct_acl
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
            for event in ("file-sync", "close", "rename", "committed", "dir-sync", "stage-sync", "parent-sync", "stage-remove", "final-parent-sync"):
                assert event in events, events
            assert events.index("file-sync") < events.index("close") < events.index("rename") < events.index("stage-sync") < events.index("parent-sync") < events.index("stage-remove") < events.index("final-parent-sync"), events
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
    if not rejected and not crash and fault in ("source-close", "directory-close"):
        assert fault in events, (fault, events)
        if fault == "source-close":
            assert events.index("close") < events.index("source-close") and "rename" not in events, events
        else:
            assert events.index("rename") < events.index("dir-sync") < events.index("directory-close"), events
    assert sentinel.read_bytes() == b"unrelated"
    leftovers = [p for p in data.iterdir() if p.name.startswith(".naro-save-") and p != sentinel and p != target]
    if not crash:
        assert not leftovers, leftovers
    for path in leftovers:
        assert path.is_dir() and not path.is_symlink(), path
        assert stat.S_IMODE(path.stat().st_mode) == 0o700, path
        entries = list(path.iterdir())
        if fault in ("exit-committed", "exit-dir-sync", "exit-stage-sync", "exit-parent-sync", "exit-stage-remove"):
            assert not entries, entries
        else:
            assert len(entries) == 1 and entries[0].name == "content", entries
            assert entries[0].is_file() and not entries[0].is_symlink()
    return {"result": result.strip(), "events": events, "crash_stage_count": len(leftovers)}


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
    planned = list(planned_cases(args.regression_only))
    cases = []
    for mode, kind, fault in planned:
        row = {"mode": mode, "kind": kind, "fault": fault}
        if kind == "group" and not any(g != os.getgid() for g in os.getgroups()):
            row.update(status="missing-prerequisite", error="no supplementary group available")
        else:
            try:
                row.update(run_case(binary, preload, out / f"mode{mode}-{kind}-{fault}", mode, fault, kind))
                row["status"] = "pass"
            except MissingFixturePrerequisite as error:
                row.update(status="missing-prerequisite", error=str(error))
            except Exception as error:
                row.update(status="fail", error=repr(error))
        cases.append(row)
        print(f"{row['status']}: {mode} {kind} {fault}" + (f" {row['error']}" if "error" in row else ""), flush=True)
    passed = sum(r["status"] == "pass" for r in cases)
    missing = sum(r["status"] == "missing-prerequisite" for r in cases)
    complete = len(cases) == len(planned) and len({(r["mode"], r["kind"], r["fault"]) for r in cases}) == len(planned)
    report = {"binary": str(binary), "sha256": hashlib.sha256(binary.read_bytes()).hexdigest(), "compiler_command": command,
              "cases": cases, "skips": [r for r in cases if r["status"] == "missing-prerequisite"],
              "passed": passed, "missing_prerequisites": missing, "total": len(cases),
              "expected": len(planned), "complete": complete}
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"{passed}/{len(planned)} passed; {missing} missing prerequisites")
    return int(not complete or passed != len(planned) or missing != 0)


if __name__ == "__main__":
    raise SystemExit(main())
