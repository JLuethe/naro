# Validation evidence

## Current 0.1.0 candidate

The [save-hardening qualification](save-hardening-2026-10-31/README.md) identifies
the current candidates and complete 101/101 gate. Both environments pass the
fresh 303-case corpus contract and 151 newer exact regressions, including 22
progress and 10 save-safety cases. Guest-VT 19/19 each and transport 6/6 pass.
Ubuntu uses its own pinned reference and fresh observations.

Final downloadable archive hashes, package checks, independent reviews and CI
are recorded in the release review packet and QUALIFICATION.json. Technical
qualification does not authorize publication. Prior steps 5–10 and October 30
save-progress records remain historical under their original identities.

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
