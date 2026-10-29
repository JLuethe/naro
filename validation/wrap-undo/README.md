# wrap-undo — hard-wrap undo/redo combinations

Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`
Reference executable SHA-256:
`b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2`

Fresh differential replay against the pinned GNU nano 9.3 default build.
These scenarios address the documented runtime gap **Q-UNDO-002** in
`spec/99-open-questions.md` and the hard-wrap combination axis of
**NEXT-EDIT-001** in `spec/19-completion-and-release.md`.

## Cases

39 cases in `tests/follow-up/scenarios/wrap-undo.json`:

| ID | Coverage |
|---|---|
| `TEST-NEXT-UNDO-WRAP-001-MID` | Mid-line wrap: a typed character mid-line triggers a wrap at an earlier space; cursor stays on the first line; undo restores the pre-typing column. |
| `TEST-NEXT-UNDO-WRAP-002-CHAIN` | Group break: a movement that returns to the wrap cursor (Home/End) followed by more typing; the second addition is a separate undo item from the wrap+trigger. |
| `TEST-NEXT-UNDO-WRAP-003-MULTI` | Two separate wraps, each its own undo group because `hard_wrap` closes the group with a `last_kind` reset; undo removes the second then the first, redo restores each. A single `text` step produces one `hard_wrap` call, so this is *not* two wraps in one addition group. |
| `TEST-NEXT-UNDO-WRAP-004-INDENT` | Autoindent wrap; undo restores the pre-typing cursor on the original indented line. |
| `TEST-NEXT-UNDO-WRAP-005-SPILL` | Spillage join with redo and continued editing; undo removes the join then the first wrap, redo restores each, and a further wrap after redo splits because the spillage pointer was cleared by undo (matching the reference). The continuation remainder is ` fff` (3 bytes), so 3 + 7 ≤ fill 12 and the join would be accepted if the pointer were valid. |
| `TEST-NEXT-UNDO-WRAP-006-PREFIX` | Short-overflow / non-matching prefix: the overflow line is shorter than the indent; the join must not strip a non-matching prefix nor panic. Saves the joined bytes. |
| `TEST-NEXT-UNDO-WRAP-007-INSERT` | Insert above the predecessor: the live overflow moves one line down and the spillage pointer has to follow the overflow's identity, not its index; the next wrap really joins the moved overflow (`xy cccc`). Saves bytes. |
| `TEST-NEXT-UNDO-WRAP-008-DELETE` | Delete that removes the target node: the Delete at the end of the predecessor joins it with the overflow, so the overflow's node is freed and the pointer names a freed node; the next wrap must not join the unrelated successor `TAIL`. Saves bytes. |
| `TEST-NEXT-UNDO-WRAP-009-REDO` | After undo then redo of the spillage join, the spillage pointer must be cleared so a further wrap splits (matching the reference's `delete_node`/clear-on-undo lifetime). The continuation remainder is ` fff`, so the fill accepts the join if the pointer were valid. |
| `TEST-NEXT-UNDO-WRAP-010-UNDO-ONE` | Undo only the second wrap; the spillage pointer must be cleared by the undo so the next wrap splits. The continuation remainder is ` fff`. |
| `TEST-NEXT-UNDO-WRAP-011-SAVE` | Saved-point round trip: save the first wrap (unmodified), edit (modified), undo the edit (unmodified at saved point), undo the wrap (modified past saved point), redo the wrap (unmodified), redo the edit (modified). Explicit `Modified` absence/presence assertions. |
| `TEST-NEXT-UNDO-WRAP-012-AUTOSpill` | Autoindent + spillage join with a matching indent prefix: the duplicated lead of the overflow is really stripped (`eee ccc`, not `eee     ccc`). |
| `TEST-NEXT-UNDO-WRAP-013-MISMATCH` | Mismatching nonempty prefixes: the predecessor's lead is two spaces and the target's is a two-byte quote, so the join must not strip it (`eee > ccc d`). |
| `TEST-NEXT-UNDO-WRAP-014-EMPTY` | Empty live target: the overflow is reduced to length zero by in-place deletions, which keep the node; the join is accepted and the emptied line is consumed. |
| `TEST-NEXT-UNDO-WRAP-015-TABS` | Tabs: the fixture carries a literal `0x09` lead (not an interactively typed tab, which would expand to spaces); the duplicated tab lead of the target is matched and stripped. |
| `TEST-NEXT-UNDO-WRAP-016-UTF8` | UTF-8 multibyte: a second wrap joining a remainder that ends in a multibyte character (€); the prefix-skip respects character boundaries. |
| `TEST-NEXT-UNDO-WRAP-017-WSTRAIL` | Whitespace at the join point: the target starts with a blank, so the reference removes the extra blanks and exactly one space separates the remainder from the target (`fff ccc ddd`). |
| `TEST-NEXT-UNDO-WRAP-018-REJECT` | Fill-rejected join: the remainder plus overflow exceed the fill, so the join is rejected and the wrap splits. |
| `TEST-NEXT-UNDO-WRAP-019-TRIM` | Trimblanks on, cursor before the wrap point: the typed blank is protected; the trim removes only trailing break blanks after it. |
| `TEST-NEXT-UNDO-WRAP-020-DELJOIN` | Decisive Delete-join undo: remainder ` fff` (3 bytes) + `eee ddd` (7 cols) = 10 ≤ 12, so marker validity decides; the reference does not restore the spillage pointer (undo JOIN recreates a new node), so the next wrap splits (`fff` above `eee ddd`) rather than joining into `fff eee ddd`. Saves bytes. |
| `TEST-NEXT-UNDO-WRAP-021-DIVERGE` | Divergent edit invalidates redo: after undo and one redo, a new edit discards the remaining redo history; an explicit redo reports Nothing to redo and changes nothing. |
| `TEST-NEXT-UNDO-WRAP-022-NULBEFORE` | Embedded NUL before the wrap point (fixture `aaa\0bbb cccc`; the NUL stays on the first line after the split); the NUL is a payload byte and must survive the wrap split and undo/redo. |
| `TEST-NEXT-UNDO-WRAP-023-NULAFTER` | Embedded NUL after the wrap point (in the remainder); the NUL must survive the wrap split and undo/redo as a payload byte. |
| `TEST-NEXT-UNDO-WRAP-024-BSPJOIN` | Decisive Backspace-join equivalent of 020: position at the start of the spillage target and Backspace to join it into the predecessor; the reference does not restore the spillage pointer, so the next wrap splits. Saves bytes. |
| `TEST-NEXT-UNDO-WRAP-025-CHAIN-REDO` | Ordinary-addition redo continuation (integrated from the finder suite): wrap, separate non-wrapping addition, undo both, redo both, then wrap the predecessor again; the reference's ADD redo never reassigns the spillage pointer, so the next wrap splits rather than joining. |
| `TEST-NEXT-UNDO-WRAP-026-CUT-TAIL` | Whole-line cut of the spillage target: the cut detaches the target into the cutbuffer, leaving ordinary successor text `TAIL` below the predecessor; a fill-accepted wrap of the predecessor splits because the cut node's generation leaves the buffer. Saves bytes. |
| `TEST-NEXT-UNDO-WRAP-027-NUL-JOIN` | Production NUL join through the live overflow target: a payload NUL in the spillage target is joined by an accepted second wrap; the production `decode_nuls` path preserves it as a payload byte (0x00) in the saved file. A regression that removes `decode_nuls` from the join corrupts this case. |
| `TEST-NEXT-UNDO-WRAP-028-MARK` | Explicit mark through a spillage join: the mark is set on the overflow, the join moves it to the continuation, and the following cut removes only the text between the cursor and the mark (`aaa bbb ccc  ` / `eeedd`). A mark clamped to the start of the replaced span cuts the whole buffer. |
| `TEST-NEXT-UNDO-WRAP-029-EMPTY-DEL` | Delete that joins an empty predecessor with its successor: the join frees the lower node, so the spillage pointer names a freed node and the next wrap must split (`eee` above `ddd`). |
| `TEST-NEXT-UNDO-WRAP-030-EMPTY-BSP` | Backspace equivalent of 029. |
| `TEST-NEXT-UNDO-WRAP-031-PARTIAL-CUT` | Partial multiline cut of the target: the top node survives and the bottom node is detached, so the pointer names a freed node and the next wrap must split (`eee` above `dd`). |
| `TEST-NEXT-UNDO-WRAP-032-QUOTE` | Quote prefix: the default `quotestr` matches the leading `> `; the reference copies the quote lead to the continuation and restores the cursor to column 10 (`> aaa bbb ` / `> ccc dddX`). |
| `TEST-NEXT-UNDO-WRAP-033-CONT-INDENT` | Continuation autoindent: the reference samples the next line when it is in the same paragraph and is not a paragraph start, so the continuation gets the two-space indent of `  zzz` and not the four-space indent of the wrapped line. |
| `TEST-NEXT-UNDO-WRAP-034-FILL-ZERO` | Nonpositive fill with line numbers: the reference wraps at the terminal width (80 columns) and not at the margin-reduced edit width, so a fill of 0 keeps the 78-byte line unwrapped. |
| `TEST-NEXT-UNDO-WRAP-035-FILL-NEG` | Negative fill with line numbers: the reference wraps at `COLS + fill` (72 columns), so the break is before `ccc` (`cccX`, not `bb cccX`). |
| `TEST-NEXT-UNDO-WRAP-036-ONECHAR` | One-character live target: the overflow is reduced to one character by in-place deletions, which keep the node; the join is accepted (`eee c`). |
| `TEST-NEXT-UNDO-WRAP-037-PASTE` | Paste into the live target: a bracketed paste edits the overflow without freeing the node, so the pointer still names it and the join is accepted (`eee Zddd`). |
| `TEST-NEXT-UNDO-WRAP-038-PASTE-SHIFT` | Multi-line paste that shifts the live target: the pointer names the target's identity, not its index, so the join still happens (`eee ddd`). |
| `TEST-NEXT-UNDO-WRAP-039-MARK-SHIFT` | Explicit mark on a line below the wrapped line: the continuation is inserted above the marked line, so the marked node moves down by one; the cut of the marked region must follow the moved mark. |

## Result

39/39 exact matches: screen rows, cursor, terminal modes, exit status, fixture
bytes and `capture_file` saved-byte checks. No declared deviations. Both
harness statuses are 0. The report is `target/next-wrap2/report.json`; the
machine-checked manifest accepts it (`python3 tools/check_wrap_undo.py
--report target/next-wrap/report.json`).

The eight defects that the review reproduced against the pinned reference
(without a source change) are now fixed and covered by the decisive cases
`028-MARK` … `035-FILL-NEG` and `039-MARK-SHIFT`. The pre-fix candidate (`e70159f7…`) still fails
exactly those eight cases; the current candidate matches all 38.

| Case | What it decisively exercises |
|---|---|
| `028-MARK` | The explicit mark through the spillage join and the split. The reference maps the mark from the eaten line onto the joined line and then onto the continuation; the old candidate clamped it to the start of the replaced span and the following cut removed the buffer. |
| `029-EMPTY-DEL`, `030-EMPTY-BSP` | A join over an empty predecessor keeps the *top* node and frees the lower one, so the spillage pointer names a freed node. The old heuristic treated the empty predecessor as a whole-line cut and kept the lower node. |
| `031-PARTIAL-CUT` | A partial multiline cut keeps the top node and detaches the bottom one, even though the cut starts at column zero. The old heuristic kept the bottom node. |
| `032-QUOTE` | The quote lead is part of the line's lead, is copied to the continuation and suspends the automatic indentation for the split. |
| `033-CONT-INDENT` | The continuation indent is sampled from the next line when it is in the same paragraph and is not a paragraph start. |
| `034-FILL-ZERO`, `035-FILL-NEG` | A nonpositive fill wraps at the terminal width (`COLS + fill`), not at the margin-reduced edit width. |
| `020-DELJOIN`, `024-BSPJOIN` | Undo of a Delete/Backspace join that freed the spillage target, then a fill-accepted second wrap whose marker validity (not fill rejection) determines the result. |
| `025-CHAIN-REDO` | The ordinary-addition redo continuation that resurrects a stale marker when the wrap is undone and redone; the next wrap must split, not join. |
| `026-CUT-TAIL` | Whole-line cut of the spillage target, leaving ordinary successor text below; the cut detaches the target so the next wrap splits, not joining the successor. |
| `027-NUL-JOIN` | A payload NUL in the live overflow target exercised through an actual production second-wrap join. Removing `decode_nuls` from the production join path corrupts this case. |

## Implementation notes

`Editor::hard_wrap` follows the reference's `do_wrap` operation sequence
instead of replacing the two lines in one generic splice: the wrap point
(`break_line`), the optional added space, the join with the overflow line,
the removal of the duplicated prefix, the removal of the extra blanks, the
optional blank trim and the `do_enter` split. Each step has an effect on the
explicit mark and on the identity of the lines, so the mark is mapped with
the reference's `expunge` and `do_enter` rules:

* a mark on the eaten (overflow) line moves onto the joined line, offset by
  the join position;
* a mark behind the join point shifts back over the removed prefix and the
  removed blanks;
* a mark behind the wrap point moves to the continuation line, offset by the
  continuation's indentation;
* the reference's own quirk is reproduced: a quote lead is prepended to the
  continuation without moving a mark that is already on it.

Undo and redo still clear the mark, as the reference does.

Line identity is a stable per-line **generation** carried in parallel with
`State.lines` (`State.generations`). A line keeps its generation across
in-place edits; a freed line discards it; a newly created or recreated line
(including a line recreated by undo/redo of a join, Enter or cut) gets a
fresh generation. `Buffer::replace` takes an explicit `Splice` policy
instead of inferring the survivor from the endpoint coordinates:

| `Splice` | Operation | Surviving node |
|---|---|---|
| `Plain` | insertion, in-place edit, search and replace | the top node; inserted lines are new |
| `Join` | a line break is deleted (`expunge`) | the top node; the bottom node is freed |
| `Cut` | a region is cut (`extract_segment`) | a whole-line cut keeps the bottom node, any other cut keeps the top node |
| `Replace` | a region is replaced wholesale (filter output) | no node; every resulting line is new |

The previous coordinate heuristic also matched a join over an empty
predecessor and a partial multiline cut, which is why the emptied-predecessor
and partial-cut joins used the wrong node. `Buffer::undo`/`redo` reassigns
fresh generations to lines whose snapshot generation is no longer live, so a
recreated node cannot inherit the old spillage. The join condition compares
the live `spillage` generation to the generation currently at the successor
line. `hard_wrap` sets `spillage` to the new continuation line's generation.

The quote prefix and the indentation of the line's lead now come from the
reference's `quote_length` plus `indent_length`; a quoted line suspends the
automatic indentation for the split and copies its quote lead to the
continuation. A nonpositive fill uses the terminal width (`COLS + fill`).
The continuation's indentation is sampled from the next line when that line
is in the same paragraph and is not a paragraph start.

The independently supported `last_kind` reset (a hard wrap closes the
addition group) is retained.

## Reproduce

Use a **new** output directory per run (the runner refuses to overwrite
existing evidence):

```sh
cargo build --release --target-dir target/next-default
python3 tools/check_follow_up.py --suite wrap-undo \
    --binary target/next-default/release/naro --out target/next-wrap2
python3 tools/check_wrap_undo.py --report target/next-wrap/report.json
```

`target/next-default/release/naro` is the candidate;
`~/src/nano-install/default/bin/nano` is the pinned reference. The runner
copies both into the output directory, records their SHA-256, drives each
scenario through both, compares file bytes, modified/saved state, cursor and
screen behavior through undo and redo, and writes `report.json` plus per-case
`result.json` trees.

`python3 tools/check_wrap_undo.py` validates the manifest (the exact 38 case
IDs, no gaps, the fixture and expectation structure) and, with `--report`,
the recorded evidence: the exact result membership, every per-side assertion
and comparison flag, the summary counts, both harness statuses, the pinned
reference commit and executable, the candidate's source fingerprint (the
`build.rs` convention) and the scenario digest of the inputs that were
replayed. A printed digest is not a validation and a self-reported boolean is
not accepted on its own; the negative tests in `tools/test_check_wrap_undo.py`
cover the failure modes.

## Scenario hash conventions

`coverage.json` records three scenario hashes, which differ by serialization
convention:

| Label | Serialization | SHA-256 |
|---|---|---|
| `scenario_sha256_canonical` | parsed JSON, sorted keys, compact separators | `7856d86b…` |
| `scenario_sha256_raw` | current source file bytes | `0089d12b…` |
| `scenario_sha256_runner` | runner's frozen `json.dumps(cases, indent=1) + '\n'` | `0ab3bcd8…` |

The canonical hash is the stable identifier; the raw and runner hashes are
preserved for traceability. The runner hash is the one the report binds to.

## Source/build provenance

| Identity | SHA-256 |
|---|---|
| Candidate binary | `ebb1f6b4b731a8340d4e2ead9e9e82a8e2220297018dab2685271f9948054d52` |
| Source fingerprint (build.rs convention) | `522a6c33202ed6de6abe209bbe86e5f86a7ff49d0de0f41da11dca9f75a45e4e` |
| Pinned reference | `b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2` |

The candidate was built from the current working tree (revision `823cb96`)
with `cargo build --release --target-dir target/next-default` (default
profile, features `""`). The source fingerprint is the complete `src`,
`native`, `assets`, `Cargo.toml`, `Cargo.lock`, `build.rs` and `CREDITS.md`
sha256sum-of-sha256sums, matching the value embedded by `build.rs` and
emitted by `NARO_BUILD_INFO=1 ./naro`.

### Work-root caveat for the retained baseline

The full baseline (`tools/validate_parallel.py`) compares the candidate
against the **retained** reference recordings in `spec/evidence/runs/`.
Those recordings contain the fixture path, and a message that names the path
is centered in the terminal, so the work root has to be the default
`/tmp/nanospec-work` for the rendered text to have the same length. A longer
work root makes ten unrelated baseline cases (the browser's `DIR:` line and
the centered `[ Mistakes in … ]` message) differ in padding only. The
follow-up suites run both sides in the same run and are unaffected.

## Remaining limits

The following remain unimplemented or not separately verified at runtime:

* the interactions of hard wrapping with **soft wrap**, **view mode**,
  **terminal resize** and the magic-line `WAS_BACKSPACE_AT_EOF` undo quirk;
* the combination of hard wrapping with **paste**, **justification**,
  **file insertion** and **external tools** beyond the paste cases
  `037-PASTE`/`038-PASTE-SHIFT` (their node lifetimes are implemented with
  the same explicit splice policies, but no differential case covers them);
* the reference's guard that skips the separating space when the joined
  remainder itself ends in a blank is not reachable through typing: the wrap
  point is always the end of the last blank run inside the wrap column, so
  the remainder starts with a non-blank, and the wrap triggers at exactly one
  column past the wrap column, so the remainder cannot end with a blank
  either. `017-WSTRAIL` therefore covers the reachable whitespace branch of
  the join (the extra blanks at the join point are removed);
* the **tiny profile**, which has no undo/redo or hard wrap at all (doc 22) —
  by design, not an unfinished feature.

See `spec/06-undo-redo.md` §4 and `spec/99-open-questions.md` (Q-UNDO-002).
