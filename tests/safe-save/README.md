# Safe-save tests

Build using `cargo test --no-run --message-format=json` (repeat with
`--features tiny`). Select the test executable from the Cargo JSON, then run
`python3 tests/safe-save/run.py --binary /absolute/test/executable --out target/fresh-evidence`.
Linux /proc, ACL/xattr support, C compiler and normal build prerequisites are
required. The output directory must be new. Tests call actual files::write in
isolated test processes with fixture-bounded LD_PRELOAD faults. The Rust fixture
is cfg(test), excluded from shipped binaries. Reports record executable hashes,
subprocess logs, operations and resulting fixtures. Every planned case remains
in the report, including unavailable supplementary-group and ACL fixtures.
Fixture setup `EINVAL`/unsupported-ACL errors are marked
`missing-prerequisite`; errors from the editor operation remain product/test
failures. Any missing prerequisite makes the runner exit nonzero. `expected`,
`total`, `passed`, `missing_prerequisites` and `complete` expose omissions; the
full matrix requires all 659 planned cases to pass.

The matrix covers all save modes, file/link/metadata policy, syscall failures,
EINTR, short/partial writes, abrupt exit boundaries, staging-name collisions,
and default-ACL inheritance for a new file compared with direct parent creation.
Returned precommit failures must preserve original bytes/inode/mtime, keep the
buffer dirty and remove their private staging directory without touching an
unrelated sentinel. Abrupt exit may leave a mode-0700 staging directory containing
`content` before publication or empty afterward. Post-commit stage sync,
parent sync, stage removal, and final parent sync failures must explicitly
report uncertain durability after complete replacement.
`--regression-only` tests old original-preservation behavior in three modes.
`python3 -m unittest discover -s tests/safe-save -p 'test_run.py'` exercises the
runner's accounting with a deterministic no-supplementary-group control: 94
unavailable cases cannot turn 565/659 coverage into a success. It also verifies
that an editor-operation `EINVAL` stays a failure, while a fixture setup
`EINVAL` is a missing prerequisite.

Generate terminal candidates with `python3 tests/safe-save/progress_cases.py`
and `python3 tests/safe-save/progress_cases.py save-safety`, redirecting each into
a fresh JSON file. Run nanoharness on both with a fresh NANOSPEC_WORK and --out,
without --candidate-expectations (identity mapping already applied). Applicable
full screen/style/cursor assertions stay. Explicit differences cover temp/openat
gates, preservation messages and rejection in read-only destination directories.
The latter replace an unreachable writing snapshot with a complete error screen,
dirty-buffer exit and retained-backup checks. Original scenarios, recordings and
comparison rules remain unchanged. This is semantic validation, not nano parity.

Run `tests/safe-save/locking.json` with nanoharness against a default candidate
and fresh output/work directories. It checks saving under the buffer's owned
lock pathname and preserving an unrelated sidecar at a save-as destination,
including warnings, saved title state, output bytes and cleanup on exit.
`cargo test files::lock_tests` also checks inode ownership, refresh, missing
locks, explicit takeover, buffer metadata and saved/modified state in ordinary
and confined fixtures; its undo/redo assertion applies to the default profile.

Run `python3 tests/safe-save/test_progress_cases.py` for deterministic generated-gate
regressions. The C helper is built with glibc fortification and its imported
symbols are checked before exercising open faults, release, FIFO interruption,
non-target passthrough and variadic creation modes. The shared generator in
`spec/tools/open_gate.py` also adapts the tiny FIFO resize gate in tiny CI and
fresh differential runs, retaining its blocked-open acknowledgment, helper
status, interruption, dirty-buffer and terminal assertions.
