# 01 — Command line

Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

Scope: invocation name, option parsing, option effects and validation,
positional arguments (`+LINE,COLUMN`, `+/string`, `-`, `FILE:LINE`), startup
ordering relative to nanorc processing, help/version output, diagnostics,
output streams, and exit status.

Inventory: [`data/cli-options.csv`](data/cli-options.csv) (one row per option
character, with long names, argument rules, build conditions, handler source
lines and `--help` text). Evidence: `evidence/cli/cli-probes.json` (non-tty
probes `CLI-P-*`), `evidence/runs/TEST-CLI-*` (terminal probes).

Conventions: "the default build" and "the tiny build" are the two reference
profiles of `00-reference-environment.md`. "Exits with status N" means the
process exit status. "ALERT/AHEM/REMARK/HUSH/INFO/NOTICE/MILD" are status-bar
message importance levels defined in `04-rendering.md` §6. A message shown "at
startup" is drawn on the status bar once the first screen appears.

---

## 1. Normative requirements

### CLI-001 — Restricted mode by invocation name
- **Conditions:** all builds.
- **Trigger:** the basename of `argv[0]` (the text after its last `/`) starts with the character `r`.
- **Result:** restricted mode is on before any option is processed, exactly as if `-R` had been given first. Examples: `rnano` and `rvi`, and `/x/rfoo`, are restricted. `xnano` is not.
- **Note:** the check is on the first byte only and is case-sensitive (`Rnano` is not restricted).
- **Source:** `src/nano.c:1877-1879` (`main`), `src/utils.c:55-63` (`tail`).
- **Evidence:** runtime-observed (`CLI-P-003`: `rnano --help` prints the restricted help; `CLI-P-042`: `xnano --help` prints the full help); key tables `evidence/tables/default-rnano.json` equal `default-restricted.json`.
- **Tests:** TEST-CLI-P003, TEST-CLI-P042, TEST-KEY-RESTR-001.

### CLI-002 — Option syntax and parser
- The parser is GNU `getopt_long` with the short-option string
  `ABC:DEFGHIJ:KLMNOPQ:RST:UVWX:Y:Zabcdef:ghijklmno:pqr:s:tuvwxyz!@%_01/`
  (identical in **every** build) and the long-option table of
  `data/cli-options.csv`. The long-option table **is** build-dependent.
- Short options can be grouped (`-ilc`). A short option that takes an argument consumes the rest of the word (`-T4`) or the next word (`-T 4`).
- Long options take an argument as `--name=value` or `--name value`.
- **Unambiguous prefixes of long options are accepted** (`--solo` = `--solosidescroll`, `--he` = `--help`, `--vers` = `--version`). An ambiguous prefix is an error (CLI-004).
- **Permutation:** options may appear after file names (`nano file -v` enables view mode), unless the environment variable `POSIXLY_CORRECT` is set. Then every word after the first non-option word is a file name (`nano file -v` opens two buffers, the second named `-v`).
- `--` ends option processing. Later words are file names, even if they start with `-` or `+` (`nano -- -v` edits a file named `-v`; with `nano -- +50` the `+50` is still interpreted as a positional `+LINE` argument only when another word follows it, see CLI-030).
- Options are processed left to right; the effects of `-h`, `-V` and `-z` happen at the moment the option is reached (CLI-010 to CLI-012).
- **Source:** `src/nano.c:1744-1841` (long table), `1881-2153` (loop).
- **Evidence:** runtime-observed: `CLI-P-018` (ambiguous), `CLI-P-019`/`CLI-P-038` (prefixes), TEST-CLI-058 (permutation), TEST-CLI-059 (`POSIXLY_CORRECT`), TEST-CLI-017 (`--`).
- **Rust note:** a hand-written parser must reproduce prefix matching, ambiguity detection, permutation and `POSIXLY_CORRECT`, plus the glibc diagnostic texts of CLI-004.

### CLI-003 — Option effects
Each option sets the state named below. Flags are boolean and idempotent. For
string- and number-valued options, the last occurrence wins. Unless stated,
the effect is the same as the nanorc option of the same meaning (`10-nanorc.md`).

| Short | Long (aliases) | Arg | Effect | Build condition (handler) | Restricted-mode note |
|---|---|---|---|---|---|
| `-A` | `--smarthome` | – | smart Home (`05` EDIT-HOME) | not tiny | |
| `-B` | `--backup` | – | make backups on save (`08` FILE-BAK) | not tiny | flag cleared after parsing (CLI-021) |
| `-C` | `--backupdir` | dir | numbered backups in dir | not tiny | dir not validated, backups off |
| `-D` | `--boldtext` | – | interface uses bold instead of reverse (`04` REND-COLOR) | all | |
| `-E` | `--tabstospaces` | – | typed Tab inserts spaces | not tiny | |
| `-F` | `--newbuffer`, `--multibuffer` (deprecated) | – | Read File / Execute go into a new buffer by default | multibuffer | option hidden from `--help` |
| `-G` | `--locking` | – | vim-style lock files (`08` FILE-LOCK) | not tiny | |
| `-H` | `--historylog` | – | persist search/replace/execute history | histories | flag cleared (CLI-021) |
| `-I` | `--ignorercfiles` | – | do not read any nanorc | nanorc | |
| `-J` | `--guidestripe` | number > 0 | guide stripe at that column | not tiny | |
| `-K` | `--rawsequences` | – | nano decodes escape sequences itself (`03` INPUT-RAW); also disables the mouse | all | |
| `-L` | `--nonewlines` | – | no automatic final newline (`08`) | not tiny | |
| `-M` | `--trimblanks` | – | trim trailing blanks when hard-wrapping/justifying | wrapping or justify | |
| `-N` | `--noconvert` | – | no DOS line-ending conversion on read | not tiny | |
| `-O` | `--bookstyle` | – | leading whitespace starts a paragraph | not tiny | |
| `-P` | `--positionlog` | – | persist cursor positions (`12` FEAT-POSLOG) | histories | flag cleared (CLI-021) |
| `-Q` | `--quotestr` | regex | quoting regex for justify | justify | |
| `-R` | `--restricted` | – | restricted mode (`12` FEAT-RESTRICT) | all | |
| `-S` | `--softwrap` | – | soft wrapping (`04`) | not tiny | |
| `-T` | `--tabsize` | number > 0 | tab width | not tiny | |
| `-U` | `--quickblank` | – | status messages vanish after 1 keystroke (0.8 s timed with minibar/zero) | all | |
| `-V` | `--version` | – | print version, exit 0 (CLI-011) | all | |
| `-W` | `--wordbounds` | – | punctuation counts as word characters | not tiny | |
| `-X` | `--wordchars` | string | extra word characters | not tiny | |
| `-Y` | `--syntax` | name | force syntax (`11` SYN-SELECT) | color | |
| `-Z` | `--zap` | – | Backspace/Delete erase a marked region | not tiny | |
| `-a` | `--atblanks` | – | soft-wrap at blanks | not tiny | |
| `-b` | `--breaklonglines` | – | hard-wrap on (overrides earlier `-w`) | wrapping | |
| `-c` | `--constantshow` | – | constant cursor-position display | all | |
| `-d` | `--rebinddelete` | – | swap Backspace/Delete key meanings (`03` INPUT-BSDEL) | all | |
| `-e` | `--emptyline` | – | blank row below title bar | not tiny | |
| `-f` | `--rcfile` | file | read only this rcfile (`10` RC-LOOKUP) | nanorc | |
| `-g` | `--showcursor` | – | show cursor in browser/help | browser or help | |
| `-h` | `--help` | – | print usage, exit 0 (CLI-010) | all | |
| `-i` | `--autoindent` | – | auto-indent | not tiny | |
| `-j` | `--jumpyscrolling` | – | scroll by half screens | not tiny | |
| `-k` | `--cutfromcursor` | – | ^K cuts to end of line | not tiny | |
| `-l` | `--linenumbers` | – | line-number margin | linenumbers | |
| `-m` | `--mouse` | – | mouse support | mouse | |
| `-n` | `--noread` | – | names given on the command line are treated as new files (not read) | not tiny | |
| `-o` | `--operatingdir` | dir | confine file access to dir (CLI-022) | operatingdir | |
| `-p` | `--preserve` | – | keep ^S/^Q as XOFF/XON (CLI-020, `02` KEY-PRESERVE) | all | |
| `-q` | `--indicator` | – | scroll-bar indicator | not tiny | |
| `-r` | `--fill` | integer | wrap/justify width (≤ 0: relative to screen width) | wrapping or justify | |
| `-s` | `--speller` | command | alternative speller | speller | option hidden from `--help` |
| `-t` | `--saveonexit` | – | save without asking on exit | all | |
| `-u` | `--unix` | – | save in Unix format by default | not tiny | |
| `-v` | `--view` | – | view mode (read only) | all | |
| `-w` | `--nowrap` | – | hard-wrap off (overrides earlier `-b`) | wrapping | |
| `-x` | `--nohelp` | – | no help lines | all | |
| `-y` | `--afterends` | – | Ctrl+Right/Ctrl+Delete stop at word ends | not tiny | |
| `-z` | `--listsyntaxes` | – | list syntaxes, exit 0 (CLI-012) | color | |
| `-!` | `--magic` | – | use libmagic for syntax detection | libmagic | |
| `-@` | `--colonparsing` | – | `FILE:LINE[:COL]` notation (CLI-034) | not tiny | |
| `-%` | `--stateflags` | – | state flags in title bar | not tiny | |
| `-_` | `--minibar` | – | mini bar instead of title bar | not tiny | |
| `-0` | `--zero` | – | hide all bars | not tiny | |
| `-1` | `--solosidescroll` | – | old one-line sideways scrolling | **all** for `-1`; long form not tiny | |
| `-/` | `--modernbindings` | – | modern key bindings (`02` KEY-MODERN) | all | |
| – | `--whitespacedisplay` | – | start with whitespace display on | not tiny | no short form |

- **Source:** handlers `src/nano.c:1883-2153`; `data/cli-options.csv` column `handler_source`.
- **Evidence:** source-confirmed for all rows; runtime-observed for `-v -x -c -0 -_ -% -i -e -l -q -J -D -R -Y -@` (TEST-CLI-028..049) and the key-table effects of `-/ -p -R -v -t` (gdb dumps).

### CLI-004 — Unknown options and missing arguments
- **Unknown short option** (a character not in the option string, e.g. `-^`): glibc writes `<argv0>: invalid option -- '<c>'` + newline to **stderr**. nano then writes `Type '<argv0> -h' for a list of available options.` + newline to **stdout** and exits with status 1.
- **Unknown long option** (`--bogus`): stderr `<argv0>: unrecognized option '--bogus'`, then the same stdout line, exit 1.
- **Ambiguous long prefix** (`--s`): stderr `<argv0>: option '--s' is ambiguous; possibilities: '--syntax' '--showcursor' …` (glibc lists the matches in table order), then the stdout line, exit 1.
- **Missing argument:** short: stderr `<argv0>: option requires an argument -- 'T'`; long: stderr `<argv0>: option '--tabsize' requires an argument`; then the stdout line, exit 1.
- **Long option given an argument it does not take** (`--view=x`): glibc reports `option '--view' doesn't allow an argument` (same exit path). *Inferred from glibc behavior; not probed.*
- `<argv0>` is `argv[0]` exactly as invoked (not just its basename).
- The getopt diagnostic texts belong to glibc (domain `libc`) and follow its locale. Only the `Type '%s -h'…` line is nano-owned (`MSG` in `data/messages.csv`).
- Processing stops at the first error. Earlier immediate options have already run (`-V --bogus` prints the version and exits 0 before `--bogus` is reached; `--bogus -V` exits 1).
- **Source:** `src/nano.c:2150-2152`.
- **Evidence:** runtime-observed `CLI-P-009, -010, -016, -017, -018, -020, -021, -035, -039, -040`.
- **Tests:** TEST-CLI-P009…P040.

### CLI-005 — Tiny-build option acceptance
In the tiny build the short-option string is unchanged, but the handlers of
options marked "not tiny" (and of disabled features) are compiled out, and so
are their long names.
- A short option whose handler is absent (e.g. `-A`, `-I`): getopt accepts it silently, so nothing appears on stderr. nano prints `Type 'nano -h' for a list of available options.` on stdout and exits 1.
- The long name of such an option (`--smarthome`): glibc reports `unrecognized option`, then the stdout line, exit 1.
- `-1` stays accepted in tiny (its handler is outside the conditional block) and has no visible effect there.
- The options available in the tiny reference build are exactly those listed by its `--help` (CLI-010) plus `-1`.
- **Source:** `src/nano.c:1881-2153` and `#ifdef` structure; `data/cli-options.csv` columns `build_condition_*`.
- **Evidence:** runtime-observed `CLI-P-029/-030/-031/-032`, `CLI-P-007`.

### CLI-006 — Numeric option values
- `-T/--tabsize`, `-J/--guidestripe` and `-r/--fill` are parsed with `strtol` base 10. The whole text must be consumed, so optional leading whitespace and an optional `+` or `-` sign are allowed: `--tabsize=+3` and `--guidestripe= 7` are accepted (`CLI-P-034`). Trailing characters (`4x`), an empty value, or an out-of-range value (`ERANGE`) are errors.
- Additional constraints: tabsize > 0; guidestripe > 0; fill: any value parsed successfully.
- On error nano writes to **stderr** the translated template followed by a newline, and exits 1:
  - `Requested tab size "%s" is invalid`
  - `Guide column "%s" is invalid`
  - `Requested fill size "%s" is invalid`

  `%s` is the argument exactly as given.
- These checks happen when the option is reached, before the terminal is touched, so they work without a tty.
- **Source:** `src/nano.c:1924-1930, 1970-1976, 2074-2083`; `src/utils.c:109-125` (`parse_num`).
- **Evidence:** runtime-observed `CLI-P-011…015, -034`.

### CLI-007 — String option values
`-C`, `-Q`, `-X`, `-Y`, `-f`, `-o` and `-s` store their argument verbatim (the
last occurrence wins). Nothing is validated at parse time. Later validation:
- `-C`: CLI-021. `-o`: CLI-022. `-Q`: CLI-023.
- `-s`: leading spaces and tabs are stripped after the rcfiles are processed (`src/nano.c:2264`).
- `-Y`: an unknown name gives an ALERT `Unknown syntax name: %s` when a buffer is opened, **but only if at least one syntax was defined in the rcfiles** (with `-I`, or with no syntaxes, nothing is reported: TEST-CLI-047). `-Y none` means no syntax (`11`).
- `-f`: see CLI-012 and `10-nanorc.md` RC-LOOKUP.

### CLI-010 — `--help`
- Writes the usage text to **stdout** and exits 0, at the moment the option is reached. No terminal is needed.
- Default build: the text is exactly the one captured in `CLI-P-001` (see `evidence/cli/cli-probes.json`):
  - line 1: `Usage: nano [OPTIONS] [[+LINE[,COLUMN]] FILE]...` followed by an empty line. The word `nano` is literal; it is never replaced by `argv[0]`.
  - two paragraphs (cursor placement; `-` reads stdin), then an empty line;
  - a header row and one row per option, each produced by: a space, the short form padded with spaces to 14 columns, a space, the long form padded to 24 columns, then the description. Padding is computed from display width (`breadth`), and at least one space follows each column even when the text is longer than its column.
- **Restricted mode active at that moment** (invoked as `r*`, or `-R` earlier on the command line): the rows for `-B`, `-C`, `-F`, `-H`, `-P`, `-R` and `-s` are omitted (`CLI-P-003`, `CLI-P-004`). `-h -R` prints the full text, because `-R` has not been processed yet.
- Tiny build: no intro paragraphs and no header row; only the options compiled into tiny are listed (`CLI-P-007`).
- Option descriptions and the column headers `Option`, `Long option`, `Meaning` are translated (gettext). The argument placeholders such as `-C <dir>` / `--backupdir=<dir>` are translatable strings too.
- **Source:** `src/nano.c:473-648`.
- **Evidence:** runtime-observed.

### CLI-011 — `--version`
- Writes to stdout and exits 0 when reached:
  ```
   GNU nano, version 9.3
   (C) 2026 the Free Software Foundation and various contributors
   Compiled options: --enable-utf8
  ```
  Each line starts with one space. The third line lists `--disable-X` for each optional feature that is off. Tiny builds list `--enable-tiny` followed by `--enable-X` for each feature explicitly enabled. Then `--enable-debug` (debug builds), `--disable-nls` (no NLS), and finally `--enable-utf8` or `--disable-utf8`.
- The copyright line is absent in tiny builds.
- Builds made in a git checkout print ` GNU nano from git, <git describe>` as the first line (`BV-REVISION`, `00-reference-environment.md` §2).
- **Source:** `src/nano.c:652-790`.
- **Evidence:** runtime-observed `CLI-P-005`, `CLI-P-008`.

### CLI-012 — `--listsyntaxes`
- When the option is reached: if `-I` was **not** already seen, the rcfiles are processed now. `-f` is honored only if it appeared **before** `-z`. Then, if any syntax is defined, nano prints `Available syntaxes:` + newline. After that come the syntax names in **reverse order of definition** (most recently defined first), each preceded by one space. A newline is emitted before a name once the accumulated width of previous names exceeds 45, plus a final newline. Exit 0.
- No syntaxes defined: prints nothing at all, exit 0 (`CLI-P-024/-025/-044`).
- Errors in the rcfiles are **not** printed in this path (`CLI-P-028`), and the vital-key check does not run, because the key tables do not exist yet.
- **Source:** `src/nano.c:2114-2121`, `794-811`.
- **Evidence:** runtime-observed `CLI-P-024…028, -043…045`.

### CLI-013 — Startup order
After option parsing, startup proceeds in this order. Each step's observable
effects are specified in the referenced section.

1. The SIGWINCH handler is installed (not tiny).
2. **stdout must be a terminal.** Otherwise: CLI-040.
3. If `TERM` is unset, `TERM=vt220` is put in the environment (CLI-041).
4. Curses starts (`initscr`); failure exits 1 (CLI-041). Colors are started if the terminal has them. `NO_COLOR` is noted (`04` REND-COLOR).
5. Key and function tables are built (`02`), using the flags **as set by the command line at this point** (CLI-020).
6. Unless `-I`: the rcfiles are processed and merged with the command line (CLI-014, `10-nanorc.md`).
7. Hard-wrap override by `-b`/`-w` (CLI-015).
8. Post-processing rules (CLI-021, CLI-020).
9. Histories: directories are created and files loaded (`12` FEAT-HIST).
10. `-C` and `-o` validation (CLI-021, CLI-022), quoting regex compilation (CLI-023), `$SPELL` (CLI-024), defaults for unset string options.
11. Terminal modes, windows, signal handlers, mouse, escape-key timing (`13`, `03`).
12. The files on the command line are opened in order (CLI-030 to CLI-036).
13. **stdin must be a terminal** (CLI-040).
14. If no buffer was opened, an empty one is created and **view mode is turned off** (CLI-037).
15. First screen; startup messages (CLI-038).

- **Source:** `src/nano.c:2156-2683`.

### CLI-014 — Merging command line and nanorc
When rcfiles are read (not `-I`, not tiny):
- **Boolean flags:** the final value of each flag is *(value after the rcfiles ran) OR (value set on the command line)*. The command line can turn a flag **on** in spite of the rcfile, but cannot turn **off** a flag that an rcfile set (an rcfile `unset` of a command-line flag has no effect either).
- **`fill`:** the command-line value wins if `-r` was given; otherwise the rcfile value (default −8).
- **`tabsize`:** the command-line value wins if `-T` was given; otherwise the rcfile value, defaulting to 8.
- **`guidestripe`:** the command-line value wins if `-J` was given (> 0).
- **`backupdir`, `wordchars`, `quotestr`, `speller`:** the command-line value wins if given; otherwise the rcfile value.
- **`operatingdir`:** the command-line value wins if given; **in restricted mode the rcfile value is always discarded** (only `-o` can set it).
- **Hard-wrap:** if an rcfile left `nowrap` *unset* (`unset nowrap`), `breaklonglines` is turned on (backward compatibility). Then CLI-015 applies.
- Options that only exist in nanorc (colors, `punct`, `brackets`, `matchbrackets`, `whitespace`, `allow_insecure_backup`, `casesensitive`, `regexp`) take their rcfile values.
- **Source:** `src/nano.c:2185-2275`.
- **Evidence:** source-confirmed; runtime tests TEST-RC-PREC-001…006 (planned, `16-test-plan.md`).

### CLI-015 — `-b` versus `-w`
The last of `-b`/`--breaklonglines` and `-w`/`--nowrap` on the command line
decides hard-wrapping, overriding any rcfile setting. If neither is given, the
rcfile/default decides (default: off).
- **Source:** `src/nano.c:1736-1738, 2006-2009, 2101-2105, 2277-2282`.

### CLI-020 — Order-sensitive interactions of `-p`, `-/`, `-R`, `-v`
The key tables are built from the command-line flags (step 5 of CLI-013).
Therefore:
- `-p`/`--preserve` on the command line removes the ^S (`savefile`, main), ^Q (`wherewas`, main/browser/help), ^S (`speller`, Execute) and ^Q (`discardbuffer`, Write Out) bindings. `set preserve` in an rcfile does **not** remove them, but it does make the terminal keep XON/XOFF (^S/^Q stop and resume output) — see `02` KEY-PRESERVE and Q-KEY-002.
- `-/` (modern bindings) clears the preserve flag **after** the tables are built. With `-p -/`, the modern ^S/^Q bindings exist, but the Execute-menu ^S (speller) and the Write-Out ^Q (discard buffer) are missing, and flow control is not preserved (TEST-KEY-MODPRES-001).
- `-R` and `-v` given on the command line remove the registrations listed in `02` KEY-RESTR/KEY-VIEW. Neither mode can be set from an rcfile.
- **Source:** `src/nano.c:2183, 2302-2304`; `src/global.c:1259-1298, 1319-1320, 1558-1559, 1564-1584`.
- **Evidence:** runtime-observed via gdb table dumps `default-preserve`, `default-modern`, `default-restricted`, `default-view`.

### CLI-021 — Post-processing rules
After merging:
1. `boldtext` → the highlight attribute is bold instead of reverse.
2. Restricted mode → backups, history logging and position logging are switched off (whatever the source of these flags). The `-C` directory is not validated.
3. `rawsequences` → mouse off.
4. `modernbindings` → `preserve` off.
5. `zero` → `nohelp` on.
6. History/position logging requested but no usable state directory (`12` FEAT-HIST) → both logs off.
7. `-C`/`backupdir` given and not restricted → the path must resolve to an existing directory, otherwise: restore the terminal, print `Invalid backup directory: <dir>` + newline on stderr, exit 1 (TEST-CLI-033). The stored value becomes the canonical absolute path with a trailing `/`.
- **Source:** `src/nano.c:2284-2333`, `src/files.c:1505-1516`.

### CLI-022 — `-o` operating directory
If set (command line, or rcfile when not restricted), nano resolves it to a
canonical absolute path and changes the working directory to it. If it cannot
be resolved, or `chdir` fails: stderr `Invalid operating directory: <dir>` +
newline, exit 1 (TEST-CLI-032). Confinement rules are in `08-files.md` FILE-OPDIR.
- **Source:** `src/nano.c:2334-2339`, `src/files.c:1463-1473`.

### CLI-023 — Quoting regex
The quoting regex (`-Q`, `set quotestr`, default `^([ \t]*([!#%:;>|}]|/{2}))+`)
is compiled as a POSIX ERE at startup in builds with justify. If it is invalid:
stderr `Bad quoting regex "<regex>": <regerror text>` + newline, exit 1
(TEST-CLI-034: `Bad quoting regex "(": Unmatched ( or \(`). The regerror text
comes from the C library.
- **Source:** `src/nano.c:2341-2360`.

### CLI-024 — `$SPELL`
If no speller was set by `-s` or an rcfile, and nano is not restricted, the
value of the environment variable `SPELL` (when set) becomes the alternative
speller command.
- **Source:** `src/nano.c:2362-2374`.

### CLI-030 — Positional arguments: `+` arguments
Positional words are processed left to right. A word starting with `+` is a
**modifier word** only when at least one more word follows it on the command
line. A `+…` word in the last position is a file name (TEST-CLI-016,
TEST-CLI-062). A modifier word applies to the next file word only. Its forms
(default build):

1. `+` followed by zero or more ASCII letters from `c`, `C`, `r`, `R`, then optionally `/STRING` or `?STRING`:
   - `c` turns case-sensitive searching on, `C` off; `r` turns regex searching on, `R` off. **These are global settings that persist for the rest of the session** (later files, later interactive searches) (TEST-CLI-063).
   - Any other letter (`[A-Za-z]`) produces an ALERT `Invalid search modifier '<letter>'`, and scanning continues with the next character.
   - `/STRING`: search forward for STRING from the start of the file. `?STRING`: search backward from the start (which wraps around, so it finds the last occurrence in the file).
   - `/` or `?` with nothing after it: ALERT `Empty search string`. No search; the cursor stays at line 1.
   - When no `/` or `?` follows the letters, the **entire text after `+`** (letters included) is parsed as a position (form 2). `+c5`, for example, fails with `Invalid line or column number` (TEST-CLI-008 shows both ALERTs: the second one turns the first into `[ Invalid search modifier 'x' ] ...`).
2. Position: `+` alone means the last line of the file. Otherwise the text after `+` is parsed as `LINE`, `LINE<sep>COLUMN` or `<sep>COLUMN`, where `<sep>` is the first occurrence of `,` `.` or `:`. Leading spaces are skipped. Each number follows CLI-006 rules. A part that fails to parse gives ALERT `Invalid line or column number`. A part that parsed **is still used** (`+3,` goes to line 3 and reports the error, TEST-CLI-056).
3. In the tiny build only form 2 exists, and `+/…` is a parse error.

- **Source:** `src/nano.c:2517-2555`, `src/utils.c:130-157`.
- **Evidence:** runtime-observed TEST-CLI-001…015, -052…056, -063.

### CLI-031 — Applying a position
After the file has been opened (if opening it succeeded), a given position is
applied as follows (line and column are 1-based):
- line < 0 → `last_line + line + 1` (so `-1` is the last line); line 0 → the current line (line 1 for a fresh buffer); then clamp to `[1, last line]`. The "last line" is the last line of the buffer, which is the empty line after a final newline (TEST-CLI-003/-006 land on the empty line 101 of a 100-line file).
- column < 0 → `display_width(line) + column + 2` (`-1` is just past the last character); column 0 → the preferred column + 1 (that is, column 1 for a fresh buffer); clamp ≥ 1. The cursor goes to the first character whose display position does not exceed column − 1. A column beyond the end of the line puts the cursor at the end of the line, while the *preferred column* stays column − 1, so the next Up/Down movement aims for it (TEST-CLI-065).
- With soft wrapping on, a preferred column more than one screen-width past the line is reduced to the line's width.
- Viewport: if the target line is within half a screen of the end of the buffer (and jumpy scrolling is off), the viewport is placed so that the last line is on the bottom row. Otherwise the target line is centered (`editwinrows / 2` rows from the top) (TEST-CLI-001/-003).
- A position given together with a recorded position-log entry: the log is applied first and the explicit position overrides it.
- **Source:** `src/nano.c:2598-2608`; `src/search.c:820-883` (`goto_line_and_column`, `hugfloor = TRUE`).

### CLI-032 — Applying a search string
For `+/STRING` / `+?STRING` (not tiny): the cursor is put at line 1, column 0.
If regex mode is on, STRING is compiled (see CLI-033). The search runs from
the top in the chosen direction without skipping the first character, so a
match at line 1 column 0 is found. Found: the cursor goes to the match start,
the match is **spotlighted** (`04` REND-SPOT, the cursor is hidden while
spotlighted), and the viewport is centered on it. A REMARK such as
`Search Wrapped` is wiped. Not found: AHEM `"<STRING>" not found` (truncated
per `07` SRCH-NOTFOUND); the cursor stays at line 1. In both cases STRING
becomes the remembered search string (the default of the next ^W). The
direction flag remains "backward" after `+?`.
- **Source:** `src/nano.c:2609-2627`.
- **Evidence:** runtime-observed TEST-CLI-009/-010/-011/-012/-015.

### CLI-033 — Invalid regex in `+r/…` (suspected defect)
**Observed reference behavior:** `nano +r/( file` shows nothing usable. The
failed compilation is ignored, the search runs with an uncompiled regex, and
the process gets SIGSEGV. The crash handler restores the terminal, prints
`Sorry! Nano crashed!  Code: 11.  Please report a bug.` on stderr, saves
modified buffers (none here) and exits with status 1 (TEST-CLI-057).
**Requirement for the reimplementation:** this is not to be reproduced. See
Q-DEF-001: the proposed behavior is to show AHEM `Bad regex "<STRING>": <error>`
(the message `regexp_init` already produces) and skip the search.
- **Source:** `src/nano.c:2613-2616` (return value of `regexp_init` ignored).

### CLI-034 — `-@` colon parsing
Applies only in non-tiny builds, when `-@` (or `set colonparsing`) is on, the
word is not `-`, no `+` position was given for it, the name contains a `:`,
and **the name as given does not exist** (`stat` fails):
1. Scan back from the end over trailing digits. If the character before them is `:` **and** at least one digit follows that colon, cut the name at that colon.
2. If the cut name exists, parse the digits after the colon as `LINE` (or `LINE:COL` when the name was cut twice) and open the cut name. A failed parse here kills nano: `Invalid number` + newline on stderr, exit 1.
3. If the cut name does not exist: restore the colon. If no further colon follows it, try once more from the new end (the second colon from the right), treating `NAME:LINE:COL`.
4. If no cut name exists, the original word is the file name.

The scan never looks at the first character of the name, so `:5` is not split.
Examples: `f.txt:7` → line 7 (TEST-CLI-018); `f.txt:7:3` → line 7 column 3
(TEST-CLI-019); `nofile:7` → the new file `nofile:7` (TEST-CLI-020); without
`-@` → the new file `f.txt:7` (TEST-CLI-021); `-@ +2 f.txt:7` → no colon
parsing, new file `f.txt:7` (TEST-CLI-022).
- **Source:** `src/nano.c:2570-2593`.

### CLI-035 — `-` reads standard input
Default build: the word `-` (exactly) reads stdin into a new, unnamed buffer:
- The terminal is restored to its original state first. If stdin is a terminal, the line `Reading data from keyboard; type ^D or ^D^D to finish.` is written to stderr.
- `/dev/stdin` is opened. Failure → curses resumes, ALERT `Failed to open stdin: <strerror>`, and the word is skipped.
- While reading, ^C (SIGINT) stops the reading, giving ALERT `Interrupted`.
- The data is read with the same rules as a file (`08` FILE-READ: line splitting, CR LF conversion, NUL encoding). Then **stdin is reconnected to `/dev/tty`** (failure: die `Could not reconnect stdin to keyboard`), the terminal state is re-saved, and curses resumes.
- Messages: REMARK `Read N lines` (or `… (converted from DOS format)`).
- The buffer has no name, and is marked **modified** unless view mode is on or nothing was read. The cursor is left **at the end of the inserted data**, that is, at the start of the empty last line after a final newline (TEST-CLI-030).
- A syntax is chosen for it (by header line or default syntax; it has no file name).
- In the tiny build `-` is an ordinary file name.
- **Source:** `src/nano.c:840-893, 2557-2564`; `src/files.c:756-762`.
- **Evidence:** runtime-observed TEST-CLI-030/-031.

### CLI-036 — Opening named files
Each remaining word is opened into a new buffer (`08-files.md` FILE-OPEN), with
its failure modes. A word that cannot be opened (directory, device file,
invalid name ending in `/`, outside the operating directory, lock declined)
yields an ALERT and no buffer; its position modifier is ignored. A missing file
gives an empty buffer with that name and REMARK `New File`. With `-n`
(`noread`) the file is not read even if it exists. After the loop, `noread` is
turned off, so later insertions read normally.
- Messages: `'<name>' is a directory`, `'<name>' is a device file`, `'<name>' is an invalid filename` (TEST-CLI-024/-025/-026); in tiny also `'<name>' is a FIFO`.
- Only the **first ALERT** produced while opening the second and later files is stored with the buffer that is current at that moment, and shown when that buffer is switched to (`08` FILE-MULTI-ERR). Because a failing word creates no buffer, its message is stored with the previously opened buffer (TEST-CLI-050: the message about `.` appears again when switching to `nonexist.txt`).
- Single-buffer builds (multibuffer disabled): after the first successfully opened file, if more words remain, nano dies with `Can open just one file`.
- **Source:** `src/nano.c:2594-2596, 2641-2656`; `src/files.c:385-492`; `src/winio.c:2329-2335`.

### CLI-037 — No file opened
If no buffer exists after processing the words (no words, or all failed), an
empty unnamed buffer is created and **view mode is turned off**, even with `-v`
(TEST-CLI-029). Otherwise the first opened buffer becomes current. If more than
one buffer was opened, the status bar shows `<name> -- N lines` for it
(`08` FILE-MULTI). If view mode is on, `newbuffer` is turned on, so files
inserted later open in new buffers.
- **Source:** `src/nano.c:2638-2656`.

### CLI-038 — Startup messages
After the first screen is drawn:
1. If an rcfile or history file had problems: ALERT `Mistakes in '<path of first rcfile with a problem>'` or `Problems with history file` (TEST-CLI-037). The individual error lines are written to stderr **after nano exits** (`10-nanorc.md` RC-ERR).
2. Default build: if the current buffer is unnamed and empty, it is the only buffer, help lines are shown, and the first key bound to *help* in the main menu is ^G (keycode 7), then HUSH `Welcome to nano.  For basic help, type Ctrl+G.` (two spaces after the period).
- Messages from opening files (Read N lines, New File, errors) were produced earlier and are visible according to message priority (`04` REND-MSG).
- **Source:** `src/nano.c:2658-2674`.

### CLI-040 — Not a terminal
- stdout is not a terminal (checked after option parsing, so `-h`, `-V`, `-z` and option errors still work): `die("Standard output is not a terminal\n")`. Before printing, die writes the disable-bracketed-paste sequence `ESC [ ? 2 0 0 4 l` (8 bytes) to **stdout** (default build; nothing in tiny). Then stderr `Standard output is not a terminal`, exit 1 (`CLI-P-023`).
- stdin is not a terminal (checked after all files were opened): `die("Standard input is not a terminal\n")` — terminal restored, message on stderr, modified buffers emergency-saved (`13` SIG-EMERG), exit 1 (TEST-CLI-036).
- **Source:** `src/nano.c:2160-2162, 2634-2636, 349-390, 229-238`.

### CLI-041 — TERM handling
- `TERM` unset → nano sets `TERM=vt220` before starting curses (TEST-CLI-060 works).
- `TERM` names an unknown terminal → ncurses prints `ncurses: cannot initialize terminal type ($TERM="<value>"); exiting` on stderr and the process exits 1 (TEST-CLI-061). This message is ncurses-owned.
- ncurses honors `LINES` and `COLUMNS` from the environment, overriding the real size (TEST-CLI-064). nano does not reset them.

### CLI-050 — Exit status
| Status | When |
|---|---|
| 0 | normal exit (last buffer closed) and `-h`, `-V`, `-z` |
| 1 | invalid option or option value (CLI-004/005/006), any `die()` (not a tty, invalid directories, bad quoting regex, `Invalid number`, out of memory, SIGHUP/SIGTERM, crash handler) |
| 2 | the last buffer was closed by *discard* — ^X then ^Q at "Save modified buffer?" (not with modern bindings; with them ^X), or ^O then ^Q (Discard buffer) in the Write-Out prompt — see `08` FILE-EXIT |
| 11 | `die()` reentered (a second fatal error while dying) |
| other | curses library termination (e.g. initscr failure: 1) or death by an uncaught signal (SIGKILL, SIGQUIT is ignored, SIGINT is ignored) |

The status-2 marker is cleared at every pass of the main loop, so it only
affects an exit performed during the same keystroke (`src/nano.c:2745`).
- **Evidence:** 0 and 1 runtime-observed. 2 is source-confirmed and documented (`nano.1` EXIT STATUS); runtime test TEST-FILE-EXIT-002.

### CLI-060 — Environment variables read by nano
| Variable | Effect | Section |
|---|---|---|
| `TERM` | terminal type; vt220 if unset | CLI-041 |
| `LINES`, `COLUMNS` | (ncurses) override window size | CLI-041 |
| `ESCDELAY` | (ncurses) ignored in effect: nano sets 50 ms explicitly | `03` INPUT-ESC |
| `LANG`, `LC_ALL`, `LC_CTYPE`, `LC_MESSAGES` | locale, UTF-8 mode, translations | `14`, `18` |
| `HOME` | home directory (when root, or HOME unset: passwd entry) | `10`, `12` |
| `XDG_CONFIG_HOME` | rcfile lookup | `10` RC-LOOKUP |
| `XDG_DATA_HOME` | history/position directory | `12` FEAT-HIST |
| `SPELL` | alternative speller | CLI-024 |
| `SHELL` | shell for Execute (default `/bin/sh`) | `12` FEAT-EXEC |
| `TMPDIR` | directory for temporary files | `08` FILE-TEMP |
| `NO_COLOR` | default spotlight/error colors replaced by reverse video | `04` REND-COLOR |
| `NANO_NOCATCH` | do not install the SIGSEGV/SIGABRT handler | `13` SIG-CRASH |
| `POSIXLY_CORRECT` | (glibc getopt) no option permutation | CLI-002 |

---

## 2. Original implementation notes

- Flags live in `unsigned flags[4]` indexed by the enum in `src/definitions.h:328-381`; `SET/UNSET/ISSET/TOGGLE` macros. The command-line/rc merge saves a copy (`flags_cmdline`) and ORs it back.
- `hardwrap` is a local tri-state (−2 unset, 0 nowrap, 1 breaklonglines).
- `optind` is advanced manually through the positional words; `+` words consume one extra slot.
- `parse_line_column` splits at `strpbrk(",.:")`.

## 3. Evidence summary

| Requirement | Evidence |
|---|---|
| CLI-001 | runtime (CLI-P-003, -042), source |
| CLI-002 | runtime (CLI-P-018, -019, -038; TEST-CLI-017, -058, -059), source |
| CLI-003 | source (all); runtime for the options listed in CLI-003 |
| CLI-004…006 | runtime (CLI-P probes), source |
| CLI-010…012 | runtime, source |
| CLI-014 | source; runtime tests planned (TEST-RC-PREC-*) |
| CLI-020 | runtime (gdb tables), source |
| CLI-021…024 | runtime (TEST-CLI-032…035), source |
| CLI-030…038 | runtime (TEST-CLI-001…065), source |
| CLI-033 | runtime (crash observed) |
| CLI-040/041 | runtime |
| CLI-050 | runtime (0/1), source + documentation (2, 11) |

## 4. Open questions and decisions

- **Q-DEF-001** (CLI-033): crash on an invalid `+r/` regex. Decision needed. Proposal: report `Bad regex` and skip the search.
- **Q-CLI-001:** glibc getopt message texts and their translation are part of the observable output. Option: replicate the glibc English texts and use the libc gettext domain for translations, or accept differences. Proposed: replicate the English texts exactly; translations through the `libc` domain where available.
- **Q-CLI-002:** `--listsyntaxes` silently drops rcfile errors (CLI-012). This is reproduced as specified.
- **Q-DOC-001:** `nano.1` says the nameless emergency file is `nano.save`; the code writes `nano.<pid>.save` (`13` SIG-EMERG).
