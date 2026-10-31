# NARO development progress

## Release readiness steps 1–2 — 2026-10-30

The [release checklist](RELEASE_CHECKLIST.md) defines 0.1.0 as an experimental
default-feature Linux x86_64 GNU/glibc release. The primary download will be the
qualified Ubuntu binary with corresponding source and provenance. Tiny remains
an optional source build; physical keyboard trials and other platforms are
explicitly deferred. Actual runtime minimums must come from the final manifest.

Host and Ubuntu closure runners now require wrap-undo (58), filter (6), and
release-fixes (15), using frozen environment reference binaries. The collector
reopens their complete evidence, recomputes expectations/comparisons, and checks
identities, inventories, hashes, steps, and subprocess statuses. The historical
53 follow-ups / 51 exact expectation and existing deviations remain separate.
The original pinned wrap checker defaults and all 43 existing tests are retained.

Validation: nine new tests pass, including a complete synthetic collector run,
rejection of each missing suite on either environment, missing command status,
and tampered report/recording cases. A fresh filter replay is 6/6 exact and its
full evidence passes the new validator. Python syntax, shell syntax, diff checks,
and specification audit pass; the same nine pre-existing audit citations remain.
The new tests are included in CI. No production editor source was changed.

Local replay evidence: `target/release-readiness-step2-2026-10-30/filter/`.
It uses the existing fixed `candidate-v2.bin` and is a focused checker integration
test, not a newly frozen release candidate. The complete final host/Ubuntu,
console, and package runs have not been performed for this step. Because checker
code is part of the verification fingerprint, new qualification needs fresh
reports; historical records must not be relabeled. Next: readiness-plan step 3.

These changes are included in this source delivery. Remote delivery and CI
status are verified separately; see the
[verification receipt](validation/release-readiness-step2.json).

## Claude-review fixes — 2026-10-30/31

Claude's independent report is retained at
`target/naro-test-runs/claude-zSR4qq/CLAUDE_TEST_REPORT.md`.
Codex reproduced the seven proposed failures and expanded them to a permanent
initial 12-case suite: seven original cases, three replacement-history cases, one
relative rcfile error and one valid-rc control. Before fixes, 11 differ and the
valid-rc control matches; afterward, 12/12 match with both harnesses and all
assertions passing. Oracle expectations were preserved, not weakened.

Six causes were repaired:

- Bracketed paste attempts hard wrap after insertion if the cursor remains on
  the original line, matching the ordinary paste path. Multiline paste skips
  the attempt; the existing compound wrap history supplies the undo/redo names.
- Soft-wrap vertical movement permits the final chunk's end-of-line position,
  rebases the desired column, preserves position on impossible boundary moves,
  and adjusts byte indices when a tab crosses a chunk boundary.
  Three additional probes isolated a related End defect: it discarded the
  desired right-edge column when the actual cursor landed on a tab. That is
  also fixed, with three further permanent oracle-asserted regressions, bringing
  the suite to 15 cases.
- A width change remaps the old viewport top through its logical line and chunk
  column before normal cursor visibility adjustment.
- Continuation rows paint the blank line-number field using the number style.
- Replacement history stores the match head as both undo and redo cursor;
  the live replacement/search cursor is unchanged.
- Explicit rcfiles are expanded and canonicalized before reading, so diagnostics
  name the canonical absolute path.

Permanent scenarios: `tests/follow-up/scenarios/release-fixes.json`.
CI runs their assertions on the default executable. Specs 03/04/06/10 and the
generated requirements index now cite the measured cases. The specification
audit passes, retaining the nine previously unresolved citations.

Codex evidence is durable under `target/naro-test-runs/codex-claude-x1n2fz12/`.
`candidate-v2.bin` is the final default release build from HEAD `56d2cc2` with
the working-tree fixes, production fingerprint
`735264926d90c259fdaeb662c1c9c6e08a44a479110e60593460aeda4efd024c`,
executable SHA-256
`cb8e5566abeae2e18b2cb38ea5f67fc77e20aa197eb9fee00a971b691d2cdad2`.
Build metadata are in `candidate-v2-build-info.json`. This is not a committed or
published release. V1 and the accidentally premature `candidate-final.bin` copy
remain preserved; neither is the final candidate. `ATTEMPTS.md` explains that
copy and an earlier process-precheck mistake; neither was an editor failure.

V1 passed the initial 12 regressions, 83 Claude probes/controls, all old follow-up
suites, the retained baseline, CLI/regex and 34 ASan cases. It failed the three
new End/tab probes, retained in `broader-after/`. V2 passes those three probes
and all Rust/lint configurations. Final V2 verification is complete for this fix
cycle; the [compact summary](validation/claude-review.json) records report hashes.
The two broader V2 replays reuse the unchanged
oracle recordings from `broader-after/`, verifying identical scenario inputs
and reference binary hashes, and record that provenance explicitly.
Nightly Rust and the native bridge are instrumented for ASan; external
ncurses/libmagic/system libraries are not rebuilt with instrumentation.

| Final candidate check | Result |
|---|---|
| Permanent release-fixes suite | 15/15 exact, both harnesses 0, all assertions pass |
| Original 35 probes, corrected structural/multibyte cases, minimized controls, three tab-boundary probes | 86/86 exact, all checks pass |
| Instrumented ASan build, same 86 cases | 86/86 exact, all checks pass, no sanitizer diagnostic |
| Wrap / filter / edges / tools / supplement | 58/58, 6/6, 13/13, 20/20, 3/3 exact; all harnesses 0 |
| Full wrap evidence checker | 0 |
| Retained baseline | 303 recorded; 301 full / 302 file-exit matches; six skips; workers [0,0,0,0]; runner 0 |
| CLI / regex | 38/38 and 162/162 |
| Rust | Default debug/release 9 each; tiny release/all-features debug 5 each |
| fmt / Clippy | Default and all-features pass with warnings denied |
| Python / spec audit | 88 tests pass; audit 0, same nine unresolved citations |

Only TEST-CLI-057 and TEST-PROMPT-NUL-001 differ in the retained baseline.
Existing assertions, comparison normalization and deviation policy were not
weakened. These local results precede the source-delivery commit; remote CI
status is verified separately after pushing. The frozen binary retains its
original build revision and hash even after the reviewed source is committed.
Source delivery does not publish a release/tag or replace a system editor.
Portable packaging and genuine console/VT qualification must be refreshed for
the release candidate. Remaining combinations and physical/other-platform scope
stay open; this finite verification does not establish exhaustive nano parity.

## Historical Pi-review cycle

Codex independently reproduced and fixed the confirmed Pi findings. Full GNU
nano parity remains incomplete. The next independent assignment is
[NARO_TEST_AGENT_HANDOFF.md](NARO_TEST_AGENT_HANDOFF.md); the ready-to-paste
prompt is [NARO_TEST_AGENT_START_PROMPT.md](NARO_TEST_AGENT_START_PROMPT.md).

## Changes and causes

- `src/features.rs::hard_wrap`: shift pre-existing lower marks before mapping
  split-origin marks; apply join and prefix/blank-deletion transforms in order.
  This fixes two caught crashes and unintended marked cuts while retaining
  nano's mark-clearing history behavior and existing node-generation model.
- `src/features.rs::execute`: perform filter cut, magic-line restoration and
  insertion separately within one history transaction. Marked filters retain
  insertion-end cursor; unmarked filters return to original line/x=0. Failed
  in-place filters clear hard/soft marks and close addition grouping.
- `wrap-undo.json`: 39→58 cases. The 19 additions preserve original failing
  fixtures, exercise both mark origins and split/prefix boundaries, and add
  quoted/UTF-8/trimblanks/history controls. New expectations were measured on
  pinned GNU nano before being frozen. Existing behavioral expectations were
  preserved; notes 017/022/039 were corrected.
- New `filter.json`: six cases for identity/uppercase marked filters, magic EOF,
  history/cursor, failed-filter cleanup/full save, and a newline-paste control.
- `tools/check_wrap_undo.py`: require frozen executables, all scenario files,
  per-side recordings and raw traces. Check actual hashes and production/tools
  fingerprints, explicit default features, exact membership and typed statuses;
  recompute scenario assertions and comparisons, require complete steps and
  snapshots, check inline byte metadata. No report-supplied executable is run.
  This verifies artifact integrity/consistency, not signed build authenticity.
- `tools/test_check_wrap_undo.py`: 21→43 tests, including complete synthetic
  artifact fixtures and decisive missing/tampered nested-evidence negatives.
  Manifest-only checks still need no installed GNU nano.
- `tools/check_follow_up.py` records verification-tool identity separately from
  production-source and scenario hashes. CI now executes wrap/filter regression
  assertions against the built default executable, in addition to manifest tests.
- Specs 05/06/12/97/98/99, follow-up inventory, validation summary and the five
  requested review/progress/next-steps/handoff/prompt documents were reconciled.
  Historical checkpoints remain historical, and unresolved citations stay open.

## Independently measured before/after

Reference: clean `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`, executable
`b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2`.
Fresh pre-fix release executable matches Pi's `c6c7395a…` binary exactly.
All 45 original Pi scenarios were replayed unchanged: before, 32 exact and
13 different; after, 45/45 exact. Repeated probes count separately here;
this is not 13 distinct implementation bugs. All observed failures share the
five causes above. The checker defect is separate from editor behavior.

Before source editing, reference and candidate logs captured actual file bytes,
exit/assertion status, highlighted cells, stderr and emergency saves. The two
crashes are caught bounds panics (exit 1/code 6), not verified native memory
corruption. A failed-filter timeout was harness SIGKILL while awaiting a save
answer; mark cleanup makes the unchanged input sequence match the reference.
Pi's assertion/cursor/coverage reporting mistakes are detailed in the review.

## Verification

Evidence root: `/tmp/naro-codex-review/` (temporary, not committed).
The frozen default release executable used for editor regression was
`fixed/release/naro`, SHA-256
`c1860f2a9f880ae3ae64e3cee6f7e7b50c99fc27502be972aa1269c13e23d538`.
Its build revision is the pre-commit HEAD `dfcb38a…` **with the reviewed source
changes**, features `""`, Rust 1.99.1, production fingerprint
`75b568359917f7f4ad084906606b79435cac5e82d99fcc7f6e590b41714d3d74`.
The implementation commit in the delivery receipt records these production
bytes. This executable retains its original build revision; it is not relabeled
as a later build. Rebuilding after commit can change its binary hash. Binary
revision alone never identifies a dirty build.

| Check | Result |
|---|---|
| Original Pi probes, fresh two-sided replay | 45/45 exact after fixes |
| Added mark regressions/controls before stronger assertions | 19/19 exact |
| Expanded wrap suite | 58/58 exact, both harnesses 0; strengthened artifact gate passes |
| Filter regressions | 6/6 exact, both harnesses 0, oracle byte/cursor/selection assertions pass |
| Edges / tools / supplement | 13/13, 20/20, 3/3 exact; both sides 0 |
| Retained baseline at `/tmp/nanospec-work` | 303 recorded, 301 full / 302 file-exit matches, six existing skips, workers `[0,0,0,0]`, runner 0 |
| Default Rust debug and release | 9/9 each |
| Tiny release / all-features debug | 5/5 each (separate build directories) |
| fmt / default and all-features Clippy | All 0, warnings denied |
| Checker / comparator-harness-namespace-audit / console Python | 43 + 36 + 9 tests pass |
| Nightly ASan: instrumented Rust and native bridge | Original five probes 5/5 exact, both sides 0, no sanitizer diagnostic |
| Specification audit and retained inventory | Audit 0 (nine known unresolved citations); inventory 309 recorded, zero not-run/uncited |

Only the existing retained-baseline safety deviations TEST-CLI-057 and
TEST-PROMPT-NUL-001 remain. Its six skips are external-path/root-browser policy
and a tiny-only case. No new deviation, normalization or weakened assertion was
introduced.

Commands, actual statuses and complete recordings are retained in the evidence
root: `before/`, `after/`, `added-wrap/`, `filter-before/`, `acceptance/`,
`filter-final/`, `edges/`, `tools/`, `supplement/`, `baseline/`,
`rust-statuses.json` and logs. The intentional note-only corrections to old
cases 017/022 followed the first 58-case replay; the delivery replay binds the final
scenario bytes. The original tested reports remain preserved, not rehashed to pretend they
ran altered scenarios or verification tools. The final `acceptance/` replay
binds the final scenario bytes and the strengthened checker/input validation.

The ASan build used a scratch CC wrapper executing
`cc -fsanitize=address -fno-omit-frame-pointer "$@"` and:

```sh
env RUSTFLAGS='-Zsanitizer=address -Cforce-frame-pointers=yes' CC=/tmp/naro-codex-review/asan-cc /home/john/.cargo/bin/cargo +nightly build --target x86_64-unknown-linux-gnu --target-dir /tmp/naro-codex-review/asan
```

It used the unchanged five-probe input and existing PTY harness. External
ncurses/libmagic/system libraries were not rebuilt with sanitizers. This bounded
run does not certify all FFI paths. Pi's Miri attempt stopped at unsupported
nr_width FFI after six passing buffer tests; Valgrind was unavailable. No TSan,
new physical-console, portable release or exhaustive memory qualification is
claimed.

## Remaining work and delivery

Q-UNDO-002 remains partial. Combined hard+soft wrap/resize/EOF history,
structural-caller spillage lifetime and multibyte lead transforms need the
precise independent matrix in the new handoff. The nine unresolved audit
citations remain gaps. See [Codex next steps](NARO_NEXT_STEPS.md).

Normal commits and push to the existing `main` branch are authorized by the
user. Only reviewed source/tests/tools/CI/specs and requested documents are
included. Prior untracked reviews/handoffs, raw session exports, binaries,
archives, logs and credentials are excluded. No history rewrite or force push.
A documentation delivery receipt records the implementation commit and frozen-build provenance after verification.

## Delivery receipt

Implementation/test/tooling/specification commit:
[`859d8084af11a42c0a9c18006e148e61e5f2026d`](https://github.com/JLuethe/naro/commit/859d8084af11a42c0a9c18006e148e61e5f2026d)
— `Fix wrap mark transforms and filter parity; verify replay artifacts`.
Delivery branch is the existing `main`, remote `https://github.com/JLuethe/naro`.
This receipt and coverage metadata are a following documentation-only commit;
its hash is reported in the final delivery report and repository history.

Final `acceptance/report.json`: 58/58 exact, reference/candidate harness 0,
artifact checker 0; final scenario raw/canonical/runner and verification hashes
are in `validation/wrap-undo/coverage.json`. A complete copied bundle with a
nested candidate exit changed to 99 is rejected (checker 1), as is a standalone
fabricated report with current metadata and absent artifacts. The 43 checker
unit tests pass. Filter 6/6, follow-ups 13/13 + 20/20 + 3/3, retained baseline,
Rust/lint/Python and ASan results remain as recorded above.

The source commit has the same production fingerprint as the frozen tested
binary; that executable still correctly reports build revision `dfcb38a…` and
its reviewed working-tree inputs. It has not been rebuilt or relabeled after
commit. No release artifact, tag, system editor or physical-console claim is
part of this delivery. The tracked working tree is clean after these commits;
pre-existing untracked historical inputs remain preserved and excluded.
