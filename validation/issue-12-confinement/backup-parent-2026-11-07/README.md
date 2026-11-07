# Issue #12 backup parent hardening

The backup publication path checked its temporary file's identity before
`renameat`, leaving a substitution window in a configured nonsticky shared
backup directory. In a bounded synthetic fixture, a mapped different-UID actor
moved the temporary entry after that check and replaced it with an
outside-pointing symlink. The earlier binary reported success, saved the
document, and published the symlink as the backup. The outside referent was
not written, but the backup pathname and intended backup bytes were wrong.

The fix checks the opened backup parent's owner and sticky permissions before
any temporary entry is created. It uses the same native predicate as the
document save path: editor or root ownership, and a sticky bit whenever group
or other write is present. The group mode bits include the POSIX ACL mask.
This applies to configured backup directories, sibling backups, and the home
fallback. A private staging child is unnecessary after this authorization:
the backup temporary is created mode 0600 and a different UID cannot move its
entry in an allowed parent. Nonsticky shared backup directories are now
refused; ordinary unconfined saves may use their existing home fallback, while
confined saves return the backup confirmation error without touching the
document. Editor-owned mode-0755 and sticky mode-1777 backup directories work.

## Commands and results

Commands ran in isolated `issue12-backup-stage` worktree, based on `1ab0863`.
The default test executable SHA-256 is
`2fbf92bedd4c889949207c200b421fc53eae45a869779650e9fb69debe14ff17`;
tiny is `ed3d47eab72ca21430c3ac5249a284e81d6c1cef7af0c50d32430284d816a785`.
The old executable is
`7adb41857e95a928f4dc835b1cf910959121bbb200d3bda7e3a95802e258553b`:
it was built from production revision `1ab0863` with only the six-line
`NARO_SAVE_BACKUP_DIR` test-fixture hook added. The [old negative-control
report](old-negative-control.json), [new report](new-negative-control.json),
and [policy report](policy-report.json) retain observed results.

| Command | Result |
| --- | --- |
| `cargo fmt --check` | Passed |
| `cargo clippy --offline --all-targets --all-features -- -D warnings` | Passed |
| `cargo test --offline` | 74 passed, 10 ignored |
| `cargo test --offline --features tiny` | 41 passed, 10 ignored |
| `python3 tests/backup/parent_policy.py --binary <default> --out target/backup-parent-policy-1` | 4/4 passed: owned and sticky allowed, nonsticky shared and ACL named-writer refused |
| `unshare --map-root-user --map-subids python3 tests/backup/parent_policy.py --binary <old> --out target/backup-parent-old-distinct --only unsafe-open --distinct-uid-actor` | Expected regression failure: backup name became outside-pointing symlink, old test reported success |
| Same command with `<default>` and `--out target/backup-parent-new-distinct` | Passed: refused before temporary creation, original document unchanged |
| `python3 tests/backup/run_safe_save.py --binary <default> --out target/backup-integration` | 1200/1200 passed |
| `python3 tests/safe-save/run.py --binary <default> --out target/safe-save-default` | 659/659 passed |
| Same runner with `<tiny>` and `--out target/safe-save-tiny` | 659/659 passed |
| `python3 tests/confinement/parent_policy.py --binary <default> --out target/confinement-parent-default` | 10/10 passed |
| Same runner with `<tiny>` and `--out target/confinement-parent-tiny` | 10/10 passed |
| `python3 tests/confinement/run.py --binary <default> --out target/confinement-default` | 77/77 passed |
| Same runner with `<tiny>`, `--tiny --out target/confinement-tiny` | 72/72 passed |

All fixture paths and mutation targets were disposable. The gate fires once at
the real backup `renameat` boundary after the identity check, and every child
has a ten-second deadline. The mapped-UID case requires user namespaces and
subordinate IDs; the ACL case requires POSIX ACL support. CI now runs both
parent-policy scripts using its freshly built default test executable, plus
the document parent-policy script using tiny. These bounded interleavings do
not establish exhaustive concurrency safety, actual power-cut persistence, or
qualification of a later integrated binary.
