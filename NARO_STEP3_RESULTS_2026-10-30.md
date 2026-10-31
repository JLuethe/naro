# Step 3 behavioral qualification results

Date: October 30, 2026, America/Los_Angeles.
Plan: [targeted behavioral qualification](NARO_STEP3_PLAN_2026-10-30.md).
Evidence: `target/naro-test-runs/codex-step3-2026-10-30/`.

Status: complete for the bounded step 3 matrix; final verification passed.

## Coverage

The permanent `tests/follow-up/scenarios/step3-gaps.json` has 40 cases. Each has
explicit expectations measured from the pinned GNU nano executable, including
saved bytes, intermediate cursor/buffer rows, and applicable selection
attributes. View-mode cases assert no Modified title; external formatter and
speller fixtures leave receipts proving execution. Paired comparisons also
check complete screens, messages, terminal modes, and exit state.

| Family | Cases | What the probes demonstrate |
| --- | ---: | --- |
| View-mode bracketed paste | 2 | Single/multiline paste and attempted edits/history leave original bytes unchanged. |
| EOF wrapping and history | 4 | Default final empty line and `-L`, with live-join controls and Backspace/history variants. |
| Structural operations at EOF | 21 | Thirteen corrected `-L` caller/control cases plus eight operations at the actual magic/final boundary. Read, command insert, replacement, actual justification, formatter/speller success/failure, marked filter, and cut/paste paths execute. |
| Soft-wrap paging | 8 | PageUp/PageDown, tabs 3/4/8, line numbers, narrow/wide resizing, later Up/Down, and minimal odd-page-height cases. |
| Selection reversal | 2 | Marks originating before/after a split, crossing the anchor, cut, undo, and redo identify the selected bytes. |
| Unicode quote prefixes | 3 | Explicitly recognized NBSP, EM-space, and ideographic-space quote leads are copied on actual wraps and survive undo/redo. |

The structural identity probes use a short `zz` remainder and `eee ddd`
successor: 2 remainder bytes plus 7 display columns fits fill 12. The observed
join/no-join therefore distinguishes live successor identity from fill rejection.
The original oracle witness rows and receipts are retained in
`oracle-witnesses.json`; reference outcomes remain authoritative.

## Defect found and repaired

Soft-wrap paging used the preferred column as an absolute column on the target
logical line. When the target was a continuation chunk, that could land on a
different visual row and shift the cursor or viewport incorrectly.

Minimal reproduction: six 30-column lines, soft wrap, a 20-column by 9-row
terminal, End followed by PageDown. Nano lands at column 10 on a continuation;
the pre-fix NARO lands at column 19 on the preceding chunk. The corresponding
PageUp probe puts the NARO cursor one screen row below nano.

Two permanent oracle-asserted regressions were added before the fix. Both fail
on the original binary; recordings and nonzero harness/comparison results are
in `page-before/`. Across the complete usable exploratory matrix, 33/40 matched
and seven paging cases differed, all explained by this cause.

`src/basic_features.rs::page` now uses the existing chunk-relative vertical
movement calculation, including tab-boundary handling, and recomputes the
viewport to preserve the cursor's screen row. Soft-wrap file-boundary jumps
also update the preferred column. Ordinary non-soft-wrap paging is unchanged.
The focused post-fix paging run passes 8/8 with both harnesses zero.

No comparison normalization, historical expectations, or accepted deviations
were weakened. CI and both closure runners now require the 40-case suite via
the common suite inventory. The final collector validates its full recordings
and assertions, bringing the newer exact suites to 119 cases per environment;
the historical 53-case gate remains separate.

## Probe corrections and limitations

The first exploratory batch had two invalid `BSpace` key names (the harness uses
`Bsp`) and a justification fixture whose short paragraph did not change. The
three corrected probes have separate IDs and recordings. The originals and
wrapper failure are retained and explained in `ATTEMPTS.md`. These were probe
errors, not editor defects, and do not count as passing coverage.

This is finite host coverage. It does not qualify Ubuntu artifacts, genuine VT
operation, physical keyboards, all quote regexes/locales, every scrolling mode,
or exhaustive nano parity. Those claims remain outside this step. The final
release still needs a committed freeze and its own host/Ubuntu, console, and
package qualification.

## Candidate identity

Both builds embed base revision `fc30606138d393a720bcb888ad3aecedd83ed112`.
The repaired build contains the explicitly recorded working-tree fix.

| Build | SHA-256 |
| --- | --- |
| Before | `157049e37ba34ca3400f873862523154b8ec55e8fb7b5b3a68422716286920c1` |
| After | `175dbaed9cba423558121506b7c36f58a48da1c9aad8503df009248eb41a1187` |

The repaired production fingerprint is
`4cabd71741ffc8ee0357d945c67904c8a2fd0089c12e9b32a1c5b3e35c394ae6`.
Build logs, metadata, original state, failures, and ongoing checkpoints remain
in the evidence directory. Do not relabel this binary as a later committed build.

## Verification checkpoint

- Focused fixed paging: 8/8 exact, both harnesses zero.
- Rust: default 9 and all-features 5 pass.
- Formatting and default/all-features Clippy with warnings denied pass.
- Closure gate tests 9, existing wrap checker tests 43, comparator tests 14,
  harness tests 6, and audit tests 9 pass.
- Specification audit passes with the same nine pre-existing unresolved citations.
- Final step3-gaps replay: 40/40 exact, both harnesses zero, all assertions pass.
- Final controls: wrap 58/58, filter 6/6, release-fixes 15/15 exact; both
  harnesses zero and all assertions pass for each suite.
- Complete evidence validation passes for all four suites (119 comparisons).
- Retained baseline: 303 recorded, 301 full / 302 file-exit matches, six
  exclusions, four workers zero, runner zero. Only TEST-CLI-057 and
  TEST-PROMPT-NUL-001 differ, as already declared.
- [Compact verification receipt](validation/step3-review.json) identifies
  report hashes, build/source identity, outcomes, and remaining release work.

The implementation, regressions, and evidence receipt are included in this
source delivery. Remote delivery and CI are verified separately during step 4.
No release or tag has been published.
