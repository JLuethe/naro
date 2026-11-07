#!/usr/bin/env python3
"""Bounded backup-parent and post-identity-check substitution tests."""
import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import subprocess
import sys
import time

OLD = b"original fixture\n"
OUTSIDE = b"outside sentinel\n"
TEST = "files::safe_save_tests::fixture_save"


class InfrastructureError(Exception):
    pass


class PrerequisiteError(Exception):
    pass


def identity(path):
    st = path.stat()
    return st.st_dev, st.st_ino


def acl_named_writer(uid):
    return struct.pack("<I", 2) + b"".join(
        struct.pack("<HHI", tag, perm, ident) for tag, perm, ident in
        ((1, 7, 0xffffffff), (2, 7, uid), (4, 5, 0xffffffff),
         (16, 7, 0xffffffff), (32, 0, 0xffffffff)))


def substitute(temp, stolen, outside, distinct_uid, write_temp=False):
    if distinct_uid:
        code = """import os,sys
temp,stolen,outside,write_temp=sys.argv[1:]
if write_temp=='1':
    fd=os.open(temp,os.O_WRONLY)
    os.write(fd,b'poison')
    os.close(fd)
else:
    os.rename(temp,stolen)
    os.symlink(outside,temp)
"""
        def drop():
            os.setgroups([])
            os.setgid(100000)
            os.setuid(100000)
        actor = subprocess.run([sys.executable, "-c", code, os.path.relpath(temp),
                                os.path.relpath(stolen), str(outside), str(int(write_temp))], preexec_fn=drop,
                               capture_output=True, text=True, timeout=5)
        if actor.returncode:
            raise InfrastructureError(f"mapped actor exited {actor.returncode}: {actor.stderr}")
    else:
        if write_temp:
            with temp.open("r+b") as file:
                file.write(b"poison")
        else:
            temp.rename(stolen)
            temp.symlink_to(outside)


def check_private_temp(temp):
    code = """import os,sys
try:
    os.open(sys.argv[1],os.O_WRONLY)
except PermissionError:
    pass
else:
    raise AssertionError('different UID opened private backup temporary')
"""
    def drop():
        os.setgroups([])
        os.setgid(100000)
        os.setuid(100000)
    actor = subprocess.run([sys.executable, "-c", code, os.path.relpath(temp)],
                           preexec_fn=drop, capture_output=True, text=True, timeout=5)
    if actor.returncode:
        raise InfrastructureError(f"mapped actor exited {actor.returncode}: {actor.stderr}")


def run_case(binary, preload, base, kind, distinct_uid):
    data = base / "root/data"
    backups = base / "root/backups"
    data.mkdir(parents=True)
    backups.mkdir()
    target = data / "target"
    target.write_bytes(OLD)
    if kind.startswith("foreign-owner-"):
        assert os.geteuid() == 0, "foreign ownership requires namespace root"
        os.chown(target, 100000, 100000)
    elif kind.startswith("writable-mode-"):
        target.chmod(0o666)
    target_before = identity(target)
    outside = base / "outside-sentinel"
    outside.write_bytes(OUTSIDE)
    outside_before = identity(outside)
    if kind in ("owned-private", "foreign-owner-private", "writable-mode-private"):
        backups.chmod(0o700)
    elif kind in ("owned-normal", "foreign-owner-normal", "writable-mode-normal"):
        backups.chmod(0o755)
    elif kind == "owned-sticky":
        backups.chmod(0o1777)
    elif kind in ("foreign-owner-sticky", "writable-mode-sticky"):
        backups.chmod(0o1777)
    elif kind == "unsafe-open":
        backups.chmod(0o777)
    elif kind == "acl-writer":
        backups.chmod(0o750)
        try:
            os.setxattr(backups, "system.posix_acl_access", acl_named_writer(100000))
        except OSError as error:
            if error.errno in (errno.ENOTSUP, errno.EOPNOTSUPP, errno.ENOSYS):
                raise PrerequisiteError("POSIX ACL support unavailable") from error
            raise
        assert backups.stat().st_mode & stat.S_IWGRP
    else:
        raise AssertionError(kind)
    unsafe = kind in ("unsafe-open", "acl-writer", "foreign-owner-sticky",
                      "foreign-owner-normal", "writable-mode-sticky", "writable-mode-normal")
    owned = identity(backups)
    inherited = {k: v for k, v in os.environ.items()
                 if not k.startswith(("NARO_SAVE_", "NARO_BOUND_"))}
    env = dict(inherited, LD_PRELOAD=str(preload), NARO_SAVE_FIXTURE=str(base / "root"),
               NARO_SAVE_MODE="0", NARO_SAVE_BACKUP="1", NARO_SAVE_CONFINED="1",
               NARO_SAVE_BACKUP_DIR=str(backups), NARO_BOUND_FIXTURE=str(base),
               NARO_BOUND_DEV=str(owned[0]), NARO_BOUND_INO=str(owned[1]),
               NARO_BOUND_STAGE="backup-publish" if unsafe or distinct_uid and kind.endswith("-private") else "none")
    with (base / "process.log").open("wb") as log:
        proc = subprocess.Popen([str(binary), "--exact", TEST, "--ignored", "--nocapture", "--test-threads=1"],
                                env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 10
            while proc.poll() is None and time.monotonic() < deadline:
                if (base / "ready").exists():
                    entries = [p for p in backups.iterdir() if p.name.startswith(".naro-backup-")]
                    assert len(entries) == 1, entries
                    if kind.endswith("-private"):
                        check_private_temp(entries[0])
                    else:
                        substitute(entries[0], backups / "stolen", outside, distinct_uid,
                                   write_temp=kind in ("writable-mode-sticky", "writable-mode-normal",
                                                       "foreign-owner-normal"))
                    (base / "release").write_text("resume\n")
                    break
                time.sleep(0.002)
            try:
                proc.wait(timeout=max(0.1, deadline-time.monotonic()))
            except subprocess.TimeoutExpired as error:
                raise InfrastructureError("fixture process exceeded ten seconds") from error
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
    if 91 <= proc.returncode <= 97:
        raise InfrastructureError(f"gate shim exited {proc.returncode}")
    assert proc.returncode == 0, proc.returncode
    result = (base / "root/result").read_text()
    entries = [{"name": p.name, "symlink": p.is_symlink(),
                "uid": p.lstat().st_uid, "mode": oct(stat.S_IMODE(p.lstat().st_mode)),
                "link_target": os.readlink(p) if p.is_symlink() else None,
                "bytes": p.read_bytes().decode() if p.is_file() else None}
               for p in backups.iterdir()]
    observed = {"gate_reached": (base / "ready").exists(), "result": result.strip(),
                "target_bytes": target.read_bytes().decode(), "target_identity": identity(target),
                "outside_bytes": outside.read_bytes().decode(), "outside_identity": identity(outside),
                "backup_entries": entries}
    (base / "observation.json").write_text(json.dumps(observed, indent=2) + "\n")
    assert identity(outside) == outside_before and outside.read_bytes() == OUTSIDE
    if unsafe:
        assert not observed["gate_reached"], "unsafe backup parent reached publish gate"
        assert result.startswith("error "), result
        assert target.read_bytes() == OLD and identity(target) == target_before
        assert not entries, entries
    else:
        assert observed["gate_reached"] == (distinct_uid and kind.endswith("-private"))
        assert result.startswith("ok "), result
        assert target.read_bytes() == b"replacement\n"
        assert len(entries) == 1 and not entries[0]["symlink"] and entries[0]["bytes"] == OLD.decode()
        if kind == "foreign-owner-private":
            assert entries[0]["uid"] == 100000
        if kind == "writable-mode-private":
            assert entries[0]["mode"] == "0o666"
    return observed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--binary", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--only", choices=("unsafe-open", "acl-writer",
                                       "foreign-owner-sticky", "foreign-owner-normal", "foreign-owner-private",
                                       "writable-mode-sticky", "writable-mode-normal", "writable-mode-private"))
    ap.add_argument("--distinct-uid-actor", action="store_true")
    args = ap.parse_args()
    binary = args.binary.resolve(strict=True)
    args.out.mkdir(parents=True, exist_ok=False)
    out = args.out.resolve()
    preload = out / "gates.so"
    try:
        with (out / "compile.log").open("wb") as log:
            subprocess.run(["cc", "-shared", "-fPIC", "-Wall", "-Wextra", "-Werror",
                            str(Path(__file__).resolve().parents[1] / "confinement/gates.c"),
                            "-ldl", "-o", str(preload)], check=True,
                           stdout=log, stderr=subprocess.STDOUT)
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"infrastructure-failure: compile gate shim: {error}")
        return 2
    if args.distinct_uid_actor:
        assert os.geteuid() == 0, "distinct UID actor requires namespace root"
    cases = (args.only,) if args.only else ("owned-private", "owned-normal", "owned-sticky",
                                           "unsafe-open", "acl-writer", "writable-mode-private",
                                           "writable-mode-normal", "writable-mode-sticky")
    report = {"binary": str(binary), "sha256": hashlib.sha256(binary.read_bytes()).hexdigest(), "cases": []}
    for kind in cases:
        row = {"name": kind}
        try:
            row["observed"] = run_case(binary, preload, out / kind, kind, args.distinct_uid_actor)
            row["status"] = "pass"
        except InfrastructureError as error:
            row.update(status="infrastructure-failure", error=str(error))
        except PrerequisiteError as error:
            row.update(status="missing-prerequisite", error=str(error))
        except Exception as error:
            row.update(status="assertion-failure", error=repr(error))
        observation = out / kind / "observation.json"
        if observation.exists():
            row["observed"] = json.loads(observation.read_text())
        report["cases"].append(row)
        print(f"{row['status']}: {kind}" + (f" {row['error']}" if "error" in row else ""), flush=True)
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return int(any(row["status"] != "pass" for row in report["cases"]))


if __name__ == "__main__":
    raise SystemExit(main())
