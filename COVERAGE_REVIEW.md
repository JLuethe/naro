# Coverage review for the 0.1.0 candidate and issue #14

## Historical 0.1.0 review

Reviewed October 31, 2026. Production source: `b934b1f`. The complete
technical gate passed 101/101 checks for that named candidate. The separate
specification audit found nine unresolved test-ID citations. They were not nine
observed editor failures. The original audit, counts, and requirement inventory
remain available in `spec/evidence/final-audit.txt`, the committed history of
`spec/evidence/audit.json`, and `spec/97-coverage.md`. The 303 recorded corpus
cases had six additional exclusions; two deliberate non-full matches were not
exclusions. The 151 newer exact regressions were distinct from 53 historical
follow-up cases. Guest-VT observations were distinct from eight ioctl-model
tests and deferred physical-keyboard trials.

## Issue #14 disposition, November 5, 2026

The nine names were removed from *test citations* in the affected normative
requirement blocks. None was relabeled as an executed scenario. The underlying
reference probes, table dumps, and source observations remain identified by
their own evidence type. The resulting structural audit has no unresolved
test-ID warning for these nine because there is no longer a false test claim;
that result does **not** qualify the listed candidate behaviors.

| Requirement / former test citation | Correct evidence and remaining qualification |
| --- | --- |
| CLI-001 / `TEST-CLI-P003` | `CLI-P-003` in `spec/evidence/cli/cli-probes.json` records reference `rnano --help`; it is not a candidate scenario. First-byte invocation behavior remains unqualified. |
| CLI-001 / `TEST-CLI-P042` | `CLI-P-042` records reference `xnano --help`; it is not a candidate scenario. Case-sensitive negative variants remain unqualified. |
| CLI-001 / `TEST-KEY-RESTR-001` | Historical `default-rnano.json` and `default-restricted.json` reference dumps agree. There is no candidate re-dump/assertion under this name. |
| CLI-004 / `TEST-CLI-P009` | `CLI-P-009` and related `CLI-P-*` records are non-tty reference probes, not mapped candidate assertions for each diagnostic variant. |
| CLI-014 / `TEST-RC-PREC-001` | The precedence series was proposed only. Source analysis supports the documented rule; a full candidate runtime matrix remains unqualified. |
| CLI-020 / `TEST-KEY-MODPRES-001` | Source and separate reference table dumps describe the combined `-p -/` behavior. No mapped candidate test asserts its key table and terminal-flow outcomes together. |
| CLI-050 / `TEST-FILE-EXIT-002` | Reference statuses 0 and 1 were observed. Status 2 was source/man-page derived; the discard-to-exit runtime path remains unqualified. |
| INPUT-014 audit association / `TEST-INPUT-020` | This planned name was in a later evidence table for INPUT-012/013 cancellation and timing. The block-based audit associated it with nearby INPUT-014 prose; neither requirement gains runtime coverage from the planned name. |
| KEY-003 / `TEST-KEY-TABLE-001` | `spec/data/keybindings.csv` and 13 historical reference dumps are inventories, not an executed candidate comparison of the complete table and its order. |

The spec now states these limits at the requirement sites. The remaining
candidate work is a distinct qualification task: construct scenarios with
the exact trigger, observable assertion, reference/candidate identity, and
runner result for each behavior that release scope requires.

## Evidence and failure accounting

The documented runner is `spec/tools/nanoharness.py` (see
`spec/16-test-plan.md`). A scenario with no `expect` checks is reported
`RECORDED`, not `PASS`. Failed expectations or failed steps produce
`FAIL`; execution exceptions produce `ERROR`; either gives a nonzero
runner exit. `compare_runs.py` rejects missing evidence as a difference,
including when given an explicit test ID. No issue #14 citation is retained
on the basis of a skipped, missing, or infrastructure-failed run. The check
commands and their outcomes are recorded in
`validation/issue-14-citations/README.md`.

This review does not alter any historical reference result, exclusion, or
normalization rule. Current qualification and exact artifacts remain indexed
in `validation/README.md`.
