# Validation evidence

## Current 0.1.0 candidate

The save-progress repair supersedes the previous candidate and step 10 proposal.
See [renewed qualification](save-progress-2026-10-30/README.md) and its
[complete technical gate](save-progress-2026-10-30/closure/gate.json).
Production commit: `16f6398968adc1f815055a4413cf0465aed28126`.
Primary Ubuntu executable: `b95bb4f9984f8e321fbd69e2a4e3058c7f184d6b35a8ae7650f6f5b7897f90bf`.
Host qualification executable: `4a97874ca06d2e3093f81769c5e0989554a5c87cf8f95ef7d43d9074102c0d7d`.
Reference source: GNU nano `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.

Both candidates passed full fresh qualification: 303 recorded corpus cases,
301 full / 302 file-exit matches and six exclusions; CLI 38 / regex 162;
historical follow-ups 53 with 51 exact; 132 newer exact regressions; 19 guest-VT
comparisons each. The complete gate passes 99/99. Host root/home retains 27 exact
cases plus its separately asserted no-home difference. No new mismatch was
accepted or normalized. Ubuntu used its own reference and fresh observations.

The primary archives are repackaged after documentation refresh; final archive
hashes, package checks and independent review are identified by the release
review packet and downloadable qualification sidecar. Source and binary hashes
must be matched to those exact assets. Publication is not implied.

[Step 5](step5-qualification-2026-10-30/README.md),
[step 6](step6-console-2026-10-30/README.md),
[step 7](step7-package-2026-10-30/README.md),
[steps 8–9](step8-9-release-2026-10-30/README.md), and
[earlier step 10](step10-ci-2026-10-30/README.md) retain their historical identities.
The earlier independent Claude review confirmed the synchronization repair and
found missing save feedback; its decision led to this production repair and full
requalification. Historical success does not qualify the replacement binaries.

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
