# 03 — Terminal input

Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

Scope: how terminal bytes become logical key events: terminal modes, ncurses
keypad translation and its timing, nano's own escape decoding, Escape/Meta
handling, decimal byte entry, verbatim input, bracketed paste, mouse events,
resize events, and input during prompts and external operations.

Inventory: [`data/escape-sequences.csv`](data/escape-sequences.csv) (every
sequence nano decodes itself, with the resulting code and source line).
Evidence: `evidence/runs/TEST-INPUT-*`, `TEST-KEY-*`.

**Layering.** Input passes through four layers. Layers 1–2 belong to the
terminal and ncurses. Layers 3–4 are nano's, and they are what this
specification requires.

1. **Terminal** — sends bytes. Which bytes a physical key sends depends on the emulator and its modes (application cursor keys `ESC[?1h`, keypad transmit `ESC=`, bracketed paste `ESC[?2004h`, mouse `ESC[?1000h`).
2. **ncurses keypad translation** (when enabled) — a byte string that matches a terminfo key capability of `$TERM` (`kcuu1`, `kf1`, `kLFT5`, …) and arrives completely within the ESC delay becomes one `KEY_*` code. Everything else passes through as bytes. With `--rawsequences` this layer is off.
3. **nano's burst reader** — gathers each burst of available codes into a buffer.
4. **nano's decoder** — Escape/Meta logic, its own escape-sequence tables (for sequences ncurses did not translate), and the mapping to nano's logical key codes.

A reimplementation that reads the terminal directly must reproduce the *combined*
effect of layers 2–4 for the terminal types it supports (`15-rust-architecture.md`
§4). The decisive point is that layer 2 only recognizes sequences listed in the
terminfo entry, and the rest reaches layer 4 as raw bytes.

---

## 1. Normative requirements

### INPUT-001 — Terminal modes while editing
While nano owns the screen (`terminal_init`):
- input is raw (no line buffering), CR is not translated to LF (`nonl`; Enter arrives as 0x0D, ^J as 0x0A), no echo;
- `IEXTEN` and `OPOST` are cleared; `ISIG` is cleared (^C, ^Z, ^\ arrive as bytes and do not raise signals);
- `IXON` is cleared unless *preserve* is on (then ^S/^Q control flow and do not reach nano);
- keypad mode is on (ncurses sends `smkx` = `ESC[?1h ESC=` for tmux-256color), unless `--rawsequences`;
- bracketed-paste mode is requested by writing `ESC[?2004h` (not in tiny builds);
- the escape delay is 50 ms (`set_escdelay(50)`), which overrides `ESCDELAY` from the environment;
- ncurses "typeahead" checking is disabled.
- **Temporary changes:** while reading a file or stdin, during an external command, and while writing a file, ISIG is enabled, so that ^C sends SIGINT and interrupts the operation (`08` FILE-INTR, `12` FEAT-EXEC).
- **Source:** `src/nano.c:1152-1238, 2508-2514, 820-836`.
- **Evidence:** runtime-observed (raw trace of TEST-SMOKE-001 shows `ESC[?2004h`, `ESC[?1h ESC=`).

### INPUT-002 — Bursts
nano waits (blocking) for the first code. It then collects, without waiting,
every code ncurses can deliver immediately; together these form one **burst**.
Exception: when the first code is ESC and either *rawsequences* is on or
verbatim input is in progress, it waits 20 ms before collecting the rest.
Decoding (INPUT-004) looks at what remains in the burst, so whether bytes
arrive together or separately changes their meaning (Escape vs Meta, typed text
vs pasted text).
- Typed text is inserted when a non-text key arrives or the burst is exhausted, so one burst of text is one insertion (`02` KEY-020).
- While a macro is being recorded, every code of the burst is recorded (`12` FEAT-MACRO).
- When ncurses keeps failing to deliver a code (12,345,678 consecutive errors, which happens when input is gone, e.g. the terminal hung up), nano dies with `Too many errors from stdin`.
- **Source:** `src/winio.c:190-321`.

### INPUT-003 — ncurses escape delay
With keypad translation on, an ESC followed within 50 ms by the rest of a
terminfo key string yields one key code. An ESC with nothing following within
50 ms is delivered alone. Bytes that do not complete a known key string are
delivered as they are. **Consequences (observable):**
- Alt+key (ESC x) arrives as ESC, x and is decoded as Meta by nano (INPUT-004), whatever the timing: a lone ESC followed by `x` 800 ms later is still `M-x` (TEST-INPUT-001).
- Sequences unknown to the terminfo entry arrive as raw bytes and are decoded by nano's tables (INPUT-005). Example: `ESC [ 3 ; 2 ~` (Shift+Delete) is not in tmux-256color and is decoded by nano.
- **Source:** `src/nano.c:2511-2514`; ncurses.

### INPUT-004 — Escape and Meta decoding
nano keeps three pieces of state across codes: `escapes` (0, 1 or 2),
`first_escape_was_alone`, and `last_escape_was_alone` (an ESC is *alone* when
no other code followed it in its burst). There is also the decimal-entry
counter `digits` of INPUT-006. For every code `c` taken from the buffer:

1. **c is ESC (0x1B):** shift the alone-flags (`first ← last`; `last ← (burst now empty)`). If decimal entry was in progress, cancel it and set `escapes = 1`. Otherwise increment `escapes`; if it becomes 3, reset it to 0 when this ESC was alone, and to 1 when it was not. Produce no key; read the next code.
2. **escapes == 0:** a code below 0xFF other than Tab (0x09) and DEL (0x7F) is returned **as is**: plain text and control codes. Tab, DEL, 0xFF and ncurses `KEY_*` codes go to the final mapping (INPUT-007).
3. **escapes == 1 (one ESC before c):** set escapes to 0, then:
   - c < 0x20 or c > 0x7E:
     - Tab → **Shift+Tab**;
     - Backspace (`KEY_BACKSPACE`, 0x08, 0x7F) → **Ctrl+Shift+Delete** (shown as `M-Bsp`, chop word left; not tiny);
     - another control code, when the ESC was not alone → **Meta+control** (meta flag, code < 0x20). It is never a shortcut (`02` KEY-010) and is reported as `Unbindable key: M-^X`;
     - otherwise (a lone ESC followed later by a control code, or ESC + an ncurses `KEY_*` code): c goes to the final mapping **without** the meta flag. For example, ESC then an ncurses-translated Up arrow is plain Up.
   - c printable (0x20–0x7E) and (no code follows in the burst, or the next code is ESC, or c is neither `O` nor `[`) → **Meta+c**. An upper-case letter is folded to lower case unless Shift+Meta bindings exist (`02` KEY-033).
   - otherwise (c is `O` or `[`, and more codes follow) → the escape sequence is decoded with nano's tables (INPUT-005), then mapped (INPUT-007).
4. **escapes == 2 (two ESCs before c):** set escapes to 0, then:
   - c is `[` and the next code is one of `A B C D a b c d` (iTerm2/Eterm/rxvt "double escape" arrows): consume it and return `A`→Home, `B`→End, `C`→Ctrl+Right, `D`→Ctrl+Left, `a`→Shift+PgUp, `b`→Shift+PgDn, `c`→Shift+Home, `d`→Shift+End (lower-case forms set Shift held; not in tiny).
   - c is `[` or `O`, more codes follow, and the next is not ESC → decode the escape sequence, **with the meta flag set**, then map. (Alt+F1 and similar on terminals that prefix ESC.)
   - c is a digit `0`–`2`, or `3`–`9` while decimal entry is already in progress → decimal byte entry (INPUT-006).
   - no decimal entry in progress:
     - both ESCs, *the first alone and the second not alone* (that is: Esc pressed, then a Meta key from a terminal that prefixes ESC) → **Meta+c** (folding as above);
     - otherwise → **Ctrl+c** by the classic mapping: `@`…`_` → 0x00…0x1F; `` ` ``…`~` → 0x00…0x1E (`` ` ``→0, `a`→1, …); `3`–`7` → 0x1B–0x1F; `?` and `8` → 0x7F; space and `2` → 0x00; `/` → 0x1F; any other character unchanged. Example: Esc Esc c = ^C (TEST-INPUT-002); Esc Esc g = ^G (TEST-INPUT-013).
   - The result then goes to the final mapping.
- **Source:** `src/winio.c:1008-1121, 984-1000`.
- **Evidence:** runtime-observed TEST-INPUT-001/-002/-003/-004/-013; source-confirmed.

### INPUT-005 — nano's own escape-sequence tables
When an `ESC O …` (SS3) or `ESC [ …` (CSI) sequence reaches nano undecoded, it is
matched against the tables in `data/escape-sequences.csv` (154 entries, each with
its documented terminal and resulting code). Rules:
- Matching looks only at the codes already in the burst. A sequence split across bursts is not recognized.
- The number of codes consumed is defined per pattern. Common cases: `ESC [ X` consumes 1 (a final letter); `ESC [ n ~` consumes 2; `ESC [ 1 ; m X` consumes 4; `ESC [ 2 0 0 ~` (paste start) consumes 4. The consumed codes are removed even when the result is "unknown".
- A pattern that is recognized but has no meaning yields **Unknown sequence** (`FOREIGN_SEQUENCE`, `02` KEY-025). This includes multi-modifier forms (`ESC O 4 x`, `ESC O 6…8 x`), `ESC [ 1 n ; 2 ~`, `ESC [ 2 n ; 2 ~` (F17–F24 on some terminals), and every SS3/CSI final not in the tables.
- **Special case:** a CSI sequence starting with `2` that matches no `2…` pattern consumes **all** remaining codes of the burst (TEST-INPUT-014: `ESC [ 2 0 0 x` swallowed the `x`).
- Keypad keys with NumLock off (`ESC O j/k/l/m/o`) produce the characters `* + , - /`, and `ESC O n/p/q/r/s/t/v/w/x/y` produce Delete, Insert, End, Down, PgDn, Left, Right, Home, Up, PgUp (TEST-INPUT-015).
- Shift+arrow forms (`ESC [ 1 ; 2 A-D`, `ESC O 1 ; 2 A-D`, `ESC [ a-d`) produce the arrow with Shift held.
- Tiny builds keep only a subset (entries whose build condition is `!NANO_TINY` are absent there and give Unknown sequence).
- **Source:** `src/winio.c:443-939`.
- **Evidence:** source-confirmed (table); runtime: TEST-INPUT-012 (`ESC [1;2C/D`), -014, -015, -008 (`--rawsequences`).

### INPUT-006 — Decimal byte entry (Esc Esc + three digits)
After two ESCs, a digit starts a decimal byte code. Digits are accepted while the value stays ≤ 255: the first digit must be 0–2; the second may be 0–9, but only 0–5 when the first is 2; the third likewise. After each accepted digit except the last, nothing is produced and nano stays in the "two escapes" state. When the third digit completes the value:
- value > 0x7F in a UTF-8 locale → the two-byte UTF-8 encoding of code point U+00value is produced (`Esc Esc 2 3 4` inserts `ê`, U+00EA, TEST-INPUT-003);
- value is Tab (9) or DEL (127) → passed to the final mapping (Tab key / Backspace);
- other values → that byte (a control code acts as that control key: 000 → ^@ (*nextword*), 013 → Enter);
- **a digit that would exceed 255** (e.g. the third digit of `256`) ends the entry: the digits so far are discarded and the offending digit is returned as an ordinary key (`Esc Esc 2 5 6` inserts `6`, TEST-INPUT-004).
- A non-digit after one or two accepted digits: the entry is left half-finished, and the non-digit is processed by the final mapping as an ordinary key. The next ESC cancels the half-finished entry. *(Source-derived.)*
- **Source:** `src/winio.c:941-973, 1084-1110`.

### INPUT-007 — Final mapping
After INPUT-004, the code is mapped (not tiny unless noted):
1. Codes that ncurses assigned (via `key_defined`) to the terminfo strings `kLFT5 kRIT5 kUP5 kDN5 kHOM5 kEND5` → Ctrl+Left/Right/Up/Down/Home/End (also in tiny). `kDC5` → Ctrl+Delete, `kDC6` → Ctrl+Shift+Delete. `kUP kDN` → Up/Down with Shift held. `kLFT6 kRIT6 kUP6 kDN6 kHOM6 kEND6` → the Ctrl+… code with Shift held. `kLFT3 kRIT3 kUP3 kDN3 kHOM3 kEND3 kPRV3 kNXT3 kIC3 kDC3` → Alt+Left … Alt+Delete. `kLFT4 kRIT4 kUP4 kDN4` (Shift+Alt+arrows) → Home/End/PgUp/PgDn with Shift held. When the terminal lacks one of these capabilities, nano's private code for it is used, which is only produced by nano's own tables.
2. Codes from F25 to F63 → Unknown sequence (modified function keys beyond F24).
3. **Linux console only:** the modifier state is queried. Shift+Tab, Shift+Delete, Ctrl+Shift+Delete, Shift-held for any key; Alt alone + Up/Down/Home/End/PgUp/PgDn/Delete/Insert → the Alt codes; Ctrl + arrows/Home/End/Delete → the Ctrl codes; Shift+Alt+arrows → Shift+PgUp/PgDn/Home/End. Disabled while a macro or string binding is replayed. (Source-specified only; L-2.)
4. ncurses codes: `KEY_SLEFT/SRIGHT/SR/SF` → arrows with Shift held; `KEY_SHOME`/`SEND` → Home/End with Shift held; `KEY_A1`/`KEY_C1` (keypad 7/1) → Home/End; `KEY_EOL` → Ctrl+End; `KEY_SPREVIOUS`/`KEY_SNEXT` → PgUp/PgDn with Shift held; `KEY_A3`/`KEY_C3` → PgUp/PgDn; **DEL (0x7F) and `KEY_BACKSPACE`** → Backspace, or Delete when *rebinddelete* (`-d`) is on; **`KEY_DC`** → Delete, or Backspace when *rebinddelete* is on (TEST-INPUT-007); `KEY_SDC` → Shift+Delete; `KEY_SCANCEL` → `KEY_CANCEL`; `KEY_SUSPEND`/`KEY_SSUSPEND` → ^Z (0x1A); `KEY_BTAB` → Shift+Tab.
5. Ignored (no key; reading continues): `KEY_BEG`, `KEY_SBEG`, `KEY_B2` (keypad 5), `KEY_RESIZE`, `KEY_FRESH`, and for ncurses patch levels 20230507–20231027 the focus-in/out codes.
6. The keypad operator keys `kpDIV kpMUL kpSUB kpADD` (if defined by terminfo) → `/ * - +`.
7. Everything else is returned unchanged.
- **Source:** `src/winio.c:1123-1366`; `src/nano.c:2452-2506`.

### INPUT-008 — Verbatim input (`M-V`)
In the edit window (and at prompts, `17` PROMPT-VERB):
1. `Verbatim Input` (INFO) is shown. With *zero* and the cursor on the last row, the view scrolls one line first.
2. For the next keystroke, keypad translation is turned off (so special keys arrive as raw escape sequences), bracketed paste is turned off (`ESC[?2004l`), and with *preserve* flow control is turned off. After an ESC, nano waits 20 ms for the rest of the burst.
3. The first code read decides:
   - **A hexadecimal digit, in a UTF-8 locale** → Unicode entry: up to six hex digits (case-insensitive). Space or Enter (^M) ends the entry early. While digits are pending in the edit window, INFO `Unicode Input: <digits>` shows them right-aligned in a six-character field (spaces on the left, upper-case hex). Six digits complete it. A value ≥ 0x110000, or any other key, makes the code **invalid**: when the invalid key was the start of an escape sequence, the rest of that sequence is discarded; when it was a UTF-8 lead byte, its continuation bytes are discarded. A valid value is inserted as its UTF-8 encoding (`M-V 0 0 e 9 Space` inserts `é`, TEST-INPUT-006).
   - **ESC with more codes in the burst** → ESC plus the next code are inserted (2 bytes). The remaining codes of the sequence are then processed normally: `M-V` then Up inserts `ESC O` and then types `A` (displayed `^[OA`, TEST-INPUT-006).
   - **Any other code** → that byte, with these exceptions:
     - a byte ≥ 0x80 → not inserted verbatim; it is put back and processed as normal input (so a UTF-8 character typed after M-V is simply inserted);
     - in the edit buffer, ^J (0x0A) is refused: `Invalid code`;
     - at a file-name prompt, NUL (0x00) is refused (beep), while ^J is accepted;
     - in the buffer, NUL is accepted (stored as an embedded NUL, `18` BYTE-NUL).
   - A window resize while waiting cancels verbatim input without inserting anything.
4. Afterwards keypad, bracketed paste and flow control are restored. On success the status bar is wiped. On an invalid code: AHEM `Invalid code`.
5. Verbatim input counts as a *change* (refused in view mode).
- **Source:** `src/winio.c:1386-1582`; `src/text.c:3052-3093`.
- **Evidence:** runtime-observed TEST-INPUT-006.

### INPUT-009 — Bracketed paste
The terminal wraps pasted text in `ESC [ 2 0 0 ~` … `ESC [ 2 0 1 ~`. ncurses
maps these to the codes `START_OF_PASTE`/`END_OF_PASTE` (`define_key`); if that
fails, nano's CSI table does the same (INPUT-005).
- **Edit window:** the start marker triggers *paste mode*: all following codes are read until a code that is neither a byte 0x20–0xFF (except 0x7F), nor Tab, nor CR/LF. Bytes and Tabs are collected, CR and LF start a new line, and the end marker stops collection. The collected text is pasted with the regular paste operation, as **one undoable PASTE action** (`06` UNDO-PASTE). It does not go through auto-indent, tab conversion, hard-wrapping per character or the cutbuffer; the cutbuffer is left unchanged. Tabs stay tabs (TEST-INPUT-005). In view mode: `Key is invalid in view mode`. If collection stopped at anything other than the end marker (for example ESC, or a control code such as ^K inside the paste): ALERT `Flawed paste`, and the code that stopped it is lost. NUL bytes inside a paste end the paste the same way (code 0x00 is outside the accepted set).
- **Prompts:** between the markers, every byte is inserted into the answer, including Tab (no completion), and every command key is ignored with a beep (TEST-INPUT-011).
- After inserting the collected edit-window text, the regular paste operation
  performs one hard-wrap attempt when hard wrapping is enabled and the cursor
  remains on the original line. CR/LF paste input moves to another line and
  skips this attempt. A wrapping paste undoes with `Undid paste` and redoes
  with `Redid addition`. Oracle regressions: TEST-NEXT-RELEASE-PASTE-01-BRACKETED-WRAP
  and TEST-NEXT-RELEASE-PASTE-02-P2-02-FULL in `../tests/follow-up/scenarios/release-fixes.json`.
- **Yes/No questions:** the first code after the start marker is taken as the answer, and the rest up to the end marker is discarded.
- **Help viewer and browser:** everything up to the end marker is discarded; AHEM `Paste is ignored`.
- Tiny builds have no bracketed-paste support: the markers arrive as unknown sequences and the text as typed keys.
- **Source:** `src/nano.c:1425-1462`; `src/prompt.c:451-480`; `src/prompt.c:725-730`; `src/help.c:493-496`; `src/browser.c:640-643`; `src/nano.c:2492-2496`.
- **Evidence:** runtime-observed TEST-INPUT-005, -011.

### INPUT-010 — Mouse
Enabled by `-m`/`set mouse`/`M-M` (mouse builds; never with `--rawsequences`).
When enabled, nano asks ncurses for all mouse events and sets a 50 ms click
interval. ncurses enables the terminal's mouse reporting: `ESC[?1000h` (normal
tracking) for tmux-256color, as observed in the raw trace. Only these events
matter:
1. **Button-1 click or release** (press alone does nothing; TEST-INPUT-009: the cursor moved on the release):
   - **Scroll-bar column** (rightmost column, when the indicator is shown, in the main window): go to the line `last_line * row / editwinrows + 1`, where `row` is the clicked edit row, plus one when it is not 0. The preferred column is kept; a full redraw follows.
   - **Help lines** (the two bottom rows, when shown, and not in a Yes/No question): the clicked item is computed as follows. N is the number of shown items; with N < 5 each column is `COLS/2` wide, otherwise `COLS/((N+1)/2)`. The index is `(x / width) * 2 + row` (row = 1 or 2). It is reduced by 2 when it exceeds N and `x % width < COLS % width` (the wider last items). An index beyond N is ignored. Otherwise the key of the index-th shown function is fed as input (a printable keycode gets an ESC before it, so it acts as Meta). TEST-INPUT-009: clicking under `^R Read File` opened the insert prompt.
   - A click on the status/prompt row while help lines are shown (row LINES−3) is a prompt click (`17` PROMPT-MOUSE).
   - **Edit window:** the cursor moves to the clicked row and to the column `actual_last_column` of the clicked chunk (it never goes past the end of the row). Clicking at the cursor position toggles the mark (`05` EDIT-MARK). Any other click breaks the cut chain. The viewport is updated as for movement (centering if needed).
   - **Browser:** `09` BROWSE-MOUSE. **Yes/No:** `17` PROMPT-YESNO.
2. **Wheel** (buttons 4/5, ncurses mouse version ≥ 2): in the edit window, or on the status-bar row of the bottom window, each roll scrolls two lines (two Alt+Up or Alt+Down keys, `05` EDIT-SCROLL). Rolls elsewhere are ignored.
3. All other mouse events are ignored.
- Mouse coordinates in the edit window are adjusted by the line-number margin.
- **Source:** `src/winio.c:1584-1700`; `src/nano.c:449-470, 1327-1378`.
- **Evidence:** runtime-observed TEST-INPUT-009 (X10 click in text and on a help item).

### INPUT-011 — Window resize as an input event
SIGWINCH sets a flag. When nano next asks for a key (or immediately, if it is
already waiting), the screen is regenerated (`13` SIG-WINCH) and a pseudo-key
"window resized" is produced. In the edit window it causes nothing beyond the
redraw. Prompts re-display themselves with the new width and keep the answer
and cursor. Yes/No questions are re-displayed. Verbatim input is cancelled. The
browser rereads and redraws its list. The linter re-displays its message. Search
loops redraw and continue (`Searching...` is shown).
- **Source:** `src/winio.c:221-226, 278-280`; `src/prompt.c:443-450, 621-625`.
- **Evidence:** runtime-observed TEST-INPUT-010 (help lines reflowed at 40×10 and restored at 80×24).

### INPUT-012 — Cancelling long operations with ^C
- **Searching** (find, replace, spell): about once per second, nano drains pending keystrokes without blocking. If one of them is bound to Cancel in the search context, the search stops with HUSH `Cancelled`, and the rest of the input buffer is discarded. While a search is running, `Searching...` appears after the first second (two seconds after a wrap).
- **Reading/writing files, reading stdin, running external commands:** ^C sends SIGINT (INPUT-001), which interrupts the system call or stops the command (`08`, `12`).
- **Source:** `src/search.c:272-307`.

### INPUT-013 — Timed waits for messages
In the edit window, when *minibar* or *zero* is on (or the terminal has 1 row),
and the last message has importance REMARK…MILD other than INFO, **or** a
search match is spotlighted, nano waits for the next key with a timeout:
1.5 s, or 0.8 s with *quickblank*. On timeout the message (or spotlight) is
removed, the minibar is redrawn, and nano waits again without a timeout. During
the timed wait ^C is not delivered as SIGINT (ISIG stays cleared).
- **Source:** `src/winio.c:205-250`.

### INPUT-014 — Keys with no meaning in a context
See `02` KEY-025 (edit window, browser, help) and `17` PROMPT-DISP (prompts
beep). Keys > 0xFF, Meta+control and unbound control codes are never inserted
as text.

---

## 2. Original implementation notes
- `key_buffer` is a growable array of `int` keycodes (initial capacity 32, doubled as needed). `put_back` pushes codes in front, which is used for macros, string binds, mouse-to-key conversion, Unicode/byte expansion and the "suspended" fake key.
- String-bind expansion uses a sentinel code `MORE_PLANTS` in the buffer and a pointer into the expansion string.
- Escape state lives in static variables of `parse_kbinput`.
- `KEY_FRESH` is pushed back with `ungetch` after SIGCONT, to neutralize a key-eating issue.

## 3. Evidence summary
| Requirement | Evidence |
|---|---|
| INPUT-001 | runtime (raw trace), source |
| INPUT-002/003 | source; runtime (TEST-INPUT-001 timing) |
| INPUT-004 | runtime TEST-INPUT-001/-002/-003/-004/-013, source |
| INPUT-005 | runtime TEST-INPUT-012/-014/-015, TEST-INPUT-008 (`-K`), source |
| INPUT-006 | runtime TEST-INPUT-003/-004 |
| INPUT-007 | runtime TEST-INPUT-007 (`-d`), TEST-KEY-* (modified keys); VT parts source-only |
| INPUT-008 | runtime TEST-INPUT-006 |
| INPUT-009 | runtime TEST-INPUT-005/-011; Yes/No, help, browser parts source-only |
| INPUT-010 | runtime TEST-INPUT-009 (click, help-line click); wheel, scroll bar source-only |
| INPUT-011 | runtime TEST-INPUT-010 |
| INPUT-012/013 | source; runtime tests planned (TEST-INPUT-020..) |

## 4. Open questions
- **Q-IN-001:** A Rust implementation that does not use ncurses has to reproduce ncurses' terminfo-driven translation (layer 2) and its 50 ms ESC delay to match the decoding of keys known to terminfo. Proposed decision: implement a terminfo-driven key matcher equivalent to ncurses `keypad` mode for `$TERM`, with the same timing, then feed nano's decoder. Alternatively use ncurses via FFI (`15` §4).
- **Q-IN-002:** On the Linux console, modifier detection uses `ioctl(TIOCLINUX)`. Not verified (L-2).
- **Q-IN-003:** The CSI-`2` "consume the whole burst" rule (INPUT-005) loses typed characters that share a burst with a malformed sequence. Deterministic, so it is reproduced.
