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
mode-0755 and sticky mode-1777 directories succeed. Nonsticky mode-0777 and a
POSIX ACL named writer are refused before temporary creation, preserving the
original document. Its one-shot `backup-publish` gate can demonstrate the prior
gap with an old binary: a mapped different-UID actor moves the backup temporary
entry after the identity check and substitutes a symlink. The fixed binary must
never reach that gate for the unsafe parent. Run the actor case with
`unshare --map-root-user --map-subids` where supported. The fixture contains
only synthetic files and has a ten-second child deadline.

The same gate also covers a foreign-owned source in a root-owned sticky backup
directory. On the earlier binary, the backup temporary became owned by the
foreign UID, which could then move it despite the sticky bit. A mode-0755
backup parent also lets that UID traverse and edit its file after chown. The
current policy refuses before chown whenever the parent has group/other
execute permission. A source mode with group/other write permission is likewise
refused in such a parent before chmod, so another UID cannot alter published
backup bytes. Both properties remain available when the backup directory is
mode 0700. The mapped-UID private-directory gate confirms that even a foreign
owner or a permitted writer of the temporary file cannot traverse that parent
to edit the unpublished bytes.

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
