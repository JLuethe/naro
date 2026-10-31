# Validation evidence

Latest release preparation: [step 10 review](../NARO_STEP10_REVIEW_2026-10-30.md)
and [CI synchronization diagnosis](step10-ci-2026-10-30/README.md). New 40-case
host/Ubuntu evidence and the 97-check collector supplement the unchanged frozen
qualification. Independent Claude verification and publication remain separate.


## Current 0.1.0 candidate

The current qualified production commit is
`fd91763c4f14d9bed8187d64d44f2136440b7b3e`. The primary Ubuntu default binary is
`33a39eb339492720ec6166e84fea421749e0b2ec3bd612b276c2377f91b7c4a1`;
the host qualification binary is
`cae387c78619520aacbf61690e675496b82f8ccf04af2824beb9e864004f0a96`.
The reference source is GNU nano `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.
Documentation and evidence commits may be newer than these build identities.

| Record | What it establishes |
| --- | --- |
| [Source/build freeze](../NARO_STEP4_FREEZE_2026-10-30.md) | Clean committed source, separate binaries, references and build provenance |
| [Step 5 qualification](step5-qualification-2026-10-30/README.md) | Host and independent Ubuntu matrices, accepted differences and integrity review |
| [Step 6 console](step6-console-2026-10-30/README.md) | 19/19 guest-VT comparisons per candidate and six transport checks |
| [Refreshed step 8/9 packages](step8-9-release-2026-10-30/README.md) | Approved documentation, fresh package/rebuild/link checks, full gate and backup |
| [Step 7 packages](step7-package-2026-10-30/README.md) | Exact archive linkage, installed assets, source rebuild and preservation |
| [Complete technical gate](step7-package-2026-10-30/closure/gate.json) | All 97 required checks passed |
| [Coverage review](../COVERAGE_REVIEW.md) | Nine unresolved citations and the limits of audit coverage |

Each environment recorded 303 baseline cases: 301 full matches and 302 file/exit
matches, with six exclusions. The separate historical follow-ups have 53 cases,
51 exact; the newer suites add 119 exact cases per environment. Do not merge
these inventories into an unexplained aggregate or count excluded cases as passes.

The refreshed step 8/9 archives supersede step 7 as the selected download set;
step 7 remains historical evidence. This is not an announcement of publication. [The release checklist](../RELEASE_CHECKLIST.md)
tracks remaining final CI and release-decision gates, including the earlier
saved-cursor CI failure retained in the step 8/9 receipt.
If later packaging changes archive bytes, use the newer reviewed artifact receipt
and checksums rather than attributing old package results to new inputs.

## Evidence interpretation and preservation

A recorded run or successful harness exit alone is not a passing comparison.
Required results include assertions, candidate/reference identity, complete
inventories, raw traces, saved bytes and subprocess statuses. The newer suite
checker reopens its evidence and recomputes comparisons. Declared exceptions
remain bounded; unknown differences are not normalized away.

Full recordings are local and are not included in a normal GitHub clone:

- `target/release-freeze-2026-10-30/`
- `target/naro-test-runs/claude-step5-2026-10-30-attempt01/`
- `target/step6-console-2026-10-30/`
- `target/step7-package-2026-10-30/`

Verified preservation outside the repository is documented in the dated backup
receipts. Those backups are on the same disk, not off-machine protection.
Claude's original step 5 checksum list has three stale entries for two mutable
ledgers; the [Codex review](step5-qualification-2026-10-30/codex-review.json)
records the discrepancy. All listed test artifacts matched. The original files
were preserved, and a separate complete manifest captures the final state.

To reproduce qualification, use the dated plans and fresh output directories,
record your exact executable/environment, and keep tests inside owned fixtures.
Never rerun a historical command into an existing evidence folder or assume a
local rebuild inherits qualification. [CONTRIBUTING.md](../CONTRIBUTING.md)
describes ordinary development checks.

## Historical records

The top-level `terminal.json`, `cli.json`, `regex.json`, `safety.json` and
`environment.json` describe an earlier frozen build; they are not the current
candidate's evidence. Earlier directories remain useful history:

- [Follow-up qualification](follow-up/README.md)
- [Root/home qualification](root-console/README.md)
- [Earlier guest-VT qualification](console-vm/README.md)
- [Earlier closure gate](closure/README.md)
- [Optional tiny qualification](tiny/README.md)

Use the hashes and scope in each historical report. Keep original reference
recordings and failed attempts intact. Historical profile sizes, test counts,
package successes and CI outcomes do not certify different later artifacts.
