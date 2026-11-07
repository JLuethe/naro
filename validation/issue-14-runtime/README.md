# Issue #14 candidate runtime checks

Date: November 6, 2026. This work follows the citation correction in
`validation/issue-14-citations/README.md`; it does not change the historical
reference corpus or relabel its observations as candidate tests.

## Reproduce

From the repository root, with the pinned GNU default ELF available:

```sh
/home/john/.cargo/bin/cargo build --offline --release
/home/john/.cargo/bin/cargo build --offline --features test-hooks
CARGO_TARGET_DIR="$PWD/target/issue14-tiny-target" /home/john/.cargo/bin/cargo build --offline --no-default-features --features tiny,test-hooks
python3 tests/issue14/run.py \
  --binary "$PWD/target/release/naro" \
  --hooks-binary "$PWD/target/debug/naro" \
  --tiny-hooks-binary "$PWD/target/issue14-tiny-target/debug/naro" \
  --reference /home/john/src/nano-install/default/bin/nano \
  --out "$PWD/target/issue14-runtime-new-run"
```

Choose an unused `--out` directory for each run. The live-reference mode
requires the GNU ELF's pinned SHA-256. Every mode requires equal revision,
source fingerprint, version, and
compiler in the candidate builds. It checks exact feature lists. Its
`artifacts.json` records SHA-256 and `NARO_BUILD_INFO` for the binary population
actually exercised. The final integrated candidate needs its own fresh run;
an isolated-branch pass does not qualify a merged binary.

For CI hosts without that GNU ELF, replace `--reference PATH` with
`--recorded-oracles`. This fail-closed mode verifies the SHA-256 of the
committed `spec/evidence/cli/cli-probes.json`, then uses its exact help and
three diagnostic tuples. The live-reference mode additionally checks two
diagnostic variants. Both modes require the 13 committed reference key-table
dumps for structural comparisons; neither silently skips missing evidence.

The production ELF runs CLI help/diagnostic tests, status-2 discard, combined
modern/preserve save flow, quickblank timing, and long-search cancellation.
The hook ELFs snapshot configuration and ordered key tables at startup. The
default hook build compares nine recorded reference key profiles plus the
combined modern/preserve derivation; the optional tiny hook build compares
four tiny reference profiles. Skipping `--tiny-hooks-binary` leaves those four
unqualified in that run. Reference-table snapshots are structural checks of
test-hook binaries; they do not by themselves assert every production key
interaction.

## Negative control and observed result

Before the `SearchPoll` fix, the production candidate received ^C and `X` in
one burst during a finite two-million-byte missing-literal search. It displayed
`Cancelled`, then inserted `X`; ^X reached the modified-buffer prompt and the
scenario timed out. The [committed negative-control receipt](negative-control.json)
records the binary, raw-result hashes and decisive observations. The large raw
failure remains in the isolated worktree at `target/issue14-cancel-prototype-run`.
With the fix, the same burst exits 0,
leaves the file SHA-256 unchanged, and satisfies the `Cancelled` wait. A
separate unit test confirms non-cancel queued input remains intact.

The branch's complete runner passed on the locally built production, default
test-hook, and tiny test-hook ELFs. The exact receipt and per-case results are
in the ignored `target/issue14-final-full` and `target/issue14-final-ci`
directories. In the earlier
prototype, a 20-million-byte line and a 300,000-line fixture finished on GNU
nano before ^C could be delivered; those runs are failed test setups, not
evidence of GNU cancellation behavior. The normative source evidence in
`spec/03-terminal-input.md` supplies the buffered-input discard rule. Search
timing parity against a forced long-running GNU search remains unqualified.

The RC merge cases cover one boolean, three numeric options, one string
option, and restricted cleanup; they do not cover every rc option. The
quickblank case checks visible clearing after 1.2 seconds, not a precision
measurement of the 0.8-second threshold. These limits must remain visible
when reporting issue #14.

## Search Cancel binding follow-up

A later review found that long-search polling recognized raw ^C rather than
the effective binding in the search menu. The follow-up uses the same ordered
key lookup rule as ordinary dispatch: after `unbind ^C search` and
`bind ^G cancel search`, ^G cancels and discards the trailing same-burst key,
while ^C allows the missing search to finish. Unit tests check the queued
input decision directly; production PTY tests exercise the actual rc parser,
key lookup, and long-search polling. The prior issue #14 production binary
failed both new scenarios; [the negative-control receipt](rebound-negative-control.json)
records its SHA-256, scenario and raw-result hashes, and failure notes. The
large raw fixtures remain ignored in the isolated worktree.
