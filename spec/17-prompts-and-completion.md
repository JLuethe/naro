# 17 — Prompts, answer editing, history and completion

Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

Scope: the status-bar prompt (layout, scrolling, editing keys, input
gathering, paste, verbatim input, mouse), the return protocol of prompts, the
Yes/No question, history browsing and history completion, filename and
username tab completion, and restricted-mode limits. Specific prompts (search,
replace, go to line, write, insert, execute, go to dir, spell) are specified in
their own documents; this file covers the shared machinery.

Evidence: `evidence/runs/TEST-PROMPT-001…012`, TEST-PROMPT-NUL-001,
TEST-I18N-001/-002, TEST-FEAT-013, TEST-INPUT-010, TEST-SRCH-*.

---

### PROMPT-DISP — Layout and horizontal scrolling
1. The prompt row is the status row (`04` REND-001), painted over its full width in the PROMPT_BAR attribute (`04` REND-050).
2. The prompt text is formatted, then cut so it occupies at most `COLS − 5` columns (cut at a character boundary). It is followed by `:` and then a space, or `<` when the answer is scrolled.
3. `base = width(prompt) + 2`. With `column = base + width(answer[0..cursor])`, the first displayed column of the answer is:
   `page(column) = 0` if `column == base` or `column < COLS − 1`; otherwise, if `COLS > base + 2`, `column − base − 1 − (column − base − 1) mod (COLS − base − 2)`; otherwise `column − 2`.
4. The answer is drawn with `display_string` from that column (control characters as `^X`, tabs expanded, `04` REND-020) over `COLS − base` columns. If the answer extends past the right edge (the last page is later than the current one), a `>` is put in the last column.
5. The cursor is at screen column `column − page`.
6. TEST-PROMPT-006 (100 digits after `Search:` at 80 columns): cursor at the end → `Search:<` followed by the last 30 digits, cursor at x=38; Home → `Search: ` + 71 digits + `>` in column 79, cursor at x=8.
- **Source:** `src/prompt.c:337-395, 591-625`.

### PROMPT-EDIT — Editing the answer
The cursor position is a byte offset into the answer. Functions (whatever keys
are bound to them in the prompt's menu, `02`):

| Function | Effect |
|---|---|
| left / right | one character; in UTF-8 also skips zero-width characters |
| prevword / nextword | as in the editor, with `wordchars` and the `afterends` flag (TEST-PROMPT-007 `^→` from 0 to the start of the second word) |
| home / end | start / end |
| backspace / delete | remove the character before / at the cursor (delete also removes following zero-width characters) |
| cut (`^K`) | at the end of the answer: clear the whole answer; otherwise remove from the cursor to the end (TEST-PROMPT-004 s08, -007 s10). The cutbuffer is not touched. |
| copy (`M-6`) | if the answer is non-empty: replace the cutbuffer with the answer, cursor to 0 (TEST-PROMPT-007 s03) |
| paste (`^U`) | insert the cutbuffer's **first line** at the cursor (TEST-PROMPT-007 s06/s07) |
| verbatim (`M-V`) | read a verbatim keystroke (`03` INPUT-008) and insert its bytes (TEST-PROMPT-008: `^A` shown) |
| help (`^G`) | open the help viewer for this menu; the answer is kept (TEST-PROMPT-011) |
| refresh (`^L`) | full repaint |
| nohelp toggle (`M-X`) | toggle the help lines and redraw |
| a string binding | inject its text (`02` KEY-032) |

- **Typed characters:** a key code that is not bound in the current menu is inserted if it is a byte 0x20–0xFF or Tab and not a Meta key; other codes beep. Consecutive bytes are gathered and inserted together once no more input is waiting (or before a command), so multibyte characters arrive whole. NUL bytes inserted into the answer are stored as 0x0A (`18` BYTE-NUL).
- **Bracketed paste:** between the paste markers, all bytes are inserted literally, a Tab is a character (TEST-PROMPT-008: `a<Tab>bc`, displayed as spaces to the next tab stop), and any other command (including Enter for CR) is ignored with a beep. So a pasted CR does not submit.
- **Mouse** (with `-m`): a click on a help-line item runs that item. A click on the prompt row at column ≥ `base` moves the cursor to the character at that column of the displayed page; a click left of `base` moves it to 0 (TEST-PROMPT-010).
- **Resize:** the prompt is reformatted for the new width and redrawn with the same answer and cursor (TEST-PROMPT-012 at 50×15: prompt on row 12).
- Every other function bound in the menu ends the prompt (PROMPT-RET). In view mode, functions that would change the buffer only beep.
- **Source:** `src/prompt.c:30-336, 413-588`.

### PROMPT-RET — Return protocol
`do_prompt(menu, provided, history, …)` starts with the answer `provided` and
the cursor at the end (or where the caller put it) and returns:
- `-1` for Cancel (`^C`), `-2` for Enter with an empty answer, `0` for Enter with text;
- otherwise the key code of the function that ended the prompt, which the caller interprets (toggles like `M-C`, switching prompts like `^R`/`^T`, first/last line, the browser). After Cancel, Enter and the first/last line or first/last file functions, the cursor position the caller had saved is restored.
- If no message was shown during the prompt, the status row is wiped afterwards. A listed completion is cleared by redrawing the edit window.
Callers that re-prompt after a toggle keep the typed answer (`07` SRCH-001).
- **Source:** `src/prompt.c:591-656`.

### PROMPT-YESNO — Yes/No/All questions
1. The question is drawn on the prompt row (PROMPT_BAR, cut to `COLS − 1` columns). With help lines: ` Y Yes` (row 1, column 0), ` N No` (row 2, column 0), ` A All` (row 1, column `width`), and the Cancel key (`^C Cancel`, row 2, column `width`), with `width = 16`, or `COLS/2` when `COLS < 32`; letters are the first letters of the translations (`14` I18N-YESNO).
2. The cursor is shown while waiting, except for the replace question (`Replace this instance?`), where it is hidden.
3. Answers: `14` I18N-YESNO. A bracketed paste: its first character is used as the answer key, the rest is discarded. Resize redraws. `^L` repaints; the nohelp toggle works. Mouse: clicking one of the shown answers selects it.
- **Source:** `src/prompt.c:658-830`.

### PROMPT-HIST — History browsing
Applies to prompts with a history list: search (and its "to replace" form),
replace-with, and execute (`12` FEAT-HIST for the lists and storage).
1. **Older** (Up, `^P`): on the first step, the list pointer is reset to the bottom (the empty current item) and the typed answer is remembered. Then, if an older item exists, the answer becomes that item and the cursor goes to its end (TEST-PROMPT-005: `par` → `three` → `two`).
2. **Newer** (Down, `^N`): moves to the next newer item. Arriving back at the bottom with an empty item, the remembered answer is restored (TEST-PROMPT-005: `two` → `three` → `par`).
3. **Tab** (history completion): the fragment is the whole answer when the previous key was not also Tab (otherwise the fragment of the first Tab is kept). If the fragment is non-empty: search **older** from the current position for an entry starting with the fragment (byte comparison over its length), skipping entries equal to the current answer; if none, search from the bottom (newest) down to the current position. The found entry becomes the answer and the list position (TEST-PROMPT-005: `t` → `three` → `two` → `three`, and then Up moves to the entry older than the current one, `two`). Nothing found: the answer is unchanged, no beep.
4. When the prompt ends, the list pointer is reset to the bottom.
5. Without history support (tiny), Up/Down have no history effect.
- **Source:** `src/prompt.c:490-536`; `src/history.c:67-200`.

### PROMPT-COMPLETE — Filename completion (Tab)
At the Read File, Write, and Go To Directory prompts, unless restricted:
1. If the cursor is not at the end of the answer: beep, nothing else (TEST-PROMPT-004 s04).
2. If the answer starts with `~` and has no `/`: complete user names from the passwd database (entries starting with the text after `~`), as `~name`; users whose home is outside the operating directory are skipped.
3. Otherwise (or when no user matched), split at the last `/`: the directory part is `~`-expanded and, when relative, prefixed with the current directory `./` (the browser's current directory while browsing); the rest is the prefix. All directory entries starting with the prefix (byte comparison), except `.` and `..`, are candidates; entries outside the operating directory are skipped; at Go To Directory only directories count. An unreadable directory → beep.
4. No candidates → beep (TEST-PROMPT-004 s10).
5. The longest common prefix of the candidates (compared character by character) replaces the fragment after the last `/`. With exactly one candidate that is a directory, `/` is appended (TEST-PROMPT-001: `alps` → `alps/`). If nothing changed and there is one candidate: beep.
6. **Listing:** with two or more candidates, a sorted list (directory-aware alphabetical order as in the browser, `09` BROWSE-002) is shown in the edit window: column width = longest name (max `COLS − 1`) + 2, `ncols = (COLS + 1) / (longest + 2)`, rows placed at the bottom of the edit window (`lastrow = editwinrows − 1`, minus 1 in zero mode); if the list does not fit, it starts at row 0 and the last row's last cell shows `(more)` (TEST-PROMPT-003). The cursor is hidden while the list is shown; the first listing beeps. The list stays until a completion leaves fewer than two candidates or the prompt ends (TEST-PROMPT-002: list kept while editing).
- **Source:** `src/files.c:2373-2610`.
- **Evidence:** runtime TEST-PROMPT-001…004.

### PROMPT-RESTR — Restricted mode at the Write prompt
When restricted and the buffer has a name: typed characters, verbatim input,
Delete, Backspace, cut and paste are ignored; movement works; Tab completion is
off (TEST-PROMPT-009: `zz`, Backspace, `^K`, Del had no effect; Enter wrote
`f.txt`). See `12` FEAT-RESTRICT for the rest.
- **Source:** `src/prompt.c:264-266, 300-310, 499`.

### PROMPT-VERB — Verbatim input in prompts
As `03` INPUT-008, but the bytes go into the answer. A verbatim sequence of
999 or more bytes is discarded; an empty result beeps.

### PROMPT-MOUSE — Summary
Mouse is only active with `-m`/`set mouse` (`03`). Prompts: PROMPT-EDIT.
Yes/No: PROMPT-YESNO. Browser: `09` BROWSE-007. Help lines: a click on an item
in any menu acts like its key.

## Original implementation notes
- `answer` (heap string) and `typing_x` are globals; `prompt` holds the formatted prompt text; `absorb_character` keeps a static "puddle" of gathered bytes.
- `foretext` keeps the Execute answer when a tool function is invoked from the Execute prompt.

## Evidence summary
| Requirement | Evidence |
|---|---|
| PROMPT-DISP | runtime TEST-PROMPT-006, -012 |
| PROMPT-EDIT | runtime TEST-PROMPT-004, -007, -008, -010, -011 |
| PROMPT-RET | runtime TEST-SRCH-*, source |
| PROMPT-YESNO | runtime TEST-I18N-001/-002, TEST-PROMPT-NUL-001, TEST-SIG-011…014 |
| PROMPT-HIST | runtime TEST-PROMPT-005, TEST-FEAT-013 |
| PROMPT-COMPLETE | runtime TEST-PROMPT-001…004 |
| PROMPT-RESTR | runtime TEST-PROMPT-009 |

## Open questions
- **Q-PROMPT-001:** NUL answers Yes at Yes/No questions (`14`). Proposal: do not reproduce.
- **Q-PROMPT-002:** Username completion reads the passwd database (`getpwent`); in tests it depends on the host. Tests must not assert specific user names.
