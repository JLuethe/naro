# Final5 historical fault-boundary verification

The six reported raw candidate execution failures are closed as a verification
gap by a separate, candidate-only run against frozen final5 commit
`2888560a9a2709469334a417d1ad9ac3a91c30ba`. All **6 scenarios, 67 steps and
52 harness assertions passed**, together with the independent syscall-marker,
destination-inode, fallback-location and link checks. No product defect was
found and no production code was changed. The raw differential failures and
historical source scenarios remain unchanged; this receipt does not relabel
those historical recordings as passes.

Evidence is retained in
[`target/remediation-2026-11-06/final5-adapted-faults`](../target/remediation-2026-11-06/final5-adapted-faults/).
The [aggregate report](../target/remediation-2026-11-06/final5-adapted-faults/report.json),
[exact adaptations](../target/remediation-2026-11-06/final5-adapted-faults/adaptations.json),
[generated scenarios](../target/remediation-2026-11-06/final5-adapted-faults/candidate-scenarios.json)
and [harness log](../target/remediation-2026-11-06/final5-adapted-faults/attempt01/run.log)
preserve the commands, helper, inputs, observations and checks. Full recordings,
raw terminal streams, private NSS probes and fixture contents are retained in
`attempt01/candidate/` and `attempt01/work/` under that evidence root.

## Boundary adaptation and outcomes

The generated helper is derived from the historical fixture-only ptrace
supervisor. It matches only newly created `.naro-backup-*` or `.naro-save-*`
leaves directly inside each exact fixture work directory. Relative `openat`
paths are resolved using the traced child's directory descriptor. A marker is
written only after observing or setting the syscall result, and records its
operation, actual temporary pathname, result and errno.

| Historical case | Intended marker | Branch and content outcome | Steps / assertions |
|---|---|---|---|
| `TEST-NEXT-IO-002-BACKUP-FAIL` | backup `openat`, `-13` / EACCES | ordinary HOME fallback contains `original\n`; destination saves `Xoriginal\n`; old local backup retained | 10 / 6 |
| `TEST-ROOT-STATE-002-ACCOUNT` | backup `openat`, `-13` / EACCES | actual private uid 0 selects passwd `account`, despite HOME naming `home`; exact fallback bytes and saved destination verified | 10 / 11 |
| `TEST-ROOT-STATE-002-MISSING` | backup `openat`, `-13` / EACCES | private uid 0 with no passwd entry falls back to HOME; no account backup appears | 10 / 11 |
| `TEST-ROOT-STATE-002-NO-HOME` | backup `openat`, `-13` / EACCES | private uid 0, no passwd entry and no HOME reaches the original confirmation branch; declining preserves destination bytes/inode and old backup; no fallback appears | 11 / 10 |
| `TEST-NEXT-IO-001-ENOSPC` | save `write`: `4`, then `-28` / ENOSPC | preserved-original diagnostic, dirty-buffer exit question, original destination bytes/inode and no transaction leftovers | 13 / 5 |
| `TEST-NEXT-IO-002-LINK-BACKUP` | save `write`: `4`, then `-28` / ENOSPC | same preservation branch; backup contains original bytes; hard-link bytes/inode and symlink target retained | 13 / 9 |

All original exit and temporary-directory assertions were retained. Two explicit
policy adaptations were necessary in the disposable copies: the historical
ENOSPC wait for nano's `Maybe ^T^Z` truncation warning becomes the issue-3
`original file unchanged` diagnostic, and NO-HOME's historical deletion of the
old backup becomes c26's documented retention of its exact `old backup\n`
bytes. Neither alteration is applied to historical scenarios or comparison
normalization. Other historical interaction steps are retained; marker waits,
branch/content assertions and inode/link/fallback checks are additional.

The three root cases use the unchanged `spec/tools/namespace_exec.py`
bubblewrap user/mount/PID/IPC/UTS/network namespace backend. Probe assertions
confirm uid/euid 0, the intended passwd home or its absence, HOME state, and
private character `/dev/null` device 1:3. The host harness ran as ordinary uid
1000. Bubblewrap, ptrace, compiler, tmux and `en_US.UTF-8` prerequisites were
available; **no case was skipped or classified as missing a prerequisite**.
Only this run's private tmux sockets were cleaned up.

## Clean pre-fix negative control

The [negative-control report](../target/remediation-2026-11-06/final5-adapted-faults/negative-control/report.json)
and [complete test log](../target/remediation-2026-11-06/final5-adapted-faults/negative-control/test.log)
record a detached worktree at exact c26 parent
`2c63ec35bde6ee46cf51837f47860667c69349ae`. Its only tracked modification is
appending the exact c26 fixture-owned hard-link regression to
`src/backup_tests.rs`; the [test](../target/remediation-2026-11-06/final5-adapted-faults/negative-control/test.rs)
and [patch](../target/remediation-2026-11-06/final5-adapted-faults/negative-control/test.patch)
are preserved separately. It uses an ordinary pre-existing hard link inside a
fresh disposable fixture, with no race or real user file.

The old test executable exits **101 as expected**: backup creation returns
success, but the source-byte assertion observes `left: []` instead of
`original backup bytes\n`. The binary embeds the requested pre-fix revision and
the recorded adapted-source fingerprint. The identical test is also run against
the final5 test executable and exits **0**, with one test passed and no failures;
see [positive-control receipt](../target/remediation-2026-11-06/final5-adapted-faults/positive-control.json)
and [log](../target/remediation-2026-11-06/final5-adapted-faults/positive-control.log).

## Commands

From `/home/john/Code/naro`:

```sh
python3 target/remediation-2026-11-06/final5-adapted-faults/verify.py
python3 target/remediation-2026-11-06/final5-adapted-faults/negative-control.py
```

The first command creates disposable copies and runs the unchanged harness:

```sh
/usr/bin/python3 /home/john/Code/naro/spec/tools/nanoharness.py /home/john/Code/naro/target/remediation-2026-11-06/final5-adapted-faults/candidate-scenarios.json --binary /home/john/Code/naro/target/remediation-2026-11-06/daybreak-final5-frozen/naro-default --out /home/john/Code/naro/target/remediation-2026-11-06/final5-adapted-faults/attempt01/candidate --keep
```

`NANOSPEC_WORK` names `attempt01/work` inside the evidence root;
`TMUX_TMPDIR` is created privately under `/tmp` using `frozen_process.py`.
The aggregate report records command exit 0 and successful owned cleanup.

The negative-control script records and executes:

```sh
git worktree add --detach /home/john/Code/naro/target/remediation-2026-11-06/final5-adapted-faults/negative-control/source 2c63ec35bde6ee46cf51837f47860667c69349ae
# In that worktree, after appending only the preserved test:
/home/john/.cargo/bin/cargo test --offline --locked --no-run --message-format=json --target-dir /home/john/Code/naro/target/remediation-2026-11-06/final5-adapted-faults/negative-control/build
/home/john/Code/naro/target/remediation-2026-11-06/final5-adapted-faults/negative-control/build/debug/deps/naro-8b785946e7ffb0d9 --exact files::backup_tests::insecure_backup_replaces_a_hard_link_without_truncating_source --nocapture
# Positive control, from /home/john/Code/naro:
/home/john/Code/naro/target/daybreak-final5-test-default/debug/deps/naro-8b785946e7ffb0d9 --exact files::backup_tests::insecure_backup_replaces_a_hard_link_without_truncating_source --nocapture
```

The drivers intentionally require fresh output/work directories and preserve
all evidence. No installed executable was replaced, and no publication or
network operation occurred.

## SHA-256 bindings

| Artifact | SHA-256 |
|---|---|
| Frozen final5 production binary | `4e64b3ad0b3e7287272d163741adf053287c16dd69e2ca764bf5e57194b2ff3d` |
| Frozen final5 production source fingerprint | `7b6ef4e024bc5d25f59fb66eebad7f8297d4be4f49a34d1037c3b8d4f928e636` |
| Final5 positive-control test executable | `0a0214bd07ceba7ab5196ddc90d317d32acbea622ff7bb349ff7d8eb1b374c47` |
| Pre-fix unmodified source fingerprint | `33e3f5e98dae5c0331995e74944362f996fbebb2c9b493ee719aebf3c3fb5ce1` |
| Pre-fix source with only appended regression | `14e896e633a5454d0cd50b9f898b66503e7710daa084d9deb251a9c266736aa8` |
| Pre-fix test executable | `27543e8cde8fb65498e46808852e3503880fbab3332a35e36253e47663e07a5f` |
| report.json | `602da6e2618497ef0073779bc6227912d6a47c5eaf7067a4756c97b932326aa8` |
| candidate-scenarios.json | `e28c744c4b5f32ac9d1f88a8aef921e41dcc3b700d332b0e6bb32f3a62dd8792` |
| faultwrap-adapted.c | `b01a4a7929d538f3a16e640bde74ca417d2c8736ca9d14a6b52d6ee9da95c831` |
| verify.py | `80ac20580cf7d645d1d295ad4aa906ce3f8f7c6a662dc2172057deeb3d51fc51` |
| negative-control.py | `9fd916cb8392853b81def4fcfdd09fe5555bec410548e23250f280302d9bb3aa` |
| negative-control/report.json | `524e262bb407a4aa014d6946c108c30a717ec212b98995db3b680484fda01022` |
| negative-control/test.rs | `fb551e0bcbce231becfcc3e49f08cd7d21ae0e7a2f4e0624b49a831b8e61cc0f` |
| negative-control/test.patch | `a4f4665aad137fa609f341f9b9e87b96f425ba76a74992f3d3af0f8b5135d824` |
| negative-control/test.log | `ae4953106fb68c0eb19239cdafb38b4652edc132015d06cb3cdea385c3de42a0` |
| positive-control.json | `05bf4b10aeddc5e2bee90a3b9363bfb41c1f4f6947137eaa746728443aea1749` |

The aggregate report also binds the unchanged original scenario JSON files,
historical supervisor, harness and namespace backend by SHA-256, checked both
before and after execution. These are local host fixture results; they do not
simulate actual storage power loss or establish nano parity for the deliberately
changed save/backup policies.
