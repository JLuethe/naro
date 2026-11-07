# Backup and safe-save integration

Build a test executable with `cargo test --no-run --message-format=json`, then
run:

```sh
python3 tests/backup/run_safe_save.py --binary /absolute/test/executable --out target/fresh-backup-evidence
python3 tests/backup/parent_policy.py --binary /absolute/test/executable --out target/fresh-backup-parent-policy
```

Run as an ordinary host user so the overridden HOME keeps fallback output in
the fixture. Backups and their configuration are absent in the tiny profile;
use the safe-save and recovery runners for that profile. This Linux runner loads the fixture-bounded safe-save syscall interposer into isolated
Rust test processes and records the binary hash, every case, events and result.
All source, backup, home fallback and sentinel paths belong to fresh fixtures.

The parent-policy runner uses a configured backup directory. Editor-owned
mode-0755 and sticky mode-1777 directories succeed, including foreign-owner
and writable-mode source metadata. Nonsticky mode-0777 and a POSIX ACL named
writer are refused before staging. The one-shot `backup-publish` gate compares
old direct temporary files with the new private mode-0700 staging directory:
a mapped different UID can move a chowned temporary in a root-owned sticky
parent or edit writable bytes in a mode-0755 parent on the old binary. With
private staging, the actor can neither traverse the child nor move its entry;
the complete backup is published. Run these actor cases with
`unshare --map-root-user --map-subids` where supported. Fixtures are synthetic
and children have a ten-second deadline.

The matrix exercises overwrite, append and prepend with backups enabled;
`allow_insecure_backup` on/off; confinement on/off; missing, regular, source
hard-link and source symlink backup entries; exclusive temp-name collisions;
and write, partial-write, metadata, sync, close and rename failures in both the
backup and main save. Backup-read errors must skip fallback, backup-rename
errors must use the ordinary home fallback where allowed, and confirmation
flags distinguish ENOSPC. Every precommit failure retains destination bytes,
pathname, inode and mtime, with the buffer modified. Published backups are a
separate permitted side effect. Source-close and directory-close fault events
prove those later close paths execute on the expected side of the save commit.

`cargo test files::backup_tests` additionally verifies metadata and numbering,
regular/symlink/hard-link replacement and identity-checked cleanup/publication
when an owned temporary entry is replaced by a fixture sentinel. The ignored
foreign-owner tests use `run_namespace.py`; they require a prepared rootless
Podman image and never use host root.
The parent-policy distinct-UID fixtures select a nonzero ID present in both
`/proc/self/uid_map` and `/proc/self/gid_map`. Namespace layouts vary by host;
if no shared distinct ID is mapped, the runner records a missing prerequisite
and exits nonzero. The chosen ID is retained in each observation.
The foreign-owned target is created by that actor in a disposable writable
fixture directory, then the directory is restored to mode 0755 before the
editor runs. This avoids depending on `chown` privileges in rootless CI.
CI first runs `probe_namespace_actor.py` inside the same kind of namespace.
When that environment cannot clear groups and establish a distinct UID/GID,
the five optional cases are reported as unqualified in the CI log; they are
not counted as passes. Unexpected probe errors fail CI.
