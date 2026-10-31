# Claude focused code review

Source-only review of the immutable cache snapshot; no runtime claims.
The subsequent tiny-only adjustment limits alert preservation to Interrupted
and preserves tiny footer cache across same-size resume. Default behavior is
unchanged. Frozen qualification and exact asset review remain separate gates.

No blocker in this delta, and none that affects the default 0.1 release. The two caveats I have are tiny-only and low severity.

## The footer cache matches when nano resets its footer
nano starts each footer from a blank window whenever it calls `window_init`; otherwise it draws the shortcuts over the old ones. I checked each case where nano does that:

- **Help viewer:** nano's help turns off NO_HELP and ZERO and resets the window only when one of them was set (`help.c:404-407`, and `547-548` on exit). naro's `open_help` also turns both off (`features.rs:963-974`), so the cache key changes (help footer present ↔ absent, zero on ↔ off) and the old footer isn't reused. With only minibar set, nano just blanks the status row (`help.c:409`), and naro's key stays the same, so it keeps drawing over the old footer, as nano does.
- **NO_HELP / ZERO toggles, at the prompt too** (`nano.c:1082/1091`, `prompt.c:539`): covered by the help-footer and zero parts of the key. Your new 5-row and minibar 4-row tests target the case I reported.
- **Resize** (`winio.c:224` → `regenerate_screen` → `nano.c:1063`) and **resume after suspend** (`continue_nano` sets `the_window_resized`, `nano.c:1011`): both handled by the explicit resets on signals 28 and 18 and in `suspend()`.
- **External spell checker** (`text.c:2173` `regenerate_screen`): handled by the reset in `features.rs:1737`.
- **Linter** (`text.c:2803/2944`): it turns NO_HELP off and restores it on exit (`features.rs:2027-2028`), which changes the key.
- Setting `last_footer_layout` after `canvas.flush` keeps it tied to the frame that was actually drawn. A hidden-help frame sets `None`, so the next help frame starts clean.

## The toggle-message suppression matches nano
`editor.rs:1379-1383` follows `nano.c:1140-1142` (NO_HELP, LINE_NUMBERS or WHITESPACE under minibar, zero, or a one-row terminal). It comes after the "Too tiny" check and the flag change, and nothing after it is skipped except the message. The zero and constant-show toggles return earlier, as before.

## Default signal handling is unchanged
Signal 28 still clears the message in the default build. The only addition is resetting the cache before `nr_resize`.

## Low, tiny only
1. **Resize now keeps *any* level-7 alert in tiny, not just the FIFO `Interrupted` one** (`editor.rs:600-608`). For example, `Error writing f: Permission denied` and then a resize now stays on screen in naro-tiny, where before it was cleared. Your runtime evidence only covers the FIFO interrupted case. Either limit the check to an alert set by the save in progress, or add one tiny test with a different alert followed by a resize. This doesn't block default.
2. **tiny suspend/resume:** in tiny builds `continue_nano` only calls `terminal_init` and doesn't reset the window (`nano.c:1012-1014`). So tiny nano keeps drawing over the old footer after `fg`, while naro-tiny now redraws it clean on 18. You can only see this at 5 rows or fewer, if the gaps differ. This is a source inference and hasn't been run.

## Acknowledged
The tiny result you reported: a single open without the mask aborts like nano, and the remaining difference was that naro erased the alert. That fits this repair.

## Limits
- Yes/No questions (`render.rs` Question branch) still blank the bottom two rows before drawing Yes/No. At 5 rows or fewer nano draws Yes/No over the old shortcuts (`blank_bottombars` does nothing there). This existed before; the cache now just carries that frame forward. Your save-progress flows that go through a question at 5 rows will show whether it matters.
- I didn't trace pause frames (`pause_until`, which blanks help rows when not paused) at 5 rows or fewer. That's outside this delta.
- I'm making no runtime claims: the tiny 3-case rerun, the 22+8 default tests, the full frozen qualification and the final evidence review are all still pending.
