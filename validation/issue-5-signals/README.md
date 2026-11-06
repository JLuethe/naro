# Issue #5 — atomic signal delivery

Base: `f5e79cfcffb13bc314e819bdc7a0c5ef3fa02d3e`. Host: Linux
7.2.15-1-omarchy x86_64, GCC 16.2.1 20260810, Rust 1.99.1
(58cf8f9c3 2026-10-13), xterm-256color, C.UTF-8. Tested binaries identify
an uncommitted combined issue #4/#5 working tree. These are scoped host checks,
not release or guest-VT qualification. Each terminal report records exact binary
SHA-256 and compiled source/build identity.

## Design and results

Five independent event bits use a compile-time verified lock-free atomic unsigned
integer. The handler only selects a local bit and performs atomic fetch-or.
Compare-and-exchange consumes one event without clearing intervening delivery,
even on an external-command writer thread. Priority is HUP, TERM, TSTP, CONT,
WINCH. Same-class POSIX coalescing is intentional; chronological arrival order
is not retained. All handled signals are masked during the handler. No terminal,
allocation or recovery operation runs inside signal context.

Interrupted paste now queries pending state without consuming the event needed
by normal dispatch for recovery and cleanup.

| Evidence | Result |
| --- | --- |
| [Old native](old-native/report.json) | 9/37; all 6 burst permutations and 20 distinct-class read/clear injections fail |
| [Final native](native-final/report.json) | 37/37, including all 25 event pairs and 10,000 worker-thread races |
| [Old incomplete paste](old-paste/report.json) | 0/2; HUP/TERM fail to exit, requiring fixture-process SIGKILL |
| [Final default PTY](default-terminal-final/report.json) | 12/12 |
| [Final tiny PTY](tiny-terminal-final/report.json) | 10/10 |
| [Default Rust tests](test-default.log) | 17/17 |
| [Clippy all targets/features](clippy-all.log) | pass, warnings denied |
| [Formatting](fmt.log) | pass |

PTY checks assert status 1, fatal text, exact saved bytes, recovery mode 0600,
original preservation, original termios restoration, cursor visibility,
alternate-screen exit, default paste shutdown, and removal of an observed
startup lock. Tiny lacks locking/paste and instead checks absence of both.
Bursts queue all six HUP/TERM/WINCH orders while the child is stopped, then
resume it with CONT. Native tests independently check every event class and
inject the precise consume race in a private instrumented test executable.
PTYs use ordinary uninstrumented editor builds.

## Commands and artifacts

Commands run in `/home/john/Code/naro`, with fresh output directories. Exact
commands and statuses are in [commands.json](commands.json). Native reports
also contain exact C compiler commands, original source hashes, executable
hashes and injection locations. Reports and raw PTY traces remain in each run
directory. The final source manifest covers the signal files and test drivers.

Old paste uses the read-only issue #4 baseline built from `git archive f5e79cf`
with `test-hooks`; the panic hook is inactive. Its SHA-256 is
`ed285902c5d4a3521a58fd187511af80920417028ebe8725d3ac78ae5dc6ca74`.

## Preserved attempts

`new-native` and `default-terminal` passed before replacing the handler's
immutable array lookup with local signal constants; final runs cover that final
production change. The first two tiny attempts passed unsupported default-only
options (`-I`/`-G`, then `-I`) and never launched an editor. Tiny v3 launched and
passed every assertion except a mistaken expectation of a paste-disable
sequence, which tiny does not emit because it never enables paste. The harness
now checks tiny never enables paste; v4 and final both passed 10/10. Failed
reports/traces are retained and are not counted as product regressions or
successful coverage.

Raw fixture files, generated native executables/sources, terminal traces and
command logs are retained locally and ignored by Git; only the reports and
receipts are checkpointed. Log links above refer to this local evidence.
