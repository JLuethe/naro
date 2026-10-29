# NARO session review: current hard-wrap parity audit

> **Status (2026-10-28):** the work that this review describes as
> outstanding has since been implemented and verified; the hard-wrap undo/redo
> suite now has 39 cases and matches the pinned reference exactly. See
> `spec/98-progress.md` (the final checkpoint) and
> `validation/wrap-undo/README.md` for the current state. This document is
> kept as the review that motivated that work; the statements below describe
> the tree *before* it.

Reviewed 2026-10-28 in `/home/john/Code/naro`. Implementation handoff:
[NARO_NEXT_STEPS.md](NARO_NEXT_STEPS.md).

## Decision

**Hard-wrap parity remains incomplete. Do not push this tree as completed
functionality.** The exported session made useful, demonstrably effective
fixes and its final 27-case pass is reproducible. Nevertheless, fresh review
replays found eight differential mismatches in ten targeted probes, including
an explicit-mark error that causes a subsequent cut to remove unintended
text, and line-identity errors in empty-line joins and partial multiline
cuts. The manifest/report gate also accepts deliberately invalid evidence.

No application source was changed during this review. The requested handoff
and this review were written; the older content of this file is retained
below as historical evidence, explicitly superseded by this current review.
No commit, push, force-push, history rewrite or staging action was performed.

## Scope and evidence identities

Primary export: `opencode-hardwrap-parity.json`, 1,995,738 bytes, 225 messages;
SHA-256 `5d7a44eeb98ec77304d9e93d0f8ab3fcc055f2aa3a6a511c6a813cd72da4a0c9`.
Session `ses_e7bc0370fffep5VmMn5Kfvylm8`, titled “NARO hard-wrap undo/redo
parity.” References **M0…M224** below mean zero-based `messages[index]` in
that export. The export was parsed and reviewed incrementally, including
tool inputs/results and the post-interruption continuation. Its `succeeded`
outcome and final prose are claims, not substitutes for test evidence.

Reviewed repository code, specs, scenario inputs, workflow/tools, diffs,
history, retained reports and checksums. Consulted the pinned local GNU nano
source directly; did not substitute the installed system nano or modify the
reference checkout. No relevant `AGENTS.md` was found under the parent tree.

| Identity | Verified value |
|---|---|
| NARO HEAD | `823cb96cc6aba9281b58da7ad33dfa3dd4a6a138` |
| Pinned reference checkout | `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`, clean |
| Reference binary | `/home/john/src/nano-install/default/bin/nano`, GNU nano 9.3 default |
| Reference SHA-256 | `b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2` |
| Final session/review default binary SHA-256 | `e70159f7f0cd4d10af7a4576dafec56523de377f8b7451c2058e479fff8f4a1d` |
| Current source fingerprint, build.rs convention | `860f62a4f6c2f79b12167c456511ada0ecb9b284070cc58ca6ef60fdfdc47e09` |
| Earlier fixed candidate used for some session suites | `accb57fdddd675fb3234bee3cc8efdc814f4b5702821fc2a1f345bbac49a6110` |
| Session-start candidate (not HEAD's implementation) | `f29e4a48b21709f43eea66922a28d60068a14bf2785b05a288759710adb70eba` |
| Review compiler | `rustc 1.99.1 (58cf8f9c3 2026-10-13)` |

Clean review build: `/tmp/naro-review-build-20261028/release/naro`, produced
by `/home/john/.cargo/bin/cargo build --release --target-dir
/tmp/naro-review-build-20261028`. Both its file hash and `NARO_BUILD_INFO=1`
output exactly reproduce the session's final binary and source fingerprint;
features are empty (default). Recomputed the fingerprint from sorted file
paths under `src`, `native`, `assets`, plus Cargo.toml, Cargo.lock, build.rs
and CREDITS.md using SHA-256 of sha256sum output, including filenames and
newlines, as build.rs does. A commit ID alone would not identify this dirty
source tree.

Current suite hashes also match retained coverage:

| Serialization | SHA-256 |
|---|---|
| Raw `wrap-undo.json` bytes | `f5c1a95793ef89a9d37e0d7ee08da8ead86d64d1c121956f80f4069df2fad83c` |
| Parsed JSON, sorted keys, compact separators | `cd0c3ec4c9512ea432f09f31b2a77e6b86a2fee3290e5373c64c25672f5fa86f` |
| Runner `json.dumps(cases, indent=1) + '\n'` | `89cf963af6b5e6489ab1814bc76cf61b8f156ccfe550415be98f4e49d5f0892a` |

## Session reconstruction

The session began on top of earlier uncommitted hard-wrap work, not a clean
HEAD. M4/M5 establish 11 tracked files, 398 insertions and 22 deletions,
plus untracked scenarios/reviews/evidence. The earlier prefix/NUL/trim/group
fixes were already present. This session's main new application change was
the generation model and its integration into file loading and line updates.

| Messages | Work performed and actual outcome |
|---|---|
| M0–M5 | Read earlier reviews/spec checkpoint, inspected status/diff/HEAD; saved diff, fingerprints and untracked inputs under `/tmp/opencode/hw-task-preserve`. Large status output was truncated and reissued more narrowly. |
| M6–M23 | Verified pinned reference and session-start binary; inspected hard_wrap, Buffer/history, cut/paste, direct line replacements, harness/runner support and old failures. |
| M24–M38 | Built decisive shortened Delete and Backspace join cases. Initially used unsupported `expect.rows`, then minimal supported expectations. First reference attempt failed on unknown key `Backspace`; corrected to `Bsp`. Reference then split `fff` above `eee ddd`. Initial captured-file decoding also failed because values were lists; representation interpretation was corrected later. |
| M39–M47 | Session-start candidate joined `fff eee ddd`, decisively reproducing structural-history resurrection for both keys. Preserved failures and inspected nano `delete_node`, `do_wrap`, JOIN history and `extract_segment`. |
| M48–M67 | Added `State.generations`, `Buffer.next_gen`, live generation matching, generation initialization and maintenance in new/magic/replace/history, no-survivor and clear helpers, file loading, and updated the NUL unit fixture to use a generation. Default/tiny compiled and unit tests passed. |
| M68–M70 | Provider quota interruption followed by user-requested continuation after adding credits. No implementation result should be inferred from that failed turn. |
| M71–M78 | First “fixed” replay failed immediately. Investigation proved the default executable had been overwritten by a tiny build in the same target directory; its option rejection was not an editor panic. Rebuilt default separately (`accb57fd…`); both decisive structural cases then matched. |
| M79–M82 | Original 23-case wrap suite, five finder and three NUL cases matched. fmt initially requested reformatting despite a misleading pipeline status; formatting was applied; default/all-features Clippy and default/tiny unit tests passed. |
| M83–M87 | Added whole-line cut with real successor `TAIL`. Reference and fixed candidate split `eee`/`TAIL`; old candidate joined `eee TAIL`. Preserved old/fixed/reference evidence. |
| M88–M96 | Added production live-overflow NUL join. Reference/fixed retained payload NUL. Temporarily removed production `decode_nuls`, rebuilt mutation, observed seven differences, restored source and rebuilt. This is meaningful regression evidence beyond the decoder-only unit test. |
| M97–M119 | Shortened 020's final text from ` fff ggg` to ` fff`, added save capture and Backspace 024, moved 022's NUL before the split, integrated 025 ordinary-redo, 026 cut-tail, 027 NUL join. Intermediate 24 then 27 cases matched. |
| M120–M145 | Replayed finder/NUL; ran Rust checks; started 61-case baseline (initial foreground timeout, then another run); added not_contains harness test; added checker and CI manifest step. Checker initially rejected mixed-case AUTOSpill and was relaxed. Corrected 011's note; broadened audit ID regex; regenerated audit/requirements. |
| M146–M155 | Built final default candidate (`e70159f7…`). Initial manual fingerprint computation disagreed; reproduced build.rs's exact serialization and obtained `860f62a4…`. Final 27 cases matched and scenario serialization hashes were recorded. |
| M157–M161 | Confirmed 61/61 baseline subset; edges 13/13, tools 20/20, supplement 3/3; launched one four-worker full baseline. |
| M162–M197 | Updated coverage, validation README, specs 05/06/97/98/99, matrix and generated inventory. CSV edit introduced unquoted commas and invalid status/gate/evidence columns; audit really failed despite displayed `AUDIT:0`. Inspected actual exit 1, fixed row, audit then passed. |
| M198–M214 | Created acceptance archive, copied successful/old-failing/mutation recordings, binaries and source diff; generated checksums; ran comparator/harness/namespace tests, regenerated inventories/audit. Observed old orphaned editors from timed-out validation rather than proving timeout cleanup. |
| M216–M220 | Full baseline finished: 303 recorded, 301 full, 302 file/exit, six exclusions, four worker statuses 0; only two declared deviations. Copied report/tree/log, updated manifest/checkpoint and regenerated 874-file checksum list. |
| M221–M224 | Clean rebuild reproduced final binary; fmt/Clippy/default/tiny tests and 27-case replay repeated. Final summary claimed completion, then listed quote/fill/mark/indent limitations and ineffective branch scenarios. No Git commit or push occurred. |

The export contains many `... | tail ...; echo $?` commands that report the
pipeline's last process rather than the test's exit. M29/M71 and M191 show
actual failures next to displayed zero statuses. Use reports, explicit child
statuses, subsequent fixes and direct reruns as evidence. The task also
required unique attempt paths, but M35/M39 and later runs repeatedly removed
earlier output directories to reuse them. Thus even a checksummed acceptance
archive cannot establish preservation of every failed attempt/log. This
review kept its own attempts separate and did not mutate source for a test.

## Defect/fix assessment against current source

| Defect | Current evidence and assessment |
|---|---|
| Inherited F1 unsafe prefix slice | `hard_wrap` guards `next.len() >= lead` and prefix equality; original crash fix retained. Case 006 exercises short target and saved bytes; matches freshly. This session did not newly discover/fix F1. |
| Inherited F2 internal NUL treated as LF separator | Production joined bytes and indent are decoded before external-byte replace. Case 027 is a live-target join and mutation-sensitive in M94; freshly matches. Unit test alone is not production coverage. |
| Inherited R3 trim cursor hazard | typed_x guard retained in hard_wrap; case 019 freshly matches. Not new in this session. |
| Inherited addition group close | `last_kind.clear()` after hard_wrap retained; 002 and separate-wrap 003 freshly match. 003 is not multiple wraps in a single ADD chunk. |
| R2 ordinary-history and structural resurrection | Generation remapping/live-marker behavior fixes 020/024/025; failing-before recordings and fresh matches support those sequences. It does not establish all structural identity behavior. |
| R1 whole-line cut retargeting | 026 fixes the reproduced whole-line case and freshly matches. Current generic survivor heuristic creates new errors for empty joins and partial cuts; see below. |
| Identity initialization after file load | `src/files.rs:113–117` assigns loaded lines generations. `new`, `magic`, replace and direct replacement helpers maintain the parallel vector. Broad history/operation invariant still needs tests. |
| Explicit-mark preservation | Previously acknowledged as unverified; now demonstrated wrong with saved-byte consequence. |
| Quote prefix, nonpositive fill, continuation indent | Previously source-confirmed limitations; now each has a runtime mismatch. |

The implementation is coherent enough to retain locally, but its survivor
inference and generic full-span mark mapping are incomplete. Do not describe
F3/F4 as universally closed merely because the previously decisive sequences
pass.

## Fresh verification performed by this review

All commands ran on the existing source without application changes.
Plain `cargo` was initially not found (three commands); reran using
`/home/john/.cargo/bin/cargo`. `audit_spec.py --help` does not implement help;
it actually ran its audit/regeneration and reported no warnings/problems.
No generated application changes resulted.

| Check | Result |
|---|---|
| cargo fmt --check | Pass, actual exit 0 |
| cargo test --release, default | 7/7 |
| cargo test --release --features tiny | 5/5 |
| cargo clippy --all-targets -- -D warnings | Pass |
| cargo clippy --all-targets --all-features -- -D warnings | Pass |
| cargo test --all-features | 5 tests, tiny configuration; does not replace default wrap testing |
| Python comparator/harness/namespace unittest modules | 27/27 (14 + 6 + 7) |
| spec/tools/test_inventory.py | Exit 0; 309 scenarios recorded, zero not-run/uncited. It regenerates CSV metadata; incidental test-runs.csv changes were preserved in /tmp and restored to the entry state. |
| tools/check_wrap_undo.py manifest and real --report | Exit 0, 27 IDs / 27 matches |
| spec/tools/audit_spec.py | No problems/warnings; structural check only |
| Clean optimized default build | Exact final session binary/source identity reproduced |
| Fresh tools/check_follow_up.py --suite wrap-undo | **27/27 exact**, accepted 27, both harness statuses 0; every per-side check true, no declared deviations |
| Ten additional targeted probes | Both harness sides exit 0 with successful steps/checks; comparator finds **eight mismatches and two matches** |
| Deliberately invalid --report | Incorrectly accepted, exit 0; proves checker gap |
| Retained acceptance SHA256SUMS | All 874 entries checked; no mismatches |
| git diff --check | Pass |

Fresh 27-case output: `/tmp/naro-review-20261028/wrap27/report.json`.
Additional scenarios/recordings and comparisons:

- `probe-scenarios.json`, `ref/`, `cand/`, `probe-comparison.json` (five cases).
- `geometry-scenarios.json`, `geometry-ref/`, `geometry-cand/`,
  `geometry-comparison.json` (three cases).
- `negative-scenarios.json`, `negative-ref/`, `negative-cand/`,
  `negative-comparison.json` (two cases).
- `invalid-report.json`, preserved starting diff/status/older review, and a
  checksummed evidence listing in the same temporary directory.

These paths are local temporary review artifacts, not files to commit.
The handoff contains a self-contained generator for the nine decisive
scenarios/control so the next agent does not depend on `/tmp` surviving.
That generator was syntax/execution checked: nine unique cases, with fixture
bytes and arguments matching the observed probes.
The extra nondecisive negative-fill case is retained as evidence of why a
passing boundary example alone was insufficient.

The full 303-case baseline and broad follow-up suites were **inspected from
retained evidence, not rerun in this review**. Their binary/source linkage
is strong because the final build reproduces exactly, but they do not cover
the new failures. No new platform/package/physical-console certification
was performed or inferred.

## New runtime findings and severity

Reference/candidate are the exact hashes above, default features, 80×24
terminal, synthetic fixtures only. Literal `\n` in byte strings below denotes
LF; trailing spaces matter. Counts refer to comparator differences, not
distinct defects. Both sides' minimal exit/temp assertions pass; comparison
is what detects these failures.

| Probe | Differences | Observed failure |
|---|---:|---|
| REVIEW-MARK | 12 | Reference cut preserves first line and yields `eeedd`; candidate cuts nearly everything and saves `b' ddd\n'`. Selection attributes differ before cut. **P1**. |
| REVIEW-EMPTY-DEL | 9 | Reference splits `eee` above `ddd`; candidate joins `eee ddd` after deleting an empty predecessor's newline. **P1**. |
| REVIEW-EMPTY-BSP | 9 | Same incorrect survivor identity through Backspace. **P1**. |
| REVIEW-PARTIAL-CUT | 9 | Cut ending one byte into target should detach that target; candidate preserves its generation and later joins `eee dd` instead of splitting. **P1**. |
| REVIEW-QUOTE | 8 | Reference copies `> ` to overflow and restores cursor x=10 on redo; candidate omits quote prefix and has x=8. **P2**. |
| REVIEW-CONT-INDENT | 8 | Reference samples next paragraph line's two-space indent; candidate copies current line's four spaces. **P2**. |
| REVIEW-FILL-ZERO | 24 | With line numbers and fill 0, reference does not wrap 78-byte line; candidate wraps at reduced edit width. **P2**. |
| REVIEW-FILL-NEG-NUMBERS | 7 | Fill −8: reference second line `cccX`, candidate `bb cccX`; candidate used edit width rather than terminal COLS. **P2**. |
| REVIEW-FILL-NEG-CONTROL | 0 | Same negative-fill fixture without line numbers matches. |
| REVIEW-FILL-NEG | 0 | Initial less decisive negative-fill fixture matches despite differing limits; retained, not presented as disproving geometry bug. |

Exact fixture/action generators, saved bytes and implementation suggestions
are in [NARO_NEXT_STEPS.md](NARO_NEXT_STEPS.md). Key source evidence:

- `src/features.rs:520–530` replaces both lines in full; `src/buffer.rs:382–391`
  clamps an internal mark into the replaced span to its start. Nano
  `src/cut.c:expunge` maps a mark from the eaten line and
  `src/text.c:do_enter` maps it through the split. Nano undo/redo clears mark.
- `src/buffer.rs:346` treats any empty multiline deletion starting at x=0
  as a whole-line cut, keeping gen_b. Nano `expunge` keeps the top node for
  a join even when empty; `extract_segment` keeps bottom only when both x
  endpoints are zero, and keeps top for a partial multiline cut. The Rust
  caller needs operation semantics as well as coordinates.
- `src/features.rs:433` uses `e.indent(&s)`, whereas pinned
  `src/text.c:1244–1246` computes quote length + indentation and do_wrap
  copies quote prefix regardless of autoindent.
- `src/features.rs:426` uses `layout.width + fill`; reference uses terminal
  COLS. `src/render.rs:118–166` distinguishes cols from margin-reduced width.
- `src/features.rs:558–561` always copies current lead; pinned
  `src/text.c:849–887` samples next line when in the same paragraph.

**Checker defect (P1 for acceptance integrity):** `tools/check_wrap_undo.py`
computes and prints hashes without verifying them against expected values.
Its `--report` branch reads matches/accepted but does not enforce them; it
does not validate per-side check flags or provenance/scenario hash.
Starting from coverage.json, the review set summary matches/accepted to zero,
both per-side checks and accepted flags false, reference identity wrong and
binary/scenario hashes wrong, retaining `match: true` and harness statuses
0. It printed **`OK: report 0/27 matches, both harnesses 0`** and exited 0.
CI runs only manifest membership, so it does not guard hard-wrap behavior.

## Test completeness and specification consistency

Runtime coverage is an observation of exact inputs, not a proof of the
description attached to those inputs. The session acknowledges several
false branch labels in its final handoff, but earlier README tables,
coverage prose and broad fix claims still describe them as covered:

| Cases | Evidence from retained reference snapshots and inputs |
|---|---|
| 007 | After Enter, types ` eeee` on blank line; no second wrap. |
| 008 | Deletes one character of `cccc dddd`; final `eeee fff` does not wrap. No overflow node deletion. |
| 012 | Indented target is already 12 columns at fill 14; second wrap is fill-rejected. No accepted matching-indent prefix removal. |
| 013 | First addition yields `  aaa bbb cd`, no wrap/target; later split has no matching-vs-mismatching live-target decision. |
| 014 | Target is `cccc`, not empty/one character. |
| 015 | Interactive tab became spaces; no literal-tab target prefix and autoindent is off. |
| 017 | Second remainder is `eee` and is nonblank-ending; initial target's trailing blank is not the branch predicate. |
| 005/009/010 | Long ` fff ggg` continuation can reject on fill independent of marker validity. 025 is the decisive ordinary-redo replacement; shorten these to test their own advertised clearing branches. |

Case 022 is genuinely before-split now, but fixture hex decodes to
`aaab\0bbb cccc`, NUL offset 4; note claims `aaa\0bbb` at offset 3.
The saved reference first row `aaab^@bbb` confirms the actual fixture.
Case 020's notes call ` fff` three bytes; the literal has four bytes and
the remainder after the split is `fff` (three). State that distinction
precisely when justifying fill acceptance. It remains decisive either way.

`spec/06-undo-redo.md` still has 001–023 citations alongside its new 27-case
paragraph. `spec/97-coverage.md` and Q-UNDO-002 appropriately retain partial
status but overstate general identity closure. The inventory regex change
now preserves suffixes, yet `requirements.csv` can still contain nonexistent
unsuffixed range endpoints (e.g. TEST-NEXT-UNDO-WRAP-001). `audit_spec.py`
checks declarations/paths, not complete suite membership or runtime checks.
It reports 309 baseline scenarios and one follow-up suite row; this is not
a machine-verified mapping of every required hard-wrap branch.

Remaining unverified interactions include broader survivor semantics through
cutbuffer append/replacement, paste/file insert/filter/formatter/speller,
justification and their history; valid targets elsewhere during unrelated
history; mark/prefix/trim/UTF-8/NUL combinations; softwrap, indicators,
resizing, negative-fill extremes and magic-line history quirk. They are
test obligations/source-review risks, not newly demonstrated failures in
this review. Tiny deliberately omits undo/redo and hard wrap; its shared
generation storage merits the normal tiny size/CI gates after buffer changes.

## Retained evidence: what it proves and what it does not

`validation/wrap-undo/archive/hw-acceptance/SHA256SUMS`: all 874 entries
verified with no mismatches. This verifies those bytes, not completeness of
all attempts, correctness of metadata, or behavior outside recorded inputs.

| Session result | Binary/evidence assessment |
|---|---|
| Final wrap 27/27, M155/M222 | `e70159f7…`; archived wrap-27 report and current fresh replay agree. |
| Full baseline 303/301/302, M216 | `e70159f7…`; retained report has four workers 0, six exclusions, only CLI-057 and PROMPT-NUL-001 declared. Not a 303/303 exact match. |
| Edges 13, tools 20, supplement 3, M159 | Inspected target/hw-edges-fix, hw-tools-fix, hw-supplement-fix reports: all exact, `e70159f7…`. |
| Baseline subset 61/61, M158 | `accb57fd…`, not final e701 binary. Final full baseline covers those baseline IDs again. |
| Finder 5/5 and NUL 3/3, M120 | target/hw-find-final2 and hw-nul-final2 use `accb57fd…`. Do not call these fresh final-binary runs. Relevant decisive versions also appear in final integrated 27. |
| Decisive R2, cut and NUL fixed reproductions | Acceptance subreports use `accb57fd…`; final 27 repeats integrated versions with e701. MANIFEST descriptions incorrectly call r2short-fixed e701. |
| Old failures and NUL mutation | `f29e4a48…` old candidate fails structural/cut sequences; mutation hash `6d96965e…` fails production NUL join. Useful preserved causal evidence. |
| “Inventory tests pass”, M223 | M202 ran `build_inventories.py`, which regenerates data. It was not `test_inventory.py`. Distinguish regeneration from test execution. |

Acceptance MANIFEST also names `r2short-cand-failing/` while the actual
directory is `r2short-cand-failing-old/`. The archived source-diff patch
predates final checkpoint wording edits. These are metadata/delivery gaps,
not hash mismatches or evidence that the final application source differs
from the rebuilt binary. Correct provenance descriptions instead of editing
the older recordings to match a desired story.

Full baseline exclusions are CLI-025/032/033/035 (external absolute-path
probes), BROWSE-003 (root-directory browser) and KEY-007 (optional tiny).
CLI-057 differs in file/exit comparison too because NARO avoids a reference
regex crash; PROMPT-NUL-001 differs in prompt behavior while file/exit matches.
Keep these named safety deviations separate from hard-wrap parity defects.

## Git and GitHub review

Inspected status, unstaged/staged diff, diff checks, branch, recent commits,
remote/tracking config and live remote ref. At review entry:

- Branch `main`, upstream `origin/main`, both at `823cb96…`; no staged changes.
- `origin` fetch/push URL `https://github.com/JLuethe/naro`;
  `branch.main.remote=origin`, `branch.main.merge=refs/heads/main`;
  normal remote fetch refspec, `push.autosetupremote=true`.
- `git ls-remote --heads origin main` confirmed live GitHub main still
  `823cb96cc6aba9281b58da7ad33dfa3dd4a6a138` (not just a stale local tracking ref).
- 15 tracked modified files, **614 insertions, 39 deletions** before review
  documentation: workflow; specs 05/06/97/98/99; follow-up matrix;
  generated requirements/audit; audit/harness tools/tests; buffer/features/files.
- Untracked: existing reviews; three opencode session exports; six wrap-undo
  scenario files; checker; validation/wrap-undo tree. This review adds
  NARO_NEXT_STEPS.md and updates the already-untracked NARO_SESSION_REVIEW.md.

Recent history is tiny/profile/delivery work, not these hard-wrap fixes:

| Commit | Subject |
|---|---|
| 823cb96 | Link tiny specification and record verified handoff mirror |
| 3fce053 | Qualify tiny profile with 31 linked gates and preserve completion evidence |
| 0a7cd51 | Implement optional tiny editor with reduced dependencies and oracle fixtures |
| e8e5d7d | Specify optional compile-time tiny profile and acceptance gates |
| 9851330 | Close release qualification with verified delivery receipt |

**Readiness decision: no commit or push now.** The user authorized a normal
commit/push conditional on coherent verified readiness. Saved-byte defects,
misleading branch coverage and a permissive evidence checker fail that
condition. The diff is not validated as completed hard-wrap functionality.
Existing fixes remain available in the user's tree. These review documents
are useful local handoff material, but a documentation-only push would not
complete the requested functional readiness gate and was not performed.

Before a future push: fix/replay the P1 defects, strengthen evidence checks,
complete agreed quote/geometry/indent and branch gates, update provenance/
scope docs, inspect staged paths, check live upstream again, commit and
push normally to the existing branch. Never stage session exports,
temporary files, secrets, binaries or test artifacts. In particular do not
blindly stage the untracked validation archive (874 acceptance files plus
older trees). No commit hash was created in this review.

## Priorities and handoff

1. **P1 explicit-mark corruption:** preserve a failing reference/candidate
   cut result; fix mark mapping in the production join/split and add decisive
   selection/byte/history regression tests.
2. **P1 survivor identity:** distinguish whole-line cut from empty-line
   joins and partial cuts; add operation-specific generation tests and terminal
   controls before expanding to the rest of the structural history matrix.
3. **P1 regression integrity:** make the checker reject inconsistent/stale
   evidence, replace misleading branch tests with decisive cases, and then
   implement/verify the demonstrated quote, geometry and continuation defects.

Mark/identity changes overlap buffer primitives and require coordinated
integration. Checker tests and geometry can proceed independently; quote and
continuation logic share paragraph/lead handling. A full final validation
depends on all implemented fixes and must use one frozen default executable.
Detailed commands, acceptance criteria, reproducer generator, dependencies
and commit exclusions are in [NARO_NEXT_STEPS.md](NARO_NEXT_STEPS.md).

---

## Historical review retained verbatim below

The following earlier review concerns `opencode-session.json` and the
predecessor working tree. Its conclusions, counts and proposed next steps
are historical, not this review's current assessment. Use the current
sections above and NARO_NEXT_STEPS.md for development decisions.


# Naro OpenCode session review

Reviewed on 2026-10-28 against repository HEAD `823cb96cc6aba9281b58da7ad33dfa3dd4a6a138` and its existing working-tree changes.

## Assessment

The session found and corrected two real discrepancies in the five selected scenarios: typing after a wrap could extend the wrong undo group, and a second wrap did not join into the previous overflow line. The retained differential reports support the reported progression from 3/5 to 4/5 to 5/5 exact matches. The broad regression results also exist and retain the established deviations.

However, the new spillage implementation contains outstanding crash and byte-preservation defects, and the new scenarios do substantially less than the documentation claims. Q-UNDO-002 should be described as partially covered until these defects and the missing combinations are addressed. The session's `succeeded` outcome and final “all green” statement do not establish completion of that requirement.

| Priority | Finding | Classification |
|---|---|---|
| P1 | F1: Unconditional removal of the next line's prefix can panic or delete text. | New source defect; runtime reproduction pending |
| P1 | F2: The join passes internally encoded NUL bytes to an external-byte API. | New source defect; runtime reproduction pending |
| P1 | F3: Spillage uses an index that structural edits never update or invalidate. | New source defect; affected sequences untested |
| P2 | F4: Live and recorded spillage state diverge, and undo does not model the reference's node lifetime. | Source inconsistency and predicted compatibility defect |
| P2 | F5: No saved edit bytes, no spillage redo, and no actual multiple-wrap case support several coverage claims. | Confirmed coverage/documentation defects |
| P2 | F6: Status/log preservation, durable evidence, and default-profile lint coverage are incomplete. | Confirmed verification-process gaps |
| P3 | F7: Stale provenance, a wrong reference path, and weak requirement indexing complicate reproduction. | Confirmed documentation/integration defects |

P1 means fix before accepting the spillage change; P2 means resolve before claiming the runtime gap closed. The proposed reproductions and future checks below were **not executed** during this review.

## Review scope and evidence

The complete export contains 183 messages: one user instruction, 178 assistant messages, three background-completion messages, and one idle record. Its 181 tool events comprise 134 shell commands, 31 reads, 13 edits, and three writes. Review covered the instructions, reasoning and progress claims, command inputs and outputs, edit payloads, failures and retries, final summary, current diffs, scenario definitions, runner/comparator code, and retained result trees. Message references below use the export's zero-based `messages` index; they can be located without interpreting terminal timestamps.

The requested work in the original session was to close a hard-wrap undo/redo runtime gap using private fixtures and the pinned GNU nano reference, preserve complete logs and exit statuses, retain existing evidence/deviations, and document exact results and remaining limits. It expressly excluded concurrent full validations, publication, and physical-console certification.

This review used file reads, JSON analysis, hashing, Git inspection, and in-memory reconstruction of the exported edits. It did not build or launch Naro, invoke a harness or audit, execute tests, change source/scenarios/specifications, or alter existing evidence. Only this review document was added to the repository.

### Current repository correspondence

The session began with a clean worktree at the same HEAD. Its final changes are still uncommitted:

| Files | Current correspondence |
|---|---|
| `src/features.rs` | Contains the `last_kind.clear()` fix and the rewritten spillage join. |
| `src/buffer.rs` | Adds `State.spillage: Option<usize>` and initializes it in normal/tiny state construction. No mutation-time maintenance was added. |
| `tests/follow-up/scenarios/wrap-undo.json` | Untracked; contains the same five new scenarios. |
| `validation/wrap-undo/README.md`, `coverage.json` | Untracked; contain the session's compact report and claims. |
| `spec/06-undo-redo.md`, `97-coverage.md`, `98-progress.md`, `99-open-questions.md` | Mark the gap resolved for the default profile and describe the two fixes. |
| `spec/data/requirements.csv` | Contains the change generated by the session's audit. |
| `opencode-session.json` | Untracked session export supplied for this review. |

No session change to the comparator, deviation policy, existing scenario suites, CI workflow, or historical qualification manifests appears in the current diff. The pinned reference checkout is currently clean at `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.

### Build identity matters, but the hash change is explained

Two passing candidate versions must be distinguished:

| Identity | Before formatting | Final/current |
|---|---|---|
| Executable SHA-256 | `108bb0005fa639d818ae97be133204ac43b272c2c4019ef663854cc718eee35f` | `f38607f611702770e857493593816587c66880ddc0cc9bdc6021502b1ff1e9be` |
| Production source fingerprint | `d82e2c4692a8ca2070a12c1e58de15d2acad3c775a7e93c85b4d89b81d403438` | `96838e012cfb51c9155a1d2dd6f3a4d982475fc85b4c3dc128036abb8ef9b489` |

The current `target/release/naro` hashes to the final executable. The current production fingerprint, computed using the input set and hashing convention in `build.rs`, matches the final wrap/edges reports. Applying all exported source edits in memory to HEAD reconstructs the older fingerprint exactly. Comparing that reconstruction with current source shows only rustfmt layout changes in `src/features.rs`; `src/buffer.rs` is identical. Thus the older broad regression is relevant behavioral evidence, although it is not a test of the final executable bytes. The fingerprint embedded by `build.rs` explains why formatting can change the binary hash.

## Outstanding source defects and regression risks

### F1 — P1: Prefix stripping can panic or remove real text

At [src/features.rs](src/features.rs#L499), the join initializes `ni = lead`, skips blanks, and slices `next[ni..]`. `lead` is the current line's indentation length. Nothing checks that the next line is that long or that it has the same prefix.

The pinned reference's `src/text.c` spillage branch strips `lead_len` bytes only when `strncmp` says the two prefixes match, then removes extra blanks. This guard is missing from Naro. The defect also applies to ordinary indentation with no quote prefix; it is not limited to the quoting branch already listed as deferred.

Consequences:

- If the next line is shorter than `lead`, the Rust slice panics.
- If it is long enough but its prefix differs, the join silently removes actual text.
- With multibyte text, skipping an arbitrary byte count can also remove part of a character.

A small proposed reproduction is an initially empty file with `-I -b -r 12`, **without** autoindent: type `    aaa bbb d`, move Up then End, and type ` eee`. Source tracing gives a first-line indentation of four bytes and an existing overflow line `d` of one byte. The second wrap meets the join condition, then attempts `next[4..]`. This sequence has not been run in this review.

Recommended correction: reproduce the reference's conditional prefix comparison and use valid bounds; do not merely clamp `ni`, which would still discard mismatching content. Cover autoindent both on and off, shortened overflow lines, different indentation, and changed indentation between wraps.

### F2 — P1: Joining corrupts embedded NUL bytes

Naro stores external NUL bytes as byte `10` inside a line; see [src/bytes.rs](src/bytes.rs#L243). [Buffer::replace](src/buffer.rs#L252) instead accepts external bytes and splits byte `10` into separate logical lines.

The new join clones the internally encoded current and next lines into `joined` and passes that vector directly to `replace` at [src/features.rs](src/features.rs#L506). An embedded file NUL in either copied line is consequently interpreted as a line separator. It can change file bytes and line structure. If a NUL occurs before the assumed wrap offset, the subsequent split may also operate on a shorter line than expected.

This is distinct from the temporary NUL-literal insertion mistake discussed during the session. That intermediate implementation was replaced; the remaining problem is the final implementation's byte-domain mismatch.

Recommended correction: convert the internal line payload back to external bytes before calling the API, or use an explicitly internal-line operation. Add saved-byte comparisons with NULs before/after the split and in the overflow line, through undo and redo. Existing generic NUL tests do not exercise the new branch.

### F3 — P1: A spillage index survives deletion and line shifts

The new field is assigned in `hard_wrap` and initialized in `Buffer::new`/tiny snapshots. A repository search finds no updates or invalidation when other editing operations change line structure. [Buffer::replace](src/buffer.rs#L264) splices the line vector without maintaining `spillage`; `enter`, `delete`, `cut`, insertion, and paste use this operation, and other features also mutate lines.

An in-bounds index is not a stable identity:

- Inserting a line before the overflow moves the actual overflow but leaves the index behind. A later wrap can fail to join the real overflow or join an unrelated successor at the old index.
- Deleting the overflow can leave the marker pointing at the next ordinary line, making that line eligible for an unintended join.
- Being temporarily out of range does not make the marker safe: later line insertion can make the stale index valid again.

The reference keeps a node pointer and clears it in `delete_node` when that node is freed (`src/nano.c:100–109`); renumbering other nodes does not retarget that pointer. Naro's numeric equality check cannot provide equivalent behavior without maintenance.

The session explicitly recognized this issue in messages 88–91 and 116, then left management “minimal” in message 117. The final report does not disclose that limitation.

Recommended correction: define an invariant that preserves actual line identity across structural changes, or maintain/clear the index at every relevant mutation according to the reference. Add insert-before, delete-overflow, cut/paste, and undo/redo sequences before claiming the join implemented generally.

### F4 — P2: History snapshots do not consistently represent spillage lifetime

At [src/features.rs](src/features.rs#L553), `last.after` is cloned **before** `state.spillage = Some(line0 + 1)`. The newly created marker is absent from that operation's recorded after-state, so the session's claim that keeping it in `State` automatically carries the correct state through history is false. Conversely, an operation's before-state can restore an old marker when undoing a later wrap.

Reference semantics need care here. Nano's undo of the split deletes the overflow node and clears `spillage_line`; redoing an ENTER constructs a new node without necessarily making it the spillage target. Simply moving the assignment before the snapshot is therefore not a demonstrated compatibility fix.

One missing sequence is: create an overflow, perform the second spillage wrap, undo only that second operation, then edit the predecessor enough to wrap again. Naro restores the old `Some(index)` from the before-state; source inspection of nano's split undo and node deletion predicts a cleared marker. Another is redo followed by further wrapping. These can diverge even when the immediate undo/redo screens look identical.

Recommended correction: explicitly establish the reference's marker lifetime through history and implement that policy. Test continued editing after undo/redo, not just the displayed restored text. Runtime confirmation of these sequences remains outstanding.

## F5 — The new coverage is narrower than reported

The five retained scenarios are valid differential observations, but their names and documentation overstate several dimensions:

| Case | What it actually exercises | Missing or inaccurate claim |
|---|---|---|
| `001-MID` | Mid-line typing, one wrap, undo, redo, cursor/screens. | No edited file is saved or captured. |
| `002-CHAIN` | A wrap, Home/End, another addition, two undo and two redo steps. | Useful regression for group closing. The note saying movement itself breaks the group is misleading; returning to the addition endpoint normally permits continuation, while the wrap reset causes this separation. |
| `003-MULTI` | One batched text insertion and one automatic split, then undo/redo. | It does **not** exercise two wraps. |
| `004-INDENT` | One autoindented wrap, undo, redo. | Does not combine indentation with a spillage join, so it misses F1. |
| `005-SPILL` | A second wrap joining into overflow, then two undo steps. | No `M-E` occurs: spillage redo is entirely untested. No saved bytes or continued edits after history restoration. |

For `003-MULTI`, the retained reference and candidate `multi-wrap` snapshots contain `aaa bbb ccc` on the first text row and `ddd eee fff ggg` on the second, with cursor `(15, 2)`. The latter is still longer than fill 12. There is one new break, not two. The same output was visible during the session in message 59, yet the two-wrap claim persisted in the scenario note, README, progress log, and resolution entry. `Editor` batches queued text and calls `hard_wrap()` once for the insertion; a long `text` step does not prove repeated wraps.

Every new scenario exits with Ctrl+X and an `n` answer, and none contains Save or `capture_file`. Their final `work/f.txt` bytes equal their starting fixtures. `captured_files` is empty. Their only explicit checks are successful exit and empty temporary storage. The differential comparator does compare screens, attributes, cursor/modes, input bytes, final fixture, and exit state; its comparison is meaningful, but those final bytes do not establish the bytes of unsaved edits.

The visible Modified indicator provides some modified-state coverage. It does not establish a newly saved point followed by undo/redo back across that point. Existing `TEST-NEXT-EDIT-002` covers a simpler save/wrap sequence and still passes; it does not substitute for saving the new spillage/indentation combinations. The session's temporary saved-byte probe in message 106 confirmed a trailing space for a simple first wrap, but that probe was not added to the permanent suite and did not cover the final join implementation.

Recommended coverage before resolving Q-UNDO-002:

1. Force genuinely separate wrap events with settled input steps and record each event; assert the resulting logical lines and intended undo boundaries against nano.
2. Redo the spillage operation, continue editing after undo and redo, and verify redo invalidation after a divergent edit.
3. Add saved fixtures and `capture_file` observations at meaningful stages, with expected hex bytes. Keep separate cases where saving would itself change undo grouping. Compare Modified before save, after save, across undo, and after redo to the saved point.
4. Combine spillage with autoindent on/off, equal and unequal prefixes, short/empty next lines, tabs, UTF-8 and NUL payloads, trimblanks on/off, a remainder ending in a blank, and a join that is refused because it exceeds fill.
5. Cover structural changes around the overflow and the existing acknowledged axes: quoting, soft wrap/view behavior, magic-line backspace, selection/paste, and multiple buffers where relevant. Preserve documented exclusions instead of claiming exhaustive combinations.

## What the recorded checks establish

These are existing session results inspected during the review, not fresh executions by this reviewer.

| Check | Recorded result | Candidate/evidence and limit |
|---|---|---|
| Initial new suite | 3/5; exit 1 | Message 42: CHAIN and SPILL differ. |
| After undo-group fix | 4/5; exit 1 | Message 68; CHAIN fixed, SPILL still differs. |
| Intermediate join | 4/5; exit 1 | Messages 107/118; first implementation still wrong. |
| Completed new suite | 5/5; exit 0 | Older binary: `target/new-wrap-undo/report.json`. |
| Final new suite | 5/5; exit 0 | Current binary: `target/new-wrap-undo-final/report.json`; both harness statuses 0 and all recorded checks true. |
| Baseline undo/edit/move | 55 matches | Retained subset recordings/diff; comparator process itself exits 1 because 254 unrelated recordings are absent. |
| Full default baseline | 303 recorded, 301 full matches, 302 file/exit matches, six skipped; all four worker statuses 0 | Older binary: `target/new-baseline-full/report.json`. Only differences are declared `TEST-CLI-057` and `TEST-PROMPT-NUL-001`. |
| Edges | 13/13 exact | Older and final binaries: `target/new-edges-regression` and `target/new-edges-final`. |
| Tools | 20/20 exact | Older binary: `target/new-reg-tools/report.json`. |
| Supplement | 3/3 exact | Older binary: `target/new-reg-supplement/report.json`. |
| Backup and FIFO EOF | 1/1 exact each | Older binary: corresponding `target/new-reg-*` reports. |
| HUP/TERM tool cleanup | One accepted difference each; zero exact matches | Older binary: corresponding signal reports. Both are `Q-TOOL-001`, not new failures and not exact matches. |
| Environments | 13/13 exact | Older binary: `target/new-reg-environments/report.json`. |
| CLI | 38/38; eight excluded | Messages 127/180; retained `spec/evidence/naro-cli/report.json` identifies the final binary. |
| Regex | 81 cases in each of two locales; zero differences | Older binary: `spec/evidence/naro-regex/report.json`. |
| Rust release unit tests | Default six passed; tiny five passed | Messages 128/129; existing tests, with no new hard-wrap unit regression. |
| Comparator/harness tests | 14/five passed | Message 139. |
| Formatting | First failed, then passed after `cargo fmt` | Messages 130/131. |
| Strict Clippy | Passed `--release --all-features -- -D warnings` | Messages 130/180; important default-profile omission below. |
| Specification audit | No problems/warnings | Messages 162/177; structural audit, not proof of new runtime coverage. |

Across the eight follow-up suites listed in the checkpoint, there are 53 scenarios: 51 exact and two declared cleanup differences. “All match exactly including the differences” in the progress log is inaccurate wording; “all accepted, 51 exact” describes the reports.

The six baseline exclusions are five fixture-policy/external-path cases and the default run's tiny-profile case. Eight separate CLI exclusions remain. No new standalone safety-assertion suite, package/install qualification, root/home suite, real guest-VT run, or physical-console certification is recorded for these changes. Historical tiny/default/closure gates remain evidence for their own fingerprints. The session did run tiny unit tests, so “tiny qualification not rerun” should not be read as “no tiny check was run.”

## F6 — Verification and evidence preservation gaps

### Default-profile Clippy was not run

The session used `cargo clippy --release --all-features -- -D warnings`, without `--all-targets`. In [src/main.rs](src/main.rs#L8), enabling `tiny` selects `tiny_features.rs` instead of `features.rs`. Therefore that command excludes the main edited hard-wrap implementation. The default release build and unit test compile it, but do not establish strict default Clippy success. The repository's CI correctly has separate default and all-features Clippy commands with `--all-targets`; that workflow was not run against these uncommitted changes during the session.

### Not all command statuses and logs were preserved

Many commands correctly printed `PIPESTATUS[0]`, and the final wrap/full reports corroborate success. However:

- Build pipelines in messages 36, 67, 117, 121, and 177 pipe through `tail` without independently preserving the build status. A successful `tail` can mask an unsuccessful build; an older executable could then be tested. The observed build output shows successful builds, so this is an auditability gap rather than proof of a failed build.
- Follow-up loops in messages 70 and 126 discard each runner's status. The latter captures a `tail` pipeline in command substitution and prints only its summary. Retained reports rescue the final results, but the blanket claim “all command exit statuses were preserved” is unsupported.
- Most compiler/test output was truncated with `tail` without a full log destination. The release unit-test output happened to include all six test results; other commands do not provide the complete logs originally requested.
- The follow-up runner preserves full reference/candidate logs per output directory, and the full validator preserves four worker logs. Those successful paths are stronger evidence than the shell tail alone.

### Failed evidence was overwritten

The runner refuses existing output directories, but the session repeatedly precedes it with `rm -rf target/new-wrap-undo`, and also reuses regression directories. Initial failing recordings, diffs, and frozen binaries from the 3/5 and intermediate 4/5 runs are no longer retained in those directories. The export preserves commands and displayed output; the permanent scenario remains a useful reproducer. It does not preserve the complete before-fix result trees requested by the user.

The current successful trees are also under gitignored `target/`. Only a compact coverage JSON and README were prepared for version control. That JSON omits environment/build details, per-side assertion results, and a durable link/hash for the complete final report. This is weaker than the linked provenance approach used by the existing qualification gates.

### Timeouts and comparator failures were handled, with limitations

- Messages 71 and 123 hit the shell's 120-second timeout during the 55-case replay. The session reran them in the background and eventually recorded harness exit 0. These are orchestration timeouts, not demonstrated editor test failures. The export does not explicitly establish that every child of each timed-out attempt stopped before the same fixture IDs were reused; separate output directories alone do not isolate `/tmp/nanospec-work/<scenario-id>`.
- Messages 80 and 137 compare the complete 309-case reference tree with a 55-case candidate subset, yielding exit 1 and 254 missing-evidence differences. The later exact count of 55 matches/zero subset differences is supported by the retained diff JSON. Calling the comparator invocation itself a pass would be wrong. Future subset comparisons should explicitly select the expected IDs and fail on missing records within that subset.
- Minor inspection failures included a nonexistent `spec/tools/environment.py`, cargo/rustc absent from PATH (resolved using `~/.cargo/bin`), a `KeyError: steps_ok` on older reference-schema evidence, an out-of-range CSV read, and progress `grep` commands returning 1 when no completion text existed. None demonstrates a product defect. The session also repeatedly polled despite its background tool's instruction to wait for completion notifications; this added noise without improving coverage.

Only one full baseline validation is visible, with four disjoint internal partitions, after the subset replay completed. There is no evidence of another concurrent full validation, publication, or physical-console certification. Those original scope restrictions appear respected.

## F7 — Documentation and integration corrections needed

1. **Reopen/narrow the resolution.** `spec/06-undo-redo.md`, `97-coverage.md`, `98-progress.md`, and `99-open-questions.md` currently imply all default chunk combinations are addressed. Retain the five-case result, but list F1–F5 and the untested branches explicitly. Tiny has no undo/redo by design; calling tiny undo “source-specified” is misleading and does not describe a missing tiny implementation obligation.
2. **Fix the MULTI and byte/save claims.** The suite proves one batched split in MULTI, unchanged on-disk fixture bytes, visible state in the captured screens, and no redo in SPILL. Correct each repeated claim, including the new README's broad statement that the documented combinations are covered.
3. **Correct the reference executable.** `validation/wrap-undo/README.md:36` names `~/src/nano-install/default/bin/naro`. The runner and session actually use `~/src/nano-install/default/bin/nano`.
4. **Identify both candidate versions.** `coverage.json` names final `f38607…`; `spec/98-progress.md:36` still names older `108bb0…`. Label the broad older run and final targeted rerun separately instead of presenting a single candidate identity.
5. **Document scenario hash serialization.** The compact coverage hash `1e8c3655dd03c8bf34c3a537e1edd9f0e65c1670fe5912e9961f3117cec3bac5` is valid for canonical JSON with sorted keys and compact separators, as explicitly computed in message 144. The runner hashes its pretty-printed scenario bytes, producing `d36f4aa8c9f2fd5362bc9a3a5e8f13795cdb1f6aa2d30abe15bc866a6052692d`; the repository file's raw hash is `c32a8933845c445d08a5e6b6306328b2bab376fe072eda0e66f29d1d4cc99b91`. These are different conventions, not evidence of scenario tampering. Specify the convention or preserve the runner's hash alongside the canonical one.
6. **Do not treat the regenerated index as coverage validation.** The audit's regex truncates suffixed IDs and does not expand `001…005`. It generates `TEST-NEXT-UNDO-WRAP-001` under UNDO-008, although no scenario has that exact ID. It also drops the old nearby `TEST-UNDO-010` reference. The file is explicitly a heading/nearby-test index, so this is an indexing limitation; the session's claim that this validates the new evidence is stronger than the audit supports.
7. **Integrate future regression protection.** The standalone wrap suite is not executed by `.github/workflows/rust.yml`, `validate_parallel.py`, or the structural audit's baseline scenario scan. It is not linked from a machine-checked new gate. Preserve historical follow-up gates, but add an explicit current regression entry or dedicated checked manifest so these cases cannot silently disappear. A clean audit currently says nothing about the standalone report's consistency or whether MULTI/redo/save claims are true.

The older specification still lists broader source-only/platform/operator limits. This session did not remove them, and the new fixes do not certify arbitrary libc, terminal, locale, build configurations, or hardware behavior.

## Recommended next steps

1. Preserve the existing session export, current diff, successful result trees/logs, frozen executables, and both build identities before cleanup. Use unique attempt directories and a retained manifest for subsequent work. Do not rewrite historical reference evidence or broaden normalization to hide discrepancies.
2. On the next authorized implementation/testing pass, first add isolated reproductions for F1–F4 against the pinned nano executable. Start with the short overflow/no-autoindent case and NUL byte preservation, then structural changes and continued editing after history restoration. Record actual reference behavior before choosing the spillage lifetime policy.
3. Correct the prefix, byte-domain, and identity/lifetime handling. Keep the independently supported undo-group fix. Preserve each failing recording before modifying the implementation.
4. Repair the coverage suite as described in F5, including genuine repeated wraps, spillage redo, and saved-byte/saved-point checks. Add focused automated regression protection to the normal verification workflow without changing old qualification results.
5. After those changes, run the focused suite and affected undo/edit/move, byte, and edge checks on one frozen candidate. Run default and all-features Clippy with all targets, appropriate default/tiny unit checks, formatting, and comparator/harness checks. Expand to one serially scheduled full baseline and relevant follow-up/safety checks once the focused results are sound. Capture complete logs and exact statuses; stop and account for failures before continuing.
6. Update the compact report from the actual final runner report, include source/build provenance and assertion outcomes, correct the documentation and reference path, and state the remaining exclusions. Only then reconsider Q-UNDO-002's resolved status. Package, platform, guest-VT, and operator work should remain separate unless the eventual changes or intended release scope warrant them.

No implementation changes or tests have been performed as part of this review.

## Session traceability

This table maps the complete export to the analysis above; routine inspection and waiting messages are grouped rather than reproduced verbatim.

| Message range | Activity and review disposition |
|---|---|
| 0–35 | Original scope, checkpoints, baseline/follow-up scenarios, harness/comparator, buffer/editor, reference/toolchain/binary inspection. Existing save/undo coverage was found; initial binary hash was `21172c…`. |
| 36–41 | Release build and design/write of five scenarios. No separate new generator or CI integration was added. |
| 42–65 | Initial 3/5 failure, detailed screen/cursor investigation, reference-source grouping and spillage analysis. Older-schema inspection error was recoverable. |
| 66–81 | Group reset added; 4/5 result; existing follow-up checks; first subset timeout/retry/comparison. Missing unrelated evidence explains comparator exit 1. |
| 82–98 | New field/constructors; discussion of structural invalidation; reference join and byte-width inspection. Recognized lifetime issue was not implemented. |
| 99–120 | Intermediate join implementations, temporary NUL insertion mistake, screen/trailing-space confusion corrected by a saved-byte probe, failed 4/5 attempts, final full-current-line join correction. |
| 121–140 | First 5/5 success; regression suites; second subset timeout/retry; default/tiny unit checks; formatting failure/fix; comparator/harness tests; one full baseline started. |
| 141–152 | Compact report/README and spec edits; canonical hash computation; unsupported MULTI/save/redo claims propagated. |
| 153–173 | Progress polling, final source read, scenario listing, structural audit and requirements regeneration; full validation completes with established counts and exit 0. |
| 174–182 | Confirmed baseline documentation, rebuild after formatting, final 5/5 suite, manual candidate-hash update, final edges/CLI/all-features Clippy, summary and idle record. Final summary overstates completeness/status preservation; no publication or new qualification gate was created. |

For an exact export identity, `opencode-session.json` SHA-256 at review time is `8397d9de4e694590059ef0a394289214af6d13edd045545b367e6ac043d32033`.
