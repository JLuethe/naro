# Optional tiny qualification

Reference: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.

Implementation complete; final paired qualification is running. Do not infer
completion from an intermediate report. Spec 22 defines the acceptance gates.

Fresh oracle comparisons use `tools/check_follow_up.py` with suites `tiny`,
`tiny-cli`, and `tiny-vt`, explicitly selecting `~/src/nano-install/tiny/bin/nano`.
`tools/check_tiny_ci.py` checks pinned file/screen/cursor/CLI assertions and
candidate safety without needing that oracle executable. `measure_profiles.py`
compares equal-compiler release builds using stripped fixture copies and native
header/dependency records. All terminal tests stay in harness-owned fixtures.

The eight ioctl cases are models, not physical-console certification. Tiny is
not a promise about arbitrary upstream configure combinations. Prior full
preview and Ubuntu package evidence remains historical and unchanged.
