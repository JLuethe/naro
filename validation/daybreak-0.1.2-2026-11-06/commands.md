# Final5 qualification command ledger

These commands were orchestrated in the Codex session. The `daybreak-*` output
names identify the qualification campaign; they do not assert that a Daybreak
Blue model executed the commands. The independent Daybreak Blue rerun remains a
separate handoff.

All commands ran from `/home/john/Code/naro` unless another working directory is
shown. Parallel commands are listed separately. Raw outputs are in the named
`target/remediation-2026-11-06/` directories. Earlier Sol commands are recorded
in `validation/issue-3-safe-save/lock-identity.json`,
`validation/issue-3-safe-save/lock-identity.md`, and the backup-fix reports
named by `validation/issue-3-safe-save/README.md`.

## Source and focused preflight

| Command | Outcome |
|---|---|
| `git status --short --branch` plus `git show --stat`, `git show --check`, and receipt reads for `2888560` | clean tracked candidate; unrelated untracked files preserved |
| `cargo fmt --check` | pass |
| `cargo test --locked --offline files::lock_tests -- --nocapture` | 7 passed |
| `cargo test --locked --offline --features tiny files::lock_tests -- --nocapture` | 7 passed |
| `python3 tests/safe-save/test_progress_cases.py` | 7 passed |
| `git diff --check` | pass |

## Exact artifact construction

The following ran in separate target directories and exited 0:

```sh
cargo build --locked --offline --release --target-dir target/daybreak-final5-default
cargo build --locked --offline --release --features tiny --target-dir target/daybreak-final5-tiny
cargo build --locked --offline --release --features credits --target-dir target/daybreak-final5-credits
cargo build --locked --offline --release --features test-hooks --target-dir target/daybreak-final5-hooks
cargo build --locked --offline --release --features tiny,test-hooks --target-dir target/daybreak-final5-hooks-tiny
cargo test --locked --offline --no-run --message-format=json --target-dir target/daybreak-final5-test-default
cargo test --locked --offline --no-run --features tiny --message-format=json --target-dir target/daybreak-final5-test-tiny
```

`install -m 0555` copied the five release executables into
`target/remediation-2026-11-06/daybreak-final5-frozen/`. `sha256sum`, `stat`,
and `NARO_BUILD_INFO=1` were run for every copy and passed the expected
revision/fingerprint/features checks.

## Rust and discovery gates

These two equivalent Rust/Clippy passes exited 0; the second was persisted in
`daybreak-final5-*.log` for independent reopening:

```sh
cargo test --locked --offline
cargo test --locked --offline --no-default-features --features tiny
cargo test --locked --offline --all-features
cargo clippy --locked --offline --all-targets --all-features -- -D warnings
cargo clippy --locked --offline --all-targets --no-default-features --features tiny -- -D warnings
```

```sh
cargo fmt --check 2>&1 | tee target/remediation-2026-11-06/daybreak-final5-fmt.log
cargo test --locked --offline 2>&1 | tee target/remediation-2026-11-06/daybreak-final5-test-default.log
cargo test --locked --offline --no-default-features --features tiny 2>&1 | tee target/remediation-2026-11-06/daybreak-final5-test-tiny.log
cargo test --locked --offline --all-features 2>&1 | tee target/remediation-2026-11-06/daybreak-final5-test-all-features.log
cargo clippy --locked --offline --all-targets --all-features -- -D warnings 2>&1 | tee target/remediation-2026-11-06/daybreak-final5-clippy-all-features.log
cargo clippy --locked --offline --all-targets --no-default-features --features tiny -- -D warnings 2>&1 | tee target/remediation-2026-11-06/daybreak-final5-clippy-tiny.log
```

Discovery commands and outcomes:

```sh
python3 -m unittest discover -s spec/tools -p 'test_*.py' -v       # 66 passed
python3 -m unittest discover -s tools -p 'test_*.py' -v            # 125 passed
python3 -m unittest discover -s tests/remediation -p 'test_*.py' -v # 11 passed
python3 -m unittest discover -s tests/safe-save -p 'test_*.py' -v  # 7 passed
python3 -m unittest discover -s tests/catalog -p 'test_*.py' -v    # 5 passed
python3 -m unittest discover -s tests/console -p 'test_*.py' -v    # 9 passed
```

## Issue #3 matrices and terminal checks

```sh
python3 tests/safe-save/run.py --binary target/daybreak-final5-test-default/debug/deps/naro-8b785946e7ffb0d9 --out target/remediation-2026-11-06/daybreak-final5-safe-default
python3 tests/safe-save/run.py --binary target/daybreak-final5-test-tiny/debug/deps/naro-92b0cf5a83e9781f --out target/remediation-2026-11-06/daybreak-final5-safe-tiny
python3 tests/backup/run_safe_save.py --binary target/daybreak-final5-test-default/debug/deps/naro-8b785946e7ffb0d9 --out target/remediation-2026-11-06/daybreak-final5-backup
python3 tests/recovery/run.py --binary target/remediation-2026-11-06/daybreak-final5-frozen/naro-hooks --out target/remediation-2026-11-06/daybreak-final5-recovery-default
python3 tests/recovery/run.py --tiny --binary target/remediation-2026-11-06/daybreak-final5-frozen/naro-hooks-tiny --out target/remediation-2026-11-06/daybreak-final5-recovery-tiny
python3 tests/remediation/safe_save_semantics.py --binary target/remediation-2026-11-06/daybreak-final5-frozen/naro-default --out target/remediation-2026-11-06/daybreak-final5-semantics
```

Outcomes: 448/448 per safe-save profile, 1200/1200 backup, 41/41 per
recovery profile, 22/22 progress, and 10/10 safety.

```sh
python3 spec/tools/nanoharness.py tests/safe-save/locking.json target/issue-3-lock-validation/historical-locking.json --binary target/remediation-2026-11-06/daybreak-final5-frozen/naro-default --out target/remediation-2026-11-06/daybreak-final5-locking
python3 spec/tools/nanoharness.py target/issue-3-lock-validation/verified-save-progress.json target/issue-3-lock-validation/verified-save-safety.json --binary target/remediation-2026-11-06/daybreak-final5-frozen/naro-default --out target/remediation-2026-11-06/daybreak-final5-save-terminal
```

Outcomes: 6/6 lock scenarios with 35 assertions and 32/32 save scenarios
with 1,718 assertions.

The first extension command below exited 1 because it was given the 41-case
fault-matrix directory instead of the three terminal panic recordings; its
default, credits, and production-no-hook subchecks passed. The correction then
passed.

```sh
python3 tools/check_extensions.py --default target/remediation-2026-11-06/daybreak-final5-frozen/naro-default --credits target/remediation-2026-11-06/daybreak-final5-frozen/naro-credits --panic-runs target/remediation-2026-11-06/daybreak-final5-recovery-default --panic-binary target/remediation-2026-11-06/daybreak-final5-frozen/naro-hooks --out target/remediation-2026-11-06/daybreak-final5-extensions
python3 spec/tools/nanoharness.py tests/follow-up/scenarios/panic.json --candidate-expectations --binary target/remediation-2026-11-06/daybreak-final5-frozen/naro-hooks --out target/remediation-2026-11-06/daybreak-final5-panic
python3 tools/check_extensions.py --default target/remediation-2026-11-06/daybreak-final5-frozen/naro-default --credits target/remediation-2026-11-06/daybreak-final5-frozen/naro-credits --panic-runs target/remediation-2026-11-06/daybreak-final5-panic --panic-binary target/remediation-2026-11-06/daybreak-final5-frozen/naro-hooks --out target/remediation-2026-11-06/daybreak-final5-extensions-attempt02
```

## Signals, search, undo, native bridge, catalogs, and identity

All commands below exited 0:

```sh
python3 tests/signals/terminal.py --binary target/remediation-2026-11-06/daybreak-final5-frozen/naro-default --out target/remediation-2026-11-06/daybreak-final5-signals-default
python3 tests/signals/terminal.py --tiny --binary target/remediation-2026-11-06/daybreak-final5-frozen/naro-tiny --out target/remediation-2026-11-06/daybreak-final5-signals-tiny
python3 tests/signals/native.py --out target/remediation-2026-11-06/daybreak-final5-signals-native
python3 tests/search/run.py --out target/remediation-2026-11-06/daybreak-final5-search-resource
python3 tests/search/terminal.py --binary target/remediation-2026-11-06/daybreak-final5-frozen/naro-default --out target/remediation-2026-11-06/daybreak-final5-search-terminal-default
python3 tests/search/terminal.py --tiny --binary target/remediation-2026-11-06/daybreak-final5-frozen/naro-tiny --out target/remediation-2026-11-06/daybreak-final5-search-terminal-tiny
python3 tests/undo/stress.py --out target/remediation-2026-11-06/daybreak-final5-undo
python3 tests/robustness/run_native.py --runs 100000 --out target/remediation-2026-11-06/daybreak-final5-native-fuzz
python3 tests/catalog/run.py --binary target/daybreak-final5-test-default/debug/deps/naro-8b785946e7ffb0d9 --out target/remediation-2026-11-06/daybreak-final5-catalog-default
python3 tests/catalog/run.py --binary target/daybreak-final5-test-tiny/debug/deps/naro-92b0cf5a83e9781f --out target/remediation-2026-11-06/daybreak-final5-catalog-tiny
python3 tests/remediation/regex.py --binary target/remediation-2026-11-06/daybreak-final5-frozen/naro-default --out target/remediation-2026-11-06/daybreak-final5-regex-default
python3 tests/remediation/regex.py --binary target/remediation-2026-11-06/daybreak-final5-frozen/naro-tiny --out target/remediation-2026-11-06/daybreak-final5-regex-tiny
python3 tools/check_branding.py --binary target/remediation-2026-11-06/daybreak-final5-frozen/naro-default --profile default --out target/remediation-2026-11-06/daybreak-final5-branding-default
python3 tools/check_branding.py --binary target/remediation-2026-11-06/daybreak-final5-frozen/naro-tiny --profile tiny --out target/remediation-2026-11-06/daybreak-final5-branding-tiny
python3 tools/measure_profiles.py --full target/remediation-2026-11-06/daybreak-final5-frozen/naro-default --tiny target/remediation-2026-11-06/daybreak-final5-frozen/naro-tiny --out target/remediation-2026-11-06/daybreak-final5-profiles
NANOSPEC_WORK=/home/john/Code/naro/target/remediation-2026-11-06/daybreak-final5-tiny-ci-work python3 tools/check_tiny_ci.py --binary target/remediation-2026-11-06/daybreak-final5-frozen/naro-tiny --out target/remediation-2026-11-06/daybreak-final5-tiny-ci
python3 tools/check_large_files.py --binary target/remediation-2026-11-06/daybreak-final5-frozen/naro-default --out target/remediation-2026-11-06/daybreak-final5-large
python3 tests/backup/run_namespace.py target/daybreak-final5-test-default/debug/deps/naro-8b785946e7ffb0d9
```

`naro-credits --credits > daybreak-final5-credits.txt`, `cmp -s CREDITS.md
daybreak-final5-credits.txt`, and `sha256sum` proved byte equality. Running
`python3 tests/nanorc/issue11_differential.py --help` invoked that script's
argument-free test entry point rather than help; all nine bounded configuration
comparisons passed. This operator surprise is recorded, not repeated as a help
claim.

## Differential inventories

```sh
NANOSPEC_WORK=/home/john/Code/naro/target/remediation-2026-11-06/daybreak-final5-diff-default-work python3 tests/remediation/differential.py --binary target/remediation-2026-11-06/daybreak-final5-frozen/naro-default --reference /home/john/src/nano-install/default/bin/nano --root-reference target/root-reference/install/bin/nano --profile default --jobs 8 --out target/remediation-2026-11-06/daybreak-final5-diff-default
NANOSPEC_WORK=/home/john/Code/naro/target/remediation-2026-11-06/daybreak-final5-diff-tiny-work python3 tests/remediation/differential.py --binary target/remediation-2026-11-06/daybreak-final5-frozen/naro-tiny --reference /home/john/src/nano-install/tiny/bin/nano --profile tiny --jobs 8 --out target/remediation-2026-11-06/daybreak-final5-diff-tiny
```

Both commands exited 1 from their explicit nonaccepted raw classifications;
they accounted every expected case. Counts and dispositions are in the main
report and receipt.

## Packaging

```sh
git clone --no-local --no-hardlinks . target/remediation-2026-11-06/daybreak-final5-package-source
git -C target/remediation-2026-11-06/daybreak-final5-package-source checkout --detach 2888560a9a2709469334a417d1ad9ac3a91c30ba
git -C target/remediation-2026-11-06/daybreak-final5-package-source fsck --full
```

The clone was clean and had no alternates. From that clone, both package
commands exited 0:

```sh
python3 tools/package.py --binary /home/john/Code/naro/target/remediation-2026-11-06/daybreak-final5-frozen/naro-default --out /home/john/Code/naro/target/remediation-2026-11-06/daybreak-final5-package-default
python3 tools/package.py --binary /home/john/Code/naro/target/remediation-2026-11-06/daybreak-final5-frozen/naro-tiny --features tiny --out /home/john/Code/naro/target/remediation-2026-11-06/daybreak-final5-package-tiny
```

The first two `check_package.py` commands ran concurrently without separate
`NANOSPEC_WORK` roots, collided in a catalog fixture, and exited 1 at 14/15
package checks and 40/44 asset checks. Those directories are preserved. These
sequential corrections exited 0 at 15/15 package checks and 44/44 asset checks
each:

```sh
NANOSPEC_WORK=/home/john/Code/naro/target/remediation-2026-11-06/daybreak-final5-package-work-default python3 tools/check_package.py --archive /home/john/Code/naro/target/remediation-2026-11-06/daybreak-final5-package-default/naro-0.1.2-x86_64-unknown-linux-gnu.tar.gz --source-archive /home/john/Code/naro/target/remediation-2026-11-06/daybreak-final5-package-default/naro-0.1.2-source.tar.gz --out /home/john/Code/naro/target/remediation-2026-11-06/daybreak-final5-package-check-default-attempt02
NANOSPEC_WORK=/home/john/Code/naro/target/remediation-2026-11-06/daybreak-final5-package-work-tiny python3 tools/check_package.py --archive /home/john/Code/naro/target/remediation-2026-11-06/daybreak-final5-package-tiny/naro-0.1.2-x86_64-unknown-linux-gnu.tar.gz --source-archive /home/john/Code/naro/target/remediation-2026-11-06/daybreak-final5-package-tiny/naro-0.1.2-source.tar.gz --out /home/john/Code/naro/target/remediation-2026-11-06/daybreak-final5-package-check-tiny-attempt02
```

## Ubuntu

```sh
git clone --no-local --no-hardlinks . target/remediation-2026-11-06/ubuntu-source-final5
git -C target/remediation-2026-11-06/ubuntu-source-final5 checkout --detach 2888560a9a2709469334a417d1ad9ac3a91c30ba
git -C target/remediation-2026-11-06/ubuntu-source-final5 fsck --full
python3 target/remediation-2026-11-05/ubuntu-launch.py --source target/remediation-2026-11-06/ubuntu-source-final5 --out target/remediation-2026-11-06/ubuntu-final5 --commit 2888560a9a2709469334a417d1ad9ac3a91c30ba --source-sha256 7b6ef4e024bc5d25f59fb66eebad7f8297d4be4f49a34d1037c3b8d4f928e636
```

The launcher exited 0. Its internal default/tiny differential commands exited
1 with fully recorded raw dispositions; regex and explicit semantics exited 0.
The exact command, image, mounts, stage statuses, and network isolation are in
`ubuntu-final5/launch.json`.

The additional network-disabled Ubuntu issue #3 command mounted the same clean
source read-only, the final5 results writable, the pinned Rust toolchain
read-only, and ran `bash /qualification.sh` using
`target/remediation-2026-11-06/ubuntu-issue3-inner.sh`. It exited 0 after:

- building exact default/tiny Rust test executables and hook variants;
- safe-save 378/378 per profile with three explicitly logged supplementary
  group skips per profile;
- backup 1200/1200;
- recovery 41/41 per profile;
- open-gate unit tests 7/7; and
- tiny CI 195/195.

## Diagnostic-only commands

Read-only `sed`, `rg`, `find`, `tail`, JSON-inspection snippets, `git status`,
`git rev-parse`, `git rev-list`, `sha256sum`, `stat`, `--help`, and version
commands were used to inspect instructions, receipts, runner interfaces,
recordings, hashes, and live Ubuntu progress. One environment wrapper first
reported bare `rustc: command not found` and then successfully used
`/home/john/.cargo/bin/rustc`. One broad package `sha256sum .../*` invocation
returned 1 for the two extracted-package directories while hashing all regular
files; exact archive hashes were still recorded. Neither diagnostic error was
treated as product evidence.

## Adapted historical fault boundaries and clean negative control

Sol 6.1/high ran the following from the repository root; both exited 0:

```sh
python3 target/remediation-2026-11-06/final5-adapted-faults/verify.py
python3 target/remediation-2026-11-06/final5-adapted-faults/negative-control.py
```

The first invoked `nanoharness.py` on disposable candidate-only scenario copies
and final5, producing 6/6 cases, 67/67 steps, 52/52 harness assertions, all
intended syscall markers, and all inode/link/fallback-home checks. The second
created a detached worktree at `2c63ec3`, appended only the preserved regression,
built it offline, observed the expected exit 101 and empty aliased source, then
ran the identical test against final5 with exit 0. Exact nested commands and
hashes are in `validation/final5-adapted-faults-2026-11-06.md`.
