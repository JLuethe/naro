# 98 — Progress log

Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

This file lets a later session resume without the earlier conversation.
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
locks; narrow normalization documented in 16. Eleven regression tests pass;
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
