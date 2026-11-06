# Bounded robustness checks

`python3 tests/robustness/run_native.py --out target/native-NEW` compiles the
actual native bridge with Clang libFuzzer, AddressSanitizer and
UndefinedBehaviorSanitizer in default and tiny configurations. Each runs
100,000 inputs, up to 4096 bytes, with a two-second per-input timeout, 512 MiB
RSS limit and 90-second process limit. Missing Clang/runtime support fails the
command. Source and executable hashes, commands and raw output are retained.
Fixed benign regex patterns exercise capture offsets and byte helpers with
arbitrary input bytes, including embedded NUL and UTF-8. This does not fuzz
filesystem races, terminal operations, arbitrary regex patterns, or all Rust
code. Native libraries themselves are not rebuilt with sanitizers.

`cargo test bounded_arbitrary_bytes_preserve_coordinate_progress` checks
byte/UTF-8 cursor progress and reverse-boundary invariants over deterministic
arbitrary byte strings. `python3 tests/undo/stress.py --out target/undo-NEW`
also covers a 10 MiB buffer with 210,000 edits and eight simultaneous 4 MiB
buffers with 1000 edits and complete undo each. Its limits are 15 seconds,
256 MiB address space and 96 MiB peak RSS. The standalone harness uses real
buffer/byte modules with unused native declarations and a field-identical lock
holder declaration; exercised paths do not call these stubs.

These checks supplement exact executable terminal qualification; they do not
transfer a result from an instrumented binary to an unrecorded release build.
