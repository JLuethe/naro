# Step 6 results — 2026-10-30

Status: **passed for both frozen default candidates**. No new editor findings.
The [execution plan](NARO_STEP6_PLAN_2026-10-30.md) is complete. Final packaging,
closure collection, documentation/public claims and publication remain later gates.

| Check | Result |
| --- | --- |
| Host candidate genuine guest-VT | 19/19 exact; checker exit 0 |
| Ubuntu candidate genuine guest-VT | 19/19 exact; checker exit 0 |
| Private VM upload/reconnect transport | 6/6 pass; checker exit 0 |
| Terminal/keyboard/meta restoration | Verified in all 76 paired editor runs |
| Ioctl-model comparisons | Already passed 8/8 per candidate in step 5 |
| Frozen inputs | Verify unchanged after testing |
| Owned processes | VM exited 0; disposable export container removed; none running |

## Exact inputs and scope

Source: `fd91763c4f14d9bed8187d64d44f2136440b7b3e`.
Production fingerprint:
`4cabd71741ffc8ee0357d945c67904c8a2fd0089c12e9b32a1c5b3e35c394ae6`.

- Host candidate: `cae387c78619520aacbf61690e675496b82f8ccf04af2824beb9e864004f0a96`.
- Ubuntu candidate: `33a39eb339492720ec6166e84fea421749e0b2ec3bd612b276c2377f91b7c4a1`.
- Guest nano reference: `6540492f810998a20a4dba4ac8048cd8b76d37a39e642f14f9f9c3d30c621ba7`.

The reference is the independently built Ubuntu nano from pinned upstream
`6ed285c3ec7a1d228def4d4e7021c6ba269f620c`. Both candidates used this same oracle
inside the recorded guest runtime. This is distinct from step 5's native host
oracle and does not relabel host/container observations as guest-VT results.

Runtime: Ubuntu 24.04 exported from image
`093817959dc26bb88c4f8df915372db75dee73f9356eb94f2ba428ea04fe9735`;
guest kernel `7.2.8-9-omarchy`, genuine `/dev/tty1`, QEMU/KVM emulated PS/2
keyboard. The VM had no host disk, network, or active host console attached.
Applications ran as fixture uid/euid 1000 with genuine guest VT descriptors.
The report retains kernel-reported modifier bits and keymap observations.
This qualifies that guest/kernel/runtime combination, not physical keyboards.

## Execution and assertions

The frozen checkout's `prepare_console_vm.py`, `run_console_vm.py`,
`check_console_vm.py`, `check_console_transport.py`, controller, and upload code
were used unchanged. The host candidate booted in the initramfs. After its
19-case run, the existing verified chunked upload installed the exact Ubuntu
candidate; its SHA was checked before the second full run.

Each suite compared cells, nonblank attributes, cursor, file bytes/modes and
exits, with explicit macro/Unicode/navigation assertions. Both sides restored
terminal, keyboard and meta modes. The raw restoration assertions were also
checked for every one of the 76 editor runs. Transport covered incomplete,
out-of-order and bad-digest transfers, disconnect/reconnect, verified installation,
and refusal to upload while an editor was running.

One preparation attempt failed before boot: the helper copies executables twice,
and the frozen 0555 mode prevented reopening its private destination for the
second copy. Only the fixture copies were made owner-writable; preparation then
succeeded with the existing `--reuse` option. The frozen binaries, source, tests,
and normalization were unchanged. Each full behavioral suite and the transport
suite ran once and passed; there were no behavioral retries or waived failures.

## Evidence and continuation

Full local evidence: `target/step6-console-2026-10-30/`.
It includes paired raw captures, reports, commands/statuses, upload receipt,
QEMU logs, kernel/initramfs, runtime export, controller copies, keymap/VT metadata,
and a file checksum manifest. The preparation failure is in `ATTEMPTS.md`.

Compact tracked evidence and hashes:
[validation/step6-console-2026-10-30](validation/step6-console-2026-10-30/README.md).
Step 5's original report, Codex verification, checksum-ledger discrepancy and
backup are recorded [separately](validation/step5-qualification-2026-10-30/README.md).
The old pre-existing container and unrelated processes were left untouched.

Next: step 7. Finalize the exact qualified Ubuntu binary/source package, verify
archive-to-candidate linkage and the complete closure inputs, and retain the
existing installation/source-rebuild evidence where its inputs remain identical.
Do not claim that the final collector, attribution review, public documentation,
or publication gates have passed merely because console qualification passed.
