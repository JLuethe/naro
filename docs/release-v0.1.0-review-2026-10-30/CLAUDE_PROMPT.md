# Claude — independent step 10 verification

Work in `/home/john/Code/naro`. Independently verify the CI failure diagnosis and
its test-only repair. Do not change tracked files, production code, frozen
candidates, normalization, goldens, Git state, or release settings. Do not publish
anything. Use a new attempt directory and owned synthetic fixtures. Keep every
failed attempt and give its cause; never overwrite a prior run.

## Read first

- `validation/step10-ci-2026-10-30/README.md`
- `validation/step8-9-release-2026-10-30/previous-ci-failure.log`
- `tests/follow-up/scenarios/step3-gaps.json`, case `TEST-STEP3-EOF-NOFINAL-LIVE`
- `spec/tools/nanoharness.py`: `settle`, `wait_text`, `do_step`, `check`
- `NARO_STEP8_9_RESULTS_2026-10-30.md` and the current step 10 review packet.

Codex's test fix is commit `6004fa87d5cd3e3c1922bf1e9a58f28d39e871f4`.
It replaces the 150 ms pause before Enter with a wait for `Write to File:` and
adds a wait for `Wrote 2 lines` before the saved snapshot. Both time out after
five seconds. All original expectations and editor input bytes are unchanged.
The old CI run was https://github.com/JLuethe/naro/actions/runs/41168721954.
The fix's CI run is https://github.com/JLuethe/naro/actions/runs/41170577786.
Check their actual statuses; don't assume that a listed run passed.

## Frozen identities

Production revision: `fd91763c4f14d9bed8187d64d44f2136440b7b3e`.
Production fingerprint:
`4cabd71741ffc8ee0357d945c67904c8a2fd0089c12e9b32a1c5b3e35c394ae6`.
Default host binary: `target/release-freeze-2026-10-30/host/naro`, SHA-256
`cae387c78619520aacbf61690e675496b82f8ccf04af2824beb9e864004f0a96`.
Default Ubuntu binary: `target/release-freeze-2026-10-30/ubuntu/naro`, SHA-256
`33a39eb339492720ec6166e84fea421749e0b2ec3bd612b276c2377f91b7c4a1`.
Host reference: `/home/john/src/nano-install/default/bin/nano`, SHA-256
`b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2`.
Ubuntu reference: `target/release-freeze-2026-10-30/ubuntu/reference.bin`, SHA-256
`6540492f810998a20a4dba4ac8048cd8b76d37a39e642f14f9f9c3d30c621ba7`.
Offline Ubuntu image:
`093817959dc26bb88c4f8df915372db75dee73f9356eb94f2ba428ea04fe9735`.
Run editors as ordinary UID 1000, never as unisolated root. Containers may use
root only to prepare a private `/work`, then drop to UID/GID 1000 with setpriv.
Give host runs a new `NANOSPEC_WORK` under `/tmp`, inside owned fixtures. Containers
must use `--network none --pull=never`; never mount host system files writable.

## Verification tasks

1. Record starting `git status`, tracked diff, candidate/reference hashes and
   freeze verification. Preserve these identities through the run.
2. Inspect the original failure independently. Separate demonstrated facts from
   hypotheses: the original CI syscall timings were not retained. Determine
   whether the two waits synchronize the tested operation without accepting a
   wrong cursor or hiding a save error.
3. Copy the probe scripts and JSON files from
   `validation/step10-ci-2026-10-30/` into your new attempt directory before running
   them. They must not write in the tracked validation directory. Inspect the
   fsync interposer; it delays only a synthetic fixture's save and is not part of
   either production executable. Run original and synchronized scenarios at
   0, 600 and 1,200 ms delays against host NARO/nano and Ubuntu NARO/its own nano.
   Use fresh output names and fixture roots for every run. Record all per-step
   assertions, snapshots, raw traces, saved bytes, stderr and process statuses.
   Expected diagnostic failures are not qualification passes.
4. Compare the original and repaired case structurally: identical `expect`,
   input key/text bytes, fixture contents, arguments, and snapshot inventory.
   Confirm delayed original NARO captures the old CI cursor/prompt symptom,
   while synchronized tests pass. Check complete output traces, not just counts.
   Verify that a timeout still fails `steps_ok`, and that an intentionally wrong
   cursor expectation in a disposable scratch case is rejected. Never change
   the real expectation to make a probe pass.
5. Run the complete updated 40-case `step3-gaps` suite once against each frozen
   candidate and its environment's own reference, using `tools/check_follow_up.py`.
   Require 40/40 exact, all assertions and steps true, both harness statuses 0.
   Use fresh `--out` directories and the established evidence checker to validate
   each suite. Do not reuse host observations as Ubuntu evidence. No editor
   rebuild is needed.
6. Recheck the release packet's asset manifest and archived executable/source
   identity. Do not replace archives or edit their qualification sidecars. Explain
   the separate production revision, packaging revision and proposed tag target.
7. Confirm no owned processes remain, rerun freeze verification, compare final
   Git state with the starting state, and report any new finding without weakening
   normalization or silently rerunning it until green.

## Deliverables

Create `CLAUDE_STEP10_REPORT.md`, `PROGRESS.md`, `ATTEMPTS.md`, command records and
a final SHA-256 evidence manifest inside your attempt directory. State each task's
result, exact environments/binaries, all failures and uncertainty, and whether
Codex's diagnosis and synchronization repair are supported. A new editor defect,
unexplained mismatch, unexecuted operation, bad assertion or missing evidence is
a blocker. Do not claim a passing rerun proves the historical CI cause. Do not
claim to approve publication: John makes that decision after review.
