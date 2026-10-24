# Validation evidence

These compact reports describe one frozen optimized Naro executable, identified
by SHA-256 in every report. The reference is GNU nano commit
`6ed285c3ec7a1d228def4d4e7021c6ba269f620c`. See
[implementation status](../IMPLEMENTATION.md) for the current outcome and limits.

- `terminal.json`: full screen/cursor/mode/file/exit comparisons for 303 default
  scenarios; lists every differing field and explicitly declared deviation.
- `cli.json`: exact stdout/stderr/status comparisons for 38 noninteractive probes.
- `regex.json`: the 81-case corpus in each of C and en_US.UTF-8.
- `safety.json`: six assertions across the invalid-regex and NUL-answer cases.
- `environment.json`: build/runtime versions and the frozen executable hash.

Full candidate recordings, raw terminal streams, frozen executables and detailed
value-by-value diffs remain on disk under `spec/evidence/naro-v7/part-*`
(gitignored). The combined report checks that partitions are disjoint, complete,
and use the same executable hash.
Original reference evidence is checked in under `spec/evidence/runs`.
A `RECORDED` harness line alone does not establish a passing comparison.

From the repository root, reproduce with:

```sh
cargo build --release
python3 tools/validate_parallel.py --binary target/release/naro --out spec/evidence/naro-v7-new --jobs 4
python3 tools/check_cli.py --binary target/release/naro
python3 tools/check_regex.py --binary target/release/naro
python3 spec/tools/nanoharness.py tests/scenarios/safety.json --binary "$PWD/target/release/naro" --out spec/evidence/naro-safety
python3 tools/summarize_validation.py spec/evidence/naro-v7-new
```

The differential runner returns nonzero for any undeclared difference, while
still writing the complete report. Six inherited terminal cases are excluded:
five require absolute paths outside private fixtures and one needs the optional
tiny build. Eight CLI probes are excluded: six tiny and two external paths.
Run full suites serially because fixtures are keyed by scenario ID.
The final two safety scenarios assert intentional improvements to the reference;
their golden observations remain unchanged.
