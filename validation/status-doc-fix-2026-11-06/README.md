# Packaged status-document correction — 2026-11-06

The independent [Daybreak Blue access-program retest](../independent-retest-2026-11-06T085948Z/README.md)
found that both 0.1.2 archives shipped an `IMPLEMENTATION.md` identifying the
old 0.1.1 candidate. Commit `9d7cd10530501cf7f352b043d25e80756ff7d939`, tree
`11e6441073fb06637b526cc742d750171697a43c`, fixes the current version, directs
exact artifact identity to machine receipts, and labels the older counts as
historical. It also corrects that retest's provenance from the authoritative
outer CLI invocation: `daybreak_blue`, `gpt-6-sol`, high reasoning effort.
No separate Daybreak model/version is asserted.

The normal package builder now rejects a missing/mismatched current status
version or hardcoded current candidate hashes before writing output. The archive
checker validates the installed and source status documents. Existing CI already
runs these tools and their focused test files. Historical evidence and the pinned
GNU nano reference remain allowed; installed repository links retain their
immutable documentation revision.

## Identity and archive invalidation

Production inputs are unchanged. Their recomputed SHA-256 remains
`7b6ef4e024bc5d25f59fb66eebad7f8297d4be4f49a34d1037c3b8d4f928e636`.
Verification inputs changed: SHA-256 of
`git ls-tree -rz HEAD -- tests spec/tools tools` at the package commit is
`d5fadd77e0676fe91e8b6f0f09295b8837df7ce9e16c279034ebb5fcc010d3f1`.

The independently tested default and tiny executables were retained byte for
byte, with compiled revision `2888560a9a2709469334a417d1ad9ac3a91c30ba`.
Their SHA-256 values remain, respectively,
`894e0dcaf37d9a2ec7ee2380b0b705e35b3f0a0168455fa025523463da503e2a`
and `93e990da049e779d1164e76776a7c42d01fe5d42980974f2c5b78521438177ba`.
The new documentation/source revision is `9d7cd10530501cf7f352b043d25e80756ff7d939`.

The old independent-retest and final5 archive hashes remain historical and do
**not** identify or qualify these replacement archives. New exact archive hashes,
sizes, compiled identities and verification results are in [receipt.json](receipt.json).
The raw package and source-rebuild evidence is under
[`target/status-doc-fix-2026-11-06`](../../target/status-doc-fix-2026-11-06/).
This receipt is a documentation-only descendant of the package commit; it does
not claim that its own later commit is the source revision of those archives.

## Executed verification

- `python3 tools/test_package_docs.py`: 8 tests passed, including the source
  document, installed links, stale/missing/conflicting versions and stale hashes.
- `python3 tools/test_package_provenance.py`: 8 tests passed, including clean
  committed stale-version/hash fixtures rejected before binary access or output.
- `python3 tools/test_installer_transactions.py`: 16 tests passed.
- `/home/john/.cargo/bin/cargo fmt --check` and `git diff --check`: passed.
  An earlier bare `cargo` invocation was unavailable on this shell's PATH; the
  explicit configured Cargo path succeeded.
- Both fresh archives: 17/17 package checks and 44/44 installed-asset checks.
  These include installed/source status, hashes, installation/removal, malformed
  archives, offline source rebuild, rebuilt production fingerprint and features.
- Direct archive inspection: each source status is exactly the corrected file;
  each installed status is exactly its immutable-link transformation; versions
  and archive source revisions match. No editor production code was changed.

From the clean package commit, the package commands were:

```sh
python3 tools/package.py --binary target/independent-retest-2026-11-06T085948Z/frozen/naro-default --out target/status-doc-fix-2026-11-06/package-default
python3 tools/package.py --binary target/independent-retest-2026-11-06T085948Z/frozen/naro-tiny --features tiny --out target/status-doc-fix-2026-11-06/package-tiny
NANOSPEC_WORK="$PWD/target/status-doc-fix-2026-11-06/fixtures-default" python3 tools/check_package.py --archive target/status-doc-fix-2026-11-06/package-default/naro-0.1.2-x86_64-unknown-linux-gnu.tar.gz --source-archive target/status-doc-fix-2026-11-06/package-default/naro-0.1.2-source.tar.gz --out target/status-doc-fix-2026-11-06/check-default
NANOSPEC_WORK="$PWD/target/status-doc-fix-2026-11-06/fixtures-tiny" python3 tools/check_package.py --archive target/status-doc-fix-2026-11-06/package-tiny/naro-0.1.2-x86_64-unknown-linux-gnu.tar.gz --source-archive target/status-doc-fix-2026-11-06/package-tiny/naro-0.1.2-source.tar.gz --out target/status-doc-fix-2026-11-06/check-tiny
```

The checks ran sequentially with distinct owned fixture roots. Offline rebuilding
confirms source fingerprint/features; byte-for-byte rebuilt binary identity is
not claimed. The full editor/runtime campaign was not rerun for this documentation
and package-verification change.

## Remaining qualification

The original retest's early diagnostic timestamp gap remains. Issue #12
adversarial entry-swap/rename-exchange races, issue #14's nine unmapped runtime
behaviors, issue #15's unavailable locales/namespaces and broader guest-VT,
architecture/Miri/native-library qualification, and physical power-loss behavior
remain outside this correction. This work closes the shipped-status defect only.
It does not close GitHub issues or authorize publication, tagging, pushing or
global installation; none was performed.
