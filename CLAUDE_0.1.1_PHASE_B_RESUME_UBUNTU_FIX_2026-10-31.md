# Claude: finish qualification after Ubuntu tooling fixes — 2026-10-31

Work in `/home/john/Code/naro`. Independently review the final frozen inputs,
complete Ubuntu evidence and focused host readiness, then finish qualification.
This supersedes all earlier 0.1.1 resume/attempt02 prompts. Do not restart the old
attempt02 or use its binary hashes. No publication, tag, upload, editor/source
change, expectation change or commit is authorized by this qualification task.

## Start here

Read `NARO_0.1.1_UBUNTU_LAUNCHER_HANDOFF_2026-10-31.md`,
`NARO_0.1.1_UBUNTU_LAUNCHER_REPAIR_2026-10-31.md`,
`docs/NARO_IDENTITY_POLICY.md` and `docs/RELEASE_GATE_V2.md`.
Use frozen tools from the exact source below, not working-tree scripts or the
rebuilding `tests/follow-up/environment.sh`. Working HEAD may be a later docs-only
commit; frozen source is authoritative. Record git state without resetting work.

Authoritative freeze: `/home/john/Code/naro/target/ubuntu-launcher-repair-0.1.1-2026-10-31/freeze-attempt04`.

| Identity | Commit / SHA-256 |
|---|---|
| Source commit | `accc766af9ff7e36ec206dea697410e3f8f31674` |
| Source tree | `ba92e90e9c2e2c0dcaa59389334da26e013130a9` |
| Production | `63936243e73d0a3fb536d3c0a0fb0e6fe57be09da5f5bc0387ee10250b3d7093` |
| Verification | `4563417b7c8039cce9ac6a687eeced081304f19a00ff8f8f5a78526b7b1a2b83` |
| Host NARO | `ab37d9fa240297a5390da858757909e9c3996314ec59cba4545c5b096b29c647` |
| Ubuntu NARO | `70ab6932323a6b679e628bdb6cfddead8a6ff50160d741782ae8649664dc5a00` |
| Host nano | `b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2` |
| Ubuntu nano | `6540492f810998a20a4dba4ac8048cd8b76d37a39e642f14f9f9c3d30c621ba7` |
| Freeze manifest | `70cab79381ab59a07dbd7a62d7bda5072c1c5127591c1d7463f280ab74e7efbb` |

Both candidates are default-feature 0.1.1 builds, no test hooks. Nano source is
`6ed285c3ec7a1d228def4d4e7021c6ba269f620c`. Image and toolchain identities are in
`freeze.json`. Exact-source CI run `41261807521` succeeded; preserve/recheck it.
The production fingerprint is unchanged. New binaries nevertheless have new
provenance identities and require qualification of these exact hashes.

## What has and has not run

- Original Claude attempt02: old host 46/46 passed; Ubuntu 25/32 receipts, CLI and
  cleanup failed, outer 125. Preserved unchanged and backed up outside target.
- Intermediate Codex diagnostic run on fa2739b: all 32 receipts,31 zero and
  package-check1. It exposed the additional package prerequisites. Preserved as
  diagnostic evidence; it does not qualify the final source or binary hashes.
- Final tools: 151 tests pass. Final host focused readiness: 12 commands exit 0,
  CLI 38, environments 13 (3 raw/10 identity/0 unexpected), title layout 21/105,
  original EOF blocker pair 20 assertions per side, Smoke/Edit, FEAT-015 and
  corruption controls. This is not the full host matrix.
- Final Ubuntu matrix: all 32 receipts and launcher exit 0, package 15/15 and native
  assets44/44. Fresh own-Nano 303 observations and candidate comparisons, historical
  suites and all 151 new regressions ran. Codex independently reopened raw evidence
  with frozen tools; see `UBUNTU-INDEPENDENT-REOPEN.json` in the work root.
- Full host matrix for the final host hash, both 19-case genuine guest-VT groups,
  transport 6 and complete closure/gate are still NOT RUN.

Work root: `/home/john/Code/naro/target/ubuntu-launcher-repair-0.1.1-2026-10-31`.
Final Ubuntu evidence: `/home/john/Code/naro/target/ubuntu-launcher-repair-0.1.1-2026-10-31/ubuntu-full-attempt02`.
Final host focused evidence: `/home/john/Code/naro/target/ubuntu-launcher-repair-0.1.1-2026-10-31/final-readiness-host-v2/`.
Full input/evidence backup and hashes are in the handoff and tracked receipts.

## Provisioning fixes to inspect

The historical syntax include path is provided as a read-only mount of the exact
44 frozen bundled files. CLI scenarios, original GNU output and acceptance policy
were not rewritten. Inspect launch/runtime syntax inventories and actual ro mount.
The shared cleanup helper distinguishes confirmed dead private sockets from real
errors, retains actual client/probe statuses and fails on unknown errors/timeouts
or unresolved sockets. A raw tmux client exit1 saying no server is not the cleanup
stage exit: the separate cleanup result must prove removal and success.

The launcher retains exact root `naro` and `reference.bin` copies with a
`frozen-executables.json` receipt; verify against freeze, runtime and suite copies.
It pins Cargo to `/opt/rust/bin/cargo` for offline source rebuilds and uses the
provided de_DE.UTF-8 locale for the exact German symlink probe. Expect `Hilfe`,
not a skipped assertion. The four scenario locales remain unchanged: the French
request falling back to C is still covered. No broader normalization is permitted.

## Independent entry and reuse check

Verify the manifest hash, freeze inventories, source/tree/production/verification,
all executable hashes/build-info and empty default features. Repeat at the end.
Independently reopen the final host/Ubuntu readiness and corruption-control
records, actual stage statuses, raw inputs/outputs/assertions, scenario membership,
identity/deviation classifications, installed assets and exact package contents.
Use the frozen checker, not the summary booleans. The provided Codex reopening
script is an audit aid; review its coverage and recompute results yourself.

Reuse the final complete Ubuntu result only after this independent verification.
Do not rerun successful matching evidence merely to replace the actor's name.
If a concrete evidence gap requires another Ubuntu run, record why, preserve the
existing output, use a new output directory and the frozen explicit-input Ubuntu
launcher. Do not mix reports or hashes. Any unexplained failure blocks dependent
work and goes to Codex with a minimal reproduction; do not edit frozen inputs.

## New host attempt and execution order

Choose a fresh directory, preferably
`target/naro-test-runs/claude-0.1.1-phaseB-2026-10-31-attempt03/`. If it already
exists, inspect ownership and progress before acting; resume a valid existing run
instead of duplicating it. Preserve unrelated/failed attempts and use a new number
when needed. Keep argv, times, stdout/stderr and actual exits. A vanished PID or
last successful log line is not a final exit receipt. Do not fabricate lost status.

```sh
export NARO_FREEZE="/home/john/Code/naro/target/ubuntu-launcher-repair-0.1.1-2026-10-31/freeze-attempt04"
export NARO_ATTEMPT="/home/john/Code/naro/target/naro-test-runs/claude-0.1.1-phaseB-2026-10-31-attempt03"
export NARO_UBUNTU_EVIDENCE="/home/john/Code/naro/target/ubuntu-launcher-repair-0.1.1-2026-10-31/ubuntu-full-attempt02"
export PYTHONDONTWRITEBYTECODE=1
```

Create the attempt only if absent and confirmed appropriate. Check no competing
host matrix owns canonical `/tmp/nanospec-work`; Ubuntu's root is container-private.
Run the full host matrix with the final candidate, then any justified Ubuntu
rerun, then the two guest groups, transport and closure, one group at a time.

```sh
python3 "$NARO_FREEZE/verify-freeze.py"
python3 "$NARO_FREEZE/source/tools/run_closure_host.py"   --source-dir "$NARO_FREEZE/source" --binary "$NARO_FREEZE/host/naro"   --reference "$NARO_FREEZE/references/host/nano"   --root-reference "$NARO_FREEZE/references/host-root/nano"   --freeze-manifest "$NARO_FREEZE/freeze.json"   --out "$NARO_ATTEMPT/host" --jobs 4 --timeout 3600
```

Verify actual execution and inventories, not just exit 0:

- Fresh nano observations in **each** environment; 303 terminal records plus the
  six fixed exclusions. Original GNU observations remain untouched.
- CLI 38, regex 162, safety 2; historical follow-ups 53; ioctl models 8.
- Six regression suites: wrap-undo 58, filter 6, release-fixes 15, step3-gaps 40,
  save-progress 22 and save-safety 10 (151 per environment). Reopen every raw
  trace, input, step, assertion, scenario and executable binding.
- CLI branding 5 and title layout 21/105 in both environments; default Rust and
  candidate-policy tests; host quality/unit stages.
- File-write failure/backup/recovery/signal/restoration behavior, panic variants,
  1 MiB/10 MiB files, installed assets, all 41 catalogs, syntax and package checks.
- Host isolated root/home 27 plus the separately asserted no-home case.
- Optional hooks/credits executables remain separate, feature- and hash-recorded.
- Every required host command and all **32** Ubuntu `.status` receipts must exist
  and be exactly zero. Only the existing private Ubuntu `locpath` adaptation is
  permitted. Check source/verification/default binary identities after the runs.

Report raw exact, identity-reviewed, declared-deviation and unexpected counts
separately. Retain only the reviewed policies for CLI-057, PROMPT-NUL-001, the two
Q-TOOL-001 signal cases and Q-ROOT-NOHOME-001. Complete residual signatures now bind
those exceptions; any added difference blocks qualification. Do not force the
old 301/302 or 51/53 raw-match totals onto the new identity-aware reports.

## Genuine guest VT and transport

Fresh prepared fixtures (never booted during Codex readiness):

- `/tmp/nv011-uf04/nanospec-work/TEST-VT-VM-011-HOST/fx`
- `/tmp/nv011-uf04/nanospec-work/TEST-VT-VM-011-UBUNTU/fx`

Complete preserved copy:
`/home/john/Code/naro/target/ubuntu-launcher-repair-0.1.1-2026-10-31/final-vm-fixtures-v2/nanospec-work`.
Receipt: `/home/john/Code/naro/target/ubuntu-launcher-repair-0.1.1-2026-10-31/final-vm-fixtures-v2/fixture-report.json`.
If `/tmp` was cleared, restore verified copies into a new short `/tmp/nv*` root
and record the relocation without changing the original receipt. Verify kernel,
initrd, controller, reference and candidate hashes before boot. Kernel SHA is
`664cd32dbd6c33272724208a393c3bf86a7b193ccddc1af24c3408976b5e2aaa`;
runtime export SHA is
`8740ac786051cc2d2985aa9c1b2f372896fc91a815fcde5f8ba0dcaff2563f39`.
Both guests use Ubuntu's nano reference, even for the host-built NARO candidate.

Use frozen `tools/run_console_vm.py` and `tools/check_console_vm.py`, with
`NANOSPEC_WORK` set to the actual short fixture harness root, not the corpus root.
The VM launcher blocks until QEMU exits. Start each launcher as an owned
background/session process, retain its PID and logs, wait for actual control/RPC
readiness, then run all
**19** fixed cases into separate `$NARO_ATTEMPT/vm-host` and `vm-ubuntu` outputs.
A `TERM=linux` PTY or host console is not equivalent evidence. Do not attach host
disks/network or substitute old guest observations.

Keep the final Ubuntu guest alive after its 19 comparisons for transport, then
request shutdown and record the launcher exit. Run frozen `tools/check_console_transport.py` for all six checks on an owned
guest, supplying the corresponding exact frozen candidate and
`--out "$NARO_ATTEMPT/transport"`. Independently assert `before_sha256` and
`installed.sha256` match that candidate; six boolean checks alone are insufficient.
Preserve installed/uploaded identities and do not disturb unrelated containers.

For each console output, join actual `vm-run.json`, prepared `inputs.json`,
fixture/runtime receipts and checker exit into `vm-provenance.json`. Include:
source commit, actual QEMU/kernel/initrd/controller identity, runtime export hash,
`inputs`, `tested_candidate_sha256`, `guest_reference_sha256`, actual
`checker_exit`, and `candidate_upload` (null when testing the embedded executable).
Normalize the provenance `inputs` map explicitly: keep `vmlinuz` and
`initrd.cpio.gz`; map raw `reference.bin` to exactly one `nano` key; map raw
`naro` to exactly one `naro-host` or `naro-ubuntu` key for the relevant guest.
Retain the original fixture map separately. Duplicate aliases or copying the raw
`reference.bin` key directly into the joined map will fail the identity checker.
Preserve raw captures, key sequences, nonroot app/VT probes and restored modes.
Reopen with frozen `validate_console_evidence`; require 19 accepted, 0 unexpected.
Request shutdown through the existing **guest** RPC and record QEMU's real exit;
expected control EOF is acceptable only when the requested guest exits cleanly.
After requested shutdown, wait/reap the owned launcher and preserve its real
exit status externally: `vm-run.json` does not record QEMU's eventual exit code.
Keep all VM logs/provenance and clean only owned processes/sockets.

## Closure and delivery

The existing final Ubuntu output already contains validated package/source archives from the
frozen production source; Ubuntu packaging uses a separate clean source copy.
Identify the exact Ubuntu downloadable archive and source archive, their hashes,
embedded binary hash and offline build proof. Preserve package and asset evidence.

Run the complete v2 collector using actual fresh outputs:

```sh
python3 "$NARO_FREEZE/source/tools/collect_closure.py" \
  --host "$NARO_ATTEMPT/host" --ubuntu "$NARO_UBUNTU_EVIDENCE" \
  --vm-host "$NARO_ATTEMPT/vm-host" --vm-ubuntu "$NARO_ATTEMPT/vm-ubuntu" \
  --transport "$NARO_ATTEMPT/transport" \
  --package "$NARO_UBUNTU_EVIDENCE/package" \
  --package-check "$NARO_UBUNTU_EVIDENCE/package-check" \
  --out "$NARO_ATTEMPT/closure"
python3 "$NARO_FREEZE/source/tools/check_release_gate.py" \
  --reports "$NARO_ATTEMPT/closure" --out "$NARO_ATTEMPT/final/RELEASE-GATE.json"
python3 "$NARO_FREEZE/verify-freeze.py"
```

Investigate every failed/missing check. Do not edit frozen source, scripts,
policies or expectations; report a minimal reproduction to Codex if blocked.
Do not mix earlier candidate/evidence hashes into this attempt. Preserve a final
SHA-256 manifest with exact membership, verify it, and back up the complete new
attempt outside `target/` before reporting completion.

Deliver `CLAUDE_0.1.1_PHASE_B_REPORT.md`, `PROGRESS.md`, `ATTEMPTS.md`, a result
inventory, command records, final evidence manifest and passing recomputed gate.
State completed/deferred/not-run checks and known differences precisely. Report
unchanged frozen inputs, git state, cleanup and archive locations. No editor
change, commit, tag, upload, publication or community announcement is authorized.

The final backup must preserve both this new attempt and the verified reused
Ubuntu evidence/freeze archive. Keep reused raw evidence in place; avoid moving
or copying it casually across recorded absolute paths. Record all evidence roots
and archive hashes in the result inventory. Nothing is published by this task.
