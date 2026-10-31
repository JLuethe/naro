# NARO 0.1.1 environment repair handoff — 2026-10-31

## Decision and scope

The six environment failures are explained by gaps in the independent identity
oracle. No editor rendering defect was found. Production source is unchanged.
The reviewed oracle repair is committed and pushed as `498fb892d52d95b82b6eadea6f6250ebc5be7ef5`.
The raw comparator and recorded GNU observations remain unchanged.

At 30 columns GNU's brand fit sum is 31 and NARO's is 29, so NARO retaining its
name follows the existing Q-IDENTITY-001 policy. German ISO and Japanese state
labels already occupy the same display cells as nano. The requested French case
actually falls back to C because its requested locale is unavailable under the
custom LOCPATH. Separate live checks confirm genuinely active French as well.

The repair measures display cells, recognizes only finite known state/locale
alternatives, roundtrips the complete original reference row, and requires one
unique candidate projection. Three exact scenario/snapshot bindings cover the
unbranded narrow reference title. Schema, physical geometry, filename, state,
attributes, cursor, body, modes, files and exits remain checked. A different
candidate screen cannot choose the expected projection. Independently discovered
branded-width and empty-record context bypasses were closed before freezing.

## Authoritative replacement freeze

`/home/john/Code/naro/target/phaseB-environments-repair-2026-10-31/freeze-attempt02`

| Identity | Commit / SHA-256 |
|---|---|
| Source commit | `498fb892d52d95b82b6eadea6f6250ebc5be7ef5` |
| Source tree | `854bd2acb1f5bb4aa6baf637d75e7e87783c5f49` |
| Production source | `63936243e73d0a3fb536d3c0a0fb0e6fe57be09da5f5bc0387ee10250b3d7093` |
| Verification tools | `68e03dbf57b6ac02aa06734c5e69aea6c36012ac59ec020a2eaea65d52fc8406` |
| Host NARO | `dcb8ae6d96a492a349e89a11f5706bbe4416d0c6d7288aec56e6db85d20a1ce1` |
| Ubuntu NARO | `ba4e046d174120733f33eb03fbcd205a34bd08a54a008b4fc3f38e740d8193df` |
| Host nano | `b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2` |
| Ubuntu nano | `6540492f810998a20a4dba4ac8048cd8b76d37a39e642f14f9f9c3d30c621ba7` |
| Freeze manifest | `596829be9e3848a4135ffeda1c3d3dba0c177679b5681209f65e87c3bf7cb61b` |

Both binaries are default-feature 0.1.1 builds with no test hooks. Their new hashes
include provenance for the complete frozen source/tool snapshot; production
behavior did not change. Old candidate reports cannot qualify these new hashes.
The Ubuntu build remains the intended portable download after full qualification.

All five build/finalization/verification commands passed in build-attempt02.
The initial default-sandbox Podman preflight failure remains in build-attempt01;
no build had begun there. Root independently reran freeze verification with exit
0. Guest fixtures for both candidates are prepared and preserved, but unbooted.
The first fixture setup failure (missing fx parent) is retained honestly.

## Evidence and validation

Work root: `target/phaseB-environments-repair-2026-10-31/`.

- Final tooling: 146 tests across 12 suites passed; verification fingerprint
  unchanged throughout (`unit-review03/SUMMARY.json`).
- Independent corruption review: all 80 prior adversarial controls reject, plus
  branded 32-column, empty-row and physical/application-width mismatch controls
  (`geometry-final-signoff/REPORT.md`).
- Retained raw reclassification: 665 pairs, zero unexpected; 2,665 input files
  unchanged (`geometry-reclassification/RECLASSIFICATION-SUMMARY.json`). These
  are diagnostic reopens, not fresh qualification or altered historical reports.
- Fresh final host readiness: all 11 commands exit 0, environments 13/13 accepted
  (3 raw, 10 identity), CLI branding 5, layout 21/105, original EOF blocker pair
  20 assertions each, Smoke/Edit reference+candidate proof, FEAT-015 actual cursor
  restoration and all corruption controls. Frozen inputs unchanged; owned tmux
  resources cleaned (`final-readiness-host/RESULTS.md`).
- Fresh final Ubuntu readiness: environments 13/13 accepted (3 raw, 10 identity),
  CLI branding 5, layout 21/105, EOF pair 20 assertions each, independent forgery
  rejection, fresh Smoke/Edit references, FEAT-015 and genuinely active French.
  All stages/cleanup exit 0; host-side frozen-tool raw reopening and all 226
  sealed evidence files verify (`final-readiness-ubuntu/REPORT.md`).
- Exact-source [CI run 41242837960](https://github.com/JLuethe/naro/actions/runs/41242837960)
  completed successfully for `498fb892d52d95b82b6eadea6f6250ebc5be7ef5`.
  CI is separate from the pending full nano-parity qualification.

Earlier live development proofs in pre-freeze-host/Ubuntu used the previous
candidate/tool epoch and are clearly retained as development evidence. They
include genuine French activation and the 28–31-column fit boundary. Ubuntu
setup failures and the later successful reruns are all preserved, with no false
claims that failed attempts passed.

## Preservation

Claude's stopped attempt remains untouched at
`target/naro-test-runs/claude-0.1.1-phaseB-2026-10-31-attempt01/`.
All 9,475 files and 1,812 directories were independently rechecked against the
original inventory and its backup (`ORIGINAL-ATTEMPT-RECHECK.json`).
Backup: `/home/john/Backups/naro/2026-10-31-phaseB-attempt01-blocked/`.
Actual host coverage was **21 stages passed, one failed, 24 not run**. Ubuntu,
guest VT, transport and closure were not run. The old reports remain unchanged.

The replacement freeze, both final readiness sets, development and failed-attempt
evidence, prepared VM fixtures and final handoff are preserved under
`/home/john/Backups/naro/2026-10-31-environment-oracle-0.1.1/`.
Its archive is `environment-oracle-freeze-and-evidence.tar.gz`; every member,
regular-file byte, permission mode and symlink target is stream-verified against
the source inventory. The exact archive hash and counts are in the external
`BACKUP.json` and the tracked receipt, avoiding a self-referential archive hash.

Backups are outside target on the same filesystem, not off-device.
The final archive receipt is kept under
`validation/environment-oracle-0.1.1-2026-10-31/`.

## Next work for Claude

Use [the new exact-hash Phase B prompt](CLAUDE_0.1.1_PHASE_B_RESUME_ENVIRONMENT_FIX_2026-10-31.md).
It supersedes the older resume instructions. Start a new attempt directory,
independently verify the freeze/readiness receipts, then run the complete host
and Ubuntu matrices using each environment's own nano. Both new binaries require
fresh qualification even though production code is unchanged.

Then run all 19 genuine guest-VT comparisons per candidate, the six transport
checks with installed/before hashes asserted, final packaging, the complete
closure collector and the release gate. Preserve actual command statuses and raw
traces; separately count raw, identity-reviewed, declared and unexpected results.
Any unexplained difference blocks qualification. Do not accept the obsolete
0.1.0 raw-match totals as the new identity-aware target.

Frozen inputs and acceptance policy are immutable for Claude. A new finding goes
to Codex with a minimal reproduction. Nothing here publishes 0.1.1, creates a
tag, uploads assets, or changes the existing 0.1.0 release. Publication still
requires a passing complete gate and John's approval.
