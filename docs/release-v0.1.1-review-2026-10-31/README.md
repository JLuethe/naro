# NARO 0.1.1 — final publication review, October 31, 2026

**Technical qualification passes. Publication awaits John’s approval.**
Nothing has been tagged, uploaded or published for 0.1.1. The existing 0.1.0
release is unchanged. No further editor testing is required for this exact candidate.

Review [the release body](RELEASE_BODY.md), [the publication plan](PUBLICATION_PLAN.md)
and [the seven exact assets](asset-manifest.json). Proposed annotated tag:
`v0.1.1` at `a6078aed705bc0b605ad7603505767ce2b9bc206`.
The proposed GitHub release is an **experimental prerelease**, not stable/latest.
John Luethe and OpenAI’s generous support are acknowledged in the release body.

## Verified result

- Fresh host matrix: 46 stages passed. Reused Ubuntu matrix: all 32 receipts zero;
  its raw evidence was reopened by the frozen collector and gate.
- Actual Linux VT1 guests: 19 accepted cases per candidate; transport: six passed.
- Final package collector: 69/69 checks. Independent gate: pass, no problems,
  zero unexpected differences across 38 accounting sets.
- Fresh freeze checks passed before/after independent review and after repackaging.
  Claude’s seven accidental bytecode caches were archived and removed; the original
  failed check is retained. The recomputed gates match.
- CI on the exact proposed tag commit [succeeded](https://github.com/JLuethe/naro/actions/runs/41273433760).

## Exact downloadable files

The earlier archives bundled 0.1.0 documentation. Documentation was refreshed and
archives repackaged with the **same qualified Ubuntu executable**; no editor rebuild
was performed. The source archive matches all 1,561 tracked files and modes at the
proposed tag. Production and verification fingerprints match frozen `accc766`.
The later review-delivery commit is deliberately not the tag target.

The selected archives passed package 15/15, including offline source rebuilding,
malformed-archive rejection and safe uninstall; all 41 catalogs and 44 asset checks
passed. An additional fully logged ordinary-prefix check passed 5/5. The complete
collector and gate were rerun against these new archive bytes and passed.

| File | SHA-256 |
| --- | --- |
| Binary archive | `4591ab90274d6251a19f8291d49d15bf23296e1b4c15482b65dc169478d98e50` |
| Source archive | `122a18bea8942fe88a68e0ac4761d58d195d89af893263a3703f5a13fb46fc16` |
| Embedded executable | `70ab6932323a6b679e628bdb6cfddead8a6ff50160d741782ae8649664dc5a00` |

Working downloads are in `target/codex-0.1.1-final-review-2026-10-31/downloads/`.
Verified copies and the review evidence archive are preserved outside target at
`/home/john/Backups/naro/2026-10-31-release-0.1.1/`; see BACKUP.json and
ASSET-BACKUP.json beside this packet. Backups are on the same filesystem,
not off-device. Original Claude evidence and frozen Ubuntu evidence have their
own separately verified backups.

## Approval and remaining work

Approve the exact target, release body, prerelease setting and seven files in
asset-manifest.json. After approval: recheck remote refs/CI/hashes, create the
annotated tag and GitHub prerelease, then anonymously download and verify every
published asset. Record public URLs and asset IDs. Announcements need separate
authorization. Known differences, scope limits and nine unresolved audit citations
remain disclosed in RELEASE_BODY.md and COVERAGE_REVIEW.md.

See [technical receipts](../../validation/release-0.1.1-final-2026-10-31/README.md).
