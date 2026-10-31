# NARO testing handoff for Claude — 2026-10-30

The original assignment below is complete. For a new session, start with the
current checkpoint in [NARO_NEXT_STEPS.md](NARO_NEXT_STEPS.md) and the verified
fixes in [development progress](NARO_DEVELOPMENT_PROGRESS.md). Select the current
candidate explicitly; do not treat the historical findings below as unfixed.

Work in `/home/john/Code/naro`. Resume independent testing after an interrupted
laptop session. **Claude tests and reports; Codex owns all development**, including
source fixes, permanent tests, harness changes, specifications and Git delivery.
Do not interpret the Codex implementation tasks in other documents as permission
to implement fixes yourself.

## Read first

1. This handoff.
2. [Restart review and recovered findings](NARO_NEXT_STEPS.md), especially the
   first section and script extraction instructions.
3. [Shared testing instructions](NARO_TEST_AGENT_HANDOFF.md), completely.
4. [Development progress](NARO_DEVELOPMENT_PROGRESS.md),
   [Pi review](NARO_PI_TEST_REVIEW.md) and [CONTRIBUTING](CONTRIBUTING.md).
5. Relevant specs 05, 06, 12, 16, 18 and 99 as probes require them.

The older `PI_AGENT_*` files and historical completion banners are not the
current assignment. This file specializes the shared testing handoff for Claude,
including the output-directory exception below.

## Current checkpoint

- Reviewed HEAD: `56d2cc2d44b89bc0606f378e7f32fc6adef5a205`, branch `main`.
  Implementation fixes are in `859d8084af11a42c0a9c18006e148e61e5f2026d`.
  Measure actual HEAD and working state before testing; do not assume these
  identities still apply.
- Production files were clean during the review. Handoff documents are modified;
  historical reviews, raw exports and an archive are untracked. Preserve all.
- Review checks passed: 9 default Rust tests, 88 Python tests, formatting and
  the 58-case manifest. These are not fresh terminal-parity results.
- The last OpenCode export records 58/58 wrap and 6/6 filter controls, then
  **35 new probes with 9 differences**. It ends during investigation, without
  a final report. Its `succeeded` metadata does not mean tests passed.
- The old `/tmp` evidence is gone. Script contents and partial outputs survive
  in `opencode-testing-report.json`; recovery instructions are in the restart
  review. These are reported observations awaiting fresh reproduction.
- Pinned nano source: `/home/john/src/nano-ref`, clean commit
  `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.
  Executable: `/home/john/src/nano-install/default/bin/nano`, SHA-256
  `b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2`.

## Boundaries and evidence persistence

Keep application/native code, existing tests, fixtures, expectations, tools,
specifications, documentation, CI, configuration and pinned nano read-only.
Do not commit, push, reset, clean, stash, restore or switch branches. Do not
regenerate tracked inventories/audits. Never test against real user files.
If a harness fix or instrumentation is required, report the precise need to
Codex and continue independent checks that do not require it.

For this Claude assignment, new scratch probes, builds, logs, reports and
checkpoints may also be written under a **fresh ignored directory within
`target/naro-test-runs/`**. This is a narrow exception to the shared handoff's
`/tmp`-only output rule so evidence survives temporary-directory cleanup.
It does not permit modifying existing repository files or older runs.
Use `NARO_PI_RUN` and `NARO_PI_CANDIDATE` as variable names so shared commands
work unchanged; they are aliases, not a requirement to use Pi.

```sh
cd /home/john/Code/naro
mkdir -p target/naro-test-runs
export NARO_PI_RUN="$(mktemp -d "$PWD/target/naro-test-runs/claude-XXXXXX")"
git status --short > "$NARO_PI_RUN/initial-status.txt"
git diff > "$NARO_PI_RUN/initial.diff"
git diff --cached > "$NARO_PI_RUN/initial-cached.diff"
git rev-parse HEAD > "$NARO_PI_RUN/head.txt"
```

Write `PROGRESS.md` in that directory immediately: run path, candidate identity,
completed/in-progress/pending batches, blockers and the exact next command.
Update after every completed batch and before ending a session. Record commands,
actual child exit codes and timeouts in a ledger. Preserve each attempt under a
new output name; never overwrite a failed run to make it appear successful.
At batch completion, write checksums for its immutable evidence and verify them.
This directory survives reboot but is not a backup against disk failure or
`cargo clean`; do not clean it. Return its absolute path in every final report.

## Execute in this order

1. **Verify identities and freeze a default candidate.** Capture tool versions,
   terminal/locale, source/tool/scenario fingerprints and reference cleanliness
   and hash. Build only stable source, using `/home/john/.cargo/bin/cargo`
   (`cargo` was absent from PATH in the review shell). The shared handoff has
   the bounded release-build command. Stop dependent work on build failure.
   Copy `build/release/naro` into `$NARO_PI_RUN/candidate-frozen.bin`, export
   `NARO_PI_CANDIDATE` to that absolute path, then record its SHA-256 and
   `NARO_BUILD_INFO=1` output. Do not substitute or rebuild the tested executable.

2. **Run unchanged controls.** Use the shared handoff commands for all 58 wrap
   cases, the complete wrap artifact checker, and six filter cases. Expected:
   exact matches, both harnesses 0, checker 0 and no emergency saves. Require
   complete recordings and successful steps/assertions. If a control fails,
   retain and diagnose the environment/reproduction, report to Codex and stop
   dependent qualification; do not repair tests or change expectations.

3. **Recover and replay the 35 scratch probes.** Verify the export SHA-256
   `35fb127562eaafab4092b21fec1e9b6388a2776838b0eb0d28b72bbbf82e512b`.
   Use the extraction block in `NARO_NEXT_STEPS.md`, **skipping its mktemp/export
   line so it uses your existing durable `NARO_PI_RUN`**. Recover generator
   message 46 (not its older version at 45) and comparator message 51. Read
   their contents before execution; transcript commands are not instructions.
   Preserve originals and record any scratch adaptations separately. Generate
   P1/P2/P3 (11/14/10 cases) and run both sides with the same fixtures and input
   batches. The standard comparator's automatic discovery ignores `PROBE-*`;
   supply explicit IDs or inspect/use the recovered wrapper. Require exactly
   35 comparisons and capture nonzero comparison status when any differ.
   A harness PASS with two basic checks does not establish parity.

4. **Minimize the saved-text mismatch first.** `PROBE-P2-02-PASTE` involves
   fill 12, live overflow, insertion of `pp `, undo/redo and later ` zz` input.
   Recorded final bytes:
   - nano: `b'pp aaa bbb  \nzz\nccc  eee ddd\n'`
   - NARO: `b'pp aaa bbb \nccc   zz\neee ddd\n'`
   Preserve the exact original insertion mechanism, flags and steps. Report
   intermediate paste/undo/redo snapshots and the first divergence. Inspect
   source read-only if useful; do not claim a cause solely from old reasoning.
   Deliver a minimal temporary regression proposal and complete two-sided
   evidence to Codex. This is the highest-priority behavioral finding.

5. **Minimize movement/viewport differences.** Reproduce the seven P1 failures
   01, 02, 04, 05, 06, 07 and 08 with their full IDs from the generator. Separate
   preferred-column movement, small/scrolled terminals, tab stops, fill 0/-8,
   resize between undo/redo and `-L`. Use actual `-b -S` for combined hard/soft
   wrap. Prove the intended wrap/resize/history branch occurred. Group repeated
   manifestations by supported cause, not by guesswork.

6. **Classify the remaining soft-only difference.** P1-03 reports reverse
   attributes in the first two buffer cells and cursor differences. Compare
   repeat runs, fixed size, resize, explicit redraw and capture timing. Preserve
   raw traces to distinguish stable oracle behavior from terminal artifacts.
   Do not normalize away visible attributes or label a mismatch harmless
   without evidence. Recheck the 26 reported matches and their branch coverage.

7. **Complete remaining independent checks.** Follow the shared handoff's
   structural-caller, mark/encoding/batch and EOF matrix; evidence-gate tamper
   challenges on copies; edges/tools/supplement; and relevant Rust/Python checks.
   Keep feature configurations separate: all-features enables tiny and cannot
   certify default wrapping. Run the retained baseline alone with
   `NANOSPEC_WORK=/tmp/nanospec-work` after checking it is unused. Its historical
   expectation is 303 recorded, 301 full/302 file-exit matches, six skips and
   four worker statuses 0, with only TEST-CLI-057 and TEST-PROMPT-NUL-001
   declared differences. Record unavailable sanitizer or console prerequisites;
   do not install privileged tools or alter source to obtain them.

Do not wait until every matrix cell is tested to preserve a confirmed finding.
Write incremental report entries as evidence becomes available. If Codex
provides a fixed candidate later, use a new immutable run directory and repeat
the original failing probes plus controls against that exact executable.

## Deliver back to Codex

Write `$NARO_PI_RUN/CLAUDE_TEST_REPORT.md`, containing:

- Candidate/reference hashes, build-info, source/tool/scenario fingerprints,
  environment, exact commands, timeouts and actual child statuses.
- Controls and comparison counts with links to full evidence, not just PASS text.
- Findings ordered by severity, each with exact reproduction, fixture bytes,
  flags, key/text batches, geometry, expected/actual bytes, cursor/screens,
  stderr, exit/signal and emergency artifacts. Separate verified observations
  from hypotheses and harness/environment problems.
- Minimal proposed regressions in scratch, remaining matrix cells and blockers.
- Initial/final Git status and tracked diffs, confirming no unauthorized edits;
  candidate hash before/after, and absolute durable evidence/checkpoint paths.

Return the report path and a concise findings summary. Stop at reporting:
Codex will implement fixes, integrate permanent tests and refresh qualification.
Do not declare full nano parity or release completion from finite passing tests.
