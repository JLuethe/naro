# Issue #12 private staging follow-up

The bounded publish-gate fixture exposed a real gap in the earlier save path:
after the last temporary-entry identity check, another process with write
access to the mode-0777 destination parent could move that entry and substitute
a symlink. Revision `d5a496a` then reported success while the destination name
became the substituted symlink. Its referent stayed unchanged, but the saved
pathname and intended contents were corrupted. The five overwrite/append/prepend
regression cases fail against that revision (`0/5`) and pass with the private
staging implementation (`5/5`). The old failure report records destination
bytes `outside sentinel` instead of the expected new bytes.
The small [old regression report](old-regression-report.json),
[new regression report](new-regression-report.json), and
[distinct-UID report](distinct-uid-report.json) are retained with this note.

The implementation creates a unique mode-0700 child under the opened destination
parent, holds that child's descriptor, and creates the temporary `content` file
inside it. Publication uses `renameat` from the held child to the held parent.
A different-UID actor can move and substitute the child entry in a writable
parent but cannot traverse or replace its contents. The destination still gets
the intended bytes; because cleanup cannot verify the moved child under its
original name, the save reports a committed error. The unrelated substitute is
preserved. Same-UID processes can traverse the child and remain outside this
filesystem permission boundary. Final-target publication still is not CAS.

## Commands and observed results

All commands ran from the isolated `issue12-finish` worktree, with disposable
fixtures under its ignored `target/`. Cargo was invoked as
`/home/john/.cargo/bin/cargo` and `--offline` was used for reproducibility.
The default fixture executable SHA-256 is
`e99d829662b32664e47ba8a89126f5b245039ac137295422ccb6e79d224511ce`;
tiny is `8bee670a0201a08b4c2d4d9971a90b3a84b3d4ef119cd09c02b91f2cfd7010b6`.
The old revision's executable is
`f3e6f81522fc34e7ff16cd73015e22c94b219d236d8949f473b7c2b8aa9c9208`.

| Command | Result |
| --- | --- |
| `cargo fmt --check` | Passed |
| `cargo clippy --offline --all-targets --all-features -- -D warnings` | Passed |
| `cargo test --offline` | 72 passed, 10 ignored |
| `cargo test --offline --features tiny` | 39 passed, 10 ignored |
| `python3 tests/safe-save/run.py --binary <default> --out target/issue12-private-safe-save-acl-2` | 659/659 passed |
| Same runner with `<tiny>` and `--out target/issue12-private-safe-save-tiny` | 659/659 passed |
| `python3 tests/confinement/run.py --binary <default> --out target/issue12-private-confinement-final` | 77/77 passed; no infrastructure failures |
| Same runner with `<tiny>`, `--tiny --out target/issue12-private-confinement-tiny` | 72/72 passed; no infrastructure failures |
| `unshare --map-root-user --map-subids python3 tests/confinement/run.py --binary <default> --out target/issue12-distinct-uid-final --distinct-uid` | 2/2 passed; mapped UID 100000 denied stage traversal and substituted its parent entry |
| `python3 tests/confinement/run.py --binary <default> --out target/issue12-stage-regression-new-3 --stage-substitution-only` | 5/5 passed |
| Same runner with `<old>` and `--out target/issue12-stage-regression-old-3` | Expected regression: 0/5 passed; all five published the substituted outside-pointing symlink |
| `python3 tests/backup/run_safe_save.py --binary <default> --out target/issue12-private-backup` | 1200/1200 passed |

The safe-save matrix injects stage-sync, parent-sync, stage-removal and final
parent-sync failures and abrupt exits after publication. Every post-commit
failure reports an error while retaining the complete new contents. A new-file
default ACL is compared with direct creation in the destination parent. Tests
also check precommit original preservation, stage cleanup, and unrelated-entry
preservation. One initial new-file ACL matrix attempt failed because its runner
erroneously scheduled a source read fault for a missing file; that fixture
selection was corrected, and the failed `659/660` output remains in `target/`.

These results apply only to the named executables and deterministic boundaries.
They do not establish power-cut persistence or exhaustive concurrency safety.
The intended Linux durability sequence requires successful file sync, staging
directory sync, destination directory sync, staging removal, and final
destination directory sync before success. A later integrated build requires
its own qualification.
