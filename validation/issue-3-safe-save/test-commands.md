# Test-agent command record

Working directory `/home/john/Code/naro`. Rust commands used
`PATH=/home/john/.cargo/bin:$PATH`. Local evidence remains under ignored target/.
No installation, credentials, editor replacement or publishing occurred.

- `python3 -m py_compile tests/safe-save/run.py` — pass.
- `cc -shared -fPIC -Wall -Wextra -Werror tests/safe-save/faults.c -ldl -o /tmp/naro-save-faults-check.so` — pass, repeated after adding read/metadata faults.
- Python exclusively created target/issue-3-old-behavior, piped `git archive HEAD` to `tar -x -C target/issue-3-old-behavior`, copied only src/safe_save_tests.rs and appended its cfg(test) module declaration to old files.rs — pass. Old production code remained HEAD.
- `cargo test --manifest-path target/issue-3-old-behavior/Cargo.toml --no-run --message-format=json > target/issue-3-old-behavior/build.jsonl` — pass.
- Python selected the executable from Cargo JSON and ran `python3 tests/safe-save/run.py --binary <old test executable> --out target/issue-3-old-regression --regression-only` — expected exit 1: 0/3 preservation assertions pass; injected file-sync EIO modified overwrite, append and prepend originals. Wrapper recorded expected failure and exited 0.
- `cargo test --no-run --message-format=json > target/issue-3-tests-build.jsonl` — pass, repeated after production and fixture changes.
- `python3 tests/safe-save/run.py --binary <default executable> --out target/issue-3-fault-matrix-01` — 335/335 pass. Intermediate matrix later removed redundant missing-prepend fault cases.
- `cargo test --features tiny --no-run --message-format=json > target/issue-3-tests-tiny-build.jsonl` — pass, repeated after production and fixture changes.
- Default/tiny runner invocations with --out target/issue-3-fault-matrix-02 and target/issue-3-fault-matrix-tiny-02 — pass; logs target/issue-3-faults-02.log and target/issue-3-faults-tiny-02.log. Added supplementary-group ownership coverage.
- `rustfmt src/safe_save_tests.rs` — pass.
- `python3 -m py_compile tests/safe-save/run.py tests/safe-save/progress_cases.py` — pass.
- Repeated both Cargo no-run builds after production collision guard and fixture were complete — pass.
- `python3 tests/safe-save/run.py --binary /home/john/Code/naro/target/debug/deps/naro-f143b0d4013ffd62 --out target/issue-3-fault-matrix-03` — 414/414 pass; log target/issue-3-faults-03.log; SHA256 8d67444b6bb6ce8ab9dbf968610dd2a7b7a4e9b9890611e865da4a027ea27e35.
- `python3 tests/safe-save/run.py --binary /home/john/Code/naro/target/debug/deps/naro-72a4835848d83bb3 --out target/issue-3-fault-matrix-tiny-03` — 414/414 pass; log target/issue-3-faults-tiny-03.log; SHA256 d7bd1d315720e736975dfd4516041e8519b1aa436743882ccdfe91a0ef2e47e4.

Each runner executes its report.json compiler_command, then the selected test
binary with `--exact files::safe_save_tests::fixture_save --nocapture`, umask 027,
fixture-only LD_PRELOAD, NARO_SAVE_FIXTURE, NARO_SAVE_MODE, NARO_SAVE_FAULT and
NARO_SAVE_COLLISION=1 for collision cases. Abrupt boundary cases deliberately
return 99; they are not ordinary successful editor exits.

## Terminal commands

- `cargo build --release --target-dir target/issue-3-terminal-build` — pass; intermediate build before collision fix.
- `python3 tests/safe-save/progress_cases.py > target/issue-3-save-progress-candidate.json` — initial explicit gate-source assertion failed on different FIFO helper; after restricting adaptation, pass.
- `python3 tests/safe-save/progress_cases.py save-safety > target/issue-3-save-safety-candidate.json` — pass.
- `NANOSPEC_WORK=/home/john/Code/naro/target/issue-3-terminal-work python3 spec/tools/nanoharness.py target/issue-3-save-progress-candidate.json target/issue-3-save-safety-candidate.json --binary target/issue-3-terminal-build/release/naro --out target/issue-3-terminal-candidate-01 > target/issue-3-terminal-01.log 2>&1` — exit 1. Three fallback cases assumed success with a read-only parent but atomic temp creation correctly failed; opening progress timing also intentionally differs. Failed evidence retained.
- Regenerated overlays with the same generator commands into target/issue-3-save-progress-candidate-02.json and target/issue-3-save-safety-candidate-02.json — pass.
- `NANOSPEC_WORK=/home/john/Code/naro/target/issue-3-terminal-work-02 python3 spec/tools/nanoharness.py target/issue-3-save-progress-candidate-02.json target/issue-3-save-safety-candidate-02.json --binary target/release/naro --out target/issue-3-terminal-candidate-02 > target/issue-3-terminal-02.log 2>&1` — exit 1, 31/32 scenarios pass. Only three opening-progress screen expectations differed: Writing status now appears before transaction open. Explicitly updated these cells/cursor; all original bytes and final errors already passed.
- `python3 tests/safe-save/progress_cases.py > target/issue-3-save-progress-final.json` and `python3 tests/safe-save/progress_cases.py save-safety > target/issue-3-save-safety-final.json` — pass.
- `NANOSPEC_WORK=/home/john/Code/naro/target/issue-3-terminal-work-final python3 spec/tools/nanoharness.py target/issue-3-save-progress-final.json target/issue-3-save-safety-final.json --binary target/issue-3-2026-11-05/frozen/naro --out target/issue-3-terminal-final > target/issue-3-terminal-final.log 2>&1` — final result appended below.

Read-only inspection used rg, sed, cat, head, tail, find, wc, ps, git status and
Python JSON summaries for instructions, source, fixtures, render layout, test
progress and hashes. No historical scenario, recording or comparator was edited.

Final frozen terminal result: exit 0, **32/32 scenarios; 1718/1718 checks pass**. Executable SHA256 `14c1506baae0450c14c50377e08b67dc380a107b44a5004ce142ce96be487a72`. Summary `target/issue-3-terminal-final/report.json`, raw evidence retained per scenario.

Final `python3 -m py_compile tests/safe-save/run.py tests/safe-save/progress_cases.py` and `git diff --check` both passed. Python removed only this task's pycache files and /tmp/naro-save-faults-check.so.
