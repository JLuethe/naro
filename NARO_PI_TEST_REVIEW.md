# Pi / DeepSeek testing review — 2026-10-28

Codex reviewed the entire supplied session in chronological row order and
independently reproduced its behavioral failures. Five shared defects were
confirmed and repaired: two hard-wrap mark transforms, filter cut/insertion
sequencing, marked-filter cursor placement, and failed-filter selection cleanup.
The report validator also accepted missing or altered evidence and was repaired.
No claim of full GNU nano parity follows from these results.

## Inputs and evidence identity

- Session: `pi-deepseek-session.jsonl`, SHA-256
  `69720f06d5d7795ff09b7de733a4b1c9c6e3d3ca490bcd1578e3d62e48aa30da`.
  146 JSONL rows (zero-based R0–R145), 143 messages, 78 tool calls:
  59 bash, 18 reads, one grep. No implementation-edit tool calls.
- Session ran 2026-10-29 03:20:50–03:34:26 UTC
  (October 28, 20:20:50–20:34:26 Pacific).
- Starting repository and live `origin/main`: `dfcb38a8a480df32432760885b0f179dbfeb821f`.
  Source/tests were clean. `NARO_NEXT_STEPS.md` had a prior review edit;
  historical reviews, handoffs, four OpenCode exports and a validation archive
  were untracked. They were preserved. Pi's initial/final tracked diffs match.
- Pi candidate: default features, Rust 1.99.1, executable SHA-256
  `c6c7395af144a0714f2b7b79f697969211be127ca265e8ac5bd373edc2d9561f`;
  production fingerprint `522a6c33202ed6de6abe209bbe86e5f86a7ff49d0de0f41da11dca9f75a45e4e`.
- Pinned clean GNU nano 9.3 source: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`;
  executable `/home/john/src/nano-install/default/bin/nano`, SHA-256
  `b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2`.
  Codex independently checked both identities and rebuilt the pre-fix candidate.
- Pi evidence remains in `/tmp/naro-pi-Aw3VO4/`. Review evidence is in
  `/tmp/naro-codex-review/`. The latter contains `row-*.txt` under the separate
  `/tmp/naro-pi-review/` extraction, and `pi-command-ledger.json` with every
  original tool argument, paired output and source row. No transcript, raw log,
  binary or recording is committed. Scratch evidence is local and temporary;
  permanent reproductions are the checked-in scenarios.

Large payloads were read in consecutive ranges without output truncation.
The session itself includes bounded source reads and commands using head/tail;
those omitted source tails and child outputs are not invented. The full system
metadata, user prompt, thoughts, commands, outputs and final report were read.

## Findings reconciled with source and oracle

| Finding | Pi evidence and independent result | Resolution |
|---|---|---|
| T1-F1, critical: split-origin mark moved twice | REVIEW2-MARK-SPLIT saves `XL\n` instead of `X\nTAIL\n`; EOF variant exits 1, code 6, writes `.save`; T3-MARK-FWD loses TAIL | Confirmed. Shift original lower-line marks before mapping the split-origin mark. Permanent 040/041/045 and boundary controls. |
| T1-F2, critical: successor mark skips deletion mapping | PREFIX crashes; BLANKS saves `eee\n` instead of `eeedd\n`; PREFIX-STRIP wrongly removes `ccc` | Confirmed. Join mapping and removal mapping must both apply. Marks inside removed text stop at the join point. Permanent 042/043/046 and prefix controls. |
| T2-F1, high: report-only false acceptance | Missing binaries/scenarios/recordings, altered nested recording, missing default features all accepted as “provenance pinned” | Confirmed. Required artifacts, hashes, source/tools identity, recalculated assertions, step/snapshot completeness and differential comparisons now checked. |
| T4-F1, medium: filter loses trailing blank line | Identity `|cat` on region through magic EOF saves one LF instead of nano's two; no-wrap control also fails, paste control passes | Confirmed generic filter defect. Nano cuts, restores magic EOF, then inserts output; one wholesale replacement missed the intermediate newline. |
| T4-F2, medium: marked filter cursor | Selected bytes [1,4), uppercase filter: nano x=4, NARO x=0; file bytes agree | Confirmed. Preserve insertion end for marked filters; only unmarked filters reset to original line/x=0. |
| T4-F3, medium: failed filter retains mark | Nano removes reverse selection; NARO keeps it | Confirmed independently, including subsequent full-save behavior. Clear hard/soft marks and addition grouping on failed in-place filters. |
| Claimed unreachable trailing-space branch | ` eee ` as one burst produces an accepted join without adding another separator | Incorrect prior coverage claim. Both implementations already agree; permanent 044 protects it. |

Two pure-split failures are regressions relative to the pre-MiniMax candidate,
as documented in the earlier local review. This review reproduced current
failures; it does not claim to have freshly built every historical revision.
Earlier quote/indent/fill and node-survivor repairs remain in place and are
protected by cases 028–039. No source patch suggested by Pi was accepted without
checking the pinned source and executable.

Exact original reproductions now have permanent IDs 040–046 in
`tests/follow-up/scenarios/wrap-undo.json`. Filter controls and failures are in
`tests/follow-up/scenarios/filter.json`. Both suites save fixture-owned files,
assert oracle-derived bytes/cursors, and compare complete screens and modes.
See [development results](NARO_DEVELOPMENT_PROGRESS.md) for final verification.

## Errors, false positives and claims needing qualification

- The R45 replay driver deliberately omitted the handoff's final nonzero exit.
  Its shell says `driver_done=0`, while the candidate harness exits 1 and four
  comparisons differ. R80 and later ad hoc drivers likewise print differences
  without necessarily returning failure. Their wrapper success is not parity.
- Pi's final report incorrectly says candidate SPLIT/BLANKS had 3/3 assertions;
  actual R48 output is 2/3 for both, 1/3 for the two crashing cases, and 3/3
  for the trailing-space control. The reference passes all 15 assertions.
  A table also misstates SPLIT cursor coordinates: R112 records (1,1) for both
  sides after the cut; the difference is text/selection, not that cursor.
- “Code 6” is NARO's caught-panic recovery message, with exit status 1 and no
  terminating signal in the recording. It is not evidence of native memory
  corruption or a kernel-delivered SIGABRT. The invalid mark later reaches
  bounds-checked buffer slicing. No memory vulnerability was established.
- R100's failed-filter repeat records `exit_status=None`, signal 9 and
  `wait_exit timed out after 5s; editor still running ... sent SIGKILL`.
  This is harness teardown, not an application crash. Pi then called it a
  flawed error-dismissal probe. Independent testing shows the retained mark
  changes Write Out into selection-save behavior, explaining the extra prompt.
  With mark cleanup, the unchanged repeat matches nano. Thus the timeout was
  a consequence of a real UI-state discrepancy, not proof of a hang or a
  timing-only harness fault. Enter after the error also inserts a blank line;
  it must not be described as merely dismissing a modal error dialog.
- The T2 arbitrary-byte binary with a matching hash is a trust-boundary probe.
  Hash validation cannot authenticate an entirely fabricated evidence bundle.
  The repaired checker verifies consistency and required evidence without
  executing untrusted binaries; it is not a signed build attestation.
- T3-SOFTWRAP omits both `-S` and `-b`; it does not qualify combined hard/soft
  wrapping. The name is not evidence of reaching that branch. Structural T4
  probes often stop after undo/redo and omit the decisive later fill-accepted
  wrap. They do not establish spillage lifetime across every structural caller.
- Miri was actually attempted: six buffer tests pass before `columns_tabs`
  stops at unsupported FFI `nr_width`. Pi's description “first native call”
  is acceptable; “immediate failure of all tests” would be wrong. Its exit 1
  is a tooling limitation, not an editor defect. Stable Miri lookup failed;
  nightly Miri exists. Valgrind was absent. Pi did not run ASan/TSan.
- R71 generator fails with `TypeError: case() got an unexpected keyword argument
  'extra_extra'`. R72 repairs the scratch generator; R74 supplies the missing
  extra-file fixture. No production code change was involved.
- R12's unqualified `rustc --version` fails because rustc is outside PATH;
  Cargo and the absolute rustup paths work. Several `pgrep` “RUNNING” results
  match their own shell. Neither is a NARO defect.
- No externally interrupted/cancelled testing run is recorded. The one scenario
  timeout above and unsupported Miri are recorded explicitly. The six retained
  baseline skips are policy/profile exclusions, not newly skipped failures.

## Chronological test-command ledger

R numbers identify zero-based rows of the supplied JSONL. All bash commands,
including read-only inspections and inline Python bodies, were extracted
verbatim with their paired outputs to the scratch command ledger above. This
compact execution ledger covers every testing/build/probe invocation; report
editing, polling and source inspection are distinguished from tests.
`RUN=/tmp/naro-pi-Aw3VO4`, `CARGO=/home/john/.cargo/bin/cargo`, cwd repository.

| Call row → output | Executed command or driver | Actual outcome |
|---|---|---|
| 5→7, 8→9 | git status/branches/remotes/log; capture initial diffs | Read-only context, no source diff. |
| 11→12 | pinned git rev/status; `sha256sum .../nano`; `nano --version`; `cargo --version`; `rustc --version`; locale/TERM/nproc | Reference matches; rustc not in PATH. |
| 14→15,17→18 | list specs/scenarios/evidence; inspect build.rs/Cargo; AGENTS search | Inspection, no test. |
| 20→21 | `nohup ... cargo build --release --target-dir "$RUN/build" > "$RUN/build.log" 2>&1 &` | Finished release build (R39); not bounded by the recommended build timeout. |
| 23→24,32→33,38→39 | inspect build log/binary and pgrep; last poll sleeps 30 s | Build finished; pgrep self-match is not ongoing build evidence. |
| 41→42 | freeze/hash binary; `NARO_BUILD_INFO=1`; `python3 tools/check_wrap_undo.py` | Candidate identity recorded; manifest 39 valid. |
| 43→44 | inline handoff generator → `scenarios.json` | Five cases generated. |
| 45→46 | for each side: `python3 spec/tools/nanoharness.py "$RUN/scenarios.json" --binary <side-binary> --out "$RUN/<side>"` (240 s per child), then `compare` | Reference 0; candidate 1. Four DIFF, one MATCH; wrapper 0 masks failure. |
| 47→48,49→50 | print logs; decode fixture/captured bytes, stderr and `.save` | Confirms two bad cuts, two caught crashes. |
| 51→52 | inspect `target/next-wrap3/report.json`/hash | Existing genuine 39/39 report; not fresh replay. |
| 54→55 | `timeout 60s python3 tools/check_wrap_undo.py --report "$RUN/t2/fake-evidence/report.json"` | Wrong hash, no features/artifacts: false acceptance, exit 0. |
| 56→57 | nine scratch variants, each `[python3, tools/check_wrap_undo.py, --report, <variant>/report.json]`, timeout 60 s | P1/P2/P3/P6 false acceptance; P4/P5/P7/P8/P9 reject (1). |
| 58→59 | internal `report_problems` with None/tree fingerprints and arbitrary candidate bytes; `source_fingerprint('/nonexistent/root')`; genuine report CLI | API skips unavailable source check; arbitrary bundle accepted; genuine CLI 0. |
| 60→61 | dump existing scenario examples | Inspection only. |
| 60→62 | `timeout 180s python3 -m unittest discover -s tools -p test_check_wrap_undo.py`; `timeout 300s env PYTHONPATH=spec/tools python3 -m unittest test_compare_runs test_nanoharness test_namespace_exec test_audit_spec` | 21 and 36 pass; PIPESTATUS captures each child despite tail. |
| 63→64 | `timeout --kill-after=10s 900s env NANOSPEC_WORK="$RUN/wrap-work" PYTHONUNBUFFERED=1 python3 tools/check_follow_up.py --suite wrap-undo --binary "$RUN/candidate-default.bin" --out "$RUN/wrap"` (background) | R79/R81: 39 exact; report sides 0. |
| 68→69 | poll wrap log/report/pgrep | In progress; no result yet. |
| 70→71 | write/execute `python3 "$RUN/gen_t3.py"` | TypeError `extra_extra`; no cases replayed. |
| 72→73 | repair generator and execute; empty Python no-op with `|| true` | 32 generated; no-op not a test. |
| 74→75 | patch scratch extra-file and navigation/wait steps | Fixture preparation. |
| 76→77,78→79 | wrap polling, up to 20×10 s | Report arrives: 39/39. |
| 80→81 | fresh wrap report checker (60 s); two-sided `nanoharness.py "$RUN/t3-scenarios.json"` (900 s per child) and compare | Checker 0; both harnesses 0; 30/32 exact, two mark DIFF. |
| 82→83 | decode new mark failures and cursor/selection fields | Confirms same two causes. |
| 84→85 | background `rust_checks.sh`, commands below | R93/R95 record all actual statuses 0. |
| 84→93/95 | `timeout ... 180s cargo fmt --check`; `300s cargo test --release --target-dir "$RUN/default"`; `600s cargo clippy --all-targets --target-dir "$RUN/default" -- -D warnings`; `900s cargo clippy --all-targets --all-features --target-dir "$RUN/all" -- -D warnings`; `600s cargo test --release --features tiny --target-dir "$RUN/tiny"`; `900s cargo test --all-features --target-dir "$RUN/all"` | fmt/lints pass; default 9, tiny 5, all-features 5. Duplicate kill-after option in fmt wrapper is harmless. |
| 86→87,88→89 | inspect external-tool scenarios | Inspection only. |
| 90→91 | write t4b filter scenarios | Preparation. |
| 92→93,94→95 | poll Rust checks; extract counts | Completes matrix above. |
| 94→96 | two-sided `nanoharness.py "$RUN/t4b-scenarios.json"` (300 s), compare | Both harnesses 0; both scenarios DIFF. |
| 97→98 | decode filter outputs/screens and recompute comparison | Missing LF and retained selection observed. |
| 99→100 | generate controls; two-sided `nanoharness.py "$RUN/t4c-scenarios.json"` (300 s), compare | Reference 0; candidate 1. Two LF diffs; failed-filter repeat times out and is killed. |
| 101→102 | print t4c logs/step status/stderr | Confirms waiting save prompt, SIGKILL by harness. |
| 103→104 | generate controls; two-sided `nanoharness.py "$RUN/t4d-scenarios.json"` (300 s), compare | Both 0. CAT misses LF; midline cursor differs; paste control exact. |
| 105→106 | inspect filtered cursor and selection runs | Cursor 4 vs 0; failed filter keeps reverse in candidate. |
| 107→108 | `command -v valgrind`; `cargo miri --version`; list toolchains; inspect baseline-root availability | Valgrind absent; stable Miri unavailable; root unused. |
| 109→110 | background `regress.sh`: follow-up edges/tools/supplement and retained baseline, commands below | R120/R124/R126 confirm all statuses 0. |
| 109→120 | for suite edges/tools/supplement: `timeout --kill-after=10s 900s env NANOSPEC_WORK="$RUN/fu-$suite-work" PYTHONUNBUFFERED=1 python3 tools/check_follow_up.py --suite "$suite" --binary "$RUN/candidate-default.bin" --out "$RUN/fu-$suite"` | 13/13, 20/20, 3/3 exact; both sides 0. |
| 109→124/126 | `timeout --kill-after=10s 1800s env NANOSPEC_WORK=/tmp/nanospec-work PYTHONUNBUFFERED=1 python3 tools/validate_parallel.py --binary "$RUN/candidate-default.bin" --out "$RUN/baseline" --jobs 4` | 303 recorded; 301 exact, 302 file/exit, six skips, four workers 0; only two declared deviations. |
| 111→112 | extract detailed T1 cursor/screen fields | Nine/25/28/five diff fields, respectively. |
| 113→114,115→116 | poll regressions, inspect active process and logs | In progress, no new tests. |
| 117→118 | `cargo +nightly miri --version`; direct nightly-bin cargo lookup; Valgrind lookup | Nightly Miri exists; direct cargo defaults to stable and errors. |
| 119→120,123→124 | bounded regression polling | Reports arrive; checks listed above. |
| 121→122 | write scratch `PI_TEST_REPORT.md` | Report generation only. |
| 125→126 | inspect baseline summary, exclusions, worker statuses | Confirms declared deviations and all workers 0. |
| 127→128 | `timeout --kill-after=10s 420s cargo +nightly miri test --target-dir "$RUN/miri"` | Exit 1: six buffer tests pass, then unsupported `nr_width` FFI. |
| 129→130 | capture final git diff/status/HEAD; candidate/reference hashes | Unchanged source/HEAD/hash; no staged diff. |
| 131→132 | update report baseline, memory, integrity sections | Report editing only. |
| 133→134 | rerun internal checker API A/B/C/D into `t2/internal-api.txt` | Same false accept paths. |
| 135→136,139→140 | report wording/path cleanup | No tests. |
| 137→138,141→142,143→144 | read report, inspect tables and artifact inventory | No tests. R145 final report. |

Pi never received a repaired candidate during its session. Its “retest” section
therefore describes pending work. The post-fix results in the development
progress document are Codex's independent work, not results retroactively
attributed to Pi.
