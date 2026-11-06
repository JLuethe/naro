# Issue #4 — emergency recovery durability

Implemented against `f5e79cfcffb13bc314e819bdc7a0c5ef3fa02d3e` on 2026-11-05.
No applicable ancestor or repository AGENTS.md was found. CONTRIBUTING.md,
spec/00-overview, spec/08-files and spec/13-signals-and-terminal were read.
The issue body came from `target/issue-3-2026-11-05/open-issues.json`.

Emergency recovery now propagates create, write, file-sync, checked-file-close,
directory-open, directory-sync and checked-directory-close errors. The caller
prints success only after every required operation succeeds and otherwise
prints a stage-specific failure and durability warning. Failed output is kept
as potentially useful recovery bytes. Suppressed/unmodified buffers remain
silent. See [behavior](../../docs/emergency-recovery.md).

## Results

- [Old-code regression](old-regression.json): **0/3**, expected failures for
  ignored file sync, missing directory sync and ignored close. All three print
  incorrect success; the original directory-sync operation is never reached.
- [Default PTY matrix](default-faults.json): **41/41**.
- [Tiny PTY matrix](tiny-faults.json): **41/41**.
- Isolated `cargo test`: **17/17**; all-feature test: **12/12**.
- Isolated formatting and all-target/all-feature Clippy with `-D warnings`: pass.
- Scoped `git diff --check`: pass.

The driver checks panic, SIGHUP and SIGTERM, write/create failures, partial and
zero writes, EINTR, ENOSPC, file sync, checked close and directory sync. Checks
cover stderr, status, original bytes, recovery bytes, private mode, naming and
ordered durability syscalls. Restricted and unmodified buffers skip recovery.
All recovery files are disposable synthetic fixtures. This is host Linux
validation, not a physical power-loss or full release qualification.

## Reproducibility and retained failures

[Commands](commands.jsonl) record commands, return codes and raw log paths under
`target/issue-4-recovery/`. [Inspection history](inspection-commands.md) records
initial reads before that command wrapper existed and tool edits.
[Source receipt](source.json), [production patch](production.patch) and
[file hashes](file-hashes.json) identify the change. Both final candidate builds
use a fresh copy of the baseline archive with **only** `src/files.rs` and
`src/editor.rs` overlaid, avoiding unrelated concurrent issue work.

The initial default matrix had 25/41 passes because its panic-brand oracle used
`Naro` instead of the actual `NARO`. The corrected run passed 41/41. The first
tiny attempt passed `-I`, unsupported in tiny, and failed startup. An explicit
`--tiny` driver option removes that flag; the final run passed 41/41. These
failed attempts and their raw output remain under the target directory. Final
old and new runs use the same driver SHA-256 recorded in every report.

Exact final executable SHA-256 values:

| Build | SHA-256 |
|---|---|
| Baseline test-hooks | `ed285902c5d4a3521a58fd187511af80920417028ebe8725d3ac78ae5dc6ca74` |
| Issue #4 default test-hooks | `eb38b34be613d001550286b0516322379b9301b4647494a31fabea5baa7c3877` |
| Issue #4 tiny test-hooks | `55b32352ed10b3b5c565d48c4a6ecc586980f7a15868cb2b9b06426c0d62b126` |

These test-hooks binaries must not be distributed. No installation, credentials,
push, PR, issue close or publication was performed by this work. Unrelated
untracked review artifacts were preserved. Parent-directory namespace races
and the existing collision policy remain outside issue #4.
