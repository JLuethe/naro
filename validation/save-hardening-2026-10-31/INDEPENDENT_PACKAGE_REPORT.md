# Independent final package and source audit

**Passed: 41 checks, with no package blocker or unsupported claim found in the root archive audit.** This review independently recomputed 32 archive, Git-tree, checksum and identity checks, and inspected nine groups of recorded runtime outcomes. No runtime test repetition was needed.

## Archive and source identity

The binary archive contains the exact frozen Ubuntu executable `9af710dbb614423b53425c093a41a95b4733cfd539bfe40047b1bdac0bd7419d`, with the default-feature build record. Its complete payload inventory, hashes, permissions and installer match the manifest and committed source.

All **1,433 source files** match the Git blobs in packaging commit `6473fe2043f8a7c3805e2994fea3f4f1bc8d4b50`. The production file inventory and blobs are identical to frozen production commit `b934b1fcefa74adcf631c39b20ecd133c70edc59`; the recomputed fingerprint is `3ce5c0ee2d62983b32c1d71664c3404c799ff8fc08c16f6bfdb0b90d2acc21bd`. The packaging commit adds documentation/evidence while retaining those production bytes. Source archive file modes preserve Git executable bits.

The source includes the expected **22 progress, 10 safety and 3 tiny-safety cases**, identical to the frozen production commit. The 40-case step3 suite is byte-identical to the original synchronized repair commit; its decisive save case waits for the filename prompt before Enter and for `Wrote 2 lines` before the saved snapshot.

## Recorded runtime outcomes

The package checker contains the exact expected 15 checks, all passing, and is bound to the current binary archive hash. Its retained command invokes the current source archive; the source checker uses `cargo build --release --offline`, the build log records successful compilation, and the rebuilt source-fingerprint/default-feature checks pass. This supports an offline source-build claim, not byte-for-byte rebuild reproducibility.

The ordinary-prefix report has the exact five expected passing checks. Its archive hash, installer hash and compiled identity match the current archive. Retained install/identity/translation/uninstall logs agree with the 138-file payload and show the expected German translation. The package asset report records all 41 catalogs and 44 asset checks passing. The original package, checker and ordinary-prefix containers ran with networking disabled and the pinned Ubuntu image.

Root's archive audit reports 23 passing checks with the correct archive, executable, production-source and evidence hashes. The recorded closure gate reports 101/101 passing checks. These recorded runtime results were inspected; this independent task recomputed the archive and Git identities directly.

## Exact archive checksums

- Binary archive: `3d6b4d4f67fa97060993d31f4e75b6a83f65f52a465ce3efaf7334dead42179f`.
- Source archive: `062b8f73b3d6aaa6b32f421a0cc182e142804ea8b6c295a01af707c8023362be`.

## Evidence and limits

- Detailed successful checks: `attempt02/RESULT.json`.
- Combined command records: `REVIEW_COMMANDS.json`; individual Git command records are retained per attempt.
- Attempt explanation: `ATTEMPTS.md`. The first checker used an incorrect manifest/sidecar schema assumption; the corrected second attempt passed without any artifact change.
- Final integrity inventory: `EVIDENCE-SHA256SUMS`.

Download-sidecar consistency, final CI and publication approval are separate release checks. This audit changed no source, frozen artifact, package, runtime evidence or publication state. The accepted Ubuntu independent-review directory was left untouched.
