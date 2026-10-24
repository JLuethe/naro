# 08 — Files

Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

Scope: opening and reading files, inserting files, multiple buffers, line-ending
formats, final newline handling, writing (overwrite, append, prepend, selection),
backups, lock files, metadata, symbolic and hard links, files changed on disk,
read-only files, failures, exit flows, temporary files and the operating
directory. Emergency saves are in `13`. Execute/pipe is in `12` FEAT-EXEC.

Evidence: `evidence/runs/TEST-FILE-*` (34 scenarios with before/after fixture
manifests: bytes, mode, inode, link count, mtime) and TEST-CLI-023…026, -030,
-050.

Message ownership: templates in this section are nano's (`data/messages.csv`).
`%s` reasons such as `Permission denied` and `No such file or directory` come
from `strerror(errno)` (C library, locale-dependent).

---

## 1. Opening

### FILE-OPEN — Opening a file into a buffer
Given a name (command line, Read File prompt in new-buffer mode, browser,
linter):
1. With an operating directory set: a name outside it → ALERT `Can't read file from outside of <dir>`; no buffer.
2. A leading `~` or `~user` is expanded (FILE-TILDE).
3. If the name is non-empty and exists: a directory → ALERT `'<name>' is a directory`; a character or block device → ALERT `'<name>' is a device file`; (tiny only) a FIFO → ALERT `'<name>' is a FIFO`. No buffer is created in these cases. When running as root and the file has no write bit for anyone, ALERT `'<name>' is meant to be read-only` (the file is still opened).
4. A non-existent name ending in `/` → ALERT `'<name>' is an invalid filename`; no buffer.
5. A new buffer is created. The containing directory is checked (FILE-PATH). With *locking*, not view mode, and a non-empty name: lock handling (FILE-LOCK). Declining the lock question removes the buffer again.
6. Unless *noread* applies (command-line names with `-n`): the file is opened (FILE-READ). A missing file gives REMARK `New File` and an empty buffer with that name. An open error gives ALERT `Error reading <name>: <reason>` (or `Interrupted` when ^C hit during `open`), and the buffer stays, empty but named.
7. Name, cursor (line 1, x=0), stat information and syntax are set (`11` SYN-SELECT).
- **Source:** `src/files.c:385-492, 830-893`.
- **Evidence:** runtime TEST-CLI-023…026, -050; TEST-FILE-015/-019.

### FILE-PATH — Containing directory check
For the name's directory part (`.` if none): if the working directory itself
has vanished → ALERT `The working directory has disappeared`; if the directory
does not exist → ALERT `Directory '<dir>' does not exist`; any other stat
failure → ALERT `Path '<dir>': <reason>`; not a directory → ALERT
`Path '<dir>' is not a directory`; not searchable → ALERT
`Path '<dir>' is not accessible`; with locking (not view mode), not writable →
MILD `Directory '<dir>' is not writable`. The buffer is still created; only the
lock file is skipped when the check fails.
- **Source:** `src/files.c:342-380`.

### FILE-READ — Reading
1. While opening and reading, ^C raises SIGINT; an interrupted read stops, ALERT `Interrupted`, and keeps what was read. A FIFO shows HUSH `Reading from FIFO...` before opening. While a regular read is in progress, HUSH `Reading...` is shown (not in zero mode at startup).
2. The bytes are split into lines at LF (0x0A). The LF is not stored.
3. **CR LF:** unless *noconvert* (`-N`), a CR (0x0D) immediately before an LF is removed **on every line**. The buffer's format becomes DOS **only if the first line ended in CR LF**. Consequences: `a\r\nb\r\n` reads as DOS and is saved as CR LF (TEST-FILE-005). `a\nb\r\nc\r\n` reads as Unix with the CRs dropped, so saving writes plain LF (TEST-FILE-006: the CRs are lost). `a\r\nb\nc\r\n` reads as DOS and saving writes CR LF on every line, including `b` (TEST-FILE-007). With `-N`, CRs stay in the text (displayed `^M`) and the format is Unix (TEST-FILE-008). There is no Mac (CR-only) format: lone CRs are ordinary bytes.
4. NUL bytes become the internal encoded NUL (`18` BYTE-NUL). All other bytes are kept as they are, including invalid UTF-8 (TEST-FILE-011).
5. If the data ends without LF, the last line contains the remaining bytes. Otherwise the last line is empty. When inserting into an existing buffer, the read lines are grafted at the cursor (FILE-INSERT). For a new buffer, a magic line is added when needed (`05` EDIT-001).
6. Line count N = number of LFs, plus 1 if data follows the last LF.
7. Messages: if, for an existing file opened into a new buffer, `access(W_OK)` fails (not in view mode): ALERT `File '<name>' is unwritable` (TEST-FILE-015). Else, unless (*zero* or *minibar*) when opening a new buffer: REMARK `Read N line(s) (converted from DOS format)` when DOS was detected, else REMARK `Read N line` / `Read N lines` (plural forms). A read error (other than EINTR) gives ALERT with the `strerror` text.
8. Format of the buffer: with *unix* (`-u`), Unix regardless; otherwise the detected format, if the buffer had none yet (an inserted DOS file does not convert a Unix buffer).
- **Source:** `src/files.c:648-828`.
- **Evidence:** runtime TEST-FILE-005…011, -015, TEST-CLI-030.

### FILE-INSERT — Read File (`^R`, Ins, F5)
Refused in restricted mode (`02` KEY-042). Prompt (`17` PROMPT-*), with
`[from ./]` (or the operating directory):
- `File to insert [from ./]`, `File to insert unconverted [from ./]` (with *noconvert*), `File to read into new buffer [from ./]`, `File to read unconverted into new buffer [from ./]`.
- Keys: `M-F` toggles new-buffer mode for this prompt (not in view mode, where it beeps), `M-N` toggles no-conversion, `^X` switches to Execute Command (`12` FEAT-EXEC), `^T` opens the browser (choosing a file inserts it), Tab completes file names.
- Enter with a name: in new-buffer mode → FILE-OPEN into a new buffer (plus position-log restore) and the title updates. Otherwise the file is read into the current buffer at the cursor as one undoable INSERT. The cursor ends after the inserted text, and the buffer becomes modified if anything was inserted. A missing file: ALERT `File "<name>" not found` (no new buffer).
- Enter with an empty answer: in new-buffer mode → a new empty buffer; otherwise HUSH `Cancelled`.
- New-buffer mode reverts to its previous setting afterwards.
- **Source:** `src/files.c:1144-1340`.
- **Evidence:** runtime TEST-FILE-019.

## 2. Multiple buffers

### FILE-MULTI — Buffer list
Buffers form a circular list in opening order. A new buffer is inserted after
the current one. *prevbuf*/*nextbuf* (`M-,`/`M-.`, and `M-◂`/`M-▸` when not on a
Linux console) switch. With only one buffer: AHEM `No more open file buffers`.
After switching, the status bar shows HUSH `<name> -- N line(s)`, with ` (DOS)`
after the count in DOS format (`New Buffer` for unnamed; N without the final
empty line) — or, if the buffer kept an error from opening, that error once as
ALERT (FILE-MULTI-ERR). With *minibar* the line count goes into the mini bar.
With *zero* nothing is shown. The title bar shows `[i/n]`.
- The help-line tag for *exit* is `Close` when more than one buffer is open, `Exit` otherwise.
- Once a second buffer has existed, the title keeps showing `[i/n]` (e.g. `[1/1]`) even after others are closed (TEST-FILE-029).
- **Source:** `src/files.c:526-630`.
- **Evidence:** runtime TEST-CLI-027, TEST-FILE-029.

### FILE-MULTI-ERR — Deferred error messages
During startup, the first ALERT produced while the current buffer is not the
only one, and the buffer has not been read (format unset), is stored with that
buffer and shown when it is switched to (`01` CLI-036, TEST-CLI-050).

## 3. Writing

### FILE-WRITE — Write Out (`^O`, F3) and Save (`^S`)
1. **Prompt.** *writeout* always prompts (unless save-on-exit applies, FILE-EXIT). *savefile* prompts only if the buffer has no name. The prompt text is one of `Write to File`, `Write Selection to File`, `Append to File`, `Prepend to File`, `Append Selection to File`, `Prepend Selection to File`, followed by ` [DOS Format]` when the format is DOS and ` [Backup]` when backups are on (TEST-FILE-005/-012). The answer is pre-filled with the buffer's name, but empty when a mark is set (writing a selection), unless exiting.
2. Prompt keys: `M-D` toggles DOS format, `M-B` backups, `M-A` append, `M-P` prepend (append/prepend toggle each other off; switching clears a pre-filled answer equal to the buffer name), `^T` browser, `^Q` discard buffer (FILE-EXIT), Tab completion. Not in restricted mode: backup/append/prepend/browser are unavailable, and the selection is ignored (the whole buffer is written).
3. **Cancel** or Enter on an empty answer → HUSH `Cancelled`, nothing written.
4. **Name checks (overwrite mode):** compute the canonical full paths of the answer and the buffer name.
   - If the buffer has no name, a warning is needed when the answer exists. Otherwise a warning is needed when the answer differs from the buffer's name.
   - Warning in restricted mode: `File exists -- cannot overwrite` (ALERT + pause), back to the prompt.
   - If the buffer has a name and this is not a selection write: Yes/No `Save file under DIFFERENT NAME? ` — not Yes → back to the prompt.
   - If the answer exists: Yes/No `File "<name>" exists; OVERWRITE? ` (the name cropped to fit, with `...` in front) — not Yes → back to the prompt (TEST-FILE-016/-031).
   - **Same name, but the file changed on disk:** if the file exists and its mtime is newer than recorded, or its device/inode differ: ALERT `File on disk has changed` (pause), then Yes/No `File was modified since you opened it; continue saving? `. Yes → save. No → nothing is written, and the save is reported as done (the buffer stays modified). Cancel while exiting → back to the prompt (TEST-FILE-025).
5. **Writing** (FILE-WRITE-CORE) the whole buffer, or the selection (FILE-SELECTION) when a mark is set (not exiting, not restricted). Success: REMARK `Wrote N line` / `Wrote N lines` (N counts lines; an empty last line is not counted). With minibar, the size is shown in the bar instead.
6. **After a full overwrite under a name:** if the name changed, the lock file moves (old deleted, a new one written with *locking*), the buffer takes the new name, and the syntax is re-selected (re-coloring if it changed). Stat information is refreshed, the undo saved-point is set, and the buffer becomes unmodified (title redrawn).
- **Source:** `src/files.c:2036-2286`.
- **Evidence:** runtime TEST-FILE-001…018, -025, -031.

### FILE-WRITE-CORE — How bytes are written
1. Outside the operating directory (for normal writes) → ALERT `Can't write outside of <dir>`.
2. Backup, if enabled and the target exists and is not a FIFO (FILE-BAK).
3. Prepend: the existing file is first copied to a temporary file (FILE-TEMP). A FIFO target → ALERT `Error writing <name>: FIFO`. Read failure → ALERT `Error reading <name>: <reason>`. Temp failure → ALERT `Error writing temp file: <reason>`.
4. The target is opened with `O_WRONLY|O_CREAT` plus `O_APPEND` (append) or `O_TRUNC` (overwrite/prepend), with creation mode 0666 (subject to the umask). The file is **rewritten in place**, not replaced. Its inode, permissions, owner, hard links and extended attributes are kept, and a symbolic link is written **through** to its target (the link stays a link) (TEST-FILE-001/-003/-004). A new file gets `0666 & ~umask` (TEST-FILE-002: umask 077 → 0600). ^C during `open` (e.g. on a FIFO) → ALERT `Interrupted`. Other failures → ALERT `Error writing <name>: <reason>` (TEST-FILE-015: `Permission denied`; TEST-FILE-031: `No such file or directory`).
5. A FIFO target shows HUSH `Writing to FIFO...`; regular files HUSH `Writing...`.
6. Each line's bytes are written with encoded NULs decoded back to 0x00. Between lines: LF, preceded by CR in DOS format. **No line break after the last line.** Because the magic line is empty, a normal buffer ends with exactly one LF. With `--nonewlines` the text ends wherever the last line ends (TEST-FILE-010). Write failures → ALERT `Error writing <name>: <reason>`.
7. Prepend: the saved copy is appended after the buffer text, then the temporary file is deleted.
8. Except for FIFOs: `fflush` + `fsync`; failure → ALERT `Error writing …`.
9. On ENOSPC (disk full) for a normal write, after the error: a 3.2 s pause, ALERT `File on disk has been truncated!`, another 3.2 s pause, ALERT `Maybe ^T^Z, make room on disk, resume, then ^S^X`, and the stat information is refreshed.
- Metadata: nano does not restore the mtime of the written file (the system sets it). Permissions and owner are not changed for existing files.
- **Source:** `src/files.c:1711-1990`.

### FILE-SELECTION — Writing a selection
The marked region is written as if it were the whole buffer. If the region ends
in the middle of a line (end x > 0) and `--nonewlines` is off, a final newline
is added (TEST-FILE-018: selection `line1\nl` is written as `line1\nl\n`). The
buffer name, modified state and lock are unchanged.
- **Source:** `src/files.c:1992-2033`.

### FILE-FMT — Formats on save
The buffer's format decides the line breaks (DOS → CR LF). `M-D` at the Write
prompt toggles it for the buffer (it persists). With `-u` files are read as
Unix (FILE-READ 8) and therefore saved with LF (TEST-FILE-009).

### FILE-BAK — Backups (`-B`, `set backup`; not tiny; never in restricted mode)
Before overwriting an **existing regular** file:
1. HUSH `Making backup...`.
2. Name: without a backup directory, `<name>~` in the same place (the target of a symlink is not resolved; the name as given + `~`). With `-C dir`: the canonical full path of the file with every `/` replaced by `!`, inside dir, followed by `~`. If that exists, `~.1`, `~.2`, … up to `.99999` (TEST-FILE-013: `bk/!tmp!…!work!f.txt~`, then `…f.txt~.1`). If all are taken: ALERT `Too many existing backup files`; the save is abandoned.
3. An existing file with that name is first deleted (failure other than "not found" aborts the attempt, unless *allow_insecure_backup*). The backup is created exclusively (`O_EXCL`; with *allow_insecure_backup*, `O_TRUNC` without exclusion) with mode 0600. Its owner/group are set to the original's (a permission error is ignored), and its mode to the original's (TEST-FILE-012: 0640 preserved). The original's bytes are copied, synced, and its access and modification times are copied to the backup.
4. **So the plain `~` backup holds the file as it was before the latest save:** each save overwrites it (TEST-FILE-012: after two saves `f.txt~` contains the state before the second save).
5. **Failure:** an unreadable original → ALERT+pause `Cannot read original file`, then step 6 with the second attempt skipped. Other failures: delete the partial backup, then ALERT+pause `Cannot make regular backup` and `Trying again in your home directory`, and try `$HOME/<basename>~XXXXXX` (mkstemp). If that also fails: ALERT+pause `Cannot make backup`.
6. After a final failure: ALERT+pause with the `strerror` text. Unless the error is ENOSPC, Yes/No `Cannot make backup; continue and save actual file? ` — Yes → proceed with the save. Otherwise HUSH `Cannot make backup: <reason>`, and nothing is written.
- **Source:** `src/files.c:1550-1709`.
- **Evidence:** runtime TEST-FILE-012/-013.

### FILE-LOCK — Lock files (`-G`, `set locking`; not tiny; not in view mode)
- **Name:** `<dir>/.<basename>.swp`, where `<dir>` is the directory part of the name **as given** (`.` when none), so `f.txt` → `./.f.txt.swp`.
- **On opening** (into a new buffer): if a lock file exists and can be read:
  - fewer than 68 bytes, or not starting with `b0` → ALERT `Bad lock file is ignored: <lockname>`, and the file is opened **without** a lock (TEST-FILE-027);
  - otherwise Yes/No `File <name> is being edited by <user> (with <program>, PID <pid>); open anyway?` (the name cropped to fit; the user is bytes 28–43, the program bytes 2–11, and the PID the little-endian 32-bit value at 24–27) (TEST-FILE-026). Yes → continue and overwrite the lock with nano's own. No → the file is skipped. Cancel while starting up → nano exits immediately, with status 0 (TEST-FILE-028). Cancel later → the file is skipped.
  - unreadable → ALERT `Error opening lock file <lockname>: <reason>`, and the file is opened without a lock.
- **Writing a lock:** an existing lock file is deleted first (failure: MILD `Error deleting lock file <lockname>: <reason>`), then the file is created exclusively with mode 0666 & ~umask. Content: exactly 1024 bytes, all zero except: bytes 0–1 `b0`; bytes 2–11 `nano 9.3` (NUL-terminated within 10 bytes); bytes 24–27 the PID, little-endian; bytes 28–43 the user name (first 16 bytes, from the passwd entry of the effective UID); bytes 68–99 the host name (`gethostname`, at most 31 bytes); bytes 108–875 the file name as given (at most 768 bytes); byte 1007 = 0x55 when the buffer is modified, else 0x00 (TEST-FILE-014: `b0nano 9.3`, PID, `john`, `E16`, `f.txt`, 0x00 then 0x55 after the first edit). Failures: MILD `Couldn't determine my identity for lock file`, `Couldn't determine hostname: <reason>`, or `Error writing lock file <lockname>: <reason>`. The editing then continues without a lock.
- **Updates:** the lock is rewritten with byte 1007 = 0x55 when the buffer first becomes modified. It is **not** rewritten when the buffer becomes unmodified again.
- **Save as another name:** the old lock is deleted. If the new name already has a lock file: ALERT `Someone else is also editing this file` + 1.2 s pause, and nano writes its own lock anyway.
- **Removal:** when the buffer is closed (exit, close, or `die()`), the lock file is deleted. A missing lock file is not an error.
- **Source:** `src/files.c:129-340, 436-454, 1937-1946`; `src/nano.c:270-271, 370-375`.
- **Evidence:** runtime TEST-FILE-014, -026, -027, -028.

### FILE-RESTR — Restricted mode
Only names from the command line may be written: a named buffer cannot be saved
under another name, and an existing file cannot be overwritten through the
Write prompt (`File exists -- cannot overwrite`). An unnamed buffer (no files on
the command line) may be saved under a new, non-existing name. Typing into the
prompt is blocked when the buffer has a name: editing keys and characters do
nothing (`17` PROMPT-RESTR). No backups, no append/prepend, no browser. Insert,
execute, spell and suspend are refused. With `-o`, writes are also confined.

### FILE-EXIT — Exit / Close (`^X`, F2)
1. If the buffer is unmodified, or view mode is on → close (FILE-CLOSE).
2. With *saveonexit* and a name → save without asking (step 4), then close (TEST-FILE-021). With *saveonexit* and no name → ALERT+pause `No file name`, then ask.
3. Ask Yes/No `Save modified buffer? ` (`17` PROMPT-YESNO):
   - **Yes** → Write Out prompt as in FILE-WRITE, but writing the whole buffer even if a mark is set. A failed or cancelled write keeps the buffer open (HUSH `Cancelled`).
   - **No** → close without saving.
   - **^Q** (or ^X with modern bindings) → close without saving, **and the exit status becomes 2** (TEST-FILE-020).
   - **Cancel** → HUSH `Cancelled`.
4. At the Write Out prompt reached from exit, `^Q` (*discardbuffer*) closes the buffer without saving, also with exit status 2.
5. The `zzy` Easter egg: when exiting an unnamed buffer without save-on-exit and the user enters `zzy` as the file name (first time only), the credits are shown instead of saving (needs `LINES > 5`, `COLS > 31`; else AHEM `Too tiny`), and the buffer stays.
- **Source:** `src/nano.c:297-322`; `src/files.c:2088-2164, 2274-2286`.

### FILE-CLOSE — Closing
Delete the lock file. With the position log, record the position (`12`
FEAT-POSLOG). If other buffers remain: switch to the next buffer (with its
status message), remove the closed one, and update the title. Otherwise save
the history (with *historylog*) and exit (`13` SIG-EXIT).

### FILE-TEMP — Temporary files
Used for prepend, spell checking and formatting. The directory is the first of
`$TMPDIR`, `P_tmpdir` (`/tmp`) that resolves to a writable directory, else
`/tmp/`. The name is `nano.XXXXXX` plus the buffer name's extension (the part
from the last `.`, if it contains no `/`). It is created with `mkstemps`
(mode 0600) and removed after use.
- **Source:** `src/files.c:1416-1459`.

### FILE-TILDE — Tilde expansion
In file names entered at prompts or on the command line, a leading `~` (alone or
before `/`) becomes the home directory. A leading `~user` becomes that user's
home directory from the passwd database; for an unknown user the name is left
as is.

### FILE-OPDIR — Operating directory (`-o`)
The directory is canonicalized (with a trailing `/`), and the process changes
into it. A path is inside when its canonical form starts with the operating
directory. Paths that cannot be canonicalized (missing directories) count as
inside, except during tab completion. Reading, writing, browsing and tab
completion outside it are refused (`Can't read file from outside of <dir>`,
`Can't write outside of <dir>`, `Can't go outside of <dir>`).

### FILE-HUP — Emergency save
See `13` SIG-EMERG. Observed: `f.txt.save` (mode 0600), `f.txt.save.1` when
`.save` exists, `nano.<pid>.save` for unnamed buffers; stderr
`Received SIGHUP or SIGTERM`, an empty line, `Buffer written to <name>`; exit 1
(TEST-FILE-022…024).

## Original implementation notes
- `open_buffer`, `read_file`, `open_file`, `write_file`, `write_it_out`, `write_region_to_file`, `make_backup_of`, `do_lockfile`, `write_lockfile`.
- Writing a selection temporarily cuts the line list and the text at the region boundaries in place, and restores them afterwards.

## Evidence summary
| Requirement | Evidence |
|---|---|
| FILE-OPEN/PATH/READ | runtime TEST-CLI-023…026, TEST-FILE-005…011/-015/-019 |
| FILE-INSERT | runtime TEST-FILE-019 |
| FILE-MULTI | runtime TEST-CLI-027/-050, TEST-FILE-029 |
| FILE-WRITE/-CORE/-SELECTION/-FMT | runtime TEST-FILE-001…018/-025/-031 |
| FILE-BAK | runtime TEST-FILE-012/-013 |
| FILE-LOCK | runtime TEST-FILE-014/-026…028 |
| FILE-EXIT | runtime TEST-FILE-020/-021 |
| FILE-RESTR, FILE-TEMP, FILE-OPDIR | source; runtime tests planned |

## Open questions
- **Q-FILE-001:** Mixed line endings lose CRs silently when the first line ends in LF (TEST-FILE-006). Deterministic; reproduce.
- **Q-FILE-002:** In-place rewriting (no atomic rename) can leave a truncated file if nano dies during a write. Reproduce for parity; an atomic-write mode would be a deliberate deviation needing a decision.
- **Q-FILE-003:** The lock file stores the name as given rather than an absolute path, so other editors may not interpret it. Reproduce.
- **Q-FILE-004:** A bad lock file disables locking for that buffer without a further warning. Reproduce.
