# Ubuntu launcher repair receipts — 2026-10-31

Start with [the completion handoff](../../NARO_0.1.1_UBUNTU_LAUNCHER_HANDOFF_2026-10-31.md)
and [the new Claude prompt](../../CLAUDE_0.1.1_PHASE_B_RESUME_UBUNTU_FIX_2026-10-31.md).

These are verified final-input, focused host and complete Ubuntu receipts for
source accc766. They do not certify the full host matrix, guest VT, transport or
final release gate. Claude must independently reopen the retained evidence before
reuse, complete those remaining stages and preserve all outputs.

CI passed for the exact frozen source; 151 affected tooling tests passed.
The final Ubuntu launcher and all 32 required stages exited 0; strict raw evidence
reopening passed, packages 15/15 and native assets 44/44, including all 41 catalogs.
Guest fixtures are prepared, not booted. No publication was performed.

BACKUP.json identifies the final verified archive outside target. The archive
contains the full freeze, all raw evidence, failed/diagnostic attempts and prepared
fixtures. EVIDENCE-SHA256SUMS hashes this small tracked receipt set. Both final
and original-attempt backups reside on the same filesystem, not off-device.
