Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

# 21 — Console qualification and final preview delivery

For the next 0.1.0 release, use [the release checklist](../RELEASE_CHECKLIST.md).
The completion status and evidence below describe the historical qualification.
The updated host/Ubuntu runners and collector additionally require 58 wrap-undo,
6 filter, 15 release-fixes, and 40 step3-gaps exact comparisons on each final executable,
including reopened artifact validation. These 119 cases are separate from the
historical 53-case totals. Fresh final-binary qualification remains pending.

Status: complete for the scoped preview: implementation, 85-check qualification
and evidence delivery are verified in the closure matrix. The checkpoint
before this specification is `62fca5b`. This document completes the remaining
work described in [the wrap-up plan](../WRAP-UP.md). It supplements docs 19–20;
their historical evidence stays attached to the binaries actually tested.

### CLOSE-TRANSPORT-001 — Reliable private VM transport

The VM runs only in a canonical harness fixture with no host disk, network or
active host console attached. Its controller requires PID 1 and the disposable
root marker. Upload only the two named reference/candidate binaries, while no
editor runs. Bound file size to 64 MiB and each decoded chunk to 64 KiB. Start
an upload with length and SHA-256, require sequential byte offsets, verify both
at completion and atomically replace the executable only after validation.
Disconnects discard incomplete request bytes and abandon the pending upload.
Reject malformed, oversized, out-of-order and hash-mismatched transfers without
changing the installed executable. No fallback may open host console devices.

Acceptance: TEST-CLOSE-TRANSPORT-001 exercises successful multi-chunk upload,
wrong size/hash/offset, abandoned transfer, reconnect and unchanged installed
binary on failure. Boundary unit tests run in CI; VM observations remain distinct.

### CLOSE-CONSOLE-002 — Qualify the actual guest console

Run all 19 cases in tools/check_console_vm.py on the same optimized candidate
and pinned GNU reference: navigation, modifiers, selection/deletion, tabs,
multibuffer keys, Unicode, rc expansion, cancellation, missing tool, macros,
help, modern bindings and handled HUP/TERM. Read actual guest VT identity and
modifier state; inject keys only through the VM's emulated PS/2 keyboard.
Compare cells, nonblank attributes, cursor, file bytes/modes and exits under
doc 16 normalization. Assert terminal, keyboard and meta modes restore after
exit. Require explicit macro-recording and resulting-cursor assertions.

Acceptance: TEST-CLOSE-CONSOLE-001 is 19/19 matches, with source/candidate hashes,
kernel, keymap and controller provenance. Earlier partial runs do not satisfy
it. Record the final Ubuntu binary separately using the same full suite. This
certifies the recorded guest kernel/userspace/keymap, not physical hardware.

### CLOSE-MODEL-003 — Check modifier branch behavior

Keep the eight fixture-controlled ioctl scenarios separate from genuine VT
observations. Cover non-VT, query failure, Shift, Ctrl, Ctrl+Shift, Alt,
Alt+Shift and macro replay. Input timing must actually activate source recording.
No production environment variable may impersonate a console.

Acceptance: TEST-CLOSE-MODEL-001 has eight exact paired matches and passing
source/candidate assertions; CI runs candidate assertions and boundary checks.

### CLOSE-REGRESS-004 — Freeze source and validate both builds

Commit production code and record its source-input fingerprint before release
validation. Run formatting, strict all-feature Clippy, Rust and Python harness
tests. Build host and Ubuntu candidates from those same source inputs. For each,
run the 303 safe terminal cases, CLI 38, regex 162, 53 follow-up comparisons,
safety, recovery and relevant assets/performance checks. On the host rerun 27
root/home cases plus the separate no-home recovery assertion using the recorded
root oracle and namespace isolation. Root behavior is not inferred from an
ordinary Ubuntu container. Use one frozen executable per report and new output
directories; preserve original evidence and earlier failures.

Acceptance: TEST-CLOSE-REGRESS-001 retains 301 full / 302 file-exit matches in
the 303-case corpus, all CLI/regex assertions, 51 exact plus two declared cleanup
differences in the 53-case suite, 27 root matches and the named no-home deviation.
No new unexplained mismatch is accepted. Each report must identify inputs.

### CLOSE-PACKAGE-005 — Deliver exactly the tested executable

Package the final Ubuntu default-feature executable, matching source archive,
checksums, license/credits and runtime assets. Capture linked library and symbol
requirements in the build environment. Test private-prefix installation, prefix
spaces, symlink launching, all 41 catalogs, installed syntax, offline source
rebuild, invalid archive rejection and uninstall ownership/conflicts. Never
overwrite historical archives. Do not include test hooks in the release binary.

Acceptance: TEST-CLOSE-PACKAGE-001 passes the existing package checker, with the
archive binary equal to the console/regression-tested Ubuntu SHA-256 and source
fingerprint equal to the frozen checkout. GitHub source push and GitHub Release
publication are distinct; this phase pushes source/evidence, without a new tag
or hosted Release unless separately requested.

### CLOSE-EVIDENCE-006 — Make completion auditable

Add compact tracked reports for final console, Ubuntu, regression and packaging
outcomes, including binary hashes and reproducible commands. Update README,
IMPLEMENTATION, spec coverage, open questions, data README and progress. Mirror
finalized spec and relevant reports to ~/src/nano-rs without deleting unrelated
files. Audit requirement/matrix links and reference identity. Push final commits
and check remote HEAD and CI. CI's scope must not be described as the entire
local qualification suite.

Acceptance: TEST-CLOSE-EVIDENCE-001 has a passing audit and final gate, remote
HEAD at the delivered revision, successful CI and a clean tracked worktree.
Tiny mode and physical-operator console rows stay deferred. Other source-only
runtime gaps stay visible. The completion report distinguishes these limits.

### CLOSE-CONTINUITY-007 — Persist progress across ordinary interruptions

After each stage, write source revision, binary hashes, report paths, outcomes,
remaining failures, owned running processes and exact next action to disk.
Commit coherent checkpoints and push them. Run commands with bounded lifetime;
do not edit an executing shell script or overlap tests sharing fixture IDs.
The resume instructions must inspect existing state before repeating work.

Acceptance: TEST-CLOSE-CONTINUITY-001 checks a fresh reader can locate the next
incomplete stage and its evidence using only repository files. Do not claim an
automatic restart is configured unless an actual scheduler/runner was installed
and verified. Ordinary build/test jobs can finish independently of chat. An
automated model runner, if added separately, must stop for safety/permission
blocks, authentication failures and unknown errors rather than retrying around
them; it must respect user cancellation and prevent concurrent writers.

## Implementation order and completion boundary

Repair transport and rerun modifier models; commit and build; run complete VM
and host/Ubuntu gates; package and verify; update evidence and push; confirm CI.
Mark matrix rows verified only when linked evidence meets the above criteria.
The current unattended work can continue while this session is active. Persistent
resumption after session termination is a separate capability, not provided by
this spec or by a Markdown checkpoint alone.
