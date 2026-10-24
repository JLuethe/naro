# 14 — Messages and internationalization

Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

Scope: the message catalog (every user-visible string), how messages are
formatted and where they appear, plural forms, locale detection, translations,
translated Yes/No/All letters, and charset handling of translated text.

Inventories: [`data/messages.csv`](data/messages.csv) — all 682 msgids of the
`nano.pot` template generated from the pinned tree
(`evidence/messages/nano-6ed285c.pot`), with plural forms, format flags,
substitutions, source lines, display channel and translator comment;
[`data/translation-catalogs.csv`](data/translation-catalogs.csv) — the 41
`po/*.po` catalogs with counts and `Plural-Forms`.
Evidence: `evidence/runs/TEST-I18N-001…008`, TEST-PROMPT-NUL-001, and every
English message observed in other runs.

---

### MSG-CATALOG — Message texts are part of the interface
1. Every string in `data/messages.csv` that the program can show must be reproduced **byte for byte** in English (the C/untranslated case), including punctuation, double spaces (`Welcome to nano.  For basic help, type Ctrl+G.`), trailing spaces in prompts (`Save modified buffer? `), and typographic characters used by the English source.
2. Format strings use C `printf` semantics: `%s`, `%d`, `%zu`, `%zd`, `%*zd` (padded to a computed width), `%lu`, `%2d%%`. `substitutions` in the CSV names what each conversion receives. The Rust implementation must produce identical text for identical values (`16` normalizes only pids, temp names and times).
3. The display channel column tells where each message goes: status line with an importance (HUSH/REMARK/INFO/NOTICE/AHEM/ALERT, `04` REND-060), prompt text, help-line tag, help-viewer text, title bar, stdout (`--help`, `--version`, suspend), stderr during or after exit (rcfile errors, die messages, emergency save).
4. Status-line messages are centered and bracketed `[ … ]` when there is room (`04` REND-060); they are converted with `display_string` (control characters shown as `^X`), whitespace display is suppressed for them. While curses is not active, `statusline` writes `\n<message>\n` to stderr instead (e.g. `Buffer written to …`, `13` SIG-EMERG).
5. Repeated ALERTs: when an ALERT is already showing, a new message of any importance is not shown; instead `...` is appended to the first one (if it started beyond column 4), after 0.1 s and with a beep (`04`).
- **Source:** `src/winio.c` (statusline, statusbar, warn_and_briefly_pause); `po/nano.pot` regenerated in the envelope.

### MSG-PLURAL — Plural forms
Eleven messages have plural forms (`ngettext`): `%s -- %zu line (%s)`,
`%s -- %zu line`, `Read %zu line (converted from DOS format)`, `Read %zu line`,
`Wrote %zu line`, `Replaced %zd occurrence`, the word-count nouns `line`,
`word`, `character`, and the Write-prompt suffixes ` (%zu line)` and
` (%zu line, %s)` (plurals `… lines`, `occurrences`, `words`, `characters`).
English uses the singular only for n == 1 (0 → plural: `Replaced 0
occurrences`). Translations use their catalog's `Plural-Forms` expression
(TEST-I18N-001: `2 Zeilen gelesen`, `2 Zeilen,  2 Wörter,  11 Zeichen`).

### I18N-LOCALE — Locale detection
1. At startup, `setlocale(LC_ALL, "")`. **UTF-8 mode** is on when that call succeeds **and** `nl_langinfo(CODESET)` is exactly `UTF-8`. Otherwise the text is handled as single bytes (`18` BYTE-*). In the envelope, `LANG=en_US.UTF-8` → UTF-8 mode; `LC_ALL=C` → byte mode; a locale that does not exist (setlocale fails) → byte mode and English.
2. The message domain `nano` is bound to `LOCALEDIR` (`<prefix>/share/locale`). Catalog lookup follows GNU gettext: `LANGUAGE` (a colon-separated priority list) is used **only when the locale is not C/POSIX** (TEST-I18N-005: `LANG=en_US.UTF-8 LANGUAGE=fr:de` → French; TEST-I18N-006: `LANG=C LANGUAGE=de` → English), then `LC_ALL`, `LC_MESSAGES`, `LANG`.
3. Translated messages are converted by gettext to the locale's charset. In `de_DE.ISO-8859-1` the help line shows `Ausf\xFChren` as a single Latin-1 byte (TEST-I18N-003; the tmux UTF-8 terminal rendered it as `�`). A Rust implementation must output catalog text in the locale's charset (`iconv`-equivalent), or stay within UTF-8 locales and document the deviation (99 Q-I18N-001).
4. Character classification, case mapping, widths and collation for text come from the C library's locale (`18`).
- **Source:** `src/nano.c:1860-1872`.
- **Evidence:** runtime TEST-I18N-001…006.

### I18N-CATALOGS — Translations shipped
41 catalogs; the most complete have 648 of 650 translatable strings, the
least complete 179 (`eu`). Untranslated or fuzzy entries fall back to English.
The Rust version should read the **same `.po`/`.mo` files** (compiled from
`po/*.po` of the pinned tree, GPL-3.0-or-later like nano) so translations match
exactly. Message identity is the English msgid; a Rust string table keyed by
the msgid keeps catalogs usable unchanged.

### I18N-YESNO — Translated answer letters
1. The Yes/No/All letters come from the translations of `Yy`, `Nn`, `Aa` (German: `JjYy`, `Nn`, `Aa`; French: `Oo`, `Nn`, `Tt`). The first character of each is shown in the help lines (` J Ja`, TEST-I18N-001) and must be a single byte.
2. A typed key (with its UTF-8 continuation bytes, if any) answers when it occurs as a substring of the translated string (TEST-I18N-002: `j` → Yes). Then the English letters `Yy`/`Nn`/`Aa` always also work. Other letters do nothing (TEST-I18N-001: `q` ignored).
3. **Quirk:** a NUL key code (`^@`, Ctrl+Space) answers **Yes**, because the empty string matches every translated string (TEST-PROMPT-NUL-001: `^X`, `^@` → `Write to File: f.txt`). See 99 Q-PROMPT-001.
4. Control keys: `^Y` Yes, `^N` No, `^A` All (when offered), `^Q` (or `^X` with modern bindings) No with exit status 2 (`13` SIG-STATUS), Cancel (`^C`) cancels. Mouse clicks on the shown answers work (`17`).
- **Source:** `src/prompt.c` (ask_user).
- **Evidence:** runtime TEST-I18N-001/-002, TEST-PROMPT-NUL-001, TEST-SIG-011…014.

### I18N-WIDTH — Translated texts in the layout
Translated strings are measured in display columns (`18` BYTE-WIDTH), not bytes:
help-line labels are cut to their cell width (TEST-I18N-001 `Ausschneid`,
TEST-I18N-004 `コマンドを` — a double-width character that would cross the cell
edge is left out), the title bar, prompts and status messages are positioned by
columns (TEST-I18N-004 Japanese messages centered correctly). The position
report keeps its numeric layout (TEST-I18N-001 `Zeile  1/3 (33%), Spalte  2/ 6 ( 33%), Zeichen  1/11 ( 9%)`).

### I18N-HELP — Translated help text
The help viewer's texts (`htx` introductions, function descriptions) are
translated (TEST-I18N-007: title `Haupt-Hilfe für Nano`) and rewrapped by
columns (`12` FEAT-HELP).

## Original implementation notes
- `_()` = `gettext`, `P_()` = `ngettext`, `N_()` marks for extraction only. Help-line tags use `_()` on the tag at display time.
- The gnulib `localcharset` is not involved in nano itself; gettext handles conversion.

## Evidence summary
| Requirement | Evidence |
|---|---|
| MSG-CATALOG | pot extraction (static), every run's status lines |
| MSG-PLURAL | runtime TEST-SRCH-013, TEST-I18N-001 |
| I18N-LOCALE | runtime TEST-I18N-001…006 |
| I18N-YESNO | runtime TEST-I18N-001/-002, TEST-PROMPT-NUL-001 |
| I18N-WIDTH/HELP | runtime TEST-I18N-001/-004/-007 |

## Open questions
- **Q-I18N-001:** Non-UTF-8 locales need catalog charset conversion. Decide whether the Rust version supports them fully (recommended: yes, through iconv-equivalent conversion of catalog strings, since byte mode is otherwise specified).
- **Q-PROMPT-001:** NUL answering Yes is a quirk. Proposal: do not reproduce (treat NUL as an unrecognized key); record as a known deviation.
