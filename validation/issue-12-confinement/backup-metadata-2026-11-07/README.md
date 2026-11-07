# Issue #12 backup metadata publication follow-up

The earlier backup-parent check prevented entry substitution in a nonsticky
writable directory, but allowed root-owned sticky mode-1777 directories. When
root backed up a foreign-owned file, `fchown` gave the backup temporary to that
foreign UID. The UID could then move it despite the sticky bit after NARO's
identity check and substitute a symlink before rename. The bounded old-binary
fixture reached that gate, reported success, and published the symlink as the
backup. A separate old-binary fixture showed that restoring a group/other
writable mode let a different UID change the temporary file's bytes before
publication. Even a mode-0755 parent permits such editing after chown because
it is traversable, although its entries cannot be moved.

The fix enforces a publication invariant for any opened backup parent with
group or other execute permission, including the effective POSIX ACL mask.
Before changing temporary-file metadata, NARO refuses a source whose owner
differs from the editor-owned temporary inode or whose mode grants group/other
write. Immediately before close and publication it checks the actual temporary
owner and write bits again, followed by the existing inode identity check.
The temporary stays editor-owned mode 0600 on refusal, so a distinct UID cannot
move or edit it. Mode-0700 backup directories keep full foreign ownership and
writable-mode compatibility; mapped-UID gate tests confirm the foreign owner
cannot traverse that private parent even after metadata restoration. The same
rule covers configured, sibling, and home-fallback backups.

## Artifact-specific commands and results

Work ran in isolated worktree `issue12-backup-owner`, based on `a140d6e`.
The default test executable SHA-256 is
`5ccf86a5250161df721452ee64b02d89027f81a8e956ff883dbedad56309cf4a`;
tiny is `05fd4e24575b5318d0c1fc43d4cfd62e83da9b3aa95bdf0eaaa7fa43175164d5`.
The prior backup-parent executable is
`2fbf92bedd4c889949207c200b421fc53eae45a869779650e9fb69debe14ff17`.
Reports retained here: [old foreign sticky](old-foreign-sticky.json),
[new foreign sticky](new-foreign-sticky.json),
[old foreign traversable](old-foreign-normal.json),
[new foreign traversable](new-foreign-normal.json),
[old writable mode](old-writable-sticky.json),
[new writable mode](new-writable-sticky.json),
[private foreign owner](private-foreign.json),
[private writable mode](private-writable.json), and
[policy matrix](policy-report.json).

| Command | Result |
| --- | --- |
| `cargo fmt --check` | Passed after formatting the changed Rust line |
| `cargo clippy --offline --all-targets --all-features -- -D warnings` | Passed |
| `cargo test --offline` | 75 passed, 10 ignored |
| `cargo test --offline --features tiny` | 42 passed, 10 ignored |
| `python3 tests/backup/parent_policy.py --binary <default> --out target/backup-owner-policy-qualified` | 8/8 passed: private, ordinary and sticky safe cases; unsafe parent/ACL and writable-mode refusals |
| `unshare --map-root-user --map-subids python3 tests/backup/parent_policy.py --binary <old> --out target/foreign-sticky-old-qualified --only foreign-owner-sticky --distinct-uid-actor` | Expected regression failure: backup name became actor symlink while NARO reported success |
| Same command with `<default>` and `--out target/foreign-sticky-new-qualified` | Passed: no publish gate, original document unchanged |
| Old/new commands with `--only foreign-owner-normal`, outputs `target/foreign-normal-old-qualified` and `target/foreign-normal-new-qualified` | Old backup bytes changed to `poisonal fixture`; new refused before gate |
| Old/new commands with `--only writable-mode-sticky`, outputs `target/writable-sticky-old-qualified` and `target/writable-sticky-new-qualified` | Old backup bytes changed; new refused before gate |
| New commands with `--only foreign-owner-private` and `--only writable-mode-private`, outputs `target/foreign-private-qualified` and `target/writable-private-qualified` | Both passed; mapped UID denied access at publish gate, metadata and bytes preserved |
| `python3 tests/backup/run_safe_save.py --binary <default> --out target/backup-integration-qualified` | 1200/1200 passed |
| `python3 tests/safe-save/run.py --binary <default> --out target/safe-save-default-qualified` | 659/659 passed |
| Same runner with `<tiny>` and `--out target/safe-save-tiny-final2` | 659/659 passed |
| `python3 tests/confinement/run.py --binary <default> --out target/confinement-default-qualified` | 77/77 passed |
| Same runner with `<tiny>`, `--tiny --out target/confinement-tiny-qualified` | 72/72 passed |
| `python3 tests/confinement/parent_policy.py --binary <default> --out target/confinement-parent-default-qualified` | 10/10 passed |
| Same runner with `<tiny>` and `--out target/confinement-parent-tiny-qualified` | 10/10 passed |

The synthetic gate runs once at the real backup `renameat` boundary; each child
has a ten-second deadline. The mapped-UID cases require user namespaces and
subordinate ID mappings. CI runs the ordinary parent-policy matrix, and runs
the mapped-UID foreign-owner and writable-mode cases when that prerequisite is
available, otherwise emitting a missing-prerequisite notice. The checks do not
qualify physical power loss, exhaustive concurrency, or a later binary.
