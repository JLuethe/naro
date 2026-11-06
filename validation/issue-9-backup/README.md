# Issue 9: backup metadata validation

Source: `target/remediation-2026-11-05/issues.json`, SHA-256
`e3d66ed124afd1b1018b44830a67961086d93d810872a764d55dd360a429909a`.
The extracted issue is `issue-9.json`, SHA-256
`52e87e103e39f7dd3ac14d85930d5ba85d0780e40e0169c12e9f29e5dfa9add7`.

## Before fix

Detached checkout `target/issue-9-baseline-src` at commit `03aee41` kept the
original `make_backup`. Only the test module/registration and its native
ownership setup helper were copied into that isolated checkout.

`/home/john/.cargo/bin/cargo test --offline backup_preserves_supplementary_group_setid_and_times -- --nocapture`
failed: backup UID/GID `(1000,1000)` versus source `(1000,998)`.
After commenting out that assertion in the baseline test copy only, the same
command failed on final mode: backup `0o750` versus source `0o6750`.
No baseline production behavior was changed.

## After fix

The staged issue-9-only tree was `8a7e3a58a3dffac1a685dfc4d0d14f619c19f3ed`,
archived to `target/issue-9-index-src`. Its test binary SHA-256 was
`cc4dbcc299c890ecab110766d7675c375c592396efe0e45706c7fb4c70b08b18`.
`/home/john/.cargo/bin/cargo test --offline backup_tests -- --nocapture`
there passed 2 tests (current-owner set-ID/timestamps and supplementary-group
UID/GID/set-ID/timestamps), with 2 namespace-only tests separately executed
below. The supplementary fixture used host group 998. A missing supplementary
group is a test failure rather than a silent pass. The combined tree, after
issue-12 confinement integration, also passed the same focused test command:
2 passed, 2 namespace-only ignored, 0 failed.

| Command | Result |
|---|---|
| `podman run --rm --user 0 --security-opt label=disable -v "$PWD":/work:rw -w /work -e NARO_BACKUP_ROOT_NAMESPACE=1 localhost/naro-followup:ubuntu24 ./target/debug/deps/naro-f143b0d4013ffd62 --ignored --exact files::backup_tests::backup_preserves_foreign_owner_in_private_root_namespace --nocapture` | 1 passed: exact foreign UID/GID, mode 06750, and timestamps |
| `podman run --rm --user 1000 --security-opt label=disable -v "$PWD":/work:rw -w /work -e NARO_BACKUP_DENIED_SOURCE=target/issue-9-backup-fixtures/denied/source localhost/naro-followup:ubuntu24 ./target/debug/deps/naro-f143b0d4013ffd62 --ignored --exact files::backup_tests::backup_warns_when_foreign_ownership_is_denied --nocapture` | 1 passed: ownership warning and complete backup |
| `python3 spec/tools/test_compare_runs.py` | 15 passed, including backup UID/GID source relationship |
| `python3 tests/backup/run_namespace.py target/issue-9-index-src/target/debug/deps/naro-f143b0d4013ffd62` | 2 namespace tests passed, 0 skipped; runner verifies each `--list` entrypoint and exactly one executed test, and requires rootless Podman/image |
| `/home/john/.cargo/bin/cargo fmt --check` | passed in the isolated issue-9 tree |
| `/home/john/.cargo/bin/cargo clippy --offline --all-targets --all-features -- -D warnings` | passed in the isolated issue-9 tree |

The uid 0 case used rootless Podman, never host root. For the uid 1000 case,
the isolated fixture was prepared in the same container image as uid 0: a
`denied` directory with mode 0777 and a source file with bytes
`foreign owned bytes\n`, mode 0644, owner 1234:1235. The fixture was removed
after the test. Both namespace tests were rerun against the isolated issue-9
tree's binary above and passed.

After concurrent confinement and config edits settled, the combined tree also
passed `/home/john/.cargo/bin/cargo fmt --check` and
`/home/john/.cargo/bin/cargo clippy --offline --all-targets --all-features -- -D warnings`.
