# Backup and safe-save integration

Build a test executable with `cargo test --no-run --message-format=json`, then
run:

```sh
python3 tests/backup/run_safe_save.py --binary /absolute/test/executable --out target/fresh-backup-evidence
```

Run as an ordinary host user so the overridden HOME keeps fallback output in
the fixture. Backups and their configuration are absent in the tiny profile;
use the safe-save and recovery runners for that profile. This Linux runner loads the fixture-bounded safe-save syscall interposer into isolated
Rust test processes and records the binary hash, every case, events and result.
All source, backup, home fallback and sentinel paths belong to fresh fixtures.

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
