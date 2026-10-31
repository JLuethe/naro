# Step 6 — genuine guest-VT qualification

Date: 2026-10-30 (America/Los_Angeles).

Inputs: frozen source fd91763 and the exact default candidates from
[NARO_STEP4_FREEZE_2026-10-30.md](NARO_STEP4_FREEZE_2026-10-30.md).
[Step 5 passed](validation/step5-qualification-2026-10-30/README.md); its evidence
and the full freeze bundle are now backed up outside the repository.

1. Verify freeze and prior evidence; preserve checksum discrepancies explicitly.
2. Export the pinned Ubuntu image to a new private runtime. Prepare a fresh
   harness fixture with the current recorded kernel and frozen controller.
3. Boot a bounded KVM guest with no host disks, network, or host console.
4. Run the 19 established comparisons for the host candidate and the pinned
   Ubuntu-built nano oracle, then separately for the Ubuntu candidate with
   that same guest oracle. Record exact in-guest hashes, kernel, keymap,
   controller files, runtime image, initramfs, QEMU command and version.
5. Require every comparison and semantic assertion to pass: cells, nonblank
   attributes, cursor, saved bytes/modes, exits, real guest VT identity, and
   terminal/keyboard/meta restoration. Preserve failures; no normalization changes.
6. Refresh all six private-VM transport checks with the exact candidate.
   Step 5 already supplied the eight ioctl-model checks per candidate.
7. Shut down only the owned VM; save compact reports and full recordings,
   checksum and back up step 6 evidence, update progress and required gates.

Evidence: `target/step6-console-2026-10-30/`. The established scripts run from
the clean frozen checkout. A new fixture avoids overwriting old sessions.
These tests qualify a genuine guest Linux VT with emulated PS/2 input and the
recorded Ubuntu runtime. They do not certify physical keyboards or a native
host VT. Package finalization and publication are later steps.
