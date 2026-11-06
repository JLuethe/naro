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

## C-locale String boundary follow-up

An integrated review of frozen `d096a7465ca6f84c4f3989cccba8c018abfa469b`
found a later issue #11 regression: `syntax café` in a C locale printed
private-use placeholder bytes under `-z`. The review record is
`target/remediation-2026-11-05/integrated-review-byte-names/report.json`.
Additional bounded baseline runs used the same frozen default binary (SHA-256
`dba4ffdccc5f80f2d7d6ae3ad383f8d2d30d8a88bdca6c48f7eb593fb6c0d293`).
`target/issue-11-config/byte-boundary-baseline.py` and
`byte-boundary-baseline.json` retain the fixtures and outputs: the syntax name
printed encoded placeholders; a binding saved `41ee83bf420a` instead of
`41ff420a`; a formatter left `top` unchanged; and a linter was not invoked.

The follow-up keeps syntax names, binding expansions, and formatter/linter
commands as raw bytes at their output or execution boundaries. Syntax display
errors escape invalid bytes instead of inserting replacement characters.
The nanorc regression module is gated out of tiny builds, which have no nanorc
support. The generated Binding type and its generator now agree on byte
expansions.

Follow-up validation on 2026-11-05:

| Command | Result |
| --- | --- |
| `cargo test nanorc_regressions` | 9 passed, 0 failed |
| `cargo test` | 57 passed, 0 failed, 10 separately gated tests ignored |
| `cargo test --features tiny` | 28 passed, 0 failed, 10 separately gated tests ignored |
| `cargo test --all-features` | 28 passed, 0 failed, 10 separately gated tests ignored; nanorc module excluded by tiny gate |
| `cargo fmt --check` | passed |
| `cargo clippy --all-targets --all-features -- -D warnings` | passed |
| `python3 tests/nanorc/issue11_differential.py` | 9 pinned nano comparisons passed |

The added comparisons assert the exact C-locale syntax name bytes, the saved
file bytes after a bound string is expanded, a formatter's on-disk transform,
and a linter's marker file. Both programs run from ordinary disposable
nanorc/file fixtures under `target/issue-11-config`; no user or system
configuration is changed. The candidate binary for the nine comparisons had
SHA-256 `93e7ddfed948cc7767f25d0445600b64e4f3699358a95a5130bca1cfe44cd514`.
`src/config.rs` SHA-256 was
`9ad91d8aca93689d9d9c915b7601ffc28f94e2aa0e207f5189f882cf89d7312b`,
and `tests/nanorc/issue11_differential.py` SHA-256 was
`710296a264b184887c53efba27bb7d9f1ba053b0d5b836e63f44a5ab24a5c693`.
