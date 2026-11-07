#!/usr/bin/env python3
"""Bounded parent-permission and stage-open substitution checks for issue #12."""
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
NEW = b"replacement\n"
TEST = "files::safe_save_tests::fixture_save"


class InfrastructureError(Exception):
    pass


class PrerequisiteError(Exception):
    pass


def identity(path):
    st = path.stat()
    return st.st_dev, st.st_ino


def swap_as_distinct_uid(stage, borrowed, stolen):
    code = """import os,sys
stage,borrowed,stolen=sys.argv[1:]
os.rename(stage,stolen)
os.rename(borrowed,stage)
"""
    def drop():
        os.setgroups([])
        os.setgid(100000)
        os.setuid(100000)
    proc = subprocess.run([sys.executable, "-c", code, *(os.path.relpath(p) for p in (stage, borrowed, stolen))],
                          preexec_fn=drop, capture_output=True, text=True, timeout=5)
    if proc.returncode != 0:
        raise InfrastructureError(f"mapped actor exited {proc.returncode}: {proc.stderr}")


def default_acl_for_named_writer(uid):
    return struct.pack("<I", 2) + b"".join(
        struct.pack("<HHI", tag, perm, ident) for tag, perm, ident in
        ((1, 7, 0xffffffff), (2, 7, uid), (4, 5, 0xffffffff),
         (16, 7, 0xffffffff), (32, 0, 0xffffffff)))


def named_uid_mapped(uid):
    try:
        mapping = Path("/proc/self/uid_map").read_text()
        for line in mapping.splitlines():
            start, _, count = map(int, line.split())
            if start <= uid < start + count:
                return True
    except (OSError, ValueError):
        # An unknown mapping must not turn a fixture error into a skip.
        return True
    return False


def set_named_writer_acl(path, uid):
    try:
        os.setxattr(path, "system.posix_acl_access", default_acl_for_named_writer(uid))
    except OSError as error:
        unsupported = error.errno in (errno.ENOTSUP, errno.EOPNOTSUPP, errno.ENOSYS)
        unmapped_uid = error.errno == errno.EINVAL and not named_uid_mapped(uid)
        if unsupported or unmapped_uid:
            raise PrerequisiteError(f"POSIX ACL fixture setup failed: {error}") from error
        raise


def run_case(binary, preload, base, kind, distinct_uid_actor, mode=0, missing=False):
    parent = base / "root/data"
    parent.mkdir(parents=True)
    target = parent / "target"
    if not missing:
        target.write_bytes(OLD)
    target_before = identity(target) if not missing else None
    borrowed = parent / "borrowed"
    borrowed.mkdir(mode=0o700)
    borrowed_before = identity(borrowed)
    if kind == "owned-private":
        parent.chmod(0o700)
    elif kind == "owned-normal":
        parent.chmod(0o755)
    elif kind == "owned-sticky":
        parent.chmod(0o1777)
    elif kind == "unsafe-open":
        parent.chmod(0o777)
    elif kind == "acl-writer":
        parent.chmod(0o750)
        set_named_writer_acl(parent, 100000)
        assert parent.stat().st_mode & stat.S_IWGRP
    elif kind == "foreign-sticky":
        assert os.geteuid() == 0, "foreign-sticky requires namespace root"
        parent.chmod(0o1777)
        os.chown(parent, 100000, 100000)
    else:
        raise AssertionError(kind)
    unsafe = kind in ("unsafe-open", "acl-writer", "foreign-sticky")
    inherited = {key: value for key, value in os.environ.items()
                 if not key.startswith(("NARO_SAVE_", "NARO_BOUND_"))}
    before = identity(parent)
    env = dict(inherited, LD_PRELOAD=str(preload), NARO_SAVE_FIXTURE=str(base / "root"),
               NARO_SAVE_MODE=str(mode), NARO_BOUND_FIXTURE=str(base),
               NARO_BOUND_DEV=str(before[0]), NARO_BOUND_INO=str(before[1]),
               NARO_BOUND_STAGE="stage-open" if unsafe else "none")
    with (base / "process.log").open("wb") as log:
        proc = subprocess.Popen([str(binary), "--exact", TEST, "--ignored", "--nocapture", "--test-threads=1"],
                                env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 10
            while proc.poll() is None and time.monotonic() < deadline:
                if (base / "ready").exists():
                    entries = list(parent.glob(".naro-save-*"))
                    assert len(entries) == 1, entries
                    stage = entries[0]
                    stolen = parent / "stolen"
                    if distinct_uid_actor:
                        swap_as_distinct_uid(stage, borrowed, stolen)
                    else:
                        stage.rename(stolen)
                        borrowed.rename(stage)
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
    gate_reached = (base / "ready").exists()
    borrowed_survivors = [{"name": p.name, "identity": identity(p),
                           "mode": oct(stat.S_IMODE(p.stat().st_mode))}
                          for p in parent.iterdir() if p.is_dir() and identity(p) == borrowed_before]
    observed = {"gate_reached": gate_reached, "result": result.strip(),
                "target_bytes": target.read_bytes().decode() if target.exists() else None,
                "target_identity": identity(target) if target.exists() else None,
                "borrowed_before_identity": borrowed_before,
                "borrowed_before_mode": "0700",
                "borrowed_after_identity": identity(borrowed) if borrowed.exists() else None,
                "borrowed_after_mode": oct(stat.S_IMODE(borrowed.stat().st_mode)) if borrowed.exists() else None,
                "borrowed_inode_survivors": borrowed_survivors,
                "stolen_exists": (parent / "stolen").exists(),
                "stage_entries": [p.name for p in parent.glob(".naro-save-*")]}
    (base / "observation.json").write_text(json.dumps(observed, indent=2) + "\n")
    if unsafe:
        assert not gate_reached, "unsafe parent reached stage-open boundary"
        assert result.startswith("error "), result
        if missing:
            assert not target.exists()
        else:
            assert target.read_bytes() == OLD and identity(target) == target_before
        assert borrowed.is_dir() and identity(borrowed) == borrowed_before
        assert not list(parent.glob(".naro-save-*"))
    else:
        assert not gate_reached
        assert result.startswith("ok "), result
        expected = NEW if missing or mode == 0 else OLD + NEW if mode == 1 else NEW + OLD
        assert target.read_bytes() == expected and identity(target) != target_before
        assert borrowed.is_dir() and identity(borrowed) == borrowed_before
        assert not list(parent.glob(".naro-save-*"))
    return {"observed": observed, "parent_mode": oct(stat.S_IMODE(parent.stat().st_mode))}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--binary", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--only", choices=("unsafe-open", "acl-writer", "foreign-sticky"))
    ap.add_argument("--distinct-uid-actor", action="store_true")
    args = ap.parse_args()
    binary = args.binary.resolve(strict=True)
    args.out.mkdir(parents=True, exist_ok=False)
    out = args.out.resolve()
    preload = out / "gates.so"
    try:
        with (out / "compile.log").open("wb") as log:
            subprocess.run(["cc", "-shared", "-fPIC", "-Wall", "-Wextra", "-Werror",
                            str(Path(__file__).with_name("gates.c")), "-ldl", "-o", str(preload)],
                           check=True, stdout=log, stderr=subprocess.STDOUT)
    except (OSError, subprocess.CalledProcessError) as error:
        (out / "report.json").write_text(json.dumps({"status": "infrastructure-failure",
                                                    "error": str(error)}, indent=2) + "\n")
        print(f"infrastructure-failure: compile gate shim: {error}")
        return 2
    if args.distinct_uid_actor:
        assert os.geteuid() == 0, "distinct actor requires namespace root"
    cases = [(args.only, 0, False)] if args.only else [
        ("owned-private", 0, False), ("owned-normal", 0, False),
        ("owned-sticky", 0, False), ("unsafe-open", 0, False),
        ("unsafe-open", 0, True), ("unsafe-open", 1, False),
        ("unsafe-open", 1, True), ("unsafe-open", 2, False),
        ("acl-writer", 0, False), ("acl-writer", 0, True)]
    report = {"binary": str(binary), "sha256": hashlib.sha256(binary.read_bytes()).hexdigest(), "cases": []}
    for kind, mode, missing in cases:
        name = f"{kind}-mode{mode}-{'missing' if missing else 'existing'}"
        row = {"name": name, "kind": kind, "mode": mode, "missing": missing}
        try:
            row.update(run_case(binary, preload, out / name, kind, args.distinct_uid_actor, mode, missing))
            row["status"] = "pass"
        except InfrastructureError as error:
            row.update(status="infrastructure-failure", error=str(error))
        except PrerequisiteError as error:
            row.update(status="missing-prerequisite", error=str(error))
        except Exception as error:
            row.update(status="assertion-failure", error=repr(error))
        observation = out / name / "observation.json"
        if observation.exists():
            row["observed"] = json.loads(observation.read_text())
        report["cases"].append(row)
        print(f"{row['status']}: {name}" + (f" {row['error']}" if "error" in row else ""), flush=True)
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return int(any(row["status"] != "pass" for row in report["cases"]))


if __name__ == "__main__":
    raise SystemExit(main())
