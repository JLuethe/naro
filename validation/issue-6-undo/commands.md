# Commands and outcomes

Working directory: `/home/john/Code/naro`. Toolchain:
`/home/john/.cargo/bin/{cargo,rustc,rustfmt}`. Outputs below are preserved; no
failed or superseded replay was counted as a pass.

## Inspection and implementation

Read `CONTRIBUTING.md`, `spec/00-overview.md`, `spec/05-buffer-and-editing.md`,
`spec/06-undo-redo.md`, `spec/18-bytes-encoding-and-coordinates.md`,
`validation/wrap-undo/README.md`, issue #6 in
`target/remediation-2026-11-05/issues.json`, and the buffer/edit/wrap/search
callers. Used `rg --files`, `rg -n`, `sed -n`, `cat`, and `git diff` for discovery
and review. `find .. -name AGENTS.md -print` found no applicable instruction
file; unrelated sibling test fixtures denied access. No sibling file was
modified. Changes used `apply_patch`, followed by `rustfmt` on owned files.

## Development checks and retained attempts

Logs mentioned in this section are under
`target/issue-6-undo/intermediate/` after final consolidation.

| Command | Outcome / artifact |
| --- | --- |
| `cargo test --no-default-features buffer::tests -- --nocapture` | Initial compile failed on the coordinated search caller's old `history.last_mut()` API; `initial-test.log`. Search owner changed to `back_mut()` and mutable `begin()`. |
| `cargo test buffer::tests -- --nocapture` | 9 passed; `buffer-test-01.log`. |
| `cargo test --all-features buffer::tests` | 2 tiny buffer tests passed; `tiny-test-01.log`. |
| `cargo test buffer::tests` | 9, then 11, then 11 passed after successive implementation/test changes; `buffer-test-02.log`, `buffer-test-03.log`, `buffer-test-04.log`. |
| `cargo build --release --target-dir target/issue-6-undo/build-01` | Successful preliminary shared-tree build; `build-01.log`. Not used for qualification. |
| `cargo build --release --manifest-path target/issue-6-undo/source-01/Cargo.toml --target-dir target/issue-6-undo/build-02` | Successful preliminary frozen build; `build-02.log`. |
| `cargo build --release --manifest-path target/issue-6-undo/source-02/Cargo.toml --target-dir target/issue-6-undo/build-03` | Successful frozen build; `build-03.log`. |
| `cargo build --release --manifest-path target/issue-6-undo/source-03/Cargo.toml --target-dir target/issue-6-undo/build-04` | Successful frozen build; `build-04.log`. Superseded by final source including additional budget tests. |
| `python3 tests/undo/stress.py --baseline f5e79cf --out validation/issue-6-undo/stress-01` | Infrastructure failure: `/usr/bin/time` absent. Source/binary retained at `target/issue-6-undo/stress-01`; no measurement claimed. Runner changed to Linux `wait4`, no package installed. |
| `python3 tests/undo/stress.py --baseline f5e79cf --out target/issue-6-undo/stress-02` | Expected old failure/new pass, exit 0; `stress-02.log` and raw output directory. |
| Same command with `stress-03`, then `stress-04` | Expected old failure/new pass, exit 0 for each; reruns follow buffer changes. |
| `cargo clippy --all-targets --all-features -- -D warnings` | First two runs failed on concurrent issue #7 warnings; `clippy-01.log`, `clippy-02.log`. Third passed, `clippy-03.log`. |
| `cargo clippy --all-targets -- -D warnings` | First failed on two new test initializer style warnings, fixed; second passed. `clippy-default-01.log`, `clippy-default-02.log`. |
| `cargo test`; `cargo test --all-features` | 32 and 22 passed respectively, 5 explicit search stress ignores each; `full-test-01.log`, `all-features-test-01.log`. Superseded by final checks. |

Frozen copies were created using Python `shutil.copytree`/`copy2` for
`src`, `native`, `assets`, tools, test/scenario/identity-policy support,
`Cargo.toml`, `Cargo.lock`, `build.rs`, and `CREDITS.md`. SHA-256 manifests were
written for every frozen file. Later snapshots preserve their predecessors;
only owned final buffer/features inputs were refreshed for the final snapshot.

The first wrap runner invocation (`source-02`, `wrap-01`, private
`wrap-work-01`) stopped before running either binary because the isolated
snapshot lacked `docs/NARO_IDENTITY_POLICY.md`. The missing verification
support files were copied and hashed in
`source-02-validation-support.json`; expectations and normalization were not
changed. The fresh `wrap-02` run accepted all 58 cases, and
`source-02/tools/check_wrap_undo.py --report target/issue-6-undo/wrap-02/report.json`
passed. `filter-01` accepted all six cases. These preliminary raw runs remain
under `target/issue-6-undo/`, with their logs in `intermediate/`.

## Final validation

The exact unit/lint/format commands, individual exit statuses, elapsed times
and log paths are in [final-checks.json](final-checks.json).

```sh
/home/john/.cargo/bin/cargo build --release --manifest-path target/issue-6-undo/source-04/Cargo.toml --target-dir target/issue-6-undo/build-05
python3 tests/undo/stress.py --baseline f5e79cf --out target/issue-6-undo/stress-05
env NANOSPEC_WORK=/home/john/Code/naro/target/issue-6-undo/wrap-work-final python3 target/issue-6-undo/source-04/tools/check_follow_up.py --suite wrap-undo --binary target/issue-6-undo/build-05/release/naro --out target/issue-6-undo/wrap-final
env NANOSPEC_WORK=/home/john/Code/naro/target/issue-6-undo/filter-work-final python3 target/issue-6-undo/source-04/tools/check_follow_up.py --suite filter --binary target/issue-6-undo/build-05/release/naro --out target/issue-6-undo/filter-final
cp spec/evidence/scenarios/undo.json target/issue-6-undo/source-04/tests/follow-up/scenarios/issue6-undo.json
env NANOSPEC_WORK=/home/john/Code/naro/target/issue-6-undo/undo-work-final python3 target/issue-6-undo/source-04/tools/check_follow_up.py --suite issue6-undo --binary target/issue-6-undo/build-05/release/naro --out target/issue-6-undo/undo-final
python3 target/issue-6-undo/source-04/tools/check_wrap_undo.py --report target/issue-6-undo/wrap-final/report.json
git diff --check -- src/buffer.rs src/features.rs spec/06-undo-redo.md
```

Use new `--out`, `NANOSPEC_WORK` and snapshot paths when repeating these commands;
the runners intentionally refuse to overwrite prior evidence. Final outcomes
and hashes are in [summary.json](summary.json). The additional baseline undo
scenario is an unchanged copy; its hash is recorded in the final summary.
