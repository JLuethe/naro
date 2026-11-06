# Issue #14: specification citation correction

Date: November 5, 2026. Scope: the nine unresolved citations named in
`COVERAGE_REVIEW.md`. This change corrects evidence classification; it adds no
candidate runtime qualification and changes no editor source, reference
recording, comparison normalization, or exclusion.

The review table in `COVERAGE_REVIEW.md` records each former test ID and the
actual source, reference probe, or table evidence. The affected normative
blocks in `spec/01-cli.md`, `spec/02-keybindings.md`, and
`spec/03-terminal-input.md` now say where candidate behavior is unqualified.
The original historical account in `spec/97-coverage.md` and
`spec/evidence/final-audit.txt` remains intact.

## Reproduction

Run from the repository root:

```sh
python3 spec/tools/audit_spec.py
python3 spec/tools/test_audit_spec.py
python3 spec/tools/test_compare_runs.py
python3 spec/tools/test_nanoharness.py
python3 validation/issue-14-citations/check.py
```

Observed on November 5, 2026:

| Command | Outcome |
| --- | --- |
| `audit_spec.py` | exit 0; 291 requirements, 309 recorded reference scenarios, 4 explicit reference assertions, 0 problems, 0 warnings. Regenerated `spec/evidence/audit.json`; `spec/data/requirements.csv` was unchanged. |
| `test_audit_spec.py` | 9 tests, OK. |
| `test_compare_runs.py` | 15 tests, OK. |
| `test_nanoharness.py` | 6 tests, OK. |
| `check.py` | exit 0; verified nine former IDs absent from the affected normative blocks and exercised the failure cases below in disposable fixtures. |

The disposable checks call the documented runner and comparator directly.
An explicit comparison ID with no result file produced `DIFF` and exit 1.
A missing binary produced `ERROR` and exit 1. A scenario with no assertions
was `RECORDED` (0/0 checks), not `PASS`. An incorrect expected exit status
produced `FAIL` and exit 1. A timed-out step produced `FAIL` and exit 1
despite a passing exit-status assertion (1/1 checks). Thus a nonzero check
count alone cannot hide an unfinished scenario.

The audit is structural: zero missing citation warnings is not a statement
that all 291 requirements are runtime-qualified. The nine corrected behaviors
retain the explicit limits in the review table. Historical candidate
qualification remains tied to its recorded binary and environment; this
documentation-only disposition does not requalify a current build.
