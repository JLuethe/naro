# 98 — Progress log

Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

This file lets a later session resume without the earlier conversation.

## Codex Pi-review checkpoint (2026-10-28)

The prior “final” checkpoint below is historical. Its 39 matching cases missed
split-origin mark double movement and join-origin prefix/blank mapping, including
two caught crashes. Codex fixed those transforms and generic marked-filter
sequencing/cursor/failure cleanup, added 19 wrap regressions/controls and six
filter cases, and made the report gate require and recompute its evidence.

The current authoritative review, results, remaining work and testing-only
handoff are `../NARO_PI_TEST_REVIEW.md`, `../NARO_DEVELOPMENT_PROGRESS.md`,
`../NARO_NEXT_STEPS.md` and `../NARO_TEST_AGENT_HANDOFF.md`. Q-UNDO-002 stays
partial. A burst ending in a blank reaches the no-added-space branch; earlier
claims that it was unreachable were wrong. Binary hashes change when the
embedded Git revision changes even if production inputs are unchanged.

## Hard-wrap undo/redo parity checkpoint (2026-10-28, final)

This checkpoint supersedes the generation-model checkpoint below: the same
model is kept, and the reviewed defects that it did not cover are now
reproduced, fixed and covered by decisive cases.

### Reproduced defects (failing before, matching after)

The review's targeted probes were replayed against the pinned reference
(`6ed285c3ec7a1d228def4d4e7021c6ba269f620c`, executable SHA-256
`b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2`) and a
fresh default build. Both harnesses reported PASS, because their expectations
only assert the exit status; the differential comparison found eight
mismatches and one match:

| Probe | Reference | Old candidate |
|---|---|---|
| `REVIEW-MARK` | `b'aaa bbb ccc  \neeedd\n'` | `b' ddd\n'` |
| `REVIEW-EMPTY-DEL` | `b'aaa bbb ccc \neee\nddd\nTAIL\n'` | `b'aaa bbb ccc \neee ddd\nTAIL\n'` |
| `REVIEW-EMPTY-BSP` | as above | as above |
| `REVIEW-PARTIAL-CUT` | `b'aaa bbb ccc \neee\ndd\nTAIL\n'` | `b'aaa bbb ccc \neee dd\nTAIL\n'` |
| `REVIEW-QUOTE` | `b'> aaa bbb \n> ccc dddX\n'` | `b'> aaa bbb \nccc dddX\n'` |
| `REVIEW-CONT-INDENT` | `b'    aaa bbb \n  cccX\n  zzz\n'` | `b'    aaa bbb \n    cccX\n  zzz\n'` |
| `REVIEW-FILL-ZERO` | one 78-byte line | wrapped at the reduced edit width |
| `REVIEW-FILL-NEG-NUMBERS` | second line `cccX` | second line `bb cccX` |

The failing recordings are kept outside the repository; the permanent
regressions are `TEST-NEXT-UNDO-WRAP-028-MARK` … `035-FILL-NEG`, and the
pre-fix candidate (`e70159f7…`) still fails exactly those eight cases.

### Fixes

1. **Explicit mark through a join and split.** `Editor::hard_wrap` now
   reproduces the reference's operation sequence (optional added space, the
   join with the overflow, the duplicated-prefix removal, the blank trimming,
   the `do_enter` split) and maps the mark with the reference's `expunge` and
   `do_enter` rules. A mark on the eaten line moves onto the joined line, a
   mark behind the join point shifts over the removed prefix and blanks, and
   a mark behind the wrap point moves to the continuation. Undo and redo
   still clear the mark, as the reference does.
2. **Operation-specific node identity.** `Buffer::replace` takes an explicit
   `Splice` policy: `Plain` (the top node survives), `Join` (the top node
   survives and the bottom node is freed, like the reference's `expunge`),
   `Cut` (a whole-line cut keeps the bottom node, any other cut keeps the
   top node, like `extract_segment`) and `Replace` (a wholesale replacement
   frees every node in the span). The old coordinate heuristic also matched a
   join over an empty predecessor and a partial multiline cut.
3. **Quote prefix.** The wrap uses the reference's `quote_length` plus
   `indent_length` as the line's lead, suspends automatic indentation for a
   quoted line and copies the quote lead to the continuation line.
4. **Wrap geometry.** A nonpositive fill now uses the terminal width
   (`COLS + fill`) like the reference, not the margin-reduced edit width.
5. **Continuation indent.** The split samples the next line's indentation
   when that line is in the same paragraph and is not a paragraph start, as
   the reference's `do_enter` does.

### Scenario suite

`tests/follow-up/scenarios/wrap-undo.json` grew from 27 to 38 cases. The
formerly ineffective branches were repaired so that each reaches its
advertised branch: `007-INSERT` (the moved overflow is really joined),
`008-DELETE` (a node is really removed and an unrelated successor is not
joined), `012-AUTOSpill` (the matching indent prefix is really stripped),
`013-MISMATCH` (two nonempty, unequal prefixes), `014-EMPTY` (a target
reduced to length zero), `015-TABS` (a literal tab from the fixture),
`017-WSTRAIL` (the whitespace at the join point) and the `005`/`009`/`010`
redo continuations (a remainder that the fill would accept). The new cases
`028`…`039` cover the explicit mark, the empty-predecessor Delete and
Backspace joins, the partial multiline cut, the quote prefix, the
continuation indent, the nonpositive fill, a one-character target and a
paste that edits or shifts the live target.

### Verification tooling

`tools/check_wrap_undo.py` now fails closed. It validates the exact 38 case
IDs, the manifest structure, and — for a recorded report — the exact result
membership, every per-side assertion and comparison flag, the summary
counts, both harness statuses, the pinned reference commit and executable,
the candidate's source fingerprint (the `build.rs` convention) and the
scenario digest of the inputs that were replayed. `tools/test_check_wrap_undo.py`
covers the failure modes (a report with zero matches, failed side checks, a
wrong reference, a wrong candidate, a wrong scenario digest, a stale source
fingerprint, a missing or extra result, differences, a declared deviation, an
inconsistent summary and a tampered manifest). The review's false-acceptance
experiment (a report with `matches: 0`, failed checks and wrong identities)
is now rejected.

`spec/tools/audit_spec.py` resolves citations to recorded case IDs: a glob,
a path prefix or a family range no longer becomes an inventory entry, and
the cited IDs without a recorded scenario are reported as an audit warning.
`spec/tools/test_audit_spec.py` adds fixture tests for the new semantics.

### Verification against the frozen default binary

One frozen default build (`target/next-default/release/naro`, SHA-256
`eeb23513046dffe86526b39c8333e6609ca9bf6959f3241ca2707502b12d59e2`, source
fingerprint `522a6c33202ed6de6abe209bbe86e5f86a7ff49d0de0f41da11dca9f75a45e4e`,
features `""`) was used for every comparison:

| Check | Result |
|---|---|
| `cargo fmt --check` | pass |
| `cargo clippy --all-targets -- -D warnings` (default) | pass |
| `cargo clippy --all-targets --all-features -- -D warnings` | pass |
| `cargo test --release` (default) | 9/9 |
| `cargo test --release --features tiny` (separate target dir) | 5/5 |
| `cargo test --all-features` (separate target dir) | 5/5 (tiny configuration) |
| comparator/harness/namespace unittests | 27/27 |
| `tools/check_wrap_undo.py` and its negative tests | pass (21 tests) |
| `spec/tools/audit_spec.py` and its fixture tests | pass (no problems, 9 tests) |
| `spec/tools/test_inventory.py` | 309 scenarios recorded, 0 not run, 0 uncited |
| wrap-undo suite (`tools/check_follow_up.py`) | 39/39 exact, both harnesses 0, no deviations |
| edges / tools / supplement suites | 13/13, 20/20, 3/3 exact |
| full baseline (`tools/validate_parallel.py`) | 303 recorded, 301 full matches, 302 file/exit matches, 6 skipped, 4 worker statuses 0; only the declared `TEST-CLI-057` and `TEST-PROMPT-NUL-001` differences |

The full baseline compares against the retained reference recordings, which
contain the fixture path; a message that names the path is centered in the
terminal, so that run has to use the default `/tmp/nanospec-work` root or ten
unrelated cases differ in padding only.

## Hard-wrap undo/redo generation-model checkpoint (2026-10-28, later)

The spillage identity/lifetime defects (RC1 structural undo, RC2 whole-line
cut) and the production NUL join gap (RC4) were reproduced and fixed.

### The generation-based identity model

`State.spillage` is now a stable per-line **generation** (a `Vec<u64>` parallel
to `lines`), not a numeric line index. A line keeps its generation across
in-place edits; a freed line discards it; a recreated line (including by
undo/redo of a join, Enter, or cut) gets a fresh generation. `Buffer::undo`
/`redo` reassigns fresh generations to lines whose snapshot generation is no
longer live, so restoring text does not resurrect a freed target. `Buffer::
replace` assigns the survivor's generation to the spliced endpoint (the
following line for a whole-line cut, the top line for a join/split) and a
fresh generation to the eaten or split line; a dangling-marker check clears
`spillage` when its generation leaves the buffer. `hard_wrap` sets `spillage`
to the new overflow's generation and the join condition compares it to the
generation at the successor line. `files::parse` and `Buffer::magic` maintain
`generations` on load and magic-line creation.

This replaces the previous index-based heuristic, which restored a deleted
target after undoing an ordinary Delete/Backspace join (`020-DELJOIN`/`
024-BSPJOIN`) and retargeted to the following line after a whole-line cut
(`026-CUT-TAIL`). Both were reproduced as failing candidate runs (the old
release joined into `fff eee ddd` / `eee TAIL` respectively) against the
reference which splits; the fixed build matches the reference.

### Decisive cases added to the 27-case suite

The suite grew from 23 to 27 cases (`tests/follow-up/scenarios/wrap-undo.json`).
The decisive additions exercise the previously untested branches:

| Case | Defect | Decisive because |
|---|---|---|
| `020-DELJOIN` | RC1 | Shortened remainder ` fff` (3+7≤12) makes marker validity, not fill rejection, decide; old release joined `fff eee ddd`, reference splits. |
| `024-BSPJOIN` | RC1 | Backspace-join equivalent of 020. |
| `025-CHAIN-REDO` | R2 ordinary | Integrated from the finder suite; ordinary-addition redo must not resurrect the spillage marker. |
| `026-CUT-TAIL` | R1 cut | Whole-line cut of the spillage target; the cut detaches the target so the next wrap splits, not joining the successor. |
| `027-NUL-JOIN` | RC4 | A payload NUL in the live overflow target exercised through an actual production second-wrap join; removing `decode_nuls` corrupts this case (mutation-verified). |

The `022-NULBEFORE` fixture was corrected so the NUL is before the actual split
point. `011-SAVE`'s note is corrected (the undo states were swapped). A
production NUL-join regression (`tools/check_wrap_undo.py` manifest) is CI-
checked.

### Other fixes

`spec/tools/audit_spec.py`'s requirement-ID regex now captures full
multi-segment IDs (no `AUTOS`/`UNDO-ONE` truncation). A focused
`not_contains` harness unit test was added to `test_nanoharness.py`. The
`020-DELJOIN` remainder was shortened from ` fff ggg` (7+7>12, fill-rejected)
to ` fff` (3+7≤12, marker-decided).

### Verification

27/27 wrap-undo exact matches, both harnesses 0, against the pinned reference.
5/5 finder, 3/3 NUL, 61/61 undo/edit/move/bytes, 13/13 edges, 20/20 tools,
3/3 supplement, default 7 / tiny 5 Rust tests, `cargo fmt --check`, default
and `--all-targets --all-features` Clippy pass. The production NUL join was
mutation-verified (removing `decode_nuls` from the join path corrupts `027`).
The explicitly required full baseline against the final frozen candidate
completed: **303 recorded / 301 full matches / 302 file/exit matches / 6
skipped / 4 worker statuses 0**, with the two unchanged declared safety
deviations (`TEST-CLI-057`, `TEST-PROMPT-NUL-001`) and no new mismatches.
The acceptance archive (`validation/wrap-undo/archive/hw-acceptance/`)
contains the final 27-case run, the decisive reproductions (R2-structural
pre-fix failing / fixed, R1-cut pre-fix failing / fixed, NUL-join mutation
failing), the frozen final binary, the source diff, and a file-by-file
SHA256SUMS manifest.

### Provenance

Candidate binary `e70159f7f0cd4d10af7a4576dafec56523de377f8b7451c2058e479fff8f4a1d`,
source fingerprint `860f62a4f6c2f79b12167c456511ada0ecb9b284070cc58ca6ef60fdfdc47e09`
(build.rs convention over `src`, `native`, `assets`, `Cargo.toml`, `Cargo.lock`,
`build.rs`, `CREDITS.md`), revision `823cb96`, rustc 1.99.1, default features `""`.

### Remaining limits

The quoting-prefix join branch (R8), nonpositive fill with margins (S1), live
explicit mark preservation (S2), and continuation autoindent sampling (S3)
are source-confirmed but not yet verified at runtime. The ineffective branches in
`007-INSERT`, `008-DELETE`, `012-AUTOSpill`, `013-MISMATCH`, `014-EMPTY`,
`015-TABS`, `017-WSTRAIL` match the reference but do not exercise their
advertised branch. See `../validation/wrap-undo/README.md` for the full list.



The user requested addressing the documented runtime gap for hard-wrap
undo/redo combinations (Q-UNDO-002 in `99-open-questions.md`, hard-wrap axis of
NEXT-EDIT-001 in `19-completion-and-release.md`). Default and tiny qualification
were already complete; this phase added deterministic differential scenarios
for the default profile and fixed four reproduced source defects plus the
trimblanks cursor hazard in `src/features.rs`/`src/buffer.rs`.

Added `tests/follow-up/scenarios/wrap-undo.json` with twenty-three isolated
fixture scenarios, each replayed against the pinned GNU nano 9.3 default build
through `tools/check_follow_up.py` (fresh output directory; existing reference
evidence and declared deviations in `spec/evidence/follow-up-runs/` were
preserved). The suite is linked from the follow-up matrix
(`TEST-NEXT-UNDO-WRAP-SUITE` under `NEXT-EDIT-001`), so the audit and matrix
discover it.

Result: 23/23 exact matches across file bytes, modified/saved state, cursor
and screen through undo and redo, with `capture_file` saved-byte checks for the
structural, save, prefix, NUL, and option-combination scenarios. No declared
deviations. Both harness statuses are 0. Coverage recorded in
`../validation/wrap-undo/coverage.json` and `../validation/wrap-undo/README.md`.
Candidate binary SHA-256
`f29e4a48b21709f43eea66922a28d60068a14bf2785b05a288759710adb70eba`
(release build, `cargo build --release`, default features `""`); production
source fingerprint
`d7791f978fb8bf02ecd297d9c041d03f452e85a207448406e16c666f602307ea` at revision
`823cb96cc6aba9281b58da7ad33dfa3dd4a6a138`. The `coverage.json` records three
scenario hashes by serialization convention: canonical (sorted keys, compact
separators, `a263251d…`), raw source file bytes (`0c53d7cd…`), and the runner's
frozen pretty-printed file (`8fe946d0…`).

Four source defects were reproduced and fixed, plus the trimblanks cursor
hazard:

1. **F1 — unsafe prefix removal (crash).** The spillage join started stripping
   the next line at `lead` bytes unconditionally, which panicked when the
   overflow line was shorter than `lead` and silently deleted real text when
   the prefixes differed. Reproduced by `TEST-NEXT-UNDO-WRAP-006-PREFIX`: the
   starting candidate crashed with code 6; the reference saved
   `    aaa bbb  \neee d\n`. The join now strips the duplicated leading part
   only when `next[..lead] == s[..lead]` (nano's `strncmp`).
2. **F2 — embedded-NUL corruption.** The join assembled internally encoded line
   bytes (byte 10 = payload NUL) and passed them to `Buffer::replace`, which
   accepts external bytes (LF separators, NUL payload) and split on byte 10,
   turning a payload NUL into a spurious line break. The join now converts the
   joined line back to external bytes with `bytes::decode_nuls` before calling
   `replace`, and the split `replacement` indent is likewise decoded.
   Reproduced by `TEST-NEXT-UNDO-WRAP-022` (NUL before the wrap point) and
   `023` (NUL after), loaded from hex fixtures and wrapped by ordinary typing,
   plus the Rust unit test `spillage_join_preserves_embedded_nul`.
3. **F3 — stale spillage identity (R1).** `State.spillage` is a numeric line
   index. `Buffer::replace` maintains it for ordinary structural edits (the
   top survives at `a.line`, the bottom survives at `a.line + count - 1` when
   `count > 1`, interior lines are freed, lines below shift). Direct
   `state.lines` splices in `justify` and the whole-buffer formatter/speller
   replacement now call `spillage_no_survivors` / `spillage_clear` so a marker
   in the replaced range is cleared. Reproduced by `TEST-NEXT-UNDO-WRAP-007-INSERT`
   (insert before overflow, marker shifts, join happens on the moved overflow)
   and `008-DELETE` (delete the overflow, marker cleared, next wrap splits).
4. **F4 — spillage lifetime through ordinary history (R2).** `hard_wrap`
   records `None` in both the before- and after-state of the wrap history item
   (`Undo.is_wrap`) so undo/redo of a wrap yield no spillage, matching the
   reference's clear-on-undo / no-set-on-redo node lifetime. Ordinary history
   items preserve the live marker (undo/redo of a non-structural edit must not
   change it), and structural items restore it from the snapshot (their
   `replace` maintenance shifted or cleared it). This prevents a redo of an
   ordinary addition from resurrecting a stale marker after the wrap was
   undone and redone. Reproduced by `TEST-NEXT-UNDO-WRAP-009-REDO`,
   `010-UNDO-ONE`, `020-DELJOIN` (undo of Delete-join), and `021-DIVERGE`
   (divergent edit invalidates redo).
5. **R3 — trimblanks cursor hazard.** The trim loop removed all break blanks
   down to `lead`, then `replace` restored the old cursor unchanged, which
   could be past the shortened line. The trim now protects the typed blank when
   the cursor is before the wrap point (matching nano's `text.c:1331–1341`).
   Reproduced by `TEST-NEXT-UNDO-WRAP-019-TRIM`: the starting candidate crashed
   with code 6.

The independently supported `last_kind` reset (a hard wrap closes the addition
group, matching nano's `SPLIT_END`/`last_action` reset) is retained.

Regression checks (fresh runs, distinct from the historical qualification):
the wrap-undo suite (23/23), the baseline undo/edit/move+bytes corpus (61/61),
follow-up edges/tools/supplement (13/13, 20/20, 3/3), CLI 38/38 and regex 81×2,
seven default / five tiny Rust unit tests, 14 comparator and five harness
regression tests, and `cargo fmt --check` plus strict Clippy (default and
`--all-targets --all-features`) all pass. No new platform, libc, locale or
terminal combination is certified by this phase.

Remaining limits: the **quoting-prefix branch** of the spillage join
(`ENABLE_JUSTIFY` with a non-empty `quotestr`) — the default reference enables
justification with a nonempty default `quotestr`, and `hard_wrap` uses only
`e.indent(&s)`, so quoted/comment text under the default configuration is an
unimplemented behavior, not just a custom `-Q` setting; the **tiny profile**
has no undo/redo or hard wrap by design (doc 22). Q-UNDO-002 remains partially
open until the quoting-prefix branch is addressed or explicitly scoped out;
see `06-undo-redo.md` §4 and `../validation/wrap-undo/README.md`.

## Latest tiny completion checkpoint (2026-10-25)

The user requested continued implementation of unfinished work. Optional tiny
(doc 22) is now implemented and verified; `../validation/tiny/gate.json` passes
31/31 linked checks. Code commit `0a7cd514506ac59badd5f11219bfb0a108b66472` and
GitHub CI run 40173120098 are green. A following evidence/documentation commit
records completion. Current production input fingerprint:
`2c81a3fc062fbc6d35bb2c55f1bd1cdb903833029f53361611b1a7db7bc5a03f`.

Tiny: 59/59 terminal/editing, 125/125 CLI and 8/8 modeled VT comparisons match
fresh pinned tiny nano exactly. The 194 pinned CI/assertion scenarios pass,
including NUL rejection and invalid-regex recovery. Normal exit/HUP/TERM restore
terminal attributes. No bracketed-paste mode is requested. Full regression is
unchanged: 301/303 exact, 302/303 file-exit, CLI 38/38, regex 162/162 and both
safety cases pass. Both package profiles pass 15 installation/source-build checks
and 44 installed-asset checks. Rust full 6/tiny 5/all-features 5, comparator 14,
harness 5, namespace 7, console 9, formatting and strict Clippy pass.

Tiny stripped size is 856,296 bytes versus full 2,042,368 (58.07% smaller);
it needs no libmagic library/header. Build with `cargo build --release --features
tiny --target-dir target/tiny`. The full counterpart is `target/full/release/naro`.
Tiny binary SHA: `edb1691e800eea1392ac157945da097651859ee8834c0525a35ae3f260dab9ad`.
Full binary SHA: `c99f77769baf1462eecc630183b3d3e7b51da3729ea20fcc6bdc54925fe32c15`.
Local checked archives: `target/tiny-package-v1` and `target/tiny-full-package-v1`.
See the delivery receipt and reproduction commands in `../validation/tiny/README.md`.
The earlier portable Ubuntu archive remains a separate historical artifact.

Next: physical keyboard/operator certification still needs a human-operated
hardware session. Broader platforms/configure combinations and source-only gaps
in docs 97/99 are not covered by tiny qualification. Publishing a release/tag
is separate. No automatic model restart is installed; never retry around a
safety block. Do not rerun completed suites merely because a chat restarted.
Inspect current git status/remote HEAD before further changes. The default
closure below is historical; its earlier tiny deferral has now been resolved.

## Latest closure checkpoint (2026-10-24)

The implementation, full host/Ubuntu regression and portable package qualification
are complete. The combined gate in `../validation/closure/gate.json` passes all
85 checks. Production code/tools were frozen at
`390a72dc63da0f0f5b6d516282033fb1c4d6adad`; subsequent commits contain documentation,
reproduction tools and evidence. The packaging checkout was clean at
`3e3c221750076a6063852afe28643a8e172c41b1` (its GitHub CI passed).

Host executable SHA-256:
`283abffeda8ab42a6fe982ba54c355c459c7378632d50f8f132201fd76a2059d`.
Ubuntu executable SHA-256:
`eeb8ebb50fd3709aaa004897df3e589364e536a6a1eaf006ae3b8be5f6031541`.
Shared production source fingerprint:
`1c4f398661b107b55699daa63f1fcf35c22971417d67cb1a944a54718c2f7a13`.

Both builds retain 301/303 full and 302/303 file-exit matches, CLI 38/38,
regex 162/162, 51/53 exact follow-up matches plus two declared cleanup differences,
and eight exact ioctl models. Both pass all 19 genuine guest-VT cases. Host
root/home passes 27 exact cases plus the asserted no-home recovery deviation.
Rust six, comparator 14, harness five, namespace seven and console/upload nine
tests pass; formatting, Clippy, recovery, optional credits, large files and
installed assets pass. The portable package passes all 15 installation/source/
clean-container/ownership checks. No new production discrepancy remains.

Raw host checkpoint: `target/host-closure-v1/checkpoint.json` (state complete).
Ubuntu run: `target/ubuntu-closure-v1/complete`. Final portable binary and source
archives: `target/closure-artifacts-v1/package/`, with `SHA256SUMS` and `build.json`.
These paths are relative to `~/Code/naro`; large artifacts stay local.
Console evidence: `spec/evidence/follow-up-runs/vt-closure-{host,ubuntu}-v1`.
The disposable VM was shut down; the Ubuntu run exited and removed its container.
No local validation job or automatic model restart remains active.

Delivery completed: source and consolidated evidence were pushed in
`b67b1b9ce9a6b9f953fa395d90750097dc689c8f`; GitHub CI run 40170119664 passed.
`../validation/closure/delivery.json` records remote equality, the clean
qualification worktree, mirror verification and CI. All seven closure matrix
rows are verified. A final documentation-only receipt commit follows that
qualification commit, with its CI checked at delivery.

Next action: none for this scoped closure. A later session should read this
checkpoint and the delivery receipt, inspect `git status` and remote HEAD, and
start only newly requested work. Do not rerun completed suites merely because
chat restarted. Production changes require affected revalidation.
Tiny and physical keyboard/operator certification remain deferred. Publishing a
GitHub Release/tag is a separate action. A safety block must not trigger an
automatic retry around it. See spec 21 and `../validation/closure/README.md`.

Earlier checkpoints below describe historical binaries and scopes. Read
`00-overview.md`, `00-reference-environment.md`, this checkpoint, `97-coverage.md`
and relevant decisions in `99-open-questions.md` before new implementation work.

## Resume commands

```sh
# reference tree (clean, detached at the pinned commit)
cd ~/src/nano-ref && git status --porcelain && git rev-parse HEAD
# reference executables
~/src/nano-install/default/bin/nano --version
~/src/nano-install/tiny/bin/nano --version
# re-dump key/function tables (13 profiles) into spec/evidence/tables/
~/src/nano-rs/spec/tools/dump_all_tables.sh
# run scenarios
cd ~/src/nano-rs/spec && python3 tools/nanoharness.py evidence/scenarios/*.json
# regenerate inventories derived from source + dumps
python3 tools/build_inventories.py
```

Private locales for translation and non-UTF-8 probes: `LOCPATH=~/src/nano-locales`
with `de_DE.UTF-8`, `de_DE.ISO-8859-1`, `en_US.ISO-8859-1`, `ja_JP.UTF-8`.

## Session 1 (2026-10-23)

### Done
* Cloned upstream; resolved `6ed285c` → `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`;
  created a clean detached worktree at `~/src/nano-ref`.
* Built and installed the `default` and `tiny` profiles from a pristine export
  (gnulib at its pinned hash, from the GitHub mirror because Savannah returned HTTP 500).
* Wrote `00-reference-environment.md`.
* Wrote the gdb table dumper; dumped 13 profiles into `evidence/tables/`.
* Wrote `tools/nanoharness.py` and verified it with `TEST-SMOKE-001` (PASS).
* Built test locales in `~/src/nano-locales`.

### Source read so far (complete reads unless noted)
* `src/definitions.h` 1–664
* `src/global.c` 1–1666 (globals, `add_to_funcs`, `keycode_from_string`, `add_to_sclist`,
  `get_shortcut`, `interpret`, `shortcut_init`, `epithet_of_flag`)
* `src/rcfile.c` 1–1751 (whole file)
* `src/nano.c` 1–2755 (whole file)
* `src/winio.c` 1–3726 (whole file)
* `configure.ac` (feature dependencies)

### Next actions
See the bottom of this file. It is kept up to date as areas complete.

## Checkpoint A (2026-10-23, after 04)

### Additional source read (complete)
`src/prompt.c`, `src/move.c`, `src/cut.c`, `src/chars.c`, `src/utils.c`,
`src/text.c`, `src/search.c`, `src/files.c`, `src/history.c`, `src/color.c`,
`src/help.c`, `src/browser.c`. **All 18 C files of `src/` are now read in full.**
Docs read: `doc/nano.1`, `doc/rnano.1`, `doc/nanorc.5` (complete, rendered).
`doc/nano.texi` not yet read (it largely mirrors the man pages; to cross-check later).

### Documents written
- `00-reference-environment.md` (complete)
- `01-cli.md` (complete; 65 terminal scenarios + 46 non-tty probes)
- `02-keybindings.md` + generated `02-keybindings-tables.md` (complete)
- `03-terminal-input.md` (complete)
- `04-rendering.md` (complete)

### Inventories (tools/build_inventories.py regenerates all)
`keybindings.csv` (922 rows), `functions.csv`, `bindable-functions.csv`,
`helplines-80cols.csv`, `cli-options.csv`, `nanorc-options.csv`,
`nanorc-commands.csv`, `color-names.csv`, `messages.csv` (682),
`translation-catalogs.csv`, `build-features.csv`, `menus.csv`,
`escape-sequences.csv`, `toggles.csv`, `syntaxes.csv`, `undo-types.csv`.

### Harness changes
- `nanoharness.py` captures rows one by one (a whole-screen `capture-pane -e`
  carries SGR state between rows, which corrupted attributes). All earlier
  scenarios were re-run after this fix.
- Key names: `M-a`/`M-A` send ESC + lower-case letter; `Sh-M-A` sends ESC + `A`;
  modified special keys (`^Left`, `M-Up`, `Sh-^Del`, …) come from extended
  terminfo capabilities.
- Text steps: use `\r` for Enter (`\n` is ^J = Justify).

### Findings worth remembering
- `nano +r/( file` crashes (SIGSEGV) → Q-DEF-001.
- `-z` exits during option parsing (rc errors dropped; later `-f` ignored).
- Command-line `-p` removes ^S/^Q bindings; `set preserve` does not.
- tiny: optstring unchanged; unknown handlers → "Type 'nano -h'…" exit 1.

### Next
05 buffer/editing → 06 undo → 07 search → 08 files → 09 browser →
10 nanorc → 11 syntax → 12 features → 13 signals → 14 messages →
17 prompts → 18 bytes → 16 test plan → 15 architecture → 97/99/00-overview → audit.

## Final spec checkpoint (Codex, 2026-10-23/24)

The behavioral documentation phase is complete. Docs 05–14, 17 and 18 were
present after the inherited checkpoint; reviewed against their evidence and
used for the final contracts. Added 00-overview, 15 architecture, 16 test plan,
97 coverage, 99 decisions, data README, requirement inventory and audit tooling.
Full commit hash is at the top of every Markdown spec file.

Final decisions: libc POSIX regex and ncursesw FFI, byte-vector buffer with
explicit coordinates, native locale/gettext semantics; reject NUL as Yes and
fix invalid startup regex crashes; reproduce byte-mode Latin-1 word behavior.
See 99 for the full decision register, including remaining verification gaps.

Completed comparator: live/final screens, attributes indexed by cells, cursor,
modes, stdout/stderr, exit/signal, input bytes, fixture manifests and captured
locks; narrow normalization documented in 16. Twelve regression tests pass;
309/309 reference self-comparisons match. Harness now reports failed wait/settle
steps and returns nonzero for FAIL/ERROR instead of silently recording success.
No reference sources were changed.

Audit found and archived three obsolete duplicate definitions in files.json;
corrected definitions in files2.json match existing evidence. There remain 309
unique recorded scenarios, four explicit assertions and ten intentional SIGKILL
runs. Keybinding inventory actually has 921 rows (the earlier 922 included the
header). Planned probes remain source-only and are enumerated in 97/16.

Rust installed at user level through official rustup, minimal profile, no shell
startup modifications: `~/.cargo/bin/rustc` 1.99.1 and Cargo 1.99.1. Repository
`~/Code/naro` started as LICENSE/README only, origin JLuethe/naro. The spec will
be copied there before implementation, so one checkout contains the handoff.
No system packages installed. User authorized committing/pushing and continuing
through implementation/build/tests while unattended.

Resume implementation from the repository README/status report. Preserve
`spec/evidence/runs`; send candidate harness output to another directory.
`~/src/nano-rs/spec` is the original working spec; the checked-in copy travels
with Naro. Record later implementation work in the repository copy.


## Implementation validation follow-up (2026-10-24)

The repository copy at `~/Code/naro/spec` is authoritative for subsequent
corrections. The original `~/src/nano-rs/spec` remains the inherited checkpoint.
Rust was installed at user level without changing shell profiles or system
packages. A working Rust/C-native implementation and the complete spec were
committed and pushed to `JLuethe/naro`; GitHub CI builds and checks it.
See `../IMPLEMENTATION.md` for current candidate validation, distinct from
spec completion.

Harness refinements: private per-scenario TMPDIR; exact argv0 and explicit
execve environment (Python's implicit C-locale coercion must not leak into the
editor); optional hold_tty for redirected probes. Corrected ten intentional
kill recordings' terminal wait steps to sleeps, preserving their original
steps in `evidence/recording-timeout-corrections.json` and raw reference output.
Comparator now narrowly normalizes tool temp-path logs and truncated tmux dead
banner dates. Twelve comparator regression tests cover the contract.


Final harness checks also batch independent row captures into one tmux client,
preventing the 400 ms spelling message from expiring during 24 client launches.
Row SGR reset semantics remain unchanged. Exit waits require reaped status,
fixing a PTY-close/waitpid race exposed on GitHub's tmux; named signals are
converted to numeric values. Three harness regression tests cover these cases.
New results record the executable SHA-256 in addition to the frozen-run report.

GitHub's older tmux also exposed consecutive-server teardown races; each
scenario now has a unique server socket. Failure output includes final pane
state and screen. The regex safety probe waits for the save confirmation before
sending Exit. These are fixture isolation/observation fixes, not editor changes.

The faster captures exposed a real cancellation bug that slower captures masked:
a cancelled search must clear the spotlight immediately. The Rust state machine
now does so. Final replay uses `tools/validate_parallel.py` with four disjoint ID
partitions, a frozen executable and a combined completeness/hash check. The
original serial `tools/validate.py` remains available for focused diagnosis.

CI's tmux 3.4 intermittently reported a dead pane with neither exit status nor
signal even after the editor restored its terminal. Signal-mask experiments
did not resolve it. CI now builds checksum-pinned tmux 3.8 in its private runner
directory, matching the reference emulator in ENV-BASE; no status normalization
or weakened exit assertions are used.


## Final build/test checkpoint (2026-10-24)

The spec is complete and the editor builds in debug and optimized release modes.
The final frozen candidate in `~/Code/naro/spec/evidence/naro-v7` has 303 fixture-
safe recordings: 301 full matches and 302 file/exit matches. The only full
comparison differences are TEST-CLI-057 and TEST-PROMPT-NUL-001, the declared
safety improvements. Their six separate assertions pass. All 38 safe default
CLI probes and 162 regex cases match. Six Rust unit tests, twelve comparator
regressions, three harness regressions, formatting, strict Clippy and structural
audit pass. All four disjoint replay workers exit zero.

Compact results with the binary SHA-256 and source revision are checked in under
`~/Code/naro/validation/`; raw candidate evidence remains on disk (gitignored).
`~/Code/naro/IMPLEMENTATION.md` records known implementation limits, including
whole-buffer external tools and optional tiny/credits. No blanket claim of
complete source-branch or platform parity is made. The reference checkout
remains clean at the exact pinned commit. Final Markdown/tools/data/scenario
corrections are also synchronized back to `~/src/nano-rs/spec`; use the Git
repository copy as the canonical location for future edits.


## Follow-up specification (2026-10-24)

Added `19-completion-and-release.md` for selected-region spelling, formatter
selection state, editing/configuration/failure verification, environment coverage,
and installation/release. Corrected the earlier broad formatter description:
formatting remains whole-buffer; it must clear the mark at the source-defined
point. The selection-only gap is spelling.

There are 22 planned requirement headings and 41 proposed cases in
`data/follow-up-tests.csv`, all marked planned with no invented observations.
The structural audit now separates baseline/planned requirements and checks the
matrix's IDs, coverage, gates, statuses and evidence-path presence. The original
248 requirements, 309 recordings and frozen release validation remain unchanged.

Tiny is explicitly an optional compile-time reduced profile. Added a static
`CREDITS.md` with factual attribution and proposed a default-off plain-text
runtime credits extension; no editor behavior or CLI output changed in this task.
The next implementation milestone is doc 19 M1, not a new full-parity claim.

## Follow-up implementation (2026-10-24)

Implementation commit: `4952ca020e72425d04acf12639d222b7a33a9245`.
Release runner/CI commit: `eef679131cf1c16decd62dae2cd61ade497226bd`.

Implemented region-aware alternate/internal spelling, SPECIAL selection bytes,
orientation/cursor/mark restoration, whole-buffer formatter mark clearing, RAII
tool files, handled child termination and panic cleanup. Fresh differential
cases found and fixed disk-full warning phases, EINTR/short writes, backup
fallback, lazy syntax diagnostics and distinct undo/redo labels for wrapped
paste. Test fault injection is fixture-inode/path scoped ptrace on Linux x86_64.
Reference source stayed clean and original observations were preserved.

Added installed-relative catalogs/syntax, standalone ownership-aware installer,
source/binary archive/checksum/provenance tooling, default-off credits, and
separate recovery test hooks rejected by the packager. Static credits are
installed. No real user prefix/config was changed. Testing, including interactive
operator trials and install/uninstall, stayed in harness fixtures.

The current [matrix](data/follow-up-tests.csv) and
[follow-up reports](../validation/follow-up/README.md) are authoritative for
completion and deferred scope. Parent validation reports remain historical.
The new default host binary SHA-256 is
`524c97345cfca85458fa9c94ea297b0432b6f4c645f70f8a767b161b2f59f5ac`,
source-input SHA-256
`742ca8b1a18bec48989e1fcabe46a71bf847fc1d7d6582b9be9c65cfd6a73aac`.

Reproduce the host follow-up differential gate with a **new** output directory
per suite (do not run the same IDs concurrently):

```sh
cargo build --release
for suite in tools edges environments supplement backup fifo-eof signal-SIGTERM signal-SIGHUP; do
  python3 tools/check_follow_up.py --suite "$suite" --binary target/release/naro --out "target/new-$suite"
done
python3 tools/validate_parallel.py --binary target/release/naro --out target/new-baseline --jobs 4
python3 tools/check_cli.py --binary target/release/naro
python3 tools/check_regex.py --binary target/release/naro
python3 tools/check_release_gate.py --out target/new-gate.json
```

Second-environment runner uses a rootless Ubuntu 24.04 container, private build
HOME, and ordinary uid. uid 0 is unsuitable for HOME-isolated GNU nano tests:
it deliberately consults passwd for root's home. Early failed setup attempts
are preserved under `target/follow-up-env-*`; see `limits.json`. Reference
auxiliary symlinks are replaced only in the copied bootstrap tree. The reference
library/editor/catalogs are built without requiring Texinfo documentation tools.

```sh
podman build -f tests/follow-up/Containerfile -t localhost/naro-followup:ubuntu24 .
mkdir -p target/new-linux-env
podman run --rm --network none --userns=keep-id --user 0:0 \
  -v "$PWD:/project:ro" \
  -v "$HOME/src/nano-bootstrap:/reference-source:ro" \
  -v "$HOME/src/nano-ref:/reference-pinned:ro" \
  -v "$HOME/.rustup/toolchains/stable-x86_64-unknown-linux-gnu:/opt/rust:ro" \
  -v "$PWD/target/new-linux-env:/out" \
  localhost/naro-followup:ubuntu24 bash -c \
  'mkdir -p /work /opt/nano-locales; chown 1000:1000 /work /opt/nano-locales; exec setpriv --reuid=1000 --regid=1000 --clear-groups bash /project/tests/follow-up/environment.sh'
```

Use the actual local uid/gid in place of 1000 when necessary. The completed run
used `target/follow-up-env-user2` and reused its Ubuntu-built pinned reference
from `target/follow-up-env-v3/reference-install-tree`, mounted `/reference-built`.
The source C-file hash check is still performed. Fresh ordinary-user reference
recordings are separate from all failed root runs and original host goldens.
No Linux VT or isolated fixture-root device/browser certification was performed;
tiny remains optional and unimplemented. Tagging/publishing remains a separate
explicit action. Token usage cannot be inferred from these filesystem artifacts.

Final follow-up outcome: 48/48 gate checks, 37 verified matrix rows and four
explicit deferred rows. Ubuntu binary SHA-256:
`8f29d96f25206738212f18837e526595969c9724b7d2346b54e37bb121746f01`.
Both environments: 301/303 original terminal full matches, 51/53 new paired full
matches (all remaining differences declared), CLI 38/38 and regex 162/162.
The GitHub run for `eef679131cf1c16decd62dae2cd61ade497226bd` passed expanded CI.
Root HOME precedence remains a named out-of-scope issue, Q-ENV-ROOT-001.


## Root/home and conditional checks (2026-10-24)

Spec commit: `582cb8f`. Application implementation:
`4292ead60f1b93bc811b651a97bbfe8f46e455fd`.
Doc 20 and `data/root-console-tests.csv` track this phase. Effective-home lookup
now follows uid 0/passwd and non-root HOME rules, caches only successful results,
and is shared by config, tilde, histories and backup fallback. No-home resolution
skips cwd config/state. Tilde opening now retains the expanded filename and
preserves a double-slash suffix. All 27 new ordinary/root namespace comparisons
match. A separate source no-home tilde crash is safely handled (Q-ROOT-NOHOME-001).

Root evidence: `../validation/root-console/`. The frozen optimized binary source
fingerprint is `e3de64cd7995eccc549214783b542f5afa5e86e262b9026efb78fca5aa281ca8`.
The ordinary regression remains 301/303 full matches, CLI 38/38, regex 162/162
and passing existing safety assertions. New gates pass 16 checks. The previous
Ubuntu archives remain historical artifacts and do not include this phase's fix.

The root oracle is rebuilt from a private bootstrap copy, unchanged pinned C
sources, with `--sysconfdir=/etc`. This makes the no-home configuration-origin
label match the target instead of the old oracle's development installation
prefix. It never reads host /etc during root tests: each editor has a private
mount root. Its configure flags/source hashes are retained in the root report.

Bubblewrap is available on this machine and provides genuine namespace uids 0
and 1000, private passwd/group/NSS and null device. Backend safety guards and
readiness checks are implemented. JSON serialization now preserves invalid-UTF-8
path bytes and publishes only complete documents. Source and candidate backend
hashes are checked; editing the backend during a run fails closed.

The physical-console probe correctly records this tool's PTY as unavailable,
without touching the active Linux VT. Run `tools/console_check.py` explicitly
from an operator-owned real VT for the recorded trial; see the root validation
README. Two physical-console rows remain deferred. Native modifier/rendering
behavior is not certified until that trial and any resulting fixes. Optional
tiny remains outside this task. Host-root privilege semantics beyond the listed
namespace cases also remain untested.
