# NARO 0.1.1 publication verification

John approved publication of the exact reviewed target, body and seven files.
PREFLIGHT.json records the approval, passing frozen-source check, unchanged
production/tooling fingerprints, 69-check gate, package15 and ordinary-prefix5.
CI-TARGET.json and CI-DELIVERY.json both record successful CI before tagging.
The first preflight waited for review CI; no mutation happened during that wait.

PUBLICATION-VERIFIED.json records the annotated tag target, public release URL,
asset IDs, sizes and SHA-256 hashes. Draft and anonymous public download hashes
matched all seven approved files. Published body and prerelease settings match
approval; 0.1.0 remains unchanged, and latest-release status is unchanged.
Four public documentation files match the approved tag; the release page is public.

[Publication result](../../docs/release-v0.1.1-review-2026-10-31/PUBLICATION_RESULT.md)
provides clickable downloads. The original approval asset manifest remains
historical; PUBLICATION-VERIFIED.json is the final published-state receipt.
A separate outside-target publication archive and copied raw receipts are recorded
in PUBLICATION-BACKUP.json after verification. Backups are not off-device.
No editor rebuild, policy changes or community announcement were performed.
