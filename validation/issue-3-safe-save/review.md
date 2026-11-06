# Independent integrated review: issue #3

Date: 2026-11-05. Base: `278f1c541542bc044f4da8f7b3ae72b3990fabdf`.
Working directory: `/home/john/Code/naro`.

**Verdict: no remaining blocking correctness finding for issue #3.** This
verdict follows the completed implementation, final default/tiny fault matrices,
final terminal run, and CI wiring review. It does not confer release qualification.

The reviewer read CONTRIBUTING.md, docs/safe-save.md, the relevant file and test
specifications, production changes, test driver/interposer, candidate terminal
overlays, and `.github/workflows/rust.yml`. No applicable AGENTS.md was found.
The reviewer did not edit production code, repository tests, original reference
recordings, or unrelated untracked files. Supplemental checks used newly created
synthetic fixtures under ignored `target/`.

## Findings and acceptance review

The regular-file path writes to an exclusively created same-directory temporary
file. Complete writes and append/prepend source reads precede metadata copying,
file fsync, checked close, rename, and directory fsync. No regular-file path
silently falls back to truncating the destination. Writes, reads, opens, and
fsync handle EINTR; close is checked without unsafe retry on Linux.

The native commit flag distinguishes a pre-rename failure from a failure after
replacement. Rust reports uncertain durability after commit and advances the
buffer's saved state only after the transaction succeeds. The obsolete blanket
ENOSPC truncation warning was removed. Ordinary injected failures preserve
destination contents/inode and remove the owned temporary file; unrelated
sentinel entries remain untouched.

Numeric owner/group, permission bits, Linux xattrs, and POSIX ACL copying are
checked before commit. Metadata failures abort replacement. Existing timestamp
identity is deliberately not preserved; that policy is explicit, and tests
verify the new modification time. Supplementary-group restoration and default
ACL inheritance/removal received actual fixture coverage. Final-component
symlinks are rejected, hard links retain the old inode through their other
names, and append/prepend use the same transaction. FIFO streaming remains a
documented exception with checked close and an incomplete-output error.

Two correctness edges identified during review were corrected before the final
runs: empty xattr queries now supply nonzero storage on the second call, and a
generated temporary basename equal to the requested destination is skipped.
The final matrices include the basename-collision case. The reviewer separately
verified empty xattrs and directory ACL behavior.

The candidate terminal overlays preserve the historical reference and shared
comparison rules. They explicitly assert the intended preserved-original result,
non-writable-parent failure, dirty buffer, and earlier `Writing...` phase. The
remaining opening snapshot was updated explicitly rather than discarded.
Selection, append/prepend, backup feedback, FIFO interruption, narrow layouts,
cursor state, and styling are exercised by the final terminal suite.

CI generates those candidate expectations and runs actual save faults against
Cargo-discovered default and tiny test executables. The new shell block passes
syntax checking. The primary agent also executed that exact block locally with
414/414 cases passing for each profile; no hosted CI result is claimed here.

## Validation evidence

The reviewer independently ran formatting, diff, C syntax, Python syntax, six
file-sync preservation regressions, and three supplemental metadata cases. The
reviewer also inspected the final matrices, recalculated executable hashes, and
reopened all 32 final terminal result files: every step and all 1,718 checks pass.
Cargo unit-test execution alone is not counted as save coverage: the fixture
entry returns early without its fixture environment; the subprocess matrices
actually execute `files::write`.

| Evidence | Result |
| --- | --- |
| Final default syscall matrix, `target/issue-3-fault-matrix-03/report.json` | 414/414 |
| Final tiny syscall matrix, `target/issue-3-fault-matrix-tiny-03/report.json` | 414/414 |
| Old implementation, `target/issue-3-old-regression/report.json` | Expected failure: 0/3 preservation assertions pass |
| Reviewer default/tiny preservation reruns, `target/issue-3-review-regression-{default,tiny}/report.json` | 3/3 each |
| Reviewer supplemental metadata, `target/issue-3-review-supplement-02/report.json` | 3/3 |
| Final frozen terminal suite, `target/issue-3-terminal-final/` | 32/32 scenarios; 1,718/1,718 checks |

The old-code failures show changed destination bytes after injected file-sync
EIO for overwrite, append, and prepend. The equivalent final-code assertions
pass, establishing meaningful old-fail/new-pass regressions.

Verified SHA256 identities:

| Executable | SHA256 |
| --- | --- |
| Default test executable | `8d67444b6bb6ce8ab9dbf968610dd2a7b7a4e9b9890611e865da4a027ea27e35` |
| Tiny test executable | `d7bd1d315720e736975dfd4516041e8519b1aa436743882ccdfe91a0ef2e47e4` |
| Frozen default terminal executable | `14c1506baae0450c14c50377e08b67dc380a107b44a5004ce142ce96be487a72` |

The reviewer inspected final logs for unit tests (17 default, 12 all-features,
12 tiny), clippy default/all-features, default/tiny release builds, comparison
and harness tests, inventory/spec audit, smoke/safety, and branding. Those
commands passed; the specification audit retains its existing citation warnings.
The primary agent additionally reported final frozen tiny CI at 195/195.
Exact broader commands and retained failed attempts are in [commands.json](commands.json)
and [test-commands.md](test-commands.md).

## Commands executed by the reviewer

These validation commands all returned zero. Output directories were fresh when
run; choose new names when repeating the fixture commands.

```sh
/home/john/.cargo/bin/cargo fmt --check
git diff --check
cc -std=c11 -Wall -Wextra -Werror -D_DEFAULT_SOURCE -D_XOPEN_SOURCE=700 -fsyntax-only native/bridge.c
cc -std=c11 -Wall -Wextra -Werror -D_DEFAULT_SOURCE -D_XOPEN_SOURCE=700 -DNARO_TINY -fsyntax-only native/bridge.c
python3 -m py_compile tests/safe-save/run.py tests/safe-save/progress_cases.py
python3 tests/safe-save/run.py --binary target/debug/deps/naro-f143b0d4013ffd62 --out target/issue-3-review-regression-default --regression-only
python3 tests/safe-save/run.py --binary target/debug/deps/naro-72a4835848d83bb3 --out target/issue-3-review-regression-tiny --regression-only
python3 target/issue-3-review-supplement-02/check.py
```

The supplemental script and report are retained locally. It checks an empty
`user.*` attribute, a new file's inherited default ACL against a normally created
control, and removal of a temporary file's inherited ACL when the original has
none. It checks exact bytes/mode/xattrs, saved state, cleanup, and an unchanged
test-executable hash throughout the run. An earlier identical supplemental run
is retained in `target/issue-3-review-supplement-01/`.

Read-only inspection used `rg`, `sed`, `cat`, `git diff`, `git status`,
`sha256sum`, and Python JSON/hash checks. For CI, Python extracted the new
`Atomic save faults, default and tiny` run block and supplied it to `bash -n`
through `subprocess.run`; exit status was zero.

## Remaining limits

This is local Linux validation. Deterministic abrupt process exits exercise
commit boundaries; they do not simulate actual power loss, every filesystem,
storage-controller behavior, or all possible syscall failures. Privileged
foreign-UID ownership transitions and every xattr namespace were not exercised.
Directory-close and source-close failures are checked in code but are not
separately distinguished by the close-fault interposer.

Concurrent writers require external coordination, and complete adversarial
namespace/confinement handling remains separate issue #12. Uncatchable exits
may leave temporary entries, as documented. No Daybreak Blue scan, new full
host/Ubuntu/guest-VT qualification matrix, system installation, or publication
is claimed by this review.
