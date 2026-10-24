# 10 — nanorc configuration

Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

Scope: rcfile lookup, the line grammar, `set`/`unset` and every option, the
precedence between defaults, rcfiles and the command line, `include`,
`syntax` and the other syntax commands (parsing only; their effect is in `11`),
`extendsyntax`, colors, key-binding commands (semantics in `02`), and error
reporting. nanorc support is absent in tiny builds.

Inventories: [`data/nanorc-options.csv`](data/nanorc-options.csv) (70 options:
type, flag, default, validation, error template, command-line equivalent,
build condition, source line), [`data/nanorc-commands.csv`](data/nanorc-commands.csv),
[`data/color-names.csv`](data/color-names.csv).
Evidence: `evidence/runs/TEST-RC-*`, TEST-CLI-037, TEST-KEY-002…005,
`CLI-P-024…028/-043…045`.

---

### RC-LOOKUP — Which files are read
Unless `-I` (`--ignorercfiles`):
- With `-f FILE` (`--rcfile`): FILE is resolved to an absolute path. If that fails, or the path does not exist: die `Specified rcfile does not exist` (stderr, exit 1). If it exists but is a directory or device: the error `'<path>' is a directory` / `'<path>' is a device file` is recorded and the file is skipped. Otherwise only this file is read.
- Otherwise:
  1. The system rcfile `SYSCONFDIR/nanorc` (`/etc/nanorc` in usual builds; not present in the reference install), if it is readable and not a directory or device.
  2. The **first** of these that is a readable regular file: `$HOME/.nanorc`, `$XDG_CONFIG_HOME/nano/nanorc` (only if the variable is set), `$HOME/.config/nano/nanorc` (TEST-RC-001/-002/-003). If none exists and neither a home directory nor `XDG_CONFIG_HOME` is known: error `I can't find my home directory!  Wah!`.
  - The home directory is `$HOME`. If HOME is unset, or nano runs as root (euid 0), the passwd entry's directory is used.
  - A file that exists but cannot be opened: error `Error reading <path>: <reason>`. A missing file is silently skipped.
- After reading, the vital-key check runs (`02` KEY-035).
- With `--enable-altrcname=NAME` builds, `.nanorc` and `nanorc` are replaced by NAME.
- **Source:** `src/rcfile.c:1691-1749, 881-897`; `src/utils.c:31-52`.
- **Evidence:** runtime TEST-RC-001…003, CLI-P-026, TEST-CLI-051.

### RC-LINE — Line grammar
1. Lines are read with `getline` (any length). A trailing LF is removed, then a trailing CR (DOS-style rcfiles work, TEST-RC-004 lines 24/35).
2. Leading blanks (space/Tab) are skipped. Empty lines and lines whose first non-blank character is `#` are ignored. There are no trailing comments: `#` later in a line is part of the arguments.
3. The first word (up to a blank) is the command. Words are separated by runs of blanks.
4. Commands are case-sensitive: `set`, `unset`, `bind`, `unbind`, `include`, `syntax`, `header`, `magic`, `color`, `icolor`, `comment`, `tabgives`, `linter`, `formatter`, `extendsyntax`. Anything else: `Command "<word>" not understood` (TEST-RC-004 line 31).
5. **Quoted arguments** (option values, bind strings): an argument starting with `"` ends at the **last** `"` on the line, so it may contain `"`. Text after that quote is ignored. A missing closing quote: `Argument '<rest of line>' has an unterminated "` (TEST-RC-004 line 25). There is no escape character.
6. **Regex lists** (`syntax`, `header`, `magic`, `color`/`icolor`): each regex starts with `"` and ends at a `"` that is followed by a blank or the end of the line. So `"a"b"` is the single regex `a"b`. A regex not starting with `"` → `Regex strings must begin and end with a " character`; an empty regex `""` → `Empty regex string`.
- **Source:** `src/rcfile.c:1376-1689, 532-615`.

### RC-SET — `set` and `unset`
- `set`/`unset` without an option name: `Missing option`. An unknown name: `Unknown option: <name>` (names are case-sensitive).
- **Boolean options** (those with a flag in `data/nanorc-options.csv`): `set` turns the flag on and `unset` turns it off. **Extra words after the name are ignored** (TEST-RC-004 line 3).
- **Value options:** `unset` → `Cannot unset option "<name>"`. A missing value → `Option "<name>" requires an argument`. The value may be quoted (RC-LINE 5). In a UTF-8 locale a value that is not valid UTF-8 → `Argument is not a valid multibyte string`. Validation per option:

| Option | Validation and effect |
|---|---|
| `fill` | integer (`parse_num`); invalid → `Requested fill size "<v>" is invalid` and fill reset to −8 |
| `tabsize` | integer > 0; invalid → `Requested tab size "<v>" is invalid` and reset to default (8) |
| `guidestripe` | integer > 0; invalid → `Guide column "<v>" is invalid` and reset to 0 (off) |
| `matchbrackets` | no blanks (`Non-blank characters required`), an even number of characters (`Even number of characters required`) |
| `whitespace` | exactly 2 characters, each 1 column wide (`Two single-column characters required`) |
| `punct`, `brackets` | no blank characters (`Non-blank characters required`) |
| `quotestr` | stored; compiled at startup (`01` CLI-023) |
| `speller` | stored; leading blanks stripped after all rcfiles |
| `backupdir`, `operatingdir` | stored; validated at startup (`01` CLI-021/-022); `operatingdir` is ignored in restricted mode |
| `wordchars` | stored as is |
| color options | RC-COLOR |

- Later `set`s override earlier ones within and across rcfiles. Precedence with the command line: `01` CLI-014.
- `set` of a boolean flag that the command line also sets: the command line wins for "on"; nothing in an rcfile can turn off a command-line flag.
- Deprecated names still accepted: `multibuffer` (= `newbuffer`) and `nowrap` (its inverse effect: `unset nowrap` turns breaklonglines on, TEST-RC-010).
- `modernbindings`, `view`, `restricted`, `noread`, `ignorercfiles`, `rcfile`, `listsyntaxes`, `syntax` (as an option), `version`, `help` and `magic`-less builds' `magic` are **not** nanorc options.
- **Source:** `src/rcfile.c:41-143, 1526-1679`.
- **Evidence:** runtime TEST-RC-004, -007…-011.

### RC-COLOR — Color specifications
Syntax: `[bold,][italic,]FG[,BG]`. FG and BG are color names. Either may be
empty (`,green` sets only the background). The `bold`/`italic` prefixes must be
followed by a comma (`An attribute requires a subsequent comma`).
- Names (`data/color-names.csv`): the 8 basic names `red green blue yellow cyan magenta white black`, which may be prefixed with `light` (bright variant: +8 when the terminal has more than 8 colors, otherwise bold) or `bright` (deprecated: basic foreground index with bold; backgrounds still use +8); `normal` (the default color, −1); 24 extra names that need ≥ 255 colors (`pink purple mauve lagoon mint lime peach orange latte rosy beet plum sea sky slate teal sage brown ocher sand tawny brick crimson`, mapping to fixed xterm-256 indices; with fewer colors they become the default color); `grey`/`gray` (= black + 8, the bright black); and `#rgb` (three hex digits, mapped to the nearest cell of the 6×6×6 cube, or to a gray level when r=g=b and 0<r<15; requires exactly 256 colors, else the default color).
- Errors: unknown → `Color "<name>" not understood`; a prefix on a non-basic name or on `#rgb` → `Color '<name>' takes no prefix` (TEST-RC-004: `lightpink`, `#12`). A wrong option line keeps the previous color.
- `light` + basic color as a background: +8 when the terminal has more than 8 colors (no bold for backgrounds).
- **Source:** `src/rcfile.c:998-1140`.

### RC-SYNTAX — `syntax` and syntax-only commands (color builds)
- `syntax NAME ["fileregex" ...]` starts a syntax definition. NAME may be quoted (the quotes are removed). A missing or empty name → `Missing syntax name`. A half-quoted name → `Unpaired quote in syntax name`. NAME `none` → `The "none" syntax is reserved`. NAME `default` with regexes → `The "default" syntax does not accept extensions`. Defining a name twice creates two syntaxes; the later one is found first (`11` SYN-SELECT).
- `header`, `magic`, `color`, `icolor`, `comment`, `tabgives`, `linter`, `formatter` apply to the currently open syntax. Without one → `A '<cmd>' command requires a preceding 'syntax' command`. `header`/`magic` for `default` → `The "default" syntax does not accept '<cmd>' regexes`. Missing arguments → `Missing regex string after '<cmd>' command`, `Missing color name`, `Missing argument after '<cmd>'`. A quoted `comment`/`tabgives`/`linter`/`formatter` argument without a closing quote → `Argument of '<cmd>' lacks closing "`. `magic` is accepted but ignored in builds without libmagic.
- A syntax is **closed** by the next `syntax`, `set`, `unset`, `bind`, `unbind`, `include` or `extendsyntax`, and by the end of the file. A closed syntax without any `color`/`icolor` command → `Syntax "<name>" has no color commands` (reported at the syntax's line). After closing, `color` etc. are errors (TEST-RC-005: `color blue` after `set autoindent` → `A 'color' command requires a preceding 'syntax' command`, and blue is not applied).
- **Lazy loading:** during startup only the names, file regexes, headers and magic of syntaxes are taken. The full definition (colors, comment, etc.) is read from the file when a buffer first uses that syntax, from the line after `syntax` up to the next syntax/`set`/`bind`/`include`/`extendsyntax` line. Errors in that part therefore appear only when the syntax is first used.
- Regexes in `syntax`/`header`/`magic` are compiled as ERE with `REG_NOSUB` (case-sensitive). `color` uses ERE; `icolor` uses ERE + `REG_ICASE`. A regex that fails to compile → `Bad regex "<re>": <regerror text>`. A bad file regex is skipped (others on the line stay); a bad color regex drops the rest of that line.
- `color` form: `color SPEC "re" ["re"...]` or `color SPEC start="re" end="re"` (pairs may repeat on one line and mix with single regexes). `start=` without `end=` → `"start=" requires a corresponding "end="`.
- **Source:** `src/rcfile.c:640-724, 1142-1350, 1393-1520`.

### RC-INCLUDE — `include`
`include "PATTERN"` (in the main rcfiles only): closes an open syntax; a pattern
longer than PATH_MAX → `Path is too long`; a leading `~` is expanded; the pattern
is expanded with `glob(GLOB_ERR|GLOB_NOCHECK)`. Each match (in glob's sorted
order) is read as an **included file**. If the pattern matches nothing, it is
used literally (NOCHECK) and reading it fails with `Error reading <path>: <reason>`
(TEST-RC-004 line 33). Other glob errors → `Error expanding <pattern>: <reason>`
(line 32).
- In an included file only `syntax`, `header`, `magic`, `color`, `icolor`, `comment`, `tabgives`, `linter`, `formatter` are allowed. `set`, `unset`, `bind`, `unbind`, `include`, `extendsyntax` → `Command "<cmd>" not allowed in included file` (TEST-RC-006 reported mistakes in the included file). An included file that is a directory or device is reported and skipped.
- **Source:** `src/rcfile.c:899-996, 1484-1493`.

### RC-EXTEND — `extendsyntax NAME COMMAND ARGS`
Only in main rcfiles. NAME must already be defined (`Could not find syntax "<name>" to extend`).
`header` and `magic` are applied immediately to that syntax. Other commands
(`color`, `icolor`, `comment`, `tabgives`, `linter`, `formatter`) are stored and
applied after the syntax's own definition is loaded (lazy loading). A stored
command that is not one of those → `Command "<cmd>" not understood`, reported
with the extendsyntax line's file and line number (TEST-RC-006: a green color and
a header added to an included syntax).
- **Source:** `src/rcfile.c:1418-1467, 938-953`.

### RC-BIND — `bind`/`unbind`
Specified in `02` KEY-030…KEY-035.

### RC-ERR — Error reporting
- Each error is formatted `Error in <rcfile path> on line <N>: <message>` (the prefix appears only when a line number is known). They are collected in order and written to **stderr after nano exits**, one per line, after the terminal is restored (also when nano dies).
- At startup, if any error was recorded: ALERT `Mistakes in '<path>'` naming the first file that had an error (TEST-CLI-037, TEST-RC-004), or `Problems with history file` if the first problem came from the history code.
- Parsing continues after every error; the faulty command has no effect, except as noted (fill/tabsize/guidestripe reset).
- `--listsyntaxes` never prints the errors (`01` CLI-012).
- **Source:** `src/rcfile.c:162-210`.
- **Evidence:** runtime TEST-RC-004 (22 distinct errors reproduced verbatim in its result file).

## Original implementation notes
- `rcopts[]` table; options with flag 0 take arguments and are handled by name in `parse_rcfile`.
- `opensyntax`, `live_syntax`, `seen_color_command`, `lastcolor` track the syntax being parsed; `syntaxes` is a singly linked list with new syntaxes **prepended**.

## Evidence summary
| Requirement | Evidence |
|---|---|
| RC-LOOKUP | runtime TEST-RC-001…003, CLI-P-026 |
| RC-LINE/SET/COLOR | runtime TEST-RC-004, -007…-011 |
| RC-SYNTAX/INCLUDE/EXTEND | runtime TEST-RC-004…006 |
| RC-ERR | runtime TEST-RC-004, TEST-CLI-037 |

## Open questions
- **Q-RC-001:** `set` of a boolean with extra words is silently accepted. Reproduce.
- **Q-RC-002:** Syntax commands in the main rcfile end at the next `set`/`bind`, which differs from what users may expect. Reproduce.
