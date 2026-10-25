Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

# 22 — Optional tiny build

Status: implementation in progress. This phase activates the optional tiny
requirement in doc 19. The frozen default preview and its evidence remain
historical; new shared-code changes require their own default regression.

### TINY-PROFILE-001 — Compile a reduced editor

`cargo build --release --features tiny` selects the pinned P-TINY contract.
UTF-8, gettext, byte-preserving editing, file I/O, search/replace and restricted
mode remain. Exclude full-profile key tables, undo storage, nanorc/syntax loading,
help viewer, browser, histories, multibuffer command handling, mouse and external
tool implementations. Do not link libmagic or require its header for tiny.
No runtime switch changes a full executable into tiny. Default build behavior
and the existing opt-in credits/test-hooks feature contracts remain separate.

### TINY-CLI-002 — Match tiny startup

Use the tiny long-option table and retained short handlers, preserving GNU
getopt diagnostics. The short optstring is unchanged: disabled short options
reach the terse usage message while disabled long names are unrecognized.
Match help/version, restricted invocation, multiple operands, +LINE[,COLUMN],
unsupported startup searches and literal `-` filenames against the pinned tiny
binary. Ignore nanorc files and state paths. Record all tests in private fixtures.

### TINY-EDIT-003 — Preserve the retained editing contract

Use extracted tiny bindings and footer tables, including modern bindings and
byte/UTF-8 profiles. Test insert/delete, cut/copy/paste, navigation, prompts,
search/replace/regex, goto, write/insert, cancellation, view/restricted modes,
line endings, invalid bytes and magic newline behavior. Undo, marks and excluded
commands must not become reachable through keys; unsupported keys follow tiny
diagnostics. No undo snapshots are retained during ordinary tiny edits.

### TINY-TERM-004 — Match tiny input and terminal lifecycle

Tiny does not request bracketed paste. Retain only its escape/terminfo/VT
modifier mappings and no physical selection acquisition. Match basic rendering,
nohelp/constant position, normal exit, handled termination and copied-fixture
emergency saves. Separate modeled ioctl tests from actual guest VT observations;
physical operator certification remains deferred.

### TINY-GATE-005 — Validate and measure without weakening full mode

Fresh tiny reference/candidate comparisons must identify exact source, binary,
scenario and environment hashes. Add CLI and retained-function terminal suites;
every mismatch needs a fix or an explicit decision, never broad normalization.
Use separate target directories for full and tiny. Run formatting, strict Clippy,
unit/harness checks and the default 303-case corpus/CLI/regex/safety after shared
changes. Compare stripped sizes and linked libraries using the same compiler,
target and optimization settings. Report actual bytes; require no libmagic
dependency, no promise of a predetermined percentage. Package only a profile
whose feature metadata agrees with the executable. Preserve prior artifacts.

Acceptance is recorded in `data/tiny-tests.csv`. Tiny support is limited to the
tested pinned profile, not arbitrary upstream configure feature combinations.
The phase does not publish a release or claim physical-keyboard certification.

## Observed tiny distinctions

Fresh fixtures confirm that multiple file operands terminate with “Can open
just one file”, `-` is a literal filename, CR bytes are not converted, and
startup search syntax is treated as an invalid line/column. Empty startup has
no help welcome message. Ordinary search has no spotlight; replacement still
highlights its question target. Restricted help omits the `-R` description.

Tiny's raw escape parser consumes fewer bytes for unsupported sequences. In
particular, `ESC [ 200~` / `201~` are not paste delimiters; the trailing bytes
remain input. These are recorded as exact bytes/screens, not normalized away.
Ctrl terminfo/VT mappings remain, while several raw modified-key sequences do
not. Eight separate ptrace ioctl models cover the modeled VT branch.

At a Write prompt, Tab dispatches the buffer's tab-insertion operation because
upstream tiny lacks TABCOMP's prompt handler. The filename answer is then
submitted, potentially opening a different-name confirmation. That question
retains the old edit-area display until refresh. At Search, Tab changes the
buffer and leaves the prompt without searching. This observed source behavior
is reproduced in `TEST-TINY-WRITE-TAB-DISPATCH` and `TEST-TINY-PROMPT-TAB`;
these tests operate only on disposable fixture files.
