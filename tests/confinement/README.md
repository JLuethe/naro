# Deterministic opened-object boundary checks

Build the unit-test executable, then pass its `executable` path from Cargo's JSON:

```sh
cargo test --offline --no-run --message-format=json
python3 tests/confinement/run.py --binary /absolute/path/to/test-executable --out target/boundary-default
cargo test --offline --features tiny --no-run --message-format=json
python3 tests/confinement/run.py --binary /absolute/path/to/tiny-test-executable --out target/boundary-tiny --tiny
```

`--out` must be fresh. The fixture is ignored by ordinary unit runs because it
requires a fixture controller. Saves reuse the existing Rust
`files::safe_save_tests::fixture_save` entry point and run real `files::write`.
Reads use a small external C driver linked against the unchanged native bridge;
it reads and fstats the descriptor returned by `nr_confined_open`. Existing Rust
unit tests cover the read wrapper integration. No `src/` or production native
code changes are required. The separate preload shim only pauses execution and records opened descriptor
identities; it is never linked into a shipping build and does not mutate paths.
The Python controller mutates only entries it has created in its disposable
fixture. Each child has a ten-second deadline; each gate waits at most five
seconds. There is no uncontrolled race loop, external document, exploit payload,
or scheduling-dependent success criterion. Fixtures and logs are retained.

The interposer shares the same gates across `open`/`openat`, their `64`
variants, and glibc's fortified `__open*_2` entry points. It calls the matching
libc symbol, retaining fortified argument checks. A compiler can use
`__openat_2` for the no-mode source open while using ordinary `openat` for the
mode-bearing temporary creation; both must be intercepted.

The 72 default cases cover 67 saves and five reads. Tiny runs the same 67 saves
through the shared native opened-parent implementation **without confinement**;
tiny does not expose the operating-directory option. Ordinary confinement unit
tests separately cover supported relative symlink reads and parent traversal.

All save modes (overwrite, append, prepend) run baseline existing/missing-target
checks and parent symlink/atomic `RENAME_EXCHANGE`, final symlink/atomic exchange,
and removal at three actual syscall boundaries:

- Before source `openat`, after native no-follow metadata validation.
- Before temporary `openat`, with an existing source descriptor held.
- Before publication `renameat`, after the final source/entry/temporary checks.

Missing overwrite/append cases also insert a symlink or regular target, or swap
the parent, before temporary creation and publication. Missing prepend is
refused before those gates and is covered as a baseline. Confined reads pause
before reopening the authorized `O_PATH` descriptor via `/proc/self/fd`.

Assertions cover destination bytes, original/outside/other inode witnesses,
opened root/parent/source identities as applicable, read metadata/data agreement,
new publication inode identity, and absence of unpublished `.naro-save-*` files.
Parents are mode 0777 without sticky protection. The controlled actor has the
same credentials as the editor; this is a test of mutable directory entries, not
an independent multi-user permission test. Parent relocation outside the root
intentionally retains authority over the same directory inode, as documented.

Final-entry changes before source open or temporary creation are rejected. A
change immediately before publication can be replaced successfully: the final
name is not a compare-and-swap transaction. A late symlink is replaced as an
entry and its referent is unchanged. These outcomes are explicit expected
results; they are not blanket claims of race safety.

`report.json` retains per-case results and descriptor identities; each case also
retains `before.json`, gate/open records, process output, result text and files.
Timeouts and shim failures are classified as infrastructure failures separately
from assertion failures. Earlier output directories must not be reused or
removed to turn a failed attempt into a pass. Linux openat2, procfs,
`renameat2(RENAME_EXCHANGE)`, a C compiler and dynamic interposition are required.
No coverage of mount mutation, malicious temporary-entry replacement, unsupported
kernels/procfs, or every possible syscall interleaving is claimed.
