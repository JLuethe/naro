# Step 6 genuine console qualification — 2026-10-30

Both unchanged frozen candidates pass 19/19 cases. All six private VM transport
checks pass. See [results](../../NARO_STEP6_RESULTS_2026-10-30.md),
[identity receipt](receipt.json), [statuses](statuses.json),
[host report](host-report.json), [Ubuntu report](ubuntu-report.json),
[host provenance](host-vm-provenance.json), [Ubuntu provenance](ubuntu-vm-provenance.json),
[transport](transport.json), and [verified backup](backup.json).

Full recordings and inputs: `target/step6-console-2026-10-30/`.
The checksum manifest is pinned by receipt.json. Backup outside the repository:
`/home/john/Backups/naro/2026-10-30-step6/step6-console.tar.gz`.
All 10,780 regular/archive-linked files and archived symlink targets were checked
against the originals. This is a same-disk backup, not off-machine protection.
The raw PROGRESS.md was finalized before archiving; its backup-next instruction
is superseded by this receipt. The archive and raw manifest were not rewritten.

The host binary was booted in the initial initramfs; the Ubuntu candidate was
then uploaded via verified chunked transport. The Ubuntu provenance includes
that upload receipt, so the initial embedded host binary is not misidentified
as the executable used by the Ubuntu suite. Both ran against the Ubuntu-built
pinned nano in the recorded guest. Kernel/initramfs/controller/image identities,
keymap and VT observations are retained.

The setup permissions failure is preserved in ATTEMPTS.md. No editor mismatch,
behavioral rerun, production change, or normalization change occurred.
Final package/closure and publication gates remain separate.
