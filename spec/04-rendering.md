# 04 — Rendering

Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

Scope: screen layout (title bar, edit window, status bar, help lines, mini
bar, zero mode), the conversion of line text into screen cells, horizontal
scrolling and soft wrapping, line numbers, indicator, guide stripe, cursor
placement and visibility, colors and attributes, status messages, small
terminals, and redraw requirements.

Normative requirements here define the **resulting screen state**: characters
in cells, their attributes, the cursor position and its visibility. The
terminal byte stream does not have to match. Redraw algorithms appear only as
implementation notes. Evidence: `evidence/runs/TEST-REND-*` (25 scenarios),
plus the screens captured by `TEST-CLI-*`, `TEST-KEY-*` and `TEST-INPUT-*`.

Coordinates: rows and columns are 0-based screen positions; `LINES` × `COLS` is
the terminal size; "column" of text means display column (`18`
BYTE-COLUMNS).

---

## 1. Layout

### REND-001 — Window layout
The screen is divided into a top part (title bar, plus an optional blank row),
the **edit window**, and a bottom part (status bar plus optional help lines).
With `min = 3` if *zero*, else `4` if *minibar*, else `5`:

| Condition | Top rows | Edit rows | Bottom rows |
|---|---|---|---|
| `LINES < 3` | 0 | 1 (with zero: `LINES`) | 1, on the last row (with `LINES == 1` it is the same row as the edit row) |
| otherwise | 1, or 2 with *emptyline* and `LINES > min`; 0 with *minibar* or *zero* | `LINES − top − bottom` (+1 with zero) | 3 = status + 2 help lines; 1 when *nohelp* or `LINES < min` |

With *zero* the edit window also covers the bottom row, and the status bar is
drawn over the edit window's last row only while a message is shown (REND-041).
Examples at 80×24: default → title row 0, edit rows 1–20, status row 21, help rows
22–23. `-x` → edit rows 1–22, status row 23. `-_` → edit rows 0–20, mini bar row
21, help rows 22–23. `-0` → edit rows 0–23. `-e` → title row 0, blank row 1, edit
rows 2–20 (TEST-CLI-038/-039/-040/-042, TEST-REND-014…018).
- The usable text width is `editwincols = COLS − margin − sidebar` (REND-030, REND-033).
- **Source:** `src/nano.c:393-447`.
- **Evidence:** runtime-observed (zero mode `-0`: TEST-REND-010).

### REND-002 — Title bar
Drawn on row 0 when there is a top part, over the full width in the TITLE_BAR
attribute (REND-050):
1. Elements: **upper-left** = `GNU nano 9.3`, or `[i/n]` (buffer number / buffer count) when more than one buffer is or was open in this session. In the help viewer it is empty. **Prefix** = `DIR:` in the browser, `Linting --` in the linter, else empty. **Path** = in the browser the directory, in the help viewer the help title, in the linter the file name, else the buffer's file name or `New Buffer`. **State** = `View` (view mode), the placeholder `+.xxxxx` when *stateflags* is on, else `Modified`, else `Restricted` in restricted mode, else empty. When the state is empty, room for `Modified` + 1 is still reserved ("plug").
2. Widths: `verlen = width(upper-left) + 3`, `prefixlen = width(prefix) + 1` (0 if empty), `pathlen = width(path)` (+1 if a state is shown), `statelen = width(state) + 2`, `pluglen`.
3. If `verlen + prefixlen + pathlen + pluglen + statelen ≤ COLS`, the upper-left text is drawn at column 2. Otherwise it is omitted (`verlen = 2`); then, if it still does not fit, the plug is dropped; then, if it still does not fit, the side spaces are dropped (`verlen = 0`, `statelen −= 2`).
4. If `verlen > 0`, the centre part starts at `verlen + (COLS − (verlen + pluglen + statelen) − (prefixlen + pathlen)) / 2`, otherwise at column 0.
5. The prefix and one space are drawn only if everything fits. The path is drawn in full if `pathlen + pluglen + statelen ≤ COLS`. Otherwise, if `5 + statelen ≤ COLS`, `...` followed by the right-most part of the path that fits in `COLS − statelen − 3` columns is drawn (TEST-REND-011/-012). Otherwise the path is not drawn.
6. With *stateflags* and not view mode: ` *` follows the path when the buffer is modified (and `COLS > 1`), and the five flag cells `I M L R S` (or a space each) are drawn at column `COLS + 2 − statelen` (REND-003). Otherwise the state word is right-aligned at `COLS − statelen` when it fits, or clipped at column 0.
7. The path is converted with REND-020 rules for non-data text. Whitespace display therefore shows `·` in a file name (TEST-KEY-008 s11: `New·Buffer`).
- **Source:** `src/winio.c:1994-2149`.
- **Evidence:** runtime-observed (TEST-SMOKE-001, -CLI-027/-028/-035, -REND-011/-012/-018, -CLI-041).

### REND-003 — State flags
The five cells show, in order: `I` if autoindent, `M` if the mark is set, `L` if
hard-wrapping (breaklonglines), `R` if a macro is being recorded, `S` if
soft-wrapping. Each absent flag is a space. Shown in the title bar
(*stateflags*, REND-002) or in the mini bar (REND-004).
- **Source:** `src/winio.c:1981-1992`.

### REND-004 — Mini bar (`-_`/`--minibar`, not with zero)
Drawn on the status row (bottom window row 0) when no message more important
than HUSH is showing, in the MINI_INFOBAR attribute over the full width:
1. Name = the file name or `(nameless)`. `padding` = 2, or 0 if `width(name) + 19 > COLS`.
2. If `COLS > 4`: at column `padding`, the name (or `...` + its tail when `width > COLS − 2`, the tail being `COLS − 5` columns), followed by ` *` if modified, else two spaces.
3. Right after loading or saving a file (*report size*), and if `COLS > 35`: ` (N line)` / ` (N lines)` (with `, DOS` inside the parentheses for DOS format), when `width(name) + width(text) + 11 < COLS`. N excludes a final empty line. The report is shown only once. Otherwise, with several buffers and `COLS > 35`: ` [i/n]` if `width(name) + width(position) + width(ranking) + 32 < COLS`.
4. With *constantshow*: the position `LINE,COLUMN` (1-based column) at column `COLS − 27 − width(position)` if `width(name) + tally + width(position) + 32 < COLS`. Then the code of the character under the cursor at column `COLS − 23`, as 6 cells: `U+XXXX` (UTF-8 locale; at least 4 hex digits); `  0xXX` (non-UTF-8 locale); `U+000A` (UTF-8) or `  0x0A` at the end of a line that is not the last; `  ----` at the end of the buffer; `  0x00` for an embedded NUL. In UTF-8 locales, up to two following zero-width characters are appended as `|XXXX` each. Requires `width(name) + tally + 28 < COLS`.
5. With *stateflags*: the five flag cells at column `COLS − 11 − padding`, when no zero-width suffix was drawn and `width(name) + tally + 14 + 2·padding < COLS`.
6. If the current line has an anchor: `†` (UTF-8) or `+` at column `COLS − 5 − padding`, when `width(name) + 7 < COLS`.
7. The percentage `floor(100 · current line / last line)`, formatted `%3d%%`, at column `COLS − 4 − padding`, when `width(name) + 6 < COLS`.
- Example (TEST-REND-009, 80 cols, `-_ -c -%`): `  big.txt   (1200 lines)` … `1,1` at col 50, `U+006C` at col 57, `  0%` at col 74.
- **Source:** `src/winio.c:2151-2294`; main loop `src/nano.c:2703-2711`.

### REND-005 — Help lines
Shown on the two bottom rows unless *nohelp* is on, or `LINES < 5` (3 with
zero, 4 with minibar). The items are those of `02` KEY-050. With `n` items,
`itemwidth = COLS / ((n + 1) / 2)` (integer division). If it is 0, nothing is
drawn. Item `i` (0-based) goes to row `1 + i % 2` of the bottom window, at
column `(i / 2) * itemwidth`, with width `itemwidth`, plus `itemwidth` more for
the second-to-last item when n is odd, plus `COLS % itemwidth` for each of the
last two items. Each item is drawn as: the key text in KEY_COMBO attribute,
truncated to the width. Then, only if at least 2 columns remain, a space and the
translated tag in FUNCTION_TAG attribute, truncated to `width − width(key) − 1`
columns. Because tags are not followed by padding, adjacent items can touch
(`^/ Go To LineM-E Redo`, TEST-CLI-049) and long tags are cut (`New Buffe`,
TEST-KEY-010).
- **Source:** `src/winio.c:2416-2491`.
- **Evidence:** runtime-observed: every captured screen matches `data/helplines-80cols.csv`; widths 40, 30, 20, 10 observed (TEST-INPUT-010, -REND-011/-012/-018); `-x` then `M-X` shows `Help mode enabled` (TEST-REND-025).

### REND-006 — Yes/No question layout
See `17` PROMPT-YESNO: the question on the status row (PROMPT_BAR attribute,
truncated to `COLS − 1`), and with help lines ` Y Yes`/` A All` on row 1, ` N No`
and the cancel key + `Cancel` on row 2, in columns of width 16 (or `COLS/2` when
`COLS < 32`).

---

## 2. Text conversion

### REND-020 — Converting a line to cells
The visible part of a line is produced from its bytes, starting at the display
column `from` and filling at most `span` columns:
1. The first character shown is the one whose display position is the largest ≤ `from`. If it starts before `from`, or (for buffer text, without soft wrapping) starts after column 0 of a scrolled line, and is not a Tab:
   - a control character that starts before `from` is shown as its second half (the letter only);
   - a double-width character: if it starts exactly at `from`, a space is shown first; then `]` represents its right half.
2. Each character is then rendered (`advance_over` widths, `18` BYTE-COLUMNS):
   - printable ASCII 0x21–0x7E (and, in non-UTF-8 locales, bytes 0xA0–0xFF): the character itself, one column;
   - space: a space, or the second whitespace-display character when *whitespacedisplay* is on (REND-024);
   - Tab: one cell (a space, or the first whitespace-display character), then spaces up to the next multiple of *tabsize*, not beyond `from + span`;
   - a control character: `^` plus its representation: bytes 0x00–0x1F → `@`…`_` (0x00 is shown `^@`; an embedded NUL is stored as 0x0A and shown `^@` in buffer text and file names, REND-021); 0x7F → `^?`; UTF-8 C1 controls U+0080–U+009F (bytes C2 80–C2 9F) → `^` + (second byte − 0x20) as a character, except U+009F → `^=` (TEST-REND-005: U+0085 is `^e`); in non-UTF-8 locales bytes 0x80–0x9F likewise → `^` + (byte − 0x20);
   - an invalid UTF-8 byte (UTF-8 locale): U+FFFD `�`, one column per byte (`18` BYTE-INVALID);
   - a valid multibyte character: its bytes, with width `wcwidth()` (2 for wide, 0 for combining). Unassigned code points (`wcwidth = −1`) count as one column. Zero-width characters do not use a column and are kept even beyond the span; on a Linux console they are dropped.
3. **Right edge:** if the next character would pass `from + span`, or (buffer text without soft wrapping, and prompts) any text remains, the last cell is reserved for `>`: the cell, and any zero-width characters attached to it, is removed; if what remains there is a double-width character, its left half is shown as `[`.
- **Source:** `src/winio.c:1771-1964`; `src/chars.c:132-162`.
- **Evidence:** runtime-observed TEST-REND-005 (controls, C1, invalid, wide, combining, NUL, BOM), TEST-REND-001/-002 (`<`, `>`).

### REND-021 — `^@` versus `^J`
In buffer text an embedded 0x0A byte is an encoded NUL, displayed `^@`. In file
names shown at prompts and in the title bar, a newline byte is displayed `^J`.
nano switches the representation (`as_an_at`) when it displays file names
(opening files, Write/Insert prompts, lock-file questions, title bar) and back
when it draws buffer text.
- **Source:** `src/chars.c:146-150`; `src/files.c:395, 1158, 2052, 292`; `src/winio.c:2025`.

### REND-022 — Horizontal scrolling (no soft wrap)
Lines longer than `editwincols` are shown from a start column. Two modes:
- **United sidescroll** (default; used when *solosidescroll* and *softwrap* are off and `editwincols > 8`): all lines are drawn from the same start column `brink`. The edit window redraw sets `brink = page_start(cursor column)`, where for column c:
  - `c < 3` → 0;
  - `c < brink + 3` → jumpy: `c − editwincols/2` (min 0); else `c − 3`;
  - `c > brink + editwincols − 4` → `c − editwincols + (jumpy ? editwincols/2 : 3) + 1`;
  - otherwise `brink` (unchanged).

  Lines shorter than `brink` appear empty (TEST-REND-001: after End on a long line, the other lines vanish).
- **Solo sidescroll** (`-1`): each line is drawn from its own page start. The current line uses `page_start(cursor column)`, other lines start at 0, with `page_start(c) = 0` if `c == 0` or `c + 2 < editwincols`; else if `editwincols > 8`: `c − 6 − (c − 6) % (editwincols − 8)`; else `c − (editwincols − 2)` (TEST-REND-002).
- In both modes, a line drawn from a start column > 0 that has visible text shows `<` in column `margin`, and a line with more text beyond the right edge shows `>` in column `COLS − 1 − sidebar`. Both use the highlight attribute (reverse, or bold with `-D`).
- **Scroll Left/Right** (`M-<`/`M->`): `04` REND-022a in `05` EDIT-SCROLLH.
- **Source:** `src/utils.c:344-368`; `src/winio.c:2809-2851`; `src/nano.c:2694-2701`.
- **Evidence:** runtime-observed TEST-REND-001/-002.

### REND-023 — Soft wrapping (`-S`)
A line is split into **chunks** of at most `editwincols` columns:
- Without *atblanks*: break exactly after the last character that fits. A Tab that crosses the edge ends the chunk at the edge. A character that does not fit starts the next chunk.
- With *atblanks* (`-a`): break after the last blank (space or Tab) that lies before the right edge, if the text after it still starts within the edge. If there is none, break as above (TEST-REND-004).
- When `editwincols == 1`, each chunk is one character.
- No `<`/`>` markers are shown. Line numbers appear only on the first chunk; continuation chunks get a blank margin (anchors only on the first chunk).
- The viewport may start in the middle of a line (`firstcolumn` = start column of the top chunk).
- **Source:** `src/winio.c:3116-3251, 2853-2911`.
- **Evidence:** runtime-observed TEST-REND-003/-004.

### REND-024 — Whitespace display (`M-P`)
Shows Tabs with the first `whitespace` character and spaces with the second
(defaults `»` U+00BB and `·` U+00B7 in UTF-8 locales, `>` and `.` otherwise;
configurable, `10`). The Tab character occupies the first cell of the tab's
expansion. Under soft wrapping, a Tab whose expansion continues at the start of
the next chunk shows the marker there only if that position is a tab stop.
Status messages never show whitespace markers.
- **Evidence:** runtime-observed TEST-REND-006 (`a·b»    c··»    ·d`).

### REND-025 — Byte Order Mark notice
When the cursor is at column 0 of a line that starts with the bytes EF BB BF
(UTF-8 locale; not tiny), NOTICE `Byte Order Mark` is shown, and it is wiped at
the next keystroke. The BOM itself is a zero-width character in the display.
- **Source:** `src/nano.c:2715-2723`.

---

## 3. Decorations

### REND-030 — Line numbers (`-l`, `M-N`)
`margin = digits(last line number) + 1`, where digits is 2 for numbers below 100,
otherwise their decimal length (so the margin is at least 3). The margin is 0
when line numbering is off or `margin > COLS − 4`. Each line's number is drawn
right-aligned in `margin − 1` columns in the LINE_NUMBER attribute. The last margin
column holds `†` (UTF-8) / `+` for a line with an anchor, else a space (normal
attribute). Soft-wrapped continuation rows have a blank number field. The margin
is re-evaluated before every keystroke and changes when the line count crosses a
power of ten; a change forces a full redraw.
- **Source:** `src/nano.c:1256-1282`; `src/winio.c:2544-2565`; `src/utils.c:78-105`.
- **Evidence:** runtime-observed TEST-CLI-043 (3-column margin, number reverse-video 0–1), TEST-REND-007 (5-column margin for 1200 lines).

### REND-031 — Indicator ("scroll bar", `-q`)
Exists when `LINES > 5` and `COLS > 9` (re-evaluated on resize); it occupies the
last column and reduces `editwincols` by 1. Each edit row gets a space cell in
SCROLL_BAR attribute. Rows from `lowest` to `highest` are additionally reversed:
`lowest = (edittop_line − 1) · editwinrows / last_line`,
`highest = lowest + editwinrows · covered / last_line`. `covered` is
`editwinrows`, or under soft wrap the number of lines visible. When the buffer
has fewer lines than rows (without soft wrap), `highest = editwinrows`.
- **Source:** `src/winio.c:3027-3059`.
- **Evidence:** runtime-observed TEST-CLI-044, TEST-REND-008.

### REND-032 — Guide stripe (`-J N`)
In every edit row, the cell at display column `N − 1` (relative to the start
column of that row) is drawn in the GUIDE_STRIPE attribute (default reverse). If
a character starts there, that character is painted (a wide character is
painted whole, at its start column). Otherwise a space is painted. Not drawn in
the help viewer, and not on soft-wrapped chunks that start beyond the stripe.
- **Evidence:** runtime-observed TEST-CLI-045, TEST-REND-021 (stripe at cell 4, also inside a Tab).

### REND-033 — Selected text
Text between the mark and the cursor (`05` EDIT-MARK) is drawn in SELECTED_TEXT
attribute. Only the characters are painted; the rest of the row after the end of
a line is not (TEST-REND-020: `line 2` painted at columns 0–5 only). A line that
is partly inside the region is painted from/to the region boundary.
- **Source:** `src/winio.c:2758-2802`.

### REND-034 — Spotlight
A search match (`07`), and the word under correction in the spell checker, are
spotlighted: the matched text is redrawn in the SPOTLIGHTED attribute (default
black on yellow, bright yellow when ≥ 16 colors: observed `bg=11 fg=0`). A
zero-length match shows a spotlighted space. A match running past the right
edge is cut at the edge, with a spotlighted `>` in the last column. Under soft
wrap, the spotlight continues over the following rows. **While a spotlight is
shown, the cursor is hidden**, unless *showcursor* is on or the spell prompt is
active. The spotlight is removed at the next keystroke in the edit window (or
after 1.5/0.8 s with minibar/zero, `03` INPUT-013).
- **Source:** `src/winio.c:3518-3595, 201-203, 271-276`.
- **Evidence:** runtime-observed TEST-REND-022 (colors, hidden cursor), TEST-CLI-009.

### REND-035 — Syntax colors
Syntax rules (`11`) are painted over the converted row, in rule order (later
rules overwrite earlier ones). Then the guide stripe, then the selection. The
spotlight is painted last. A rule's attribute is its color pair plus bold/italic.
Matching stops at byte offset 2000 of a line (PAINT_LIMIT): text beyond it is not
colored by single-line rules, and no new multiline start is searched beyond it.
- **Evidence:** runtime-observed TEST-REND-019 (c.nanorc colors).

---

## 4. Cursor and viewport

### REND-040 — Cursor position
After each keystroke the terminal cursor is placed on the row of the current
line (or chunk) and at `margin + (cursor column − start column)`. While waiting
for a key it is made visible when (a) the caller asked to show it (edit window,
prompts, yes/no without "All", linter), (b) no spotlight is active (or
*showcursor*, or the spell prompt), and (c) the terminal has more than one row,
or the current message is at most HUSH. Otherwise it is hidden. It is hidden
while nano processes a key. In the help viewer and the browser it is hidden,
except with *showcursor* (`-g`). A successful help search positions it at the
match, but spotlighting keeps it hidden unless *showcursor* is on
(TEST-FEAT-018).
- **Source:** `src/winio.c:2493-2535, 198-203, 260`.

### REND-041 — Viewport rules
- **Movement off-screen:** when a movement puts the cursor outside the edit window, the window scrolls. For one-line moves off the top or bottom row (Up/Down, Left/Right across lines, word moves), it scrolls by exactly one row (FLOWING), unless *jumpyscrolling*. Other jumps center the cursor line (CENTERING: the line ends up `editwinrows / 2` rows from the top). With *jumpyscrolling*, every scroll centers.
- **Page Up/Down:** `05` EDIT-PAGE (the cursor keeps its screen row: STATIONARY).
- **After edits that change line structure:** refresh without moving the viewport, unless the cursor is off-screen; then center (or flow, after an Enter or a small paste).
- Center/cycle (`^L`, `M-%`), scroll up/down (`M-Up`/`M-Down`), top/bottom row: `05`.
- In zero mode, while a message is shown on the bottom row and the cursor is on that row, the view scrolls one line so the cursor stays visible.
- **Source:** `src/winio.c:3321-3459`; `src/nano.c:2725-2743`.

---

## 5. Colors and attributes

### REND-050 — Interface attributes
Each interface element has an attribute:

| Element | Default (terminal with colors) | Without colors | nanorc option |
|---|---|---|---|
| title bar | highlight (reverse; bold with `-D`) | highlight | `titlecolor` |
| line numbers | highlight | highlight | `numbercolor` |
| guide stripe | reverse | reverse | `stripecolor` |
| scroll bar | normal | normal | `scrollercolor` |
| selected text | highlight | highlight | `selectedcolor` |
| spotlight | black on yellow (bright yellow if COLORS > 15) | reverse | `spotlightcolor` |
| mini bar | same as title bar | highlight | `minicolor` |
| prompt bar | same as title bar | highlight | `promptcolor` |
| status bar | highlight | highlight | `statuscolor` |
| error message | bold white on red | highlight | `errorcolor` |
| key combo | highlight | highlight | `keycolor` |
| function tag | normal | normal | `functioncolor` |

- *Highlight* is reverse video, or bold with `--boldtext`.
- A configured color combination (`10` RC-COLOR) replaces the default. If the terminal does not support default colors (`use_default_colors`), a `normal`/unspecified foreground becomes white and the background black.
- **`NO_COLOR` set (any value) and no interface color configured at all:** the spotlight and error-message elements use reverse video instead of their colors (TEST-REND-023). As soon as **any** interface color is configured, `NO_COLOR` has no effect on these two.
- Status-bar text of importance ALERT, MILD and AHEM uses the error-message attribute. NOTICE uses the selected-text attribute. Lower importances use the status-bar attribute.
- Observed attributes at 256 colors: error = `bold, fg 7, bg 1`; spotlight = `fg 0, bg 11`.
- **Source:** `src/color.c:35-81`; `src/nano.c:2411-2430, 2172-2179`; `src/winio.c:2358-2365`.
- **Evidence:** runtime-observed TEST-REND-013/-022/-023/-024, TEST-CLI-046/-050.

---

## 6. Status messages

### REND-060 — Importance and priority
Messages have an importance: VACUUM < HUSH < REMARK < INFO < NOTICE < AHEM <
MILD < ALERT (`data/messages.csv` lists the importance of each message).
1. Before each keystroke in the edit window is executed, the "last message" is reset to VACUUM.
2. A new message is ignored if its importance is lower than the last one **and** the last one is above NOTICE. So within one action, an AHEM/MILD/ALERT cannot be overwritten by a lower one, while REMARK-level messages are simply replaced.
3. A message of importance ≥ AHEM discards all pending input (the rest of the burst, or of a macro or string bind).
4. **A second ALERT while an ALERT is shown** is not displayed. Instead `...` is appended (in the error attribute) to the first message, at column `COLS + 2 − start` (right after its closing bracket, see 6), followed by a 100 ms pause and a beep. This happens only once per first message (TEST-CLI-008, TEST-REND-013).
5. ALERT beeps.
6. **Format:** the text is converted with REND-020 (non-data) rules to at most COLS columns, with whitespace display suppressed. `start = (COLS − width) / 2`. If `start > 1`, the text is drawn as `[ text ]` starting at `start − 2`; otherwise the text alone at `start`. The status row is blanked first. The attribute covers the brackets and the text.
7. After display the **blank countdown** is set to 20 keystrokes, or 1 with *quickblank*. Each keystroke read in the edit window decrements it, and at 0 the status row is wiped.
8. When curses is not active (e.g. during `-` stdin reading or in the suspended state), the message goes to stderr as `\n<text>\n`.
9. *Constant show* (`-c`): before each keystroke, when no message is shown (VACUUM), the terminal has more than 1 row, not zero mode, and no input is pending, the cursor position is reported (INFO, see `12` FEAT-POS). With *minibar*, the position is shown inside the mini bar instead.
10. With *minibar*/*zero*: messages between HUSH and ALERT (except INFO) disappear after 1.5 s (0.8 s with quickblank) or at the next keystroke (`03` INPUT-013). In zero mode the message overwrites the last edit row and is removed after that.
- Startup messages produced while opening the 2nd and later files are stored per buffer (`08` FILE-MULTI-ERR).
- **Source:** `src/winio.c:2297-2414, 1749-1769`.
- **Evidence:** runtime-observed throughout (brackets, centering, `...`, colors).

### REND-061 — Warnings with pause
Some errors are shown with `warn_and_briefly_pause`: the help lines are blanked,
ALERT shown, and nano sleeps 1.5 s, after which the message no longer blocks
lower-importance messages. Used by backup failures, restricted overwrite refusal,
and "File on disk has changed" (`08`).

---

## 7. Small terminals and resizing

### REND-070 — Small sizes
- `LINES == 1`: the edit row and the status row coincide. The edit row is redrawn when no message (≤ HUSH) is shown. Messages below INFO first flush the edit row, then the message overwrites it. Message timeouts apply as with zero mode (TEST-REND-014: the welcome message is not visible).
- `LINES == 2`: edit row 0, status row 1, no title (TEST-REND-015).
- `LINES 3–4`: title, edit rows, status, no help lines (TEST-REND-016/-017).
- Narrow: title-bar degradation (REND-002), help-line truncation (REND-005), status messages lose their brackets when `start ≤ 1` (TEST-REND-018).
- Toggling help lines on a too-small terminal: `Too tiny` (`02` KEY-045). The credits Easter egg needs `LINES > 5` and `COLS > 31`.
- A line-number margin that would leave fewer than 4 columns is suppressed (REND-030).
- **Evidence:** runtime-observed TEST-REND-014…018.

### REND-071 — Resize
On SIGWINCH (`13` SIG-WINCH) curses re-reads the size, windows are recreated
with REND-001, the indicator and margin are re-evaluated, the first soft-wrap
column is re-aligned, and everything is redrawn (title, edit window or browser,
help lines). An active prompt is redrawn with the same answer (TEST-INPUT-010).

## 8. Redraw correctness
- After every keystroke, once nano is waiting for the next one, the screen must equal what a full redraw from the current state would produce. That is: title bar, edit rows (REND-020…035), status row (current message or blank), help lines, cursor.
- `^L` (*refresh*) in prompts, the help viewer, the browser and Yes/No repaints the whole screen from nano's internal image (`wrefresh(curscr)`); in the edit window `^L` is *center* (`05`).
- Exact sequences of terminal output are not specified. The trace is diagnostic only (`16` §4).

## 9. Original implementation notes
- `topwin`, `midwin`, `footwin` are ncurses windows. `edit_refresh` redraws all rows; `edit_redraw` redraws only changed lines after movement; `edit_scroll` uses `wscrl` plus one or two redrawn rows; `update_line` draws one line; `draw_row` paints colors, stripe and mark over the converted text.
- `display_string` sets the statics `from_x`, `till_x`, `has_more` and `is_shorter`, which `draw_row` uses.
- The multiline color cache (`multidata`) is described in `11`.

## 10. Evidence summary
| Requirement | Evidence |
|---|---|
| REND-001…006 | runtime (many screens), source |
| REND-020…025 | runtime TEST-REND-001…006, source |
| REND-030…035 | runtime TEST-REND-007/-008/-019/-020/-021/-022, TEST-CLI-043/-044/-045 |
| REND-040/041 | runtime (cursor positions in all scenarios), source |
| REND-050 | runtime TEST-REND-022…024, TEST-CLI-046 |
| REND-060/061 | runtime (messages), source |
| REND-070/071 | runtime TEST-REND-014…018, TEST-INPUT-010 |

## 11. Open questions
- **Q-REND-001:** Emulator dependence: the reference was observed through tmux, which re-encodes the output. Attributes on blank cells that are visually identical (bold/italic/blink on spaces) are not preserved by ncurses' output optimization. Normalization rule N-ATTR-BLANK (`16` §4) treats them as equal.
- **Q-REND-002:** `wcwidth` comes from glibc 2.44. Widths of newer emoji or unassigned code points vary across C libraries and emulators. The reimplementation must use the same width table as the reference envelope, or document its deviation (`18` BYTE-WIDTH, `15`).
- **Q-DOC-002:** `nanorc.5` documents the default space marker as `⋅` (U+22C5); the code uses `·` (U+00B7). The code is normative.
