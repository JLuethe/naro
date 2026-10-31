# Step 7 — finalized technical package candidate

Date: October 30, 2026 (America/Los_Angeles).
Status: **complete**. Download files are identified, checksummed, backed up, and
supported by a passing complete technical gate. Nothing has been published.

## Plan and execution

1. Select the frozen Ubuntu default executable; retain host as qualification evidence.
2. Inspect the existing binary/source archives and prove their identities and contents.
3. Reuse package/source-rebuild evidence only for byte-identical archive inputs.
4. Add ordinary-prefix installation coverage in the recorded Ubuntu environment.
5. Run the complete collector across host, Ubuntu, guest-VT, transport and packages.
6. Assemble precise download/provenance/runtime/checksum files and preserve them
   outside `target/`, with a verification receipt and links to full raw evidence.

All six tasks are done. No editor rebuild or production/permanent-test change
was required. Each new check ran once, exited zero, and passed without waived
failures or altered normalization.

## Selected artifacts

Production commit: `fd91763c4f14d9bed8187d64d44f2136440b7b3e`.
Production fingerprint:
`4cabd71741ffc8ee0357d945c67904c8a2fd0089c12e9b32a1c5b3e35c394ae6`.
Ubuntu executable:
`33a39eb339492720ec6166e84fea421749e0b2ec3bd612b276c2377f91b7c4a1`.
Its features are default/empty; test-hooks, tiny and optional credits are absent.
The host executable is qualification evidence, not a second primary download.

| Archive | SHA-256 |
| --- | --- |
| `naro-0.1.0-x86_64-unknown-linux-gnu.tar.gz` | `a42e7dbfe39d24e3fe3b005e1d115fd52310f6fe6c6275baca7ea57985c04f80` |
| `naro-0.1.0-source.tar.gz` | `2bbb757b0d73577aa1c2ba0f32c16a36b22300e2fb2dc9a5aeb1d48913dd7460` |

Both archives are reused byte-for-byte from Claude's Ubuntu qualification.
All 1,143 source files match the clean frozen checkout and the source-file
manifest. Recomputing the production fingerprint from the source archive gives
the exact compiled fingerprint. The binary archive contains the exact qualified
executable, 134 installed payload files, all 41 catalogs and 44 syntax files,
translation PO sources, LICENSE, NOTICE, CREDITS, documentation and example
configuration. The standalone installer matches the frozen source copy.
All payload hashes/modes and archive member inventories passed inspection.

## Download list

The preserved directory is:
`/home/john/Backups/naro/2026-10-30-step7/downloads/`.

- `naro-0.1.0-x86_64-unknown-linux-gnu.tar.gz` — primary binary package, installer and assets.
- `naro-0.1.0-source.tar.gz` — exact corresponding frozen source.
- `build.json` — original package provenance, file hashes and linked symbol requirements.
- `BUILD-ENVIRONMENT.json` — original Ubuntu build/runtime/package records.
- `RUNTIME-REQUIREMENTS.md` — tested runtime, dependencies, installation and scoped qualification.
- `QUALIFICATION.json` — exact identities and technical acceptance results.
- `SHA256SUMS` — hashes of the preceding six files.

The archives' original internal manifests remain unchanged. The expanded
SHA256SUMS covers the new delivery sidecars as well as the original archives.
`build.json` and the internal manifest record the same compiled source identity;
later documentation commits are not represented as executable build commits.

## Validation

| Check | Result |
| --- | --- |
| Complete closure collector | **97/97**, exit 0 |
| Archive/source/identity audit | **20/20**, exit 0 |
| Reused Ubuntu package checks | **15/15**, exact same archive SHA |
| Catalog and installed-asset checks | **41 catalogs**, **44/44** checks |
| Offline corresponding-source rebuild | Previously passed in Ubuntu; fingerprint/features match |
| Additional ordinary-prefix install/uninstall | **5/5**, frozen Ubuntu image, exit 0 |
| Guest-VT qualification used by collector | **19/19** per exact candidate |
| Private VM transport used by collector | **6/6** |
| Assembled download checksums | All six payload files match |
| Freeze verification after work | Passed; originals unchanged |

The existing package checker covers spaced-prefix install, symlink launch,
installed hashes, all catalogs and syntax, offline source rebuild, malformed
archive rejection, destination symlinks, modified-file conflicts and ownership
on uninstall. The additional test exercises an ordinary private prefix using
the installer extracted from the archive: install, all installed hashes, exact
binary/build identity, native translation discovery, and uninstall preserving
an unrelated file. It runs as uid 1000 in a disposable no-network Ubuntu
container; it does not install anything into the host user's prefix.

The collector consumed both step 5 matrices, both step 6 guest-VT reports,
transport, unchanged Ubuntu package metadata and package checks. It reopened
all eight newer regression-suite bundles successfully. No collector patch,
evidence rewrite, locale normalization change, or missing-input waiver was needed.

The offline rebuild establishes source rebuildability and matching production
inputs/features; it does not claim bit-for-bit reproducible executable builds.
Runtime support is the recorded Ubuntu 24.04/glibc 2.39 environment, with measured
native libraries/symbols. No universal Linux or guessed minimum ABI is promised.

## Preservation and next gate

Working evidence: `target/step7-package-2026-10-30/`.
Preserved full evidence:
`/home/john/Backups/naro/2026-10-30-step7/step7-evidence.tar.gz`.
The seven download files and all 70 evidence files were verified against their
originals. Earlier complete step 5/freeze and step 6 archive hashes were also
reverified. The [backup receipt](validation/step7-package-2026-10-30/backup.json)
records all locations and hashes. These are same-disk backups outside the
repository; off-machine protection remains separate.

[Tracked reports and complete gate](validation/step7-package-2026-10-30/README.md).
Next is step 8 documentation reconciliation, followed by attribution/reporting
review and final release approval. Existing packaged documentation describes
the frozen source checkpoint; the delivery sidecars identify this qualification.
Public claims and comprehensive license/attribution clearance have not been
completed by this technical package audit. No tag, hosted release, or upload
has been published. Changes to these selected archive bytes would require new
checksums and appropriate package revalidation.
