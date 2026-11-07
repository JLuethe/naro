# Fortified libc gate correction

CI run [42336509856](https://github.com/JLuethe/naro/actions/runs/42336509856)
reported 27 passes and 45 failures in the default bounded matrix. Existing-file
source-open gates were not reached, and the subsequent temporary/publication
gates had no recorded source identity. Missing-target and confined-read cases
passed. The raw [CI log](ci-42336509856-failed.log) is preserved.

The cause is a test interposer omission: glibc can call `__openat_2` for a
no-mode source open while calling `openat` for mode-bearing temporary creation.
The initial interposer exported only `open` and `openat`. This was reproduced
locally with unchanged native source and `-D_FORTIFY_SOURCE=2`: exactly 27 passes
and 45 failures. [Imported symbols](default-symbols.txt) include `__openat_2`;
[the failed replay](before-fix-default.log) is retained. Its assertion failures
are explained by missed test instrumentation, not evidence of a product
confinement failure. No old failure status was rewritten as a pass.

The correction routes ordinary, `64`, and fortified `_2` open/openat symbols
through the same gates and source identity recorder. Each wrapper dispatches to
the matching actual libc symbol, including its fortified argument validation.
All existing gate-reached, inode, byte-content, and cleanup assertions remain.
No production code or fingerprint input changed.

## Local verification

Executed in `/home/john/Code/naro/target/issue-12-bounded` on base revision
`b10eb35180d4d051fe1cdaae9a3d2730d7b5227b`. Cargo used
`/home/john/.cargo/bin/cargo`. The native compiler wrappers were:

```sh
#!/bin/sh
exec /usr/bin/cc -D_FORTIFY_SOURCE=2 "$@"
```

The large-file variant additionally passed `-D_FILE_OFFSET_BITS=64`. Each was
selected using `CC=<absolute-wrapper>` and a fresh `CARGO_TARGET_DIR` for
`cargo test --offline [--features tiny] --no-run --message-format=json`.
The resulting test executables were passed to:

```sh
python3 tests/confinement/run.py --binary <test-executable> --out <fresh-directory> [--tiny]
```

| Native bridge build | Default | Tiny |
| --- | --- | --- |
| Ordinary original binaries | 72/72 passed | 67/67 passed |
| `-D_FORTIFY_SOURCE=2` | 72/72 passed | 67/67 passed |
| `-D_FORTIFY_SOURCE=2 -D_FILE_OFFSET_BITS=64` | 72/72 passed | 67/67 passed |

Large-file binaries import `__openat64_2`, verified with `readelf -Ws`; see
[their symbol record](default64-symbols.txt). The runners compiled the corrected
interposer with `-Wall -Wextra -Werror`. All six corrected matrices report zero
assertion or infrastructure failures. The ordinary, fortified, and large-file
runs retain the same case counts and expectations.

[results.json](results.json) records binary, gate and report hashes and counts.
Full build records, compiler wrappers, gate records, subprocess output and all
matrix reports/fixtures remain under `target/issue12-libc/` in the isolated
worktree. This local reproduction establishes the missed fortified hook; a
subsequent Ubuntu CI run remains necessary to confirm the integrated workflow.
This correction does not change the original concurrency limits or constitute
release artifact qualification.
