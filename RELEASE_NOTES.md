# NARO 0.1.3 development candidate notes

NARO 0.1.3 is a local development candidate. It is not a published release or
an assertion that integrated qualification has passed. The source now includes
private safe-save staging for attacker-writable destination directories,
additional bounded confinement, runtime coverage and resource/hostile-input
checks, and a private locale fixture for exact differential retesting. The
new version string changes the NARO title and CLI identity assertions; their
version-bound expectations are reviewed separately from original GNU nano
recordings. Results for earlier binaries do not qualify a 0.1.3 build.

## Historical 0.1.2 development candidate notes

NARO 0.1.2 is a local development candidate. Its safety and release-readiness
changes are still undergoing integrated qualification; no 0.1.2 archive, tag,
or release is asserted here. Default and tiny builds now provide `naro --credits`
with the same GNU nano 9.3 port attribution as `CREDITS.md`. The Cargo `credits`
feature remains accepted for existing build commands. The 0.1.1 notes below
describe their own qualified artifacts and are retained as historical results.

## Historical 0.1.1 release notes

NARO 0.1.1 is the product-identity update to the experimental Linux x86_64 release.
The editing title, version, usage and help identify NARO. NARO is an independent
Rust port of GNU nano 9.3, not an official GNU nano release.

## Changes since 0.1.0

- Editing headers show NARO's name and 0.1.1 version, including narrow layouts.
- CLI version, usage/help and welcome identity use NARO wording.
- Qualification distinguishes raw equality from the reviewed NARO identity
  difference. Original GNU observations stay unchanged; complete title layout,
  filename/state, cell attributes, cursor and non-identity text remain checked.
- Portable qualification provides exact frozen syntax assets, scoped tmux cleanup,
  retained executable inputs and explicit package/compiler/locale prerequisites.

The inherited save-progress, paste/wrap, navigation, undo/redo, file-safety and
rcfile fixes from 0.1.0 remain in the tested production source.

## Qualified inputs and results

Frozen source revision: `accc766af9ff7e36ec206dea697410e3f8f31674`.
Production fingerprint: `63936243e73d0a3fb536d3c0a0fb0e6fe57be09da5f5bc0387ee10250b3d7093`.
Primary Ubuntu executable SHA-256: `70ab6932323a6b679e628bdb6cfddead8a6ff50160d741782ae8649664dc5a00`.
Use `naro-0.1.1-x86_64-unknown-linux-gnu.tar.gz` and corresponding
`naro-0.1.1-source.tar.gz`, with their final accompanying SHA256SUMS.
Documentation repackaging changes archive hashes without rebuilding this executable.

The full host matrix passed all 46 stages; Ubuntu passed all 32. Each environment
uses its own nano reference and fresh 303-case observations. Each terminal set
accepted 26 raw-exact, 275 identity-reviewed and two declared differences, with
302 file/exit matches and six fixed exclusions. CLI 38, regex 162, safety 2,
historical suites, all 151 newer regression cases, installed assets and large-file
checks passed. Both genuine guest VT groups accepted 19 cases, and transport
passed six checks. The collector passed 69 checks. Independent gate recomputation
found no problems or unexpected results across 38 accounting sets.

Package checks cover installation in ordinary/spaced paths, symlink launching,
41 catalogs, syntax, offline source rebuilding, malformed archives and safe
uninstall. Corresponding source matches production inputs/features; byte-for-byte
binary reproducibility is not claimed. Exact receipts are in
[0.1.1 validation](validation/release-0.1.1-final-2026-10-31/README.md).

## Known differences and scope

NARO identity is intentional. Other retained declared differences concern
invalid-regex recovery, rejecting NUL as Yes, two external-tool signal-cleanup
cases and isolated-root no-home tilde recovery. Six corpus cases are excluded;
nine audit citations remain unresolved in [COVERAGE_REVIEW.md](COVERAGE_REVIEW.md).
Optional tiny builds and physical keyboard/operator console certification retain
their separate scope. Other architectures/OSes, broad fuzzing and a security audit
are not established by these results. This is a GNU/glibc build with a native C
bridge, ncursesw and libmagic; see [INSTALL.md](INSTALL.md).

## Attribution and reports

John Luethe develops NARO. Thank you to OpenAI for their generous support.
GNU nano contributors and the Free Software Foundation supplied reference behavior
and reused data/assets. See [LICENSE](LICENSE), [NOTICE](NOTICE) and [CREDITS.md](CREDITS.md).
Report bugs through [GitHub issues](https://github.com/JLuethe/naro/issues), including
build identity and a synthetic reproduction; follow [SECURITY.md](SECURITY.md) for
security reports. Publication and community announcements require separate approval.
