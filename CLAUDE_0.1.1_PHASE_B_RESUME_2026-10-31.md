# Claude: resume NARO 0.1.1 qualification — 2026-10-31

Work in `/home/john/Code/naro`. Resume the full Phase B qualification after an
independent input/readiness check. Codex repaired T1–T6 and the remaining CLI-help
identity wording. The final candidate source is **eb9ae23a128d291a47af0ab463f322b5a36c6fd1**.
Nothing in this assignment authorizes a tag, upload, publication, editor change,
reference-baseline rewrite or acceptance-policy change.

## Read first

1. `NARO_0.1.1_TOOLING_HANDOFF_2026-10-31.md` and `docs/RELEASE_GATE_V2.md`.
2. The original report/blockers in
   `target/naro-test-runs/claude-0.1.1-step4-2026-10-31-attempt01/`.
3. Final build/fixture/readiness receipts under
   `target/qualification-tooling-0.1.1-2026-10-31/work/`.
4. The actual frozen launchers and gate code. Use the frozen tools, rather than
   working-tree versions or `tests/follow-up/environment.sh`.

Authoritative freeze: `/home/john/Code/naro/target/qualification-tooling-0.1.1-2026-10-31/work/freeze-attempt03`.

| Identity | SHA-256 / commit |
|---|---|
| Source commit | `eb9ae23a128d291a47af0ab463f322b5a36c6fd1` |
| Production | `63936243e73d0a3fb536d3c0a0fb0e6fe57be09da5f5bc0387ee10250b3d7093` |
| Verification tools | `2e0d1804f37816018425c8e84c8d0b743ac16b75a5d6c46f98b7403d2de83a2d` |
| Host NARO | `9c118168ff0903f9b7de8606ced7fcbe5aa48386fff17f76a7b31e960f0871cc` |
| Ubuntu NARO | `2d3f20f2ab4ed66b9b04a6d47bda8b6e3b5c79664150074a423fa792905d5dba` |
| Host nano | `b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2` |
| Ubuntu nano | `6540492f810998a20a4dba4ac8048cd8b76d37a39e642f14f9f9c3d30c621ba7` |
| Isolated-root nano | `fe02ea07dc9a1e0afa009ef97dc034728995e39c65b75455985b0cf980fa3def` |
| Freeze manifest | `95945d92088c1f34f38eea03f26900e63dbb33586a4e492e34b7c25db574acd6` |

Both NARO candidates are default-feature 0.1.1 builds with no test-hooks. The
Ubuntu candidate remains the intended portable Linux download after qualification.
The pinned GNU source commit is `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.
The frozen Ubuntu image ID is
`093817959dc26bb88c4f8df915372db75dee73f9356eb94f2ba428ea04fe9735`.
All other source/tree/toolchain/image hashes are in `freeze.json` and its inputs.
Old 0.1.1 candidates/freezes, including attempts 01/02, are superseded.

## Independent entry check

- Verify the freeze, manifest SHA, source commit/tree, complete inventories,
  production and verification fingerprints, binary build-info and empty features.
  Repeat freeze verification at the end. Do not rebuild a default candidate.
- Reopen the focused host and Ubuntu readiness evidence independently. Each has
  CLI 5/5, 21 title-layout cases/105 assertions, the original paired/corpus blocker
  proofs, actual seeded history restoration, forged-evidence rejection and
  unchanged frozen inputs. These are readiness checks, not the full matrix.
- Check exact-source CI run `41235061226` directly and preserve its final result;
  CI checks do not substitute for nano parity. Earlier run `41232082842` failed
  the obsolete namespace test; the stricter reviewed-record test is now fixed.
- Confirm no competing host matrix/editor process owns the same corpus fixtures.
  Both launchers deliberately use `/tmp/nanospec-work` because historical fixtures
  embed that literal path. A private alternate root can silently skip history
  restoration. The gate now requires FEAT-015 cursor `(1,11)` on row `l40`.
  Ubuntu's `/tmp` is isolated inside its own container.
- Preserve a fresh attempt directory. Keep every command's argv, start/end,
  stdout/stderr and actual exit; journal progress after each stage. Never delete
  failed attempts, relabel raw differences as exact matches or rewrite old reports.

If any entry check fails, stop the dependent work, preserve the minimal evidence
and report the exact tooling/editor distinction. Do not weaken a check to proceed.

## Full host and Ubuntu matrix

Use a new attempt path; if it exists choose the next numbered attempt. The
launchers require new child output directories. Default candidates/source are
inputs; source checks and optional feature builds use private workspaces.

```sh
export NARO_FREEZE="/home/john/Code/naro/target/qualification-tooling-0.1.1-2026-10-31/work/freeze-attempt03"
export NARO_ATTEMPT="/home/john/Code/naro/target/naro-test-runs/claude-0.1.1-phaseB-2026-10-31-attempt01"
export PYTHONDONTWRITEBYTECODE=1
mkdir "$NARO_ATTEMPT"
python3 "$NARO_FREEZE/verify-freeze.py"
```

Host:

```sh
python3 "$NARO_FREEZE/source/tools/run_closure_host.py" \
  --source-dir "$NARO_FREEZE/source" \
  --binary "$NARO_FREEZE/host/naro" \
  --reference "$NARO_FREEZE/references/host/nano" \
  --root-reference "$NARO_FREEZE/references/host-root/nano" \
  --freeze-manifest "$NARO_FREEZE/freeze.json" \
  --out "$NARO_ATTEMPT/host" --jobs 4 --timeout 3600
```

Ubuntu, using its own frozen reference/install and pinned offline image:

```sh
python3 "$NARO_FREEZE/source/tools/run_closure_ubuntu.py" \
  --source-dir "$NARO_FREEZE/source" \
  --binary "$NARO_FREEZE/ubuntu/naro" \
  --reference "$NARO_FREEZE/ubuntu/reference.bin" \
  --reference-install "$NARO_FREEZE/ubuntu/reference-install" \
  --root-reference "$NARO_FREEZE/references/host-root/nano" \
  --freeze-manifest "$NARO_FREEZE/freeze.json" \
  --out "$NARO_ATTEMPT/ubuntu" --timeout 43200
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

- `/tmp/nv011-final03/nanospec-work/TEST-VT-VM-011-HOST/fx`
- `/tmp/nv011-final03/nanospec-work/TEST-VT-VM-011-UBUNTU/fx`

Complete preserved copy:
`/home/john/Code/naro/target/qualification-tooling-0.1.1-2026-10-31/work/vm-fixtures-preserved-final03`.
Receipt: `/home/john/Code/naro/target/qualification-tooling-0.1.1-2026-10-31/work/FINAL03-FIXTURE-RECEIPT.json`.
If `/tmp` was cleared, restore verified copies into a new short `/tmp/nv*` root
and record the relocation without changing the original receipt. Verify kernel,
initrd, controller, reference and candidate hashes before boot. Kernel SHA is
`664cd32dbd6c33272724208a393c3bf86a7b193ccddc1af24c3408976b5e2aaa`;
runtime export SHA is
`8740ac786051cc2d2985aa9c1b2f372896fc91a815fcde5f8ba0dcaff2563f39`.
Both guests use Ubuntu's nano reference, even for the host-built NARO candidate.

Use frozen `tools/run_console_vm.py` and `tools/check_console_vm.py`, with
`NANOSPEC_WORK` set to the actual short fixture harness root, not the corpus root.
Boot each private guest, wait for actual control/RPC readiness, then run all
**19** fixed cases into separate `$NARO_ATTEMPT/vm-host` and `vm-ubuntu` outputs.
A `TERM=linux` PTY or host console is not equivalent evidence. Do not attach host
disks/network or substitute old guest observations.

Run frozen `tools/check_console_transport.py` for all six checks on an owned
guest, supplying the corresponding exact frozen candidate and
`--out "$NARO_ATTEMPT/transport"`. Independently assert `before_sha256` and
`installed.sha256` match that candidate; six boolean checks alone are insufficient.
Preserve installed/uploaded identities and do not disturb unrelated containers.

For each console output, join actual `vm-run.json`, prepared `inputs.json`,
fixture/runtime receipts and checker exit into `vm-provenance.json`. Include:
source commit, actual QEMU/kernel/initrd/controller identity, runtime export hash,
`inputs`, `tested_candidate_sha256`, `guest_reference_sha256`, actual
`checker_exit`, and `candidate_upload` (null when testing the embedded executable).
Preserve raw captures, key sequences, nonroot app/VT probes and restored modes.
Reopen with frozen `validate_console_evidence`; require 19 accepted, 0 unexpected.
Request shutdown through the existing **guest** RPC and record QEMU's real exit;
expected control EOF is acceptable only when the requested guest exits cleanly.
Keep all VM logs/provenance and clean only owned processes/sockets.

## Closure and delivery

The matrix launchers create and validate fresh package/source archives from the
frozen production source; Ubuntu packaging uses a separate clean source copy.
Identify the exact Ubuntu downloadable archive and source archive, their hashes,
embedded binary hash and offline build proof. Preserve package and asset evidence.

Run the complete v2 collector using actual fresh outputs:

```sh
python3 "$NARO_FREEZE/source/tools/collect_closure.py" \
  --host "$NARO_ATTEMPT/host" --ubuntu "$NARO_ATTEMPT/ubuntu" \
  --vm-host "$NARO_ATTEMPT/vm-host" --vm-ubuntu "$NARO_ATTEMPT/vm-ubuntu" \
  --transport "$NARO_ATTEMPT/transport" \
  --package "$NARO_ATTEMPT/ubuntu/package" \
  --package-check "$NARO_ATTEMPT/ubuntu/package-check" \
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
