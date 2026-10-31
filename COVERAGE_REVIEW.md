# Coverage review for the 0.1.0 candidate

Reviewed October 30, 2026. Production source: `16f6398`.

The complete technical gate passed 99/99 checks for the named candidate.
Separately, the specification audit reports nine unresolved test-ID citations.
These are not nine observed editor failures, and a clean structural audit does
not establish complete requirement coverage. This review does not remove
warnings, invent recorded scenarios, or treat reference-only observations as
candidate verification.

## Citation disposition

| Requirement / cited ID | Evidence found and disposition |
| --- | --- |
| CLI-001 / `TEST-CLI-P003` | Historical `CLI-P-003` exists in `spec/evidence/cli/cli-probes.json`. It is a differently named reference probe, not this recorded scenario. Retain the unresolved scenario mapping. |
| CLI-001 / `TEST-CLI-P042` | Historical `CLI-P-042` exists in the same probe file. Retain the distinction and unresolved scenario mapping. |
| CLI-001 / `TEST-KEY-RESTR-001` | Restricted/rnano table observations exist in `spec/evidence/tables/default-restricted.json` and `default-rnano.json`. No recorded scenario with the cited ID is established. Retain the gap. |
| CLI-004 / `TEST-CLI-P009` | Historical `CLI-P-009` exists; prose cites a larger range of reference CLI probes. Do not turn the range into claimed scenario execution. Retain unresolved mapping. |
| CLI-014 / `TEST-RC-PREC-001` | The CLI/nanorc merge requirement labels the proposed precedence series as planned. No exact scenario mapping is established here. Retain as unqualified for that cited series. |
| CLI-020 / `TEST-KEY-MODPRES-001` | The `-p` / modern-binding interaction is described in the specification. No exact recorded scenario under this ID is established. Retain the gap. |
| CLI-050 / `TEST-FILE-EXIT-002` | Exit statuses 0/1 have observations; the status-2 path is described as source-confirmed. The named runtime test is not established. Retain this specific runtime gap. |
| INPUT-014 audit association / `TEST-INPUT-020` | The citation occurs in a later evidence table describing planned INPUT-012/013 cancellation/timing tests. The audit associates nearby prose with INPUT-014. Record that association limit; the planned ID still lacks a recorded scenario. |
| KEY-003 / `TEST-KEY-TABLE-001` | `spec/data/keybindings.csv` and historical table dumps exist. They are not an executed candidate re-dump under this test ID. Retain the gap. |

All nine are explicitly retained. Related current tests may exercise part of
these behaviors, but this review does not assert equivalence without inspecting
and mapping the exact trigger, expected result and candidate observation.

## Current evidence versus historical inventory

[The validation index](validation/README.md) names current host/Ubuntu, console
and package reports. Baseline observations, noninteractive CLI probes, table
dumps, paired scenarios and explicit assertions are different evidence types.
Keep their inventories and provenance separate.

The 303 recorded corpus cases have six additional exclusions; the two deliberate
non-full matches are not exclusions. The 132 newer exact regressions are separate
from the historical 53 follow-up cases. Guest-VT observations are separate from
eight ioctl-model tests and from deferred physical keyboard trials.

The original baseline coverage table in [spec/97-coverage.md](spec/97-coverage.md)
is preserved as historical context; its older gaps/counts are not a description
of the current candidate. Newer checks cover additional wrapping, writes,
recovery, catalogs and guest-console behavior, without claiming exhaustive
coverage of those areas.

## Later closure work

For each retained citation, either add a meaningful reference/candidate test
with explicit assertions and provenance, or revise the specification's evidence
classification to link the actual probe/table artifact accurately. Do not merely
rename missing IDs to make the warning count zero. Such work is outside this
documentation draft and must not relabel the frozen candidate's evidence.
