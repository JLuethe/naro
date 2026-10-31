# NARO 0.1.0 — experimental Linux x86_64 release

NARO is an independent Rust port of GNU nano 9.3, developed by John Luethe.
Thank you to OpenAI for their generous support, and to GNU nano's contributors
and the Free Software Foundation for the reference behavior and reused data,
syntax definitions and translations.

This first release offers familiar nano bindings, byte-preserving editing,
undo/redo, search and regex replacement, multiple buffers, nanorc configuration,
syntax highlighting, macros and translations. It is an experimental release.

## Downloads and installation

Choose `naro-0.1.0-x86_64-unknown-linux-gnu.tar.gz` for the default Linux x86_64
GNU/glibc build. The matching source is `naro-0.1.0-source.tar.gz`.
Download the seven release files together and run `sha256sum -c SHA256SUMS`.
Follow INSTALL.md inside the archive or repository for installation and removal.
The supplied installer requires Python 3.11 or newer. It does not replace nano
or change your shell profile.

The binary was built and qualified under Ubuntu 24.04/glibc 2.39. It uses a small
C bridge and dynamic native libraries including ncursesw, libc and libmagic.
See RUNTIME-REQUIREMENTS.md and build records for measured dependencies; these
results do not promise support for every Linux distribution. Tiny is available
as an optional source-build profile, not a binary download in this release.

## Qualification and known limits

Both frozen host and Ubuntu candidates completed the terminal corpus at the
retained 303 recorded / 301 full / 302 file-and-exit expectations, 38 CLI checks,
162 regex checks, 151 newer exact regressions and 19 guest-VT comparisons each.
The full technical collector passed 101 checks. Package verification covers
installation/removal, 41 catalogs, syntax, archive rejection and offline source
rebuilding. Save progress now appears before blocking writes and FIFO opens;
22 deterministic transient regressions and 10 save-safety regressions cover
progress, backup failures, prepend preservation, interruption, translated text
and narrow terminal layouts. The source
archive also contains the synchronized save test that avoids an earlier
intermittent snapshot failure, with its original cursor/file assertions intact.

Declared differences remain for invalid-regex recovery, NUL as a Yes response,
two external-tool signal-cleanup cases, and isolated-root no-home tilde recovery.
Six baseline cases are excluded and nine specification-to-test citations remain
unresolved. See COVERAGE_REVIEW.md and IMPLEMENTATION.md. These results are not
proof of exhaustive nano parity, a security audit or physical-keyboard coverage.

## Provenance and reporting

The executable's production revision is `b934b1fcefa74adcf631c39b20ecd133c70edc59`;
its SHA-256 is `9af710dbb614423b53425c093a41a95b4733cfd539bfe40047b1bdac0bd7419d`.
The corresponding-source archive's packaging/documentation revision is
`6473fe2043f8a7c3805e2994fea3f4f1bc8d4b50`, the proposed release tag target. Its tracked file
contents match that commit, including the synchronized save test and new progress
regressions. Production inputs match the frozen executable. Archive hashes are
listed in SHA256SUMS. Source rebuilding is verified; byte-for-byte binary
reproducibility is not claimed.

Report bugs at https://github.com/JLuethe/naro/issues with build identity, OS,
terminal, locale and a synthetic reproduction. For security bugs follow
SECURITY.md: open a public issue with a `Security:` title, omit confidential data,
and request private follow-up if needed.

NARO's project license is GPL-3.0-or-later. Reused files retain their original
terms and notices; LICENSE, NOTICE, CREDITS.md and source assets are included.
