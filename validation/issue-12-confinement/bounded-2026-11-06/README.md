# Issue #12 bounded interleaving evidence

Date: 2026-11-06 (America/Los_Angeles). Tested production source revision
`80185fe` in isolated branch/worktree `issue-12-bounded`, under
`/home/john/Code/naro/target/issue-12-bounded`. No production source changes were
needed. All fixtures are disposable files under that worktree's `target/`.

**Result:** the opened-parent/opened-source policy held for the exercised
interleavings. No outside sentinel inode's bytes were written, no old source inode's bytes were
modified, and no unpublished save temporary remained. The matrix also confirms
the documented lack of a final-entry compare-and-swap guarantee: an entry
introduced after final validation can be replaced by publication. In particular,
a late symlink can be replaced as an entry; its referent is never written.
This is not an exhaustive race-safety claim, vulnerability confirmation, release
qualification, or an issue-closure decision.

## Commands and results

Cargo commands used `/home/john/.cargo/bin/cargo`. Build commands produced test
executable paths from Cargo JSON; the runner commands used those absolute paths.
Exact executable SHA-256 values and per-case opened identities are in
[default-report.json](default-report.json) and [tiny-report.json](tiny-report.json).

| Command | Observed result |
| --- | --- |
| `cargo test --offline --no-run --message-format=json` | Built existing default fixture executable |
| `python3 tests/confinement/run.py --binary <default-test-executable> --out target/issue12-boundary/external-reviewed-default` | 72/72 passed; 0 infrastructure failures; 0 assertion failures |
| `cargo test --offline --features tiny --no-run --message-format=json` | Built existing tiny fixture executable |
| Same runner with tiny executable, `--tiny --out target/issue12-boundary/external-reviewed-tiny` | 67/67 passed; 0 infrastructure failures; 0 assertion failures |
| `cargo test --offline` | 72 passed, 10 ignored |
| `cargo test --offline --features tiny` | 39 passed, 10 ignored |
| `cargo clippy --offline --all-targets --all-features -- -D warnings` | Passed |
| `cargo fmt --check` | Passed |

The existing ignored Rust save fixture is invoked explicitly by the controller;
its ignore status in ordinary unit-suite totals does not omit it from these
matrices. Tiny's 67 cases cover the shared native opened-parent save path with
confinement disabled, because tiny has no operating-directory option. The five
confined read cases use an external driver linked against the unchanged native
bridge; ordinary Rust confinement tests cover its Rust wrapper integration.

## Exercised interleavings

The [runner documentation](../../../tests/confinement/README.md) explains the
one-shot gates, deadlines, fixture ownership, and assertions. Existing targets
were tested in overwrite, append, and prepend modes. Missing targets were tested
in overwrite/append at the applicable gates, plus normal prepend refusal.

| Entry mutation | Before source open | With source held, before temp creation | Immediately before publication |
| --- | --- | --- | --- |
| Parent renamed and replaced by outside-pointing symlink | Save uses pinned parent inode | Save uses pinned parent inode | Save uses pinned parent inode |
| Parent atomically exchanged with outside directory | Save uses pinned parent inode, now at outside pathname | Same | Same |
| Final symlink, atomic final-entry exchange, or removal | Save refused | Save refused | Save publishes; concurrent entry is replaced |
| Previously missing target gets symlink or regular entry | Not applicable | Save refused | Save publishes; concurrent entry is replaced |

Read cases pause before `/proc/self/fd` reopens the held `O_PATH` source. Parent
symlink/exchange and final symlink/exchange/removal all return the original
source's bytes and `(device,inode)` metadata. Parents are deliberately mode 0777
without sticky protection. The controlled actor uses the editor's credentials;
this is not a multi-user credential/permissions test.

Each case checks the actual authorized parent identity, opened source identity
when present, new destination identity, destination bytes, original/outside/other
inode witnesses, and temporary cleanup. Missing targets have no original source
identity. For read cases the opened root and source identities are recorded.
Moving an opened parent outside the root intentionally retains authority over
that directory object; the unrelated outside sentinel inode remains unchanged.

## Evidence and limits

Committed JSON reports, suite/matrix logs, and [manifest.json](manifest.json)
record the final results, hashes, tool versions, and production input hashes.
Full fixture trees, gate records, process logs, compiler logs, and all earlier
attempts remain under `target/issue12-boundary/` in the isolated worktree.

The first matrix versions also passed (72 default, 67 tiny). An initial
integrated Rust fixture produced one Clippy failure on a constant assertion;
[attempt01-clippy.log](attempt01-clippy.log) preserves it. That test fixture was
removed in favor of the existing Rust save fixture and external read driver,
so the final implementation changes no production fingerprint input. The final
Clippy pass is separately recorded. No failed attempt was overwritten or counted
as a pass.

The tests do not cover malicious temporary-entry replacement, mount mutation,
unsupported kernels/procfs, separate attacker credentials, or every syscall
interleaving. Final-entry publication is still not compare-and-swap. A fresh
build after a new commit can carry a different build-revision string even when
production source hashes are unchanged; these results do not transfer existing
artifact receipts to a newly built executable or qualify a release package.
