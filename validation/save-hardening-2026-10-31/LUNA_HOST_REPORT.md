# Luna independent narrow progress verification

**Review scope:** frozen host qualification evidence for release candidate `b934b1fcefa74adcf631c39b20ecd133c70edc59`, the complete 151-case closure suite, and an independent frozen host rerun of `save-progress` (22 cases). This report is from Luna; it does not claim Claude's review or an independent full matrix rerun.

## Result

The frozen host `save-progress` rerun passed all 22 cases against the pinned nano reference. Both programs exited 0, every reference and candidate assertion passed, and all 22 raw recordings compared exactly. The frozen closure evidence checker also passed all six suite bundles, covering 151 cases, with no evidence problems.

The root-owned host qualification checkpoint completed 35 checks with status 0 for every check. I reopened its reports and identities; I did not rerun its 303-case corpus or broader host pipeline. The separate initial sandbox attempt failed before scenario execution because tmux could not connect to its socket (`Operation not permitted`). That setup failure was preserved, then the suite was retried under the already-authorized escalated environment and passed.

## Frozen identities

- Source commit: `b934b1fcefa74adcf631c39b20ecd133c70edc59`
- Production source fingerprint: `3ce5c0ee2d62983b32c1d71664c3404c799ff8fc08c16f6bfdb0b90d2acc21bd`
- Verification fingerprint: `604c032c865701dac6f5fc0f0c9ce5e3764ed3e434b51e2ccea5fdf8172d45aa`
- Frozen host candidate SHA-256: `5767ed4938e25b0b49c0a9c546959a88260a9e2cbffb6dd472fe160c4ea666a7`
- Frozen host nano reference SHA-256: `b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2`
- The host checkpoint build info reports default features, the pinned nano commit `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`, and Rust `1.99.1`.
- `verify-freeze.py` was run after the replay and exited 0: frozen source, tools, binaries, references, and recorded inputs matched.

## Strict review of host closure evidence

I ran the read-only `tools/check_closure_regressions.py` collector against the root-owned host evidence, frozen candidate and frozen reference. It exited 0. Each row reported `pass: true` and an empty problem list. The checker reopened full evidence and validated suite inventory, unique IDs, per-case checks and statuses, candidate and reference fingerprints, source fingerprint, and scenario identity.

| Suite | Cases | Accepted | Match count | Checker |
| --- | ---: | ---: | ---: | --- |
| wrap-undo | 58 | 58 | 58 | Pass |
| filter | 6 | 6 | 6 | Pass |
| release-fixes | 15 | 15 | 15 | Pass |
| step3-gaps | 40 | 40 | 40 | Pass |
| save-progress | 22 | 22 | 22 | Pass |
| save-safety | 10 | 10 | 10 | Pass |
| **Total** | **151** | **151** | **151** | **Pass** |

All six reports bind to the frozen host candidate/reference hashes above and the production source fingerprint. Their root checkpoint commands all exited 0. The host checkpoint completed 35/35 checks at status 0, including package and package-check stages. The earlier terminal corpus report recorded 303 scenarios, 301 full matches, 302 file matches, and six skipped cases; its worker statuses were `[0, 0, 0, 0]`. Those figures are inspected root-owned evidence, not a new matrix execution by this review.

I separately inspected the SIGTERM and SIGHUP follow-up reports: each shows one accepted, declared deviation (`Q-TOOL-001`) rather than a raw match. Both reference and candidate assertions passed, while comparison records an interruption-related temporary-file difference. These historical signal reports are outside the six-suite strict closure checker I ran; root’s broader complete collector accepts them under their recorded deviation metadata. I did not relabel them as exact matches.

## Independent frozen `save-progress` replay

Attempt 02 used the frozen source's `tools/check_follow_up.py`, the frozen host candidate and frozen host nano reference. Its raw output retains both full 22-case candidate/reference directories, terminal recordings, assertion summaries, and report.

- Reference command exit status: 0
- Candidate command exit status: 0
- Exact comparisons: 22/22
- Assertions: passed for every case on reference and candidate
- Report summary: `recorded=22`, `matches=22`, `accepted=22`
- Strict closure validation of the replay: pass, no problems

The cases cover normal, narrow, minibar and zero modes; German translation; open and sync errors; FIFO, direct writes and interruption; color, append, prepend and selection; widths 8, 10 and 14; single-row no-help/zero modes; regular and FIFO completion overlays; and narrow CJK rendering.

Attempt 01 used the same frozen tool and binaries in the workspace sandbox. The tmux server failed to connect with `Operation not permitted`; both harnesses returned status 1 and the report had no recordings (`matches=0`, `accepted=0`). This is an environment setup failure, not a product finding. The attempt is retained under `host-save-progress/`. The authorized escalated retry is under `attempt02-host-save-progress/`.

## Timing record

The harness outputs and saved command transcript record execution results and exit statuses but no per-command start/end wall-clock timestamps. Those timestamps are unavailable; none are inferred here.

## Evidence paths

- Root qualification checkpoint and logs: `target/narrow-progress-qualification-2026-10-31/host/`
- Strict six-suite audit output: `closure-audit.jsonl`
- Failed sandbox setup attempt: `host-save-progress/`
- Successful replay and raw evidence: `attempt02-host-save-progress/`
- Strict replay validation and reproducible read-only validator: `replay-strict-validation.json`, `validate_replay.py`
- Commands, statuses, and setup/retry record: `commands.log`, `ATTEMPTS.md`
- SHA-256 inventory of this complete evidence directory: `SHA256SUMS`
