# 98 — Progress log

Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

This file lets a later session resume without the earlier conversation.
Latest wrap-up review (2026-10-24): read `../WRAP-UP.md` before resuming.
It records the published revision, uncommitted console work, incomplete final
validation, and ordered completion gates. Earlier checkpoints below describe
their recorded binaries and do not certify these newer local changes.
When resuming, read in this order: `00-overview.md`,
`00-reference-environment.md`, this file, `97-coverage.md`, and the relevant
parts of `99-open-questions.md`.

## Resume commands

```sh
# reference tree (clean, detached at the pinned commit)
cd ~/src/nano-ref && git status --porcelain && git rev-parse HEAD
# reference executables
~/src/nano-install/default/bin/nano --version
~/src/nano-install/tiny/bin/nano --version
# re-dump key/function tables (13 profiles) into spec/evidence/tables/
~/src/nano-rs/spec/tools/dump_all_tables.sh
# run scenarios
cd ~/src/nano-rs/spec && python3 tools/nanoharness.py evidence/scenarios/*.json
# regenerate inventories derived from source + dumps
python3 tools/build_inventories.py
```

Private locales for translation and non-UTF-8 probes: `LOCPATH=~/src/nano-locales`
with `de_DE.UTF-8`, `de_DE.ISO-8859-1`, `en_US.ISO-8859-1`, `ja_JP.UTF-8`.

## Session 1 (2026-10-23)

### Done
* Cloned upstream; resolved `6ed285c` → `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`;
  created a clean detached worktree at `~/src/nano-ref`.
* Built and installed the `default` and `tiny` profiles from a pristine export
  (gnulib at its pinned hash, from the GitHub mirror because Savannah returned HTTP 500).
* Wrote `00-reference-environment.md`.
* Wrote the gdb table dumper; dumped 13 profiles into `evidence/tables/`.
* Wrote `tools/nanoharness.py` and verified it with `TEST-SMOKE-001` (PASS).
* Built test locales in `~/src/nano-locales`.

### Source read so far (complete reads unless noted)
* `src/definitions.h` 1–664
* `src/global.c` 1–1666 (globals, `add_to_funcs`, `keycode_from_string`, `add_to_sclist`,
  `get_shortcut`, `interpret`, `shortcut_init`, `epithet_of_flag`)
* `src/rcfile.c` 1–1751 (whole file)
* `src/nano.c` 1–2755 (whole file)
* `src/winio.c` 1–3726 (whole file)
* `configure.ac` (feature dependencies)

### Next actions
See the bottom of this file. It is kept up to date as areas complete.

## Checkpoint A (2026-10-23, after 04)

### Additional source read (complete)
`src/prompt.c`, `src/move.c`, `src/cut.c`, `src/chars.c`, `src/utils.c`,
`src/text.c`, `src/search.c`, `src/files.c`, `src/history.c`, `src/color.c`,
`src/help.c`, `src/browser.c`. **All 18 C files of `src/` are now read in full.**
Docs read: `doc/nano.1`, `doc/rnano.1`, `doc/nanorc.5` (complete, rendered).
`doc/nano.texi` not yet read (it largely mirrors the man pages; to cross-check later).

### Documents written
- `00-reference-environment.md` (complete)
- `01-cli.md` (complete; 65 terminal scenarios + 46 non-tty probes)
- `02-keybindings.md` + generated `02-keybindings-tables.md` (complete)
- `03-terminal-input.md` (complete)
- `04-rendering.md` (complete)

### Inventories (tools/build_inventories.py regenerates all)
`keybindings.csv` (922 rows), `functions.csv`, `bindable-functions.csv`,
`helplines-80cols.csv`, `cli-options.csv`, `nanorc-options.csv`,
`nanorc-commands.csv`, `color-names.csv`, `messages.csv` (682),
`translation-catalogs.csv`, `build-features.csv`, `menus.csv`,
`escape-sequences.csv`, `toggles.csv`, `syntaxes.csv`, `undo-types.csv`.

### Harness changes
- `nanoharness.py` captures rows one by one (a whole-screen `capture-pane -e`
  carries SGR state between rows, which corrupted attributes). All earlier
  scenarios were re-run after this fix.
- Key names: `M-a`/`M-A` send ESC + lower-case letter; `Sh-M-A` sends ESC + `A`;
  modified special keys (`^Left`, `M-Up`, `Sh-^Del`, …) come from extended
  terminfo capabilities.
- Text steps: use `\r` for Enter (`\n` is ^J = Justify).

### Findings worth remembering
- `nano +r/( file` crashes (SIGSEGV) → Q-DEF-001.
- `-z` exits during option parsing (rc errors dropped; later `-f` ignored).
- Command-line `-p` removes ^S/^Q bindings; `set preserve` does not.
- tiny: optstring unchanged; unknown handlers → "Type 'nano -h'…" exit 1.

### Next
05 buffer/editing → 06 undo → 07 search → 08 files → 09 browser →
10 nanorc → 11 syntax → 12 features → 13 signals → 14 messages →
17 prompts → 18 bytes → 16 test plan → 15 architecture → 97/99/00-overview → audit.

## Final spec checkpoint (Codex, 2026-10-23/24)

The behavioral documentation phase is complete. Docs 05–14, 17 and 18 were
present after the inherited checkpoint; reviewed against their evidence and
used for the final contracts. Added 00-overview, 15 architecture, 16 test plan,
97 coverage, 99 decisions, data README, requirement inventory and audit tooling.
Full commit hash is at the top of every Markdown spec file.

Final decisions: libc POSIX regex and ncursesw FFI, byte-vector buffer with
explicit coordinates, native locale/gettext semantics; reject NUL as Yes and
fix invalid startup regex crashes; reproduce byte-mode Latin-1 word behavior.
See 99 for the full decision register, including remaining verification gaps.

Completed comparator: live/final screens, attributes indexed by cells, cursor,
modes, stdout/stderr, exit/signal, input bytes, fixture manifests and captured
locks; narrow normalization documented in 16. Twelve regression tests pass;
309/309 reference self-comparisons match. Harness now reports failed wait/settle
steps and returns nonzero for FAIL/ERROR instead of silently recording success.
No reference sources were changed.

Audit found and archived three obsolete duplicate definitions in files.json;
corrected definitions in files2.json match existing evidence. There remain 309
unique recorded scenarios, four explicit assertions and ten intentional SIGKILL
runs. Keybinding inventory actually has 921 rows (the earlier 922 included the
header). Planned probes remain source-only and are enumerated in 97/16.

Rust installed at user level through official rustup, minimal profile, no shell
startup modifications: `~/.cargo/bin/rustc` 1.99.1 and Cargo 1.99.1. Repository
`~/Code/naro` started as LICENSE/README only, origin JLuethe/naro. The spec will
be copied there before implementation, so one checkout contains the handoff.
No system packages installed. User authorized committing/pushing and continuing
through implementation/build/tests while unattended.

Resume implementation from the repository README/status report. Preserve
`spec/evidence/runs`; send candidate harness output to another directory.
`~/src/nano-rs/spec` is the original working spec; the checked-in copy travels
with Naro. Record later implementation work in the repository copy.


## Implementation validation follow-up (2026-10-24)

The repository copy at `~/Code/naro/spec` is authoritative for subsequent
corrections. The original `~/src/nano-rs/spec` remains the inherited checkpoint.
Rust was installed at user level without changing shell profiles or system
packages. A working Rust/C-native implementation and the complete spec were
committed and pushed to `JLuethe/naro`; GitHub CI builds and checks it.
See `../IMPLEMENTATION.md` for current candidate validation, distinct from
spec completion.

Harness refinements: private per-scenario TMPDIR; exact argv0 and explicit
execve environment (Python's implicit C-locale coercion must not leak into the
editor); optional hold_tty for redirected probes. Corrected ten intentional
kill recordings' terminal wait steps to sleeps, preserving their original
steps in `evidence/recording-timeout-corrections.json` and raw reference output.
Comparator now narrowly normalizes tool temp-path logs and truncated tmux dead
banner dates. Twelve comparator regression tests cover the contract.


Final harness checks also batch independent row captures into one tmux client,
preventing the 400 ms spelling message from expiring during 24 client launches.
Row SGR reset semantics remain unchanged. Exit waits require reaped status,
fixing a PTY-close/waitpid race exposed on GitHub's tmux; named signals are
converted to numeric values. Three harness regression tests cover these cases.
New results record the executable SHA-256 in addition to the frozen-run report.

GitHub's older tmux also exposed consecutive-server teardown races; each
scenario now has a unique server socket. Failure output includes final pane
state and screen. The regex safety probe waits for the save confirmation before
sending Exit. These are fixture isolation/observation fixes, not editor changes.

The faster captures exposed a real cancellation bug that slower captures masked:
a cancelled search must clear the spotlight immediately. The Rust state machine
now does so. Final replay uses `tools/validate_parallel.py` with four disjoint ID
partitions, a frozen executable and a combined completeness/hash check. The
original serial `tools/validate.py` remains available for focused diagnosis.

CI's tmux 3.4 intermittently reported a dead pane with neither exit status nor
signal even after the editor restored its terminal. Signal-mask experiments
did not resolve it. CI now builds checksum-pinned tmux 3.8 in its private runner
directory, matching the reference emulator in ENV-BASE; no status normalization
or weakened exit assertions are used.


## Final build/test checkpoint (2026-10-24)

The spec is complete and the editor builds in debug and optimized release modes.
The final frozen candidate in `~/Code/naro/spec/evidence/naro-v7` has 303 fixture-
safe recordings: 301 full matches and 302 file/exit matches. The only full
comparison differences are TEST-CLI-057 and TEST-PROMPT-NUL-001, the declared
safety improvements. Their six separate assertions pass. All 38 safe default
CLI probes and 162 regex cases match. Six Rust unit tests, twelve comparator
regressions, three harness regressions, formatting, strict Clippy and structural
audit pass. All four disjoint replay workers exit zero.

Compact results with the binary SHA-256 and source revision are checked in under
`~/Code/naro/validation/`; raw candidate evidence remains on disk (gitignored).
`~/Code/naro/IMPLEMENTATION.md` records known implementation limits, including
whole-buffer external tools and optional tiny/credits. No blanket claim of
complete source-branch or platform parity is made. The reference checkout
remains clean at the exact pinned commit. Final Markdown/tools/data/scenario
corrections are also synchronized back to `~/src/nano-rs/spec`; use the Git
repository copy as the canonical location for future edits.


## Follow-up specification (2026-10-24)

Added `19-completion-and-release.md` for selected-region spelling, formatter
selection state, editing/configuration/failure verification, environment coverage,
and installation/release. Corrected the earlier broad formatter description:
formatting remains whole-buffer; it must clear the mark at the source-defined
point. The selection-only gap is spelling.

There are 22 planned requirement headings and 41 proposed cases in
`data/follow-up-tests.csv`, all marked planned with no invented observations.
The structural audit now separates baseline/planned requirements and checks the
matrix's IDs, coverage, gates, statuses and evidence-path presence. The original
248 requirements, 309 recordings and frozen release validation remain unchanged.

Tiny is explicitly an optional compile-time reduced profile. Added a static
`CREDITS.md` with factual attribution and proposed a default-off plain-text
runtime credits extension; no editor behavior or CLI output changed in this task.
The next implementation milestone is doc 19 M1, not a new full-parity claim.

## Follow-up implementation (2026-10-24)

Implementation commit: `4952ca020e72425d04acf12639d222b7a33a9245`.
Release runner/CI commit: `eef679131cf1c16decd62dae2cd61ade497226bd`.

Implemented region-aware alternate/internal spelling, SPECIAL selection bytes,
orientation/cursor/mark restoration, whole-buffer formatter mark clearing, RAII
tool files, handled child termination and panic cleanup. Fresh differential
cases found and fixed disk-full warning phases, EINTR/short writes, backup
fallback, lazy syntax diagnostics and distinct undo/redo labels for wrapped
paste. Test fault injection is fixture-inode/path scoped ptrace on Linux x86_64.
Reference source stayed clean and original observations were preserved.

Added installed-relative catalogs/syntax, standalone ownership-aware installer,
source/binary archive/checksum/provenance tooling, default-off credits, and
separate recovery test hooks rejected by the packager. Static credits are
installed. No real user prefix/config was changed. Testing, including interactive
operator trials and install/uninstall, stayed in harness fixtures.

The current [matrix](data/follow-up-tests.csv) and
[follow-up reports](../validation/follow-up/README.md) are authoritative for
completion and deferred scope. Parent validation reports remain historical.
The new default host binary SHA-256 is
`524c97345cfca85458fa9c94ea297b0432b6f4c645f70f8a767b161b2f59f5ac`,
source-input SHA-256
`742ca8b1a18bec48989e1fcabe46a71bf847fc1d7d6582b9be9c65cfd6a73aac`.

Reproduce the host follow-up differential gate with a **new** output directory
per suite (do not run the same IDs concurrently):

```sh
cargo build --release
for suite in tools edges environments supplement backup fifo-eof signal-SIGTERM signal-SIGHUP; do
  python3 tools/check_follow_up.py --suite "$suite" --binary target/release/naro --out "target/new-$suite"
done
python3 tools/validate_parallel.py --binary target/release/naro --out target/new-baseline --jobs 4
python3 tools/check_cli.py --binary target/release/naro
python3 tools/check_regex.py --binary target/release/naro
python3 tools/check_release_gate.py --out target/new-gate.json
```

Second-environment runner uses a rootless Ubuntu 24.04 container, private build
HOME, and ordinary uid. uid 0 is unsuitable for HOME-isolated GNU nano tests:
it deliberately consults passwd for root's home. Early failed setup attempts
are preserved under `target/follow-up-env-*`; see `limits.json`. Reference
auxiliary symlinks are replaced only in the copied bootstrap tree. The reference
library/editor/catalogs are built without requiring Texinfo documentation tools.

```sh
podman build -f tests/follow-up/Containerfile -t localhost/naro-followup:ubuntu24 .
mkdir -p target/new-linux-env
podman run --rm --network none --userns=keep-id --user 0:0 \
  -v "$PWD:/project:ro" \
  -v "$HOME/src/nano-bootstrap:/reference-source:ro" \
  -v "$HOME/src/nano-ref:/reference-pinned:ro" \
  -v "$HOME/.rustup/toolchains/stable-x86_64-unknown-linux-gnu:/opt/rust:ro" \
  -v "$PWD/target/new-linux-env:/out" \
  localhost/naro-followup:ubuntu24 bash -c \
  'mkdir -p /work /opt/nano-locales; chown 1000:1000 /work /opt/nano-locales; exec setpriv --reuid=1000 --regid=1000 --clear-groups bash /project/tests/follow-up/environment.sh'
```

Use the actual local uid/gid in place of 1000 when necessary. The completed run
used `target/follow-up-env-user2` and reused its Ubuntu-built pinned reference
from `target/follow-up-env-v3/reference-install-tree`, mounted `/reference-built`.
The source C-file hash check is still performed. Fresh ordinary-user reference
recordings are separate from all failed root runs and original host goldens.
No Linux VT or isolated fixture-root device/browser certification was performed;
tiny remains optional and unimplemented. Tagging/publishing remains a separate
explicit action. Token usage cannot be inferred from these filesystem artifacts.

Final follow-up outcome: 48/48 gate checks, 37 verified matrix rows and four
explicit deferred rows. Ubuntu binary SHA-256:
`8f29d96f25206738212f18837e526595969c9724b7d2346b54e37bb121746f01`.
Both environments: 301/303 original terminal full matches, 51/53 new paired full
matches (all remaining differences declared), CLI 38/38 and regex 162/162.
The GitHub run for `eef679131cf1c16decd62dae2cd61ade497226bd` passed expanded CI.
Root HOME precedence remains a named out-of-scope issue, Q-ENV-ROOT-001.


## Root/home and conditional checks (2026-10-24)

Spec commit: `582cb8f`. Application implementation:
`4292ead60f1b93bc811b651a97bbfe8f46e455fd`.
Doc 20 and `data/root-console-tests.csv` track this phase. Effective-home lookup
now follows uid 0/passwd and non-root HOME rules, caches only successful results,
and is shared by config, tilde, histories and backup fallback. No-home resolution
skips cwd config/state. Tilde opening now retains the expanded filename and
preserves a double-slash suffix. All 27 new ordinary/root namespace comparisons
match. A separate source no-home tilde crash is safely handled (Q-ROOT-NOHOME-001).

Root evidence: `../validation/root-console/`. The frozen optimized binary source
fingerprint is `e3de64cd7995eccc549214783b542f5afa5e86e262b9026efb78fca5aa281ca8`.
The ordinary regression remains 301/303 full matches, CLI 38/38, regex 162/162
and passing existing safety assertions. New gates pass 16 checks. The previous
Ubuntu archives remain historical artifacts and do not include this phase's fix.

The root oracle is rebuilt from a private bootstrap copy, unchanged pinned C
sources, with `--sysconfdir=/etc`. This makes the no-home configuration-origin
label match the target instead of the old oracle's development installation
prefix. It never reads host /etc during root tests: each editor has a private
mount root. Its configure flags/source hashes are retained in the root report.

Bubblewrap is available on this machine and provides genuine namespace uids 0
and 1000, private passwd/group/NSS and null device. Backend safety guards and
readiness checks are implemented. JSON serialization now preserves invalid-UTF-8
path bytes and publishes only complete documents. Source and candidate backend
hashes are checked; editing the backend during a run fails closed.

The physical-console probe correctly records this tool's PTY as unavailable,
without touching the active Linux VT. Run `tools/console_check.py` explicitly
from an operator-owned real VT for the recorded trial; see the root validation
README. Two physical-console rows remain deferred. Native modifier/rendering
behavior is not certified until that trial and any resulting fixes. Optional
tiny remains outside this task. Host-root privilege semantics beyond the listed
namespace cases also remain untested.
