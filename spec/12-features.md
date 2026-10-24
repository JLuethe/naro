# 12 — Features: justify, tools, macros, histories, help

Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

Scope: paragraph justification (FEAT-PARA/QUOTE/JUST), the spell checker
(FEAT-SPELL), linter (FEAT-LINT), formatter (FEAT-FORMAT), the Execute prompt
and filters (FEAT-EXEC), macros (FEAT-MACRO), cursor position and word count
(FEAT-POS), search/replace/execute histories (FEAT-HIST), the position log
(FEAT-POSLOG), the help viewer (FEAT-HELP), restricted mode (FEAT-RESTRICT),
build features (FEAT-BUILD), and the credits (FEAT-CREDITS).

Inventory: [`data/build-features.csv`](data/build-features.csv). Evidence:
`evidence/runs/TEST-FEAT-001…020`. External programs in tests are **stubs**
placed in the fixture's `bin/` (first in PATH); TEST-FEAT-010 used the host's
hunspell (which has no dictionary installed) on purpose.

---

## 1. Justification (ENABLE_JUSTIFY; absent in tiny)

### FEAT-QUOTE — Quote and indentation parts
- The **quote part** of a line is the match of the quoting regex (`quotestr`, default `^([ \t]*([!#%:;>|}]|//))+`) when it starts at offset 0; otherwise empty. The **indentation** is the run of blanks after the quote part. "Lead" = quote + indentation.
- A line is **in a paragraph** (`inpar`) when it has text after its lead.
- **Source:** `src/text.c:1460-1543`.

### FEAT-PARA — Paragraph boundaries
A line L is the beginning of a paragraph (BOP) when:
1. L is the first line of the buffer; or
2. (not if L has no text) `bookstyle` is on, autoindent off, and L starts with a blank; or
3. L's quote part differs from the previous line's (length or bytes); or
4. the previous line has no text; or
5. the indentation widths (in columns, after the quote) of L and its predecessor differ **and** the predecessor is not itself a BOP (recursively, limit depth 222, past which "not a BOP").
Lines without text are never BOPs. A paragraph is a BOP plus the following
in-paragraph lines up to the next BOP or text-less line.
- Consequence (TEST-FEAT-001): `␣␣Lorem…` / `␣␣Second line of` / `the paragraph.` → the first two lines form one paragraph (equal indentation), and `the paragraph.` starts a new one (different indentation, predecessor not a BOP). This "first-line indent" rule means a paragraph whose second line is indented differently from its first stays one paragraph only when the first line is the BOP.
- *Paragraph begin/end* movement (`05` EDIT-068) uses the same rule.
- **Source:** `src/text.c:1489-1532`; `src/move.c` (do_para_begin/end).

### FEAT-JUST — Justify (`^J`, F4), full justify (`M-J`)
1. **Target width** `wrap_at`: `fill` > 0 → `fill`; `fill` ≤ 0 → `COLS + fill` (default `fill` −8), minimum 0 (`01` CLI-024). Line numbers reduce the available width (`04`).
2. **Paragraph choice (no mark):** if the cursor line is in a paragraph and not its BOP, go back to the BOP. Then search forward from there for the first in-paragraph line (`find_paragraph`). None: cursor goes to the end of the last line and nothing else happens (no undo item, no message change). Full justify starts at the top and treats every paragraph to the end.
3. **Per paragraph:** the *sample line* is the second line (or the only line). Its lead becomes the lead of every output line except the first, which keeps its own lead. All lines are concatenated: each next line's lead is dropped, and if the accumulated line doesn't end with a space, one space is added between them. Then **squeeze** (after the first line's lead): every run of blanks → one space; after a character from `punct` (default `!.?`), optionally followed by one from `brackets` (default `"')>]}`), **up to two** blanks are kept as spaces and the rest dropped; trailing spaces are removed (TEST-FEAT-003: `two.   three` → `two.  three`).
4. **Rewrap:** while the line is wider than `wrap_at`, break it with `break_line` (`05` EDIT-015 rules) at the last blank that fits after the lead, and if none fits, at the first blank after it (an unbreakable word stays long). The new line = sample lead + text after the break point's blank run. **Without `trimblanks`** the line being broken keeps exactly one trailing blank — the first blank of the run at the break (TEST-FEAT-001 file: `amet,␣`, `tempor.␣`). With `-M`/`trimblanks`, the trailing blanks are removed (TEST-FEAT-003).
5. **Cursor:** after justifying one paragraph, the cursor goes to the start of the line after the paragraph (or the end of the last line). After full justify, it returns to column 0 of the line number it was on. `placewewant` = the cursor column.
6. **Undo:** one combined item `justification` (COUPLE_BEGIN, CUT, PASTE, COUPLE_END); messages `Undid justification`/`Redid justification` (TEST-FEAT-001 s04). The buffer is marked modified even if nothing changed.
7. **Messages:** `Justified paragraph` (plain statusbar), `Justified file` (REMARK), `Justified selection` (REMARK).
8. **Marked region:** the region is treated as one paragraph. An empty region → AHEM `Selection is empty`. If it starts inside the lead, the start moves to column 0; blanks before the start are excluded; if it ends inside a lead, the end moves to the end of that lead; blanks after the end are included. The first-line lead is that of the paragraph containing the region start (its first text line); the later-line lead is that first line's quote + the next line's indentation. If the region started mid-line, the justified text begins on a new line; if it ended before the end of a line, a new line with the first-line lead follows. Mark and cursor are swapped back when the region was marked backward.
9. In view mode: `Key is invalid in view mode`. Restricted mode does not affect justify.
- **Source:** `src/text.c:1397-1458, 1545-2040`.
- **Evidence:** runtime TEST-FEAT-001 (three ^J then undo), -002 (M-J with quoted paragraph merged and wrapped with `> ` lead), -003 (trimblanks, punctuation spacing).

## 2. External tools

### FEAT-TEMP — Temporary file for tools
The spell checker and formatter write the buffer (or region) to a temp file:
the first writable directory of `$TMPDIR`, `P_tmpdir` (`/tmp`), else `/tmp/`;
name `nano.XXXXXX<ext>` where `<ext>` is the buffer's filename extension (the
last `.…` of the name, if no `/` follows it). Created with `mkstemps` (mode
0600). It is written in SPECIAL mode (no backup, no lock, no file-format
conversion other than the buffer's format, no notes). On failure: ALERT
`Error writing temp file: <reason>`. The file is removed afterwards.
- **Evidence:** TEST-FEAT-005/-007 (`/tmp/nano.XXXXXX.txt` as last argument).
- **Source:** `src/files.c:1414-1455`; `src/text.c:2548-2591, 2957-2992`.

### FEAT-SPELL — Spell checking (`^T` then `^T`/`^S` at the Execute prompt; F12)
Refused in restricted mode (FEAT-RESTRICT). With a mark, only the region is checked.
**Alternate speller** (`-s CMD`/`set speller`, non-empty):
1. The command is split on single spaces (no quoting; empty fields skipped) and the temp file name is appended as the last argument; run with `execvp` in the terminal after `endwin` (curses suspended), SIGWINCH blocked while waiting.
2. The temp file being empty: AHEM `Selection is empty` (mark) or `Buffer is empty`, and nothing runs.
3. Exec failure → child exit 9. Exit status > 2 or a signal: ALERT `Error invoking '<argv0>'`, stop. Status 1–2: ALERT `Program '<argv0>' complained`, continue.
4. If the temp file's mtime (sec+nsec) is unchanged: REMARK `Nothing changed` and stop (TEST-FEAT-005 first run).
5. Otherwise the buffer (or region) is replaced by the file's contents as one undo group `spelling correction` (TEST-FEAT-005: `Undid/Redid spelling correction`), the cursor returns to its line/byte position (clamped; at end of line if it was), the mark is restored for a region. REMARK `Finished checking spelling`.
**Internal speller** (no alternate speller):
1. Status `Invoking spell checker...`. Pipeline: `hunspell -l` (if exec fails, `spell`) reading the temp file → `sort -f` → `uniq`. Curses is suspended while reading the output.
2. For each output line (a misspelled word; CR or LF separated): search for its first **whole-word, case-sensitive, literal, forward** occurrence from the top of the buffer (or region start). Not found: ALERT `Unfindable word: <word>`, 2.8 s pause, continue. Found: spotlight it, show the prompt `Edit a replacement` **prefilled with the word**, cursor at its end (TEST-FEAT-004 typing appended to the word: `tehthe`). Cancel → stop all checking. Enter with a different word → replace loop over whole-word occurrences with Yes/No/All prompts (`07` SRCH-007), then statusbar `Next word...` with a 0.4 s pause. Enter with the same word → next word.
3. Afterwards the search flags are restored and the exit statuses are checked in order uniq, sort, spell: non-zero → ALERT `Error invoking 'uniq'`/`'sort'`/`'spell'` (the word `spell` is used even when hunspell ran; TEST-FEAT-010). Otherwise REMARK `Finished checking spelling`.
- **Source:** `src/text.c:2110-2245, 2247-2591`.
- **Evidence:** runtime TEST-FEAT-004, -005, -010.

### FEAT-LINT — Linter (`^T ^Y` at the Execute prompt)
1. Restricted → refused. No syntax, or syntax without a non-empty `linter`: AHEM `No linter is defined for this type of file` (TEST-FEAT-011).
2. The mark is cleared. If the buffer is modified: YESORNO `Save modified buffer before linting?` — Cancel → `Cancelled`; Yes → write (failure stops linting).
3. Status `Invoking linter...`. The command is split on spaces, the buffer's **filename as given** is appended (TEST-FEAT-006: `--flag f.txt`), and it runs with stdout+stderr into a pipe (curses stays active).
4. Output parsing, per CR/LF-separated line: `FILENAME:LINE:COLUMN: MESSAGE` where the field after the second colon is read up to the first space; `:COLUMN` may be missing or written `LINE,COLUMN`. Lines without a space, without a second field, or with LINE ≤ 0 are ignored (TEST-FEAT-006 `garbage line`). The message is the text after the **first space** of the line. Column ≤ 0 → 1.
5. Exit status > 2 or a signal → ALERT `Error invoking '<linter command>'`. No messages → REMARK `Zero messages from '<linter command>'`.
6. **Linting mode:** help lines are forced on (if hidden and LINES > 5); title bar `Linting -- <file>` (TEST-FEAT-006); the MLINTER menu. For each message: if FILENAME exists and is a different inode from the current buffer, nano switches to an open buffer with that inode, or asks `This message is for unopened file <name>, open it in a new buffer?` (Yes → open; No → drop all messages for that file, REMARK `No messages for this file` if none remain; Cancel → `Cancelled`, stop). A FILENAME that cannot be stat-ed is treated as the current buffer (TEST-FEAT-006 `other.txt`). The cursor goes to LINE and display column COLUMN−1, centered; the message is shown as NOTICE.
7. Keys: PgDn / `^V` / next-block → next message; at the last: statusbar `At last message`, beep, 0.6 s pause (at most once per second). PgUp / `^Y` / prev-block → previous (`At first message`). `^G` help. Cancel or Enter → leave. Others beep. Resize is handled.
8. On leaving, the help-line state is restored.
- **Source:** `src/text.c:2606-2955`.
- **Evidence:** runtime TEST-FEAT-006, -011.

### FEAT-FORMAT — Formatter (`^T ^O`)
Restricted → refused. No `formatter` in the syntax → AHEM `No formatter is
defined for this type of file`. The mark is cleared, the whole buffer is
written to a temp file (FEAT-TEMP), status `Invoking formatter...`, the program
runs **without leaving curses mode** (its terminal output is wiped by a full
refresh), arguments as for the alternate speller (TEST-FEAT-007: `-x
/tmp/nano.XXXXXX.txt`). Status handling as FEAT-SPELL steps 3–5, with the undo
group `formatting` and the final REMARK `Buffer has been processed`
(TEST-FEAT-007 then `Undid formatting`).
- **Source:** `src/text.c:2957-2992`.

### FEAT-EXEC — Execute command (`^T`)
1. Restricted → refused (TEST-FEAT-012). Otherwise the Insert-File prompt in "execute" mode: `Command to execute` (+ ` in new buffer` when the newbuffer toggle is on, `M-F`; TEST-FEAT-017). The Execute menu also gives `^T`/`^S` spell, `^Y` linter, `^O` formatter, `^J` full justify, `^V` cut till end, `^Z` suspend, `M-\` pipe (inserts `|` at the start of the answer, TEST-FEAT-017 s05), `^X` back to Read File, Up/Down history (FEAT-HIST). These run the function on the buffer instead of a command.
2. The command runs as `$SHELL -c CMD` (`/bin/sh` if SHELL is unset), stdout+stderr captured. Status `Executing...`. `^C` sends SIGINT to the command (the terminal's interrupt key is re-enabled while it runs).
3. **Filter:** a command starting with `|` gets the marked region, or else the whole buffer, on stdin (via a separate sender process) and its output **replaces** that text (undo group `filtering`). `||CMD` lets stdout go to the terminal (only stderr is captured). In a new buffer (`M-F`), the previous buffer's region/whole text is piped, and the output goes into the new buffer.
4. Output is inserted at the cursor (or into a new buffer) like an inserted file named `pipe` (`08` FILE-READ messages, e.g. `Read 1 line`). After a filter, the cursor goes to the start of its original line.
5. Command failure (non-zero status or signal): ALERT `Error: <text after the first ": " in the last inserted line>` or `Error: ---`; killed by a signal → ALERT `Cancelled`. Sender failure → `Piping failed`. After an ALERT the operation is undone and the undo item discarded.
6. Successful commands go into the execute history.
- **Source:** `src/files.c:973-1140, 1344-1349`, insert_a_file_or (`src/files.c`).
- **Evidence:** runtime TEST-FEAT-017 (new buffer `echo hi`, `|rev` filter into new buffer, filter in place), -012.

## 3. Macros

### FEAT-MACRO — Record (`M-:`) and run (`M-;`)
- `M-:` toggles recording. Starting: REMARK `Recording a macro...`; the previous macro is kept aside. The state flag `R` appears in the title bar with `stateflags` (`04`).
- Every key code read while recording is appended, including all codes of a burst. The codes of the `M-:` that stops the recording are removed (the buffer is cut back to where the latest burst began).
- Stopping with nothing recorded: the previous macro is restored, REMARK `Cancelled` (TEST-FEAT-009). Otherwise REMARK `Stopped recording`.
- `M-;` while recording: AHEM `Cannot run macro while recording` (that keystroke is removed from the recording). With an empty macro: AHEM `Macro is empty`. Otherwise the codes are pushed back in front of the input queue, and modifier state (Shift/Ctrl held) is ignored while they replay.
- TEST-FEAT-008: recording `<`, End, `>`, Down, Home, then replaying three times produced `<a>`, `<b>`, `<c>`, `<>` (the magic line gets a new line).
- **Source:** `src/winio.c:68-136, 270-300`.

## 4. Position, counting

### FEAT-POS — Cursor position (`^C`) and word count (`M-D`)
- `^C` (*report cursor position*, also always with `constantshow`): INFO `line %*zd/%zd (%2d%%), col %2zu/%2zu (%3d%%), char %*zu/%zu (%2d%%)`. Line counts include the magic line; columns are 1-based display columns, total = width of the line + 1; chars are **multibyte characters** of the whole buffer, newlines included (TEST-FEAT-019: `line  1/3 (33%), col  2/ 4 ( 50%), char  1/8 (12%)` for `abc\ndef\n`; at the end `line  3/3 (100%), col  1/ 1 (100%), char  8/8 (100%)`). Number widths: line and char fields are padded to the width of their totals. Constant display: `04` REND-060 item 9.
- `M-D` (word count): INFO `[In Selection:  ]N line[s],  N word[s],  N character[s]`. Lines: of the region or buffer, not counting a final empty segment. Words: the number of successful *next word* steps treating punctuation as part of a word (like `wc -w`). Characters: multibyte characters (newlines count).
- **Source:** `src/text.c:2995-3050`; `src/winio.c` (report_cursor_position).

## 5. Histories (ENABLE_HISTORIES)

### FEAT-STATEDIR — Where state files live
If `$HOME/.nano/` is an existing directory it is used (legacy). Otherwise
`$XDG_DATA_HOME/nano/` or, without that variable, `$HOME/.local/share/nano/`.
If missing, it is created with mode 0700 (and, without XDG_DATA_HOME, also
`~/.local` and `~/.local/share` with 0700; TEST-FEAT-014). Failures are recorded
as startup errors: `Unable to create directory <dir>: <reason>` +
`It is required for saving/loading search history or cursor positions.`, or
`Path <dir> is not a directory and needs to be.` + `Nano will be unable to
load or save search history or cursor positions.` (shown after exit, and as
`Problems with history file` at startup, `10` RC-ERR).
- **Source:** `src/history.c:201-255`.

### FEAT-HIST — Search, replace and execute histories (`-H`, `set historylog`)
- File `search_history` in the state dir. Format: search entries oldest→newest, one per line, an empty line, replace entries, an empty line, execute entries, Each list is written in full including its empty "current" item, so every list (also the last) ends with an empty line (TEST-FEAT-013 output: `old2\nold1\nnewz\nabc\n\nrep1\nXY\n\ncmd1\n\n`). On loading, each empty line switches to the next list. Embedded LF in an entry is stored as NUL.
- Loading: an unreadable existing file → error `Error reading <file>: <reason>` and history saving is disabled. Duplicates are dropped while loading (the later one survives).
- Each list holds at most 100 entries plus the empty "current" item; adding removes an existing duplicate and then, if full, the oldest.
- Saving at exit only when a history changed. The file is opened with `wb`, then `chmod 0600` (failure → `Cannot limit permissions on <file>: <reason>`). Write errors → `Error writing <file>: <reason>`.
- Browsing: Up/`^P` older, Down/`^N` newer; the starting point is the empty current item. Tab completes (`17` PROMPT-HIST).
- **Source:** `src/history.c:48-350`.
- **Evidence:** runtime TEST-FEAT-013.

### FEAT-POSLOG — Cursor position log (`-P`, `set positionlog`)
- File `filepos_history`. Each line: optional anchor line numbers each followed by a space, then the canonical absolute path, a space, the line number, a space, the column (display column + 1) (TEST-FEAT-014: `40 41 /…/f.txt 41 2`). The path starts at the first `/` of the line; LF in paths is stored as NUL.
- Loading: up to 200 lines; a line of length ≤ 1 stops reading. Entries are kept in file order; **the most recently updated entry is first** (TEST-FEAT-015: the reopened file moved before `/elsewhere`).
- When a file is opened (not new, not stdin), its entry (matched by canonical path) restores anchors and moves the cursor to line/column (TEST-FEAT-015: line 40 column 2, centered). When a buffer is closed (or nano exits), the entry is updated with the current line, column and anchors, moved to the front, and the file is rewritten immediately (mode 0600; max 200 entries). If the file's mtime changed since the last load, it is reloaded first (several nano instances).
- **Source:** `src/history.c:351-600`.
- **Evidence:** runtime TEST-FEAT-014, -015.

## 6. Help viewer

### FEAT-HELP — `^G` / F1
1. In builds without help: in the main or browser menu, statusbar `^W = Ctrl+W    M-W = Alt+W`; elsewhere a beep.
2. All flags are saved and restored afterwards. During help: help lines forced on (and zero mode off), search forward, case-insensitive, literal; whitespace display off; no line numbers; tab size 8; the cursor hidden; the syntax `nanohelp`.
3. **Text:** an introduction specific to the menu the help was called from (main, search/replace, replace-with, go-to-line, insert, write, browser, browser search, go-to-dir, spell, execute, linter, …; exact texts in `data/messages.csv`), then for every function available in that menu, one line: the first key padded to 7 cells, the second key in parentheses padded to 10 cells (or blanks), then the function's description; a blank line after functions marked `BLANKAFTER`. In the main menu, all toggles follow: `M-X\t\t <name> enable/disable`, with blank lines after the line-numbers, softwrap and autoindent groups.
4. The first line of the text (up to the first `\n`) is the title shown in the title bar (`Main nano help text`, TEST-FEAT-018). The body is hard-wrapped into a temporary buffer: introductory text at `min(max(COLS,40),74)` columns, key descriptions at `COLS−18` (min 22) after a two-tab indent; a line with a single space is added at the top when `minibar` is on or `emptyline` is off and LINES > 6.
5. Keys: Up/Down (and scroll up/down) scroll by one row (never past the last screen); PgUp/PgDn, first/last line; search (`^W`/`^F` forward, `^Q`/`^B` backward) / next / previous (searching positions the cursor at the spotlighted match, with visibility subject to REND-040 (hidden by the spotlight in TEST-FEAT-018); that test found `Justify` after `Search Wrapped`); `^L` refresh; Exit (`^X`; the full MHELP list is in `02`); bracketed paste → `Paste is ignored`; mouse; other keys → `02` KEY-025.
6. On resize, the text is rewrapped and the position kept by byte offset of the top line.
7. On exit, the buffer is discarded, flags, tab size, margin, syntax, spotlight and the prompt answer restored, and the screen redrawn (TEST-FEAT-018 s08).
- **Source:** `src/help.c`.
- **Evidence:** runtime TEST-FEAT-018, TEST-KEY-* help-line evidence.

## 7. Restricted mode

### FEAT-RESTRICT — `-R`, or invoked as `r*` (argv[0] basename starting with `r`)
- **Refused functions** (AHEM `This function is disabled in restricted mode` plus a beep): Read File/insert (`^R`), Execute (`^T`), spell, linter, formatter, suspend (TEST-FEAT-012). Several of these are also left out of the shortcut lists and help lines (`02`, profile `default-restricted`).
- **Write Out:** if the buffer has a name, the filename at the prompt cannot be edited (typing, Delete, Backspace, cut, paste and verbatim input are ignored). Writing to an existing file other than the buffer's own → ALERT `File exists -- cannot overwrite` with a pause. The `^T` browser, backup toggle and prepend/append toggles are unavailable. Writing a marked region is not offered.
- **Startup:** backups (`-B`/`set backup`), `historylog` and `positionlog` are turned off; `operatingdir` from an rcfile is ignored (only `-o` counts) (TEST-RC-011); `$SPELL` is not consulted; `--help` omits `-B`, `-C`, `-F`, `-H`, `-P`, `-R`, `-s`.
- **Exit on a fatal signal:** no emergency save files are written (`13` SIG-EMERG).
- The title bar state area shows `Restricted` when the buffer is unmodified (TEST-RC-011).
- **Source:** `src/nano.c:205-213, 370-380, 1877-1879, 2246-2300, 2364-2372`; `src/files.c:2185-2195`; `src/prompt.c:300-310`; `src/winio.c:2064-2072`.

## 8. Build features and credits

### FEAT-BUILD — Build profiles
`data/build-features.csv` maps each `--disable-*`/`--enable-*` option to the
`ENABLE_*`/`NANO_TINY` macros and to the requirements that disappear. The
reimplementation's acceptance profile is the **default** build
(`00-reference-environment.md` profile P-DEF); the tiny profile (P-TINY) is
optional and specified only through the differences recorded in `01`, `02`, `04`.

### FEAT-CREDITS — Easter egg
At the `Save modified buffer?`/Write prompt during exit, entering the filename
`zzy` (once per session) shows the scrolling credits instead of saving
(`do_credits`): names and translators scroll, any key stops it. Optional to
reproduce; listed for completeness.
- **Source:** `src/files.c:2148-2160`; `src/winio.c:3603-3700`.

## Original implementation notes
- `ran_a_tool` keeps the help lines (`MMOST`) after tools; `treat()` is shared by alternate speller and formatter; `fix_spello` uses `findnextstr(…, whole_word_only=TRUE, INREGION …)`.

## Evidence summary
| Requirement | Evidence |
|---|---|
| FEAT-PARA/JUST | runtime TEST-FEAT-001…003 |
| FEAT-SPELL | runtime TEST-FEAT-004, -005, -010 |
| FEAT-LINT | runtime TEST-FEAT-006, -011 |
| FEAT-FORMAT | runtime TEST-FEAT-007 |
| FEAT-EXEC | runtime TEST-FEAT-017, -012, TEST-FILE-030 (stderr is captured too; `false` → `Error: ---`) |
| FEAT-MACRO | runtime TEST-FEAT-008, -009 |
| FEAT-POS | runtime TEST-FEAT-019, TEST-EDIT-026 (`2 lines,  5 words,  24 characters`) |
| FEAT-HIST/POSLOG/STATEDIR | runtime TEST-FEAT-013…015 |
| FEAT-HELP | runtime TEST-FEAT-018 |
| FEAT-RESTRICT | runtime TEST-FEAT-012, TEST-RC-011 |
| FEAT-CREDITS | source only |

## Open questions
- **Q-FEAT-001:** The internal speller depends on `hunspell`/`spell`, `sort` and `uniq` from PATH, and on their output. The Rust version must run the same external pipeline (or document a deviation).
- **Q-FEAT-002:** Without trimblanks, justify leaves one trailing blank on every broken line. This is reference behavior and must be reproduced.
- **Q-FEAT-003:** The credits are optional.
