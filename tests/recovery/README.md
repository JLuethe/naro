# Emergency-save durability regressions

`run.py` starts only the supplied test-hooks binary in private PTYs and disposable
directories. It uses the existing `NARO_TEST_PANIC_DIR` acknowledgment/trigger
and `tests/safe-save/faults.c` syscall interposer. No production hooks or global
installation are added. Linux `/proc/self/fd` is required by the interposer.

```sh
cargo build --offline --locked --features test-hooks --target-dir target/recovery-hooks
python3 tests/recovery/run.py --binary target/recovery-hooks/debug/naro --out target/recovery-results
cargo build --offline --locked --features tiny,test-hooks --target-dir target/recovery-tiny-hooks
python3 tests/recovery/run.py --tiny --binary target/recovery-tiny-hooks/debug/naro --out target/recovery-tiny-results
```

Each output directory must be fresh. The driver records executable/interposer/
driver SHA-256 hashes, each check, exit status, stderr, raw terminal output,
actual recovery files and syscall events. Failures exit nonzero.

The matrix covers panic, SIGHUP and SIGTERM with successful/short/interrupted
writes and interrupted sync; create, zero/partial/error writes, ENOSPC, file-sync,
checked-close and directory-sync errors. Every outcome checks visible reporting
and on-disk bytes, original preservation and mode 0600 where applicable.
Success additionally requires file sync, checked close and directory sync in
order. Named, relative, nameless, collision, restricted and unmodified buffers
are covered. `--regression-only` selects the three original durability defects
so the same expectations can demonstrate old-code failure/new-code success.
