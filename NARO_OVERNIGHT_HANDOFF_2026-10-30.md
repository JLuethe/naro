> Published and verified: [NARO v0.1.0](https://github.com/JLuethe/naro/releases/tag/v0.1.0).
> See the [publication record](NARO_RELEASE_PUBLICATION_2026-10-31.md).
> The preparation and approval text below is retained as historical context.

# NARO overnight handoff — completed release preparation

Updated October 31, 2026. Start with [the final approval packet](NARO_RELEASE_REVIEW_2026-10-31.md).
John authorized fixes, testing, packaging, independent review and GitHub updates.
No tag, release, upload or community announcement is authorized.

## Exact identities

- Production: b934b1fcefa74adcf631c39b20ecd133c70edc59.
- Packaging and proposed tag target: 6473fe2043f8a7c3805e2994fea3f4f1bc8d4b50.
- Production fingerprint: 3ce5c0ee2d62983b32c1d71664c3404c799ff8fc08c16f6bfdb0b90d2acc21bd.
- Primary Ubuntu binary: 9af710dbb614423b53425c093a41a95b4733cfd539bfe40047b1bdac0bd7419d.
- Host evidence binary: 5767ed4938e25b0b49c0a9c546959a88260a9e2cbffb6dd472fe160c4ea666a7.
- Binary archive: 3d6b4d4f67fa97060993d31f4e75b6a83f65f52a465ce3efaf7334dead42179f.
- Source archive: 062b8f73b3d6aaa6b32f421a0cc182e142804ea8b6c295a01af707c8023362be.

## Completed

Save progress, safe prepend/backup failures, FIFO cancellation, completion redraw,
translated clipping and narrow footer behavior are implemented. Full fresh host
and Ubuntu qualification passed, with 151 newer exact cases each and 19 guest-VT
comparisons each. Final gate 101/101, transport 6/6, package 15/15, ordinary-prefix 5/5,
archive 23/23, 41 catalogs and 44 asset checks pass. No new mismatch was accepted.

Independent host 151+22, Ubuntu 151+10, bounded console 47, package/source 41 and
assets 94 reviews passed within their recorded scopes. Claude independently
reran the full 101 collector, checked raw evidence and packages/backups, and
passed the final metadata verification. Failed setup and reviewer-script attempts
remain preserved. Host subagent command timestamps were unavailable and disclosed.
One obsolete owned tiny-build polling loop was stopped after its ownership was
verified; no unrelated process was touched. Historical checkpoints remain in Git
history and preserved evidence; they do not qualify these current bytes.

## Evidence and downloads

- Current tracked receipts: validation/save-hardening-2026-10-31/.
- Freeze: target/release-freeze-narrow-progress-2026-10-31/.
- Full matrix: target/narrow-progress-qualification-2026-10-31/.
- Final package workspace: target/narrow-progress-release-2026-10-31/.
- Final Claude evidence: target/claude-save-hardening-final-2026-10-31/attempt02/.
- Final Claude metadata: target/claude-final-metadata-2026-10-31/.
- Outside-target backups and seven downloads: /home/john/Backups/naro/2026-10-31-narrow-progress/.

Backups are verified on the same filesystem, not off-device. Production CI
41179989844 and proposed-tag CI 41181383327 passed. Final review-delivery CI is
checked after that commit and retained as DELIVERY-CI.json in the backup directory;
FINAL-EVIDENCE-BACKUP.json records the last complete evidence preservation.

## Next action

Wait for John's explicit approval of the exact tag target, prerelease setting,
release body and seven-file manifest. Recheck CI, remote refs and asset hashes,
then follow PUBLICATION_PLAN.md in docs/release-v0.1.0-save-hardening-review-2026-10-31/.
Do not retarget the tag to the later review-delivery commit or substitute a build.
After authorized publication, independently download and rehash all uploaded
assets before reporting the public release complete. Community announcements
require separate authorization.
