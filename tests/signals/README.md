# Signal delivery regressions

Run from the repository root, with fresh output directories:

```sh
python3 tests/signals/native.py --out target/signals-native
cargo build --target-dir target/signals-default
python3 tests/signals/terminal.py --binary target/signals-default/debug/naro --out target/signals-terminal
cargo build --features tiny --target-dir target/signals-tiny
python3 tests/signals/terminal.py --binary target/signals-tiny/debug/naro --tiny --out target/signals-tiny-terminal
```

`native.py` compiles the real bridge with a test-only hook immediately before its
consume operation. The hook delivers a selected signal after the pending-state
snapshot: all 25 pairs check same-class coalescing and distinct-class retention.
It also checks all six HUP/TERM/WINCH permutations, termination priority, all five
event classes, errno and mask preservation, and 10,000 synchronized worker-thread
delivery/consume races. Only the private generated test source has the hook.
`--revision f5e79cf` applies the same hook before the old read/clear and reproduces
the original failures. This source seam makes the narrow race deterministic;
PTY testing separately uses an uninstrumented editor.

`terminal.py` opens disposable PTYs and fixture files, sends signals only to its
child editor, and asserts exit 1, fatal diagnostics, recovery bytes/mode, unchanged
originals, termios restoration, cursor/alternate-screen cleanup and removal of a
lock observed during default startup. Tiny has no locking or bracketed paste;
its checks require no lock and no paste enable sequence. Burst tests stop the
editor, queue each permutation, and resume it, introducing a CONT event as well.
Two default cases interrupt an unfinished bracketed paste with HUP/TERM and
require both the ordinary edit and collected paste bytes in the recovery file.
`--paste-only` narrows the test for old-code failure proof. Standard signals
coalesce; neither driver asserts delivery of every repeated same-class signal.

This is focused Linux host evidence, not a release/guest-VT qualification.
