# Incremental search and replacement regressions

`cargo test search::tests` exercises actual Editor find/replace operations:
captures (including NUL), zero-width progression, overlap, wrap, both directions,
regions, interactive Yes/No/All, cancellation, multiline output, cursor/mark and
per-occurrence undo/redo. Tiny runs the applicable assertions too.

`python3 tests/search/run.py --out target/search-resources-NEW --before-revision REV`
freezes source inputs and builds isolated optimized default/tiny test binaries.
It runs six explicit stress tests with a 5-second wall bound, core dumps disabled,
96 MiB address-space/48 MiB RSS find bounds, and 256 MiB address-space/192 MiB
RSS replacement bounds. Literal/regex find use a 2 MiB dense line. Replacement
uses 200,000 matches, or 100,000 newline-producing matches. Baseline replacement
runs with tiny so snapshot undo cannot explain an old failure. Compilation,
missing test execution, output assertions, timeout and peak memory are checked;
failures remain failures in the report. Use a fresh output directory.

`python3 tests/search/terminal.py --binary /absolute/naro --out target/search-pty-NEW`
checks actual Ctrl-C handling during a 32 MiB absent-literal search and an 8 MiB
dense replacement; add `--tiny` for tiny. Inputs have 4096-byte lines to keep this
check independent of full-line rendering allocations. Each editor has a 384 MiB
address-space bound and bounded waits. Replacement must stop before completing,
then save exactly the confirmed prefix and unchanged remaining text. All files
and traces remain under the requested private output directory.

Use the existing `spec/tools/nanoharness.py` and `spec/evidence/scenarios/search.json`
for terminal parity, and `tests/search/parity.py REFERENCE CANDIDATE --out REPORT`
for classification using the unchanged identity policy. It requires every case.
Raw comparison stays strict; permitted branding is reported separately.
