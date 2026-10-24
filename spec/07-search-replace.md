# 07 — Search and replace

Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

Scope: the search and replace prompts and their toggles, literal and regex
matching, direction, start position and progression, wraparound, zero-length
matches, replacement (confirmation, all, cancel, region, backreferences), the
search string default and history, and bracket matching. The regex dialect is
specified in `11-syntax-highlighting.md` §R (shared contract).

Evidence: `evidence/runs/TEST-SRCH-*` (19 scenarios), TEST-CLI-009…015,
TEST-MOVE-014/-015.

---

### SRCH-001 — Search prompt
`^W`/`^F`/F6 (*whereis*) clears the "backwards" flag; `^B`/`^Q` (*wherewas*)
sets it. Both then show the prompt
`Search` + `[Case sensitive]` + `[Reg.exp.]` + `[Backwards]` + `[<default>]` + `:`.
Each bracket part (with a leading space) appears only when its flag is on; the
part ` (to replace)` (or ` (to replace) in selection` when a mark is set) is
added when replacing. The default part is ` [<last search string>]`, shown when a
previous search string exists. It is the display form of the string truncated
to `COLS/3` columns, with `...` added inside the brackets when longer.
- Keys in the prompt (`02` tables MWHEREIS/MREPLACE): `M-C` toggles case sensitivity, `M-R` regex, `M-B` direction, `^R` switches between search and replace (in view mode: `Key is invalid in view mode` with a 0.6 s pause), `^T` switches to Go-To-Line keeping the typed text, `^Y`/`^V` go to the first/last line, `Up`/`Down`/`^P`/`^N` browse history (`17`), Tab completes from history. After a toggle the prompt is shown again with the answer kept.
- **Enter with text:** the text becomes the search string and is added to the search history (duplicates removed, `17` PROMPT-HIST).
- **Enter with an empty answer:** uses the previous search string. If there is none: HUSH `Cancelled`.
- **Cancel:** HUSH `Cancelled`.
- In regex mode, the string is compiled first. Failure: AHEM `Bad regex "<string>": <regerror text>`, and no search (TEST-SRCH-016).
- **Source:** `src/search.c:73-167`.
- **Evidence:** runtime TEST-SRCH-001…003, -014, -016, -017.

### SRCH-002 — Case sensitivity and literal matching
- Case-sensitive literal search: byte-exact substring match.
- Case-insensitive literal search (the default): in UTF-8 locales, characters are compared after `towlower` of their code points, ASCII letters by folding `A–Z`/`a–z`. Invalid bytes only match identical bytes. The needle length in characters determines the comparison span (TEST-SRCH-019: `É` finds `é`). In non-UTF-8 locales: `strcasecmp`-style comparison in the C library's locale.
- Regex search: POSIX ERE, compiled with `REG_ICASE` when not case-sensitive (`11` §R).
- **Source:** `src/utils.c:217-280`; `src/chars.c:402-550`.

### SRCH-003 — Where a search starts and how it proceeds
- A new search (prompted, or next/previous via `M-W`/`M-Q`/`M-F`/`M-B`) starts at the cursor **skipping the character at the cursor**. Forward: the first match starting after the cursor. Backward: the last match starting before the cursor. If the cursor is at the start (backward) or end (forward) of a line, the skip does not apply and the whole line portion is searched.
- Lines are searched in order. At the end (or start) of the buffer the search wraps to the other end with REMARK `Search Wrapped`, and continues up to and including the starting line. On the starting line, a forward search accepts matches up to and including the starting offset; a backward one accepts matches at or after the starting offset.
- **The magic line never yields a match** (an empty last line is skipped).
- Found at exactly the starting position after a full cycle: REMARK `This is the only occurrence` (TEST-SRCH-004).
- Not found: AHEM `"<string>" not found` (SRCH-008).
- Found: the cursor moves to the start of the match, the match is spotlighted (`04` REND-034; not when a hard mark is set), the viewport is centered when the match is off-screen, and the horizontal scroll adjusts so that the end of the match is visible.
- *findnext*/*findprevious* (`M-W`/`M-F`, `M-Q`/`M-B`) set the direction and search for the last string without prompting. If no search string exists yet, the most recent history entry is used. If there is none: AHEM `No current search pattern` (TEST-SRCH-018).
- Every second (about), pending keys are checked for Cancel (`03` INPUT-012). After one second, HUSH `Searching...` is shown; after a wrap, after two seconds.
- **Source:** `src/search.c:169-450`.
- **Evidence:** runtime TEST-SRCH-001/-002/-004/-006/-017.

### SRCH-004 — Regex specifics
- Forward regex search uses `regexec` with `REG_STARTEND` from the skip position to the end of the line. `^` therefore matches only at line starts (REG_NOTBOL is not used here; a match beyond offset 0 cannot be `^`). `$` matches at line ends.
- Backward regex search finds the **last match whose start is ≤ the start limit**. It does so by repeatedly searching forward, each time starting one character after the previous match's start, until no match starts within the limit. The match is then re-run from the last good start to obtain its subexpressions. Consequence: matches overlapping a later match can be found backward even though forward stepping skips them.
- Zero-length matches are allowed: the cursor goes there and a spotlighted **space** covers the character at that position (TEST-SRCH-003: `^` hides the first letter of the line while spotlighted). Repeated next-search moves on, because each search skips one character.
- **Source:** `src/utils.c:219-267`.

### SRCH-005 — Replace
*replace* (`^\`, `M-R`, or `^R` at the search prompt). Refused in view mode (`Key is invalid in view mode`). The direction
flag is cleared first.
1. Search prompt with ` (to replace)` (SRCH-001). Toggles as for search.
2. Prompt `Replace with` (history: the replace history). Cancel → HUSH `Cancelled`. Another bound function → that function is run and replacing stops. Enter with an empty answer → the replacement is the empty string. A non-empty answer goes into the replace history.
3. The search string is the one entered at step 1 (restored even if the history was browsed at step 2).
4. **Loop** (`do_replace_loop`), starting at the cursor (or, with a mark, at the start of the region, or its end when searching backward; the mark is hidden during the loop and the search is limited to the region, without wrapping):
   - find the next match (SRCH-003 rules, but in REPLACING mode: on the starting line, the match at exactly the starting position is **not** accepted after wrapping);
   - with a region: a match outside it ends the loop;
   - unless "All" was chosen: spotlight the match, redraw, ask `Replace this instance?` with Yes/No/All/Cancel (`17` PROMPT-YESNO; the cursor is hidden while asking). **Y**: replace. **N**: skip (the next search skips one character). **A**: replace this and all remaining ones without asking. **^C**: stop.
   - replacing: the matched text is replaced by the replacement (SRCH-006). Each replacement is one REPLACE undo item. When moving forward, the search continues right after the inserted text. After a zero-length match, or with a regex starting with `^`, the next search skips one character (so `^` replaces once per line).
5. Afterwards the cursor and viewport return to where they were before step 1 (the cursor offset is adjusted if text before it on its line changed length). The summary is REMARK `Replaced N occurrence` / `Replaced N occurrences` (plural form), shown even for 0 when at least one match was found and the user cancelled (TEST-SRCH-013). If no match was found at all: AHEM `"<string>" not found`.
- **Source:** `src/search.c:527-744`.
- **Evidence:** runtime TEST-SRCH-007 (y/n/y), -008 (All), -010 (region), -012 (empty replacement), -013 (cancel → 0), -015 (zero-length), -011 (`^`).

### SRCH-006 — Replacement text
- Literal mode: the replacement is inserted verbatim.
- Regex mode: `\1` … `\9` are replaced by the corresponding subexpression of the match, but **only when the number ≤ the number of groups in the regex**. Otherwise the backslash and digit are kept literally (TEST-SRCH-009: `\3` with two groups stays `\3`). `\0`, `\\`, `&` and other escapes have no special meaning. A group that did not participate contributes the empty string.
- Example (TEST-SRCH-009): regex `(f)(o+)` (case-insensitive), replacement `<\2\1\3>` turns `foo Foo FOO` into `<oof\3> <ooF\3> <OOF\3>`.
- Example (TEST-SRCH-015): regex `o*`, replacement `-`, All, on `foo Foo FOO / bar foo / baz` → `-f- -F- -F-` / `-b-a-r- -f-` / `-b-a-z-`, `Replaced 16 occurrences`. This fixture pins down how empty matches interleave with non-empty ones (`11` §R).
- **Source:** `src/search.c:452-519`.

### SRCH-007 — Spell-check replacement
The internal speller (`12` FEAT-SPELL) uses the replace loop in "whole word
only" mode: case-sensitive, forward, literal, and only matches that are separate
words (not preceded or followed by a letter). It never wraps.

### SRCH-008 — Not-found message
AHEM `"<s>…" not found`, where `<s>` is the display form of the search string
cut to `COLS/2` columns, followed by `...` when it was cut (TEST-SRCH-005).

### SRCH-009 — Search persistence
The search string, case/regex flags and direction are global and persist across
buffers and across invocations of search. They can be set from the command
line (`01` CLI-030) and by `set casesensitive` / `set regexp` (`10`). The
help viewer saves and restores all flags around itself, and its searches are
forward, case-insensitive and literal.

### SRCH-010 — Bracket matching (*findbracket*, `M-]`)
1. If the character under the cursor is not in *matchbrackets* (default `(<[{)>]}`): AHEM `Not a bracket` (TEST-MOVE-015).
2. *matchbrackets* is split in two halves of equal character count, openers then closers, in corresponding order. An opener searches forward, a closer backward.
3. Starting one character away from the cursor, nano scans for either the bracket or its partner, keeping a balance (same bracket +1, partner −1). The partner at balance 0 is the match. The cursor moves there (TEST-MOVE-014: `(` at 0 matches `)` at 16 across nested brackets). Brackets inside strings or comments are not special.
4. None found: AHEM `No matching bracket`; the cursor stays.
- **Source:** `src/search.c:885-1005`.

## Original implementation notes
- `findnextstr` is shared by search, replace and the spell checker (`modus` JUSTFIND / REPLACING / INREGION; `whole_word_only`). `came_full_circle` tracks the wrap.
- The regex is compiled into the global `search_regexp` for the duration of one search, and freed afterwards.

## Evidence summary
| Requirement | Evidence |
|---|---|
| SRCH-001 | runtime TEST-SRCH-001/-002/-003/-014/-016/-017 |
| SRCH-002 | runtime TEST-SRCH-002/-019 |
| SRCH-003/004 | runtime TEST-SRCH-001…006/-018 |
| SRCH-005/006 | runtime TEST-SRCH-007…015 |
| SRCH-008 | runtime TEST-SRCH-005 |
| SRCH-010 | runtime TEST-MOVE-014/-015 |

## Open questions
- **Q-SRCH-001:** The spotlight of a zero-length match hides the character under it. This is deterministic and reproduced.
- **Q-SRCH-002:** Regex semantics must match glibc ERE leftmost-longest matching (`11` §R). The `o*` fixture above is a minimal acceptance test.
