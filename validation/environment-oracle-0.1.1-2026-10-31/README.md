# Environment oracle repair receipts — 2026-10-31

These receipts describe tooling repair, replacement candidate builds and focused
readiness. They do not certify full Phase B or authorize publication.

Start with [the handoff](../../NARO_0.1.1_ENVIRONMENT_HANDOFF_2026-10-31.md) and
[the exact-hash Claude prompt](../../CLAUDE_0.1.1_PHASE_B_RESUME_ENVIRONMENT_FIX_2026-10-31.md).

`FROZEN-IDENTITIES.json` binds the complete source/tool freeze and rebuilt
candidates. CI passed for that exact source commit. All 146 final tooling tests,
fresh host/Ubuntu environments, bounded identity/blocker proofs and independent
artifact checks passed. Guest fixtures are prepared but unbooted. Full host and
Ubuntu matrices, both 19-case guest-VT runs, transport, final package evidence and
closure gate remain Claude's work.

`BACKUP.json` records the verified complete replacement-freeze/evidence archive
outside target. `EVIDENCE-SHA256SUMS` hashes this small tracked receipt set. The
complete raw evidence remains under the work/backup locations named in the
handoff. Both backups are on this filesystem; neither is an off-device copy.
