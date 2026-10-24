Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

# 20 — Root home resolution, isolated paths and Linux console verification

Status: specified; implementation and new evidence are tracked in
[data/root-console-tests.csv](data/root-console-tests.csv). This phase addresses
steps 1 and 2 of the next-work list. Historical doc 19 results remain unchanged.

## Scope and sources

Implement the root-home difference Q-ENV-ROOT-001 and safely replace deferred
path checks with fresh observations inside a namespace-owned filesystem root.
Build a console capability check and a reproducible operator protocol. Physical
VT behavior remains conditional on a real console; a PTY with TERM=linux does
not establish it. No host root account, passwd file, device or active console
is modified. The clean pinned tree remains read-only.

Sources: `src/utils.c:31–51`, `src/rcfile.c:1710–1747`,
`src/history.c:200–255`, `src/files.c:1635–1710,2290–2330`,
`src/nano.c:1842–1848,2682–2690`, `src/winio.c:1198–1264`.

### ROOT-HOME-001 — Resolve and cache the effective home precisely

For non-root effective uid, a set HOME wins, including an empty value. When
HOME is unset, or effective uid is zero, try getpwuid(effective uid). A found
entry replaces HOME even when pw_dir is empty. When lookup fails, retain HOME.
Only a nonempty result becomes the cached home. Missing/empty results mean no
home; do not substitute the current directory. Preserve pathname bytes. Once
selected, reuse the cached home during that editor process, as the reference
does. Do not rewrite HOME, XDG variables, uid, passwd or environment globally.

Acceptance covers uid 0 and non-root, HOME set/unset/empty, passwd found/missing/
empty, differing HOME/passwd directories, and cache stability after fixture NSS
input changes. Use genuine namespace uids and fixture passwd data for primary
evidence; a test-only NSS shim may supplement rare lookup failures but must be
identified as such.

### ROOT-CONSUMERS-002 — Share resolution across existing consumers

Configuration lookup, bare-user tilde prefixes (`~/...`), history/position
storage and backup fallback use the same resolved home. Named-user tilde lookup
continues to consult that user's passwd entry separately. A standalone `~`
remains literal, matching expand_leading_tilde(). Explicit rc paths and XDG
precedence remain governed by docs 01/10/12. With no resolved home, skip home
paths rather than reading cwd/.nanorc or creating cwd/.local; XDG can still
provide a path. Match the reference diagnostic when neither home nor XDG exists.
If a no-home tilde operation crashes the reference, record a separate decision
before defining safe target behavior; do not reproduce memory faults.

### ROOT-STATE-003 — Preserve file and failure behavior

Assert which home receives history/position/backup files and which decoy home
remains untouched. Preserve exact saved bytes, modes and link relationships.
Backup failure uses the already documented fixture-inode fault schedule; only
new random backup filename tokens may receive a separately documented, scoped
normalization. Root home resolution must not change normal-user save behavior,
user-name completion, locks or emergency-save naming.

### ROOT-ISOLATE-004 — Confine root tests to a private namespace

Every root/path test uses a disposable harness fixture. A bubblewrap backend
creates user, mount, PID, IPC, UTS and network namespaces, maps the launching
user to the requested namespace uid, mounts only explicit read-only runtime
inputs, and exposes a fixture-owned passwd/group/NSS configuration. Host homes,
/etc, /root, /proc and device directories are not mounted as test data. Read-only
runtime libraries/binaries are dependencies, never editing targets. Root is
read-only except the fixture and private runtime pseudo-filesystems. Use a
private /dev with an actual null character device (major 1, minor 3), not the
host /dev/null or a regular-file substitute. Record effective uid, account home,
namespace root, device identity, backend identity and binary/scenario hashes.

Fail closed if setup/capability checks fail; no fallback to unisolated execution.
Bound child lifetime with the existing harness. Refuse unsafe fixture roots,
symlink roots and unsupported namespace identities. A missing backend is a
blocked automated gate, never a passing or silently skipped result.

### ROOT-PATH-005 — Re-record the two deferred filesystem semantics

Run fresh counterparts of TEST-CLI-025 and TEST-BROWSE-003 against the pinned
reference and candidate inside identical isolated roots. Verify /dev/null is a
character device and root browsing cannot escape above `/`. Populate a small
synthetic root with deterministic fixture entries and read-only runtime mount
points. Exercise browser root/parent navigation and cancel, plus the source's
special-file diagnostic. Compare screens, cursor, files and exit/modes with
existing rules. Map original IDs to new ROOT test IDs; these are fresh isolated
observations, not executions against the host's original filesystem.

### ROOT-REGRESS-006 — Retain ordinary-user compatibility and attribution

After changing shared home lookup, run the safe default terminal corpus, CLI
and regex corpora, safety assertions, relevant backup/rc/history cases, Rust
checks and comparator/harness regressions. Use one frozen candidate per report.
Keep old release reports historical and identify this implementation's binary
and source input hash separately. Do not expand root support claims beyond the
new observed cases. Any new mismatch requires a fix or a named decision.

### VT-PROBE-001 — Detect a console without changing it

A read-only probe operates on the caller's existing stdin/stdout descriptors,
recording isatty, tty name, TERM, kernel, termios and VT_GETSTATE success/error.
It opens no arbitrary /dev/ttyN, does not switch VTs, alter keymaps/keyboard
modes, resize another terminal, or inject keys into another session. A PTY,
redirected stream, permission failure or unavailable ioctl records deferred VT
verification with the exact reason. TERM alone is insufficient.

### VT-INPUT-002 — Define the physical-key acceptance protocol

On a real operator-owned Linux VT, record console/keymap/locale/TERM and binary
hashes. Run pinned nano and Naro on copied fixtures. Test bare arrows, Home/End,
PageUp/PageDown, Backspace/Delete, Shift+Tab, Ctrl/Shift/Alt arrows, selected text,
Ctrl+Delete, Shift+Delete and combinations supported by the actual keymap.
Reference modifier bits are Shift=1, Ctrl=4 and Alt=8, read with TIOCLINUX
subcommand 6 after VT_GETSTATE detection. Sequence-derived bindings take their
reference priority; macro/rc-expansion replay must not acquire physical held
modifiers. Observe bytes, cursor/selection and rejected/unsupported combinations.

Any native VT support changes require fixture-controlled ioctl tests for success,
failure and non-VT fallback, with no production override that impersonates a VT.
Such tests prove branches only; they do not replace physical-key observations.
Implement missing branches based on the pinned source before advertising full
console compatibility. Do not manufacture a physical-key pass in this session.

### VT-RESTORE-003 — Record operator results and terminal restoration

Provide a checklist/report format for normal exit, canceled prompts, recoverable
tool failure and handled termination on copied buffers. Compare before/after
termios and observable cursor/keypad/mouse/paste states. Record unsupported cases,
operator identity and actual observations. Never prefill passes. Uncatchable kill
is distinct from restoration evidence. No interactive run is launched merely by
probing capabilities. The manual gate stays deferred until real-console evidence
is available; automated root/home work can complete independently.

## Delivery order

1. Commit the specification/matrix with planned status.
2. Implement shared effective-home lookup and no-home handling.
3. Build the namespace backend and collect new root/home/device/browser evidence.
4. Add the console probe/operator materials and record this session's capability.
5. Run regressions, update statuses and decisions, mirror spec files and push.

Physical-console verification remains a conditional gate. This phase does not
implement optional tiny or publish a release. It supplies concrete changes and
reviewable evidence for the supported root cases without relabeling historical
ordinary-user certification.
