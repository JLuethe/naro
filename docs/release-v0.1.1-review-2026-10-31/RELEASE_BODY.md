NARO 0.1.1 is the experimental Linux x86_64 identity update: the editing header,
CLI version, usage, help and welcome identify NARO. NARO is an independent Rust
port of GNU nano 9.3, developed by John Luethe. Thank you to OpenAI for their
generous support, and to GNU nano contributors and the Free Software Foundation.

## Downloads

Use `naro-0.1.1-x86_64-unknown-linux-gnu.tar.gz` for the default GNU/glibc build,
with corresponding `naro-0.1.1-source.tar.gz`. Download the seven release files
and verify `sha256sum -c SHA256SUMS`. INSTALL.md inside the archive explains native
dependencies, Python 3.11+ installation and safe removal. The editor needs no Rust
at runtime and does not replace the system nano or modify shell configuration.

The primary binary was built and tested under Ubuntu 24.04/glibc 2.39, with
ncursesw/tinfo and libmagic. See RUNTIME-REQUIREMENTS.md and build records for
measured linkage and symbol requirements. Tiny remains source-build only.

## Qualification and scope

Fresh host qualification passed all 46 stages; Ubuntu passed 32. Each environment
used its own nano reference and 303 observations. Terminal results per environment:
26 raw exact, 275 identity-reviewed, two declared differences, 302 file/exit matches
and six fixed exclusions. Raw and reviewed counts are separate. CLI 38, regex 162,
safety 2, historical follow-ups and 151 newer regressions passed. Both genuine
Linux guest-VT groups accepted 19 cases and transport passed six checks.
The 69-check collector and independent raw-evidence gate recomputations passed,
with zero unexpected differences across 38 accounting sets.

The selected documentation-refreshed archives passed package 15/15, ordinary-prefix
5/5 and 41 catalogs/44 asset checks. Corresponding source builds offline with
--locked and matches production inputs/features. Binary reproducibility is not
claimed. The executable is the exact qualified default binary with no test hooks.

NARO identity is intentional. Retained declared differences cover invalid-regex
recovery, NUL as Yes, two external-tool signal cleanup cases and isolated-root
no-home tilde recovery. Nine audit citations remain unresolved; see
COVERAGE_REVIEW.md. This is not a security audit, physical-keyboard certification
or certification of every Linux distribution, architecture or external tool.

## Provenance and reporting

Compiled source: `accc766af9ff7e36ec206dea697410e3f8f31674`.
Executable SHA-256: `70ab6932323a6b679e628bdb6cfddead8a6ff50160d741782ae8649664dc5a00`.
Corresponding-source/documentation and tag commit:
`a6078aed705bc0b605ad7603505767ce2b9bc206`. Production and verification
fingerprints match the frozen tested source. Documentation packaging changes the
archive hashes; use this release's SHA256SUMS and QUALIFICATION.json.

Report bugs at https://github.com/JLuethe/naro/issues with build identity, OS,
terminal, locale and a synthetic reproduction. Follow SECURITY.md for security
reports. NARO is GPL-3.0-or-later; reused files retain their original notices.
