# Issue #6: bounded delta undo

The default profile now journals changed byte ranges instead of cloning `State`
before and after each operation. In-line edits reuse the live line allocation;
structural edits reuse its first-line prefix. Journals retain cursor endpoints,
affected anchors and the endpoint nodes that survive a splice. Replay assigns
fresh identities only to recreated nodes. Hard wrap extends the triggering
item atomically; indentation, comments, justification, formatting and filters
use the same journal.

The per-buffer 32 MiB policy is documented in
[UNDO-001](../../spec/06-undo-redo.md). It bounds accounted retained and pending
history, not total process RSS or temporary allocator reallocation storage.
Oldest groups are evicted. A transaction that cannot fit creates a history
barrier without rolling back or corrupting the live edit. Saved points are
rebased or invalidated when history is discarded. Tiny retains no history.

## Evidence

- [Final commands and exit statuses](final-checks.json): default and all-feature
  tests, both Clippy profiles, and formatting of the owned Rust files. The
  default run passes 35 tests; the all-feature run includes tiny and passes 24.
  Seven separately invoked search stress tests are explicitly ignored by these
  commands and are not counted as passes for this issue.
- Twelve default buffer tests cover 1,000 edits in one 10 MiB line, full
  undo/redo, typing/deletion grouping, saved points and divergent history,
  embedded NULs, selections, magic lines, 300 deterministic multiline edits,
  line identities, oversized compound operations, a growing group crossing
  the budget, and wraps with an absent or oversized triggering item.
- [Stress runner](../../tests/undo/stress.py) freezes and compiles the real
  `buffer.rs` and `bytes.rs`, using unused native declarations only to satisfy
  the byte module's types. The exercised insert/undo/redo paths have no native
  calls. It starts with a 10 MiB single line, performs 10,000 separate edits
  and full undo/redo, then 200,000 further edits forcing eviction, and verifies
  the retained undo/redo suffix and exact resulting bytes. Bounds are 15
  seconds, 96 MiB peak RSS and 256 MiB address space. Linux `wait4` measures
  the child process's peak RSS; compilation is excluded.
- `stress-05` compares the same harness against `f5e79cf` and the final buffer
  source. The baseline aborts with a memory allocation error at the address
  space bound. The delta implementation completes within both bounds. Exact
  measurements and source/binary hashes are in [stress-report.json](stress-report.json).
- Final production differential runs use `target/issue-6-undo/source-04` and
  `build-05/release/naro`; [source-04.json](source-04.json) hashes the frozen
  inputs and verification support. The 58-case wrap suite, six filter cases
  and eleven baseline undo scenarios exercise real terminal actions and
  compare the complete recordings against pinned GNU nano 9.3. The existing
  identity policy is unchanged; accepted identity differences are not raw
  matches. [summary.json](summary.json) records final outcomes and artifacts.

## Scope and provenance

Owned production changes are `src/buffer.rs`, the undo callers in
`src/features.rs`, and the policy in `spec/06-undo-redo.md`. Issue #7 owns search
and spelling-search changes and uses the coordinated `record_replacement`
APIs. The frozen production snapshot includes the concurrent caller/native
changes present when captured, each identified by its hash. At final capture,
the current tree differed from this snapshot only in `src/search.rs`; the
final unit and lint checks ran against the current integration tree. The
terminal report therefore qualifies its frozen executable, not a later
combined build or an unrecorded future change.

Large binaries, copied sources, fixtures and raw terminal traces remain local
under `target/issue-6-undo/`. Concise reports and command records are retained
here. Earlier attempts are preserved under `target/issue-6-undo/intermediate/`;
their failures and superseding runs are listed in [commands.md](commands.md).
No package, publication, installation, credentials, or production files were
used. This is focused issue validation, not a release certification.
