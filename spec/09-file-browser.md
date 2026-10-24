# 09 — File browser

Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

Scope: the file browser opened with `^T` at the Read File and Write Out prompts
(browser builds, not restricted mode): layout, sorting, navigation, search,
go-to-directory, selection, cancellation, and failure messages.

Evidence: `evidence/runs/TEST-BROWSE-*`. Keys: `02-keybindings-tables.md`
sections MBROWSER, MWHEREISFILE, MGOTODIR, and the letter keys of `02` KEY-024.

---

### BROWSE-001 — Entering the browser
`^T` at the Insert or Write prompt calls the browser with the current answer:
- If the answer (after `~` expansion) names a directory, browsing starts there. Otherwise its last `/` component is stripped and that directory is used. Otherwise the current working directory (if it has disappeared: ALERT `The working directory has disappeared`, 1.2 s pause, back to the prompt).
- With an operating directory, a start outside it is replaced by the operating directory.
- The directory is canonicalized. If it cannot be opened: ALERT `Cannot open directory: <reason>`, 1.2 s pause, back to the prompt. An empty directory listing (impossible in practice, `..` always exists): ALERT `No entries`, 1.2 s pause.
- The browser returns either a chosen file path, which the prompt then uses as its answer and proceeds with as if Enter was pressed, or nothing (exit/cancel), in which case the prompt is shown again with the previous answer.
- **Source:** `src/browser.c:675-706, 381-446`; `src/files.c:1251-1262, 2117-2126`.

### BROWSE-002 — Listing and sorting
- All entries of the directory except `.` are listed, **including hidden files**, each with its full path. Entries are sorted with directories first, where "directory" means `stat` (following symlinks) says directory. Within each group the order is a case-insensitive comparison (`18` multibyte-aware), with byte comparison as tie-breaker (TEST-BROWSE-001 order: `..`, `lnk`→dir, `sub`, `.hidden`, `alpha.txt`, `Beta.txt`, `dangling`, `long…name.txt`, `zed`).
- **Width:** `gauge` = (widest name in columns) + 10, at least 15, at most COLS. Entries per row: `piles = (COLS + 2) / (gauge + 2)`. Rows: the edit rows (minus 1 in zero mode).
- **Cell format:** the name (`display_string`); if the name is at least `gauge − 7` columns wide (and COLS ≥ 15), `...` followed by the tail of the name. Right-aligned in the cell is an info field of at most 7 columns (12 for `(parent dir)`):
  - `..` → `(parent dir)`;
  - a directory (including a symlink to one) → `(dir)`;
  - a symlink to a non-directory, or a name that cannot be stat-ed (e.g. a dangling link) → `--`;
  - a regular or other file → its size: below 1 KiB `%4d  B`, then `%4d KB`, `%4d MB`, `%4d GB` (integer division by 1024ⁿ), or `(huge)` when that number reaches 1024. Example: 10 bytes → `  10  B`, 2048 → `   2 KB`, 3 MiB → `   3 MB`.
  - Info longer than its maximum is truncated.
- Cells are separated by 2 columns. The **selected** entry's whole cell is painted in the SELECTED_TEXT attribute. The title bar shows `DIR:` and the directory path (`04` REND-002).
- The view shows the "page" of `rows × piles` entries containing the selection.
- **Source:** `src/browser.c:44-256`; `src/files.c:2331-2355`.
- **Evidence:** runtime TEST-BROWSE-001.

### BROWSE-003 — Navigation
With `n` entries, selection index `s` (0-based), `p = piles`, `R = rows`:

| Function (keys) | Effect |
|---|---|
| left (◂) | `s−1` if `s > 0` |
| right (▸) | `s+1` if not last |
| prevword (`^◂`, Left Column) | start of the current row: `s − s mod p` |
| nextword (`^▸`, Right Column) | end of the current row: `s + p − 1 − s mod p`, clamped to the last entry |
| up (▴, `^P`) | `s − p` if `s ≥ p` |
| down (▾, `^N`) | `s + p` if `s + p ≤ n − 1` |
| prevblock (`^▴`, Top Row) | first row of the page, same column |
| nextblock (`^▾`, Bottom Row) | last row of the page, same column; if beyond the list, the last full row in that column (or the row before) |
| pageup (PgUp, `^Y`, `-`, `b`) | `s < p` → 0; `s < R·p` → `s mod p`; else `s − R·p` |
| pagedown (PgDn, `^V`, space) | `s + p ≥ n − 1` → last; `s + R·p ≥ n` → `(s + R·p − n) mod p + n − p`; else `s + R·p` |
| firstfile (Home, `^Home`, `M-\`) / lastfile (End, `^End`, `M-/`) | first / last |
| enter (Enter, `s`) | BROWSE-005 |
| gotodir (`^/`, `^_`, `M-G`, `g`) | BROWSE-006 |
| whereis/wherewas (`^F`/`^W`, `^B`, `w`, `/`) | BROWSE-004 |
| findnext/findprevious (`M-F`/`M-W`/`n`, `M-B`/`M-Q`/`N`) | repeat search |
| refresh (`^L`) | reread and redraw the directory, keeping the selection by name |
| nohelp toggle (`M-X`) | toggle help lines and reread |
| help (`^G`, `?`) | browser help text |
| exit (`^X`, `^T`, `^C`, `e`/`q`/`x`) | leave without choosing |

- A bracketed paste is discarded with AHEM `Paste is ignored`. Other unbound keys → `02` KEY-025 messages.
- After a terminal resize, the list is reread and the selection kept by name.
- **Source:** `src/browser.c:446-661`.
- **Evidence:** runtime TEST-BROWSE-001 (Right, Down, End, Home), -004 (`?`, `q`, `w`).

### BROWSE-004 — Searching names
Prompt `Search` + ` [Backwards]` + ` [<last>]` (shared search string and search
history with the editor; `17`). An empty answer uses the last string; with
none: HUSH `Cancelled`. Matching: case-insensitive substring of the entry's
**basename**, starting with the entry after the selection (forward) or before
it (backward), wrapping with HUSH `Search Wrapped`. Found at the start entry
again: HUSH `This is the only occurrence`. Not found: AHEM `"<s>" not found`.
Repeat search without a string: HUSH `No current search pattern`. In the search
prompt, `^Y`/`^V` and `M-\`/`M-/` jump to the first/last file.
- **Source:** `src/browser.c:258-366`.
- **Evidence:** runtime TEST-BROWSE-001 (`inner` not found in this directory; `BETA` finds `Beta.txt`; repeat → only occurrence).

### BROWSE-005 — Choosing (Enter)
- On `/..` (the parent of the root): ALERT `Can't move up a directory` (TEST-BROWSE-003).
- Outside the operating directory: ALERT `Can't go outside of <dir>`.
- A name that cannot be stat-ed: ALERT `Error reading <path>: <reason>`.
- A non-directory: it is chosen; the browser returns its full path (TEST-BROWSE-001: `Beta.txt` was inserted).
- A directory: it is entered. When entering `..`, the directory just left becomes the selection in the parent (TEST-BROWSE-002). Otherwise the first entry (`..`) is selected.
- A directory that cannot be opened: ALERT `Cannot open directory: <reason>`, and the current list stays (its path and selection are kept).

### BROWSE-006 — Go to directory
Prompt `Go To Directory` (no history; Tab completes directory names only). Cancel
or an empty answer: HUSH `Cancelled`. The answer is `~`-expanded; a relative path
is taken relative to the current browser directory. Outside the operating
directory: ALERT `Can't go outside of <dir>`. Trailing slashes are removed. If the
target is an entry of the current list, it becomes selected (so it is highlighted
if it cannot be opened). Then the directory is read (BROWSE-005 failure rule).
- **Evidence:** runtime TEST-BROWSE-002 (`g d`), -003 (`/`).

### BROWSE-007 — Mouse
A click in the list selects the entry at that cell
(`page start + row·p + column/(gauge+2)`). A click beyond the last column of a
row selects the previous one, and a click beyond the end of the list selects the
last entry. A second click on the already-selected entry chooses it (Enter).
- **Source:** `src/browser.c:463-489`.

## Original implementation notes
- `filelist` holds full paths. `read_the_list` scans the directory twice (first for widths). `selected`, `piles`, `gauge` and `usable_rows` are file-static.

## Evidence summary
| Requirement | Evidence |
|---|---|
| BROWSE-001…006 | runtime TEST-BROWSE-001…004, source |
| BROWSE-007 | source |

## Open questions
- **Q-BROWSE-001:** sorting relies on `towlower` and the C library's locale for non-ASCII names. Must match glibc behavior in the reference envelope.
