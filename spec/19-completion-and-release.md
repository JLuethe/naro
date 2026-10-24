Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

# 19 — Compatibility completion, verification and release

Status: planned follow-up; requirements and tests below are not implemented or
executed by the act of writing this document. The original behavioral contract
in 00–18 remains authoritative for reference behavior. This document specifies
the next implementation and release work requested after the first working build.

## Scope, evidence and priorities

The frozen baseline is implementation revision `639ab573c67a15839fe2cda9fa52561c4bd99daf`,
reported in [validation](../validation/README.md): 303 fixture-safe terminal
scenarios, 301 full matches, 302 file/exit matches, 38 CLI matches, 162 regex
matches and six safety assertions. Those are historical results for that binary.
They do not verify the requirements or planned cases introduced here.

Deliver four workstreams in order: selection-aware spelling and formatter state;
editing/configuration/failure verification; environment coverage; installation
and release. Package layout work can proceed alongside verification. Tiny and
runtime credits are optional and are not prerequisites for the default release.

The original two reference differences remain intentional: Q-DEF-001 invalid-regex recovery
and Q-PROMPT-001 rejection of NUL as Yes. Retain their reference observations and
separate semantic assertions. Q-KEY-001 retains its existing safe-dispatch policy.
Do not weaken comparison rules to make a new case pass. Follow-up Q-TOOL-001
records a separate ownership improvement: handled HUP/TERM reaps the running
tool and removes its temp file, whereas the reference leaves that file. Keep
that field-level difference visible and assert clean candidate resources.

The [planned test matrix](data/follow-up-tests.csv) assigns test IDs, requirement
IDs, methods, oracles and gates. Every row starts as `planned`. Create executable
cases and collect evidence during implementation; do not add invented recordings
to `evidence/runs`. The specification audit reports baseline and planned counts
separately. All filesystem tests use private fixtures under doc 16's rules.

## 1. Selection-aware spelling and formatter state

Correction to the earlier work list: GNU nano formats the **whole buffer**, even
when text is marked. Selection-only processing applies to spelling. Source:
`src/text.c:2043–2591, 2957–2992`; [FEAT-SPELL/FORMAT](12-features.md).

### NEXT-SPELL-001 — Serialize precisely the spelling region

With a mark, pass only the selected byte range to both alternate and internal
spellers; without a mark, pass the whole buffer. Resolve forward/backward marks
to ordered byte endpoints while retaining their orientation for restoration.
Preserve the reference's line-ending, internal-NUL and final-newline rules;
reuse SPECIAL tool-file serialization rather than lossy string conversion.
For an alternate speller, an empty selection reports `Selection is empty`
and runs no child; an empty unmarked buffer reports `Buffer is empty`. The
internal pipeline still runs on empty input, as confirmed by the source and
TEST-NEXT-SPELL-002-INTERNAL. Preserve bytes outside the selection.

### NEXT-SPELL-002 — Replace and restore alternate-speller state

Retain the pinned command splitting, argv order, mtime comparison and exit-status
handling in FEAT-SPELL: statuses 1/2 complain but can still produce a correction;
status >2 or a signal stops replacement. An unchanged sec+nsec mtime yields
`Nothing changed`. Changed output replaces the selected region or whole buffer
with one `spelling correction` undo group. Preserve the shared cutbuffer and
unselected prefix/suffix. Restore the reference's mark orientation and adjusted
endpoints, cursor line/byte/EOL intent, preferred column and viewport behavior.
Match modified/saved-state effects through undo and redo, including replacement
text that changes the number of lines. Follow source behavior on read failures.

### NEXT-SPELL-003 — Confine internal spelling searches and replacements

Run the existing hunspell/spell → sort -f → uniq pipeline on the region file.
Search and Yes/No/All replacement must stay inside the selected region and track
its changing endpoint. Identical words before or after it are excluded. Restore
the original search pattern/options and cursor/mark state after completion,
cancel or tool failure. Keep nano's prompt prefilling and replacement undo
grouping; do not impose the alternate speller's grouping on this separate path.

### NEXT-TOOL-004 — Preserve formatter scope and mark-clearing order

Check restricted mode and formatter availability first. Once an eligible
formatter is selected, clear the mark before serializing the **whole buffer**,
including when later temp creation or invocation fails, as the source does.
Keep curses active, wipe child terminal output by refresh, and use the pinned
argument/status/mtime rules. Successful replacement has one `formatting` undo
group. Do not add selection-only formatting as a compatibility feature.

### NEXT-TOOL-005 — Own tool resources and failure restoration

Tool files have mode 0600, reference-compatible extension and bytes, and remain
inside each test's private TMPDIR. Remove them on ordinary success, no-change,
cancel and recoverable failure. Define explicit ownership through every return
path. Check restoration after handled signals; do not claim cleanup after
uncatchable SIGKILL. Preserve terminal modes, locks, unrelated buffers and
history according to the existing contracts. Test command splitting on literal
spaces: the reference does not provide shell quoting or general whitespace splitting.

Use fixture-owned tool stubs that log argv/input, produce deterministic output
and explicitly control mtime. Acceptance includes both selection orientations,
partial lines, Unicode/invalid bytes, changed line counts, empty selections,
undo/redo, no-change, cancellation and exit statuses. See TEST-NEXT-SPELL-001…006
and TEST-NEXT-TOOL-001…003 in the matrix.

## 2. Editing, configuration and failure verification

### NEXT-EDIT-001 — Exercise compound edits and saved points

Add reference-derived sequences combining hard-wrap boundaries, fill settings,
indentation/tabs, selection, cut/paste, undo/redo and save. Check bytes, cursor,
mark, history grouping and modified state after every meaningful transition.
Include edits exactly at the fill column, multiple blanks, unbreakable words,
the magic final line, and wrapping after a single-line paste. Keep reference
quirks already documented in 05/06; do not infer grouping from elapsed time.

### NEXT-RC-002 — Verify precedence and lazy syntax loading

Cover CLI versus rc overrides, rc lookup order, nested includes, quoted paths
containing spaces, glob ordering, syntax boundaries, extendsyntax and delayed
loading. Compare diagnostics, selected syntax, effective behavior and rendered
attributes, not just parser return values. Use bounded include graphs and
deterministic fixture content. An unexpected reference crash/hang becomes an
explicit decision-register issue before any proposed implementation deviation.

### NEXT-IO-003 — Inject write failures inside fixtures

Provide a controlled backend for ENOSPC, short writes, interrupted writes and
backup failures. A fixture-built fault shim or isolated size-limited filesystem
must affect only explicitly registered fixture-owned target files and test
processes; terminal descriptors and host paths are excluded. Run equivalent
fault schedules against reference and candidate where possible and record the
backend, injection point and actual syscall/error outcome. Trigger comparable
faults by target byte offset/condition rather than assuming equal syscall counts
between C and Rust implementations.

Check resulting partial bytes, diagnostics, exit behavior, permissions, link
relationships, backup and lock lifecycle. Nano rewrites in place: **do not add
atomic renaming or promise preservation beyond the reference contract**. FIFO
tests use fixture-created FIFOs and bounded fixture helper processes. A missing
fault backend is `blocked`, not a passing test or a silently skipped release gate.

### NEXT-RECOVER-004 — Verify signal and panic recovery

Exercise HUP/TERM, child interruption and controlled Rust panics with modified
named/nameless buffers and multiple buffers. Panic injection belongs in a
separate test-hooks build; production artifacts contain no active injection
interface. No native undefined behavior or real memory-corruption experiment is
required. Assert emergency-file bytes/mode/collision handling, lock cleanup and
raw-trace restoration of cursor, alternate screen, keypad, mouse and paste.
Use a fixture acknowledgment to choose injection time rather than a fragile sleep.
Keep forced SIGKILL recordings distinct from clean-exit/restoration evidence.

### NEXT-OBS-005 — Keep test results attributable and timing explicit

Every run identifies binary hash, source revision, build flags, environment,
scenario revision and oracle. Capture rows without tearing and wait for reaped
exit status. For transient messages, add explicit before/after phase checks;
do not change a message duration merely to fit a screenshot. Record failures,
timeouts, exclusions and deferred manual cases. Re-run affected cases and the
required regression corpus after fixes. Preserve the original reference files.

These are verification gaps until evidence identifies a code defect. Completion
means new reference/candidate comparisons agree or a reviewed, named deviation
has its own semantic assertions. Existing 301 baseline matches and both safety
cases must remain satisfied. See TEST-NEXT-EDIT/RC/IO/RECOVER/OBS in the matrix.

## 3. Environment and terminal coverage

### NEXT-ENV-001 — Certify environments individually

Record OS/architecture, libc and width behavior, ncurses/terminfo, tmux, locale
data, libmagic database identity, compiler/toolchain and linkage. Baseline is
ENV-BASE in doc 00. Require a second automated Linux environment for a general
Linux release claim. Existing Ubuntu CI build/smoke results are not a completed
full-corpus certification. Build the candidate and the pinned reference for
that environment before differential claims; separate build failures from
behavioral differences. Do not reuse host goldens as proof of a new libc's behavior.

### NEXT-I18N-002 — Separate catalog availability from behavior

Check that every shipped catalog (41 in the baseline) can be installed and
resolved in its gettext domain; derive the count from assets rather than
hardcoding a permanent target. This does not certify translation quality.
Expand behavioral cases in C/UTF-8 and representative German UTF-8/Latin-1,
Japanese UTF-8 and French UTF-8 locales, supplementing the eight existing i18n
cases. Check prompts, plural forms, answer letters, case/word rules, byte counts,
widths and combining/invalid-byte handling. Record unavailable locales explicitly.
Keep byte/internal assertions when UTF-8 tmux cannot faithfully display raw bytes.

### NEXT-TERM-003 — Add real-console and terminal evidence

Extend representative TERM/layout/resize/paste/modifier cases; name tested
emulators rather than claiming every terminal. Real Linux VT modifier/ioctl
paths require a real VT and a manual checklist: record console/keymap/TERM,
exact keys, resulting cursor/text and terminal restoration. Use copied fixtures.
Without suitable access, mark this conditional gate deferred and exclude real-VT
compatibility from release claims. It is not a prerequisite for a tmux-scoped preview.

### NEXT-PATH-004 — Rework excluded path cases without inventing equivalence

Review TEST-CLI-025/032/033/035 and TEST-BROWSE-003 individually. Replace absolute
host paths with fixture-owned equivalents only when path/type/confinement
semantics survive the substitution. Keep an original-to-replacement mapping and
capture new pinned-reference evidence. A regular file is not an equivalent to
`/dev/null`; a normal directory is not an equivalent to filesystem root. Such
cases remain deferred unless an isolated fixture-root environment can preserve
the behavior without accessing host paths. Never count a redesigned test as an
execution of the unchanged excluded scenario. Tiny TEST-KEY-007 remains optional.

## 4. Installation and release

### NEXT-DIST-001 — State the supported binary envelope

Initial distribution target is Linux x86_64/glibc, dynamically linked to the
verified ncursesw/libmagic runtime libraries. Build artifacts on the oldest
declared supported runtime and inspect required library/symbol versions. Publish
only measured compatibility limits; a binary built on the current glibc 2.44
host is not automatically portable to older distributions. Keep macOS, Windows,
other architectures and a static build outside this initial release scope.

### NEXT-ASSET-002 — Install assets independently of the checkout

Use `<prefix>/bin/naro`, `<prefix>/share/naro/locale`,
`<prefix>/share/naro/syntax`, and `<prefix>/share/doc/naro`. Keep the gettext
domain/file names required by the reused catalogs (`nano.mo`). Locale resolution
order is explicit `NARO_LOCALEDIR`, installed assets relative to the resolved
executable/prefix, then a development-checkout fallback. Test symlinked launchers
and prefixes with spaces. An explicit override is authoritative. Invalid or missing catalogs fall back to
untranslated messages without trying a lower-priority directory or preventing
editing.

Install syntax files and an example nanorc include; do not silently activate new
syntax or overwrite user configuration. Preserve the existing nano-compatible
configuration lookup contract. Installed operation must work with the build
checkout unavailable, including translated output and an explicit syntax include.

### NEXT-PKG-003 — Produce inspectable release artifacts

Provide a versioned archive, matching source archive, checksums and a manifest
identifying source revision, compiler, target, build features, runtime dependencies
and packaged files. Include LICENSE, NOTICE, retained per-file notices and the
PO/syntax sources already shipped in the repository. Audit the actual files and
license inventory rather than labeling every asset with one blanket license.
Keep product/release version and pinned reference version distinct. Preserve the
current compatibility CLI output unless a separately recorded extension changes it.

### NEXT-INSTALL-004 — Make installation reversible and testable

Support a user-selected prefix with a user-level default; installation requires
no shell-profile or user-config edits. Test installation/removal only in fresh
fixture-owned prefixes. Track installed files in a manifest. Removal leaves
unrelated files and modified/conflicting files intact and reports conflicts;
never recursively delete an arbitrary prefix. Reject archive path traversal and
escaping symlinks. Test a clean staged environment without repository paths.

### NEXT-RELEASE-005 — Gate a preview release on evidence

Require formatting, strict Clippy, meaningful Rust tests, comparator/harness
regressions, the safe default terminal corpus, CLI/regex corpora, safety assertions
and required new matrix cases. All artifacts identify their exact binary/build.
Regular CI may run a focused subset; a release-candidate run must cover the full
required scope. Publish a compatibility table listing matches, intentional
deviations, exclusions and deferred environments. Newly proposed tests are never
listed as passed based on the historical baseline. Creating a tag or publishing
a release is a later explicit action, not part of this specification-writing task.

### NEXT-UX-006 — Exercise the installed editor by hand

Use copied sample files for open/edit/save/reopen, unsaved exit/cancel, undo/redo,
selection and spelling, formatter errors, bracketed paste, resize, multibuffer,
translated prompts and normal/error terminal restoration. Include deterministic
1 MiB and 10 MiB fixtures; record load/action timings without inventing unmeasured
performance promises. Check that all output bytes and line endings are preserved
as the reference specifies. Record the tested terminal and any issues separately
from automated conformance. This gate does not replace differential tests.

## Optional tiny build and credits proposal

### NEXT-TINY-001 — Keep tiny optional and define it by the pinned profile

Tiny is a compile-time reduced-feature editor, intended to reduce size and
dependencies. The pinned default tiny profile retains basic editing, file I/O,
search and UTF-8/NLS; it omits undo, marks/selections, softwrap and numerous
commands, plus nanorc, syntax colors, help viewer, browser, histories, multiple
buffers, mouse, spell/lint/format tools and hard wrapping. Exact availability
comes from [build-features.csv](data/build-features.csv) and the tiny binding
tables, not this abbreviated list. Some upstream configure features can be
explicitly re-enabled; that is a different profile.

A future Cargo `tiny` feature/build should exclude code and unused native
dependencies, not merely hide commands. Match tiny options, diagnostics, help,
bindings and editing behavior against the pinned tiny executable. Measure size
with the same Rust toolchain, target and release settings as the full build;
publish measured bytes/dependencies, with no invented reduction percentage.
Default-profile release readiness does not depend on implementing tiny.

### NEXT-CREDITS-001 — Start with static credits and preserve compatibility

Recommended first delivery is the readable [CREDITS.md](../CREDITS.md), installed
with documentation. Credit the project, GNU nano/FSF and contributors for the
reference and reused data, the native libraries, translation/syntax contributors,
and Codex-assisted development. Preserve specific notices in NOTICE/assets; do
not invent contributor names or imply upstream endorsement.

Proposed later runtime presentation: an optional `naro --credits` prints the same
plain-text content to stdout and exits zero, with no network calls, terminal-mode
changes, buffer/file writes, prompts or animation. It is a product CLI extension,
not GNU nano parity. A proposed Cargo `credits` feature is default-off. Enable the command only in
an explicitly selected product build, recorded in the deviation register with
its CLI tests. No existing keys,
help text, `--help`/`--version` output or save filenames change as part of this
documentation proposal. The nano `zzy` scrolling Easter egg remains optional;
do not intercept a user's save filename to implement Naro's credits.

## Milestones and evidence handoff

1. M1: spelling/formatter requirements and their differential cases pass.
2. M2: required editing/rc/failure cases pass, including a documented fault backend.
3. M3: baseline and second Linux certifications are recorded; conditional VT/path
   gaps are named with reasons and excluded claims.
4. M4: staged install, archive, clean-environment tests and manual checklist pass;
   publishable preview artifacts and compatibility notes are ready for review.

For each milestone update the matrix status with evidence paths and the tested
revision/hash, then rerun the required regression gate. Use `planned`, `recorded`,
`verified`, `blocked` or `deferred` precisely; only verified cases satisfy a gate.
New observations belong under a separate follow-up evidence directory. Mirror
finished spec changes back to `~/src/nano-rs/spec`, with this repository canonical.
