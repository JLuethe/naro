# Issue 7 — incremental search and replacement

Implemented and validated on 2026-11-05. This evidence is for the exact frozen
artifacts below; it does not qualify an arbitrary rebuild or a release package.
No installation, publication, external report, or real user files were involved.

## Change

Ordinary find scans incrementally and retains one candidate plus a reusable
terminated line; retained memory does not depend on match count. The spelling
caller also stops at its first acceptable match. Regex calls reuse the terminated
input instead of copying an entire line for each match.

Replacement streams over an immutable input snapshot. Forward traversal retains
one match; backward traversal retains compact spans only for its current line
and regenerates captures when used. All builds each affected line once. Multiline
All keeps output grouped until completion and uses a Fenwick tree for inserted
line offsets, avoiding repeated line-table shifts. Each occurrence still records
an independent undo delta through issue 6's batch history API. Snapshot/output
and backward-span memory are O(input + output), in addition to bounded history
and the regex engine. Replacement bookkeeping/output is linear or near-linear.
The existing literal matcher retains its pattern-length factor in the worst
case; libc regex engine costs also remain outside that bookkeeping bound.

Scanning and replacement poll cancellation, preserve unrelated buffered keys,
and leave signals pending for the main loop. Cancellation is checked **between**
libc regex calls; a single in-progress `regexec` call is not preempted.

## Evidence

- Nine focused regression tests pass in default and all-features/tiny: capture
  substitution, NUL bytes, the specified 16 zero-width replacements, overlapping
  backward find, magic-line exclusion, wrap, regions, Yes/No/All, cancellation,
  multiline output after interactive replacement, adjusted marks, anchors,
  surviving generations, and full per-occurrence undo/redo where available.
- Full integrated suites: default **35 passed, 7 ignored**; all-features **24 passed,
  7 ignored**. Six ignores are separately executed resource fixtures; the other
  is the isolated locale-catalog fixture owned by issue 8. `cargo fmt --check`
  and all-targets/all-features Clippy with `-D warnings` pass.
- Resource fixtures: **12/12 final cases pass**, default and tiny. All are bounded
  to five seconds. Maximum final time was 0.145 s; maximum measured RSS was
  33,880 KiB. Dense find uses 2 MiB; literal/regex/backward replacement uses
  200,000 matches; multiline replacement uses 100,000 matches. Detailed limits,
  process results, binary hashes and exact commands are in `results.json`.
- Baseline `f5e79c…` fails all six selected comparisons: dense literal find aborts
  under the 96 MiB address-space limit in both profiles; dense regex find times
  out in both; tiny literal/regex replacement times out. Tiny disables history,
  so the replacement failure is independent of issue 6's snapshot-undo defect.
- Actual PTY Ctrl-C tests: **4/4 pass**, default and tiny. Absent-literal search
  returns to the UI in 1.09/1.19 s; replacement stops in 0.14/0.16 s and saves the
  exact partially replaced bytes. These include subsequent rendering time.
- Existing search terminal corpus: **19/19 accepted**, all by the unchanged
  `Q-IDENTITY-001` policy, zero declared deviations and zero unexpected
  differences. Raw strict comparison reports the expected GNU nano/NARO title
  differences; no non-title differences occurred. Recorded scenarios 007/017
  intentionally finish with harness termination in both editors.

## Exact artifacts and environment

Default executable SHA-256:
`5acb843662bf277cd6076dd428bdaf447feb7000d9f553bb128a1d84eeec2217`.

Tiny executable SHA-256:
`c902d60bcac906bc6419c7fb7c6065ee7bfc98d15aec9bd46261a800a179638b`.

Source snapshots/manifests, build logs, test binaries, resource measurements,
raw terminal traces and reference/candidate runs are retained in
`target/issue-7-search/`. Final frozen inputs are under `resources-02/after/`.
At the final search validation capture, working-tree differences from the frozen
inputs were limited to later issue 6 `buffer.rs` unit tests, with production code
identical. Subsequent work on other issues is outside these frozen-artifact
claims. Integrated suite counts above are from that captured tree. Build-info strings, artifact hashes and raw timings are in `results.json`.

Environment: Rust 1.99.1, Cargo 1.99.1, GCC 16.2.1, glibc 2.44,
ncursesw 6.6.20251230, libmagic 5.48, tmux 3.8. Terminal locale C.UTF-8.
Pinned GNU reference executables were read from
`/home/john/src/nano-install/{default,tiny}/bin/nano`; the 19-case replay uses default.

## Actual commands

```sh
cargo test
cargo test --all-features
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings
python3 tests/search/run.py --out target/issue-7-search/resources-01 --before-revision f5e79cfcffb13bc314e819bdc7a0c5ef3fa02d3e
python3 tests/search/run.py --out target/issue-7-search/resources-02
cargo build --release --manifest-path target/issue-7-search/resources-02/after/Cargo.toml
cargo build --release --features tiny --manifest-path target/issue-7-search/resources-02/after/Cargo.toml
NANOSPEC_WORK=/home/john/Code/naro/target/issue-7-search/reference-work python3 spec/tools/nanoharness.py spec/evidence/scenarios/search.json --binary /home/john/src/nano-install/default/bin/nano --out target/issue-7-search/reference-runs
NANOSPEC_WORK=/home/john/Code/naro/target/issue-7-search/candidate-work python3 spec/tools/nanoharness.py spec/evidence/scenarios/search.json --binary /home/john/Code/naro/target/issue-7-search/naro-final-default --out target/issue-7-search/candidate-runs
python3 spec/tools/compare_runs.py target/issue-7-search/reference-runs target/issue-7-search/candidate-runs --json target/issue-7-search/parity-diff.json
python3 tests/search/parity.py target/issue-7-search/reference-runs target/issue-7-search/candidate-runs --out target/issue-7-search/parity-review.json
python3 tests/search/terminal.py --binary target/issue-7-search/naro-final-default --out target/issue-7-search/terminal-default-final
python3 tests/search/terminal.py --binary target/issue-7-search/naro-final-tiny --out target/issue-7-search/terminal-tiny-final --tiny
```

Cargo above is `/home/john/.cargo/bin/cargo`. Optimized production executables
were copied immediately after each frozen build to the distinct `naro-final-*`
paths. Test binaries are instrumented only by Rust's test harness and were not
installed or distributed.

Preserved preliminary failures: the first PTY fixture used a single huge line and
hit an unrelated 335,544,320-byte renderer allocation under its 384 MiB process
bound. It was replaced with 4096-byte lines, keeping the same overall data sizes.
A second attempt waited for an entire prompt phrase, while curses transmitted
only its changed suffix; the final driver waits for that specific suffix. The
first parity-driver invocation passed `dict_values` to an API requiring a mapping;
correcting that invocation produced the reported result. None of these failed
attempts counts as a product pass. Their logs/traces remain under the target tree.
