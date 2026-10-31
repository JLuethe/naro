# Claude static review of the prior save-progress change

Scope: immutable snapshot of production change `16f6398`; read-only source
review, no tests run by Claude. Findings led to the new repair, and do not
constitute approval of replacement candidates.

I found one new correctness problem in the change and one serious data-loss bug that was already in the code before it. Nothing else in the change looked wrong, and I didn't find any false passes in the test gate, the waits, or the expected results. All findings come from reading source only; I ran nothing.

## Findings

### 1. Medium–Low: the "Writing..." frame can still show the old tab-completion list
**Where:** `src/prompts.rs:694-698` (progress screen copied from `last_screen`), `src/prompts.rs:389` (`submit` clears the completion list), `src/render.rs:853-857`.

**Confirmed in naro's source:**
- One Tab with several matches fills `self.completion` (`prompts.rs:898-902`). `draw` paints that list into the edit area, so it ends up in `last_screen`.
- On Enter, `submit` clears `self.completion`, but `try_write` builds the progress screen from the stale `last_screen`.
- So "Writing..." / "Writing to FIFO..." are flushed with the old list still covering the buffer text.

**In nano (read from source, not run):**
- When the prompt ends, `do_prompt` calls `edit_refresh` if a list is showing (`prompt.c:647-648`). That redraws the edit window but only queues it (`winio.c:3430`).
- `statusline()` then calls `wrefresh(footwin)` (`winio.c:2391`), which pushes every queued window to the screen. So nano's "Writing..." frame shows the restored buffer with no list.
- Before the first message (the open stage for a regular file), both programs still show the list, so they agree there.

**Suggested fix:** when the progress screen is built after a list was showing, repaint the edit area first (for example, call `render::edit` on the copied screen), or redraw the whole frame when `completion` was non-empty when Enter was pressed.

**Suggested test:** in `work/` put `f.txt` (`hello\n`) and `f.txt.a`. Run `-I f.txt` with the SYNC gate. Steps: `X`, `^O`, wait for `Write to File:`, `End`, `Tab` (wait until the list shows), `Enter`, wait for `home/SYNC.ready`, take a snapshot. Expected (same as nano): the edit area shows `Xhello`, not the list. Do a FIFO version too (`Writing to FIFO...` stage).

### 2. High (existed before this change; outside the patch): prepending to an unreadable file wipes it
**Where:** `src/files.rs:216-220`, `243-257`.

- `old` is `fs::read(&p).ok()`, so a read failure silently becomes `None`.
- In prepend mode (`mode == 2`) the file is still opened with `truncate(mode != 1)`, which is true. Only the buffer is written, and the original contents are lost.
- nano stops before opening: `fopen(realname,"rb")` fails, it shows `Error reading %s: %s`, and nothing is written (`files.c:1764-1769`). Spec `08-files.md:111` describes nano's behaviour.
- nano also fails when prepending to a file that doesn't exist; naro creates it. That difference is harmless.

**Reproduction (as a non-root user):** `printf 'orig\n' > f; chmod 0222 f`. Open another buffer, `^O`, `M-P`, type `f`, Enter. naro leaves `f` holding only the buffer text; nano shows `Error reading f: Permission denied` and leaves `f` unchanged.

This isn't caused by the change, but it falls under the "final saved bytes or safety" check you asked for. It should be fixed and tested separately, not in this change.

## Checked and consistent with nano
- **Message order:** after the backup and the prepend/FIFO checks, `Writing to FIFO...` (left out of tiny, matching `#ifndef NANO_TINY`), then open, then `Writing...`, then write, then old contents for prepend, then fsync except for FIFOs. This matches `files.c:1789-1908`. Changing the FIFO check to a shared `fifo` variable doesn't change which writes get an fsync.
- **Bytes and file metadata:** the data written, the open flags, which writes get fsync, and the buffer's name/stat/saved updates are the same as before the change.
- **Suppressed messages:** `action_level <= 4` matches the `importance < lastmessage && lastmessage > NOTICE` rule. Since `key()` resets the level on every keystroke, as nano does at `nano.c:1588`, the check almost never blocks anything. The progress paint doesn't set `action_level`, which is harmless because the success or error message replaces it straight away.
- **Hidden cursor:** this matches nano's `curs_set(0)` after reading any key (`winio.c:260`). It is placed after all the early returns, and the next `draw` (`nr_refresh`) shows the cursor again. When nothing is painted, `last_screen` correctly stays the prompt or question screen.
- **Layout:** the status-row blank, the brackets when `start > 1`, the cursor column, `statuscolor` (nano's `STATUS_BAR`) with no `...`, translation via `native::tr`, and keeping the title and the prompt/Yes-No shortcut rows all match nano's `statusline`.
- **Failure flows:**
  - ENOSPC now copies the progress screen into `pause_screen`. `draw` refills the status row and keeps the help rows, so the result looks the same as before.
  - Backup-question → Yes runs a new `try_write` after a key reset, so `Writing...` shows over the Yes/No screen, as in nano.
- **Test gate:**
  - It catches Rust's `open64`/`write`/`fsync` and nano's `open`/`fwrite`/`fsync`. Read-only opens and the gate's own files are skipped, and each phase fires once.
  - The "ready" file is created only after the synchronous paint (`wrefresh` / `nr_refresh`) has already reached the terminal, so the snapshot doesn't depend on timing.
  - Missed matches (for example a path that resolves to a different form) or a timeout make the run hang or fail with a different error message; they can't pass silently.
  - The expected file contents are exact and nothing is normalized.
  - The FIFO case gates the open (no message yet / `Writing to FIFO...`) separately from the write (`Writing...`), with a reader that waits for the release.

## Remaining limits and missing tests
- **Tiny builds:** tiny nano never calls `fsync` (`files.c:1880-1909`), so the SYNC-gated probes can't run there; they would hang rather than pass falsely. Tiny progress parity, including no FIFO message, isn't covered.
- **Not covered at all:** a 1-row terminal, `-x`/no help rows, and FIFO messages in narrow terminals (fewer than about 22 columns, where the text is cut off without brackets). There's also no German FIFO case, no append to a FIFO, no `-B` backup save, and no save-on-exit (`-t` / `saveonexit`).
- **"Making backup..." is still missing:** nano shows this message (`files.c:1563`, and spec `08-files.md:135` lists it), but naro never paints it. With `-B`, the screen differs from nano during the backup step. It was outside the approved scope, but the spec currently claims it.
- **Ctrl-C during a blocked FIFO open:** the spec (`08-files.md:112`) says nano shows `Interrupted`, but naro has no Ctrl-C handling around `open`. This existed before the change.
- **Not checked:** I didn't read the hidden-cursor rerun output or the harness code that compares snapshots, and I didn't look at commit `16f6398` beyond your statement that it matches this snapshot. The 13/13 and 0/13 results are Codex's numbers, not mine.
