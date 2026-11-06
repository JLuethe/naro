# NARO

NARO is an independent Rust port of GNU nano, based on nano 9.3. It is an
experimental terminal editor for Linux, with familiar nano keybindings,
byte-preserving editing, undo/redo, search and regex replacement, multiple
buffers, nanorc configuration, syntax highlighting, macros and translations.

This source tree is version **0.1.2**, a local development candidate with safety
and release-readiness changes awaiting integrated qualification. It uses NARO's
name and version in the editing title, CLI and help. `naro --credits` prints the
project attribution in default and tiny builds. The 0.1.1 frozen host and Ubuntu
candidates were qualified separately; those results do not qualify this tree.
See [GitHub Releases](https://github.com/JLuethe/naro/releases) for published
packages. The prior primary binary profile is Linux x86_64 GNU/glibc, built and
tested under Ubuntu 24.04/glibc 2.39.

## Get started

Download the binary archive and matching source for your selected version from
[GitHub Releases](https://github.com/JLuethe/naro/releases).
Download all seven release files and run `sha256sum -c SHA256SUMS` before installing.
Read [installation instructions](INSTALL.md) for dependencies, source builds and removal.

To build the default editor from a source checkout, provide Rust/Cargo, a C
compiler, pkg-config, ncursesw development files and libmagic development files:

```sh
cargo build --release --locked
./target/release/naro example.txt
./target/release/naro --credits
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

## Historical 0.1.1 qualification

The qualified executable records source revision
`accc766af9ff7e36ec206dea697410e3f8f31674`. The primary Ubuntu executable SHA-256 is
`70ab6932323a6b679e628bdb6cfddead8a6ff50160d741782ae8649664dc5a00`.
Packaging/documentation commits may be newer while retaining the same production
fingerprint, verification tools and exact executable.

For both frozen host and Ubuntu candidates:

- Terminal corpus: 303 accepted records: 26 raw exact, 275 identity-reviewed and
  two declared differences; 302 file/exit matches and six fixed exclusions.
- CLI 38, regex 162 and safety 2 passed.
- Historical follow-ups: 53 accepted, including two declared signal-cleanup differences.
- Additional regressions: all 151 cases accepted; raw and identity-reviewed results
  are counted separately.
- Genuine guest Linux VT: 19 accepted per candidate, one raw exact and 18
  identity-reviewed, with emulated PS/2 input.

The complete collector passed 69/69 checks; the release gate recomputed cleanly
from raw evidence with zero unexpected differences in all 38 accounting sets.
NARO's branding is an intentional reviewed difference from GNU nano. Filename,
state, geometry, attributes, cursor and non-identity text remain checked.

Packaging covers offline corresponding-source rebuilding, installation/removal,
all 41 catalogs, syntax and malformed-archive rejection. These are scoped test
results; complete nano parity and a security audit are not established.

[0.1.1 qualification receipts](validation/release-0.1.1-final-2026-10-31/README.md)
identify the exact inputs and evidence. [Implementation status](IMPLEMENTATION.md)
explains known differences; the [coverage review](COVERAGE_REVIEW.md) retains nine
unresolved specification-to-test citations. Historical reports keep their original
artifact scope.

## Scope and dependencies

Editor behavior is implemented in Rust with a small native C bridge. NARO uses
ncursesw, libc/POSIX interfaces and libmagic; it is not a pure-Rust or static
binary. The GNU nano executable is a testing reference, not a runtime dependency.

External spelling, formatting, linting and command execution need suitable
programs installed and configured separately. They are not included in the
binary archive. See [optional tools and profiles](INSTALL.md#optional-tools-and-profiles).
Tiny is an optional source-build profile; no tiny binary was selected for 0.1.1.
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

The [release notes](RELEASE_NOTES.md) describe the 0.1.2 candidate and the
historical 0.1.1 update. The
[release checklist](RELEASE_CHECKLIST.md) distinguishes completed technical
qualification from remaining publication gates.
