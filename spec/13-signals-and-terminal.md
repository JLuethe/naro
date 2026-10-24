# 13 — Signals, terminal state, and abnormal exit

Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

Scope: terminal mode setup and restoration, the signals nano handles, emergency
saving, the crash handler, suspend and continue, resize, and exit status.
Evidence: `evidence/runs/TEST-SIG-001…010`, TEST-FEAT-016, TEST-INPUT-010,
TEST-CLI crash probe (Q-DEF-001), CLI-P die probes. All signals in tests were
sent only to the nano process under test; all files were fixture files.

---

### SIG-TERM-INIT — Terminal setup
1. Before curses: if stdout is not a tty → die `Standard output is not a terminal` (`01` CLI-040). If `TERM` is unset, `TERM=vt220` is put into the environment. `initscr()` failure → exit 1 without a message (ncurses prints its own).
2. The original termios of stdin is saved at startup (and again after reading stdin data from a pipe, when stdin is reconnected to `/dev/tty`; failure → die `Could not reconnect stdin to keyboard`).
3. `terminal_init` (at start, after a tool, after resume): curses `raw`, `nonl`, `noecho`; termios `IEXTEN` and `OPOST` off; `ISIG` off (so ^C, ^\, ^Z are plain keys); `IXON` **on only with `-p`/preserve** (in raw mode it is otherwise off, so ^S/^Q reach nano); then write `ESC[?2004h` (bracketed paste on; not in tiny).
4. Other input settings: keypad on for the edit and prompt windows (unless `-K`), `typeahead(-1)`, ESC delay 50 ms, mouse via `ESC[?1000h` when enabled (`03`).
5. `NO_COLOR` in the environment suppresses the default spotlight and error colors (`04` REND-050).
- **Source:** `src/nano.c:1152-1240, 2155-2175, 2495-2515, 840-853`.

### SIG-TERM-RESTORE — Restoring the terminal
On any exit path (normal, die, suspend, before tools that need the terminal):
cursor visible (`curs_set(1)`), `endwin()`, write `ESC[?2004l` to stdout (even
when stdout is not a terminal in the die path — 8 bytes, `01` CLI-041), then
restore the saved termios (`TCSANOW`). Mouse reporting is turned off before
suspending. TEST-SIG-001…010 final trace modes: cursor visible, not on the
alternate screen, bracketed paste off, keypad transmit off.
- **Source:** `src/nano.c:229-239`.

### SIG-IGN — Ignored signals
SIGINT and SIGQUIT are ignored (`SIG_IGN`) while editing (TEST-SIG-005: both
sent, nano kept running and exited normally with 0). While reading stdin data,
while a search runs, and while an executed command runs, a temporary SIGINT
handler is installed with ISIG on: ^C then sets a "cancelled" flag (reading
stdin, searching) or kills the command (`12` FEAT-EXEC).
- **Source:** `src/nano.c:814-838, 908-918`.

### SIG-EXIT — SIGHUP and SIGTERM
Handled by `die("Received SIGHUP or SIGTERM\n")`:
1. A second call to die exits immediately with status **11**.
2. Restore the terminal (SIG-TERM-RESTORE). Print the rcfile errors, if any (`10` RC-ERR). Print the message to stderr.
3. **Emergency save** (SIG-EMERG) for every buffer in the ring, starting with the current buffer and going forward (TEST-SIG-006: `b.txt.save` first, then `a.txt.save`). Each buffer's lock file is deleted first (TEST-SIG-008: the `.f.txt.swp` that existed during editing was gone after exit).
4. Exit with status **1** (TEST-SIG-001…004, -006, -008…-010). Unmodified buffers produce only the message (TEST-SIG-009, view mode TEST-SIG-010).

### SIG-EMERG — Emergency save files
For a **modified** buffer, when not in restricted mode (TEST-SIG-004: no file written):
- Base name: the buffer's filename as given (relative names are relative to the current directory at that moment), or `nano.<pid>` for a nameless buffer (TEST-SIG-002: `nano.372293.save`; Q-DOC-001: the man page says `nano.save`).
- Target: base + `.save`; if that exists (by `stat`), base + `.save.1`, `.save.2`, … up to `.save.99999` (TEST-SIG-003: `f.txt.save` existed → `f.txt.save.1`). When all exist: stderr `\nToo many .save files\n` and no file.
- Written in SPECIAL mode (`08` FILE-WRITE: no backup, no lock, the buffer's format and BOM, no status messages) as a new file created with mode **0600** (TEST-SIG-001/-003/-006 mode 0o600). The buffer's contents including the final newline rule apply (TEST-SIG-001: `abcx\n`).
- Success: stderr `\nBuffer written to <target>\n`. Failure: the write-failure text goes nowhere visible (statusline output after endwin is lost), and no message is printed.
- **Source:** `src/nano.c:326-391`; `src/files.c` (get_next_filename).

### SIG-CRASH — SIGSEGV and SIGABRT
Unless `NANO_NOCATCH` is set in the environment (or a DEBUG build), a handler
with `SA_RESETHAND` calls `die("Sorry! Nano crashed!  Code: %d.  Please report
a bug.\n", signal)`, so modified buffers are emergency-saved and the exit status
is 1 (observed with `nano +r/( file`, Q-DEF-001: `Code: 11`). The handler is
reset, so a second fault kills the process with the signal.
- **Requirement for the Rust version:** the same handler semantics apply to *panics*: a panic must restore the terminal, print `Sorry! Nano crashed!  Code: <n>.  Please report a bug.` and emergency-save modified buffers, then exit 1. The reference defect itself (crash on that regex) must **not** be reproduced (99 Q-DEF-001).
- **Source:** `src/nano.c:940-965`.

### SIG-SUSPEND — Suspend (SIGTSTP, `^T ^Z`)
- In the main menu `^Z` alone is not suspend: it shows AHEM `To suspend, type ^T^Z` (TEST-SIG-007 s1) — shown only when ^T is bound to Execute in MMAIN and ^Z to suspend in MEXECUTE (with other bindings the message is not shown). Suspending is done with *suspend* (`^T ^Z`, or a key bound to `suspend`). Refused in restricted mode.
- Suspending (also on an external SIGTSTP, which the handler catches with all signals blocked): mouse off, restore the terminal, print `\n\n` and `Use "fg" to return to nano.\n` to stdout, then `kill(0, SIGSTOP)` (the whole process group).
- **SIGCONT:** mouse re-enabled if on; the resize flag is set so the next input returns a resize event (full re-init and redraw, as SIG-WINCH), and a fake `KEY_FRESH` is pushed to wake input. TEST-SIG-007: after SIGCONT the screen was redrawn and `^X` exited normally (status 0). The tiny build calls `terminal_init` directly instead.
- **Source:** `src/nano.c:215-227, 967-1021`.

### SIG-WINCH — Window resize
- The handler only sets flags. The input routine returns a resize event when the flag is set (`03` INPUT-010), and `regenerate_screen` then: `endwin()` + `refresh()` so ncurses re-reads LINES/COLS; recomputes the indicator (LINES > 5 and COLS > 9) and the edit width; `terminal_init`; recreates the windows; and redraws everything (`04` REND-071; TEST-INPUT-010).
- SIGWINCH is blocked while an external program (tool) runs and while reading its output; a resize during that time is processed afterwards.
- With `LINES`/`COLUMNS` in the environment, ncurses uses them (`01` CLI-043); resizes then do not change the size.
- **Source:** `src/nano.c:896-906, 1023-1071`.

### SIG-STATUS — Exit status summary
| Path | Status |
|---|---|
| Normal exit (`^X`, all buffers closed) | 0 |
| Last buffer closed by answering `^Q` (or `^X` with modern bindings) at `Save modified buffer?`, or `^Q` (*discard buffer*) at the exit Write prompt | **2** (TEST-SIG-011, -012). The status is reset to 0 at every main-loop iteration, so it only survives when that buffer was the last one (TEST-SIG-013: exit 0). `^N` (No) gives 0 (TEST-SIG-014). |
| Option errors, `-h`/`-V` | `01` CLI-030/-040 (0 for help/version, 1 for errors) |
| die (any fatal error, SIGHUP/SIGTERM, crash) | 1 |
| die called while dying | 11 |
| Emergency-save failure | still 1 |

- **Source:** `src/prompt.c:783-788`, `src/files.c:2108-2112`, `src/nano.c:2745`.
- **Evidence:** runtime TEST-SIG-*, TEST-CLI-*.

## Original implementation notes
- `the_window_resized` (sig_atomic_t) and `resized_for_browser`; `KEY_FRESH` and `THE_WINDOW_RESIZED` are internal key codes.
- `original_state` (struct termios).

## Evidence summary
| Requirement | Evidence |
|---|---|
| SIG-TERM-INIT/RESTORE | trace modes in all runs, CLI-P die probes |
| SIG-IGN | runtime TEST-SIG-005 |
| SIG-EXIT/EMERG | runtime TEST-SIG-001…004, -006, -008…-010 |
| SIG-CRASH | runtime crash probe (Q-DEF-001) |
| SIG-SUSPEND | runtime TEST-SIG-007, TEST-FEAT-016 |
| SIG-WINCH | runtime TEST-INPUT-010 |

## Open questions
- **Q-SIG-001:** The emergency save uses the buffer name as given, relative to the current directory. except for the startup `-o` chdir, nano keeps its working directory fixed. Resolve the name against that resulting directory. See FILE-OPDIR.
- **Q-SIG-002:** The Rust panic handler is a deliberate equivalent of SIG-CRASH (no reference panic exists).
