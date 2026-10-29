# 06 — Undo and redo

Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

Scope: which operations are undoable, how they are grouped, what undo and redo
restore (text, cursor, mark, modified state), the saved-state marker, redo
invalidation, and messages. Not available in tiny builds (no undo/redo at
all; ^Z/^Y/M-U/M-E unbound).

Inventory: [`data/undo-types.csv`](data/undo-types.csv). Evidence:
`evidence/runs/TEST-UNDO-*`, `TEST-EDIT-025`, `TEST-INPUT-005`.

---

## 1. Model

### UNDO-001 — Per-buffer history
Each buffer has a linear history of undo items and a *current* pointer: items
above it can be redone, items below it can be undone. Closing a buffer discards
its history. Items are never limited in number. The cutbuffer is not part of the
history; zap and chop-word keep their own copies inside their items.
- **Source:** `src/definitions.h:503-528, 587-594`; `src/text.c:926-1095`.

### UNDO-002 — New edits discard redo
Creating a new item (any undoable action) first discards all items that were
undone and not redone. Then the item is added, and "last action" is set to its
kind. After that, redo reports `Nothing to redo` (TEST-UNDO-004).

### UNDO-003 — Grouping
- **ADD (typing):** an addition continues the current ADD item only if the previous action was an addition **and** the cursor is exactly at the place where that addition ended (same line and offset). Separate bursts typed contiguously therefore form one item; typing after moving away (even back to the same spot after a movement command) starts a new one. Movement commands do not reset the "last action" by themselves, but they change the cursor, so the next typing starts a new item, except after a movement that ends exactly at the item's end (TEST-UNDO-001).
- **BACK / DEL:** a deletion continues the current item if the previous action was the same kind (Backspace vs Delete are different) on the same line, and the deleted character is adjacent: for Delete, at the same offset; for Backspace, immediately before the previous start. Otherwise a new item. Deleting a line break creates a separate **JOIN** item (TEST-UNDO-002/-006).
- **CUT:** consecutive cuts in one chain (`05` EDIT-031) form one item. A cut after the chain was broken starts a new item. **ZAP** likewise for consecutive zaps.
- **PASTE, INSERT, ENTER, REPLACE, INDENT, UNINDENT, COMMENT, UNCOMMENT, CUT_TO_EOF:** one item each.
- **Compound operations** are bracketed by COUPLE_BEGIN … COUPLE_END and undone/redone as one step: *justification* (paragraph, whole file, or selection), *filtering* (`|command`), *spelling correction* with an external speller, *formatting*. Their messages use the operation's name (`Undid justification`).
- **Automatic hard wrapping** adds SPLIT_BEGIN/SPLIT_END around the wrap's own items (an ADD of a space, a DEL join, an ENTER). One undo removes the wrap and the triggering typed text item, together reported as `addition`.
- **Bracketed paste** produces one PASTE item (`03` INPUT-009; TEST-INPUT-005).
- **Word completion** inserts with ADD (typing right after it extends the item, TEST-EDIT-025).
- Not undoable (no item): cursor movement, mark changes, toggles, saving, anchors, the cut chain itself.

### UNDO-004 — Item contents (normative effect)
Each item records the cursor position before and after, the character count
before and after, the affected text and flags. Requirements per kind:

| Kind | Undo restores | Redo re-applies | Cursor after undo / redo |
|---|---|---|---|
| ADD | removes the added bytes; if the addition created the magic line, removes it again | re-inserts; re-creates the magic line if needed | start / end of the addition |
| ENTER | re-joins the two lines (restoring removed auto-indent blanks) | splits again (with the same indentation) | original position (end of indentation when an all-blank line was trimmed) / start of the text on the new line |
| BACK, DEL | re-inserts the deleted characters | deletes them | after (BACK) or at (DEL) the restored text / at the deletion point |
| JOIN | splits the line again | joins again | end of the first line or start of the second, as before the join |
| JOIN from Backspace at the start of the magic line | nothing to restore; cursor goes to the start of the last line | nothing changes; cursor to the join position | see UNDO-007 |
| REPLACE | restores the line's previous text (whole line swap) | swaps again | start of the match |
| CUT, CUT_TO_EOF, ZAP | re-inserts the cut text at its start (whole-line cuts at x=0) | cuts the same span again (zaps don't touch the cutbuffer) | cursor at the start, or at the end when the cursor was at the end of a region |
| PASTE | removes the pasted text | pastes the recorded text (not the current cutbuffer) | start / end |
| INSERT (file / command output) | removes it | re-inserts it | start / end |
| INDENT/UNINDENT/COMMENT/UNCOMMENT | removes/adds the recorded per-line indentation or comment marks | applies them again | recorded position |
| COUPLE | undoes/redoes the 3 inner items as one step, and restores the screen row of the cursor | | |

- An inherited anchor at the start of a cut is cleared on undo, unless the user placed it.
- **Source:** `src/text.c:452-845, 954-1230`.
- **Evidence:** runtime TEST-UNDO-001…011.

### UNDO-005 — Messages and side effects
- Undo: HUSH `Undid <noun>`; redo: HUSH `Redid <noun>`. Nouns: `addition`, `line break`, `deletion`, `line join`, `replacement`, `erasure`, `cut`, `paste`, `insertion`, `indent`, `unindent`, `comment`, `uncomment`, or the compound name (`justification`, `filtering`, `spelling correction`, `formatting`). Translated. No message in *zero* mode, and no undo message while a word-completion run is active.
- Empty history: AHEM `Nothing to undo` / `Nothing to redo` (TEST-UNDO-001).
- After undo or redo: the mark is removed, the preferred column is set to the cursor column, the character count is set to the recorded value, and "last action" is reset (so the next typing starts a new item).
- In view mode, undo and redo are not refused (they are not "changing" functions in nano's list), but the history is empty because nothing can be edited. *(Inferred.)*
- **Source:** `src/text.c:495-845`.

### UNDO-006 — Saved state
When the buffer is written in full under its name, the current history position
is remembered as the *saved point*. After an undo or redo, if the current
position equals the saved point, the buffer becomes **unmodified** (title bar
updated). Otherwise it becomes modified. The initial state of a freshly opened
buffer counts as a saved point (TEST-UNDO-001: undoing all typing returns to
unmodified). Undo across the saved point marks the buffer modified again, and redo
back to it unmodified (TEST-UNDO-003). Redo of an INSERT that inserted nothing
does not set modified.
- **Source:** `src/text.c:670-675, 839-844`; `src/files.c:1970-1972`.

### UNDO-007 — Backspace at the start of the magic line (quirk)
Backspace at x=0 on the empty last line moves the cursor to the end of the
previous line and deletes nothing (`05` EDIT-020), but still records a JOIN item
marked "backspace at EOF". Undoing it only moves the cursor to the start of the
last line. Redoing it only moves the cursor back to the end of the previous line,
**and marks the buffer modified** although the text is unchanged (TEST-UNDO-009).
Reproduce as observed.

### UNDO-008 — Interaction with other features
- Search/replace: each replacement is one REPLACE item. A replace-all run produces one item per replacement (undo steps back one at a time).
- External commands at the Execute prompt: inserted output is one INSERT item. With `|` (filter), COUPLE(CUT + INSERT) named `filtering`. If the command fails (ALERT), the operation is undone **and discarded** from the history (`12` FEAT-EXEC).
- Spell check with the internal speller: each replacement is a REPLACE item. With an alternative speller: COUPLE named `spelling correction`.
- Macros replay keystrokes and create ordinary items.
- Automatic hard wrapping and the spillage-line join are covered by fresh differential cases `TEST-NEXT-UNDO-WRAP-001-MID` through `TEST-NEXT-UNDO-WRAP-039-MARK-SHIFT`; see `../validation/wrap-undo/README.md`.
- **Source:** `src/files.c:1128-1132`; `src/text.c:2064-2107`.

## 2. Original implementation notes
- `undostruct` keeps `head_lineno/head_x`, `tail_lineno/tail_x`, `strdata`, `wassize/newsize`, `cutbuffer`, `grouping` (per-line indentation strings for INDENT/UNINDENT/COMMENT), `xflags` (`WAS_BACKSPACE_AT_EOF`, `WAS_WHOLE_LINE`, `INCLUDED_LAST_LINE`, `MARK_WAS_SET`, `CURSOR_WAS_AT_HEAD`, `HAD_ANCHOR_AT_START`).
- Lines are located by line number (`line_from_number`), so items stay valid as long as history is applied in order.
- SPLIT_BEGIN is inserted *below* the triggering item.

## 3. Evidence summary
| Requirement | Evidence |
|---|---|
| UNDO-002 | runtime TEST-UNDO-004 |
| UNDO-003 | runtime TEST-UNDO-001/-002/-005/-006/-008, TEST-INPUT-005, TEST-EDIT-025; fresh `TEST-NEXT-UNDO-WRAP-001-MID`…`039-MARK-SHIFT` |
| UNDO-004/005 | runtime TEST-UNDO-001…011, source; fresh `TEST-NEXT-UNDO-WRAP-001-MID`…`039-MARK-SHIFT` |
| UNDO-006 | runtime TEST-UNDO-001/-003 |
| UNDO-007 | runtime TEST-UNDO-009 |
| UNDO-008 | source; fresh `TEST-NEXT-UNDO-WRAP-001-MID`…`039-MARK-SHIFT` |

## 4. Open questions
- **Q-UNDO-001:** the redo of a no-op Backspace at EOF setting *modified* (UNDO-007) looks unintended, but it is deterministic and harmless. Proposed: reproduce.
- **Q-UNDO-002:** hard-wrap undo in all chunk combinations. **Partially covered** for the default profile by the 39-case differential suite `TEST-NEXT-UNDO-WRAP-001-MID` … `039-MARK-SHIFT` (mid-line wrap; group break; two separate wraps; autoindent; spillage join with redo and continued editing; short-overflow/non-matching-prefix; spillage generation identity through structural undo/redo, whole-line cut and ordinary-addition redo; divergent edit; save/`Modified` round trip; autoindent+spillage; mismatching nonempty prefix; empty and one-character targets; tabs; UTF-8; whitespace at the join point; fill-rejected join; trimblanks; undo of Delete/Backspace join; whole-line cut of the target; production NUL join; the explicit mark through a join; the quote prefix; the continuation indent; the nonpositive fill geometry; a paste that edits or shifts the live target); see `../validation/wrap-undo/README.md`. All 39 cases match the pinned reference exactly. The spillage marker is a stable per-line generation, every splice states which node survives (a join keeps the top node, a whole-line cut keeps the bottom node, a partial multiline cut keeps the top node), and the explicit mark follows the reference's `expunge`/`do_enter` rules through the join, the added space, the prefix removal, the blank trimming and the split. Reproduced and fixed: F1 unsafe prefix removal (crash), F2 embedded-NUL corruption (including the production join path), F3/R1 stale spillage identity across structural edits and whole-line cut, F4/R2 structural and ordinary spillage lifetime through history, R3 trimblanks cursor hazard, the explicit-mark corruption, the operation-specific survivor identity, the missing quote prefix, the reduced-width fill geometry and the continuation indent sampling. A machine-checked manifest (`tools/check_wrap_undo.py`) validates the exact 39 scenario IDs, no gaps, the report's per-side assertions, the pinned reference and candidate provenance and the scenario digest; `tools/test_check_wrap_undo.py` covers the failure modes. Remaining limits: the interactions of hard wrapping with soft wrap, view mode, terminal resize and the magic-line `WAS_BACKSPACE_AT_EOF` undo quirk are not separately verified; the **tiny profile** has no undo/redo or hard wrap by design (doc 22).
