#!/usr/bin/env python3
"""Backup-enabled files::write faults, confined to fresh disposable fixtures."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

OLD = b"original data must survive\n"
NEW = b"replacement\n"
PREVIOUS = b"previous backup\n"
SAVE_FAULTS = ("none", "short", "open", "zero", "eio", "enospc", "partial-eio",
               "file-sync", "close", "rename", "metadata", "source-close",
               "dir-sync", "directory-close")
BACKUP_FAULTS = ("stage-open", "stage-metadata", "open", "zero", "eio", "enospc",
                 "partial-eio", "file-sync", "close", "rename", "metadata", "dir-sync", "read-eio")


def run_case(binary, preload, root, mode, fault, phase, kind, insecure, confined):
    data = root / "data"
    data.mkdir(parents=True)
    home = data / "home"
    home.mkdir()
    target, backup = data / "target", data / "target~"
    sentinel = data / ".naro-backup-unrelated"
    target.write_bytes(OLD)
    target.chmod(0o640)
    os.utime(target, ns=(1_000_000_000, 2_000_000_000))
    sentinel.write_bytes(b"unrelated")
    if kind == "hardlink":
        os.link(target, backup)
    elif kind == "symlink":
        backup.symlink_to("target")
    elif kind == "regular":
        backup.write_bytes(PREVIOUS)
    before = target.stat()
    old_backup = backup.lstat() if backup.exists() else None
    env = dict(os.environ, HOME=str(home), LD_PRELOAD=str(preload),
               NARO_SAVE_FIXTURE=str(root), NARO_SAVE_MODE=str(mode),
               NARO_SAVE_FAULT=fault, NARO_SAVE_BACKUP="1",
               NARO_SAVE_FAULT_PHASE=phase, NARO_SAVE_BACKUP_COLLISION="1")
    for key in ("NARO_SAVE_INSECURE", "NARO_SAVE_CONFINED", "NARO_SAVE_COLLISION"):
        env.pop(key, None)
    if insecure:
        env["NARO_SAVE_INSECURE"] = "1"
    if confined:
        env["NARO_SAVE_CONFINED"] = "1"
    proc = subprocess.run([str(binary), "--exact", "files::safe_save_tests::fixture_save",
                           "--ignored", "--nocapture"], env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=10, umask=0o027)
    (root / "process.log").write_bytes(proc.stdout)
    assert proc.returncode == 0, proc.stdout
    result = (root / "result").read_text()
    events = (root / "events").read_text().splitlines()
    progress = (root / "progress").read_text()
    fallback = phase == "backup" and fault == "rename" and not confined
    committed = fallback or phase == "save" and fault in ("none", "short", "dir-sync", "directory-close")
    success = fallback or phase == "save" and fault in ("none", "short")
    expected = NEW if mode == 0 else OLD + NEW if mode == 1 else NEW + OLD
    assert target.read_bytes() == (expected if committed else OLD), (result, events)
    after = target.stat()
    identity_before = (before.st_dev, before.st_ino)
    identity_after = (after.st_dev, after.st_ino)
    assert (identity_after != identity_before) == committed
    assert (after.st_uid, after.st_gid, stat.S_IMODE(after.st_mode)) == (before.st_uid, before.st_gid, 0o640)
    if not committed:
        assert after.st_mtime_ns == before.st_mtime_ns
    assert result.startswith("ok " if success else "error "), result
    assert ("modified=false" if success and mode == 0 else "modified=true") in result
    if phase == "save":
        assert backup.read_bytes() == OLD
        assert not backup.is_symlink()
        bmeta = backup.stat()
        assert (bmeta.st_dev, bmeta.st_ino) != (before.st_dev, before.st_ino)
        assert (bmeta.st_uid, bmeta.st_gid, stat.S_IMODE(bmeta.st_mode), bmeta.st_mtime_ns) == (before.st_uid, before.st_gid, 0o640, before.st_mtime_ns)
        assert events.index("backup-file-sync") < events.index("backup-close") < events.index("backup-rename") < events.index("backup-dir-sync")
        if not success:
            assert ("File replaced, but durability is uncertain" if committed else "original file unchanged") in result, result
        if fault in ("source-close", "directory-close"):
            assert fault in events, events
            assert events.index("close") < events.index("source-close")
            if fault == "directory-close":
                assert events.index("rename") < events.index("dir-sync") < events.index("directory-close")
            else:
                assert "rename" not in events
    elif fallback:
        assert "Cannot make regular backup" in progress and "Trying again in your home directory" in progress
        assert "backup-rename" in events and "rename" in events, events
        assert events.index("backup-dir-sync") < events.index("rename")
        assert len(list(home.iterdir())) == 1
        assert next(home.iterdir()).read_bytes() == OLD
        if old_backup:
            assert backup.lstat().st_ino == old_backup.st_ino
            assert backup.read_bytes() == (PREVIOUS if kind == "regular" else expected if kind == "symlink" else OLD)
        else:
            assert not backup.exists()
    else:
        assert "Cannot make backup:" in result and "confirm_backup=" in result, result
        assert ("confirm_backup=false" if fault == "enospc" else "confirm_backup=true") in result
        stage = {"zero": "write", "eio": "write", "enospc": "write", "partial-eio": "write", "metadata": "metadata", "read-eio": "read"}.get(fault, fault)
        assert "backup-" + stage in events, events
        assert "rename" not in events, events
        if fault == "read-eio":
            assert "Cannot read original file" in progress
            assert "Trying again in your home directory" not in progress
            assert not list(home.iterdir())
        elif not confined:
            assert "Trying again in your home directory" in progress
        if fault != "dir-sync" and old_backup:
            # A failed unpublished attempt keeps even an existing backup entry.
            assert backup.lstat().st_ino == old_backup.st_ino
            assert backup.is_symlink() == (kind == "symlink")
            assert backup.read_bytes() == (PREVIOUS if kind == "regular" else OLD)
        elif not old_backup and fault != "dir-sync":
            assert not backup.exists()
        elif fault == "dir-sync":
            assert backup.read_bytes() == OLD and not backup.is_symlink()
    collision = Path((root / "backup-collision").read_text())
    assert collision.read_bytes() == b"unrelated collision"
    assert sentinel.read_bytes() == b"unrelated"
    assert not [p for p in data.iterdir() if p.name.startswith((".naro-backup-", ".naro-save-")) and p not in (collision, sentinel)]
    if not confined and phase == "backup" and fault != "rename":
        # Fallback remains fixture-owned. Complete backups may remain after a
        # directory-sync failure; earlier failures clean up only their own file.
        remaining = list(home.iterdir())
        assert len(remaining) == (1 if fault == "dir-sync" else 0), remaining
        assert all(p.read_bytes() == OLD for p in remaining)
    return dict(result=result.strip(), events=events)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error("run as an ordinary host user so HOME fallback stays inside the fixture")
    binary, out = args.binary.resolve(strict=True), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    preload = out / "faults.so"
    faults = Path(__file__).resolve().parents[1] / "safe-save/faults.c"
    command = ["cc", "-shared", "-fPIC", "-Wall", "-Wextra", "-Werror", str(faults), "-ldl", "-o", str(preload)]
    subprocess.run(command, check=True)
    cases = []
    for confined in (False, True):
        for insecure in (False, True):
            for mode in range(3):
                for kind in ("missing", "regular", "hardlink", "symlink"):
                    for phase, faults_for_phase in (("save", SAVE_FAULTS), ("backup", BACKUP_FAULTS)):
                        for fault in faults_for_phase:
                            label = f"c{int(confined)}-i{int(insecure)}-m{mode}-{kind}-{phase}-{fault}"
                            row = dict(case=label, confined=confined, insecure=insecure, mode=mode, kind=kind, phase=phase, fault=fault)
                            try:
                                row.update(run_case(binary, preload, out / label, mode, fault, phase, kind, insecure, confined), status="pass")
                            except Exception as error:
                                row.update(status="fail", error=repr(error))
                                print(f"FAIL {label}: {error}", flush=True)
                            cases.append(row)
    report = dict(binary=str(binary), sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                  faults_sha256=hashlib.sha256(faults.read_bytes()).hexdigest(),
                  driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  compiler_command=command, cases=cases, total=len(cases),
                  passed=sum(row["status"] == "pass" for row in cases))
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"{report['passed']}/{report['total']} passed")
    return int(report["passed"] != report["total"])


if __name__ == "__main__":
    raise SystemExit(main())
