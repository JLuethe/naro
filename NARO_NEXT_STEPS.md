> Published and verified: [NARO v0.1.0](https://github.com/JLuethe/naro/releases/tag/v0.1.0).
> See the [publication record](NARO_RELEASE_PUBLICATION_2026-10-31.md).
> The preparation and approval text below is retained as historical context.

# NARO next steps — Codex development ownership

## Release preparation complete — October 31, 2026

The [final approval packet](NARO_RELEASE_REVIEW_2026-10-31.md) supersedes the
historical checkpoints below. Both candidates passed full qualification, the
final technical gate passed 101/101, packages passed 15/15 plus 5 ordinary-prefix
checks, and Claude’s evidence and final metadata reviews passed. Required
publication approval remains with John. No tag, release or upload was performed.
Final review-delivery CI and preservation receipts are recorded after the commit.


## Save hardening and final qualification — October 31, 2026

Production `b934b1f` repairs save progress and the independently found safety and
terminal-state edges. Both new frozen candidates passed the full fresh matrix
and 101/101 gate, including 151 newer exact cases per environment and 19/19 guest-VT
each. See [current qualification](validation/save-hardening-2026-10-31/README.md).
Final package verification and independent asset review follow on these exact
bytes. Earlier proposals below are superseded; no publication is authorized.


## Save-progress repair and renewed qualification — October 30, 2026

Claude confirmed the earlier CI synchronization fix, then found missing save
feedback. John chose implementation and full requalification. Codex added
`Writing...` and `Writing to FIFO...` with 13 deterministic regressions in
production commit `16f6398968adc1f815055a4413cf0465aed28126`.
Both newly frozen candidates passed the complete fresh matrix and 99/99 gate,
including 132 newer exact cases per environment and 19/19 guest-VT each. The
production commit's GitHub CI passed. See the
[current qualification record](validation/save-progress-2026-10-30/README.md).

The old candidate, tag proposal and archives below are superseded. Final
refreshed archive identities and independent Claude verification are recorded
in the final release packet and QUALIFICATION.json sidecar. No publication is
authorized; John must approve the exact tag, prerelease setting, body and assets.
Codex owns implementation; Claude independently tests and reports. All earlier
checkpoints retain their historical scope.


## Step 10 preparation — October 30, 2026

The CI saved-cursor failure is reproduced as a save-completion synchronization
race and repaired in test-only commit 6004fa8. Frozen production code and binaries
are unchanged. Fresh affected suites pass 40/40 per environment, and the collector
passes 97/97. See the [step 10 review packet](NARO_STEP10_REVIEW_2026-10-30.md) for
the exact tag/assets proposal and Claude's independent verification prompt.
Claude verification and explicit publication approval remain; verify the cited
CI runs and final delivery before publishing. Earlier checkpoints are historical.


## Steps 8–9 complete — October 30, 2026

Reviewed documentation, attribution and public GitHub reporting are applied.
The same qualified Ubuntu executable was repackaged with current guidance;
fresh package checks pass 15/15 and the full collector passes 97/97. Exact
archives and full evidence are verified outside target. See the
[completion receipt](NARO_STEP8_9_RESULTS_2026-10-30.md).

Step 10 remains: investigate/disposition the earlier GitHub CI saved-cursor
failure, verify final delivery CI and remote HEAD, then obtain approval for the
exact tag/release/assets. Nothing is published. All earlier checkpoints below
are historical and do not override this state.

## Step 7 complete — exact packages and full gate, 2026-10-30

The unchanged frozen Ubuntu executable is selected as the primary Linux x86_64
download. Its binary and corresponding-source archives are byte-identical to
Claude's checked packages. The [complete technical gate](validation/step7-package-2026-10-30/closure/gate.json)
passes **97/97** checks; archive audit **20/20**, and a new ordinary-prefix
install/uninstall check **5/5**. Existing 15/15 package checks, 41 catalogs,
44/44 asset checks and offline source rebuild remain valid for these exact inputs.

[Step 7 results](NARO_STEP7_RESULTS_2026-10-30.md) identify the seven download files,
including runtime/provenance sidecars and checksums. Downloads and full evidence
are preserved at `/home/john/Backups/naro/2026-10-30-step7/`, with all copied
contents verified. Prior full raw-evidence backups were also rehashed. These
are same-disk backups. The archive source remains fd91763; no production code,
permanent tests, normalization or executable bytes changed. No owned processes
remain and nothing was published.

Next: step 8 public documentation, step 9 attribution/reporting review, and
step 10 final delivery/CI and publication approval. Do not treat a passing
technical gate as authorization to publish. Earlier checkpoints below remain
historical and do not override this state.

## Steps 5–6 passed — 2026-10-30

Claude qualified both frozen candidates with no new editor findings: the 303-case
corpus, historical 53-case follow-ups, all 119 exact regressions, CLI/regex/safety,
recovery, assets, large files and applicable root/home checks passed. See the
[step 5 receipt](validation/step5-qualification-2026-10-30/README.md).
Codex verified the test artifact hashes and freeze, re-evaluated the matrix,
and recorded stale checksum entries affecting only the two mutable ledgers.
The original tester evidence was preserved.

Codex then completed [step 6](NARO_STEP6_RESULTS_2026-10-30.md): 19/19 genuine
guest-VT matches per candidate and all six VM transport checks passed. Raw
terminal/keyboard/meta restoration assertions pass for all 76 editor runs.
The frozen binaries and production source remain unchanged. The owned VM exited
zero; no owned processes remain. An initial preparation permissions issue was
resolved only in disposable fixture copies and retained in the attempts ledger.

Verified same-disk backups outside the repository are under
`/home/john/Backups/naro/2026-10-30-step5/` and `2026-10-30-step6/`.
These protect against repository cleanup, not disk loss. Full step 6 evidence:
`target/step6-console-2026-10-30/`.

Next: step 7 final package/closure review, then public documentation, attribution,
and release-decision gates. No tag or GitHub Release has been published.
Earlier handoffs below are historical and do not override this checkpoint.

## Step 4 complete — committed freeze, 2026-10-30

Source `fd91763c4f14d9bed8187d64d44f2136440b7b3e` is pushed and its
[GitHub CI passed](https://github.com/JLuethe/naro/actions/runs/41164011073).
Fresh default host and Ubuntu binaries were built from the same clean detached
checkout and production fingerprint. Ubuntu has a separately built pinned nano
reference. Both candidates pass 4/4 smoke assertions; Ubuntu also passes both
minimal paging comparisons against its own reference. Complete provenance and
hashes are in [the freeze record](NARO_STEP4_FREEZE_2026-10-30.md) and
[compact receipt](validation/release-freeze-2026-10-30.json).

Next: [Claude step 5 qualification](NARO_CLAUDE_QUALIFICATION_HANDOFF_2026-10-30.md),
using the frozen binaries and prepared local launchers. The
[start prompt](NARO_CLAUDE_QUALIFICATION_START_PROMPT_2026-10-30.md) is ready to
paste into Claude. Full host/Ubuntu, guest-VT, and package qualification remain
pending; no release was published. The local bundle is
`target/release-freeze-2026-10-30/`; preserve it and all older attempts.

The sections below are historical checkpoints and do not override this handoff.

## Step 3 complete locally — 2026-10-30

The [targeted plan](NARO_STEP3_PLAN_2026-10-30.md) and
[results](NARO_STEP3_RESULTS_2026-10-30.md) close the bounded behavioral gaps.
Seven pre-fix paging differences shared one cause: soft-wrap paging used an
absolute logical-line column rather than the destination chunk's column.
The fix and permanent 40-case suite pass, as do the existing 79 controls and
complete artifact validation. The 303-case baseline retains its two deliberate
differences. No new deviation was introduced.

Next: step 4, a committed source freeze, then final host/Ubuntu qualification.
The current fixed binary is `target/naro-test-runs/codex-step3-2026-10-30/candidate-after.bin`;
its metadata and evidence are local, and its build includes the recorded
working-tree fix. It is not an Ubuntu-qualified or packaged release candidate.
Step 3 changes are included in this source delivery; preserve unrelated
untracked reviews. Step 4 records the selected commit and fresh build identities
separately. The earlier interrupted Ubuntu planning request started no container.

## Release readiness — scope and gate updated, 2026-10-30

Steps 1 and 2 of [the release-readiness plan](NARO_RELEASE_READINESS_PLAN_2026-10-30.md)
are complete locally. [The release checklist](RELEASE_CHECKLIST.md) defines the
default-profile Linux x86_64 preview, required gates, accepted differences, and
deferrals. Both qualification runners and the collector now require the newer
79 exact regressions in addition to historical closure coverage. Focused tests
pass; see [development progress](NARO_DEVELOPMENT_PROGRESS.md).

Next: step 3's targeted behavioral combinations, then freeze and qualify the
actual release artifacts. Do not mistake the updated gate or historical reports
for completed final host/Ubuntu, console, or package qualification. Changes from
steps 1–2 are included in this source delivery; remote delivery and CI status
are verified separately.

## Current checkpoint — Claude findings fixed and verified, 2026-10-30/31

Claude completed the restart assignment and confirmed six causes. Codex has
reproduced and repaired all six locally; see the latest section of
[development progress](NARO_DEVELOPMENT_PROGRESS.md). The new permanent
`release-fixes` suite passes 15/15, including three additional End/tab boundary
regressions. Both the default and ASan builds match all 86 broader probes and
controls. All old follow-up suites pass, and the retained baseline preserves its
two declared deviations. [Verification summary](validation/claude-review.json)
and `target/naro-test-runs/codex-claude-x1n2fz12/PROGRESS.md` identify the evidence.

The implementation and regression suite are included in this source delivery;
publishing the first release remains separate. For an independent retest,
use `candidate-v2.bin` in that directory, with the new permanent
regressions and the original failing inputs. Do not rebuild or relabel the
earlier Claude candidate as the fixed build. The remaining release work is
portable packaging and console qualification of the final source/build,
coverage gaps explicitly listed in Claude's report, and review of public-facing
claims and release notes. The restart instructions below are historical context.

## Restart review — 2026-10-30

**Start here after the interrupted laptop session.** The latest OpenCode export
contains nine differential failures that have not been integrated into the
development record. Reproduce these before expanding the generic matrix below.
The power interruption is user-reported; the export alone does not establish
its cause. Codex owns implementation and permanent regression tests. Other
models remain independent testers under `NARO_TEST_AGENT_HANDOFF.md`.

### State verified during this review

- Branch `main`, HEAD `56d2cc2d44b89bc0606f378e7f32fc6adef5a205`; local
  `origin/main` agrees. The remote was not fetched or independently checked.
- Latest implementation is `859d8084af11a42c0a9c18006e148e61e5f2026d`;
  HEAD adds its delivery receipt. Production, tests, tools, specs and CI have
  no local tracked changes. No implementation repair was made in this review.
- Pre-existing tracked edits: this document and `NARO_TEST_AGENT_HANDOFF.md`
  add OpenCode testing instructions. Preserve them.
- Pre-existing untracked material: `NARO_HARDWRAP_REVIEW.md`,
  `NARO_MINIMAX_SESSION_REVIEW.md`, `NARO_OPENCODE_TEST_AGENT_START_PROMPT.md`,
  `PI_AGENT_HANDOFF.md`, `PI_AGENT_START_PROMPT.md`, five `opencode-*.json`
  exports, and `validation/wrap-undo/archive/`. Preserve; do not blanket stage,
  delete, reset or clean. The older Pi assignment is superseded.
- Pinned nano source is clean at `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.
  Its executable SHA-256 is still
  `b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2`.
- `/tmp/naro-codex-review`, `/tmp/naro-pi-Aw3VO4`,
  `/tmp/naro-opencode-oyNTpm` and `/tmp/nanospec-work` are absent. Historical
  summaries survive, but their referenced temporary evidence cannot be checked
  in place. The untracked archive is older evidence, not a replacement for the
  missing 58-case/Pi/OpenCode bundles.
- Fresh checks: formatting passes; default Rust debug tests **9/9**;
  wrap checker unit tests **43/43**; comparator **14/14**, harness **6/6**,
  namespace **7/7**, audit unit tests **9/9**, console unit tests **9/9**.
  Manifest check passes with 58 scenarios and recorded scenario hashes.
  `cargo` is absent from this shell's PATH: use `/home/john/.cargo/bin/cargo`.
  Rust output was isolated in `/tmp/naro-state-review-build`.
- This review did **not** rerun terminal comparisons, release/tiny builds,
  Clippy, ASan, packaging or console qualification. Earlier 58/58 wrap, 6/6
  filter and 301/303 full-baseline results are historical, not fresh passes.

### Recovered unfinished session

Input: `opencode-testing-report.json`, SHA-256
`35fb127562eaafab4092b21fec1e9b6388a2776838b0eb0d28b72bbbf82e512b`.
It has 64 messages, dated October 28, 2026, 21:23–21:33 Pacific
(October 29, 04:23–04:33 UTC). It ends during paste investigation and contains
no final testing report or final repository-integrity check. Its metadata says
`succeeded`; that is not a test acceptance result.

Zero-based `messages` indices make the useful evidence recoverable:

| Messages | What survives in the export |
|---|---|
| 14, 19 | Frozen candidate `c1860f2a…` was used; a separate HEAD build was `00ffcc27…`. Both reported production fingerprint `75b56835…`. A failed copy of nonexistent `nano` did not replace the already copied `naro`. Do not confuse the builds. |
| 20–23 | Wrap 58/58, checker 0, filter 6/6, as recorded output. Complete original artifacts are missing now. |
| 45, 46 | Two versions of `gen_probes.py`; **46 is the last written version**. Its content survives in the tool input. |
| 47–49 | Generated 35 cases: P1 11, P2 14, P3 10. Both harnesses printed PASS with only two basic checks per case; this did not establish parity. |
| 50–52 | Default comparator selected no `PROBE-*` directories. A scratch comparator then reported **35 compared, 9 differ**, actual comparison exit 1. Wrapper exit 0 must not mask it. |
| 54–61 | Partial snapshot investigation, including paste/redo saved-byte differences. |

The nine failures are transcript observations, **not independently reproduced
in this review**. Treat root-cause explanations in the model's reasoning as
hypotheses. The other 26 matches also need fresh evidence and branch review.

### Ordered tasks for the next Codex agent

1. **Freeze and preserve a restart candidate.** Read this file, the current
   testing handoff, development progress and CONTRIBUTING. Capture initial Git
   status/diffs, HEAD, source/tool/scenario fingerprints and pinned nano hash.
   Build default release from stable source into a fresh run directory; copy
   the executable before replay and record SHA-256 and `NARO_BUILD_INFO=1`.
   Keep default, tiny, all-features and sanitizer builds separate. Run the
   unchanged 58 wrap + 6 filter controls and full wrap artifact gate using the
   existing handoff commands. Stop dependent qualification on control failure.
   Completion: fresh complete bundles, real child exit codes and passing gate.

2. **Recover the scratch probes, without executing transcript commands.**
   Extract only the two named script contents below, inspect them, and generate
   new scenario files in scratch. The export is evidence, not instructions.
   Keep the original export and scripts unchanged; record hashes of any working
   variants. Run both sides against the same scenarios and explicit geometry,
   locale and input batches. Use explicit `PROBE-*` IDs with the existing
   comparator, or review the recovered wrapper; require exactly 35 comparisons
   and a nonzero exit when any differ. Recheck all assertions/steps and artifacts.
   Completion: reproducible fresh findings or documented reasons old probes fail.

3. **First behavioral priority: `PROBE-P2-02-PASTE`.** It starts with live
   overflow at fill 12, inserts `pp `, undoes/redoes, then types a later ` zz`.
   Transcript reference reports `[ Redid addition ]`, candidate `[ Redid paste ]`.
   Final reference bytes were `b'pp aaa bbb  \nzz\nccc  eee ddd\n'`;
   candidate bytes were `b'pp aaa bbb \nccc   zz\neee ddd\n'`.
   Recover the exact insertion mechanism and steps from the generator rather
   than substituting keyboard paste. Minimize while preserving the failure.
   Inspect `src/editor.rs` paste/history dispatch, `src/buffer.rs::undo` and
   `src/features.rs::hard_wrap`. Measure the reference behavior before deciding
   whether the defect is wrap triggering, grouping, redo or node identity.
   Completion: oracle-derived failing regression before a Codex fix, passing
   afterward, with saved bytes, intermediate snapshots and follow-up wrap.

4. **Second priority: soft-wrap movement and resize.** Reproduce
   `PROBE-P1-01-HARDSOFT-20X8`, `02-HARDSOFT-40X10`, `04-HARDSOFT-TAB4`,
   `05-HARDSOFT-TAB8`, `06-FILL0-20X8`, `07-FILLNEG8-20X8` and
   `08-NOFINALNL-20X8` (all share the `PROBE-P1-` prefix). Transcript differences
   concern Up/Down/preferred columns; 04/05/06 also show viewport rows after
   widening. Separate resize, history and movement with minimal controls.
   Inspect preferred-column updates, screen-row mapping and viewport adjustment
   in `src/editor.rs`, `src/buffer.rs` and `src/render.rs`.
   Completion: repeatable oracle comparisons and permanent regressions for each
   distinct cause, not one fix or one test per duplicate manifestation.

5. **Third priority: `PROBE-P1-03-SOFTONLY-20X8`.** The transcript shows reverse
   attributes in nano's leftmost two buffer cells plus cursor differences.
   Repeat with fixed size, resize, redraw and controlled capture timing to
   distinguish stable behavior from stale terminal state. Retain raw traces
   and compare visible attributes under the existing normalization contract.
   Completion: classified reproducible behavior or a measured harness issue;
   do not discard visible attribute differences or change goldens speculatively.

6. **Complete the independent coverage matrix.** After the above findings,
   finish the three detailed priorities in `NARO_TEST_AGENT_HANDOFF.md`:
   combined wrap/EOF/history, structural callers with a provably fill-accepted
   subsequent join, and multibyte/mark/batch transforms. Recheck that the 26
   transcript matches actually enter their intended branch. Broaden ASan beyond
   five old probes using the recipe in development progress. Challenge the
   artifact gate on scratch copies. Testing models report; Codex alone repairs
   source, harnesses, permanent tests and specs.

7. **Run final regression configurations after fixes.** Default debug/release
   tests, tiny release tests and all-features tests in separate target dirs;
   fmt and both default/all-features Clippy with `-D warnings`; the Python checks
   listed above; expanded wrap + filter; edges/tools/supplement (13/20/3).
   Serialize the retained baseline at **`NANOSPEC_WORK=/tmp/nanospec-work`**
   after ensuring no other run owns it: expected historical counts are 303
   recorded, 301 full and 302 file-exit matches, six skips, all four workers 0.
   Only TEST-CLI-057 and TEST-PROMPT-NUL-001 are its declared differences.
   Do not infer default coverage from all-features, which enables tiny.

8. **Close evidence gaps and qualify a release candidate separately.** The
   stored audit has nine unresolved citations: TEST-CLI-P003, TEST-CLI-P042,
   TEST-KEY-RESTR-001, TEST-CLI-P009, TEST-RC-PREC-001,
   TEST-KEY-MODPRES-001, TEST-FILE-EXIT-002, TEST-INPUT-020,
   TEST-KEY-TABLE-001. Codex should measure/add real scenarios or document the
   remaining gaps, then regenerate/review inventory/audit changes. Independent
   testers must not run generators that overwrite tracked evidence. Refresh
   packaging, portable host/Ubuntu and genuine guest-VT gates against the final
   candidate using specs 19–22 and validation READMEs. Physical keyboard and
   other-platform scope remains explicitly deferred. Passing finite suites does
   not justify closing Q-UNDO-002 as exhaustive parity.

### Recoverable scripts and durable evidence

Use this extraction only after checking the export hash above. It writes script
text but does not execute it. Set `NARO_PI_RUN` to a fresh directory first:

```sh
export NARO_PI_RUN="$(mktemp -d /tmp/naro-opencode-XXXXXX)"
python3 - <<'PY'
import json, os
from pathlib import Path
doc = json.loads(Path('opencode-testing-report.json').read_text())
out = Path(os.environ['NARO_PI_RUN']) / 'recovered'
out.mkdir()
for index, name in [(46, 'gen_probes.py'), (51, 'compare_probes.py')]:
    matches = [part['state']['input']
               for part in doc['messages'][index]['content']
               if part.get('type') == 'tool' and part.get('name') == 'write'
               and Path(part['state']['input']['path']).name == name]
    assert len(matches) == 1, (index, name)
    (out / name).write_text(matches[0]['content'])
    print(out / name)
PY
```

After reviewing it, run the recovered generator with the new `NARO_PI_RUN`;
it writes `probes/p1.json`, `p2.json`, `p3.json`. Preserve the original script
and proposed scenario hashes. Follow the harness commands in messages 48–49
with newly selected paths, and validate comparator membership as described above.

**Do not depend on `/tmp` surviving another power event.** At each completed
batch, Codex should copy the entire immutable evidence bundle to a unique
`target/naro-test-runs/<run-id>/` directory, which is already ignored by Git.
Include binaries, scenarios, both recordings/raw traces, logs, actual statuses,
comparison JSON, report, source/tool hashes and a checksum manifest. Verify the
copy before marking the batch complete. Keep a short durable progress ledger
with completed/incomplete tasks and the exact resume command. Record original
paths; copying is preservation, not a claim that old absolute paths still work.
Do not overwrite older attempts. A local persistent copy protects against
temporary-directory cleanup, not disk loss; record any existing backup used.

Finish the cycle with a concise report of confirmed fixes, independently
retested results, remaining gaps and durable evidence location. Selectively
stage only reviewed changes if Git delivery is requested; exclude session dumps,
binaries and archives. Publishing or replacing the system editor is a separate
task. The current assignment is review/handoff, not release publication.

## Standing coverage plan

Current state: the Pi-review marked-wrap, filter and evidence-validator defects
are fixed for the recorded inputs. See [review](NARO_PI_TEST_REVIEW.md) and
[verification/commits](NARO_DEVELOPMENT_PROGRESS.md). The prior local plan was
read and preserved before replacement; its confirmed fixes are incorporated.
The historical 39-case checkpoint is not complete parity certification.

Codex is the sole implementation, permanent-test, specification and GitHub
owner. Pi/DeepSeek, OpenCode/MiniMax and GLM are independent testing agents only.
The binding next assignment is [NARO_TEST_AGENT_HANDOFF.md](NARO_TEST_AGENT_HANDOFF.md)
and its [start prompt](NARO_TEST_AGENT_START_PROMPT.md). Testing agents must
report defects to Codex rather than change implementation or expectations.
For the next OpenCode session, use the
[OpenCode testing prompt](NARO_OPENCODE_TEST_AGENT_START_PROMPT.md).

1. **Close combined terminal/history gaps.** Review independent evidence for
   hard+soft wrap (`-b -S`), scrolled viewports, resize mid-history, preferred
   column, view mode, `-L`, magic-EOF Backspace and a subsequent fill-accepted
   wrap. Pi's earlier similarly named cases did not reach every claimed branch.
   Fix measured mismatches only; do not redesign history speculatively.
2. **Validate structural callers.** Extend decisive wrap-lifetime checks through
   file/command insertion, search replacement, justification, formatter/speller
   and failed tools. Keep each surviving/detached node policy aligned with nano.
   Cover marked-filter reverse/empty/whole-buffer, empty/multiline/NUL output,
   saved points and divergence. The six current filter cases are finite coverage.
3. **Extend position/encoding evidence.** Marks before/at/after splits and
   removed prefixes; Unicode quote leads/blanks, literal tabs, CJK/combining
   characters, malformed UTF-8 and NUL; exact bursts versus individual keys;
   successive cuts, paste and undo/redo. Preserve the reference's byte/display
   width distinctions and quote-prepend quirk until contrary oracle evidence.
4. **Broaden memory and console qualification.** The critical five-case ASan
   run covers instrumented Rust/native bridge only. Extend to structural and
   stress cases, then refresh genuine VT/portable release qualification for a
   release candidate. Miri's unsupported FFI and unavailable Valgrind are not
   safety findings. Physical-keyboard and other-platform scope stays open.
5. **Maintain honest evidence.** Keep exact scenario membership and independent
   recomputation in the report gate; never substitute report booleans for
   artifacts or treat hashes as signed authenticity. Keep the nine unresolved
   audit citations listed as gaps until real scenarios/evidence exist. Add
   appropriate oracle scenarios, not invented coverage records.

Do not weaken assertions, normalize real differences or invent deviations.
Q-UNDO-002 remains partial. Default, tiny and all-features are different test
configurations. A release requires refreshed packaging and portable/console
checks; this development push does not publish or replace a system editor.
