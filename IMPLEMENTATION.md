# Implementation status

Reference: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.

The specification is complete for the documented reference envelope. Naro's
implementation and compatibility validation are ongoing. This file distinguishes
a successful build from complete behavioral parity.

The implementation uses Rust byte vectors and transactional undo, a Rust editor
state machine and cell renderer, generated reference key/function data, and a
small native bridge for ncursesw, libc locale/POSIX regex/getopt, and libmagic.
It ships the original syntax definitions and translation catalogs, including PO
sources. No reference executable is used at runtime.

Verified on this machine: Rust/Cargo 1.99.1, debug and optimized release builds,
five in-memory buffer/byte tests, strict Clippy and formatting checks, ten
comparator regression tests, and all 162 regex-corpus cases through Naro's actual
Rust/native wrapper in harness fixtures. The integration smoke test matches the
reference exactly, including terminal attributes and modes.

The second frozen debug run recorded 303 fixture-safe default-profile scenarios:
209 full matches; 293 matches on the file/exit subset. This is an intermediate
baseline, not the latest source's final score. A focused repair replay matched
23 of 24 formerly failing scenarios fully and all 24 on the file/exit subset.
A complete release-binary replay is in progress; final results will replace this
checkpoint. Evidence is stored locally under `spec/evidence/naro-*` with binary
hashes and structured comparison reports.

Known work includes advanced help/browser interactions, rare rc grammar/lazy
loading details, complete prompt/translation formatting, soft-wrap and tool edge
cases, and remaining terminal lifecycle comparisons. Byte-locale screen captures
are limited by tmux's UTF-8 model. Tiny builds and credits are optional and not
implemented. The invalid-regex crash and NUL-as-Yes behavior are deliberately
fixed, per spec 99; their reference runs are expected to differ.

Use `tools/validate.py` for complete replays or `--ids TEST-…` for focused work.
Do not overwrite `spec/evidence/runs`. Run full suites serially: default fixture
paths are shared by test ID. Set `NANOSPEC_WORK` explicitly for simultaneous
experiments, recognizing that different absolute paths can affect golden text.
