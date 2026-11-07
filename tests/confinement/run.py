#!/usr/bin/env python3
"""Bounded, deterministic issue #12 interleavings in fresh disposable fixtures.

All mutations are controller-owned entries. No user files or race loops. The
preload gate pauses once at a real syscall; each child has a ten-second deadline.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

OLD = b"original fixture\n"
NEW = b"replacement\n"
OUTSIDE = b"outside sentinel\n"
OTHER = b"other entry\n"
TEST = "files::safe_save_tests::fixture_save"


class InfrastructureError(Exception):
    pass


def identity(path):
    s = path.stat()
    return [s.st_dev, s.st_ino]


def exchange(a, b):
    libc = ctypes.CDLL(None, use_errno=True)
    fn = libc.renameat2
    fn.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    fn.restype = ctypes.c_int
    if fn(-100, os.fsencode(a), -100, os.fsencode(b), 2):
        raise InfrastructureError(f"renameat2 exchange: errno {ctypes.get_errno()}")


def records(path):
    if not path.exists():
        return {}
    return {row[0]: [int(x) for x in row[1:]] for line in path.read_text().splitlines()
            if (row := line.split()) and row[0] != "stage"}


def separate_uid_stage_swap(stage_entry, displaced, outside_target):
    """One bounded actor with a mapped, different UID in a user namespace."""
    code = """import os,sys
stage,displaced,outside=sys.argv[1:]
try:
    os.listdir(stage)
except PermissionError:
    pass
else:
    raise AssertionError('private stage was traversable by the actor')
os.rename(stage,displaced)
os.symlink(outside,stage)
"""
    def drop():
        os.setgroups([])
        os.setgid(100000)
        os.setuid(100000)
    actor = subprocess.run([sys.executable, "-c", code, os.path.relpath(stage_entry),
                            os.path.relpath(displaced), str(outside_target)],
                           preexec_fn=drop, capture_output=True, text=True, timeout=5)
    assert actor.returncode == 0, (actor.returncode, actor.stdout, actor.stderr)


def run_case(binary, reader, preload, base, tiny, operation, stage, action, mode, missing=False):
    parent = base / "root/data"
    outside = base / "outside"
    parent.mkdir(parents=True)
    outside.mkdir()
    # Deliberately attacker-writable synthetic parents, without sticky-bit protection.
    parent.chmod(0o777)
    outside.chmod(0o777)
    target = parent / "target"
    sentinel = base / "original-sentinel"
    if not missing:
        target.write_bytes(OLD)
        os.link(target, sentinel)
    (outside / "target").write_bytes(OUTSIDE)
    os.link(outside / "target", base / "outside-sentinel")
    (parent / "other").write_bytes(OTHER)
    os.link(parent / "other", base / "other-sentinel")
    before = {"root": identity(base / "root"), "parent": identity(parent), "outside_parent": identity(outside),
              "target": identity(target) if not missing else None,
              "outside": identity(outside / "target"), "other": identity(parent / "other")}
    (base / "before.json").write_text(json.dumps(before, indent=2) + "\n")
    # Prevent ambient safe-save fixture flags from changing this matrix.
    inherited = {key: value for key, value in os.environ.items()
                 if not key.startswith(("NARO_SAVE_", "NARO_BOUND_"))}
    env = dict(inherited, LD_PRELOAD=str(preload), NARO_BOUND_FIXTURE=str(base),
               NARO_BOUND_DEV=str(before["parent"][0]), NARO_BOUND_INO=str(before["parent"][1]),
               NARO_BOUND_STAGE=stage, NARO_SAVE_FIXTURE=str(base / "root"), NARO_SAVE_MODE=str(mode))
    if not tiny:
        env["NARO_SAVE_CONFINED"] = "1"
    command = ([str(reader), str(base)] if operation == "read" else
               [str(binary), "--exact", TEST, "--ignored", "--nocapture", "--test-threads=1"])
    (base / "command.json").write_text(json.dumps(command) + "\n")
    with (base / "process.log").open("wb") as log:
        proc = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 10
            if stage != "none":
                while not (base / "ready").exists():
                    if proc.poll() is not None:
                        raise AssertionError(f"expected gate not reached; child status {proc.returncode}; see process.log/result")
                    if time.monotonic() > deadline:
                        raise InfrastructureError("gate not reached within ten seconds")
                    time.sleep(0.002)
                # ready is closed before its stage/identity records are consumed:
                # inode identities are re-read after child completion below.
                if action == "parent-symlink":
                    parent.rename(base / "moved-parent")
                    parent.symlink_to(outside, target_is_directory=True)
                elif action == "parent-exchange":
                    exchange(parent, outside)
                elif action == "target-symlink":
                    if not missing:
                        target.rename(parent / "displaced")
                    target.symlink_to(outside / "target")
                elif action == "target-exchange":
                    exchange(target, parent / "other")
                elif action == "target-remove":
                    target.rename(parent / "displaced")
                elif action == "target-create":
                    target.write_bytes(OTHER)
                    os.link(target, base / "created-sentinel")
                elif action in ("stage-entry-symlink", "stage-entry-symlink-separate-uid"):
                    entries = list(parent.glob(".naro-save-*"))
                    assert len(entries) == 1, entries
                    (base / "stage-name").write_text(entries[0].name)
                    if action.endswith("separate-uid"):
                        separate_uid_stage_swap(entries[0], parent / "displaced-stage", outside / "target")
                    else:
                        entries[0].rename(parent / "displaced-stage")
                        entries[0].symlink_to(outside / "target")
                elif action != "none":
                    raise AssertionError(action)
                (base / "release").write_text("resume\n")
            try:
                proc.wait(timeout=max(0.1, deadline - time.monotonic()))
            except subprocess.TimeoutExpired as error:
                raise InfrastructureError("child exceeded ten seconds") from error
            if 91 <= proc.returncode <= 97:
                raise InfrastructureError(f"synchronization shim exited {proc.returncode}; see process.log")
            assert proc.returncode == 0, f"fixture child exited {proc.returncode}; see process.log"
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
    result_path = base / "result" if operation == "read" else base / "root/result"
    result = result_path.read_text()
    if (base / "authority").exists():
        assert [int(x) for x in (base / "authority").read_text().split()] == before["root"]
    gate = records(base / "ready")
    opened = records(base / "opened")
    actual_parent = (base / "moved-parent" if action == "parent-symlink" else
                     outside if action == "parent-exchange" else parent)
    destination = actual_parent / "target"
    assert identity(actual_parent) == before["parent"]
    assert stat.S_IMODE(actual_parent.stat().st_mode) == 0o777
    if operation == "save" and stage != "none":
        assert gate["parent"] == before["parent"], gate
    if stage in ("temp-open", "read-reopen") and not missing:
        assert gate["source"] == before["target"], gate
    if operation == "save" and not missing and stage != "none" and not (
            stage == "source-open" and action in ("target-symlink", "target-remove")):
        assert "source" in opened, opened
    if "source" in opened:
        expected_source = before["other"] if stage == "source-open" and action == "target-exchange" else before["target"]
        assert opened["source"] == expected_source, opened
    assert (base / "outside-sentinel").read_bytes() == OUTSIDE
    assert identity(base / "outside-sentinel") == before["outside"]
    outside_target = parent / "target" if action == "parent-exchange" else outside / "target"
    assert outside_target.read_bytes() == OUTSIDE
    assert identity(outside_target) == before["outside"]
    assert (base / "other-sentinel").read_bytes() == OTHER
    assert identity(base / "other-sentinel") == before["other"]
    if not missing:
        assert sentinel.read_bytes() == OLD
        assert identity(sentinel) == before["target"]
    if operation == "read":
        assert (base / "read-data").read_bytes() == OLD
        assert [int(x) for x in result.split()[1:]] == before["target"]
        assert opened["read"] == before["target"]
        outcome = "pinned-read"
    else:
        success = (stage == "publish" or action in ("none", "parent-symlink", "parent-exchange")) and not (missing and mode == 2) and not action.startswith("stage-entry-symlink")
        if success:
            assert result.startswith("ok "), result
            expected = NEW if missing or mode == 0 else OLD + NEW if mode == 1 else NEW + OLD
            assert destination.read_bytes() == expected
            assert not destination.is_symlink()
            assert identity(destination) not in (before["target"], before["outside"], before["other"])
            outcome = "published-without-CAS" if stage == "publish" and action.startswith("target-") else "authorized-parent-save"
        else:
            if action.startswith("stage-entry-symlink"):
                expected = NEW if missing or mode == 0 else OLD + NEW if mode == 1 else NEW + OLD
                assert destination.read_bytes() == expected, (destination.read_bytes(), expected)
                assert not destination.is_symlink()
                assert "File replaced, but durability is uncertain" in result, result
                displaced = parent / "displaced-stage"
                assert displaced.is_dir() and not list(displaced.iterdir())
                stage_entry = actual_parent / (base / "stage-name").read_text()
                assert stage_entry.is_symlink()
                assert stage_entry.resolve() == outside / "target"
                outcome = "published-from-held-private-directory"
            elif action == "target-symlink":
                assert result.startswith("error "), result
                assert destination.is_symlink()
            elif action == "target-exchange":
                assert result.startswith("error "), result
                assert destination.read_bytes() == OTHER
                assert identity(destination) == before["other"]
            elif action == "target-create":
                assert result.startswith("error "), result
                assert destination.read_bytes() == OTHER
            elif missing or action == "target-remove":
                assert result.startswith("error "), result
                assert not destination.exists()
            else:
                assert result.startswith("error "), result
            if not action.startswith("stage-entry-symlink"):
                outcome = "refused-before-publication"
    if (base / "created-sentinel").exists():
        assert (base / "created-sentinel").read_bytes() == OTHER
    for directory in (actual_parent, outside_target.parent):
        leftovers = list(directory.glob(".naro-save-*"))
        if action.startswith("stage-entry-symlink") and directory == actual_parent:
            assert leftovers == [directory / (base / "stage-name").read_text()], leftovers
        else:
            assert not leftovers, directory
    return {"result": result.strip(), "before": before, "gate": gate, "opened": opened,
            "authorized_parent_after": identity(actual_parent),
            "destination_after": identity(destination) if destination.exists() else None,
            "outcome": outcome, "temporary_leftovers": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--tiny", action="store_true")
    parser.add_argument("--distinct-uid", action="store_true",
                        help="run the isolated publish substitution with a mapped different UID")
    parser.add_argument("--stage-substitution-only", action="store_true",
                        help="run only same-UID stage substitution regression cases")
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    args.out.mkdir(parents=True, exist_ok=False)
    out = args.out.resolve()
    preload = out / "gates.so"
    command = ["cc", "-shared", "-fPIC", "-Wall", "-Wextra", "-Werror",
               str(Path(__file__).with_name("gates.c")), "-ldl", "-o", str(preload)]
    with (out / "compile.log").open("wb") as log:
        subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
    reader = out / "read-fixture"
    if not args.tiny:
        # Compile the unchanged bridge just as build.rs does, with this tiny driver.
        command = ["cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Wformat=2",
                   "-Werror=format", "-Werror=format-nonliteral", "-D_DEFAULT_SOURCE",
                   "-D_XOPEN_SOURCE=700", str(Path(__file__).with_name("read_fixture.c")),
                   str(Path(__file__).resolve().parents[2] / "native/bridge.c"),
                   "-lncursesw", "-lmagic", "-o", str(reader)]
        with (out / "reader-compile.log").open("wb") as log:
            subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
    cases = []
    for mode in range(3):
        cases.append(("save", "none", "none", mode, False))
        cases.append(("save", "none", "none", mode, True))
        for stage in ("source-open", "temp-open", "publish"):
            for action in ("parent-symlink", "parent-exchange", "target-symlink", "target-exchange", "target-remove"):
                cases.append(("save", stage, action, mode, False))
        if mode != 2:
            for stage in ("temp-open", "publish"):
                for action in ("parent-symlink", "parent-exchange", "target-symlink", "target-create"):
                    cases.append(("save", stage, action, mode, True))
        cases.append(("save", "publish", "stage-entry-symlink", mode, False))
        if mode != 2:
            cases.append(("save", "publish", "stage-entry-symlink", mode, True))
    if not args.tiny:
        for action in ("parent-symlink", "parent-exchange", "target-symlink", "target-exchange", "target-remove"):
            cases.append(("read", "read-reopen", action, 0, False))
    if args.distinct_uid:
        if os.geteuid() != 0:
            raise SystemExit("--distinct-uid requires namespace root and a mapped UID 100000")
        cases = [("save", "publish", "stage-entry-symlink-separate-uid", 0, False),
                 ("save", "publish", "stage-entry-symlink-separate-uid", 0, True)]
    elif args.stage_substitution_only:
        cases = [case for case in cases if case[2] == "stage-entry-symlink"]
    report = {"binary": str(binary), "sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
              "tiny": args.tiny,
              "reader_sha256": hashlib.sha256(reader.read_bytes()).hexdigest() if reader.exists() else None,
              "cases": []}
    for operation, stage, action, mode, missing in cases:
        name = f"{operation}-{stage}-{action}-mode{mode}-{'missing' if missing else 'existing'}"
        row = {"name": name}
        try:
            row.update(run_case(binary, reader, preload, out / name, args.tiny, operation, stage, action, mode, missing))
            row["status"] = "pass"
        except InfrastructureError as error:
            row.update(status="infrastructure-failure", error=str(error))
        except Exception as error:
            row.update(status="assertion-failure", error=repr(error))
        report["cases"].append(row)
        print(f"{row['status']}: {name}" + (f" {row['error']}" if "error" in row else ""), flush=True)
        (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    counts = {status: sum(row["status"] == status for row in report["cases"])
              for status in ("pass", "infrastructure-failure", "assertion-failure")}
    print(json.dumps(counts))
    raise SystemExit(0 if counts["pass"] == len(cases) else 1)


if __name__ == "__main__":
    main()
