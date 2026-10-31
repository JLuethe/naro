# Claude: resume Phase B after environment oracle repair — 2026-10-31

Work in `/home/john/Code/naro`. Resume the full Phase B qualification after an
independent input/readiness check. This supersedes the earlier Phase B resume prompt. The first Phase B host run
stopped at environments: 21 stages passed, one failed, and 24 later host stages
were not run. Independent GNU title-layout checks show all six failures were
oracle coverage gaps, not editor bugs. The requested French locale actually
fell back to C, and the German/Japanese state labels occupy the correct cells.
Codex repaired the independent title oracle and exact scenario-bound context;
production source is unchanged. Final candidate source: **498fb892d52d95b82b6eadea6f6250ebc5be7ef5**.
Nothing in this assignment authorizes a tag, upload, publication, editor change,
reference-baseline rewrite or acceptance-policy change.

## Read first

1. `NARO_0.1.1_ENVIRONMENT_HANDOFF_2026-10-31.md` and `docs/RELEASE_GATE_V2.md`.
2. The original report/blockers in
   `target/naro-test-runs/claude-0.1.1-step4-2026-10-31-attempt01/`.
3. Final build/fixture/readiness receipts under
   `target/phaseB-environments-repair-2026-10-31/`.
4. The actual frozen launchers and gate code. Use the frozen tools, rather than
   working-tree versions or `tests/follow-up/environment.sh`.

Authoritative freeze: `/home/john/Code/naro/target/phaseB-environments-repair-2026-10-31/freeze-attempt02`.

| Identity | SHA-256 / commit |
|---|---|
| Source commit | `498fb892d52d95b82b6eadea6f6250ebc5be7ef5` |
| Production | `63936243e73d0a3fb536d3c0a0fb0e6fe57be09da5f5bc0387ee10250b3d7093` |
| Verification tools | `68e03dbf57b6ac02aa06734c5e69aea6c36012ac59ec020a2eaea65d52fc8406` |
| Host NARO | `dcb8ae6d96a492a349e89a11f5706bbe4416d0c6d7288aec56e6db85d20a1ce1` |
| Ubuntu NARO | `ba4e046d174120733f33eb03fbcd205a34bd08a54a008b4fc3f38e740d8193df` |
| Host nano | `b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2` |
| Ubuntu nano | `6540492f810998a20a4dba4ac8048cd8b76d37a39e642f14f9f9c3d30c621ba7` |
| Isolated-root nano | `fe02ea07dc9a1e0afa009ef97dc034728995e39c65b75455985b0cf980fa3def` |
| Freeze manifest | `596829be9e3848a4135ffeda1c3d3dba0c177679b5681209f65e87c3bf7cb61b` |

Both NARO candidates are default-feature 0.1.1 builds with no test-hooks. The
Ubuntu candidate remains the intended portable Linux download after qualification.
The pinned GNU source commit is `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.
The frozen Ubuntu image ID is
`093817959dc26bb88c4f8df915372db75dee73f9356eb94f2ba428ea04fe9735`.
All other source/tree/toolchain/image hashes are in `freeze.json` and its inputs.
This exact freeze-attempt02 under the environment-repair directory is authoritative.
All earlier qualification-tooling and branding freezes are superseded; directory
numbering is local to each work root. Do not select a freeze by number alone.

## Why the oracle changed

At 30 columns the GNU brand fit sum is 31 and NARO's is 29; retaining NARO
is within Q-IDENTITY-001. Only the three exact TERM-001 source-case hashes and
`small` snapshots supply narrow context. Schema, physical dimensions, display
cells, attributes, filename and state stay checked. Candidate output never
chooses the expected projection. Finite locale alternatives must roundtrip the
complete original GNU row and produce one unique NARO row. Do not mask row 0,
change original observations, accept arbitrary translations or normalize state
positions to make a comparison pass.

The stopped attempt remains at
`target/naro-test-runs/claude-0.1.1-phaseB-2026-10-31-attempt01/`.
It and all failed setup attempts are preserved separately. Existing retained
reclassifications and development proofs do not qualify these rebuilt binaries.
CLI/layout checks alone do not cover environments; independently reopen fresh
13-case environment readiness and all its adversarial controls before Phase B.

## Independent entry check

- Verify the freeze, manifest SHA, source commit/tree, complete inventories,
  production and verification fingerprints, binary build-info and empty features.
  Repeat freeze verification at the end. Do not rebuild a default candidate.
- Reopen the focused host and Ubuntu readiness evidence independently. Each has
  CLI 5/5, 21 title-layout cases/105 assertions, the original paired/corpus blocker
  proofs, actual seeded history restoration, forged-evidence rejection and
  unchanged frozen inputs. These are readiness checks, not the full matrix.
- Check exact-source CI run `41242837960` directly and preserve its final result;
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
export NARO_FREEZE="/home/john/Code/naro/target/phaseB-environments-repair-2026-10-31/freeze-attempt02"
export NARO_ATTEMPT="/home/john/Code/naro/target/naro-test-runs/claude-0.1.1-phaseB-2026-10-31-attempt02"
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

- `/tmp/nv011-envfix01/nanospec-work/TEST-VT-VM-011-HOST/fx`
- `/tmp/nv011-envfix01/nanospec-work/TEST-VT-VM-011-UBUNTU/fx`

Complete preserved copy:
`/home/john/Code/naro/target/phaseB-environments-repair-2026-10-31/final-vm-fixtures/nanospec-work`.
Receipt: `/home/john/Code/naro/target/phaseB-environments-repair-2026-10-31/final-vm-fixtures/FIXTURE-PROVENANCE.json`.
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
