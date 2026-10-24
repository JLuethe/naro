Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

# 15 — Rust architecture

This is an implementation design, not evidence that code already implements
all of the behavioral requirements. Normative behavior remains in 01–14,
17–18. Target: Linux/glibc, ncursesw, the pinned reference's default features;
GPL-3.0-or-later for newly written source, with upstream attribution for reused
data. The repository is `https://github.com/JLuethe/naro`.

## 1. State and ownership

Use byte strings, never Rust `String`, for editable content and paths. Start
with `Vec<Vec<u8>>` lines: predictable behavior and simple edits outweigh a
rope's performance during parity work. Positions are typed `(line, byte)`;
display columns and character counts are distinct values. Maintain the magic
line after every text mutation. Embedded file NUL is encoded as internal LF;
structural line breaks live between vectors. No lossy conversion on save.

A Buffer owns lines, cursor/preferred column, viewport, mark/soft-mark, anchors,
name/format/stat snapshot, syntax, modified flag and undo history. Editor owns
a nonempty circular buffer list, current index, shared cutbuffer, search/options,
histories, key tables, macros, message state and active interaction. Buffer
switches retain per-buffer state. Prompts and questions are explicit modes;
callers specify their continuation (save, exit, replace, insert, tool).

## 2. Module boundaries

| Module | Owns / contract |
|---|---|
| `bytes` | Valid/invalid UTF-8 stepping, NUL encoding, libc widths/classes/case, columns; doc 18 |
| `buffer` | Insertion, deletion, cuts, regions, line operations and history; docs 05/06 |
| `config` | CLI parser, flags, rc lexer, precedence and diagnostics; docs 01/10 |
| `input` | ncurses codes plus nano decoder, bursts, paste/verbatim/mouse/macros; docs 02/03 |
| `terminal` | Narrow ncurses/termios FFI, lifetime guard, resize and restoration; docs 04/13 |
| `render` | Layout and byte-to-cell conversion, title, status, help, decorations; doc 04 |
| `editor` | Dispatch and interaction state machine; shared prompt editing, docs 07/17 |
| `files` | Read/write in place, backups/locks, stat checks, confinement; doc 08 |
| `regex` | Owned POSIX regex handle, compile/execute/error interfaces; doc 11 §R |
| `syntax` | rc syntax rules, selection and multiline caches; doc 11 |
| `features` | Justify, browser, tools, histories/help/counts; docs 09/12 |
| `i18n` | gettext catalogs/plurals and locale encoding; doc 14 |

Small modules may initially share a file; these are dependency boundaries.
Rendering reads state and performs no edits. Mutation methods update mark,
anchors, counts and history together. Dispatch determines view/restricted
permission before mutation. Impossible functions from string bindings must
fail harmlessly (Q-KEY-001).

## 3. Undo, files and error handling

Begin with owned before/after edit transactions carrying text, cursor, mark,
operation noun and saved-state identity. Group consecutive typing/deletion/cut
by the exact adjacency rules of UNDO-003; do not group by elapsed time. A later
range-delta representation can reduce memory without changing history effects.
Saved point is a history identity, not byte equality; undo/redo clears mark.
Compound operations remain one externally visible item, replace-all one per
replacement. Preserve the no-op magic-line backspace quirk (UNDO-007).

Use `OpenOptions`/libc to rewrite files in place; do not substitute atomic rename
(Q-FILE-002). Check confinement before opening and follow symlinks as specified.
Backups precede truncation. Emergency files use exclusive creation and 0600.
Normal failures return structured diagnostics; no unwrap/panic on file input,
regexes, terminal sizes or configuration. Keep terminal guards alive during
error reporting; close locks even when exiting abnormally.

## 4. Native compatibility boundaries

Choose ncursesw FFI for screen/input and libc POSIX regex FFI (Q-IN-001,
Q-REGEX-001). These retain terminfo keypad decoding, ESC delay, locale-aware
width/classes, leftmost-longest matching, GNU ERE extensions, invalid-byte rules,
submatches and `regerror` wording. The Rust `regex` crate is not a substitute.
Use a tiny C bridge for opaque `regex_t` and platform-dependent termios/curses
constants rather than guessing layouts in Rust. All editor behavior remains
Rust; the bridge exposes bounded allocation/match/free and terminal primitives.
Every native pointer has one Rust owner, freed by Drop; no borrowed pointer
outlives a native call. Compile patterns as byte C strings, handle embedded NUL
through the specified encoding, and validate results before slicing bytes.

Initialize locale once with `setlocale(LC_ALL, "")` before threads; detect exact
`UTF-8` via `nl_langinfo`. libc `wcwidth`, classes and folding define the envelope.
Use gettext/ngettext with shipped pinned catalogs; its charset conversion covers
byte-mode locales (Q-I18N-001). Paths use Unix OsStrExt. Other platforms need a
separate tested compatibility envelope rather than assumed equivalence.

## 5. Terminal and signal lifetime

Use a Terminal guard to save/restore termios, enter/leave ncurses, turn paste and
mouse modes on/off, and restore cursor visibility. Signal handlers only store
atomic flags or wake a self-pipe; allocation, locks, formatting, ncurses and file
I/O occur in the event loop. Use polling input with a bounded timeout so HUP/TERM
can trigger emergency saves even without keystrokes. WINCH recomputes layout;
CONT reinitializes. Suspend restores the terminal first. Ensure child processes
do not inherit editor handlers/raw terminal state unintentionally.

A `catch_unwind` boundary around the editor loop restores the terminal and
attempts emergency saves on Rust panics. Do not attempt recovery from arbitrary
memory corruption in a signal handler. The panic equivalence specified in doc
13 requires a deliberate diagnostic code; record platform-specific limits.
The invalid CLI regex crash is fixed, never emulated (Q-DEF-001).

## 6. Build and validation

Install Rust with rustup under the user's home; do not install system packages.
Use Cargo.lock, edition 2024, minimal dependencies, and a reproducible build
script for the native bridge. Binary `naro` is the primary entry point; a `nano`
entry point can support argv compatibility. Retain GPL LICENSE and upstream
attribution. Never invoke the reference executable from the implementation.

Run byte/coordinate, history/saved-state and regex-corpus tests before terminal
integration. Then use `16`'s harness `--binary` with separate evidence outputs.
Record semantic file progress separately from complete terminal equality.
Build success is necessary but does not establish a complete reimplementation.
Track unimplemented functions explicitly; no passing claim based on a smoke test.
