# Final frozen Ubuntu readiness — 2026-10-31

**PASS on execution-attempt01.** This is focused readiness, not full release
qualification. No editor build, source edit, commit or publication was performed.

Frozen source: `498fb892d52d95b82b6eadea6f6250ebc5be7ef5`.
Freeze manifest SHA-256: `596829be9e3848a4135ffeda1c3d3dba0c177679b5681209f65e87c3bf7cb61b`.
Ubuntu NARO: `ba4e046d174120733f33eb03fbcd205a34bd08a54a008b4fc3f38e740d8193df`.
Own Ubuntu Nano: `6540492f810998a20a4dba4ac8048cd8b76d37a39e642f14f9f9c3d30c621ba7`.
Production fingerprint: `63936243e73d0a3fb536d3c0a0fb0e6fe57be09da5f5bc0387ee10250b3d7093`.
Verification fingerprint: `68e03dbf57b6ac02aa06734c5e69aea6c36012ac59ec020a2eaea65d52fc8406`.

The pinned image ran offline with the full frozen source and all assets copied
privately to `/work/naro`, including all 41 catalogs. Tests asserted UID/GID 1000,
used own Nano at `/work/reference`, canonical `/tmp/nanospec-work`, and private
container tmux sockets. Only the private copied environments scenario locale
paths changed to `/opt/nano-locales`; frozen source stayed read-only and unchanged.

| Check | Result |
| --- | --- |
| Fresh environments plus generic raw-evidence reopening | 13 accepted: 3 raw exact, 10 identity-reviewed, 0 unexpected |
| CLI identity | 5/5 |
| Title layout | 21 cases, 105/105 assertions |
| Original EOF-LF-LIVE | One pair; 20/20 assertions each; strict evidence reopening passes |
| Independent report forgeries | Integer acceptance and forged identity explanation both rejected |
| Smoke + Edit with two fresh own-Nano references | 2 identity-reviewed, 2 file/exit matches, 0 unexpected; strict raw reopening passes |
| Original FEAT-015 | Both restore x1/y11/visible and row11 `l40`; strict reopening passes |
| Real French selection | Both actually display `Modifié`; strict comparison passes |

All ten test commands, four locale-generation commands, freeze verifications,
image inspections and cleanup stages returned zero. Runtime hashes match before
and after. Freeze input hashes are unchanged, and complete freeze verification
passed before and after. Owned tmux cleanup, container stop and removal all
returned zero. An independent scoped Podman query confirms the container absent.

A second, host-side verification used the same frozen tools to reopen raw files,
recompute assertions/comparisons, check exact suite membership and validate all
statuses and provenance. It passed; see `INDEPENDENT-REOPEN.json`. The execution
manifest contains 215 files and independently verifies with zero mismatches.

`execution-attempt01/` retains argv, times, statuses, raw logs and terminal bytes,
source/asset hashes, locale adaptation, comparisons, negative controls and cleanup
receipts. No earlier failed attempt exists in this final readiness directory.
Prior pre-freeze proofs remain unchanged historical evidence. Full qualification
and release closure are separate coordinator/Claude work.
