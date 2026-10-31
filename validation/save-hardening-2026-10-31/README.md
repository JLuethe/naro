# Save hardening and renewed release qualification

Production: `b934b1fcefa74adcf631c39b20ecd133c70edc59`. Production fingerprint:
`3ce5c0ee2d62983b32c1d71664c3404c799ff8fc08c16f6bfdb0b90d2acc21bd`.

Primary Ubuntu executable: `9af710dbb614423b53425c093a41a95b4733cfd539bfe40047b1bdac0bd7419d`.
Host qualification executable: `5767ed4938e25b0b49c0a9c546959a88260a9e2cbffb6dd472fe160c4ea666a7`.
Both are clean default-feature offline builds from the same committed source.
The [identities](identities.json) bind candidates and each environment's reference.

Fresh host and Ubuntu qualification passes: 303 corpus cases, 301 full / 302
file-exit matches, six exclusions; CLI 38 / regex 162; historical 53 cases / 51 exact;
151 newer exact regressions (58+6+15+40+22+10); guest-VT 19/19 each;
transport 6/6. Root/home has 27 exact plus its separately asserted no-home case.
Recovery, write failures, installed assets/locales and 1 MiB / 10 MiB checks pass.
The [complete technical collector](closure/gate.json) passes 101/101.
No new mismatch was accepted or normalized. Ubuntu used its own reference and
fresh observations. The verifier fingerprint is unchanged.

Fixes cover all save-progress messages, safe prepend and backup read failures,
blocked-save cancellation, completion removal, translated clipping and narrow
footer behavior. Development negative controls and all failed setup attempts
remain preserved; only the exact frozen runs above qualify these executables.
The [Claude code review](claude-code-review.md) is source-only, separately scoped.

Final archives use a later documentation commit with the same
production fingerprint and exact Ubuntu executable. Fresh final archive checks,
independent evidence/asset reviews, CI and preservation receipts are recorded
with the final review packet. Publication requires John's approval.

[Previous qualification](../save-progress-2026-10-30/README.md) remains historical
and does not qualify these new bytes. Optional tiny is covered by separate CI
assertions, not this downloadable candidate or a full terminal parity claim.
Physical keyboard trials, other platforms and a security audit remain outside
scope. Nine historical unresolved specification citations remain disclosed.

## Final package and independent review

The final corresponding-source archive matches packaging commit
`6473fe2043f8a7c3805e2994fea3f4f1bc8d4b50`; the exact frozen Ubuntu executable
is reused. Final package 15/15, ordinary-prefix 5/5, archive 23/23 and the
[final package gate](final-package-gate.json) 101/101 pass. Production and proposed
tag CI succeeded; their exact receipts are retained here.

[Claude's final review](CLAUDE_FINAL_REPORT.md) passes with no technical blocker.
It independently reran the complete 101-check collector, revalidated both 151-case
raw evidence sets, and checked source, downloads, CI and backup payloads.
[Separately attributed reviews](reconciled-reviews.json) include fresh host 22 and
Ubuntu 10 replays, bounded console provenance and package/source/asset audits.
Failed setup and reviewer-script attempts are preserved, not counted as passes.
Host replay command timestamps were unavailable and explicitly disclosed.

The old pending status in development-checks.json is now clearly labeled as a
historical checkpoint; it never replaced current frozen qualification. One
obsolete task-owned polling loop was identified and stopped. No unrelated
process was stopped. No tag, release, upload or community announcement was made.
See [the final approval packet](../../NARO_RELEASE_REVIEW_2026-10-31.md).

[Final narrow metadata review](CLAUDE_METADATA_REPORT.md) verifies the reconciled
qualification sidecar, checksums and manifest, with both archives unchanged.
The final delivery CI and complete preservation receipts are written after the
review-delivery commit, outside target as described in the approval packet.
