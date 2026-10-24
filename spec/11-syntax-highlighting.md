# 11 — Syntax highlighting and the regex contract

Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

Scope: selecting a syntax for a buffer, applying single-line and multiline
color rules, updating after edits and scrolling, the bundled syntax files, and
(§R) the regular-expression dialect shared by search, replace, highlighting,
syntax selection and the quoting regex. Color builds only (absent in tiny).

Inventory: [`data/syntaxes.csv`](data/syntaxes.csv) (44 bundled syntaxes with
their file regexes, header/magic regexes, comment/linter/formatter/tabgives
strings, rule counts, license line). Evidence: `evidence/runs/TEST-SYN-*`,
TEST-REND-019, TEST-RC-005/-006, and the regex corpus
`evidence/regex/cases.tsv` + `results-*.jsonl` (81 cases run through glibc in
two locales by `tools/regex/regex_probe.c`).

---

## 1. Syntax selection

### SYN-SELECT — Which syntax a buffer gets
Determined when a buffer is opened (also for stdin and the help viewer), and
again when it is saved under a new name:
1. No syntax defined at all (no rcfiles, `-I`) → none.
2. A command-line syntax name (`-Y NAME`): `none` → no syntax. Otherwise the syntax with that name (the most recently defined one wins). If none has that name: ALERT `Unknown syntax name: <name>` (not in the help viewer), and continue with step 3.
3. **File regexes:** each syntax's file regexes are tested (unanchored, case-sensitive, `REG_NOSUB`) against the buffer's **canonical absolute path** (or the name as given if it cannot be resolved). The first syntax in **reverse order of definition** with a matching regex wins. A later definition in the rcfiles therefore overrides an earlier one (TEST-SYN-001), and a regex may match directory parts (TEST-SYN-008: `/sub/`).
4. **Header regexes:** tested against the first line of the buffer, same order (TEST-SYN-002).
5. **libmagic** (with `--magic`/`set magic`, libmagic builds): if the file exists, libmagic's description of it (following symlinks) is tested against the `magic` regexes. Failures → ALERT `magic_load() failed: <reason>` or `magic_file(<name>) failed: <reason>`.
6. The syntax named `default`, if defined (TEST-SYN-003).
7. Otherwise none.
- On first use, the syntax's full definition is loaded (`10` RC-SYNTAX lazy loading), and its colors are assigned color pairs (equal fg/bg combinations share a pair).
- The help viewer always uses the syntax `nanohelp` when defined.
- **Source:** `src/color.c:124-231`.
- **Evidence:** runtime TEST-SYN-001…005, -008, -009.

### SYN-TOGGLE — Turning colors off
`M-Y` (*nosyntax*) toggles highlighting for display (`Color syntax highlighting
disabled/enabled`, TEST-SYN-010). The syntax stays attached, so commenting,
linter, formatter and tabgives still work. Without terminal color support, no
color is shown, but the other syntax features still apply.

## 2. Applying rules

### SYN-RULES — Painting order
For each visible row, after the text is drawn (`04` REND-035), each rule of the
syntax is applied in definition order, so later rules overwrite earlier ones
(TEST-SYN-006: `bold,white "q"` overrides `red "^q"`; `icolor magenta "zz"`
overrides the cyan multiline region). A rule's attribute is its color pair plus
bold/italic.

### SYN-SINGLE — Single-line rules
For a rule with one regex: starting at byte 0, repeatedly find the next match
in the line, with `REG_NOTBOL` for searches not starting at 0. Paint
`[so, eo)`, then continue at `eo`. Zero-length matches are not painted; the
search steps one character forward. Searching stops at byte 2000 of the line,
or when a match starts beyond the visible part. Only the visible part is
painted.
- **Source:** `src/winio.c:2606-2649`.

### SYN-MULTI — Multiline rules (`start=`/`end=`)
Per line and per multiline rule, nano keeps a state:
NOTHING / STARTSHERE / WHOLELINE / ENDSHERE / JUSTONTHIS. Requirements:
1. **Region semantics:** a region starts at a match of `start` and ends at the end of the first match of `end` found **after** the start match (searching from the start match's end, possibly on later lines). The text from the start match's start to the end match's end is painted. When no end follows in the rest of the file, the region runs to the end of the file.
2. **Within a line:** after a region closes, searching for the next `start` continues after the end match (REG_NOTBOL). Several regions can exist on one line (TEST-SYN-006 line 4). Empty regions (zero-length start and end at the same place) are not painted. When both start and end are zero-length, the search advances one character.
3. **Continuation:** a line following a line where a region is open (STARTSHERE or WHOLELINE) is first searched for `end` from offset 0. No match: the whole line is painted (WHOLELINE). Match: paint up to its end (ENDSHERE), then look for new starts after it.
4. Zero-length `start="^"`, `end="$"` paints each whole line (TEST-SYN-007).
5. Start matches beyond byte 2000 of a line are not considered.
- **Source:** `src/winio.c:2651-2734`; `src/color.c:287-375`.
- **Evidence:** runtime TEST-SYN-006 (open region across 3 lines, closed regions on one line, unterminated region at the end), -007.

### SYN-UPDATE — Keeping colors correct after edits
After any edit, the visible screen must show colors as if every line's
multiline state were recomputed from the top of the file (the observable
requirement). nano reaches this with a per-line cache: after typing or deleting
on a line, it checks whether that line's start/end situation changed; if so it
redraws everything from that line. After structural edits (paste, cut, insert,
undo of those, justify, long jumps), it recomputes the cache for the whole
file. TEST-SYN-006 s2 (typing `>>` before `<<` on line 1) and s5 (opening a new
region at the end of the last line) show correct repainting.
- **Implementation note:** `precalc_multicolorinfo` (whole file), `check_the_multis` (one line), the flags `perturbed`/`recook`. A Rust implementation may use any incremental scheme that gives the same result.
- **Source:** `src/color.c:233-375`.

### SYN-BUNDLED — Bundled syntaxes
The installed syntax files (`share/nano/*.nanorc`) and `extra/*.nanorc` (not
installed) are listed in `data/syntaxes.csv`. They are data, not code, and the
reimplementation may ship the same files (license check per file:
`00-reference-environment.md` §1.2). A user gets them only through `include`;
nano loads no syntax by default. The `nanohelp` syntax colors the help viewer.
`default` (in `default.nanorc`) applies to otherwise unmatched files.

### SYN-STRINGS — Syntax-attached strings
- `comment "STR"`: comment marker (`05` EDIT-042). Default `#`; `""` disables commenting.
- `tabgives "STR"`: what Tab inserts (`05` EDIT-012), and what indent/unindent use.
- `linter "CMD"` / `formatter "CMD"`: `12` FEAT-LINT / FEAT-FORMAT.

---

## §R — Regular-expression contract (shared)

### REGEX-001 — Engine and flags
All regexes are POSIX regular expressions **as implemented by the C library**
(glibc 2.44 in the envelope; gnulib's replacement regex is not built in).
- Search and replace: `REG_EXTENDED`, plus `REG_ICASE` unless case-sensitive. Forward search uses `REG_STARTEND` from the cursor to the end of the line (`07` SRCH-004). No `REG_NEWLINE`.
- Highlighting: `color` → `REG_EXTENDED`; `icolor` → `REG_EXTENDED|REG_ICASE`. Matching after position 0 uses `REG_NOTBOL`.
- File, header and magic regexes: `REG_EXTENDED|REG_NOSUB`.
- Quoting regex (justify): `REG_EXTENDED`; the match must start at 0 (`12` FEAT-QUOTE).
- Compile errors are reported with the C library's `regerror` text, for example `Unmatched ( or \(`, `Invalid preceding regular expression`, `Unmatched [, [^, [:, [., or [=`, `Unmatched \{`, `Trailing backslash`, `Invalid character class name`, `Invalid content of \{\}` (corpus). Their wording is part of the observable output.

### REGEX-002 — Required matching semantics (from the corpus)
A conforming engine must reproduce, in the reference locales, every result in
`evidence/regex/results-en_US.UTF-8.jsonl` and `results-C.jsonl`. Key points:
1. **POSIX leftmost-longest**: among matches at the leftmost position, the longest is chosen (`a|ab` on `ab` → `[0,2]`; `ab|a` → `[0,2]`).
2. **POSIX subexpression rules**: `(a|ab)(c|bcd)` on `abcd` → groups `[0,1]` and `[1,4]`; `(a*)(ab)*b` on `ab` → `[0,1]` and unset; `(a|b)*` on `abab` → last iteration `[3,4]`.
3. **Back-references in ERE** (`(a)\1` matches `aa`; `\10` = `\1` followed by `0`).
4. **GNU extensions:** `\<`, `\>`, `\b`, `\B`, `\w`, `\W`, `\s`, `\S`, `` \` ``, `\'`. `\d` is **not** a digit class; it matches a literal `d`. There are no lazy quantifiers: `a+?` means `(a+)?`, which is greedy. `{,n}` is accepted.
5. **Bracket expressions:** POSIX classes (`[:alpha:]` etc.) follow the locale (`[[:alpha:]]` matches `é` in UTF-8; `[[:space:]]` does not match U+00A0 in en_US.UTF-8). Equivalence classes `[[=e=]]` match accented forms in UTF-8. Ranges `[à-ç]` use code points in UTF-8. `[]a]` and `[^]a]` follow POSIX. Unmatched `)` is a literal.
6. **Multibyte and invalid bytes (UTF-8 locale):** `.` and negated brackets match whole characters; **an invalid UTF-8 byte is not matched by `.` or `[^…]`** (`.+` on `a\xffb` matches only `a`). A literal byte in the pattern can match it. In the C locale everything is bytes.
7. **Case folding** (`REG_ICASE`) is per character via the locale (`É`↔`é` in UTF-8; not in C). There is no multi-character folding (`ß` does not match `SS`).
8. **Newlines:** without `REG_NEWLINE`, `.` and `[^x]` match 0x0A. That byte appears in line data as an encoded NUL. `^`/`$` match only at string ends (with NOTBOL for later starts).
9. **Empty matches** are allowed (`x*` on `abc` → `[0,0]`), and their use in replace-all is fixed by the fixture of `07` SRCH-006.

### REGEX-003 — Consequences for a Rust implementation
The `regex` crate (and most backtracking engines such as `fancy-regex`/`pcre2`)
**cannot** satisfy REGEX-002 as is. They use leftmost-first alternation, lack
POSIX subexpression rules, have no back-references (`regex`), treat `\d` as a
digit class, support lazy quantifiers, follow different class definitions, and
handle invalid UTF-8 differently. See `15-rust-architecture.md` §4 for the
options (FFI to the C library's POSIX regex, or a dedicated POSIX engine plus a
syntax translator). The corpus is the acceptance test.

## Original implementation notes
- `syntaxtype` (name, file/header/magic regex lists, comment, tabstring, linter, formatter, colors, `multiscore`), `colortype` (`start`, `end`, `id`, `pairnum`, `attributes`).
- `linestruct.multidata[id]` caches the multiline state per rule.

## Evidence summary
| Requirement | Evidence |
|---|---|
| SYN-SELECT | runtime TEST-SYN-001…005/-008/-009 |
| SYN-RULES/SINGLE/MULTI/UPDATE | runtime TEST-SYN-006/-007, TEST-REND-019 |
| SYN-TOGGLE | runtime TEST-SYN-010 |
| REGEX-001/002 | glibc corpus (runtime, 81 cases × 2 locales), TEST-SRCH-* |

## Open questions
- **Q-SYN-001:** The libmagic path was not runtime-probed. libmagic descriptions depend on the installed magic database version (file 5.48 here), so results are environment-specific.
- **Q-REGEX-001:** Decision required on the regex engine strategy (`15` §4). Exact parity requires POSIX semantics from the same C library.
