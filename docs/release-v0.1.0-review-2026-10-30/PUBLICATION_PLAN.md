# Publication plan — prepared, not executed

Proposed repository: `JLuethe/naro`.
Proposed tag: **v0.1.0** (annotated).
Exact target: **6004fa87d5cd3e3c1922bf1e9a58f28d39e871f4**.
Title: **NARO 0.1.0 — experimental Linux x86_64 release**.
Proposed GitHub release setting: **prerelease**, reflecting the experimental scope.
Do not mark it as the stable/latest release. This setting is part of John's review.

Use the exact seven files in `asset-manifest.json`, whose preserved locations,
byte counts and hashes are explicit. The two tar archives remain byte-identical
to the verified step 8 set. Build/environment/runtime records are also unchanged.
Only QUALIFICATION.json and SHA256SUMS are refreshed to identify step 10's
synchronization diagnosis and newest acceptance evidence. Earlier sidecars remain
in their original backup with the original archive receipts.

The source archive's production inputs match the tag. The full source archive
records packaging commit 536d091; compiled code records fd91763. Tag 6004fa8 adds
only the test synchronization fix and diagnostic evidence since the documentation
delivery. Do not imply that GitHub's automatically generated tag source archive
is byte-identical to the explicitly verified `naro-0.1.0-source.tar.gz` asset.

## Required before authorization

1. Confirm successful CI for the exact tag target and final delivered review
   commit; verify remote refs and ensure v0.1.0 does not already exist.
2. Review Claude's independent report. Resolve any new defect or unexplained
   mismatch; no expectation or normalization changes may hide a failure.
3. Recheck every asset against the manifest and SHA256SUMS, using the backup
   copies outside target. Confirm the tested executable and production fingerprint.
4. Have John approve the exact tag target, prerelease setting, RELEASE_BODY.md
   wording and seven-file asset manifest. This document is not approval.

## Authorized execution sequence

After those gates and explicit publication authorization, create the annotated tag
at the exact SHA above, push that tag, and create the GitHub prerelease using
RELEASE_BODY.md and precisely the seven manifest assets. Publish the binary and
corresponding source together. Never use a moving `main` ref as the tag target,
replace the existing archives, overwrite another tag, or substitute a fresh build.

Verify the published tag resolves to the approved commit. Download every uploaded
asset into a new empty directory; verify its SHA-256 against the approval manifest,
then run `sha256sum -c SHA256SUMS`. Check the binary/source/notes links anonymously.
Record release URL, asset IDs, hashes, and the verification result. Only then
update repository candidate/pending wording and the community announcement with
the actual release URL. Send no announcement until John authorizes posting it.

The existing backups protect against `cargo clean`, not disk loss. An off-machine
copy is useful additional preservation and is not claimed by these receipts.
