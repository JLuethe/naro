# Issue #12 — opened-object confinement hardening

Follow-up: [bounded interleaving evidence (2026-11-06)](bounded-2026-11-06/README.md)
now exercises the entry-swapping items. The original results below remain a
historical record of the earlier implementation and tests, not the current
coverage claim.

Date: 2026-11-05. This is defensive remediation of the issue's source-supported
hypothesis. **No symlink-swap, rename-exchange, adversarial race, or exploit
reproduction was constructed or executed.** The issue's requested race proof
and associated acceptance items remain unverified; these results do not prove
an exploitable vulnerability or complete that investigation.

The [policy](../../docs/operating-directory.md) documents Linux openat2 and
procfs requirements, authorized-at-open directory capabilities, intended relative
symlink workflows, confined special-file refusal, and external-tool trust. The
implementation pins startup authority, authorizes reads and metadata together,
passes an opened parent to safe-save, anchors confined backups/locks/recovery,
and obtains browser/completion names from authorized directory streams.

## Commands and observed results

Commands ran from `/home/john/Code/naro` with Cargo at
`/home/john/.cargo/bin/cargo` (the shell PATH did not include Cargo). All fixture
paths were beneath `target/`; no real documents or installed editor were used.

| Command | Result |
| --- | --- |
| `cargo test --offline confinement` | 10 passed: startup root descriptor/chdir, regular reads with matching metadata, contained relative symlinks, missing-parent and missing-authority refusal, outside paths, all save modes/new files/final save-link refusal, sidecar/configured backups, recovery/lock operations, authorized directory enumeration, FIFO refusal before data open, and shared ordinary save operations |
| `cargo test --offline --features tiny confinement` | 1 shared opened-parent save/append/metadata/remove test passed. Tiny has no operating-directory option; confined feature tests are explicitly excluded, not claimed as tiny coverage |
| `cargo test --offline backup_tests` | 2 passed; 2 namespace-specific cases explicitly ignored by this command; separate issue #9 evidence records their dedicated runs |
| `cargo clippy --offline --all-targets --all-features -- -D warnings` | Passed |
| `cargo fmt --check` | Passed |
| `python3 tests/safe-save/run.py --binary <default-test-executable> --out target/remediation-2026-11-05/issue12/safe-save` | 414/414 passed |
| Same runner with the tiny test executable and `--out .../tiny-safe-save` | 414/414 passed |
| `cargo build --offline --features test-hooks` then `python3 tests/recovery/run.py --binary target/debug/naro --out .../recovery` | 41/41 UI/disk checks passed |
| `cargo build --offline --features tiny,test-hooks` then recovery runner with `--tiny --out .../tiny-recovery` | 41/41 UI/disk checks passed |

Test executables for the save matrices came from
`cargo test --offline [--features tiny] --no-run --message-format=json`; their
exact paths and hashes are retained in [matrix-artifacts.json](matrix-artifacts.json).
The full matrices were run after parent-relative save/recovery changes and
before the final browser and O_PATH regular-read additions. Final focused tests
and Clippy cover those additions. The matrices therefore describe their recorded
intermediate binaries, not a final release qualification or an inherited pass
for a later binary.

## Raw evidence and limits

Raw output is under `target/remediation-2026-11-05/issue12/`: `default-final.log`,
`tiny-final.log`, `backup-final.log`, `clippy-final.log`, `fmt.log`, four matrix
output directories with reports/process logs, Cargo build records,
`environment.json`, and `compile-inputs.json` (working-tree input hashes at the
final focused validation boundary). The parent integration is concurrent work;
these records do not claim a clean final commit or a release artifact.

Initial failed attempts are retained as `attempt01-default.log`,
`attempt01-tiny.log`, and `attempt01-clippy.log`. The first exposed invalid
O_PATH/openat2 flag combination and was corrected. The latter exposed an
incorrect attempt to claim a feature absent from tiny, plus its unused test
import; tiny now runs only applicable shared operations. None is counted as a
pass. Startup and native lookups propagate unsupported-kernel/header/policy and
procfs errors without fallback; unavailable-kernel/procfs environments were not
separately exercised on this host. The directory API is tested directly;
full interactive browser differential coverage was not added in this issue.
