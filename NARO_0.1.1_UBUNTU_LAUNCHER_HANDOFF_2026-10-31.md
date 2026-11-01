# NARO 0.1.1 Ubuntu launcher completion handoff — 2026-10-31

## Outcome

The reported CLI and cleanup failures were tooling/environment problems. Further
complete-pipeline testing found missing collector executable copies and two
package-check prerequisites. All are fixed without changing production source,
assets, original GNU observations, scenario inputs or acceptance policy.

Final code commit: `accc766af9ff7e36ec206dea697410e3f8f31674`. Exact-source CI run
[41261807521](https://github.com/JLuethe/naro/actions/runs/41261807521) passed.
The final 151 affected tooling tests passed. Both default-feature candidates were
rebuilt and frozen from this complete reviewed source; no test hooks are enabled.

## Changes

- Provide the historical absolute GNU syntax include path as a read-only bind of
  all 44 exact frozen bundled files. They match the historical GNU installation.
  Both real editors print nothing without the path; all 38 CLI comparisons pass
  when it is provided. The absolute c.nanorc render include is covered too.
- Use bounded owned tmux cleanup with actual per-client and probe evidence.
  Confirmed dead private sockets succeed; unknown errors, timeouts, socket
  symlinks and remaining sockets fail. Preserve the original command exit after
  successful cleanup. Host cleanup respects the same result.
- Retain verified top-level `naro` and `reference.bin` collector inputs, recording
  source/destination/hash and preserving executable modes. Refuse altered inputs
  or overwriting evidence. Per-suite files alone did not satisfy the contract.
- Export the pinned Cargo executable for source rebuilds. Select the existing
  de_DE.UTF-8 locale for the exact German symlink translation probe, retaining
  stdout/stderr/locale evidence. Source rebuilds use --offline --locked.
  The checker is now included in the verification fingerprint. The original
  four scenario locales, including requested-French/C fallback, remain unchanged.
- Move CLI checks earlier without changing required Ubuntu stage membership.

## Final immutable identities

Freeze: `/home/john/Code/naro/target/ubuntu-launcher-repair-0.1.1-2026-10-31/freeze-attempt04`.

| Identity | Commit / SHA-256 |
|---|---|
| Source commit | `accc766af9ff7e36ec206dea697410e3f8f31674` |
| Source tree | `ba92e90e9c2e2c0dcaa59389334da26e013130a9` |
| Production | `63936243e73d0a3fb536d3c0a0fb0e6fe57be09da5f5bc0387ee10250b3d7093` |
| Verification | `4563417b7c8039cce9ac6a687eeced081304f19a00ff8f8f5a78526b7b1a2b83` |
| Host NARO | `ab37d9fa240297a5390da858757909e9c3996314ec59cba4545c5b096b29c647` |
| Ubuntu NARO | `70ab6932323a6b679e628bdb6cfddead8a6ff50160d741782ae8649664dc5a00` |
| Host nano | `b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2` |
| Ubuntu nano | `6540492f810998a20a4dba4ac8048cd8b76d37a39e642f14f9f9c3d30c621ba7` |
| Freeze manifest | `70cab79381ab59a07dbd7a62d7bda5072c1c5127591c1d7463f280ab74e7efbb` |

Production remains identical to the previous candidate fingerprint. Binary hashes
changed because build provenance names the complete new source commit. Earlier
host 46/46 results cannot qualify this final host hash. The Ubuntu candidate
remains the intended portable Linux x86_64 download after complete qualification.

## Completed final validation

- Tools 151/151 across 12 suites at the final verification fingerprint; no source
  changes during the run (`unit-review03/SUMMARY.json`).
- Focused host: 12 commands exit 0, CLI 38/38, environments 13/13 (3 raw/10 identity),
  layout 21/105, original EOF pair 20 assertions per side, fresh Smoke/Edit,
  FEAT-015 and corruption controls. Frozen files unchanged; only owned sockets
  cleaned. This is focused readiness, not full host qualification.
- Complete Ubuntu: launcher exit 0, all 32 exact required status receipts0 and
  completion sentinel present. Fresh own-Nano 303 reference and candidate records;
  original named deviations only. All historical suites, six regression suites
  totaling151 cases, ioctl 8, CLI 38/regex 162/safety 2, recovery/panic, extensions,
  1MiB/10MiB, assets and packaging ran on the final hash.
- Independent raw reopening with frozen tools recomputed comparisons,
  assertions, source-case membership and classifications. It also checked all 38
  CLI results against the original corpus, readonly syntax inventory 44, retained
  executable identities, package 15/15, exact archived executable and cleanup.
  See `UBUNTU-INDEPENDENT-REOPEN.json` for full accounting and empty problem lists.
- Fresh final guest fixtures are prepared and preserved, **unbooted**, at
  `/tmp/nv011-uf04/nanospec-work/TEST-VT-VM-011-{HOST,UBUNTU}/fx`. Preserved copy:
  `/home/john/Code/naro/target/ubuntu-launcher-repair-0.1.1-2026-10-31/final-vm-fixtures-v2/`. Source, binaries, runtime archive and kernel
  identities are verified in `fixture-report.json` and its manifest.

Final raw evidence: `/home/john/Code/naro/target/ubuntu-launcher-repair-0.1.1-2026-10-31/ubuntu-full-attempt02/`.
Final host readiness: `/home/john/Code/naro/target/ubuntu-launcher-repair-0.1.1-2026-10-31/final-readiness-host-v2/`.
The complete Ubuntu result may be reused after Claude independently reopens it;
it should not be rerun solely to change the executing agent's name.

## Candidate package files

These are local candidate files, not published downloads:

| File | SHA-256 |
|---|---|
| `/home/john/Code/naro/target/ubuntu-launcher-repair-0.1.1-2026-10-31/ubuntu-full-attempt02/package/naro-0.1.1-x86_64-unknown-linux-gnu.tar.gz` | `a452863b8a5f75a110640cd947fad13ae75b85dcb4c99638aede6f5adf7f9d52` |
| `/home/john/Code/naro/target/ubuntu-launcher-repair-0.1.1-2026-10-31/ubuntu-full-attempt02/package/naro-0.1.1-source.tar.gz` | `3641d8e5ac75ac62a48d9374c0eb807857d7a27df45bb6f3ca4b2e30a439e3f5` |

The binary archive contains the exact Ubuntu executable above. Source matches
frozen production and builds offline; licenses, attribution, translations,
syntax, installer, provenance, runtime requirements and checksums are retained by
the established package checks. Final release closure is still pending.

## Preserved attempts and backup

Original Claude attempt02 remains unchanged. Host46 passed on its older binary;
Ubuntu wrote25/32 receipts with CLI1 and cleanup1, outer 125. Its verified complete
archive is outside target at
`/home/john/Backups/naro/2026-10-31-phaseB-attempt02-blocked/blocked-phaseB-attempt02.tar.gz`,
SHA `93fe887be9b70ca71e321414f29ecfd5ed343cb10503b6e23b90f57dd4432317`.

All diagnostic and failed setup attempts remain under the work root. In
particular source fa2739b/freeze03 full Ubuntu produced32 receipts,31 zero and
package-check1; cleanup was0 and no editor difference was found. It is diagnostic,
not final qualification. The separate package preflight15/15 retains the same
archives and demonstrates the prerequisite fix. Final source accc766/freeze-attempt04 is the
only authoritative replacement freeze. Build01/02 setup failures and the initial
process-test shutdown-race failure are retained honestly in ATTEMPTS.md.

Final freeze, complete evidence and prepared fixtures are preserved under
`/home/john/Backups/naro/2026-10-31-ubuntu-launcher-0.1.1/`.
The archive name is `ubuntu-launcher-freeze-and-evidence.tar.gz`.
Exact checksum/member counts and stream-verification receipt are kept outside
the payload and under `validation/ubuntu-launcher-0.1.1-2026-10-31/`.
The archive verifies every member, regular-file byte, permission mode and symlink
target against the source inventory. These backups are on the same filesystem,
not off-device. Final evidence manifest and tracked receipts identify the payload.

## Remaining qualification

Use [the new exact-hash Claude prompt](CLAUDE_0.1.1_PHASE_B_RESUME_UBUNTU_FIX_2026-10-31.md).
Claude must independently reopen the retained final evidence, then run the full
host matrix for the final host hash, both 19-case genuine guest-VT groups,
transport 6, the complete collector and the release gate. Record new evidence in
a fresh attempt03, preserve both reused Ubuntu and new outputs, and back up the
result outside target. Investigate every missing/failed check without weakening
policies. No final technical gate has passed yet. No 0.1.1 tag, upload, release
publication or announcement is authorized or performed by this handoff.
