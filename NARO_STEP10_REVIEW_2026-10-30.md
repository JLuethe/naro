# NARO step 10 — release preparation and review

Historical proposal, superseded by the [save-progress repair and renewed
qualification](validation/save-progress-2026-10-30/README.md). Claude completed
this review and identified missing transient save feedback. John selected a fix,
new builds and full requalification. The original packet below retains its
preparation-time state; its old tag target and archives are not current.

Prepared October 30, 2026. Nothing is published. This packet prepares items 1–4:
CI diagnosis, delivery verification, exact download verification, and a concrete
publication proposal. Claude's independent verification and John's publication
authorization remain separate.

## 1. CI failure: test synchronization repaired

The original failure captured the write prompt at cursor (20,21), before the save
completed; saved bytes and exit passed. The test used 150 milliseconds of quiet
output as a completion signal. Quiet output does not establish that fsync has
returned or that the editor has redrawn the completed-save screen.

Controlled 600/1,200 ms fsync delays reproduce the exact NARO failure with both
frozen candidates. Both nano references also fail the original cursor assertion
while writing. All four zero-delay controls pass. The repaired scenario waits
for the filename prompt before Enter and the `Wrote 2 lines` message before the
saved snapshot. All twelve synchronized delay cases pass; a deliberately short
deadline still fails. Every original expectation and editor input byte is retained.
For each executable, complete output traces are byte-identical across delays.

Commit `6004fa87d5cd3e3c1922bf1e9a58f28d39e871f4` contains the test-only fix.
No editor source, frozen binary, comparator, normalization or harness implementation
changed. Exact historical CI syscall latency was not recorded; the diagnosis is
supported by a controlled reproduction of its symptom, not a claim to have
measured that old runner's latency. See [diagnostic evidence](validation/step10-ci-2026-10-30/README.md).

Fresh synchronized-suite results: **40/40 exact on host and 40/40 exact on Ubuntu**,
with their own references and complete evidence checks. The full collector passes
**97/97**, combining those fresh reports with the unchanged step 5/6/package
records through an explicit input map. Original reports are preserved. The
additional original-scenario control runs also passed 40/40 per environment.

Claude has not independently verified this work yet. Start a clean Claude session
with [this prompt](docs/release-v0.1.0-review-2026-10-30/CLAUDE_PROMPT.md). It requests
independent diagnosis, controlled probes, negative controls, full affected suites,
identity checks and a report without changing the repository.

## 2. Delivery and CI

Proposed release target: `6004fa87d5cd3e3c1922bf1e9a58f28d39e871f4`.
Its CI run is [41170577786](https://github.com/JLuethe/naro/actions/runs/41170577786).
The earlier documentation/package commit 536d091 and receipt commit fafc491
both completed CI successfully. The old failed run remains in the audit trail;
it has not been rerun or relabeled to conceal its failure.

The [preparation-time CI snapshot](validation/step10-ci-2026-10-30/ci-preparation.json)
records the release target's run, SHA and observed status. Final verification
follows completion; an in-progress snapshot does not certify success.
The review packet is delivered in a later documentation/evidence commit. Its own
CI and remote SHA must also be checked after delivery and again before publication;
a successful run on a different commit is not a substitute. No tag currently exists
for the proposed v0.1.0 name at the preparation check. No release was created.

## 3. Verified downloads and preservation

The exact seven proposed assets are listed in the
[asset manifest](docs/release-v0.1.0-review-2026-10-30/asset-manifest.json), including
byte counts, full SHA-256 values and preserved paths. Source and binary tar archives
are unchanged from the verified step 8 set; package tests 15/15, asset checks 44/44
(41 catalogs), ordinary-prefix checks 5/5, offline rebuild and archive checks remain
valid for those identical bytes. Only the final qualification sidecar/checksum file
are refreshed to cite step 10; no installer or archived payload changed.

The production revision is fd91763; packaging/source-documentation revision is
536d091; the proposed tag is 6004fa8. Production inputs in the archive, frozen
executable and tag agree. The source archive includes its historical test snapshot;
the tag includes the subsequent synchronization fix. Do not claim identical whole
source trees or byte-for-byte build reproducibility.

The selected executable SHA-256 remains
`33a39eb339492720ec6166e84fea421749e0b2ec3bd612b276c2377f91b7c4a1`.
Original step 8 downloads and evidence are retained. The final seven-file set and
step 10 evidence are preserved under `/home/john/Backups/naro/2026-10-30-step10/`.
See the backup receipt in the validation directory. This is same-disk preservation,
not off-machine protection. Full raw evidence is not a proposed public release asset.

## 4. Concrete publication proposal

- **Tag:** annotated `v0.1.0` at exactly `6004fa87d5cd3e3c1922bf1e9a58f28d39e871f4`.
- **Release title:** NARO 0.1.0 — experimental Linux x86_64 release.
- **Setting:** GitHub prerelease, reflecting experimental scope; not stable/latest.
- **Description:** [release body](docs/release-v0.1.0-review-2026-10-30/RELEASE_BODY.md).
- **Assets:** exactly the seven files in the [manifest](docs/release-v0.1.0-review-2026-10-30/asset-manifest.json).
- **Execution and post-upload checks:** [publication plan](docs/release-v0.1.0-review-2026-10-30/PUBLICATION_PLAN.md).

Next action: obtain Claude's independent report, resolve any finding, confirm final
CI and asset hashes, then have John approve this exact proposal. No tag, release,
asset upload, announcement, or user/system installation has been performed.
