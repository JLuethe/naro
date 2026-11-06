# Issue #3 safe-save validation

Work started on `main` at `278f1c541542bc044f4da8f7b3ae72b3990fabdf`.
The tracked tree was clean. [Initial status](initial-status.txt) records the
unrelated untracked files, which are not release inputs and are preserved.
No applicable AGENTS.md was found in the repository or its ancestor directories.
The broad parent-directory discovery encountered unrelated inaccessible
`rfile-qa-claude` fixture directories; repository discovery succeeded.

Build configuration: Cargo package 0.1.1, Rust edition 2024; default features
empty, optional `tiny`, `credits`, `test-hooks`; release LTO and one codegen
unit. Native bridge compiled with C11, ncursesw and (except tiny) libmagic.
Installed toolchain: rustc 1.99.1, cargo 1.99.1; explicit
`PATH=/home/john/.cargo/bin:$PATH` is required in this shell. Native pkg-config
versions: ncursesw 6.6.20251230, libmagic 5.48; tmux 3.8; locales C,
C.utf8, POSIX, en_US.utf8. No system installation was performed.

## Evidence status

Issue #3 implementation and scoped host validation are complete. Raw logs and exact command records are under
`target/issue-3-2026-11-05/`; that directory is new for this work. Baseline
`cargo test`, `cargo test --all-features`, comparison/harness unit tests,
inventory and specification audit returned zero. The separately named
`baseline-build` was started after the prompt warning edit and is **not** an
unmodified historical qualification binary or the authoritative old-code
regression fixture.

The current patch is not a qualified release. Prior receipts remain applicable
only to their recorded binaries. No Daybreak Blue tool, local command or plugin
was found; no Daybreak Blue scan has run. GitHub progress comments say so.

See [the design and compatibility policy](../../docs/safe-save.md).

## Completed checks

- Old-code preservation regressions: **0/3**, the expected failures, proving
  overwrite/append/prepend corruption on injected file-sync error.
- New-code syscall matrix: **414/414 default and 414/414 tiny**. Includes
  short/zero/partial writes, EINTR, EIO, ENOSPC, open/read/metadata failures,
  file sync, checked close, rename, directory sync, process exit boundaries,
  links, permissions, ACL/xattrs, supplementary-group ownership and temporary
  basename collision. Check report skip lists rather than counting unavailable
  platform capabilities as passes.
- Independent reviewer recheck: **3/3 default and 3/3 tiny** original-preservation
  regressions, plus **3/3** supplemental ACL/empty-xattr checks.
- Formatting, default/all-feature Clippy, default/all-feature/tiny unit tests,
  release builds default/tiny, comparison/harness tests, candidate expectation
  tests, inventory and spec audit passed. Formatting initially caught one
  test-file mismatch, corrected before the final successful check.
- Frozen production binaries: smoke **4/4 assertions**, safety **6/6 assertions**,
  CLI branding **5/5**, tiny suites **195/195 scenarios** (59/125/8/3).
- Spec audit still reports nine existing citation warnings, no structural
  problems. These are issue #14 work, not silently treated as resolved.

- Final frozen save-progress and save-safety suites: **32/32 scenarios and 1718/1718 assertions**, all
  steps and assertions pass; one uniform recorded binary hash matches the
  default build receipt. The exact new CI fault-matrix shell was also executed
  locally and passed both 414-case matrices; hosted CI has not run.

## Files and evidence

Production changes: `native/bridge.c`, `src/native.rs`, `src/files.rs`,
`src/prompts.rs`. Tests: `src/safe_save_tests.rs`, `tests/safe-save/` and CI
workflow wiring. Documentation: `docs/safe-save.md`, IMPLEMENTATION,
spec/08-files, spec/16-test-plan and this validation directory.

[Default build](default-build.json), [tiny build](tiny-build.json),
[default faults](default-faults.json), [tiny faults](tiny-faults.json),
[old-code failures](old-regression.json), and [command outcomes](commands.json)
identify exact artifacts and executed checks. Initial and intermediate failures
remain in the referenced raw directories. Additional command records cover
[parent inspection](inspection-commands.md) and
[implementation checks](implementation-checks.md).

## Limits

No full Ubuntu/guest-VT release matrix, physical power-loss testing, or alternate
filesystem/OS certification was performed. Directory sync/close failure after
rename reports uncertain durability; rollback is not claimed. Uncatchable
termination may leave an owned temporary file. Concurrent external writers
need coordination; this work does not establish the broader issue #12
confinement/race claims. No global install, push, PR, issue closure or release
publication was performed. The requested Daybreak Blue scan is unavailable.

See [independent Astra/xhigh review](review.md) and [test command history](test-commands.md).

[The lock ownership integration correction](lock-identity.md) records the
ordinary save-as-to-sidecar data-loss regression, its negative control, the
inode-bound fix and the subsequent 448-case fault and terminal reruns.
