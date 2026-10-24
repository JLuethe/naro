# Naro

The familiar nano experience, rebuilt in Rust. GPL-3.0-or-later.

Naro is a working terminal editor with byte-preserving buffers, nano keybindings,
undo/redo, search and POSIX regex replacement, file operations, backups and locks,
nanorc, syntax highlighting, tools, histories, macros, mouse input and translations.
Compatibility work targets GNU nano commit
`6ed285c3ec7a1d228def4d4e7021c6ba269f620c` on Linux/glibc/ncursesw.
It is not yet a fully compatible replacement; see [implementation status](IMPLEMENTATION.md).

Build with Rust and a C compiler, ncursesw development headers/library, and
libmagic development headers/library:

```sh
cargo build --release
./target/release/naro file.txt
```

On this machine Rust is installed under `~/.cargo/bin`; use
`~/.cargo/bin/cargo` if it is not on PATH. No system packages were installed.
The C bridge handles native library ABIs; editor behavior is Rust. There are no
Cargo package dependencies. Translations live in `assets/locale`; override their
location with `NARO_LOCALEDIR` when moving an executable away from this checkout.
Syntax definitions in `assets/syntax` can be included from a nanorc file, as in nano.

Basic controls: Ctrl+O saves, Ctrl+X exits, Ctrl+G opens help, Ctrl+W searches,
Alt+U undoes, Alt+E redoes. Unsaved changes prompt before closing.

```sh
cargo test
cargo fmt --check
cargo clippy --all-targets -- -D warnings
python3 spec/tools/test_compare_runs.py
python3 tools/check_regex.py --binary target/release/naro
python3 tools/validate.py --binary target/release/naro --out spec/evidence/naro-validation
```

Terminal validation requires tmux, terminfo, Python 3, and the saved reference
corpus. It freezes the candidate executable, records its SHA-256, creates private
fixtures, and compares screens, attributes, cursor/modes, saved files and exit
state. Six inherited scenarios are excluded by default: five involve absolute
paths outside fixtures and one requires the optional tiny build. Validation
reports actual differences; an assertion-free recorded run is not called a pass.
Never use the corpus to test against real user or system files.

The [behavioral specification](spec/00-overview.md),
[test plan](spec/16-test-plan.md), [coverage audit](spec/97-coverage.md), and
[decisions](spec/99-open-questions.md) are checked in with reference evidence.
The pinned nano source checkout is not modified or invoked by Naro.
See [NOTICE](NOTICE) and the original headers for reused data and catalog licenses.
