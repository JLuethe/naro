# NARO 0.1.0 — final save-hardening candidate

Prepared October 31, 2026. The rebuilt candidates passed full qualification and
final package verification. Independent asset, Claude evidence and final metadata reviews passed.
Nothing is published; John must approve the exact proposal below.

## Changes and verification

Save progress now displays `Writing...`, `Writing to FIFO...` and `Making backup...`.
The follow-up fixes preserve unreadable prepend destinations, require explicit
confirmation for backup read failures, support cancellation while a FIFO open
blocks, and match completion removal, translated clipping and narrow footers.
Twenty-two progress and ten save-safety regressions cover these changes.

Both frozen candidates pass the retained 303-case corpus contract: 301 full and
302 file/exit matches, with six exclusions. CLI 38, regex 162, historical 53/51 exact,
151 newer exact regressions, recovery/write failures/locales/large files and
19 guest-VT comparisons per candidate pass. Ubuntu uses its own reference and
fresh observations. Host root/home has 27 exact plus the separately asserted
no-home case. Transport 6/6 and the complete final technical gate 101/101 pass.

Final archives passed 15 package checks, five ordinary-prefix checks, complete
inventory/hash/source audits, all 41 catalogs/44 asset checks and offline source
rebuilding. Byte-for-byte reproducible rebuilding is not claimed.
See [qualification](validation/save-hardening-2026-10-31/README.md).

Production: `b934b1fcefa74adcf631c39b20ecd133c70edc59`.
Production fingerprint: `3ce5c0ee2d62983b32c1d71664c3404c799ff8fc08c16f6bfdb0b90d2acc21bd`.
Primary Ubuntu executable: `9af710dbb614423b53425c093a41a95b4733cfd539bfe40047b1bdac0bd7419d`.
Packaging/source revision: `6473fe2043f8a7c3805e2994fea3f4f1bc8d4b50`. Its tracked source is exactly
the source archive; production inputs match the tested executable. Later review
receipts do not change that source archive or proposed tag target.

[Production CI](https://github.com/JLuethe/naro/actions/runs/41179989844) and
[proposed-tag CI](https://github.com/JLuethe/naro/actions/runs/41181383327) succeeded.
Final review-delivery CI follows the review commit.

## Exact publication proposal

- Annotated tag **v0.1.0** at **6473fe2043f8a7c3805e2994fea3f4f1bc8d4b50**.
- GitHub **prerelease**, titled **NARO 0.1.0 — experimental Linux x86_64 release**.
- [Release description](docs/release-v0.1.0-save-hardening-review-2026-10-31/RELEASE_BODY.md).
- Exactly seven files in the [asset manifest](docs/release-v0.1.0-save-hardening-review-2026-10-31/asset-manifest.json).
- [Publication and post-upload checks](docs/release-v0.1.0-save-hardening-review-2026-10-31/PUBLICATION_PLAN.md).

Working downloads are under `/home/john/Code/naro/target/narrow-progress-release-2026-10-31/downloads/`; preserved copies are under
`/home/john/Backups/naro/2026-10-31-narrow-progress/downloads/`. Freeze, full evidence and package backups were reopened and hashed.
These are same-filesystem backups, not off-device protection.

## Review status and limits

Claude's focused static reviews found no remaining default-release blocker.
Independent frozen behavior, console, package and asset reviews are separately
attributed in [the review receipts](validation/save-hardening-2026-10-31/reconciled-reviews.json).
[Claude’s final report](validation/save-hardening-2026-10-31/CLAUDE_FINAL_REPORT.md)
finds no technical blocker or unexplained mismatch. Qualification metadata and
checksums now record the completed reviews.
[Claude’s narrow metadata verification](validation/save-hardening-2026-10-31/CLAUDE_METADATA_REPORT.md)
checks the final bytes. Successful testing does not authorize publication.

Existing invalid-regex, NUL-as-Yes, two signal-cleanup and isolated-root no-home
differences remain declared. Six corpus exclusions and nine unresolved spec
citations remain disclosed. Optional tiny has separate CI assertions, not full
terminal parity qualification or a downloadable build. Physical-keyboard trials,
other platforms and a security audit are outside the measured scope.

## Delivery and next action

The final review commit is pushed to GitHub and its CI is checked after the
commit. The exact delivery result is retained outside target at
`/home/john/Backups/naro/2026-10-31-narrow-progress/DELIVERY-CI.json`.
Final evidence preservation is recorded there in `FINAL-EVIDENCE-BACKUP.json`.
The reviewed source/tag target remains `6473fe2043f8a7c3805e2994fea3f4f1bc8d4b50`;
the later review-delivery commit adds documentation and receipts.

John's next decision is publication approval for this exact proposal. Until then,
no tag, release, asset upload or announcement is authorized. At publication time,
recheck remote refs, both CI receipts and all seven hashes, then follow the
publication plan's upload and independent download-verification steps.
