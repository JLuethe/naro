# Linux console qualification

Reference: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.
Production code and upload tools were frozen at `390a72d`.

Both optimized candidates pass all 19 cases against pinned GNU nano on an actual
guest Linux VT. The host executable SHA-256 is
`283abffeda8ab42a6fe982ba54c355c459c7378632d50f8f132201fd76a2059d`;
the Ubuntu executable is
`eeb8ebb50fd3709aaa004897df3e589364e536a6a1eaf006ae3b8be5f6031541`.
Reports identify the source oracle separately. The VM has Ubuntu runtime
libraries, kernel `7.2.8-9-omarchy`, QEMU/KVM and emulated PS/2 keys. This is
guest console qualification, not a physical keyboard/operator trial.

Cases compare actual cells, visible attributes, cursor, files and exits, with
termios and keyboard/meta-mode restoration assertions. Every app has genuine
guest `/dev/tty1` descriptors and uid 1000. Kernel modifier state is observed
before each modified key. Macros must actually record and produce the expected
cursor; matching two empty macros is not accepted. The implemented fixes cover
modifier translation, console bindings/help, zero-width rendering and the
reference's raw-key macro replay behavior.

The separate ioctl model has eight paired exact matches. Its candidate hash
predates the final metadata rebuild but uses the same production source inputs;
the final host/Ubuntu regression repeats it on the delivered binaries. It models
branches and is not evidence of a physical console. Nine Python boundary/upload
tests pass, and six live transport checks verify interrupted/invalid uploads
preserve the executable, reconnect works, validated chunks install the expected
hash and a running editor rejects replacement.

Raw evidence is preserved under `spec/evidence/follow-up-runs/vt-closure-host-v1`,
`vt-closure-ubuntu-v1`, `vt-transport-closure-v1` and `vt-ioctl-closure-v1`.
Earlier failed attempts remain separate. The bounded VM was shut down after
both full runs; the host active console was never attached or taken over.

Reproduction uses `tools/prepare_console_vm.py`, `tools/run_console_vm.py`,
`tools/check_console_transport.py` and `tools/check_console_vm.py`. Prepare the
image inside a canonical harness `TEST-*/fx` fixture from private Ubuntu runtime
inputs, the pinned source executable and the chosen candidate. Start the bounded
VM, upload and verify the candidate with `console_vm.VM.install`, then run:

```sh
python3 tools/check_console_vm.py --fixture /tmp/nanospec-work/TEST-VT-VM/fx \
  --out spec/evidence/follow-up-runs/new-console-run
```

Retain the runner's `vm-run.json`, image input hashes and controller file hashes
beside the report. Initial image hashes describe the boot image; uploaded
executable hashes in each recorded case identify the binaries actually tested.
Stop the owned VM through its QMP connection when finished. Never substitute a
host tty for the fixture VM. Broader regression/package qualification is tracked
separately under spec 21 and does not follow automatically from these matches.
