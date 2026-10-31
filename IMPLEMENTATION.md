# Implementation and qualification status

NARO 0.1.0 is an experimental independent port of GNU nano 9.3. The pinned
reference is `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.
Technical candidate qualification is complete; final publication review is not.

## Candidate identity

Production commit: `16f6398968adc1f815055a4413cf0465aed28126`.
Production-source SHA-256:
`0786e7d32514c2eea5bf55e56164462a412e11dc39276acaf3baba458a08492c`.

| Role | Executable SHA-256 |
| --- | --- |
| Primary Ubuntu default candidate | `b95bb4f9984f8e321fbd69e2a4e3058c7f184d6b35a8ae7650f6f5b7897f90bf` |
| Host qualification candidate | `4a97874ca06d2e3093f81769c5e0989554a5c87cf8f95ef7d43d9074102c0d7d` |

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
| Additional regressions, each environment | wrap 58, filter 6, release-fixes 15, step3-gaps 40, save-progress 13: all 132 exact |
| Isolated root/home, host only | 27 exact plus a separately asserted no-home deviation |
| Guest Linux VT, each candidate | 19 exact comparisons, with terminal/keyboard/meta restoration |
| Ioctl models, each candidate | Eight exact comparisons; distinct from guest-VT testing |
| Private VM transport | Six checks pass |
| Recovery and large files | Separate panic instrumentation, write/signal cases, 1 MiB/10 MiB checks pass |
| Ubuntu package | 15 checks; offline source rebuild; 41 catalogs and 44 asset checks pass |
| Additional ordinary-prefix install | Five checks pass |
| Complete technical collector | 99/99 checks pass |

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
99-check release gate. Testing never publishes a release automatically.
