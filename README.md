# NARO

NARO is an independent Rust port of GNU nano, based on nano 9.3. It is an
experimental terminal editor for Linux, with familiar nano keybindings,
byte-preserving editing, undo/redo, search and regex replacement, multiple
buffers, nanorc configuration, syntax highlighting, macros and translations.

[NARO 0.1.0 is published as an experimental prerelease](https://github.com/JLuethe/naro/releases/tag/v0.1.0).
Technical qualification and independent release review are complete. The primary binary package targets Linux
x86_64 with GNU/glibc and was built and tested under Ubuntu 24.04/glibc 2.39.
Other distributions and platforms are not certified by these results.

## Get started

Download the binary archive and matching source from the [v0.1.0 release](https://github.com/JLuethe/naro/releases/tag/v0.1.0).
Download all seven release files and run `sha256sum -c SHA256SUMS` before installing.
Read [installation instructions](INSTALL.md) for dependencies, source builds and removal.

To build the default editor from a source checkout, provide Rust/Cargo, a C
compiler, pkg-config, ncursesw development files and libmagic development files:

```sh
cargo build --release --locked
./target/release/naro example.txt
```

Building does not install NARO or replace the system's `nano`.

| Action | Default binding |
| --- | --- |
| Save / exit | Ctrl+O / Ctrl+X |
| Help / search | Ctrl+G / Ctrl+W |
| Undo / redo | Alt+U / Alt+E |

NARO prompts before discarding unsaved changes. Configuration can change
bindings and behavior; see the editor's help and the installed configuration
example for your selected profile.

## What has been tested

The qualified production source is `b934b1fcefa74adcf631c39b20ecd133c70edc59`.
The primary Ubuntu executable's SHA-256 is
`9af710dbb614423b53425c093a41a95b4733cfd539bfe40047b1bdac0bd7419d`.
Documentation commits may be newer than the compiled source.

For both the frozen host and Ubuntu candidates:

- Terminal corpus: 303 recorded cases, 301 full matches and 302 file/exit
  matches, with six separately excluded cases.
- CLI and regex checks: 38 and 162 passed.
- Historical follow-ups: 53 cases, 51 exact and two declared cleanup differences.
- Additional regressions: 151/151 exact comparisons.
- Genuine guest Linux VT: 19/19 exact comparisons using emulated PS/2 input.

The complete technical collector passed 101/101 checks. Packaging includes
corresponding-source rebuilding, installation/removal, all 41 catalogs, syntax
loading and archive rejection checks. These results are scoped evidence, not
proof of complete nano compatibility or a security audit.

[Current validation index](validation/README.md) identifies the exact inputs,
reports and limits. [Implementation status](IMPLEMENTATION.md) explains known
differences and the [coverage review](COVERAGE_REVIEW.md) lists nine unresolved
specification-to-test citations. Historical reports identify older builds.

## Scope and dependencies

Editor behavior is implemented in Rust with a small native C bridge. NARO uses
ncursesw, libc/POSIX interfaces and libmagic; it is not a pure-Rust or static
binary. The GNU nano executable is a testing reference, not a runtime dependency.

External spelling, formatting, linting and command execution need suitable
programs installed and configured separately. They are not included in the
binary archive. See [optional tools and profiles](INSTALL.md#optional-tools-and-profiles).
Tiny is an optional source-build profile; no tiny binary is selected for 0.1.0.
Physical keyboard trials and other architectures/operating systems remain outside
this release's qualification scope.

## Bugs, contributions and attribution

Report ordinary bugs through [GitHub issues](https://github.com/JLuethe/naro/issues),
using synthetic files and including build identity, terminal, locale and exact
reproduction steps. Use [SECURITY.md](SECURITY.md) for suspected vulnerabilities.
[CONTRIBUTING.md](CONTRIBUTING.md) explains development and verification.

NARO is developed by John Luethe. Thank you to OpenAI for their generous support.

NARO is a separate project from GNU nano. GNU nano's contributors and the Free
Software Foundation supplied the reference behavior and reused binding/help
data, syntax definitions and translations. The project is GPL-3.0-or-later;
reused material and native dependencies retain their original terms and notices.
See [LICENSE](LICENSE), [NOTICE](NOTICE), [CREDITS.md](CREDITS.md) and file headers.

The [release notes](RELEASE_NOTES.md) describe the 0.1.0 candidate. The
[release checklist](RELEASE_CHECKLIST.md) distinguishes completed technical
qualification from remaining publication gates.
