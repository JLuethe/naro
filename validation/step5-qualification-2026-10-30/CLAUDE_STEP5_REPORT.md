# Claude step 5 qualification report — NARO 0.1.0 frozen candidates

Date: 2026-10-30 (America/Los_Angeles). Tester: Claude (independent; no code, tests, goldens or normalizers changed; nothing committed, pushed, cleaned, published or installed).

Attempt directory: `/home/john/Code/naro/target/naro-test-runs/claude-step5-2026-10-30-attempt01/`

## Verdict

| Scope | Result |
| --- | --- |
| Step 5 host qualification | **PASSED** |
| Step 5 Ubuntu 24.04 qualification | **PASSED** |
| Ubuntu installation / assets / source-package check | **PASSED** (15/15) |
| New findings | **None** |
| Step 6 guest-VT (19 per candidate), step 7 final packaging, steps 8–10 | **Not run, not claimed** |

## 1. Identities and environments

| Identity | SHA-256 |
| --- | --- |
| Production source fingerprint | `4cabd71741ffc8ee0357d945c67904c8a2fd0089c12e9b32a1c5b3e35c394ae6` (reported by both binaries via `NARO_BUILD_INFO`) |
| Source revision | `fd91763c4f14d9bed8187d64d44f2136440b7b3e` (frozen `source/` HEAD; main HEAD `3ed1a47`, docs-only after) |
| Host candidate `host/naro` | `cae387c78619520aacbf61690e675496b82f8ccf04af2824beb9e864004f0a96` |
| Ubuntu candidate `ubuntu/naro` | `33a39eb339492720ec6166e84fea421749e0b2ec3bd612b276c2377f91b7c4a1` |
| Host nano reference | `b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2` (== `/home/john/src/nano-install/default/bin/nano`) |
| Host isolated-root reference | `fe02ea07dc9a1e0afa009ef97dc034728995e39c65b75455985b0cf980fa3def` |
| Ubuntu nano reference | `6540492f810998a20a4dba4ac8048cd8b76d37a39e642f14f9f9c3d30c621ba7` |
| `freeze.json` | `d404c22dc97a5554c47004fb25d21e7c96b510023fddfd25307a8118603409ea` (== tracked `validation/release-freeze-2026-10-30.json`) |
| Podman image | ID `093817959dc26bb88c4f8df915372db75dee73f9356eb94f2ba428ea04fe9735`, digest `sha256:7434f9d20c1d41cfd2d5ecd98ed8228b424910d51be7640a06262ccd3650c3ee` |

Build info for both: version 0.1.0, features `""` (default), rustc `1.99.1 (58cf8f9c3 2026-10-13)`, nano reference commit `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.

Every suite report names the expected candidate and reference hash (host root suites name the root reference). Copied executables at the run roots re-hash to the same values.

**Host runtime:** Linux 7.2.8-9-omarchy x86_64, glibc 2.44, Python 3.14.8, tmux 3.8, file 5.48, podman 6.1.4. System locales: C, C.utf8, en_US.utf8, POSIX. Fixture locale tree: `/home/john/src/nano-locales` (de_DE.ISO-8859-1, de_DE.UTF-8, en_US.ISO-8859-1, ja_JP.UTF-8). This is the same OS/glibc as the build record, so no post-upgrade runtime change.

**Ubuntu runtime:** container on the same kernel, Ubuntu 24.04, glibc 2.39, Python 3.12.3, tmux 3.8, file 5.45. `--network none`, uid 1000, read-only inputs. System locales: C, C.utf8, de_DE.utf8, en_US.utf8, fr_FR.utf8, ja_JP.utf8, POSIX. Generated `/opt/nano-locales` with localedef: de_DE.UTF-8, ja_JP.UTF-8, de_DE.ISO-8859-1 and en_US.ISO-8859-1 (`ubuntu/environment.json`).

## 2. Commands and exit statuses

| Time (PDT) | Command | Exit |
| --- | --- | --- |
| 20:37 | `sha256sum -c freeze-manifest.sha256`; `verify-freeze.py`; `bash -n` ×6; `podman image exists …` | 0 (all) |
| 20:38–20:55 | `bash run-host-qualification.sh $A/host > host-launch.log 2>&1` | **0**; `checkpoint.json` `state: complete`; all 33 commands status 0 (1041 s) |
| 20:55–21:13 | `bash run-ubuntu-qualification.sh $A/ubuntu > ubuntu-launch.log 2>&1` | **0**; `ubuntu/complete` = `completed` |
| 21:13–21:14 | `bash run-ubuntu-package-check.sh $A/ubuntu $A/ubuntu-install > ubuntu-install-launch.log 2>&1` | **0** |

Both launchers re-ran `verify-freeze.py` before and after (all "match"). The Ubuntu adapter runs under `set -euo pipefail`, so `completed` means every adapter command exited 0. Unlike the host checkpoint, it does not record per-stage status codes.

## 3. Matrix results

`H` = host (`host/`), `U` = Ubuntu (`ubuntu/`). Evaluated with the read-only `evaluate.py` into `host-evaluation.json` and `ubuntu-evaluation.json`. Raw reports were inspected as well as summaries.

| Area | Required | Host | Ubuntu | Evidence |
| --- | --- | --- | --- | --- |
| Terminal corpus | 303 / 301 full / 302 file+exit / 6 excl / workers 0 | 303 / 301 / 302 / 6 / [0,0,0,0] ✅ | 303 / 301 / 302 / 6 / [0,0,0,0] ✅ | H `terminal/report.json`; U `candidate/report.json`, `reference/` (303 fresh reference observations, workers 0, `reference-replay.log`), `reference-cases.json` |
| Non-full corpus cases | only declared | TEST-CLI-057 (also the single file mismatch), TEST-PROMPT-NUL-001 | same | as above |
| Exclusions | 6 explicit | TEST-BROWSE-003, TEST-CLI-025/032/033/035, TEST-KEY-007 | same | `skipped` in reports |
| CLI / regex | 38 + 162 | 38 pass; regex C 81 + en_US.UTF-8 81 = 162 pass; safety REGEX-SAFE, NUL-SAFE pass ✅ | identical ✅ | `extras/report.json`, `extras/safety/` |
| Historical follow-ups | 53, 51 exact, 2 declared | tools 20, edges 13, environments 13, supplement 3, backup 1, fifo-eof 1 all exact; SIGTERM, SIGHUP → Q-TOOL-001 accepted; ref/cand status 0; all checks true ✅ | identical ✅ | `<suite>/report.json` |
| Additional exact | 58 + 6 + 15 + 40 = 119 | 58/58, 6/6, 15/15, 40/40 ✅ | 58/58, 6/6, 15/15, 40/40 ✅ | `wrap-undo/`, `filter/`, `release-fixes/`, `step3-gaps/` |
| Evidence integrity | all four validate | `closure-regressions.log`: 4× `pass: true, problems: []` ✅ | same, run inside the container ✅ | `closure-regressions.log` |
| ioctl terminal model | 8/8 | 8/8 ✅ | 8/8 ✅ | `vt-ioctl/report.json` (**not** genuine guest-VT) |
| Root/home (host only) | 27 exact + no-home | 27/27 ✅; root-nohome-tilde 1 accepted as Q-ROOT-NOHOME-001 ✅ | n/a | `root/`, `root-nohome-tilde/` |
| Writes / recovery | pass | backup, fifo-eof, signals, edges/environments write cases pass; panic 3/3 (NAMED 8/8, NAMELESS 5/5, MULTI 11/11) ✅ | same; panic 3/3 ✅ | `panic/last-summary.json` |
| Installed assets | all catalogs | 41 catalogs; package-check 15/15 ✅ | 41 catalogs; asset checker 44/44; package-check 15/15 ✅ | H `package-check/`; U `../ubuntu-install/package-check/` |
| Locales | record | Latin-1 and UTF-8 cases in environments pass against the host reference | same cases pass against fresh Ubuntu reference observations with `/opt/nano-locales` | `environments/report.json` |
| Large files | 1 MiB + 10 MiB | pass; 0.51 s / 1.06 s ✅ | pass; 0.38 s / 1.11 s ✅ | `large/report.json` (output SHAs identical across environments) |
| Host aux / tooling | Rust/Python/fmt/Clippy + 6 extensions | fmt 0; Clippy `-D warnings` 0; cargo test 5/5; comparator 14, harness 6, namespace 7, console 9, closure 9 unittest OK; extensions 6/6 ✅ | n/a | `*.log`, `extensions/report.json` |
| Package checks | host + Ubuntu 15/15, Ubuntu SHA | host 15/15 (binary `cae387c7…`) ✅ | 15/15, binary `33a39eb3…`, archive `a42e7dbf…`; source rebuild finished; fingerprint and features match ✅ | `ubuntu-install/package-check/{report.json,assets/report.json,source-build.log}` |

### Ubuntu package check detail

- Checks: install-prefix-with-spaces (134 files), installed-hashes, symlink-launcher-assets, installed-native-catalogs-and-syntax, source-archive-hashes, source-archive-build, rebuilt-source-fingerprint, rebuilt-features, reject-checksum-mismatch / traversal / absolute / symlink / destination-symlink, uninstall-preserves-conflicts (README conflict preserved, 133 removed) and uninstall-owned-only. All pass.
- Package inputs: `ubuntu/package/`. Source archive `2bbb757b…7460`; `SHA256SUMS` `756eeeb4…c05b`.
- This is preliminary step 7 evidence only. It does not certify final release archives.

### Auxiliary builds (kept separate from candidates)

- `host/hooks/debug/naro` `dde96bff…0c86` (test-hooks).
- `host/credits/release/naro` `a066a666…1d09` (credits).
- Ubuntu test-hooks build stayed inside the container's `/work` (ephemeral).

None of these overwrote or replaced the frozen candidates.

### Scenario revisions (Ubuntu)

`ubuntu/scenario-revisions/` was compared semantically with the frozen `tests/follow-up/scenarios/`. Same file set, same case counts, and the only differing key is `locpath` (`/home/john/src/nano-locales` → `/opt/nano-locales`). The corpus `locpath` rewrite (8 cases in 2 files) is captured in `ubuntu/reference-cases.json`.

Minor observation, not a defect: the follow-up `report.json` field `environment.locpath` reads `null` in both environments. It records the process environment, not scenario `locpath`.

## 4. Declared differences (retained, not new)

- `TEST-CLI-057` / Q-DEF-001: invalid-regex recovery. This is the only full and file/exit mismatch, in both environments.
- `TEST-PROMPT-NUL-001` / Q-PROMPT-001: NUL is rejected as a Yes response. Screen mismatch only; file/exit match. Both environments.
- Q-TOOL-001: `TEST-NEXT-TOOL-003-SIGTERM` and `-SIGHUP`, `accepted: true` under the field-level policy. Both environments.
- Q-ROOT-NOHOME-001: `TEST-ROOT-HOME-002-NO-HOME-TILDE`, accepted. Host only.
- Six baseline exclusions are kept explicit. They were not counted as passes.

## 5. New findings

**None.** No unexplained mismatch, failed assertion, crash, data-integrity defect, missing evidence or unexpected command status occurred in any environment.

## 6. Failed or interrupted attempts

None. Each stage ran exactly once, in attempt01. There were no reruns and no infrastructure failures.

The adapter `qualify-ubuntu.sh`, which had no prior full run, completed its first full run without defect.

One self-inflicted, harmless command error: my ad-hoc `sha256sum ubuntu/package/*` hit a directory and returned 1. It did not affect any launcher.

## 7. Incomplete coverage and limits

- The Ubuntu matrix (per the frozen adapter) does not run fmt, Clippy, cargo test, the Python unit tests, credits, extensions, or root/home. These rows are host-only by design.
- The ioctl model is not guest-VT. The 19 genuine guest-VT comparisons per candidate (step 6) remain pending, as do the final package gate (step 7), the final closure collector, and docs/attribution/backup/publication (steps 8–10).
- No off-machine backup of this evidence (334 MB) or of the freeze bundle exists. Both survive reboot but not `cargo clean` or disk loss.

## 8. Final freeze and repository integrity

- **Freeze:** `final/freeze-verify.txt` shows `freeze.json: OK` and "Frozen source, tools, binaries, references, and recorded inputs match." The frozen hash values in `initial/hashes.txt` and `final/hashes.txt` are identical; only the path spelling differs (relative vs absolute).
- **Main repo:** HEAD `3ed1a47`, unchanged. Tracked diff and cached diff are empty before and after. The porcelain status (the pre-existing untracked reviews/JSON) is byte-identical.
- **Frozen `source/`:** HEAD `fd91763`, tracked diff empty before and after. The ignored-file listing gained `target/` (the root reference staged by the launcher, plus cargo test/Clippy builds), `tests/console/__pycache__/` and `tools/release/__pycache__/`. These are all expected outputs of the established runner and are excluded by `.gitignore`.
- **Evidence checksums:** `final/EVIDENCE-SHA256SUMS` hashes 5647 files under the attempt directory, including copied executables, references, reports, raw traces and logs.

## 9. Processes and leftovers

- **Owned processes still running:** none. No Podman containers are running; the only container is the pre-existing `naro-vt-rootfs` (created 6 days ago, not mine).
- **Unrelated:** a separate Codex session (pids 390127/390177) was diagnosing an earlier `conftest` SIGSEGV from 20:26, before this attempt started. It was not touched.
- **Leftover fixture:** `/tmp/nanospec-work/TEST-NEXT-PACKAGE-2ebba496a0b5` (20:54) was left by this attempt's host package-check stage. It was left in place, not deleted; it is safe for Codex to remove.

## 10. Next action for Codex

1. Record step 5 as passed for both candidates (host `cae387c7…`, Ubuntu `33a39eb3…`), citing this directory.
2. Back up the attempt directory and the freeze bundle outside `target/`.
3. Proceed to step 6: run the 19 genuine guest-VT comparisons for each frozen candidate with VM provenance. Then do step 7 final packaging and run the closure collector with complete inputs.
