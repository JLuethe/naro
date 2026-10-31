> Historical testing assignment — superseded for the fd91763 release candidate.
> Steps 5–7 are complete; see [current next steps](NARO_NEXT_STEPS.md) and
> [package/gate results](NARO_STEP7_RESULTS_2026-10-30.md). Do not rerun this
> assignment or replace its candidate paths without a new testing request.
> The original instructions below are preserved as historical evidence.

# NARO independent testing handoff — Claude, Pi, OpenCode or GLM

**Latest status:** Claude's completed report led to six local Codex fixes and
the new `release-fixes` regression suite. Read the current checkpoint in
[NARO_NEXT_STEPS.md](NARO_NEXT_STEPS.md) and the latest
[development progress](NARO_DEVELOPMENT_PROGRESS.md) before selecting a
candidate. The October 30 restart notice below describes the pre-fix assignment.

Claude starts with [NARO_CLAUDE_HANDOFF.md](NARO_CLAUDE_HANDOFF.md) and
[NARO_CLAUDE_START_PROMPT.md](NARO_CLAUDE_START_PROMPT.md). That assignment
allows new scratch evidence in a fresh ignored `target/naro-test-runs/` directory
for reboot persistence; all implementation and permanent-test work stays with Codex.

**Restart notice (2026-10-30):** Read the restart review at the top of
[NARO_NEXT_STEPS.md](NARO_NEXT_STEPS.md) first. The interrupted OpenCode export
preserves 35 scratch probes with nine reported differences (paste/redo bytes,
soft-wrap movement/resize, and soft-wrap attributes). Original `/tmp` bundles
are absent. Recover and freshly reproduce those probes after the unchanged
controls, before expanding the matrix below. They are transcript findings,
not newly verified defects. Codex must preserve completed evidence batches
outside `/tmp`; see the restart review's checkpoint procedure.

OpenCode uses [NARO_OPENCODE_TEST_AGENT_START_PROMPT.md](NARO_OPENCODE_TEST_AGENT_START_PROMPT.md).
For OpenCode, create a fresh `/tmp/naro-opencode-*` run directory and keep the
`NARO_PI_RUN` and `NARO_PI_CANDIDATE` variable names used in the commands below;
they are command aliases, not a requirement to use Pi. Deliver
`$NARO_PI_RUN/OPENCODE_TEST_REPORT.md` instead of `PI_TEST_REPORT.md`.

Codex owns all implementation, permanent tests, specifications and GitHub work.
The fixes and measured limits are in [development progress](NARO_DEVELOPMENT_PROGRESS.md)
and [Pi review](NARO_PI_TEST_REVIEW.md). This supersedes the older
`PI_AGENT_HANDOFF.md` and `PI_AGENT_START_PROMPT.md` testing assignment.
Do not interpret old “final” checkpoints as full parity certification.

## Mandatory role and boundaries

- You are an independent testing and validation agent.
- You may inspect source code but must not modify it.
- You may execute local development and testing commands.
- You may compare NARO against GNU nano.
- You may perform bounded memory-safety and terminal/PTY tests.
- You must not modify tests, fixtures, or specifications.
- You must not commit or push to GitHub.
- You must not attempt to repair discovered defects.
- You must record exact commands, outputs, and reproduction steps.
- You must distinguish verified findings from hypotheses.
- Return findings to Codex for implementation.

These restrictions include implementation/native code, existing scenarios and
expectations, comparators, generators, manifests, CI, docs and configuration.
Do not reset, clean, stash, switch branches, restore files or mutate source for
instrumentation. New proposed scenarios, private synthetic fixtures, scripts,
logs and reports may be written only under your fresh `/tmp/naro-pi-*` or
`/tmp/naro-opencode-*` directory.
Generated build output may use your private directory or ignored `target/`.
Never use real user files or edit the pinned reference. If you need hooks,
instrumentation or a harness fix, provide Codex a proposal and wait for its build.

## Candidate, reference and terminal

Read `CONTRIBUTING.md`, this handoff, progress and relevant specs 05/06/12/18/99.
Capture initial status/diffs/HEAD/remotes and recheck at the end. Verify a stable
source tree or obtain a frozen Codex candidate before building; do not build
while Codex is changing production inputs. Record the exact binary hash before
and after, build-info, feature/compiler/source fingerprints and tool/scenario
hashes. The embedded revision can change binary hashes without a source change.

Reference source `/home/john/src/nano-ref` must be clean at
`6ed285c3ec7a1d228def4d4e7021c6ba269f620c`. Executable
`/home/john/src/nano-install/default/bin/nano` must hash to
`b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2`.
Use it rather than system nano. Default terminal is tmux-256color, 80×24,
LANG=en_US.UTF-8; harness HOME/TMPDIR/PATH are synthetic. Use the existing
harness `term`, `cols`, `rows`, `lang` and `resize` fields for alternate probes.

```sh
cd /home/john/Code/naro
if [ -z "${NARO_PI_RUN:-}" ]; then
    export NARO_PI_RUN="$(mktemp -d /tmp/naro-pi-XXXXXX)"
fi
git status --short > "$NARO_PI_RUN/initial-status.txt"
git diff > "$NARO_PI_RUN/initial.diff"
git diff --cached > "$NARO_PI_RUN/initial-cached.diff"
git rev-parse HEAD > "$NARO_PI_RUN/head.txt"
git -C /home/john/src/nano-ref rev-parse HEAD
git -C /home/john/src/nano-ref status --short
sha256sum /home/john/src/nano-install/default/bin/nano
# Only build a stable tree; use a supplied frozen executable when available.
timeout --kill-after=10s 180s /home/john/.cargo/bin/cargo build --release --target-dir "$NARO_PI_RUN/build" > "$NARO_PI_RUN/build.log" 2>&1
naro_build_status=$?
printf 'build exit=%s\n' "$naro_build_status"
```

Stop dependent replay on build failure. Set `NARO_PI_CANDIDATE` to the absolute
path of that executable or Codex's supplied frozen build. Copy it into the run
directory before testing. Do not rebuild/relabel an already tested executable.
Run `NARO_BUILD_INFO=1 "$NARO_PI_CANDIDATE"` and `sha256sum` explicitly.

## First: unchanged regressions and evidence-gate challenge

The prior four marked failures and both extra mark manifestations are fixed
for measured inputs. Cases 040–043/045–046 reproduce them; 044 is the trailing-
blank burst control, and 047–058 cover boundary marks/quoted/UTF-8/trimmed paths.
A wrap and its trigger undo together; undo/redo clear the mark. Nano's spillage
pointer represents a live node, not text equality or line number.

Run the full 58-case wrap suite and six filter cases with fresh paths:

```sh
timeout --kill-after=10s 900s env NANOSPEC_WORK="$NARO_PI_RUN/wrap-work" PYTHONUNBUFFERED=1 python3 tools/check_follow_up.py --suite wrap-undo --binary "$NARO_PI_CANDIDATE" --out "$NARO_PI_RUN/wrap" > "$NARO_PI_RUN/wrap.log" 2>&1
naro_wrap_status=$?
printf 'wrap exit=%s\n' "$naro_wrap_status"
timeout 60s python3 tools/check_wrap_undo.py --report "$NARO_PI_RUN/wrap/report.json"
timeout --kill-after=10s 300s env NANOSPEC_WORK="$NARO_PI_RUN/filter-work" PYTHONUNBUFFERED=1 python3 tools/check_follow_up.py --suite filter --binary "$NARO_PI_CANDIDATE" --out "$NARO_PI_RUN/filter" > "$NARO_PI_RUN/filter.log" 2>&1
naro_filter_status=$?
printf 'filter exit=%s\n' "$naro_filter_status"
```

Expected: 58/58 and 6/6 exact, both harness statuses 0, every assertion/step
true, no `.save` artifact, and checker exit 0. A filtered `--ids` replay is
partial; the full-suite checker must reject it. Missing recordings or a child
failure must not be hidden by a wrapper's exit 0.

Challenge the checker only on copies in scratch space. Copy the complete new
wrap evidence directory, then remove/tamper one artifact at a time: binary,
scenarios, side scenarios, per-case result, raw trace, binary/scenario hash,
nested checks, step checks, snapshot text, summary, explicit features or source/
verification fingerprint. Preserve the original directory. Every invalid copy
must fail; the complete original must pass. Standalone all-green report JSON
with no artifacts must fail. Do not execute report-supplied binaries to test
metadata. This gate checks evidence integrity, not signed authenticity.

## Next three testing priorities

### 1. Combined hard/soft wrap, viewport, resize and EOF history

Make temporary variants of known passing scenarios (do not edit the originals).
Use **both `-b` and `-S`** for hard+soft wrap; omitting `-S` does not enable
soft wrap. Begin at 20×8 and 40×10, use a file with at least 40 numbered lines,
go near its bottom, type a burst that actually wraps, then resize narrower and
wider between undo and redo. Snapshot before/after each action and make a later
Up/Down move to expose preferred-column behavior. Repeat with `-l`, `-T 4/8`,
fill 0 and -8, then `-L` without a final newline.

Use `wrap-undo` 003/005/011/020/024/025 as starting inputs for three-plus wrap
groups, saved-point round trips and a later remainder that fits. Combine a
wrapped magic EOF, Home/Backspace, undo/redo, return to the real predecessor,
and a **fill-accepted** next wrap. Record bytes and breadth before asserting
that a spillage-lifetime branch was reached. Probe view mode with `-v`: type,
cut, paste, undo/redo and ensure text/history behavior matches the oracle.

Expected: exact oracle text, cursor, visible rows/attributes, modes, messages,
Modified state, grouping and following-wrap decision. Earlier individual resize/
EOF probes matched; these combinations remain incompletely tested. Do not
assume the viewport should restore a prior snapshot: measure nano itself.

### 2. Structural callers followed by a decisive accepted wrap

Start from case 005 or 037/038: create live overflow `ddd` at fill 12; perform
one operation on it or above it; undo/redo; then type a short remainder on its
actual predecessor. Its byte length plus target display breadth must fit 12,
so identity rather than fill rejection decides the following join.

Probe read-file insertion, command output insertion, marked `|cat`/uppercase
filters, successful/failed formatter and alternate speller, replacement and
justification. Use `filter.json` 001/002/004/005/006 as exact filter controls.
Use harness-owned executable stubs and preserve tool input/output bytes.
Include whole/partial/reverse/empty marks, targets at magic EOF and `-L`, NUL
payloads, empty output, output with one/two final LF, and subsequent cut/paste.

Expected: the pinned reference's real saved bytes (including its extra blank
line after certain marked EOF filters), marked-filter end cursor, unmarked-
filter original-line/x=0 cursor, cleared mark after failed in-place filter,
and compound undo/redo. A failed command must not add an undo item; the next
undo should target the preceding real edit. Compare source node-lifetime
hypotheses only after the final accepted-wrap observation.

### 3. Position transforms across multibyte leads and input batches

Vary 040–058 in scratch: mark before/at/after split; before/inside/after stripped
indent or blank runs; marks above/below/on the eaten successor; both selection
directions; trimblanks and default/custom quotes. Use literal fixture tabs,
Unicode spaces/quote prefixes, CJK width 2, combining marks, invalid UTF-8,
embedded NUL, tab stops 4/8, and successive cuts/edits/history. Preserve exact
input batches: compare a whole ` eee ` text step against separate characters;
they need not create identical history, but each delivery must match nano.

Expected: mark on the intended logical bytes, valid character boundaries,
correct highlighted cells and saved region, no panic/emergency save. The join
predicate intentionally mixes remainder **byte length** and target **display
breadth** in the reference; do not “correct” it without oracle evidence.

## Regression and memory checks

Run edges/tools/supplement as above with distinct suite/output/work paths.
They should remain 13/13, 20/20 and 3/3 exact. Serialize retained-baseline runs
and first verify `/tmp/nanospec-work` is unused:

```sh
timeout --kill-after=10s 1800s env NANOSPEC_WORK=/tmp/nanospec-work PYTHONUNBUFFERED=1 python3 tools/validate_parallel.py --binary "$NARO_PI_CANDIDATE" --out "$NARO_PI_RUN/baseline" --jobs 4 > "$NARO_PI_RUN/baseline.log" 2>&1
naro_baseline_status=$?
printf 'baseline exit=%s\n' "$naro_baseline_status"
```

Expected: 303 recorded, 301 full/302 file-exit matches, six policy/profile skips,
four workers 0; only TEST-CLI-057 and TEST-PROMPT-NUL-001 declared differences.
Use that exact root: retained path-bearing messages were centered before path
normalization. Never alter goldens or add deviations to hide a mismatch.

Relevant local checks: cargo fmt --check, default debug/release tests, both
Clippy configurations with warnings denied, tiny release/all-features tests in
separate directories, checker tests, comparator/harness/namespace/audit unit
tests. All-features enables tiny and cannot substitute for default wrap tests.
Do not run audit/inventory generators in this checkout; they write tracked data.

Codex ran five critical probes under a nightly ASan build instrumenting Rust
and the native bridge, with no sanitizer report. External native libraries were
not rebuilt with instrumentation. Broader sanitizer testing remains open. Use a
supplied sanitizer build or ask Codex for the exact build recipe; do not change
application source/build scripts. Record options, compiler and FFI scope. Miri
stops at unsupported nr_width FFI; that is not proof of a bug. Valgrind was
unavailable. No privileged installations or system-binary replacements.

## Evidence delivery

Write `$NARO_PI_RUN/PI_TEST_REPORT.md`. Include candidate/reference hashes,
source/tool/scenario identities, fixture hex, exact flags/keys/text batches,
terminal/locale, commands/timeouts/actual child statuses, full bounded logs,
both complete recordings, checks, raw traces, captured saved bytes, stderr,
exit/signal, selection/cursor/mode differences and emergency artifacts. Retain
failed attempts and explain harness/environment mistakes separately. For each
finding give the smallest reproduction, expected/actual bytes, severity,
verified/hypothesis status, decisive branch evidence and proposed scratch test.
List untested matrix cells. Capture final repository integrity and return the
report path to Codex. Stop at reporting; implementation and Git delivery belong
to Codex. Do not declare full parity from a finite passing suite.
