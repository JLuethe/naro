# 05 — Buffer and editing

Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

Scope: the logical buffer model, positions, text insertion, Enter, Tab,
deletion, cutting/copying/pasting and the cutbuffer, the mark and regions,
indentation, commenting, word completion, all cursor-movement commands, and
modified-state tracking.

Evidence: `evidence/runs/TEST-EDIT-*` (28 editing scenarios, each ending with a
save, so the resulting file bytes are recorded), `TEST-MOVE-*` (16 movement
scenarios), plus the scenarios of other sections. Units of positions are
defined in `18-bytes-encoding-and-coordinates.md`.

---

## 1. Model

### EDIT-001 — Buffer state
A buffer consists of:
- **lines**: an ordered, non-empty sequence of byte strings without newline characters. An embedded NUL byte is represented internally as 0x0A (`18` BYTE-NUL). Lines are numbered from 1.
- **current position**: (current line, byte offset `x` within it, 0 ≤ x ≤ length). x always lies on a character boundary, as defined by `18` BYTE-STEP.
- **preferred column** (*placewewant*): the display column that vertical movement aims for. It is set to the cursor's column by most actions; Up/Down/PgUp/PgDn keep it.
- **viewport**: top line, first column of the top line (soft wrap), horizontal scroll start (`04` REND-022).
- **mark**: absent, or (line, offset). A mark set by holding Shift is a *soft* mark (EDIT-031).
- **modified** flag, **file name** (may be empty), **file format** (Unix or DOS, `08`), **character count** (*totsize*: number of characters including one per line break, `18` BYTE-COUNT), syntax, undo history (`06`), lock file name, anchors (one boolean per line).
- **Magic line:** unless `--nonewlines` is on, the last line of a buffer whose text ends with a newline is an **empty** line that stands for "after the final newline". A file `abc\n` is the lines `["abc", ""]`. If the last line becomes non-empty (typing on it, pasting, inserting, cutting), a new empty last line is appended. When writing, no newline is written after the last line, so the magic line produces the final newline. With `--nonewlines` no magic line is maintained, and the last line may be non-empty and saved without a newline.
- **Source:** `src/definitions.h:472-610`; `src/utils.c:429-452`.
- **Evidence:** runtime TEST-EDIT-001/-002 (`""` + typing → `abc\n`; `abc` without newline is saved as `abc\nd\n` after typing on the magic line).

### EDIT-002 — Global (cross-buffer) state
The cutbuffer, the search string and its options, the histories, the macro,
the replacement answer and the flags are **global**, shared by all buffers.
Cursor, mark, undo history and modified flag are per buffer.

### EDIT-003 — Modified flag
Any change to the text sets *modified* (changing the save format at the
Write prompt does not). When it changes from unmodified to modified,
the title bar is redrawn (`Modified` appears), and if the buffer has a lock file
it is rewritten with the "modified" byte set (`08` FILE-LOCK). It is cleared by a
successful full save of the buffer under its own name (not when writing a
selection or appending/prepending), and by undo/redo arriving at the state
recorded at the last save (`06` UNDO-SAVED). Inserting a file into the current
buffer sets it only if something was inserted (the cursor moved).
- **Source:** `src/files.c:496-508, 1933-1976, 1313-1316`; `src/text.c:670-675, 839-844`.

---

## 2. Inserting text

### EDIT-010 — Typing (inject)
Typed or injected bytes (a burst of text, `02` KEY-020; a word completion; a
verbatim character; Tab's expansion) are inserted at the cursor:
1. Zero bytes inside the burst are stored as 0x0A (embedded NUL).
2. Undo: unless the previous action was also an addition **and** the cursor is exactly where that addition ended (same line, same offset), a new ADD undo item starts (`06` UNDO-ADD).
3. The bytes are inserted at x. The cursor advances by their length. A mark on the same line at a larger offset moves right with the text.
4. The character count increases by the number of **characters** in the burst. The buffer becomes modified.
5. If text was added to the last line (the magic line) and `--nonewlines` is off, a new empty last line is appended.
6. With *breaklonglines*: hard-wrap (EDIT-015).
7. The preferred column becomes the cursor column.
- In view mode: refused (`02` KEY-043).
- **Source:** `src/nano.c:1464-1565`.

### EDIT-011 — Enter (*enter*)
1. Let `extra` = 0. With *autoindent*: the sample line is the current line, except when hard-wrapping is on and the next line belongs to the same paragraph and is not a paragraph start (`12` FEAT-PARA); then the sample is the next line. `extra` = length of the sample's leading whitespace (spaces/Tabs/other Unicode blanks). If `extra > x`, `extra = x`. If `extra == x` and the current line's own indentation equals `extra` (the cursor is at the end of the indentation), the **all-blanks** case applies.
2. A new line is made of `extra` bytes copied from the sample's indentation, followed by the text after the cursor. The current line is cut at x. In the all-blanks case, the current line becomes empty (its whitespace is removed) and x becomes 0, together with a mark on that line.
3. A mark after the cursor on the same line moves to the new line (offset adjusted).
4. The cursor goes to the new line at offset `extra`. The count increases by 1 (+ `extra` when not all-blanks). Modified. An ENTER undo item is created.
- **Evidence:** runtime TEST-EDIT-008 (`    indented` + Enter → `    x`), -009 (Enter inside the indentation at x=2 → `  ` / `    indented`), -010 (Enter at the end of an all-blank line → the line is emptied).
- **Source:** `src/text.c:848-923`.

### EDIT-012 — Tab (*tab*)
1. If a mark is set **on another line** than the cursor: indent the region (EDIT-040).
2. Else, if the buffer's syntax defines `tabgives`: insert that string.
3. Else, with *tabstospaces*: insert `tabsize − (cursor column mod tabsize)` spaces (TEST-EDIT-011: column 3 → 5 spaces).
4. Else insert a Tab byte.
- At prompts, Tab completes (`17`).
- **Source:** `src/text.c:52-81`.

### EDIT-015 — Automatic hard wrapping (*breaklonglines*)
After each insertion on a line (and after a paste that stays on one line):
1. `lead` = the quote prefix (`12` FEAT-QUOTE) plus following blanks. Find the last blank after `lead` whose display end is at most `wrap_at` columns from the line start (`wrap_at` = fill if > 0, else `COLS + fill`, minimum 0; default fill −8). If none is found before the limit, the first blank after it is used. Leading blanks after `lead` are never break points. Of a run of blanks, the break comes after the last one.
2. If there is no such blank, or it is at the end of the line, or the text after it is empty, nothing happens.
3. If the line below was created by a previous wrap of this line (*spillage line*) and the remainder plus that line still fits in `wrap_at` columns, the remainder is prefixed to that line: a space is added at the end of the current line if the remainder does not end in a blank, the lines are joined, a duplicated leading part (equal to `lead`) is removed, and extra blanks at the join point are deleted.
4. With *trimblanks*, blanks before the break point are removed, except the one just typed when the cursor is right after it.
5. The line is split at the break point (as Enter, with autoindent applied). If the original line had a quote prefix, that prefix is also copied to the new line, and autoindent is suspended for the split.
6. The cursor stays where the typed text logically is (on the first or second line). The new line becomes the spillage line.
7. The whole wrap is one undoable unit (SPLIT_BEGIN … SPLIT_END, `06`).
- **Source:** `src/text.c:1233-1455`.
- **Evidence:** source-confirmed; 39 runtime differential cases `TEST-NEXT-UNDO-WRAP-001-MID` … `TEST-NEXT-UNDO-WRAP-039-MARK-SHIFT` (file bytes, modified/saved state, cursor and screen through undo and redo) match the pinned reference; see `../validation/wrap-undo/README.md`. The spillage marker is a stable per-line generation and every splice states which node survives. The quote prefix (`032-QUOTE`), the terminal-width wrap geometry with a nonpositive fill (`034-FILL-ZERO`, `035-FILL-NEG`), the continuation indent sampled from the next line (`033-CONT-INDENT`), the live explicit mark through a join (`028-MARK`) and a paste that edits or shifts the live target (`037-PASTE`, `038-PASTE-SHIFT`) are covered at runtime.

---

## 3. Deleting

### EDIT-020 — Delete (*delete*) and Backspace (*backspace*)
- With *zap* (`-Z`) and a mark set: both erase the region (EDIT-034) (TEST-EDIT-019).
- **Delete:** if a character follows the cursor, delete it, plus any zero-width characters that follow it (combining marks). At the end of a line that is not the last, join the next line onto this one. **Exception:** when the next line is the magic line and the cursor is not at x=0, nothing happens (TEST-EDIT-004). At the end of the last line, nothing happens (TEST-EDIT-005).
- **Backspace:** if x > 0, move left one character (`18` BYTE-STEP; zero-width characters are not skipped here) and delete that character. At x=0 on a line other than the first, move to the end of the previous line (*left*) and do a Delete there. The magic-line exception therefore means that Backspace at the start of the magic line does not remove the final newline (TEST-EDIT-003). At the start of the buffer, nothing happens.
- A mark on the same line after the deleted character shifts left. A mark on the joined line moves to the joined position. A joined line's anchor is ORed into the current line.
- The character count decreases by 1, the buffer becomes modified, and an undo item is created or extended (`06` UNDO-DEL).
- **Source:** `src/cut.c:27-153`.
- **Evidence:** runtime TEST-EDIT-003…007, -019, -028 (Delete at the end of a line joins the former magic line after text was typed on it).

### EDIT-021 — Chop word left/right (`Sh-^Del`, `M-Bsp`; `^Del`)
*chopwordleft*: at the very start of the buffer, HUSH `Nothing was cut`.
Otherwise the cursor moves to the previous word start (EDIT-061). If that is on
an earlier line and the cursor was not at x=0, the target becomes x=0 of the
original line instead (no joining). If the cursor was at x=0, the target is the
end of the previous line (the line break is deleted). The text between target
and cursor is deleted.
*chopwordright*: first any mark is cleared; if nothing can be cut there
(EDIT-030 with cliff test: at the end of the buffer, or at the end of the line
just before the magic line), `Nothing was cut`. Otherwise the cursor moves to the
next word start (or word end with *afterends*). If that is on a later line and the
cursor was not at the end of its line, the target becomes the end of the
original line. The text between is deleted.
In both cases the cutbuffer is not affected (a temporary one is used), and one
CUT undo item records the deletion.
- **Source:** `src/cut.c:181-250`.
- **Evidence:** runtime TEST-EDIT-020 (`one two three` → `two `), -027 (`M-Bsp` deleting `ab` before `c`).

---

## 4. Cut, copy, paste

### EDIT-030 — When there is nothing to cut
A cut, zap, or chop-right reports HUSH `Nothing was cut` (and clears any mark)
when:
- no mark is set, the cursor is on the last line, and that line is empty from x (*cut from cursor*) or from 0; **or**
- a mark is set at exactly the cursor position (empty region); **or**
- (cut-from-cursor, or chop-right) x > 0, at the end of the line, and the next line is the magic line.
- **Source:** `src/cut.c:155-179`.
- **Evidence:** runtime TEST-EDIT-014.

### EDIT-031 — Cut (*cut*, `^K`, F9)
1. If the previous action was not a cut, or the cut chain is broken (`02` KEY-021), a new cutbuffer is started (the old content is discarded) and a CUT undo item is created. Otherwise the cut is **appended** to the cutbuffer, and the undo item is extended.
2. What is cut:
   - **mark set:** the region from the earlier to the later of (mark, cursor). The mark is removed;
   - **cut-from-cursor** (`-k`), no mark: the text from the cursor to the end of the line. If the cursor is already at the end of a line that is not the last, the line break (joining the next line) is cut;
   - otherwise the **whole current line including its line break**, or, on the last line, the line's text only.
3. After a whole-line cut, the cursor is at x=0 of the line that followed, and the preferred column is 0.
4. The chain stays open after a line or cut-from-cursor cut, but a region cut closes it (the next cut starts a new cutbuffer).
5. If the cut removed the end of the buffer's text and `--nonewlines` is off, a magic line is re-added when the last line becomes non-empty.
6. Modified; status bar wiped; full redraw.
- **Source:** `src/cut.c:482-559, 253-368`.
- **Evidence:** runtime TEST-EDIT-012 (two ^K, move, paste → both lines), -013 (chain broken by movement), -015 (`-k`), -017 (region).

### EDIT-032 — Copy (*copy*, `M-6`, `M-^`)
- **Mark set:** the region is copied into a **new** cutbuffer, the mark is removed, and the cursor does not move. An empty region gives HUSH `Copied nothing`. The copy action breaks any chain.
- **No mark:** consecutive copies accumulate:
  - the cutbuffer is reset unless the previous action was a copy;
  - at the very end of the buffer (last line, at its end) when cutting from the cursor, or at x=0, or when the cutbuffer is not empty: `Copied nothing`;
  - otherwise the text of the current line (from x with *cut-from-cursor*) is added as a line including its line break. With *cut-from-cursor* and the cursor not at the end of the line, the text is added **without** the line break. On the last line with `--nonewlines`, also without the break;
  - the cursor then moves to the start of the next line (or, with *cut-from-cursor* mid-line, to the end of the current line).
- Copy never modifies the buffer.
- **Source:** `src/cut.c:606-724`.
- **Evidence:** runtime TEST-EDIT-016 (two M-6 then paste → `l1\nl2` appended).

### EDIT-033 — Paste (*paste*, `^U`, F10)
- Empty cutbuffer: AHEM `Cutbuffer is empty`.
- Otherwise a copy of the cutbuffer is inserted at the cursor (multi-line content splits the current line). The cursor ends right after the inserted text. A mark on the current line after the cursor moves with the tail. Anchors carried by the pasted lines are not copied; the anchor of the line where pasting started is kept. A PASTE undo item records it.
- With *breaklonglines*, if the paste stayed within one line, that line is hard-wrapped.
- The preferred column becomes the cursor column; modified; status wiped; full redraw. If less than a screenful was pasted, the viewport does not re-center.
- The cutbuffer survives buffer switches and is global (EDIT-002). It is also used at prompts (`17`: ^K erases the answer, M-6 copies the answer into the cutbuffer, ^U pastes its first line).
- **Source:** `src/cut.c:726-785, 370-461`.

### EDIT-034 — Zap (*zap*, `M-Del`)
Like cut (same "nothing to cut" rules, the same "what" rules including
cut-from-cursor), but the text goes to a private buffer kept in the undo item,
**not** to the cutbuffer. Consecutive zaps are combined into one undo item.
After a zap the cut chain stays open for further zaps. AHEM/HUSH as for cut.
- **Source:** `src/cut.c:581-604`.
- **Evidence:** runtime TEST-EDIT-018 (`bcdef`-region zap with `M-Del`), -019 (`-Z` + Backspace).

### EDIT-035 — Cut till end of file (*cutrestoffile*, `M-T`, `^T ^V`)
If nothing is after the cursor (at the end of the last line, or at the end of a
line followed only by the magic line with x > 0), HUSH `Nothing was cut`.
Otherwise the text from the cursor to the end of the buffer goes into a new
cutbuffer (never appended), as a CUT_TO_EOF undo item. In the Execute prompt
(`^T ^V`) this is the "Cut Till End" tool.
- **Evidence:** runtime TEST-EDIT-021.

---

## 5. Mark and regions

### EDIT-036 — Setting the mark (*mark*, `^6`, `M-A`)
Toggles: sets a (hard) mark at the cursor with HUSH `Mark Set`, or removes it
with HUSH `Mark Unset` (and redraws). With *stateflags* the `M` flag follows.
A mouse click at the cursor position also toggles the mark.

### EDIT-037 — Soft mark (Shift selection)
Holding Shift with a movement key (`02` KEY-022) sets a soft mark if no mark is
set. It disappears when a movement happens without Shift, and also when any
typed character is inserted (the text replaces nothing; the selection is just
dropped). Commands work on soft-marked regions as on hard ones.
- **Evidence:** runtime TEST-INPUT-012 (Shift+Right/Left, then Right).

### EDIT-038 — Region and line range
The **region** is the text between mark and cursor, from the earlier to the
later position, in the [start, end) sense. Line-based commands (indent,
unindent, comment) use the **line range**:
- no mark: the current line;
- mark set: from the first to the last line of the region. When the region ends at x=0 of a later line, that last line is excluded. This exclusion is remembered while the set of lines stays the same, so repeated indents keep the same lines even if the end moves to x=0 as text shifts.
- **Source:** `src/utils.c:454-498`.

---

## 6. Line operations

### EDIT-040 — Indent (*indent*, `M-}`, Tab with a multi-line mark)
On the line range, ignoring leading empty lines (if all lines are empty,
nothing happens): each non-empty line gets an indentation prepended. The
indentation is the syntax's `tabgives` string if defined, else *tabsize* spaces
with *tabstospaces*, else one Tab. Cursor and mark offsets on affected lines
move right (unless at x=0). One INDENT undo item; modified; full redraw. The
selection is kept (Shift-held state).
- **Evidence:** runtime TEST-EDIT-022 (`a`, ``, `b`, `c` → `\ta`, ``, `\tb`, `\tc`).

### EDIT-041 — Unindent (*unindent*, `M-{`, Sh-Tab)
On the line range, ignoring leading lines without removable whitespace (if none
has any, nothing happens): from each line remove its first "tab's worth": the
syntax's `tabgives` string if the line starts with it; otherwise leading spaces
up to *tabsize* of them, or up to and including the first Tab. Cursor and mark
offsets move left (clamped at 0). One UNINDENT undo item.
- **Evidence:** runtime TEST-EDIT-023 (`\ta`, `    b`, `  c`, `d` → `a`, `b`, `c`, `d`).

### EDIT-042 — Comment/uncomment (*comment*, `M-3`)
1. The comment sequence is the buffer syntax's `comment` (default `#`). An empty sequence → AHEM `Commenting is not supported for this file type`.
2. If the range is only the magic line → AHEM `Cannot comment past end of file`.
3. A sequence containing `|` is split into prefix and suffix (`/*|*/`).
4. Decision: if any line in the range is not blank and not already commented, all lines are **commented**. If all lines are blank, they are commented too. Otherwise (every non-blank line commented) all are **uncommented**. A line counts as commented when it starts with the prefix and (if there is a suffix) ends with it.
5. Commenting prepends the prefix (and appends the suffix) to every line of the range except the magic line, including blank lines. Uncommenting removes the prefix/suffix from lines that have them.
6. Cursor and mark offsets adjust (x=0 stays 0 when commenting). One COMMENT or UNCOMMENT undo item; the sequence used is remembered for undo/redo.
- **Source:** `src/text.c:300-449`.
- **Evidence:** runtime TEST-EDIT-024 (`x` → `#x`; `#y` → `y`).

### EDIT-043 — Word completion (*complete*, `^]`)
1. The **fragment** is the run of word characters (EDIT-060) directly before the cursor. If there is none: AHEM `No word fragment`.
2. A fresh attempt (the previous keystroke was not a completion) clears the list of tried words and starts scanning at the top of the current buffer. A repeated attempt first undoes the previous completion.
3. Scanning goes forward through the lines of the current buffer, then the other buffers in list order. A candidate is a byte-exact occurrence of the fragment that starts a word (not preceded by a word character) and continues with at least one more word character. The occurrence that is the fragment itself is skipped. The candidate word extends over the following word characters. Words already tried in this run are skipped.
4. The first new candidate is inserted (the part after the fragment), with hard-wrapping suppressed and applied once afterwards. The scan position is remembered for the next attempt.
5. When all buffers are exhausted: AHEM `No further matches` (if some completion was offered, after a redraw), or `No matches`. The next `^]` starts a fresh run.
6. Undo of a completion is not reported ("Undid …" is suppressed while completing). Typing directly after a completion extends the same ADD undo item.
- **Source:** `src/text.c:3095-3287`.
- **Evidence:** runtime TEST-EDIT-025 (alphabet → alpine → back to `al` with `No further matches` → alphabet again; after typing `x`, one undo removes `phabetx`).

---

## 7. Movement

### EDIT-060 — Word characters
A character is a **word character** when it is alphanumeric (`iswalnum` in
UTF-8 locales; see Q-EDIT-001 and doc 18 for non-UTF-8), or, with *wordbounds* (`-W`),
punctuation (`iswpunct`), or it occurs in *wordchars* (`-X`). An invalid byte is
not a word character. Zero-width characters are skipped (neither word nor
separator) during word movement.
- **Source:** `src/chars.c:108-130`.
- **Evidence:** runtime TEST-MOVE-001…004 (`foo.bar baz_qux`: `.` and `_` are separators by default; with `-W` or `-X ._` they are word characters).

### EDIT-061 — Previous/next word (`^◂`/`^▸`, `M-Space`/`^Space`)
- **prevword:** move left character by character (crossing line starts), until a word character has been seen and then a non-word character is found. The cursor ends on the first character of that word. If the start of a line is reached while on a word character, that is the word start. At the start of the buffer, it stops.
- **nextword:** move right character by character (crossing line ends; reaching a new line counts as a separator), until a word character follows a separator. With *afterends* (`-y`): until a separator follows a word character, so the cursor stops right after the end of a word. At the end of the buffer, it stops.
- Movement keeps going over empty lines.
- **Evidence:** runtime TEST-MOVE-001/-003.

### EDIT-062 — Home / End
- **Home** (`^A`, Home): with *smarthome*, when the line has non-blank text: if x equals the indentation length, go to x=0; else, unless soft-wrapping puts the cursor on a later chunk, go to the end of the indentation. Without smart home, or when that does not apply: under soft wrap, go to the start of the current chunk, or, if already there, to x=0; otherwise x=0.
- **End** (`^E`, End): under soft wrap, go to the last position of the current chunk, or, if already there, to the end of the line; otherwise the end of the line.
- The preferred column is updated.
- **Evidence:** runtime TEST-MOVE-005 (smart home cycle 20 → 2 → 0 → 2).

### EDIT-063 — Left / Right
**Left:** within the line, one character back, then further back over
zero-width characters. At x=0, go to the end of the previous line, if any.
**Right:** one character forward, then further forward over zero-width
characters. At the end of the line, go to x=0 of the next line, if any. At the
buffer start or end, nothing happens.
- **Evidence:** runtime TEST-MOVE-010 (combining and wide characters), -011.

### EDIT-064 — Up / Down
Move one line (soft wrap: one chunk) up or down, keeping the preferred column:
the cursor goes to the last character position whose display column does not
exceed the preferred column, and never past the end of the row's chunk. Under
soft wrap, when the target column lands on a Tab that crosses a chunk boundary,
the cursor is adjusted so that it does not skip or repeat a row. At the first or
last line nothing happens. If the cursor was on the top or bottom row, the view
scrolls one row (unless jumpy scrolling, or soft wrap with `tabsize ≥ editwincols`).
- **Evidence:** runtime TEST-MOVE-009 (preferred column 16 across `ab` and `\tx`).

### EDIT-065 — Page up / down (`^Y`/`^V`, PgUp/PgDn)
Move `editwinrows − 2` rows (at least 1) up or down, keeping the cursor's screen
row (STATIONARY) and the preferred column. If fewer rows are available, go to the
first line (x=0) or the last line (end). With *jumpyscrolling*, first move to the
top row of the screen and column 0.
- **Evidence:** runtime TEST-MOVE-008/-012.

### EDIT-066 — First / last line (`M-\`, `^Home`; `M-/`, `^End`)
First line: line 1, x=0. Last line: the last line, at its end. The view puts the
last line on the bottom row.
- **Evidence:** runtime TEST-MOVE-011.

### EDIT-067 — Blocks (`^▴`/`^▾`, `M-7`/`M-8`)
A *blank* line is empty or contains only blanks/CRs. **prevblock:** move up
until a blank line follows (from above) one or more non-blank lines, then step
down one line onto the first line of that block. **nextblock:** move down to the
first non-blank line after at least one blank line. If none, the last line. x=0;
centering if off-screen.
- **Evidence:** runtime TEST-MOVE-006.

### EDIT-068 — Paragraphs (`M-(`/`M-9`, `M-)`/`M-0`; justify builds)
Paragraph rules are in `12` FEAT-PARA. **beginpara:** go to the previous line,
then up until a paragraph start; x=0. **endpara:** go down to the last line of
the next paragraph (skipping non-paragraph lines), then one line further (x=0),
or to the end of the last line. Also usable at the Go-To-Line prompt (`^W`/`^O`).
- **Evidence:** runtime TEST-MOVE-007.

### EDIT-069 — Top/bottom row, scrolling, centering
- **toprow** (`M-Home`) / **bottomrow** (`M-End`): the cursor goes to the first / last row of the viewport, keeping the preferred column.
- **scrollup** (`M-▴`, `M--`, `M-_`) / **scrolldown** (`M-▾`, `M-+`, `M-=`): the view moves one row while the cursor stays on its text line. If the cursor would leave the window, it moves one line instead. At the top of the buffer, scroll up does nothing. Scroll down stops when the last line is at the top.
- **center** (`^L` in main): the cursor line is put in the middle row, and everything is redrawn.
- **cycle** (`M-%`): successive presses put the cursor line at the middle, top, bottom, middle, … Any other command restarts the cycle at "middle".
- **Evidence:** runtime TEST-MOVE-008.

### EDIT-070 — Scroll left/right (`M-<`/`M->`)
Not possible with soft wrap or `--solosidescroll`: AHEM `Not possible with
'--softwrap'` or `Not possible with '--solo'` (the message names `--solo`).
- **Left:** the scroll start (`brink`) decreases by *tabsize* (at least 2), but not below 0. If the cursor would be past the right edge (`brink + editwincols − 4`), it is moved left to stay inside.
- **Right:** `brink` increases by *tabsize* (at least 2). If the current line is too short to show text at the new position (`width < brink + 3`), nano looks for a visible line that is long enough, first above the cursor and then below, and moves the cursor to it. The cursor is moved right to at least `brink + 3` if needed.
- **Evidence:** runtime TEST-MOVE-013.

### EDIT-071 — Anchors (`M-Ins`, `M-"`; `M-PgUp`; `M-PgDn`, `M-'`)
*anchor* toggles an anchor on the current line. Without line numbers and
minibar, REMARK `Placed anchor` / HUSH `Removed anchor`. *prevanchor* /
*nextanchor* search upward/downward, wrapping around, for the nearest line with
an anchor other than the current one. Found: go there (x=0) and, without line
numbers, HUSH `Jumped to anchor`. Only the current line has an anchor: REMARK
`This is the only anchor`. None: AHEM `There are no anchors`. Anchors are shown in
the line-number margin and the mini bar. They move with their lines, are merged
when lines are joined, are not copied by paste, and are saved/restored with the
position log (`12`).
- **Evidence:** runtime TEST-MOVE-016.

### EDIT-072 — Go to line/column (`^/`, `^_`, `M-G`)
Prompt `Enter line number, column number` (`17`). The answer is parsed as in
`01` CLI-030 form 2. A leading `++` or `--` jumps relative to the current line
(result clamped ≥ 1). Positions are applied per `01` CLI-031, except: the
preferred column is not clamped here, and when the answer starts with `,` the
viewport keeps the cursor's screen row. Parse failure: AHEM `Invalid line or
column number`. An empty answer or Cancel: HUSH `Cancelled`. `^T` switches to
the Search prompt, keeping the typed text. `^Y`/`^V` go to the first/last line
directly; `^W`/`^O` go to paragraph start/end.
- **Source:** `src/search.c:768-883`.

## 8. Original implementation notes
- Lines are a doubly linked list of `linestruct` (`data`, `lineno`, `prev`, `next`, `multidata`, `has_anchor`). Line numbers are renumbered after structural changes. A Rust implementation may use any structure (rope, gap buffer, vector of lines) provided byte content, line numbering and the magic-line invariant are preserved.
- The cutbuffer is itself a linked list of lines. `keep_cutbuffer` implements the chain. `cutbottom` points at its last line.
- `extract_segment` and `ingraft_buffer` are the primitives for cut and paste.

## 9. Evidence summary
| Requirement | Evidence |
|---|---|
| EDIT-001, 010, 011, 012 | runtime TEST-EDIT-001/-002/-008…011 |
| EDIT-015 | partially covered (39 runtime `TEST-NEXT-UNDO-WRAP-001-MID`…`039-MARK-SHIFT` cases; the quote prefix, the nonpositive fill geometry, the continuation indent and the live explicit mark are covered; the interactions with soft wrap, view mode and terminal resize are not separately verified) |
| EDIT-020/021 | runtime TEST-EDIT-003…007, -019, -020, -027 |
| EDIT-030…035 | runtime TEST-EDIT-012…021 |
| EDIT-036/037 | runtime TEST-EDIT-022 (messages), TEST-INPUT-012 |
| EDIT-040…043 | runtime TEST-EDIT-022…025 |
| EDIT-060…072 | runtime TEST-MOVE-001…016 |

## 10. Open questions
- **Q-EDIT-001:** Resolved by TEST-BYTE-004: in non-UTF-8 locales, bytes ≥ 0x80 are sign-extended before `iswalnum`, so Latin-1 letters are not word characters. Reproduce; see doc 18 BYTE-CLASS and 99.
- **Q-EDIT-002:** Paste via the cutbuffer with *breaklonglines* only wraps single-line pastes; multi-line pastes are left unwrapped. Reproduce as specified.
