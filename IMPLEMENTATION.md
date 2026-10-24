# Implementation status

Reference: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.

The behavioral specification is complete for its documented reference envelope.
Naro builds and runs as a Rust terminal editor on Linux/glibc/ncursesw. Complete
compatibility with every source-derived requirement is not yet established.

The implementation uses byte vectors and transactional undo, a Rust editor state
machine and cell renderer, generated reference key/function data, and a small C
bridge for ncursesw, libc locale/POSIX regex/getopt, and libmagic. It ships the
original syntax definitions and translation catalogs, including PO sources.
No reference executable is used at runtime.

Final release validation (see [saved reports](validation/README.md)):

| Check | Result |
|---|---|
| Fixture-safe terminal corpus | 303 recorded; 301 full matches; two declared safety deviations |
| File/exit subset | 302/303 matches; invalid-regex recovery changes exit status |
| Noninteractive CLI corpus | 38/38 matches; eight optional/external-path probes excluded |
| POSIX regex corpus | 162/162 matches across C and en_US.UTF-8 |
| Safety behavior | Six assertions pass across both deliberate deviations |
| Rust tests | Six pass |
| Comparator / harness regressions | Twelve / three pass |
| Formatting / strict Clippy | Pass |
| Spec audit | 25 documents, 248 requirement headings, 309 reference recordings; no problems |

There are no undeclared differences in the 303-scenario candidate replay.
Six inherited terminal scenarios are excluded: five touch paths outside private
fixtures and one requires the optional tiny profile. Full source-derived behavior
beyond these observations remains subject to the limitations below.

The release executable is `target/release/naro`; a debug build is also available.
Rust/Cargo 1.99.1 was installed under `~/.cargo/bin` without changing shell
profiles or installing system packages on this machine. GitHub Actions builds
from a clean Ubuntu checkout and runs formatting, strict Clippy, Rust tests,
release compilation, comparator/harness regressions, terminal smoke and safety
assertions. CI builds checksum-pinned tmux 3.8 in a private runner directory.
The local terminal corpus uses tmux 3.8 and the locales in spec 00.

Known limits: the optional tiny build and credits are absent. External
formatter/speller commands currently operate on the whole buffer; marked-region
behavior still needs implementation. Full hard-wrap/undo combinations, rare rc
lazy-loading branches, real Linux VT modifiers, injected-panic recovery,
disk-full/FIFO/interrupted writes, libmagic database variants, and all 41 locale
catalogs need additional verification. Byte-locale screen captures also inherit
tmux's UTF-8 model. See spec 97/99 for the broader source-only coverage boundary.

The invalid-regex crash and NUL-as-Yes behavior are deliberately fixed, per
spec 99. They remain visible as differential differences and have separate
safety assertions. Do not update the golden reference recordings to hide them.

Use `tools/validate.py` for complete replays or `--ids TEST-…` for focused work.
Use `--compare-only` to recompute an existing report without rerunning scenarios
or replacing its frozen binary. Do not overwrite `spec/evidence/runs`.
Run full suites serially because default fixtures are keyed by test ID.
Set `NANOSPEC_WORK` explicitly for simultaneous experiments, recognizing that
changed absolute paths can affect bytes in golden tool logs.
