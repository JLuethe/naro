# Claude handoff — step 5 host and portable Linux qualification

Date: October 30, 2026 (America/Los_Angeles).
Repository: `/home/john/Code/naro` — <https://github.com/JLuethe/naro>.

## Assignment and boundaries

Qualify the exact frozen default host and Ubuntu binaries described in
[NARO_STEP4_FREEZE_2026-10-30.md](NARO_STEP4_FREEZE_2026-10-30.md).
Step 4 is complete; step 5 has **not** been run. The selected production source
is `fd91763c4f14d9bed8187d64d44f2136440b7b3e`, with successful
[source CI](https://github.com/JLuethe/naro/actions/runs/41164011073).
Later documentation-only commits do not change these binary identities.

Independent testing only: do not edit production code, permanent scenarios,
comparators, normalizers, specifications, or goldens. Do not commit, push,
stash, reset, clean, publish, or replace the installed editor. Keep scratch
probes and reports in fresh ignored output directories. Auxiliary hooks/credits
and package-source rebuilds made by established runners are allowed; they must
remain separate from the default executables being qualified. Codex owns fixes.

Use [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) and
[the closure specification](spec/21-console-release-closure.md) as the contract.
Do not relabel historical evidence as results for these new binaries.

## 1. Verify inputs and prepare an attempt ledger

```sh
cd /home/john/Code/naro
freeze_dir=/home/john/Code/naro/target/release-freeze-2026-10-30
cd "$freeze_dir"
sha256sum -c freeze-manifest.sha256
python3 verify-freeze.py
```

Compare the manifest hash to the tracked
[freeze receipt](validation/release-freeze-2026-10-30.json), not only its local
sidecar. Verify script syntax with `bash -n` and confirm Podman has image
`093817959dc26bb88c4f8df915372db75dee73f9356eb94f2ba428ea04fe9735`.
Do not rebuild the image or pull a moving tag to work around a missing image.
Stop and report unavailable or altered frozen inputs.

The local bundle includes a clean detached `source/` checkout, pinned reference
source/bootstrap, full compiler hashes, build records/logs, frozen binaries,
smoke evidence, and qualification helpers. A normal GitHub clone does **not**
include this bundle. The reference install tree is part of the Ubuntu inputs.

| Identity | SHA-256 |
| --- | --- |
| Production source | `4cabd71741ffc8ee0357d945c67904c8a2fd0089c12e9b32a1c5b3e35c394ae6` |
| Host `host/naro` | `cae387c78619520aacbf61690e675496b82f8ccf04af2824beb9e864004f0a96` |
| Ubuntu `ubuntu/naro` | `33a39eb339492720ec6166e84fea421749e0b2ec3bd612b276c2377f91b7c4a1` |
| Host reference `references/host/nano` | `b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2` |
| Ubuntu reference `ubuntu/reference.bin` | `6540492f810998a20a4dba4ac8048cd8b76d37a39e642f14f9f9c3d30c621ba7` |

Both candidates report default features, version 0.1.0, and source commit
`fd91763`. Build environments: host glibc 2.44; Ubuntu 24.04/glibc 2.39.
Record current runtime details too: running a frozen host binary after an OS
upgrade is a different runtime qualification, even if its bytes are unchanged.

Create a fresh parent directory, for example
`target/naro-test-runs/claude-step5-2026-10-30-attempt01/`. Do not reuse this
name if it exists. Add `PROGRESS.md` and `ATTEMPTS.md`, recording the input
identities, date/time, commands, output locations, statuses, and owned processes.
Capture initial tracked Git status/diff in the main repo and frozen checkout.
Keep unrelated untracked reviews and previous evidence intact.

Before host testing, inspect active harness/tmux processes and ensure no other
run owns `/tmp/nanospec-work` or the same fixture IDs. Do not delete somebody
else's fixtures or kill unrelated sessions. Preserve the established host work
root: changing it can alter path-bearing messages and their screen positions.

## 2. Execute the host matrix

Use a **new, nonexistent absolute** output directory. The launcher verifies the
freeze, checks the historical host reference hash, stages the separately frozen
root reference in the clean checkout's ignored target tree, and invokes the
established host runner with the frozen executable. It never rebuilds the
default candidate. It does build separate test-hooks and credits auxiliaries.

```sh
freeze_dir=/home/john/Code/naro/target/release-freeze-2026-10-30
attempt_dir=/home/john/Code/naro/target/naro-test-runs/claude-step5-2026-10-30-attempt01
bash "$freeze_dir/run-host-qualification.sh" "$attempt_dir/host" > "$attempt_dir/host-launch.log" 2>&1
```

The parent `attempt_dir` must already exist; `host` must not exist. Record the
actual exit status immediately. `host/checkpoint.json` records each command,
status, elapsed time, active command, and overall state. A successful launch
requires zero exit and `state: complete`; inspect individual reports as well.

The host reference used by the original runner is
`/home/john/src/nano-install/default/bin/nano`; the wrapper verifies it matches
the frozen copy. Root/home uses the distinct root reference, hash recorded in
the freeze document. Do not substitute the default oracle for root testing.

## 3. Execute the independent Ubuntu matrix

```sh
bash "$freeze_dir/run-ubuntu-qualification.sh" "$attempt_dir/ubuntu" > "$attempt_dir/ubuntu-launch.log" 2>&1
```

Record the actual exit status immediately. The launcher uses the immutable
image ID, `--network none`, read-only frozen inputs, and only the selected output
mount writable. Tests run as ordinary uid 1000 inside a private rootless
container, so GNU nano honors fixture HOME. Root bootstrap only prepares owned
container directories. It does not install host packages or change host locales.

`qualify-ubuntu.sh` adapts the frozen `tests/follow-up/environment.sh` in two
ways: consume the prebuilt default candidate rather than compiling a new one,
and package from clean `/project` rather than the locale-adjusted working copy.
It retains the established matrix and auxiliary test-hooks build. Changes to
scenario `locpath` occur only in the private container copy and are exported as
`scenario-revisions/`. They do not permit semantic changes to test expectations.

The runner copies the **Ubuntu-built** reference install tree to its original
runtime location, generates fresh reference observations in Ubuntu, then runs
candidate comparisons. Its default binary and reference SHA are asserted before
testing. Expect `ubuntu/complete` containing `completed`, plus `naro`,
`reference.bin`, all required reports and logs. A marker alone is insufficient.

The adapter is syntax-checked but has not completed a full run yet. Report any
runner defect as a test-infrastructure failure, preserve it, and distinguish it
from an editor defect. Do not silently skip a failing stage.

## 4. Check Ubuntu installation and source packaging

The Ubuntu matrix produces a package but does not itself run the package
checker. Run this additional launcher so installed catalogs/syntax and source
rebuilds are exercised in Ubuntu, rather than inferred from host results:

```sh
bash "$freeze_dir/run-ubuntu-package-check.sh" "$attempt_dir/ubuntu" "$attempt_dir/ubuntu-install" > "$attempt_dir/ubuntu-install-launch.log" 2>&1
```

It runs `tools/check_package.py` against the binary and source archives in a
fresh private Ubuntu container using the frozen image and toolchain. Inspect
`ubuntu-install/package-check/report.json`, its `assets/report.json`, and
`source-build.log`. Require all 15 checks passing and the Ubuntu candidate SHA.
All source-rebuild artifacts stay separate. This supplies step 5 installation
coverage and preliminary step 7 evidence; it does not certify final release
archives or replace the later full packaging gate.

## 5. Evaluate the complete matrix

Counts are obligations, not a substitute for inspecting evidence and identities.

| Area | Required result in each environment unless stated otherwise |
| --- | --- |
| Terminal corpus | 303 recorded; 301 full, 302 file/exit matches; six explicit exclusions; four worker statuses zero |
| CLI / regex | 38 CLI and 162 regex checks pass; inspect extras safety assertions too |
| Historical follow-ups | 53 cases, 51 exact; only the two declared tool cleanup differences; all semantic assertions accepted |
| Additional exact suites | wrap-undo 58, filter 6, release-fixes 15, step3-gaps 40; all 119 exact; both harnesses zero; all steps/assertions pass |
| Evidence integrity | `check_closure_regressions.py` reopens and validates full evidence for all four suites |
| Terminal model | All eight ioctl-model comparisons pass; these are not genuine guest-VT qualification |
| Host root/home only | 27 exact, plus separate one-case no-home assertion with its named deviation |
| Writes / recovery | Controlled write failures, backup/locks, FIFO/EOF, signals, restoration and auxiliary panic recovery pass |
| Installed assets | Every shipped catalog checked (record actual count), overrides, symlink launch and syntax loading pass |
| Locales | Record generated locales and UTF-8/Latin-1 behavior, including the environment-specific reference observations |
| Large files | Existing 1 MiB and 10 MiB checks pass, with timing and result data retained |
| Host auxiliary / tooling | Host runner's Rust/Python/fmt/Clippy checks and six extensions entries pass |
| Package checks | Host runner's checks pass; separate Ubuntu check has all 15 passing and matching binary identity |

Inspect raw reports under `terminal/` on host and `candidate/` on Ubuntu,
follow-up suite folders, `extras/`, `large/`, `panic/`, and package checks. Keep
Ubuntu's `reference/` and `reference-cases.json`, not just its summary. Capture
all command return codes; harness success alone is not comparison success.
For new scratch probes prove the intended operation executed, use identical
input/geometry/locale on both editors, and retain minimal reproductions.

Run artifact validation within the corresponding environment. Ubuntu's four
suite validation already runs inside its private environment, where recorded
paths and locale adjustments match. Do not mistake failures caused by blindly
revalidating container paths on the host for editor failures. Report any needed
evidence relocation explicitly; never modify raw historical captures.

### Accepted differences remain bounded

- `TEST-CLI-057` / `Q-DEF-001`: established invalid-regex recovery difference.
- `TEST-PROMPT-NUL-001` / `Q-PROMPT-001`: reject NUL as a Yes response.
- `Q-TOOL-001`: the two historical HUP/TERM tool cleanup comparisons, subject to
  their existing field-level acceptance rules.
- `Q-ROOT-NOHOME-001`: separately asserted isolated-root no-home tilde recovery.
- Keep the six baseline exclusions explicit; skipped tests are not passes.

Any new unexplained mismatch, missing evidence, failed assertion, crash,
data-integrity defect, or unexpected command status blocks qualification.
Do not normalize it away, weaken expectations, or absorb it into an old
exception. Preserve both sides and give Codex the smallest useful reproduction.

## 6. Power interruption, failures, and evidence retention

Update progress after each batch with exact commands/statuses and the next
unfinished stage. The host runner checkpoints atomically after each command;
Ubuntu leaves per-stage logs and completed output folders. Neither launcher is
a complete resume engine. Keep an owned-process/container ledger if testing is
backgrounded; report active work before handing off.

After interruption, first inspect live processes and existing files. Keep all
partial outputs and explain the interrupted attempt in `ATTEMPTS.md`. Recheck
the frozen manifest. Use a new attempt directory for a clean rerun; never
pretend the old complete marker exists or overwrite previous reports. The
Ubuntu container uses `--rm`: ephemeral work may be lost, while `/out` evidence
is durable. An interrupted last file may be incomplete. No successful status
may be inferred from the presence of a log.

Stop dependent testing on a real new failure. Independent environment checks
may continue if their inputs are valid. Distinguish infrastructure mistakes,
resource/power interruption, reference failure, and candidate failures. Record
corrected scratch attempts rather than deleting them.

At completion, re-run `verify-freeze.py`, compare initial/final tracked Git
status/diffs, and hash the retained reports, raw traces and copied executables.
Preserve command logs, reference observations, scenario revisions, failed
attempts, package inputs/outputs, runtime records, and integrity-check output.
Do not run `cargo clean`. Request or use an agreed backup destination outside
`target/` before destructive cleanup; no off-machine backup is claimed yet.

## 7. Return to Codex

Write `CLAUDE_STEP5_REPORT.md` in the attempt directory with:

1. Exact source, candidate/reference hashes, environment/image and toolchain.
2. Every matrix row's result and counts, evidence path, exit status, and skipped
   or incomplete work. Label full qualification passed/failed/incomplete.
3. Known deviations listed separately from new findings. For each new finding:
   severity, synthetic reproduction, identical inputs, expected nano result,
   actual NARO result, and relevant raw evidence paths.
4. Failed or interrupted attempts, their causes, and successful rerun linkage.
5. Final evidence checksums, repository-integrity result, owned processes still
   running, and the exact next action for Codex.

The final closure collector also requires genuine guest-VT reports for both
candidates, transport evidence, and complete package evidence. Those are later
steps. Do **not** fabricate placeholders or claim a final collector pass from
step 5 alone. Nineteen genuine guest-VT comparisons per candidate remain step 6;
final package review remains step 7; public documentation, attribution, backup,
and publication remain steps 8–10. Do not publish a release.
