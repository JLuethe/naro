# Implementation and qualification status

NARO 0.1.2 is an experimental independent port of GNU nano 9.3. The pinned
reference is `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.
The safe-save changes have scoped deterministic Linux validation; the historical
qualification below does not transfer to the current artifacts.
See [GitHub Releases](https://github.com/JLuethe/naro/releases) for published packages.

## Package identity

For an exact packaged artifact, use its `manifest.json` and accompanying
`build.json` and `SHA256SUMS`. They record the compiled revision, production-source
fingerprint, features, executable hash, documentation/source revision and archive
hashes. `NARO_BUILD_INFO=1 /path/to/naro` reports the compiled build identity.

This status document does not pin one executable or its own containing commit.
Documentation repackaging changes archive hashes even when the qualified
executable is retained. [The validation index](validation/README.md) links the
source-bound reports; each report applies only to its named inputs and scope.

## Architecture and implemented behavior

The editor uses byte-vector buffers, transactional undo, a Rust state machine
and cell renderer, generated binding/help data, and a small native C bridge.
Native services include ncursesw, libc locale/POSIX regex/getopt and libmagic.
GNU nano itself is not invoked at runtime. There are no Cargo package dependencies.

Implemented areas include byte-preserving editing, UTF-8 and byte-locale
handling, hard and soft wrapping, undo/redo, selections, search/replace, backups
and locks, multiple buffers, nanorc, syntax, browser, histories, macros, mouse
input, external tools and translations. Implementation is broader than the
finite tested matrix; it is not a claim of exhaustive compatibility.

## Current qualification scope

The [safe-save qualification](validation/daybreak-0.1.2-2026-11-06/README.md)
records fresh host/Ubuntu fault, backup, recovery, terminal and package checks.
Regular-file saving now uses atomic replacement, with the explicit compatibility
policy below. These finite tests do not establish physical power-loss behavior
or adversarial namespace-race safety (issue #12). Nine runtime citation gaps
remain (issue #14); guest-VT, additional architecture/Miri and broader native
library qualification remain outside this retest (issue #15). No unqualified
security, all-platform or release-publication claim follows from these results.

## Historical 0.1.1 qualification

The counts below belong to the exact default-profile artifacts identified in
[the historical final receipts](validation/release-0.1.1-final-2026-10-31/README.md).
They are not measurements of the current version or its packages.

| Area | Recorded result |
| --- | --- |
| Terminal corpus, each environment | 303 accepted: 26 raw, 275 identity-reviewed, two declared; 302 file/exit matches; six exclusions |
| CLI / regex, each environment | 38 / 162 pass |
| Historical follow-ups, each environment | 53 accepted, including two declared signal-cleanup differences |
| Additional regressions, each environment | wrap 58, filter 6, release-fixes 15, step3-gaps 40, save-progress 22, save-safety 10: all 151 accepted; raw/identity counts separate |
| Isolated root/home, host only | 27 accepted plus a separately asserted no-home deviation |
| Guest Linux VT, each candidate | 19 accepted: one raw, 18 identity-reviewed, with terminal/keyboard/meta restoration |
| Ioctl models, each candidate | Eight accepted comparisons; distinct from guest-VT testing |
| Private VM transport | Six checks pass |
| Recovery and large files | Separate panic instrumentation, write/signal cases, 1 MiB/10 MiB checks pass |
| Ubuntu package | 15 checks; offline source rebuild; 41 catalogs and 44 asset checks pass |
| Complete technical collector | 69/69 checks pass |

Ubuntu used its own built reference executable and fresh observations. The host
and Ubuntu results do not substitute for one another. Guest-VT testing used the
Ubuntu reference in the recorded guest userspace, kernel and keymap with emulated
PS/2 input. It is not physical keyboard/operator certification.

## Declared differences and limits

- Regular-file saving uses same-directory atomic replacement by default.
  [Safe-save compatibility](docs/safe-save.md) defines durability errors,
  metadata, links, append/prepend and interruption behavior. Nano's in-place
  inode and hard-link behavior is intentionally not retained.

- `Q-IDENTITY-001`: NARO name/version in titles, welcome and CLI identity; complete
  layout and all non-identity behavior remain checked.

- `TEST-CLI-057` / `Q-DEF-001`: established invalid-regex recovery difference.
- `TEST-PROMPT-NUL-001` / `Q-PROMPT-001`: NUL is rejected as a Yes response.
- `Q-TOOL-001`: the two bounded HUP/TERM external-tool cleanup differences.
- `Q-ROOT-NOHOME-001`: asserted isolated-root no-home tilde recovery behavior.

The six excluded baseline cases are TEST-BROWSE-003, TEST-CLI-025/032/033/035
and TEST-KEY-007. They are exclusions, not passes. Existing normalization and
field-level exception policies are documented in the evidence; new unexplained
mismatches block qualification.

Nine specification citations remain unresolved by the recorded-scenario audit.
[The coverage review](COVERAGE_REVIEW.md) distinguishes historical probe/table
observations from missing scenario IDs. A structurally passing audit does not
mean all requirements have runtime coverage.

Other architectures/OSes, static binaries, broad native-root certification,
physical keyboard trials, exhaustive locale/tool combinations and a security
audit are not established by these results. The portable binary's support is
bounded by its measured native runtime. See [INSTALL.md](INSTALL.md).

## Optional profiles and historical evidence

Tiny remains a source-build profile. It retains basic editing, UTF-8,
search/replace, POSIX regex and translations, while omitting undo/redo,
selections, nanorc/syntax, help, browser, multiple buffers, histories, mouse and
external tools. It uses ncursesw without libmagic. Its [earlier qualification](validation/tiny/README.md)
belongs to the binaries named there; it does not certify a current tiny download.

Optional credits and recovery test-hooks are separate features. Neither is
included in the default production profile. Follow-up, root, console and closure reports
predating the dated step 5–7 records are historical. Their counts, sizes and
executable hashes must not be presented as measurements of a later candidate.

CI checks selected build, unit, terminal and packaging behavior. Full local
host/Ubuntu/VM qualification is separate; a green CI job alone is not the
69-check release gate. Testing never publishes a release automatically.
