# Implementation and qualification status

NARO 0.1.0 is an experimental independent port of GNU nano 9.3. The pinned
reference is `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.
Technical qualification and independent review are complete; publication is not
authorized.

## Candidate identity

Production commit: `b934b1fcefa74adcf631c39b20ecd133c70edc59`.
Production-source SHA-256:
`3ce5c0ee2d62983b32c1d71664c3404c799ff8fc08c16f6bfdb0b90d2acc21bd`.

| Role | Executable SHA-256 |
| --- | --- |
| Primary Ubuntu default candidate | `9af710dbb614423b53425c093a41a95b4733cfd539bfe40047b1bdac0bd7419d` |
| Host qualification candidate | `5767ed4938e25b0b49c0a9c546959a88260a9e2cbffb6dd472fe160c4ea666a7` |

Both report default/empty features and version 0.1.0. Later documentation commits
are distinct from this compiled source. [The validation index](validation/README.md)
links the current reports; older reports retain their original identities.

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

## Current qualification

| Area | Recorded result |
| --- | --- |
| Terminal corpus, each environment | 303 recorded; 301 full and 302 file/exit matches; six exclusions |
| CLI / regex, each environment | 38 / 162 pass |
| Historical follow-ups, each environment | 53 cases, 51 exact; two accepted signal cleanup differences |
| Additional regressions, each environment | wrap 58, filter 6, release-fixes 15, step3-gaps 40, save-progress 22, save-safety 10: all 151 exact |
| Isolated root/home, host only | 27 exact plus a separately asserted no-home deviation |
| Guest Linux VT, each candidate | 19 exact comparisons, with terminal/keyboard/meta restoration |
| Ioctl models, each candidate | Eight exact comparisons; distinct from guest-VT testing |
| Private VM transport | Six checks pass |
| Recovery and large files | Separate panic instrumentation, write/signal cases, 1 MiB/10 MiB checks pass |
| Ubuntu package | 15 checks; offline source rebuild; 41 catalogs and 44 asset checks pass |
| Final-archive ordinary-prefix install | Five checks pass on the exact final archive |
| Complete technical collector | 101/101 checks pass |

Ubuntu used its own built reference executable and fresh observations. The host
and Ubuntu results do not substitute for one another. Guest-VT testing used the
Ubuntu reference in the recorded guest userspace, kernel and keymap with emulated
PS/2 input. It is not physical keyboard/operator certification.

## Declared differences and limits

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
belongs to the binaries named there; it does not certify a new 0.1.0 tiny download.

Optional credits and recovery test-hooks are separate features. Neither is
included in the primary candidate. Follow-up, root, console and closure reports
predating the dated step 5–7 records are historical. Their counts, sizes and
executable hashes must not be presented as measurements of this candidate.

CI checks selected build, unit, terminal and packaging behavior. Full local
host/Ubuntu/VM qualification is separate; a green CI job alone is not the
101-check release gate. Testing never publishes a release automatically.
