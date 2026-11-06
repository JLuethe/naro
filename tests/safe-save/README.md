# Safe-save tests

Build using `cargo test --no-run --message-format=json` (repeat with
`--features tiny`). Select the test executable from the Cargo JSON, then run
`python3 tests/safe-save/run.py --binary /absolute/test/executable --out target/fresh-evidence`.
Linux /proc, ACL/xattr support, C compiler and normal build prerequisites are
required. The output directory must be new. Tests call actual files::write in
isolated test processes with fixture-bounded LD_PRELOAD faults. The Rust fixture
is cfg(test), excluded from shipped binaries. Reports record executable hashes,
subprocess logs, operations and resulting fixtures. Missing supplementary groups
are explicit skips; other unavailable prerequisites fail rather than pass.

The matrix covers all save modes, file/link/metadata policy, syscall failures,
EINTR, short/partial writes, abrupt exit boundaries and temp-name collisions.
Returned precommit failures must preserve original bytes/inode/mtime, keep the
buffer dirty and remove their temp without touching an unrelated sentinel.
Abrupt exit may leave a private uncommitted temp. Directory-sync failures must
explicitly report uncertain durability after complete replacement.
`--regression-only` tests old original-preservation behavior in three modes.

Generate terminal candidates with `python3 tests/safe-save/progress_cases.py`
and `python3 tests/safe-save/progress_cases.py save-safety`, redirecting each into
a fresh JSON file. Run nanoharness on both with a fresh NANOSPEC_WORK and --out,
without --candidate-expectations (identity mapping already applied). Applicable
full screen/style/cursor assertions stay. Explicit differences cover temp/openat
gates, preservation messages and rejection in read-only destination directories.
The latter replace an unreachable writing snapshot with a complete error screen,
dirty-buffer exit and retained-backup checks. Original scenarios, recordings and
comparison rules remain unchanged. This is semantic validation, not nano parity.

Run `python3 tests/safe-save/test_progress_cases.py` for deterministic generated-gate
regressions. The C helper is built with glibc fortification and its imported
symbols are checked before exercising open faults, release, FIFO interruption,
non-target passthrough and variadic creation modes. The shared generator in
`spec/tools/open_gate.py` also adapts the tiny FIFO resize gate in tiny CI and
fresh differential runs, retaining its blocked-open acknowledgment, helper
status, interruption, dirty-buffer and terminal assertions.
