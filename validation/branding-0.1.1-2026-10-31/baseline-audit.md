# Narrow-progress freeze baseline audit

Observed 2026-10-31 17:31 UTC after `prepare-freeze` attempt01 stopped before source cloning or candidate builds.

## Working baseline mismatch

`target/release-freeze-narrow-progress-2026-10-31/verify-freeze.py` fails only at `references/source/.git/index` while checking the recorded payload hashes. Independent comparison of all `freeze.json` payload entries found exactly one difference among 15,061 files:

| Path | Recorded SHA-256 | Current SHA-256 |
| --- | --- | --- |
| `references/source/.git/index` | `649268285a867a42bcce09e74a4ef07f2cd74fa7f477a4541b122acd980d3216` | `4db89e4da88501f81e8476358796ef12de56fbbba50ab0d6f4c7efe157a111e7` |

All other 15,060 recorded file hashes and all 11 symlink targets match. The pinned nano repository remains clean at its recorded commit/tree. The NARO source remains clean at commit `b934b1fcefa74adcf631c39b20ecd133c70edc59`, tree `0908b5c978791669b343325b218c95f9955fceb3`; production fingerprint `3ce5c0ee2d62983b32c1d71664c3404c799ff8fc08c16f6bfdb0b90d2acc21bd` and verification fingerprint `604c032c865701dac6f5fc0f0c9ce5e3764ed3e434b51e2ccea5fdf8172d45aa` match the manifest.

Candidate and reference binaries retain their recorded hashes:

| Artifact | SHA-256 |
| --- | --- |
| Host NARO | `5767ed4938e25b0b49c0a9c546959a88260a9e2cbffb6dd472fe160c4ea666a7` |
| Ubuntu NARO | `9af710dbb614423b53425c093a41a95b4733cfd539bfe40047b1bdac0bd7419d` |
| Host nano | `b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2` |
| Host-root nano | `fe02ea07dc9a1e0afa009ef97dc034728995e39c65b75455985b0cf980fa3def` |
| Ubuntu nano | `6540492f810998a20a4dba4ac8048cd8b76d37a39e642f14f9f9c3d30c621ba7` |

Both candidate build-info files and both build-record files also match the freeze manifest. This establishes that the prepare failure is confined to the Git index hash; it does not establish that the failed prepare attempt built anything (it did not).

## Backup archive validation

Receipt: `/home/john/Backups/naro/2026-10-31-narrow-progress/FREEZE-BACKUP.json`.

- Archive SHA-256: `02ee62fc78f6109a2a21a3c9746a581f603cf025b0fd949bb8d9fd5d25e54ec0`, matching the receipt.
- Archive size: 143,707,106 bytes, matching the receipt.
- Embedded freeze-manifest SHA-256: `3652135cf2538507174960a7587cac6073541a28920429b36956f2b78885020c`, matching the receipt.
- Streamed every member without extracting. No absolute or parent-traversal paths and no unexpected member types were found.
- Every one of the 15,061 freeze-manifest file entries and 11 symlink targets matches the archive. The archive additionally contains files omitted from the payload manifest, including Git metadata and host build cache; those extras do not replace or alter the manifest checks.

Recommended restore path: verify the archive against the receipt, extract it into a new target directory while preserving the archive's `release-freeze-narrow-progress-2026-10-31/` top-level directory name, then run its unchanged `verify-freeze.py`. Keep the current baseline and this attempt's logs untouched. The audit did not extract or modify the archive or baseline.

## Executed checks and actual statuses

- Attempt01 preparation: exit 1, baseline verifier stopped at the single `.git/index` mismatch; no source clone or build started.
- Full working-baseline manifest comparison: exit 0; one file mismatch, zero symlink mismatches.
- NARO and nano Git identity/fingerprint inspection: exit 0; identities and cleanliness matched manifest.
- Backup receipt/archive SHA-256 check: exit 0; both matched.
- Full archive streaming comparison: exit 0; all manifest entries matched and no unsafe paths/member types were found.

Raw initial failure output is retained in `prepare-freeze.log`; runner status is in `BUILD-STATE.json` and command notes in `BUILD-COMMANDS.log`.
