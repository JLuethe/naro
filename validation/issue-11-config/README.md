# Issue #11 nanorc compatibility validation

Run from `/home/john/Code/naro` on 2026-11-05. Pinned GNU nano 9.3:
`/home/john/src/nano-install/default/bin/nano` (SHA-256
`b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2`).
NARO candidate `target/debug/naro` SHA-256 during the differential run:
`ef94b4ea1edd914d3a761bbe95179f94e93b073b26c9b8281439640dcb196db9`.
Host glibc: 2.44. Base commit: `03aee41032df81384eda2589f4a8fed133b486e6`.
The working tree also contained concurrent uncommitted remediation work; these
results apply to the stated binary and source hashes, not a release build.

| Command | Result |
| --- | --- |
| `cargo test nanorc_regressions` | 6 passed, 0 failed |
| `cargo test` | 42 passed, 0 failed, 9 ignored by separate fixture gates |
| `cargo clippy --all-targets -- -D warnings` | passed |
| `rustfmt --edition 2024 --check src/config.rs` | passed |
| `python3 tests/nanorc/issue11_differential.py` | five comparisons passed |

The differential script asserts exact `--listsyntaxes` output for bracket
classes in filenames and directory names and isolated system plus first user
rcfile lookup. It asserts nano's exact deferred file/line diagnostic for a
malformed UTF-8 value. In the C locale it uses a non-UTF-8 `operatingdir`
pathname and asserts that both editors open and display a marker file there.
System rcfiles are injected with rootless `bwrap` mounts. The pinned nano
binary is copied byte-for-byte to a disposable fixture because its compiled
sysconfdir is inside the pinned installation prefix. No host `/etc` writes
occur. Transient fixtures and the copied binary stay under
`target/issue-11-config`.

Pre-fix behavior was reproduced from a clean archive of the base commit under
`target/issue-11-config/baseline-source`, built to
`target/issue-11-config/baseline-target/debug/naro` (SHA-256
`264cd5e20ff8bd2bcaeb29147a13e8598d9bf399c5ec9504d430537062f558ac`).
`target/issue-11-config/baseline_repro.py` and `baseline-results.json` retain
the disposable repro and outputs: both bracket patterns produced no syntax
list, the malformed UTF-8 argument produced no required error, the byte-locale
directory failed with a replacement character, and the system syntax was
absent. The pinned binary and original reference recordings were unchanged.

Source hashes at this run: `src/config.rs`
`60cb62c92f8e00cd409d919d7c632606bb950e0eb66987a57a8e04c41f3ba267`;
`tests/nanorc/issue11_differential.py`
`807382cb6f15095134ec99e94c26335870fbf2fb5b21e2cdccd496d1ce789e0e`.
