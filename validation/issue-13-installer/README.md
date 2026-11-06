# Issue #13 — recoverable installer transaction

Validated locally on 2026-11-05 with Python 3.14.8, Linux 7.2.15,
glibc 2.44. All installation, removal, archive and repository operations used
`TemporaryDirectory` fixtures. No real prefix, release executable, published
artifact, credentials or upstream state was changed. This evidence concerns
the Python installer shared by default and tiny packages.

The bounded pre-fix fixture confirmed the hypothesis: after either of two
payload replacements, fresh installs had no ownership state and retries failed;
upgrades retained mixed versions or new bytes with old ownership hashes.
A partial state write left invalid JSON. All six fresh/upgrade boundary cases
and their retry/removal outcomes are retained in the raw `before-results.json`.
The original installer SHA-256 was
`3350386cae90db70600ac4e1bed2a7257bcf0df12d510f37ff9c1dc9cc0cda3c`.

The installer now syncs a complete staged payload, publishes an atomic durable
pending journal, and replays the transaction forward. Previous ownership and
new hashes define the only accepted destination contents. Final state is
synced, atomically replaced and directory-synced before journal retirement.
A transaction identity distinguishes reinstallation of identical content from
an already committed transaction. `install`, `recover` and `uninstall` share
recovery; uninstall stops safely on a pending conflict. A prefix directory
lock serializes cooperating installer invocations. Source validation still
rejects a bad payload before creating the prefix.

| Check | Result |
| --- | --- |
| Focused installer suite | 16 tests passed; 234 boundary cases |
| Boundary matrix | 78 before-operation EIO, 78 after-operation EIO, 78 child-process exits; fresh install and upgrade |
| State durability | Complete JSON/mode sync → rename → directory sync asserted; partial JSON write preserves old state |
| Additional failures | Partial payload ENOSPC, close EIO, conflict-state update failure |
| Recovery/removal | Each payload and final-state boundary; recovery without original package; missing owned-file repair |
| Protections | Modified files, payload/stage/directory symlinks, traversal, reserved metadata paths, overlapping paths, concurrent installers |
| Existing packaging tests | 9 passed, including strict dirty-tree rejection and documentation links |
| Strict synthetic package | Real changed installer/INSTALL archived from a clean temporary Git repository; 15 files installed, verified, recovered (no-op), removed |
| Static checks | `py_compile` and scoped `git diff --check` passed |

The exact commands, file hashes, logs, fixture archive identities and result
counts are recorded in [receipt.json](receipt.json). Raw evidence is under
`target/remediation-2026-11-05/issue-13-installer/`. The first strict-package
fixture attempt failed to import `package` because its repository-root path
was one parent too high. Its script and traceback are retained; it is an
infrastructure failure, not a pass. The corrected second attempt passed.

These tests exercise real filesystem calls and abrupt process exit, not
physical power-loss/storage-controller behavior. Durability assumes functioning
Linux atomic rename and file/directory `fsync`. The complete installed file set
is not switched simultaneously; users must not run from a prefix during a
transaction. Pre-journal failures may leave unreferenced staging copies and
abrupt exits may leave temporary copies; these do not claim installed ownership.
The fixture executable/native dependency probes are synthetic, so this is not
release-binary or native-library qualification. Strict packaging was not relaxed.
