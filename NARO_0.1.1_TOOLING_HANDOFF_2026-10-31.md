# NARO 0.1.1 tooling handoff — 2026-10-31

The six qualification-tooling blockers are repaired, committed and frozen. The
remaining CLI-help identity wording is also fixed. Both replacement candidates
have passed focused readiness; full release qualification is the next task for
Claude. No 0.1.1 tag, asset upload or publication has occurred.

## Authoritative frozen inputs

Use only `/home/john/Code/naro/target/qualification-tooling-0.1.1-2026-10-31/work/freeze-attempt03`. Earlier 0.1.1 freezes, including attempts 01 and 02, are
superseded and retained as evidence.

| Input | Identity |
|---|---|
| Source/tooling commit | `eb9ae23a128d291a47af0ab463f322b5a36c6fd1` |
| Source tree | `08b669a448b41591da6197a24c34f4451196ac7d` |
| Production fingerprint | `63936243e73d0a3fb536d3c0a0fb0e6fe57be09da5f5bc0387ee10250b3d7093` |
| Verification fingerprint | `2e0d1804f37816018425c8e84c8d0b743ac16b75a5d6c46f98b7403d2de83a2d` |
| Host candidate | `9c118168ff0903f9b7de8606ced7fcbe5aa48386fff17f76a7b31e960f0871cc` |
| Ubuntu candidate | `2d3f20f2ab4ed66b9b04a6d47bda8b6e3b5c79664150074a423fa792905d5dba` |
| Host nano | `b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2` |
| Ubuntu nano | `6540492f810998a20a4dba4ac8048cd8b76d37a39e642f14f9f9c3d30c621ba7` |
| Isolated-root nano | `fe02ea07dc9a1e0afa009ef97dc034728995e39c65b75455985b0cf980fa3def` |

Both candidates are version 0.1.1, default features, without test-hooks. Their
production fingerprint is identical. Production help correction commit:
`548a6682b8567ea670a71f9e51cc44abdd3be085`. The raw comparator, original GNU
observations, original reference scenarios and catalog/attribution assets remain
unchanged by the tooling repair.

## What passed

| Focused readiness | Host | Ubuntu, inside pinned image |
|---|---:|---:|
| CLI branding | 5/5 | 5/5 |
| Title layout | 21 cases / 105 assertions | 21 cases / 105 assertions |
| Original paired blocker | 20 assertions per editor; strict reopen passes | Repeated fresh pairs; strict reopen passes |
| Original corpus smoke/edit blocker | 2 accepted, 0 unexpected | 2 accepted, 0 unexpected |
| Seeded history restoration | Cursor (1,11), row `l40` | Cursor (1,11), row `l40` |
| Forged verdict/explanation evidence | Rejected | Rejected |
| Frozen inputs before/after | Unchanged | Unchanged |

Readiness reports:

- `/home/john/Code/naro/target/qualification-tooling-0.1.1-2026-10-31/work/readiness-frozen-host/RESULTS.md`
- `/home/john/Code/naro/target/qualification-tooling-0.1.1-2026-10-31/work/readiness-frozen-ubuntu/REPORT.md`
- Build receipt: `/home/john/Code/naro/target/qualification-tooling-0.1.1-2026-10-31/work/build-attempt03/FREEZE-ATTEMPT03-RECEIPT.json`
- Fresh fixture receipt: `/home/john/Code/naro/target/qualification-tooling-0.1.1-2026-10-31/work/FINAL03-FIXTURE-RECEIPT.json`

The broader final local batch passed all 16 Python/unit/manifest commands,
including namespace 7, classifier 12, evidence checker 46, closure 9, and the
original comparator 14. Subsequent VM-helper regressions pass 9/9 and actual
fixture preparation succeeds. Detailed logs and all failed setup attempts are
preserved under `target/qualification-tooling-0.1.1-2026-10-31/`. These are
readiness checks, not fresh full-matrix qualification.

## Tooling behavior

- Raw exact, reviewed identity, historical deviation and unexpected results are
  counted separately. The original raw comparator stays strict.
- Expected identity surfaces come from the reference and reviewed independent
  oracles. Unknown identity layouts fail closed. No title-row mask is used.
- The v2 gate reopens raw recordings, assertions, input bytes, hashes and
  classifications; modified flags, explanations, counters and typed booleans
  are rejected. Historical deviations bind complete reviewed residuals.
- Frozen launchers accept explicit source/binary/reference/output inputs, build
  optional variants in private spaces, and preserve the supplied default binary.
- Both corpus environments use `/tmp/nanospec-work`: seeded history fixtures
  contain that literal path. The gate proves FEAT-015 actually restored line 40.
  Do not run competing host matrices against these same fixture IDs. The Ubuntu
  container has a separate filesystem. Reports/builds/tmux sockets remain private.
- Every required host stage and all 32 Ubuntu receipts are checked. Ubuntu locale
  changes are limited to the established `locpath` replacement in private copies.

## Fresh guest fixtures

Prepared, hash-verified, never booted:

- `/tmp/nv011-final03/nanospec-work/TEST-VT-VM-011-HOST/fx`
- `/tmp/nv011-final03/nanospec-work/TEST-VT-VM-011-UBUNTU/fx`

Preserved complete copy: `/home/john/Code/naro/target/qualification-tooling-0.1.1-2026-10-31/work/vm-fixtures-preserved-final03`. Keep guest
socket paths short and record any restoration/relocation. Both guests use the
frozen Ubuntu nano reference. No previous guest observation qualifies these new
candidate bytes.

## Preserved evidence and remaining work

Claude's original 761 manifest entries plus manifest were verified and backed up:
`/home/john/Backups/naro/2026-10-31-claude-0.1.1-phaseA/claude-phaseA-evidence.tar.gz`
(SHA-256 `3e76a3d1426a5735a4a6cab01d457cbed9d890b7499933a28c10241ecd6e2d00`).
The new freeze, fixtures and readiness evidence are preserved by the separate
backup receipt at
`/home/john/Backups/naro/2026-10-31-qualification-tooling-0.1.1/BACKUP.json`.
These copies are outside `target/` on the same filesystem, not off-device.

Next: run fresh full host/Ubuntu qualification, 19 guest-VT cases per candidate,
six transport checks, package validation and the v2 closure gate. Then review
0.1.1 packages/publication material and obtain publication approval. The existing
0.1.0 release stays unchanged.

Use [the Claude resume prompt](CLAUDE_0.1.1_PHASE_B_RESUME_2026-10-31.md).
