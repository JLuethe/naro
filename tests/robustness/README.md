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

`python3 tests/robustness/terminal_resources.py --binary target/release/naro
--expected-revision "$(git rev-parse HEAD)" --out target/resources-NEW` opens
synthetic 12 MiB and eight 2 MiB documents in a real production editor PTY.
It checks buffer navigation, a clean exit, unchanged source hashes and the
actual child peak RSS and elapsed time. The fixed gates are 128 MiB peak RSS,
512 MiB address space and 30 seconds. Tiny runs the large-file case only;
its retained feature set does not include multiple buffers. The runner keeps
the executable hash, embedded build identity, linked native libraries, input
hashes, raw terminal traces, and `report.json`. Supply `--tiny` for a tiny
release binary. Both runners require the exact production feature set (empty
for default, `tiny` for tiny) and reject instrumented or extension builds.
Use a new private `--out` directory each run. These bounds
describe this fixture size and host class, not arbitrary files or load.

`python3 tests/robustness/hostile_inputs.py --binary target/release/naro
--expected-revision "$(git rev-parse HEAD)" --out target/hostile-NEW` compiles
a private valid GNU catalog control and exercises an empty catalog, truncated
header and invalid magic in real editor PTYs. It requires `msgfmt` and a
working `en_US.UTF-8` locale, including a warning-free UTF-8 charmap probe.
The default profile also exercises an invalid UTF-8 byte in a private nanorc
and checks the precise diagnostic. Tiny runs catalog checks only. Cases must
exit cleanly and leave the source file unchanged. The report records exact
executable/native library identities, fixture hashes, probes, observations and
per-case raw traces. A missing locale or `msgfmt` is a prerequisite failure.
These fixed benign malformed inputs do not establish general parser safety.

The CI workflow runs both production-editor gates for default and tiny release
builds. Existing search/replace, undo and native-bridge sanitizer gates remain
separate. A passing local or CI run applies only to the recorded executable;
it does not constitute physical power-loss, another-architecture, or
guest-VT qualification.
