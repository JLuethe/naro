# Naro

The familiar nano experience, rebuilt in Rust. GPL-3.0-or-later.

Naro is an independent Rust port of GNU nano, based on GNU nano 9.3.

Naro is a working terminal editor with byte-preserving buffers, nano keybindings,
undo/redo, search and POSIX regex replacement, file operations, backups and locks,
nanorc, syntax highlighting, tools, histories, macros, mouse input and translations.
The tested release matches 301 of 303 fixture-safe reference scenarios exactly;
the other two cover deliberate safety improvements. The CLI and regex suites
match all 38 and 162 cases. Full results and limits are in
[validation evidence](validation/README.md).

Compatibility work targets GNU nano commit
`6ed285c3ec7a1d228def4d4e7021c6ba269f620c` on Linux/glibc/ncursesw.
It is not yet a fully compatible replacement; see [implementation status](IMPLEMENTATION.md).
The upcoming 0.1.0 experimental release targets the default Linux x86_64 profile;
see the [release scope and acceptance checklist](RELEASE_CHECKLIST.md) for required
qualification and explicit deferrals. Tiny remains an optional source build.

Build with Rust and a C compiler, ncursesw development headers/library, and
libmagic development headers/library:

```sh
cargo build --release
./target/release/naro file.txt
```

On this machine Rust is installed under `~/.cargo/bin`; use
`~/.cargo/bin/cargo` if it is not on PATH. No system packages were installed.
The C bridge handles native library ABIs; editor behavior is Rust. There are no
Cargo package dependencies. Installed translations resolve relative to the executable; `NARO_LOCALEDIR`
provides an explicit override. Development builds fall back to `assets/locale`.
Syntax definitions in `assets/syntax` can be included from a nanorc file, as in nano.

Build the optional tiny profile separately:

```sh
cargo build --release --features tiny --target-dir target/tiny
./target/tiny/release/naro file.txt
```

Tiny retains basic editing, UTF-8, search/replace, POSIX regex and translations.
It omits undo/redo, selections, nanorc/syntax, help viewer, browser, multiple
buffers, histories, mouse and external tools. It requires ncursesw but does not
require libmagic headers or libraries. See the [tiny specification](spec/22-tiny-profile.md)
and [tiny validation](validation/tiny/README.md) for its measured scope.

Basic controls: Ctrl+O saves, Ctrl+X exits, Ctrl+G opens help, Ctrl+W searches,
Alt+U undoes, Alt+E redoes. Unsaved changes prompt before closing.

```sh
cargo test
cargo fmt --check
cargo clippy --all-targets -- -D warnings
python3 spec/tools/test_compare_runs.py
python3 spec/tools/test_nanoharness.py
python3 tools/check_regex.py --binary target/release/naro
python3 tools/validate_parallel.py --binary target/release/naro --out spec/evidence/naro-validation --jobs 4
```

Terminal validation requires tmux, terminfo, Python 3.11 or newer, and the saved reference
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


The [follow-up specification](spec/19-completion-and-release.md) is implemented
for the scoped default-profile preview. Its [validation reports](validation/follow-up/README.md)
cover selection-aware spelling, failure recovery, additional environments and
installation. See [INSTALL.md](INSTALL.md) for archives, user-level installation
and removal.
[Credits](CREDITS.md) acknowledge the upstream work and development assistance.
An optional `tiny` Cargo feature builds the reduced editor described below. A default-off Cargo `credits` feature
enables a separately tested `naro --credits` command.


The [root/home phase](spec/20-root-and-console.md) now implements GNU-compatible
home selection and verifies private root/device/browser cases. Its
[validation](validation/root-console/README.md) reports 27 exact new comparisons
and unchanged ordinary-user regression results. A separate no-home upstream
crash has an asserted safe fallback. Physical Linux console verification remains
deferred; readiness and explicit operator-trial tooling are available.

Linux console modifiers, rendering and macro replay are implemented. Both the
host and Ubuntu optimized candidates match all 19 cases on a genuine guest VT
with emulated PS/2 keys; see [console evidence](validation/console-vm/README.md).
Physical keyboard/operator testing remains separate. The
[closure specification](spec/21-console-release-closure.md) defines final
regression, packaging and delivery acceptance; [closure evidence](validation/closure/README.md)
identifies the exact binaries and artifact provenance.

Naro contributions are licensed under GPL-3.0-or-later. Upstream portions,
assets and native dependencies retain their original license terms and notices.
See [LICENSE](LICENSE), [NOTICE](NOTICE), [credits](CREDITS.md), and the original
file headers for licensing and attribution details.

See [SECURITY.md](SECURITY.md) for vulnerability reporting. GitHub private
vulnerability reporting is not currently enabled; do not post sensitive details
in public issues. Contribution and verification instructions are in
[CONTRIBUTING.md](CONTRIBUTING.md).

GNU nano's binding/help data, syntax definitions and translations retain their
upstream notices in `src` and `assets`. Redistribution must preserve applicable
upstream and dependency license terms and notices alongside Naro's license and
attributions.

Naro is an experimental preview. Building it does not replace the system's
`nano` or install a system utility. Build and release tooling does not publish
GitHub releases or crates.io packages automatically. See [INSTALL.md](INSTALL.md)
for explicit installation and removal steps and the measured compatibility
limits of packaged binaries.
