# NARO development progress — Codex Pi-review cycle

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
