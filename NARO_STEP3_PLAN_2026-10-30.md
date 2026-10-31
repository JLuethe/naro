# Step 3: targeted behavioral qualification

Date: October 30, 2026, America/Los_Angeles.
Starting commit: `fc30606138d393a720bcb888ad3aecedd83ed112`.
Evidence: `target/naro-test-runs/codex-step3-2026-10-30/`.

## Objective and acceptance

Close the six bounded gaps in step 3 of the release-readiness plan using identical
inputs against pinned GNU nano and a freshly frozen default NARO build. This is
host behavioral qualification, not portable Linux, console, or package approval.
Record all attempts; no changes to normalization or declared differences.

## Execution plan

1. Freeze the starting source identity, build, binary hashes, reference identity,
   and original working state. Keep builds, scratch scenarios, logs, raw traces,
   and incremental progress in a new durable ignored directory.
2. Generate an exploratory matrix for the following families. Use the corrected
   Claude structural scenarios as reviewed inputs, never execute old transcript
   commands. Keep existing permanent scenarios unchanged during exploration.
3. Run nano first, inspect operation and branch witnesses, then run NARO on the
   same inputs. Compare complete screens/attributes/cursor/modes, saved bytes,
   history messages, and exits. A matching no-op does not count as coverage.
4. Freeze explicit expectations from the reference recordings, including saved
   bytes and intermediate cursor/buffer rows. Replay the asserted scenarios on
   both editors. Keep the exploratory evidence separate.
5. If a mismatch reproduces, minimize it without losing its trigger, add its
   permanent regression before repairing production code, then rebuild and rerun
   affected probes plus required controls. Never call a harness failure parity.
6. Retain the useful bounded suite permanently, include it in routine validation
   and the release gate, record results/limits, and update the readiness plan.

## Targeted matrix

| Family | Inputs and operations | Required witness |
| --- | --- | --- |
| View mode | Single/multiline bracketed paste with hard/soft wrapping; attempted ordinary edit, cut, undo/redo | Original bytes unchanged, no modified-save prompt, exact reference messages and cursor |
| EOF and history | Default final empty line and `-L`; a real hard wrap, Home/Backspace, undo/redo, then short overflow on the actual predecessor | Final join has room under fill 12; distinguish accepted join from history-cleared identity |
| Structural callers | Read-file, real command insertion, replacement, justify, formatter/speller success and failure, marked filter, cut/paste, bracketed paste with overflow at EOF | Operation visible or fixture tool receipt; final remainder plus successor breadth fits 12, so join/no-join is meaningful |
| Soft wrapping | PageUp/PageDown at narrow geometries, tabs 3/4/8, line numbers, widening/narrowing, subsequent vertical movement | Exact cursor and viewport after every action; original file bytes unchanged |
| Selection reversal | Mark on either side of a split, cross the anchor, reverse again, cut and undo/redo | Highlight and cut identify logical bytes rather than only a successful exit |
| Unicode quote leads | Nonbreaking/EM/ideographic space quote prefixes, custom quote recognition, wrapping and history | Actual split with continuation prefix and exact UTF-8 bytes; visible selection/cursor checks where relevant |

The matrix is finite. If an intended branch is not reached, correct the probe and
retain the failed attempt rather than claiming coverage. Unsupported or newly
problematic combinations stay explicitly open until resolved.

## Verification and deliverables

- Replay unchanged wrap 58, filter 6, and release-fixes 15 controls; validate
  complete evidence using the existing strict checkers.
- Run relevant Rust/lint checks if production code changes, plus checker/harness
  tests for any test-tool changes. Broaden to the retained corpus when a fix
  affects general editing/navigation behavior.
- Deliver a permanent oracle-asserted targeted suite, compact verification
  receipt, readable findings/results, and exact continuation instructions.
- Preserve historical outputs and unrelated untracked reviews. No release,
  system-editor replacement, or GitHub publication occurs as part of this step.

## Status

Complete for the bounded 40-case matrix. One soft-wrap paging defect was found,
regressed before repair, and fixed. The final 40 cases and all 79 existing
controls match; complete artifacts validate and the retained baseline preserves
its historical results. See [the results](NARO_STEP3_RESULTS_2026-10-30.md) and
the evidence directory's `PROGRESS.md`. Steps 4 onward remain separate.
