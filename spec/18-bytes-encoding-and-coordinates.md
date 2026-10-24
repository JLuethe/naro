# 18 — Bytes, encoding, and coordinates

Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

Scope: how text is stored (byte strings), what counts as a character in
UTF-8 and byte mode, invalid sequences, NUL bytes, character classes, display
widths, and the conversions between byte offsets, character counts and screen
columns that every other document relies on.

Evidence: `evidence/runs/TEST-BYTE-001…006`, TEST-REND-005, TEST-FILE-011,
TEST-SRCH-019, TEST-I18N-003, `evidence/regex/*`.

---

### BYTE-MODEL — Storage
1. A line is a byte string (no terminator semantics beyond the implementation). nano never converts, normalizes or validates text: files are read and written byte for byte, apart from line-ending handling (`08` FILE-READ) and BYTE-NUL.
2. Positions in the buffer (`current_x`, mark, undo records, search results) are **byte offsets**. They always lie on a character boundary (BYTE-STEP).
3. The **mode** is fixed at startup (`14` I18N-LOCALE): UTF-8 mode, or byte mode (every byte is one character).

### BYTE-NUL — NUL bytes
A NUL byte read from a file, from stdin, from the clipboard of an executed
command, or typed/pasted is stored as **0x0A** inside the line (line data never
contains a real line feed, so the two cannot be confused). It is displayed as
`^@` (2 columns), and written back as NUL (TEST-BYTE-003: `a\0b\n\0\n` → edited
→ `a\0bZ\n\0\n`). The same encoding is used in history and position files
(stored there as NUL, `12`), in file names (`04` REND-021), and in prompt
answers (`17`). A regex `.` matches the encoded NUL, since it is 0x0A without
`REG_NEWLINE` (`11` REGEX-002 item 8).
- **Source:** `src/utils.c:158-183`; `src/files.c` (read_file).

### BYTE-STEP — Character boundaries
**UTF-8 mode** — `char_length(p)` (bytes in the character at p):
- a lead byte 0xC2–0xDF followed by a continuation byte (0x80–0xBF) → 2;
- 0xE0–0xEF followed by two continuation bytes → 3, **except** overlong forms (E0 followed by 80–9F) and surrogates (ED followed by A0–BF), which count as 1;
- 0xF0–0xF4 followed by three continuation bytes → 4, except overlongs (F0 + 80–8F) and code points above U+10FFFF (F4 + 90–BF), which count as 1;
- everything else (ASCII, a lone continuation byte, C0/C1 lead bytes, F5–FF, a truncated sequence) → 1.
So each byte of an invalid sequence is a character of its own (TEST-BYTE-001: `\xe9`, `\xc0`, `\x80`, `\xed`, `\xa0`, `\x80` each took one Right press and one column).
- `step_right(p) = p + char_length`. `step_left(p)`: look back at most 4 bytes for a byte that is not a continuation byte, then walk forward with `char_length` from there to find the start of the character before p (from offset 0 when p ≤ 3). A run of more than 4 continuation bytes is stepped over one byte at a time.
- **Zero-width characters** (wcwidth 0, U+0300 and up): cursor movement (Left/Right) skips over them so the cursor never stops before a combining mark (TEST-BYTE-001: `e` + U+0301 is one step; TEST-BYTE-002). *Delete* removes the character and following zero-width characters (TEST-BYTE-002: Del on `e` removed `e` and U+0301). *Backspace* removes only the character before the cursor, so it removes a combining mark alone (TEST-BYTE-002: `xéy` → `xey`). See `05` EDIT-020.
**Byte mode:** every byte is a character; step left/right is ±1 (TEST-BYTE-005: `\xc3\xa9` is two characters in the C locale).
- **Source:** `src/chars.c:253-303, 355-397`.

### BYTE-DECODE — Code point of a character (UTF-8 mode)
`mbtowide` returns the code point for valid sequences (same validity rules as
BYTE-STEP), and failure (−1) for invalid ones. In byte mode it returns the byte
value **sign-extended** from a signed `char`: bytes ≥ 0x80 become negative
values, for which the wide-character class functions report "not a letter",
"not alphanumeric", "not punctuation", "not blank" (see BYTE-CLASS).
- **Source:** `src/chars.c:151-205`.

### BYTE-CLASS — Character classes
| Class | UTF-8 mode | Byte mode |
|---|---|---|
| blank (`is_blank_char`) | ASCII: only space and Tab; others: `iswblank` of the code point; invalid → no | `isblank` of the byte in the locale |
| alphanumeric | `iswalnum` of the code point; invalid → no | **`iswalnum` of the sign-extended byte**: bytes ≥ 0x80 are never alphanumeric (TEST-BYTE-004: in `de_DE.ISO-8859-1`, `ä` is not a word character: *next word* from `äbc` stopped at `b`, and *chop next word* deleted `ä|`) |
| punctuation | `iswpunct`; invalid → no | as alphanumeric (bytes ≥ 0x80 never) |
| control (`is_cntrl_char`) | bytes 0x00–0x1F, 0x7F, and C2 80–C2 9F (U+0080–U+009F) | bytes with `(b & 0x60) == 0` (0x00–0x1F and 0x80–0x9F) or 0x7F |
| word character | alphanumeric, or punctuation when "punctuation counts", or a character listed in `wordchars` (substring test of the character's bytes) | same rules |

Word characters drive word movement, word deletion, word completion, the word
count, whole-word spell matching, and word movement in prompts (`05`, `07`,
`12`, `17`).

The byte-mode behavior for bytes ≥ 0x80 is a reference quirk (Q-EDIT-001,
confirmed): the Rust version must reproduce it for parity in non-UTF-8 locales,
or record a deviation.
- **Source:** `src/chars.c:30-140`.

### BYTE-WIDTH — Display width (`advance_over`)
Column widths, starting from column c:
| Character | Columns |
|---|---|
| Tab | to the next multiple of `tabsize`: `tabsize − c mod tabsize` (TEST-BYTE-006 with `-T 4`) |
| other bytes 0x00–0x1F, 0x7F | 2 (`^X` form, `04` REND-020) |
| UTF-8: C2 80–C2 9F (C1 controls) | 2 |
| UTF-8: an invalid byte | 1 (shown as U+FFFD) |
| UTF-8: a valid character | `wcwidth(code point)`, or 1 when wcwidth is negative (TEST-BYTE-001: 😀 2, 日 2, U+0301 0) |
| byte mode: 0x80–0x9F | 2 |
| byte mode: 0xA0–0xFF and 0x20–0x7E | 1 |

`wcwidth` is glibc 2.44's (Unicode data of that release). The terminal must
agree for correct cursor placement; that is outside nano's control.
- **Source:** `src/chars.c:305-353`.

### BYTE-COLUMNS — Coordinate conversions
- `wideness(text, n)` = the column at which byte offset `n` starts (sum of widths of all characters that begin before n; a character that contains byte n−1 is counted whole).
- `breadth(text)` = width of the whole string.
- `actual_x(text, column)` = the byte offset of the first character whose end column exceeds `column` (or the end of the string). It maps a desired column to the character covering it, so a column inside a double-width character or a tab maps to that character's start.
- `xplustabs()` = `wideness(line, current_x)`, the cursor's column.
- **placewewant** (the remembered column for vertical movement) is a column; moving vertically puts the cursor at `actual_x(line, placewewant)` (TEST-BYTE-006: column 5 kept across Down/Up through a shorter line).
- Columns are 0-based internally; reports show them 1-based (`^C`: `col` = `xplustabs()+1` / `breadth(line)+1`, TEST-BYTE-001 `col 18/19`).
- **Source:** `src/utils.c:370-430`.

### BYTE-COUNT — Character counts
- `mbstrlen(s)` = number of characters by BYTE-STEP (invalid bytes count 1 each; a C1 control counts 1).
- The buffer's `totsize` = sum of `mbstrlen` of all lines + one per line break (the magic line adds nothing). TEST-BYTE-001: 16 characters + 1 newline = 17; TEST-BYTE-005 (C locale): 3 + 1 = 4.
- The `^C` report's `char N/T` gives N = characters before the cursor (from the top, counting a newline per line) and T = totsize (`12` FEAT-POS). The word count's character figure uses the same counting.
- **Source:** `src/chars.c:283-292`; `src/winio.c` (report_cursor_position).

### BYTE-CASE — Case-insensitive comparison
UTF-8 mode (`mbstrncasecmp`): ASCII letters compare by folding to upper case;
an ASCII letter against a non-letter compares the folded letter's lower case;
non-ASCII valid characters compare `towlower` of the code points; invalid bytes
compare as bytes and an invalid byte sorts after any valid character at the same
position. The comparison length is a number of **characters** of the needle
(TEST-SRCH-019). Byte mode: the C library's `strncasecmp`/`strcasestr` in the
locale (TEST-BYTE-004: `Ä` 0xC4 found `ä` 0xE4 in `de_DE.ISO-8859-1`).
Used by literal search, the browser sort and search, and completion sorting.
- **Source:** `src/chars.c:404-520`.

### BYTE-INVALID — Summary for invalid UTF-8
Invalid bytes are preserved on disk, step and count as single characters, are
displayed as `�` taking one column (`04` REND-020; TEST-BYTE-001), are not word
characters, never match `.` or negated brackets in regexes (`11` REGEX-002), and
compare as raw bytes case-insensitively.

## Original implementation notes
- `using_utf8` (global bool). `MAXCHARLEN` = 4 in UTF-8 builds.
- `control_mbrep` gives the second character of the `^X` form: 0x7F → `?`, U+009F → `=`, C1 controls → second byte − 0x20 shown as a character, others + 64.

## Evidence summary
| Requirement | Evidence |
|---|---|
| BYTE-NUL | runtime TEST-BYTE-003, TEST-FILE-011 |
| BYTE-STEP | runtime TEST-BYTE-001/-002/-005 |
| BYTE-CLASS | runtime TEST-BYTE-004, source |
| BYTE-WIDTH | runtime TEST-BYTE-001/-006, TEST-REND-005 |
| BYTE-COLUMNS | runtime TEST-BYTE-006 |
| BYTE-COUNT | runtime TEST-BYTE-001/-005, TEST-FEAT-019 |
| BYTE-CASE | runtime TEST-SRCH-019, TEST-BYTE-004 |

## Open questions
- **Q-EDIT-001 (resolved):** in byte mode, bytes ≥ 0x80 are not word characters because of sign extension. Confirmed by TEST-BYTE-004. Decision for Rust: reproduce (parity) — see 99.
- **Q-BYTE-001:** Screen captures in non-UTF-8 locales are unreliable under tmux (a UTF-8 terminal). Non-UTF-8 tests must assert file contents and internal reports, not screen cells (`16`).
