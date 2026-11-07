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

## Issue #14 runtime follow-up, November 6, 2026

`tests/issue14/run.py` adds assertions against a named production candidate
and companion test-hook builds. Its `artifacts.json` records SHA-256 and build
identity and rejects a mismatched reference ELF, candidate revision, source
fingerprint, or feature set. The checks below apply to the binaries named in
that receipt only; an integrated build must rerun them.

| Former citation | New executed assertion and scope |
| --- | --- |
| `TEST-CLI-P003`, `TEST-CLI-P042` | Production `--help` for `nano`, `rnano`, `rvi`, `xnano`, and `Rnano`; exact GNU output with the reviewed NARO identity projection, plus restricted/full grouping. |
| `TEST-KEY-RESTR-001` | Test-hook snapshots compare all 190 ordered bindings for `rnano` and `-R` to the independent reference tables and to each other. Production invocation-name help is checked separately. |
| `TEST-CLI-P009` | Production candidate matches five pinned-reference error status/stdout/stderr tuples, including invalid short, unknown long, ambiguous prefix, missing argument, and forbidden long argument. |
| `TEST-RC-PREC-001` | Test-hook runtime checks rc-only values, CLI boolean/numeric/string precedence, and restricted cleanup. This is a representative merge matrix, not every rc option or lookup path. |
| `TEST-KEY-MODPRES-001` | Test-hook ordered table equals the reference modern table minus the two preserve-sensitive bindings; production terminal flow saves with ^S and exits with ^Q under `-p -/`. |
| `TEST-FILE-EXIT-002` | Production terminal test discards an edited existing buffer, exits 2, and preserves the file bytes. |
| `TEST-INPUT-020` | Production quickblank message clears after 1.2 seconds, and a bounded candidate long search responds to ^C while discarding a trailing same-burst `X`. The long-search reference could not be deterministically held open with the disposable fixture; this is a candidate assertion plus the documented source rule, not a reference timing comparison. INPUT-014 remains a separate requirement. |
| `TEST-KEY-TABLE-001` | Test-hook snapshots compare every row and order of all 13 recorded reference profiles (nine default and four tiny). The hooks verify startup table state; production terminal behavior is asserted only for selected key paths. |

The cancellation test initially failed: a trailing `X` became an edit after
`Cancelled`. `src/search.rs` now drains queued and ncurses pending input only
when search cancellation occurs. The
[negative-control receipt](validation/issue-14-runtime/negative-control.json)
records the failure; the raw result is retained in the isolated worktree's
ignored `target/issue14-cancel-prototype-run` directory;
the committed test reproduces its trigger and fails against the old binary.
The complete commands and limits are in `validation/issue-14-runtime/README.md`.
