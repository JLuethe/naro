# 02 — Key bindings

Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

Scope: the set of input contexts ("menus"), key notation, the default bindings
of every context and profile, how a keystroke is dispatched in each context,
behavior for unbound or invalid keys, alternate binding profiles
(`--modernbindings`, `--preserve`, restricted, view), toggles, and rebinding
through nanorc `bind`/`unbind`.

**Authoritative tables:** [`02-keybindings-tables.md`](02-keybindings-tables.md)
(generated) and [`data/keybindings.csv`](data/keybindings.csv): one row per
(registration × context), with key notation, keycode, C function, rc function
names, help-line tag and phrase, view/restricted behavior, the profiles in which
it exists, and its build/runtime condition. These tables were extracted from the
**running, unmodified** reference executables with gdb (`tools/dump_tables.py`)
for 13 profiles and cross-referenced with the registration lines in
`src/global.c`. Their evidence status is therefore *runtime-observed +
source-confirmed*. Other inventories: `data/functions.csv` (function list:
help-line tags, help-viewer descriptions, order), `data/bindable-functions.csv`,
`data/menus.csv`, `data/toggles.csv`, `data/helplines-80cols.csv`.

Terminology:
- **keycode**: the integer a keystroke decodes to (`03-terminal-input.md`). Plain bytes 0x00–0xFF, ncurses `KEY_*` codes, and nano's private codes (0x401–0x4FE) such as `CONTROL_LEFT`.
- **meta flag**: set when the keystroke came with Alt/Meta (ESC prefix). `M-a` is keycode `'a'` with the meta flag.
- **binding**: (key notation, keycode, set of contexts, function[, toggle flag | expansion string]).
- **function list**: the ordered list of (function, contexts, help-line tag, help-viewer description, blank-line-after). It drives the help lines, the help viewer, and the validity of `bind`.
- **context** = menu = `currmenu`.

---

## 1. Normative requirements

### KEY-001 — Contexts
There are exactly 16 contexts (`data/menus.csv`):

| Context | rc name | Where active |
|---|---|---|
| MMAIN | `main` | edit window |
| MWHEREIS | `search` | Search prompt |
| MREPLACE | `replace` | Search-for-replacement prompt |
| MREPLACEWITH | `replacewith` | Replace-with prompt |
| MGOTOLINE | `gotoline` | Go-to-line prompt |
| MWRITEFILE | `writeout` | Write-file prompt |
| MINSERTFILE | `insert` | Insert-file prompt |
| MEXECUTE | `execute` | Execute-command prompt |
| MHELP | `help` | help viewer |
| MSPELL | `spell` | spell-correction prompt ("Edit a replacement") |
| MBROWSER | `browser` | file browser |
| MWHEREISFILE | `whereisfile` | search prompt in the browser |
| MGOTODIR | `gotodir` | go-to-directory prompt in the browser |
| MYESNO | `yesno` | Yes/No(/All) questions |
| MLINTER | `linter` | linter message navigation |
| MFINDINHELP | *(none)* | search prompt opened from the help viewer |

MFINDINHELP has no rc name; `all` includes it. The task brief's names MSEARCH
and MFINDINFILE do not exist in this revision (they are MWHEREIS and
MWHEREISFILE). Group names used below: **MMOST** = every context except MHELP,
MBROWSER and MYESNO; **all** (rc) = MMOST + MBROWSER + MHELP + MYESNO.
- **Source:** `src/definitions.h:254-277`, `src/rcfile.c:496-506`.

### KEY-002 — Key notation (display strings)
Each default binding has a display string, shown in help lines and the help
viewer:
- `^X`: control code (`^@`… `^_`, plus `^Space` for NUL in rc syntax; displayed `^/` for 0x1F, see below).
- `M-X`: Meta + character. Letters are shown upper-case (`M-A`), but the keycode is the lower-case letter.
- `Sh-…`, `^…`, `M-…` prefixes combined with key names for modified special keys: `Sh-Tab`, `Sh-Del`, `Sh-^Del`, `^Del`, `M-Del`, `M-Ins`, `M-Home`, `M-End`, `M-PgUp`, `M-PgDn`, `^Home`, `^End`, `M-Bsp`.
- Named keys: `Enter`, `Tab`, `Bsp`, `Del`, `Ins`, `Home`, `End`, `PgUp`, `PgDn`, `Space`, `F1`–`F12`.
- **Arrow keys:** in a UTF-8 locale they are displayed as glyphs. `◂` (U+25C2) Left, `▸` (U+25B8) Right, `▴` (U+25B4) Up, `▾` (U+25BE) Down, with the prefixes `^` and `M-` (`^◂`, `M-▴`, …). In a non-UTF-8 locale the words `Left`, `Right`, `Up`, `Down` are used (`^Left`, `M-Up`, …). This is decided at startup from the locale (`using_utf8`) and changes the stored notation, which is what an rc `bind` of another key to the same function competes with (KEY-031).
- **Go-to-line key:** displayed `^/` normally, `^-` when running on a Linux virtual console (both are keycode 0x1F).
- **Help key with modern bindings:** `^H` if the terminfo `kbs` (Backspace) string of the terminal is not `^H`, otherwise `^N` (`ENV-VT220`: kbs=^H → `^N`).
- Bindings with an empty display string exist only internally (Cancel on `KEY_CANCEL`, `KEY_CENTER`, `KEY_SIC`, paste markers, `KEY_FRESH`) and are never shown.
- **Source:** `src/global.c:761-767, 1246-1250, 1388-1431, 1440-1451`.
- **Evidence:** runtime-observed (dumps `default-utf8` vs `default-C`; `default-modern` vs `default-modern-vt220`).

### KEY-003 — Default bindings
The default bindings of every context are those in `02-keybindings-tables.md`,
in the listed order. That order is the lookup order (KEY-010) and the order in
which the first key of a function is chosen for the help lines (KEY-050). The
same key may be bound in a context more than once; only the first
registration is reachable.
- Profiles: `default-utf8` is ENV-BASE. `default-C` changes only the arrow notation (KEY-002). `default-modern*` see KEY-040. `default-preserve` see KEY-041. `default-restricted` = `default-rnano` see KEY-042. `default-view` see KEY-043. `default-saveonexit` is identical to the default. `tiny-*` see KEY-044.
- **Source:** `src/global.c:1252-1626` (`shortcut_init`).
- **Evidence:** runtime-observed (13 gdb dumps) + source-confirmed.
- **Tests:** TEST-KEY-TABLE-001 (re-dump and compare `data/keybindings.csv`), TEST-KEY-HELPLINE-* (help lines per context, see KEY-050).

### KEY-010 — Shortcut lookup
Given a keycode and the meta flag, in context C:
1. Without the meta flag, keycodes 0x20–0xFF are **never** shortcuts: they are text (KEY-020). The exception is handled by the caller: in the browser and help viewer some letters are interpreted (KEY-024).
2. With the meta flag, keycodes below 0x20 are never shortcuts (`M-^X` combinations).
3. The internal code `PLANTED_A_COMMAND` returns the function named in a string binding (KEY-034).
4. Otherwise, the first binding in list order whose context set contains C and whose keycode equals the keycode is the shortcut. **The meta flag itself is not compared**: `M-a` (keycode 0x61 + meta) matches a binding whose keycode is 0x61, and such bindings exist only as `M-` notations, because rule 1 removes plain letters.
- rc `bind` adds new bindings at the **front** of the list (KEY-031), so user bindings take precedence over defaults.
- **Source:** `src/global.c:503-533`.

### KEY-020 — Main-window dispatch
For each keystroke in MMAIN (`process_a_keystroke`):
1. A window-resize pseudo-key ends processing (the screen was redrawn, `13` SIG-WINCH).
2. A mouse event is handled (`03` INPUT-MOUSE). If the click hit a help-line item, the keystroke it was converted to is read next and processed instead.
3. Shortcut lookup (KEY-010).
4. **No shortcut:**
   - keycode < 0x20, keycode > 0xFF, or the meta flag set → *unbound key* (KEY-025);
   - else in view mode → AHEM `Key is invalid in view mode`;
   - else the byte is buffered as text. A shift-selection (soft mark) is first discarded. Consecutive text bytes are collected while more keycodes are waiting in the input buffer, then inserted in one step (`05` EDIT-INSERT).
5. Buffered text is inserted when a command arrives or no more input is waiting, so a paste of `ab^K` inserts `ab` before cutting.
6. With no shortcut, the cutbuffer accumulation chain is broken (KEY-021) and a word-completion run ends.
7. **View mode:** if the function *changes something* (list in KEY-043), AHEM `Key is invalid in view mode`, and nothing else happens.
8. **First-Backspace hint:** if the keycode is `^H` (0x08), help lines are shown, the cursor is at the very start of the buffer, and the hint has not been given yet in this session, HUSH `^W = Ctrl+W    M-W = Alt+W` is shown (four spaces between the two parts). After a Meta keystroke, the hint is never given.
9. A string binding starts its expansion (KEY-034). A toggle flips its flag (KEY-045). For the cut-from-cursor toggle, the cutbuffer chain is also broken.
10. Any function other than cut, copy, zap, record-macro and run-macro breaks the cutbuffer chain (the next cut starts a fresh cutbuffer, `05` EDIT-CUT).
11. **Shift-selection:** if the keystroke had Shift held (KEY-022) and no mark is set, a *soft mark* is set at the cursor before the function runs.
12. The function runs.
13. After the function, if a soft mark exists, Shift was not held, and either the cursor moved or the function is a cursor-movement function (`left right up down home end prevword nextword beginpara endpara prevblock nextblock pageup pagedown firstline lastline`), the mark is removed.
- **Source:** `src/nano.c:1568-1723`.
- **Evidence:** source-confirmed; runtime: TEST-CLI-028 (view mode), TEST-KEY-001 (hint, unbound messages).

### KEY-021 — Cut-chain bookkeeping
A cut (`^K`) appends to the existing cutbuffer only when the previous keystroke
was also a cut, copy, zap, macro record or macro run. Every other command, any
typed character, and any mouse click that moves the cursor resets the chain.
See `05` EDIT-CUT for the full semantics.

### KEY-022 — Shift-held keys
These keycodes (as decoded in `03` INPUT-DECODE) count as "Shift held":
Shift+arrows, Shift+Home/End, Shift+PgUp/PgDn, Shift+Ctrl+arrows/Home/End
(Ctrl+Shift+Left/Right/Up/Down/Home/End), Shift+Alt+arrows (mapped to
Shift+Home/End/PgUp/PgDn), and on a Linux console any key while Shift is
pressed. They dispatch as the unshifted function with the soft-mark behavior of
KEY-020 items 11 and 13. Indent, unindent, comment, justify, spell check and
buffer switching also set the "Shift held" state after running, so that the
selection survives them.

### KEY-023 — Prompt dispatch
Covered in `17-prompts-and-completion.md` PROMPT-DISP. In summary: plain bytes
(including Tab during a bracketed paste) are inserted into the answer. Editing
functions bound in the prompt's context edit the answer. Cancel and Enter end
the prompt. Other functions bound in the context end the prompt and are
returned to the caller (toggles such as case sensitivity are implemented this
way) or are executed.

### KEY-024 — Browser and help-viewer letter keys
In MBROWSER and MHELP, keystrokes without the meta flag and with keycode < 0x7F
are interpreted **before** the binding lookup:

| Keycode | Function |
|---|---|
| `N` | findprevious |
| `n` | findnext |
| `b`, `B`, `-` | pageup |
| ` ` (space) | pagedown |
| `w`, `W`, `/` | whereis |
| `g`, `G` | gotodir (browser builds only; also in the help viewer, where it is unbound and reports `Unbound key: g`) |
| `?` | help |
| `s`, `S` | enter |
| `e`, `E`, `q`, `Q`, `x`, `X` | exit |

All other keys go through the normal lookup. These letter meanings cannot be
changed by rebinding. In the help viewer, functions that do not apply there
report *unbound key*.
- **Source:** `src/global.c:539-572`.

### KEY-025 — Unbound and invalid keys
When a keystroke has no binding in MMAIN, MHELP or MBROWSER, the status bar
shows AHEM (the input buffer is discarded) with one of these texts, checked
in order:

| Condition | Message |
|---|---|
| unrecognized escape sequence | `Unknown sequence` |
| string bind with unknown `{name}` (KEY-034) | `Unknown function: <name>` |
| string bind with an unpaired `{` | `Missing }` |
| F1–F24 (not tiny) | `Unbound key: F<n>` |
| other keycode > 0x7F | `Unbound key` |
| meta + code < 0x20 (not tiny) | `Unbindable key: M-^<letter>` (letter = code + 0x40) |
| meta + upper-case letter while Shift+Meta bindings exist (KEY-033) | `Unbound key: Sh-M-<letter>` |
| other meta | `Unbound key: M-<character upper-cased>` |
| ESC (0x1B) without meta | `Unbindable key: ^[` |
| other control code < 0x20 | `Unbound key: ^<code+0x40>` |
| plain character (browser/help only) | `Unbound key: <character>` |

The message is wiped at the next keystroke (blank delay 1).
- **Source:** `src/nano.c:1285-1325`.
- **Evidence:** runtime-observed TEST-KEY-001 (M-^A, F13, Unknown sequence, M-~), TEST-KEY-002 (Unknown function, Missing }), TEST-KEY-009 (`z` in help).

### KEY-026 — ^Z suggestion
In MMAIN, ^Z is bound to a function that only shows AHEM `To suspend, type
^T^Z`. Suspension itself is `^T ^Z` (Execute prompt, ^Z) or a user binding of
`suspend`. The message is shown only when the first main-menu key for
*execute* is still ^T and the first Execute-menu key for *suspend* is still ^Z.
Otherwise ^Z in MMAIN does nothing visible.
- **Source:** `src/nano.c:217-225`; `src/global.c:1467`.
- **Evidence:** runtime-observed TEST-KEY-001.

### KEY-040 — Modern bindings (`-/`, `--modernbindings`)
The modern profile replaces these default registrations (contexts in
parentheses; the full list is in the appendix "Profile differences"):

| Key | Default meaning | Modern meaning |
|---|---|---|
| ^G | help (all except MHELP, MYESNO, MFINDINHELP) | findnext (MMAIN, MBROWSER, MHELP) |
| ^H | backspace (MMOST) | help (as ^G above); in MHELP: exit; on terminals whose Backspace is ^H the help key is ^N instead |
| ^Q | wherewas (MMAIN, MBROWSER, MHELP) | exit (MMAIN, MBROWSER, MHELP) |
| ^X | exit (MMAIN, MBROWSER, MHELP) | cut (MMAIN) |
| ^S | savefile | savefile (unchanged; but never removed by preserve) |
| ^W | whereis | writeout (MMAIN) |
| ^O | writeout | insert (MMAIN) |
| ^R | insert | replace (MMAIN) |
| ^D | delete (MMOST) | findprevious (MMAIN, MBROWSER, MHELP) |
| ^T | execute (MMAIN) | gotoline (MMAIN); execute moves to ^E |
| ^E | end (MMOST) | execute (MMAIN) |
| ^P | prevline | location (MMAIN) |
| ^N | nextline | — (unbound, unless it is the help key) |
| ^Y | pageup | redo (MMAIN) |
| ^V | pagedown | paste (MMAIN) |
| ^C | location (MMAIN) | copy (MMAIN) |
| ^A | home (MMOST) | mark (MMAIN) |
| ^Z | ^Z suggestion | undo (MMAIN) |

The tiny build has the same list without ^Z/^Y/^A (no undo or mark in tiny)
and with the speller on ^E.
- At a Yes/No prompt, ^X (instead of ^Q) means "No, and exit with status 2" (KEY-046).
- Modern bindings switch preserve off (`01` CLI-020/CLI-021).
- The welcome message (`01` CLI-038) is not shown, because ^G is no longer help.
- **Source:** `src/global.c:1259-1298, 1311, 1317`; `src/nano.c:2302-2304`; `src/prompt.c:784-788`.
- **Evidence:** runtime-observed (dumps; TEST-KEY-006 shows `^H Help` and `^Q Exit` in the help lines, and that ^H opens and closes the help viewer).

### KEY-041 — Preserve (`-p`, `--preserve`)
- **Bindings (command line only):** ^S → savefile (main), ^Q → wherewas (main/browser/help), ^S → speller (execute), ^Q → discardbuffer (writeout) are not registered.
- **Terminal:** XON/XOFF flow control stays enabled (the tty's IXON). ^S then stops terminal output and ^Q resumes it; neither reaches nano. During verbatim input, flow control is temporarily disabled so ^S/^Q can be entered literally.
- `set preserve` in an rcfile only has the terminal effect, because the bindings already exist when rcfiles are read. ^S/^Q are swallowed by the tty anyway, so the observable difference is limited to help texts: `^Q Discard buffer` stays visible in the Write-Out help lines (TEST-KEY-012/-011).
- With `-p -/`: modern ^S/^Q exist; Execute-menu ^S (speller) and Write-Out ^Q (discard) are missing (TEST-KEY-010); flow control is not preserved.
- **Source:** `src/global.c:1282-1287, 1319-1320, 1558-1559`; `src/nano.c:1220-1238, 1527-1564`.

### KEY-042 — Restricted mode
Registrations removed at startup in restricted mode (`-R` or an `r*`
invocation name): MWRITEFILE `M-A` append, `M-B` backup, `M-P` prepend, `^T`
browser; MINSERTFILE/MEXECUTE `^X` flip-execute and `M-F` new-buffer;
MEXECUTE `M-\` pipe. The function list also differs: in MMAIN, *Justify*
replaces *Read File* in the second help-line slot, *Execute* moves to the end
of the list (so it is not shown in the help lines), and Backup/Append/Prepend,
Browse, New Buffer and Execute Command are absent from their prompts.
Functions that stay bound but refuse to act in restricted mode (AHEM
`This function is disabled in restricted mode` plus a beep): insert file,
execute, spell check, linter, formatter, suspend. Writing under another name is
refused in the Write prompt (`08` FILE-RESTR). Tab completion of filenames is
disabled.
- **Source:** `src/global.c:806-856, 1121-1125, 1146-1149, 1181-1197, 1209-1214, 1564-1584`; `src/nano.c:205-213`.
- **Evidence:** runtime-observed (dumps; TEST-CLI-049 help lines).

### KEY-043 — View mode
Registrations removed when `-v` was given on the command line: the same as
restricted mode minus the browser key (MWRITEFILE `M-A`, `M-B`, `M-P`;
MINSERTFILE/MEXECUTE `^X`, `M-F`; MEXECUTE `M-\`). The function list lacks
New Buffer and Execute Command. In MMAIN, these functions are refused with AHEM
`Key is invalid in view mode`: savefile, writeout, enter, tab, delete,
backspace, cut, paste, chopwordleft, chopwordright, zap, cutrestoffile, execute,
indent, unindent, justify, fulljustify, comment, speller, formatter, complete,
replace, verbatim, and any typed character. At prompts the same functions are
refused with a beep (`17` PROMPT-DISP). Inside the search prompt, ^R
(flip to replace) shows `Key is invalid in view mode` and pauses 0.6 s.
- **Source:** `src/nano.c:1396-1421, 1653-1656, 1610-1614`; `src/prompt.c:550-561`; `src/search.c:150-155`.

### KEY-044 — Tiny build
The tiny build has no toggles, undo, mark, indentation, macros, anchors,
bracket matching, word count, scrolling commands, Execute menu, help viewer,
browser or rcfiles. Its full binding set is in the appendix (rows marked
`+tiny` or `tiny-*`). Notable differences: `M-N` toggles line numbers only if
line numbering is compiled in (otherwise next word), `M-D` is previous word,
`M-H` is help (unavailable), `^L` refreshes in all contexts, and `KEY_FRESH`
refreshes. The help lines show Exit/Write Out/Where Is/Previous/Cut/Location
over Refresh/Read File/Replace/Next/Paste/Go To Line (TEST-KEY-007).

### KEY-045 — Toggles
Toggles are bound in MMAIN only, except *nohelp* (`M-X`), which is bound in
every context except MHELP and MFINDINHELP. In prompts, the browser and Yes/No
questions it hides or shows the help lines immediately. Default toggle keys
(`data/toggles.csv`): `M-Z` zero, `M-X` nohelp, `M-C` constantshow, `M-N` and
`M-#` linenumbers, `M-P` whitespacedisplay, `M-Y` nosyntax, `M-S` and `M-$`
softwrap, `M-L` breaklonglines, `M-O` tabstospaces, `M-I` autoindent, `M-H`
smarthome, `M-K` cutfromcursor, `M-M` mouse.

Toggling inverts the flag, then:
- **zero:** windows are recreated and everything is redrawn; no message.
- **nohelp:** if the terminal has fewer than 5 rows (3 with zero, 4 with minibar) → AHEM `Too tiny`, and the flag is restored. Otherwise windows are recreated and redrawn.
- **constantshow:** on a 1-row terminal → `Too tiny`, flag restored. In zero mode → constantshow is forced on and zero is toggled off. Otherwise, without minibar, the status bar is wiped. **No enabled/disabled message.**
- **softwrap:** turning it off resets the first visible column to 0; a full redraw follows.
- **whitespacedisplay:** title bar redrawn plus full redraw.
- **nosyntax:** multiline-color cache recomputed; full redraw.
- **tabstospaces:** if the buffer's syntax has a `tabgives` string → AHEM `Current syntax determines Tab`, and the flag is restored.
- **mouse:** mouse reporting switched on/off.
- Then, for autoindent, breaklonglines and softwrap: if both minibar (without zero) and stateflags are on, no message; else the title bar is redrawn when stateflags is on.
- For nohelp, linenumbers and whitespacedisplay: no message when minibar, zero, or a 1-row terminal is active.
- Otherwise REMARK `<description> enabled` or `<description> disabled` (descriptions in `data/toggles.csv`; for nohelp and nosyntax, the words are inverted relative to the flag: setting *nohelp* reports `Help mode disabled`).
- **Source:** `src/nano.c:1073-1148`, `src/global.c:1486-1514, 1631-1665`.
- **Evidence:** runtime-observed TEST-KEY-008 (all messages).

### KEY-046 — Yes/No dispatch
In a Yes/No(/All) question, see `17` PROMPT-YESNO. Key facts: the
locale-specific letters of `Yy`/`Nn`/`Aa` (translated strings `Yy`, `Nn`,
`Aa`) and the ASCII letters `YyNnAa` answer. ^Y = Yes. ^N = No. ^A = All (when
offered). ^Q (or ^X with modern bindings) = No **and set exit status 2**.
Cancel (^C) = cancel. ^L redraws. `M-X` toggles help lines. Anything else beeps.
- **Source:** `src/prompt.c:658-817`.

### KEY-047 — Linter dispatch
In MLINTER the only meaningful functions are cancel/enter (leave), help,
pageup/prevblock (previous message), pagedown/nextblock (next message), and
window resize. Every other key beeps. At the first or last message, an attempt
to go further shows `At first message` / `At last message` with a beep and a
0.6 s pause (at most once per second). See `12` FEAT-LINT.
- **Source:** `src/text.c:2813-2937`.

---

## 2. Rebinding (nanorc)

### KEY-030 — Grammar
```
bind   KEY  FUNCTION   MENU
bind   KEY  "STRING"   MENU
unbind KEY             MENU
```
Words are separated by blanks (space/tab). `STRING` starts at the first `"` and
ends at the **last** `"` on the line (it may contain `"`). Errors are collected
and printed after exit (`10` RC-ERR); a faulty line is skipped. An open syntax
definition is closed first (`10` RC-SYNTAX).
- **Source:** `src/rcfile.c:740-878, 535-579`.

### KEY-031 — KEY names
1. The first character is upper-cased if it is a lower-case ASCII letter; if the first character is `^`, the second one is upper-cased instead. This normalized text is stored as the binding's display string (`m-x` → `M-x`, `^x` → `^X`).
2. Rejected as `Key name <normalized> is invalid`: names of one character (`x`, `^`) and `M-` alone.
3. Accepted forms, with their keycodes (`keycode_from_string`):
   - `^` + one character: `^/` and `^-` → 0x1F; any other character ≤ `_` (0x5F) → that code − 0x40, so `^@`=0, `^A`=1 … `^_`=0x1F, while characters below `@` give a negative code and are invalid (item 6); `` ^` `` → 0. Characters above `_` are invalid. (After normalization, `^a`…`^z` are `^A`…`^Z`.)
   - `^Space` (case-insensitive) → 0.
   - `M-` + one character: an upper-case ASCII letter is turned to lower case, others are used as is (`M-a`, `M-A` → 0x61; `M-6` → 0x36; `M-[` is accepted by the parser but is a prefix byte that can never arrive).
   - `M-Space` → 0x20; `M-Left`, `M-Right`, `M-Up`, `M-Down`, `M-Ins`, `M-Del` → ALT_LEFT … ALT_DELETE (case-insensitive).
   - `Sh-M-` + one ASCII letter (case-insensitive prefix): keycode is the **upper-case** letter, and *shifted metas* mode is turned on (KEY-033).
   - `F` + number 1–24 → `KEY_F(n)`. The number is read with `atoi`, so `F5x` is F5 and `F0`/`F25` are invalid.
   - `Ins`, `Del` (case-insensitive) → `KEY_IC`, `KEY_DC`.
   - Anything else → invalid.
4. **Not bindable:** plain arrows, Home, End, PgUp, PgDn, Tab/Enter/Backspace by name, Shift- or Ctrl-modified special keys, and plain characters. They can only be reached through the control codes they produce (`^I`, `^M`, `^H`).
5. `^[` (ESC) passes name parsing but is then rejected: `Keystroke ^[ may not be rebound`.
6. `^` + a character between 0x21 and 0x3F other than `/` and `-` (for example `^1`, `^?`) yields a negative keycode and is reported as `Key name … is invalid`. *(Source-derived; `^1` not probed.)*
- **Source:** `src/global.c:368-425`; `src/rcfile.c:755-777, 866-873`.
- **Evidence:** runtime-observed TEST-KEY-005 (errors for `^[`, `F25`, `M-`, `^`, `x`; acceptance of `M-Up`, `^space`, `m-x`, `Sh-M-a`).

### KEY-032 — FUNCTION, MENU and their validation
- FUNCTION is one of the names in the table of §2.1 (exact, case-sensitive). Unknown → `Unknown function: <name>`. Missing → `Must specify a function to bind the key to`. A STRING with no closing quote → `Argument '<rest>' has an unterminated "`.
- MENU is one of the rc names of KEY-001, or `all` (case-sensitive). Missing → `Must specify a menu (or "all") in which to bind/unbind the key`. Unknown → `Unknown menu: <name>`.
- Words after MENU are ignored.
- **Effect order for bind** (parse_binding):
  1. Every existing binding of the same keycode is removed from MENU's contexts (for `all`, from all contexts). Other contexts keep it.
  2. The contexts are limited to those where the function exists:
     - *universal* functions (left, right, home, end, prevword, nextword, delete, backspace, cut, paste, tab, enter, verbatim): MMOST + MBROWSER;
     - the nohelp toggle: (MMOST + MBROWSER + MYESNO) minus MFINDINHELP; other toggles: MMAIN;
     - refresh: all contexts;
     - a STRING: MMOST + MBROWSER + MHELP;
     - every other function: the contexts where it appears in the **function list** (`data/functions.csv` column `contexts`). This list can be narrower than the default bindings: `copy` is only in MMAIN, although `M-6` copies at prompts.
  3. If no context remains: `Function '<name>' does not exist in menu '<menu>'`. This error is **suppressed in restricted or view mode** (the binding is silently dropped), because those modes remove functions.
  4. The new binding (normalized key text, keycode, contexts, function) is put at the **front** of the list.
- **Unbind:** step 1 only, for MENU's contexts.
- A key bound by step 4 replaces the key only within the computed contexts. For example, `bind ^T zap all` removes ^T from **all** contexts (step 1 uses MENU) and then adds it to MMAIN only (step 2): ^T stops working in Write Out/Insert (browser) and Go-To-Line/Search (flip-goto).
- **Source:** `src/rcfile.c:740-878, 727-737, 215-494`.
- **Evidence:** runtime-observed TEST-KEY-002/-003/-005.

### KEY-033 — Shift+Meta bindings
Normally, Meta + upper-case letter (Alt+Shift+letter, sending `ESC A`) is folded
to the lower-case keycode, so `M-A` and `Sh-M-A` behave the same. As soon as
**any** `Sh-M-<letter>` binding is parsed, folding stops for **all** letters
for the rest of the session. `ESC A` then has keycode `A`, matches only
`Sh-M-a`-style bindings, and is otherwise reported as `Unbound key: Sh-M-A`.
- **Source:** `src/global.c:408-413`; `src/winio.c:1055-1056, 1115-1116`; `src/nano.c:1311-1312`.

### KEY-034 — String bindings (macros in rc)
`bind KEY "STRING" MENU` makes KEY inject STRING as input:
- The text is processed left to right. Ordinary bytes are fed as keycodes, one byte at a time and without the meta flag (multibyte UTF-8 characters arrive as their bytes), exactly as if typed. Control bytes in STRING act as control keys (`^M` = Enter, and so on).
- `{name}` runs the function `name` (same names as FUNCTION) at that point, through the shortcut mechanism: the function is executed **even if it is not bound in the current context**, with no availability check. `{{}` and `{}}` produce a literal `{` and `}`.
- An unknown name stops the expansion with `Unknown function: <name>`. A `{` without a closing `}` stops it with `Missing }`. Bytes before the problem have already been processed.
- Toggles can be named too (`{autoindent}`).
- During expansion the Linux-console modifier probing is muted.
- In the help viewer and the browser the binding is honored as well.
- **Source:** `src/winio.c:344-408`; `src/rcfile.c:805-816`; `src/nano.c:1665-1670`; `src/prompt.c:546-549`.
- **Evidence:** runtime-observed TEST-KEY-002 (`hello{enter}world`, `{nosuch}`, `x{cut`).

### KEY-035 — Vital functions
After all rcfiles are processed (not for `-z`), nano checks that *exit* has a key in MMAIN, MBROWSER and MHELP, and *cancel* has a key in MYESNO. The check runs only for contexts where the function is in the function list (help and browser builds). If one is missing:
stderr receives `No key is bound to function '<tag>' in menu '<menu>'.  Exiting.` followed by an empty line (the template ends in a newline and the error list adds another). Then: `If needed, use nano with the -I option to adjust your nanorc settings.`, and exit status 1. `<tag>` is the help-line tag (`Exit`, or `Close` when that is the tag) and `<menu>` the rc menu name.
- **Source:** `src/rcfile.c:1355-1374`.
- **Evidence:** runtime-observed TEST-KEY-004.

### 2.1 Bindable function names
`data/bindable-functions.csv`; aliases are interchangeable. **Bindable in**
gives the contexts to which a binding is limited (KEY-032 step 2).

| rc name | Aliases | C function / toggle | Build condition | Bindable in | Default contexts (registered functions) |
|---|---|---|---|---|---|
| `cancel` | — | `do_cancel` | — | registered contexts | MEXECUTE MFINDINHELP MGOTODIR MGOTOLINE MINSERTFILE MLINTER MREPLACE MREPLACEWITH MSPELL MWHEREIS MWHEREISFILE MWRITEFILE MYESNO |
| `help` | — | `do_help` | ENABLE_HELP | registered contexts | MBROWSER MEXECUTE MGOTODIR MGOTOLINE MINSERTFILE MLINTER MMAIN MREPLACE MREPLACEWITH MSPELL MWHEREIS MWHEREISFILE MWRITEFILE |
| `exit` | — | `do_exit` | — | registered contexts | MBROWSER MHELP MMAIN |
| `discardbuffer` | — | `discard_buffer` | — | registered contexts | MWRITEFILE |
| `writeout` | — | `do_writeout` | — | registered contexts | MMAIN |
| `savefile` | — | `do_savefile` | — | registered contexts | MMAIN |
| `insert` | — | `do_insertfile` | — | registered contexts | MMAIN |
| `whereis` | — | `do_search_forward` | — | registered contexts | MBROWSER MHELP MMAIN |
| `wherewas` | — | `do_search_backward` | — | registered contexts | MBROWSER MHELP MMAIN |
| `findprevious` | — | `do_findprevious` | — | registered contexts | MBROWSER MHELP MMAIN |
| `findnext` | — | `do_findnext` | — | registered contexts | MBROWSER MHELP MMAIN |
| `replace` | — | `do_replace` | — | registered contexts | MMAIN |
| `cut` | — | `cut_text` | — | MMOST|MBROWSER (universal) | MMAIN |
| `copy` | — | `copy_text` | — | registered contexts | MMAIN |
| `paste` | — | `paste_text` | — | MMOST|MBROWSER (universal) | MMAIN |
| `execute` | — | `do_execute` | !NANO_TINY | registered contexts | MMAIN |
| `cutrestoffile` | — | `cut_till_eof` | !NANO_TINY | registered contexts | MEXECUTE MMAIN |
| `zap` | — | `zap_text` | !NANO_TINY | registered contexts | MMAIN |
| `mark` | — | `do_mark` | !NANO_TINY | registered contexts | MMAIN |
| `tospell` | `speller` | `do_spell` | ENABLE_SPELLER | registered contexts | MEXECUTE MMAIN |
| `speller` | `tospell` | `do_spell` | ENABLE_SPELLER | registered contexts | MEXECUTE MMAIN |
| `linter` | — | `do_linter` | ENABLE_LINTER | registered contexts | MEXECUTE MMAIN |
| `formatter` | — | `do_formatter` | ENABLE_FORMATTER | registered contexts | MEXECUTE MMAIN |
| `location` | — | `report_cursor_position` | — | registered contexts | MMAIN |
| `gotoline` | — | `do_gotolinecolumn` | — | registered contexts | MMAIN |
| `justify` | — | `do_justify` | ENABLE_JUSTIFY | registered contexts | MMAIN |
| `fulljustify` | — | `do_full_justify` | ENABLE_JUSTIFY | registered contexts | MEXECUTE MMAIN |
| `beginpara` | — | `to_para_begin` | ENABLE_JUSTIFY | registered contexts | MGOTOLINE MMAIN |
| `endpara` | — | `to_para_end` | ENABLE_JUSTIFY | registered contexts | MGOTOLINE MMAIN |
| `comment` | — | `do_comment` | ENABLE_COMMENT | registered contexts | MMAIN |
| `complete` | — | `complete_a_word` | ENABLE_WORDCOMPLETION | registered contexts | MMAIN |
| `indent` | — | `do_indent` | !NANO_TINY | registered contexts | MMAIN |
| `unindent` | — | `do_unindent` | !NANO_TINY | registered contexts | MMAIN |
| `chopwordleft` | — | `chop_previous_word` | !NANO_TINY | registered contexts | MMAIN |
| `chopwordright` | — | `chop_next_word` | !NANO_TINY | registered contexts | MMAIN |
| `findbracket` | — | `do_find_bracket` | !NANO_TINY | registered contexts | MMAIN |
| `wordcount` | — | `count_lines_words_and_characters` | !NANO_TINY | registered contexts | MMAIN |
| `recordmacro` | — | `record_macro` | !NANO_TINY | registered contexts | MMAIN |
| `runmacro` | — | `run_macro` | !NANO_TINY | registered contexts | MMAIN |
| `anchor` | — | `put_or_lift_anchor` | !NANO_TINY | registered contexts | MMAIN |
| `prevanchor` | — | `to_prev_anchor` | !NANO_TINY | registered contexts | MMAIN |
| `nextanchor` | — | `to_next_anchor` | !NANO_TINY | registered contexts | MMAIN |
| `undo` | — | `do_undo` | !NANO_TINY | registered contexts | MMAIN |
| `redo` | — | `do_redo` | !NANO_TINY | registered contexts | MMAIN |
| `suspend` | — | `do_suspend` | !NANO_TINY | registered contexts | MEXECUTE MMAIN |
| `left` | `back` | `do_left` | — | MMOST|MBROWSER (universal) | MBROWSER MMAIN |
| `back` | `left` | `do_left` | — | MMOST|MBROWSER (universal) | MBROWSER MMAIN |
| `right` | `forward` | `do_right` | — | MMOST|MBROWSER (universal) | MBROWSER MMAIN |
| `forward` | `right` | `do_right` | — | MMOST|MBROWSER (universal) | MBROWSER MMAIN |
| `up` | `prevline` | `do_up` | — | registered contexts | MBROWSER MHELP MMAIN |
| `prevline` | `up` | `do_up` | — | registered contexts | MBROWSER MHELP MMAIN |
| `down` | `nextline` | `do_down` | — | registered contexts | MBROWSER MHELP MMAIN |
| `nextline` | `down` | `do_down` | — | registered contexts | MBROWSER MHELP MMAIN |
| `scrollleft` | — | `do_scroll_left` | !NANO_TINY | registered contexts | MMAIN |
| `scrollright` | — | `do_scroll_right` | !NANO_TINY | registered contexts | MMAIN |
| `scrollup` | — | `do_scroll_up` | (!NANO_TINY || ENABLE_HELP) | registered contexts | MMAIN |
| `scrolldown` | — | `do_scroll_down` | (!NANO_TINY || ENABLE_HELP) | registered contexts | MMAIN |
| `prevword` | — | `to_prev_word` | — | MMOST|MBROWSER (universal) | MBROWSER MMAIN |
| `nextword` | — | `to_next_word` | — | MMOST|MBROWSER (universal) | MBROWSER MMAIN |
| `home` | — | `do_home` | — | MMOST|MBROWSER (universal) | MMAIN |
| `end` | — | `do_end` | — | MMOST|MBROWSER (universal) | MMAIN |
| `prevblock` | — | `to_prev_block` | — | registered contexts | MBROWSER MMAIN |
| `nextblock` | — | `to_next_block` | — | registered contexts | MBROWSER MMAIN |
| `toprow` | — | `to_top_row` | !NANO_TINY | registered contexts | MMAIN |
| `bottomrow` | — | `to_bottom_row` | !NANO_TINY | registered contexts | MMAIN |
| `center` | — | `do_center` | !NANO_TINY | registered contexts | MMAIN |
| `cycle` | — | `do_cycle` | !NANO_TINY | registered contexts | MMAIN |
| `pageup` | `prevpage` | `do_page_up` | — | registered contexts | MBROWSER MHELP MLINTER MMAIN |
| `prevpage` | `pageup` | `do_page_up` | — | registered contexts | MBROWSER MHELP MLINTER MMAIN |
| `pagedown` | `nextpage` | `do_page_down` | — | registered contexts | MBROWSER MHELP MLINTER MMAIN |
| `nextpage` | `pagedown` | `do_page_down` | — | registered contexts | MBROWSER MHELP MLINTER MMAIN |
| `firstline` | — | `to_first_line` | — | registered contexts | MGOTOLINE MHELP MMAIN |
| `lastline` | — | `to_last_line` | — | registered contexts | MGOTOLINE MHELP MMAIN |
| `prevbuf` | — | `switch_to_prev_buffer` | ENABLE_MULTIBUFFER | registered contexts | MMAIN |
| `nextbuf` | — | `switch_to_next_buffer` | ENABLE_MULTIBUFFER | registered contexts | MMAIN |
| `verbatim` | — | `do_verbatim_input` | — | MMOST|MBROWSER (universal) | MMAIN |
| `tab` | — | `do_tab` | — | MMOST|MBROWSER (universal) | MMAIN |
| `enter` | — | `do_enter` | — | MMOST|MBROWSER (universal) | MMAIN |
| `delete` | — | `do_delete` | — | MMOST|MBROWSER (universal) | MMAIN |
| `backspace` | — | `do_backspace` | — | MMOST|MBROWSER (universal) | MMAIN |
| `refresh` | — | `full_refresh` | — | MMOST|MBROWSER|MHELP|MYESNO | MBROWSER MHELP MMAIN MREPLACE |
| `casesens` | — | `case_sens_void` | — | registered contexts | MREPLACE MWHEREIS |
| `regexp` | — | `regexp_void` | — | registered contexts | MREPLACE MWHEREIS |
| `backwards` | — | `backwards_void` | — | registered contexts | MREPLACE MWHEREIS |
| `flipreplace` | — | `flip_replace` | — | registered contexts | MREPLACE MWHEREIS |
| `older` | — | `get_older_item` | ENABLE_HISTORIES | registered contexts | MEXECUTE MREPLACE MREPLACEWITH MWHEREIS MWHEREISFILE |
| `newer` | — | `get_newer_item` | ENABLE_HISTORIES | registered contexts | MEXECUTE MREPLACE MREPLACEWITH MWHEREIS MWHEREISFILE |
| `dosformat` | — | `dos_format` | !NANO_TINY | registered contexts | MWRITEFILE |
| `append` | — | `append_it` | !NANO_TINY | registered contexts | MWRITEFILE |
| `prepend` | — | `prepend_it` | !NANO_TINY | registered contexts | MWRITEFILE |
| `backup` | — | `back_it_up` | !NANO_TINY | registered contexts | MWRITEFILE |
| `flipexecute` | — | `flip_execute` | !NANO_TINY | registered contexts | MINSERTFILE |
| `flippipe` | — | `flip_pipe` | !NANO_TINY | registered contexts | MEXECUTE |
| `flipconvert` | — | `flip_convert` | !NANO_TINY | registered contexts | MINSERTFILE |
| `flipnewbuffer` | — | `flip_newbuffer` | ENABLE_MULTIBUFFER | registered contexts | MEXECUTE MINSERTFILE |
| `tofiles` | `browser` | `to_files` | ENABLE_BROWSER | registered contexts | MINSERTFILE MWRITEFILE |
| `browser` | `tofiles` | `to_files` | ENABLE_BROWSER | registered contexts | MINSERTFILE MWRITEFILE |
| `gotodir` | — | `goto_dir` | ENABLE_BROWSER | registered contexts | MBROWSER |
| `firstfile` | — | `to_first_file` | ENABLE_BROWSER | registered contexts | MBROWSER MWHEREISFILE |
| `lastfile` | — | `to_last_file` | ENABLE_BROWSER | registered contexts | MBROWSER MWHEREISFILE |
| `nohelp` | — | `do_toggle / toggle `NO_HELP`` | !NANO_TINY | (MMOST|MBROWSER|MYESNO) & ~MFINDINHELP | MMAIN + all except help/findinhelp |
| `zero` | — | `do_toggle / toggle `ZERO`` | !NANO_TINY | MMAIN | MMAIN |
| `constantshow` | — | `do_toggle / toggle `CONSTANT_SHOW`` | !NANO_TINY | MMAIN | MMAIN |
| `softwrap` | — | `do_toggle / toggle `SOFTWRAP`` | !NANO_TINY | MMAIN | MMAIN |
| `linenumbers` | — | `do_toggle / toggle `LINE_NUMBERS`` | !NANO_TINY && ENABLE_LINENUMBERS | MMAIN | MMAIN |
| `whitespacedisplay` | — | `do_toggle / toggle `WHITESPACE_DISPLAY`` | !NANO_TINY | MMAIN | MMAIN |
| `nosyntax` | — | `do_toggle / toggle `NO_SYNTAX`` | !NANO_TINY && ENABLE_COLOR | MMAIN | MMAIN |
| `smarthome` | — | `do_toggle / toggle `SMART_HOME`` | !NANO_TINY | MMAIN | MMAIN |
| `autoindent` | — | `do_toggle / toggle `AUTOINDENT`` | !NANO_TINY | MMAIN | MMAIN |
| `cutfromcursor` | — | `do_toggle / toggle `CUT_FROM_CURSOR`` | !NANO_TINY | MMAIN | MMAIN |
| `breaklonglines` | — | `do_toggle / toggle `BREAK_LONG_LINES`` | !NANO_TINY && ENABLE_WRAPPING | MMAIN | MMAIN |
| `tabstospaces` | — | `do_toggle / toggle `TABS_TO_SPACES`` | !NANO_TINY | MMAIN | MMAIN |
| `mouse` | — | `do_toggle / toggle `USE_MOUSE`` | !NANO_TINY && ENABLE_MOUSE | MMAIN | MMAIN |

Names that exist in the man page but **not** in this table are not bindable.
The toggle names are `nohelp zero constantshow softwrap linenumbers
whitespacedisplay nosyntax smarthome autoindent cutfromcursor breaklonglines
tabstospaces mouse`. A name that is neither a function nor a toggle falls
through to the toggle lookup and is reported as `Unknown function: <name>`.

---

## 3. Help lines and help-viewer listing

### KEY-050 — Which items appear in the help lines
For context C at width COLS:
1. `maximum = ((COLS + 40) / 20) * 2` (integer division). The number of items is the count of function-list entries registered for C, scanning in order until `maximum` entries have been counted. **Entries without a key are counted** but not drawn, so an unbound function still takes a slot.
2. Special case MWRITEFILE: if the scan reached the end of the list and the context has no key for *discardbuffer*, the count is decreased by one.
3. Entries are drawn in function-list order, skipping those with no key in C, until the count is reached. The key shown is the **first** key in lookup order bound to that function in C with a non-empty display string. User bindings are first (KEY-031), so `bind ^Q cut main` makes the help line show `^Q Cut` (TEST-KEY-002).
4. The tag is the function-list tag, translated. For *exit* in MMAIN it is `Exit` when one buffer is open and `Close` when several are (changes as buffers open and close).
5. Layout: `03`/`04` REND-HELPLINES.
- **Source:** `src/global.c:483-501`; `src/winio.c:2438-2491`; `src/files.c:59-60, 626-628`.
- **Evidence:** runtime-observed: `data/helplines-80cols.csv` was computed from the dumps by this algorithm and matches every screen captured so far (TEST-SMOKE-001, TEST-CLI-*, TEST-KEY-*).

### KEY-051 — Help-viewer key listing
`12` FEAT-HELP specifies the help text. Each function of the context's function
list is listed with its first and second keys (in lookup order). In the main
menu, the toggles are appended in flag order with their first MMAIN key.
Rebinding therefore changes the help text.

---

## 4. Original implementation notes
- Two singly linked lists: `sclist` (keystruct: keystr, keycode, menus bitmask, func pointer, toggle, expansion) and `allfuncs` (funcstruct: func, menus, tag, phrase, blank_after). Function identity is the C function pointer; several dummy functions (`case_sens_void`, `flip_replace`, `to_files`, …) exist only as identities for prompt dispatch.
- `exitfunc` points at the MMAIN *exit* entry so its tag can be swapped between `Exit` and `Close`.
- `first_sc_for(menu, func)` = first matching keystruct with a non-empty keystr.
- A Rust implementation may use any representation (for example a per-context map plus an ordered list for help-line order), provided lookup order, the "first key" choice, and the rc semantics are preserved.

## 5. Evidence summary
| Requirement | Evidence |
|---|---|
| KEY-001, KEY-002, KEY-003 | runtime (13 gdb dumps), source |
| KEY-010, KEY-020 | source; runtime TEST-KEY-001/-002, TEST-CLI-028 |
| KEY-024, KEY-025 | runtime TEST-KEY-001/-009, source |
| KEY-026 | runtime TEST-KEY-001 |
| KEY-040…043 | runtime (dumps, TEST-KEY-006/-010/-011, TEST-CLI-049), source |
| KEY-044 | runtime (tiny dumps, TEST-KEY-007) |
| KEY-045 | runtime TEST-KEY-008 |
| KEY-046, KEY-047 | source; runtime tests in `17`/`12` |
| KEY-030…035 | runtime TEST-KEY-002…005, source |
| KEY-050 | runtime (screens vs computed tables) |

## 6. Open questions
- **Q-KEY-001:** `bind KEY "{function}"` runs functions in contexts where they make no sense ("Strange behavior or even a crash can result", `nanorc.5`). Which combinations crash is not inventoried. Proposed decision: the reimplementation must not crash; a function inapplicable to the current context does nothing.
- **Q-KEY-002:** whether `set preserve` (rcfile) leaving the ^S/^Q bindings in place is intended. Reproduce as specified.
- **Q-KEY-003:** Linux-console-specific behavior (`^-` notation, modifier probing via `TIOCLINUX`, no `M-Left`/`M-Right` buffer switching on a VT) was not runtime-verified (L-2).
