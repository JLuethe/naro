Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

# GNU nano behavioral specification and Naro implementation plan

This specification describes GNU nano at the exact commit above, primarily the
unmodified default build on Linux/glibc/ncursesw. It supplies source-derived
requirements, machine-readable inventories and replayable terminal evidence for
a GPL-3.0 Rust reimplementation, Naro. Read [00-reference-environment.md](00-reference-environment.md)
for build hashes, paths, versions, locale/terminal envelope and limitations.

Observed/source behavior takes precedence over man-page descriptions where they
differ. Requirements are grouped by stable IDs. “Source” identifies the pinned
C tree and lines; “runtime” identifies saved observations. “Planned” tests are
not observations. The docs cover all major functional areas; they do not claim
exhaustive branch coverage or successful implementation.

| Document | Contract |
|---|---|
| [01](01-cli.md) | Invocation, options, startup, environment, diagnostics |
| [02](02-keybindings.md), [tables](02-keybindings-tables.md) | Dispatch, profiles, rebinding, functions, help lines |
| [03](03-terminal-input.md) | Bytes, bursts, escapes, paste, mouse, verbatim |
| [04](04-rendering.md) | Cells, layout, colors, scrolling, resize, status |
| [05](05-buffer-and-editing.md) | Buffer, mark, cut/copy/paste, edits, movement |
| [06](06-undo-redo.md) | Transactions, grouping, saved point, messages |
| [07](07-search-replace.md) | Search progression, replacement, regex, brackets |
| [08](08-files.md) | Open/read/write, metadata, backups, locks, buffers |
| [09](09-file-browser.md) | Browser layout, sorting, navigation and selection |
| [10](10-nanorc.md) | Rc lookup, grammar, options, colors, includes |
| [11](11-syntax-highlighting.md) | Syntax selection/rules and shared POSIX regex contract |
| [12](12-features.md) | Justify, tools, macros, history, help, restricted mode |
| [13](13-signals-and-terminal.md) | Terminal lifecycle, signals, emergency saves |
| [14](14-messages-and-i18n.md) | Message catalog, translations, charset, plurals |
| [15](15-rust-architecture.md) | Rust module/state design and native boundaries |
| [16](16-test-plan.md) | Replay, comparison, normalization, fixture safety |
| [17](17-prompts-and-completion.md) | Answer editing, history and completion |
| [18](18-bytes-encoding-and-coordinates.md) | Invalid bytes, NUL, widths, positions, classification |
| [19](19-completion-and-release.md) | Follow-up: tool selections, edge cases, environment certification, packaging; optional tiny/credits proposal |
| [20](20-root-and-console.md) | Effective-home resolution, isolated root/device checks, and physical-console protocol |
| [97](97-coverage.md) | Evidence coverage and explicit verification gaps |
| [98](98-progress.md) | Work state and reproducible resume instructions |
| [99](99-open-questions.md) | Decisions, defects and deliberate deviations |

Data schemas and regeneration commands are in [data/README.md](data/README.md).
Original observations are under `evidence/runs`, `evidence/cli`, `evidence/regex`
and `evidence/tables`; scenarios under `evidence/scenarios`. Keep them separate
from candidate runs. Tools are standard-library Python except the native regex
probe and gdb table extractor. The clean reference tree is never modified.

Target deviations are narrowly recorded in 99: fix invalid startup regex
crashes, reject NUL as Yes, and tolerate inapplicable string-bound functions
without crashing. Reproduce deterministic harmless quirks, including Latin-1
word classification and the magic-line undo behavior. Optional tiny/credits
are distinguished from default-profile requirements.

For resuming: read this page, 00-reference-environment, 98, 97 and 99, then the
relevant requirements and scenario evidence. Implementation status and build
results belong in the repository's README/status report, separate from the
behavioral contract.

Document 19 and `data/follow-up-tests.csv` track the implemented follow-up phase
with separate audit counts and evidence-linked statuses. See
[follow-up validation](../validation/follow-up/README.md) for the tested builds;
physical VT checks and optional tiny remain deferred. Doc 20 adds verified
namespace-root cases and a console readiness/operator protocol. The original
248 requirements and baseline observations remain separate historical evidence.
