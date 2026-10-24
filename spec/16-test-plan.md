Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

# 16 — Differential test plan

The acceptance target is the default build in ENV-BASE of
[00-reference-environment.md](00-reference-environment.md). A recorded scenario
is evidence, not a passing assertion. The inherited corpus has 309 scenarios,
all recorded; only TEST-SMOKE-001 has explicit assertions (four). Ten scenarios
intentionally end with a harness SIGKILL. Their final unsuccessful `wait_exit`
steps were corrected to equal-duration `sleep` recording steps, with original
steps archived in `evidence/recording-timeout-corrections.json`; the raw reference
recordings remain unchanged. Coverage below describes observations,
not a claim that every branch has been tested.

## 1. Running and preserving evidence

Run from `spec/`. Tools require Python 3.11 or newer, tmux, terminfo, and the reference
executables. No third-party Python packages are needed.

```sh
python3 tools/nanoharness.py evidence/scenarios/smoke.json --out evidence/recheck
python3 tools/nanoharness.py evidence/scenarios/smoke.json --binary ../target/debug/naro --out evidence/naro
python3 tools/compare_runs.py evidence/runs evidence/naro TEST-SMOKE-001
python3 tools/test_inventory.py
python3 tools/test_compare_runs.py
python3 tools/audit_spec.py
```

Always supply a separate `--out` when testing a candidate. `evidence/runs` is the
original reference corpus and must not be overwritten by a candidate. The binary
may be an executable or a directory containing `nano`/`rnano`. `--profile tiny`
overrides the scenario profile. Run each full harness invocation serially:
the tmux socket is unique per scenario invocation, but the default fixture
path is per test ID.
Set `NANOSPEC_WORK` to a separate scratch directory for simultaneous runs.
The repository-level `../tools/validate_parallel.py` safely partitions all IDs
between independent processes using disjoint fixtures and one frozen executable;
its combined report verifies complete ID coverage and identical binary hashes.
Do not run a second suite over the same IDs concurrently.

## 2. Scenario format and observables

Each JSON file contains an array of scenarios (or a single object). A scenario
has `id`, `args`, optional `profile`, `argv0`, `cols`/`rows` (80/24), `term`
(`tmux-256color`), `lang` (`en_US.UTF-8`), `locpath`, `env`, `cwd` (`work`),
`umask` (`022`), `stdin`, `stdout_redirect`, `hold_tty`, `finally_kill`, and `steps`.
Environment values and argv elements expand `$FX` to the fixture root.
The launcher uses execve to set the exact `argv0` and explicit environment,
preventing Python locale coercion from changing C-locale tests. `hold_tty`
retains a descriptor to the PTY when both streams are redirected; otherwise
closing its last descriptor can deliver SIGHUP. TMPDIR defaults to a private
per-scenario `tmp` directory outside the captured fixture manifest.
Fixtures declare `dirs`, `files` (`text`, `hex` or `b64`, optional octal `mode`),
`symlinks`, `hardlinks`, `fifos`, and `chmod`.

Steps are ordered objects with one operation:

| Step | Effect |
|---|---|
| `keys: ["^X", "Enter", "M-A", "^Left"]` | Encode named keys using the scenario's terminfo |
| `text: "abc\r"` / `hex: "00ff"` | Send exact UTF-8 / hexadecimal bytes; CR is Enter, LF is Justify |
| `paste: "a\nb"` | Send bracketed paste start, bytes, end |
| `wait: {text, regex?, timeout?}` | Wait for matching screen text (default 5 seconds) |
| `settle: milliseconds`, optional `timeout` | Wait for a quiet trace and screen |
| `sleep: milliseconds` | Allow a deliberately timed transition |
| `snapshot: name`, optional `quiet` | Capture text, cell attribute runs, cursor, terminal modes |
| `resize: [cols, rows]` | Resize the private tmux window |
| `signal: "SIGTERM"` | Signal only the editor process in this fixture |
| `capture_file: path` | Record intermediate bytes, e.g. a live lock file |
| `write_file: path`, `content`, optional `mtime_offset` | Simulate another writer inside the fixture |
| `wait_exit: seconds` | Wait for editor termination |

`expect` supports exit status, file bytes/text/mode/size/type/target, absent files,
screen text/cursor/attributes, and stdout/stderr substrings. See the smoke
scenario for an example. The runner's recorded result also includes initial
and final manifests, input bytes and timestamps, stderr, optional redirected
stdout, exit status/signal, notes, and final modes derived from the raw trace.
`raw-output.bin` preserves terminal output; equal byte streams are **not** required.
Each row starts with independent SGR state, but all row captures are batched in
one tmux client to avoid torn snapshots during short-lived messages. A dead
pane is complete only after tmux provides an exit status or signal, not merely
a closed PTY. Signal names reported by older tmux are converted to numbers.
Every new result records the executable SHA-256.

## 3. Comparison contract

`compare_runs.py REF_DIR CAND_DIR [TEST_ID ...]` checks the union of IDs by
default; absent evidence and an empty selection are errors. It exits 0 for a
match, 1 for differences, 2 for invalid invocation. `--json FILE` preserves
complete structured differences. `--files-only` is a diagnostic subset and
cannot establish conformance.

Compare final exit status and signal; stdout/stderr; ordered input bytes;
initial/final fixture bytes, type, mode, symlink target and hardlink groups;
intermediate captured file bytes; snapshot names, row count, text, attributes,
cursor and modes; final screen; and `trace_final_modes`. Compare every row,
including empty rows. A missing or extra row, snapshot or fixture entry differs.
Any recorded timeout invalidates the result. Deliberate harness SIGKILL is
compared as recorded and is not an ordinary clean-exit test.

Neither argv executable paths nor wall-clock input timestamps are compared.
Retain raw traces for diagnosis of paste/keypad/mouse restoration. Distinct
terminal output sequences may have the same terminal state. No general
whitespace, Unicode normalization, case folding, message or branding tolerance
is permitted.

## 4. Normalization rules

| ID | Allowed transformation and limits |
|---|---|
| N-PID | In diagnostic text and fixture **names**, `nano.<digits>.save` becomes `nano.<PID>.save`; numbered collision suffixes remain. No other numbers are masked. |
| N-TMP | In diagnostic text and fixture names, a complete `nano.` plus six alphanumeric characters becomes `nano.XXXXXX`, preserving extensions. Ordinary saved file contents remain exact even if they contain that spelling. For the fixture-owned `home/spell-args` (TEST-FEAT-005) and `home/fmt-args` (TEST-FEAT-007) only, replace the run's actual TMPDIR (default /tmp) plus the random basename with `<TMP>/nano.XXXXXX`, preserving arguments, extension and every other byte. No other file payload is masked. |
| N-ROOT | Replace each run's actual fixture root by `<FX>` in names, diagnostics and symlink targets; recognize `!`-encoded roots in backup names. Do not replace unrelated absolute paths or data-file bytes. |
| N-LOCK | For recognizable 1024-byte `b0` lock files (including intermediate captures), zero PID bytes 24–27, user bytes 28–43 and host bytes 68–99. Preserve program/version bytes 2–11, filename bytes 108–875, modified byte 1007 and all remaining bytes. |
| N-TIME | Ignore tmux-generated timestamps in the exact `Pane is dead (status/signal …, DATE)` banner (including the truncated date on a narrow dead-pane row), absolute inode numbers, mtimes, UID/GID, input timestamps, raw byte counts/hashes and output write fragmentation. Preserve mode, link counts and inode equivalence groups. For operations requiring mtime/inode preservation, compare before/after relationships separately; this comparator does not assert those relations. |
| N-ATTR-BLANK | Ignore bold, italic, dim, blink and foreground color on an ordinary space when they do not affect its visible background. Retain background, reverse, underline, strike, hidden, and foreground when reverse is active. Never apply this rule to non-space or wide-character continuation cells. Attributes are indexed by **terminal columns**, not Unicode indices. |
| N-CURSOR-DEAD | Ignore the final dead pane's cursor visibility (tmux forcibly hides it). Preserve its position and live snapshot cursor visibility; compare `trace_final_modes.cursor_visible` to verify restoration. |

No blanket signal/crash normalization is allowed. Q-DEF-001 and Q-PROMPT-001
are declared deviations, not passing differential tests. New code should have
separate semantic assertions for the intended safe behavior.

## 5. Coverage and acceptance

See [97-coverage.md](97-coverage.md) and `data/test-runs.csv` for the baseline.
The CLI probe corpus and regex corpus are separate from the 309 terminal
scenarios. Regex acceptance requires all 81 cases in both recorded locales;
use the same C library and locale data or record the changed envelope.

Implement in layers: byte/coordinate primitives and buffer edits; CLI/input;
rendering/prompts; undo/search/replace; file metadata/locking; rc/syntax;
features/tools/history/browser; translations/signals. At each layer, run the
applicable scenario files, compare full results, investigate all differences,
and record counts with the binary revision and build flags. An assertion-free
`RECORDED` line is not a pass. Keep file-only progress separate from full-screen
parity. A release claim requires all required default-profile scenarios plus
explicit tests for deviations; tiny and credits are optional.

Remaining runtime gaps include hard-wrap chunk/undo combinations, CLI/rc merge
precedence, wheel/scrollbar/browser mouse behavior, libmagic selection, interrupted
I/O, disk-full failures, real Linux VT modifiers, rare signal reentrancy and
other libc/emulator environments. They are source-specified, not experimentally
exhausted. Do not reproduce resource exhaustion or destructive failures on the
host merely to expand coverage.

## 6. Fixture safety

Run editor tests **only** in harness-created private fixtures. HOME, state,
configuration, stub programs, input and output files must be fixture paths.
Use fixture-only symlink/hardlink targets. The runner now defaults TMPDIR to its per-scenario private scratch `tmp` directory, outside the captured `fx` manifest; scenarios can override it to `$FX/tmp` and declare `tmp` in `dirs`. Never test against real user files,
`/etc`, system devices or an unrelated process. Do not invoke arbitrary destructive
shell commands. Existing scenarios are trusted test code, not a sandbox;
review commands before use. Cleanup is restricted to the harness's own work
subtree. Keep reference sources clean and read-only in practice.

## 7. Harness limits

The harness is not a terminal emulator: tmux mediates cells and re-encodes
Unicode. Non-UTF-8 output should be checked by bytes/internal reports rather
than UTF-8 tmux cells. One glibc width table underlies comparison. Polling may
miss transient frames; use named snapshots after stable waits. Recorded
manifests inline files only up to 4096 bytes; larger files compare size/hash.
No xattr, ACL or termios snapshot is recorded. Terminal modes not represented
by tmux/trace require explicit probes. See limitations L-1 through L-7 in `00`.

Early reference results lack `initial_fixture`, `captured_files`, inode/link
metadata. Compare these fields only where reference evidence records them; new
fields cannot retroactively establish coverage. The dead-pane date banner is
tmux output, not nano output, and only its date is masked (N-TIME).

For a probe with both stdin and stdout redirected, `hold_tty: true` retains a
private controlling-terminal descriptor across redirection. This avoids a PTY
hangup before a noninteractive probe starts. Naro regex validation uses it.
