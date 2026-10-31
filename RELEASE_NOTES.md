# NARO 0.1.0 candidate release notes

Status: approved candidate wording; publication pending. No release tag,
publication date or hosted download is announced by this document.

NARO is an independent Rust port of GNU nano 9.3. The first release is an
experimental Linux x86_64 GNU/glibc editor with familiar nano bindings,
byte-preserving editing, undo/redo, search and regex replacement, multiple
buffers, nanorc, syntax highlighting, macros and translations.

## Scope

The primary download uses the default feature profile and the Ubuntu 24.04
build. Tiny remains source-build only. Native dependencies include glibc,
ncursesw and libmagic; this is not a pure-Rust or static executable.
The supported envelope is the recorded build/runtime environment, not every
Linux distribution or operating system. See [INSTALL.md](INSTALL.md).

The qualified source is `fd91763c4f14d9bed8187d64d44f2136440b7b3e`.
The Ubuntu executable SHA-256 is
`33a39eb339492720ec6166e84fea421749e0b2ec3bd612b276c2377f91b7c4a1`.
The selected archive names are `naro-0.1.0-x86_64-unknown-linux-gnu.tar.gz` and
`naro-0.1.0-source.tar.gz`. Use the checksum file accompanying the final approved
archive set. Documentation repackaging can change archive hashes without changing
this executable. Use the final qualification receipt and SHA256SUMS distributed
with the refreshed archives; the step 7 archive hashes identify the older packages.

## Fixes included during candidate testing

- Bracketed paste now follows nano's hard-wrap behavior in the reproduced cases.
- Soft-wrap vertical movement and page navigation preserve the expected cursor
  position and viewport behavior.
- Widening a terminal preserves the expected top logical line.
- Line-number gutters on continuation rows use the expected attributes.
- Replace undo/redo restores the expected cursor position.
- Relative rcfile diagnostics show the expected absolute path.
- Additional tab-boundary, end-of-file, selection and structural-edit regressions
  are covered by permanent reference-based tests.

These describe the tested fixes, not a claim that all related combinations have
been exhaustively verified.

## Qualification

The complete technical gate passed 97/97 checks. Both frozen candidates passed
the 303-case corpus at the retained 301 full / 302 file-exit expectations,
119/119 newer exact regressions, 38 CLI and 162 regex checks, and 19/19 genuine
guest-VT comparisons. Ubuntu used its own nano reference and observations.

Package checks cover offline source rebuilding, installed hashes, ordinary and
spaced prefixes, symlink launching, 41 catalogs, syntax, malformed archives and
safe uninstall. Source rebuilding matches production inputs/features; bit-for-bit
reproducibility is not claimed. [Validation](validation/README.md) provides exact
results and evidence identities.

## Known differences and remaining limits

Existing declared differences are invalid-regex recovery, rejecting NUL as Yes,
two HUP/TERM external-tool cleanup cases, and isolated-root no-home tilde recovery.
Six baseline cases are excluded. Nine audit citations remain unresolved as
explained in [COVERAGE_REVIEW.md](COVERAGE_REVIEW.md).

Physical keyboard trials, other architectures/OSes, broad fuzzing and a security
audit are not established by this qualification. The guest-VT results use
emulated PS/2 input. Earlier tiny and sanitizer results retain their original
artifact scope and are not new binary downloads.

## Reporting and attribution

For ordinary bugs, include build identity, OS, terminal, locale, synthetic input,
exact keys/commands, expected behavior and observed behavior. Use
[GitHub issues](https://github.com/JLuethe/naro/issues) or follow
[SECURITY.md](SECURITY.md) for suspected vulnerabilities.

NARO is separate from GNU nano. GNU nano contributors and the Free Software
Foundation supplied reference behavior and reused data/assets. See
[LICENSE](LICENSE), [NOTICE](NOTICE), [CREDITS.md](CREDITS.md) and original file
headers. John Luethe develops NARO; thank you to OpenAI for their generous
support. Publication approval remains separate from candidate qualification.
