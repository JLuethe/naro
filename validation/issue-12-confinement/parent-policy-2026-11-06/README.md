# Issue #12 stage-open parent policy

The first private-staging revision left a gap between creating a private child
directory in a mode-0777 parent and opening that child. A different UID with
write permission on the parent can move the new entry and substitute another
editor-owned directory from the same synthetic fixture. The old owner/device
check then accepts that unrelated directory. In the bounded negative control,
the prior binary reported success, published the intended new target bytes, and
removed the substituted editor-owned directory. The original private stage
survived under the actor's `stolen` name. This is an unrelated-directory deletion
and a false claim of safe cleanup, even though the destination bytes were right.

The revised save path checks the opened parent's owner and mode before stage
creation. It accepts a parent owned by the editor or privileged root. Group or
other write permission additionally requires the sticky bit. POSIX ACL named
writers are reflected in the group mode mask and therefore trigger the same
conservative check. This permits editor-owned mode-0700/0755 directories and
editor-owned sticky mode-1777 directories; it rejects nonsticky mode-0777,
ACL-writable nonsticky parents, and a sticky parent owned by another unprivileged
UID. Root-owned sticky directories are permitted because root is already
privileged over the editor's files. This restriction changes compatibility for
shared nonsticky directories, including ones owned by the editor. It applies to
overwrite, append, prepend, and missing-file saves. The stage remains a private
child on the destination filesystem, and final-target publication remains
non-CAS.

## Artifact-specific checks

Commands ran in isolated worktree `issue12-parent-policy`, based on `3446773`.
The default test executable SHA-256 is
`986088d4e516f6424be975ded06d0412fa4a6d8c9fe7be2d4ea0af98f67f035c`;
tiny is `09acf407abe43cd6a2401fbf08229b54ca6a3a95fe24ea0345ea4e1babea6b29`.
The prior private-stage executable is
`e99d829662b32664e47ba8a89126f5b245039ac137295422ccb6e79d224511ce`.
Raw fixtures and logs remain under this worktree's ignored `target/`. The small
[old negative-control report](old-negative-control.json),
[new negative-control report](new-negative-control.json), and
[policy report](policy-report.json) are retained here.

| Command | Result |
| --- | --- |
| `cargo test --offline` | 74 passed, 10 ignored |
| `cargo test --offline --features tiny` | 41 passed, 10 ignored |
| `cargo fmt --check` | Passed |
| `cargo clippy --offline --all-targets --all-features -- -D warnings` | Passed |
| `python3 tests/confinement/parent_policy.py --binary <default> --out target/parent-policy-default-final2` | 10/10 passed: owned private/ordinary/sticky allowed; unsafe existing/missing and all save modes refused before stage; ACL named writer refused |
| Same runner with `<tiny>` and `--out target/parent-policy-tiny-final2` | 10/10 passed |
| `unshare --map-root-user --map-subids python3 tests/confinement/parent_policy.py --binary <old> --out target/parent-policy-distinct-old-final --only unsafe-open --distinct-uid-actor` | Expected regression failure: stage-open gate reached, prior binary removed the substituted unrelated directory |
| Same command with `<default>` and `--out target/parent-policy-distinct-new-final` | Passed: gate not reached, target and borrowed directory unchanged |
| `unshare --map-root-user --map-subids python3 tests/confinement/parent_policy.py --binary <default> --out target/parent-policy-foreign-sticky --only foreign-sticky` | Passed: foreign-owned sticky parent refused |
| `python3 tests/confinement/run.py --binary <default> --out target/confinement-default` | 77/77 passed; 0 infrastructure failures |
| Same runner with `<tiny>`, `--tiny --out target/confinement-tiny` | 72/72 passed; 0 infrastructure failures |
| `unshare --map-root-user --map-subids python3 tests/confinement/run.py --binary <default> --out target/confinement-distinct --distinct-uid` | 2/2 passed: distinct UID cannot traverse private stage or move it in owned mode-0755 parent |
| `python3 tests/safe-save/run.py --binary <default> --out target/safe-save-default` | 659/659 passed |
| Same runner with `<tiny>` and `--out target/safe-save-tiny` | 659/659 passed |
| `python3 tests/backup/run_safe_save.py --binary <default> --out target/backup-default` | 1200/1200 passed |

The negative control used only disposable synthetic paths. Its gate runs once
at the real `openat` stage-open boundary; the actor has a mapped different UID
inside a private user namespace. User namespace/subordinate-ID support and
POSIX ACL support are prerequisites for those specific cases. No real document,
credentials, installed editor, or uncontrolled race loop was involved. The
checks are deterministic boundaries, not exhaustive concurrency or physical
power-cut qualification. Later integrated binaries require their own tests.
