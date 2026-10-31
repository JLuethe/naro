# NARO 0.1.1 environment oracle repair — 2026-10-31

Claude correctly stopped at the host environments failure. Independent comparison
with pinned GNU `titlebar()` reproduces all 15 affected reference rows and their
NARO projections exactly. The six failures are identity-oracle coverage gaps;
no editor rendering defect is shown. Production source remains unchanged.

## Confirmed findings

| Cases | Actual result | Oracle correction |
|---|---|---|
| TERM-001-1/2/3 | At 30 columns GNU's fit sum is 31, NARO's is 29. NARO retaining its name is already approved by Q-IDENTITY-001. | Bound source-case/snapshot context and independent complete-row painting. |
| I18N-002-4 | German ISO `Ver�ndert` starts at cell 69 in both editors. | Recognize the known decoded state, preserve exact placement/attributes. |
| I18N-002-5 | Japanese `変更済み` is four codepoints/eight cells and starts at cell 70 in both editors. | Measure, paint, pad and slice by display cells. |
| I18N-002-6 | Requested en_US.UTF-8 fails under the custom LOCPATH; effective LC_MESSAGES is C, so English is correct. | Require complete reference-row roundtrips and one unique projection; do not infer activation from an installed catalog. |

Raw attributes, cursor, modes, body, inputs and files remain strictly checked.
Observations are not rewritten or counted as raw-exact when they differ.
Unknown, stale or ambiguous contexts still fail closed.

## Preserved attempt and actual coverage

Original: `target/naro-test-runs/claude-0.1.1-phaseB-2026-10-31-attempt01/`.
Verified backup: `/home/john/Backups/naro/2026-10-31-phaseB-attempt01-blocked/`.
All 9,475 original files are unchanged; the complete backup inventory verifies.
This backup is outside target on the same filesystem, not off-device.

Host execution: **21 stages passed, 1 failed, 24 not run**. The 303-case corpus
passed (26 raw, 275 identity reviews, 2 known deviations, 302 file/exit matches,
six exclusions). Tools 20 and edges 13 passed. Environments had 3 raw, 4 identity
reviews and 6 unexpected. Ubuntu, guest VT, transport and closure were not run.

Read-only diagnosis/inventory and separate reclassifications are under
`target/phaseB-environments-repair-2026-10-31/`. Retained captures are diagnostic
inputs, not replacement qualification of newly frozen candidates.

## Completion work

1. Extend only the reviewed oracle and source-bound context fixture. Test
   28–31-column boundaries, German ISO/Japanese states, real French translation
   and requested-French/C fallback, plus corruption/stale-context negatives.
2. Reopen retained raw pairs without modifying them. Audit full historical
   reference title shapes before freezing; keep honest raw/identity counts.
3. Freshly exercise the complete environment suite in host and Ubuntu against
   each environment's own pinned nano. Prove real locale activation explicitly.
4. Commit/freeze reviewed tooling, verify production fingerprint is unchanged,
   rebuild provenance-bound candidates and fresh guest fixtures, run focused
   readiness, and preserve the new freeze/evidence outside target.
5. Give Claude an exact-hash resume handoff for a new full qualification attempt.
   No tag, upload or release publication is part of this work.

Final identities/results are recorded in the completion receipt after validation.
