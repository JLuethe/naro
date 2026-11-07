# Issue #14 candidate runtime checks

The [0.1.3 local integrated retest](../0.1.3-local-retest-2026-11-07/README.md)
now binds both live-reference and recorded-oracle runs to the exact `dbc46bb`
host production and hook builds. Each mode passes ten production, 13 default
hook, four tiny hook and six direct PTY cases. All 12 direct PTY traces reached
EOF, include terminal reset bytes, and match saved size and SHA-256 receipts.
The historical branch results below remain separate from that integrated run.

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
actually exercised. The `dbc46bb` integrated run is linked above; any later
code build needs its own fresh run. An isolated-branch pass does not qualify a
merged binary.

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

## Decoded-key polling follow-up

The previous poll compared raw input codes. That made plain `g` cancel when
`M-G` was bound, and missed Meta+Left and F1 sent as terminal escape sequences.
Polling now probes a clone of queued input through the normal decoder without
blocking or consuming the original queue. It applies the same first effective
search-menu binding and Meta eligibility rules as ordinary key dispatch.
Incomplete escape sequences and non-cancel keys remain available to normal
dispatch; a decoded Cancel still drains the pending burst. Production PTY
regressions cover plain `g` versus Meta+g, Meta+Left, and F1 with
`rawsequences`; a unit test checks an incomplete Escape and non-cancel input.
The [negative-control receipt](decoded-negative-control.json) records the
three failures and positive control against the exact pre-fix binary. The
new tests require a fresh integrated-binary run for final qualification.

## Queued-input latency follow-up

The decoded-key poll still read only 32 raw codes per 50 ms and started each
check by cloning and decoding all previously retained input. A Cancel key
behind 8,192 ordinary keys therefore arrived much later than a Cancel alone.
The poll now keeps a private decoder cursor and feeds it only newly queued
codes. Each nonblocking read is capped at 16,384 codes, and each scan decodes
at most that many keys; the original input queue stays untouched until a
Cancel binding is found. Partial escape sequences stay in the private decoder
until more bytes arrive or the bounded ambiguity window expires.

`tests/issue14/backlog.py` creates a disposable 24 MiB file and sends the
8,194-byte burst in one PTY write while a view-only search is running. It
records production output, exit status, file digest, and time from burst to
`Cancelled`. The queued case must complete within the larger of 3 seconds or
twice the measured no-prefix baseline plus 0.5 seconds. The original exact
binary passed the baseline at 0.986 seconds but
missed the queued bound; [the negative-control receipt](backlog-negative-control.json)
records the SHA-256 hashes and failure. The test is called by
`tests/issue14/run.py` in both live-reference and recorded-oracle modes. This
is a bounded deterministic PTY test, not a claim about arbitrary input rates
or exhaustive scheduler interleavings.

## Split-sequence polling follow-up

Search polling now waits briefly for a complete SS3 or CSI terminal sequence when its
private decoder reaches a partial prefix. A final byte can arrive in a later
poll, including after the 16,384-code scan boundary, without losing a rebound
F1 or Meta+Left Cancel binding. The original input queue remains untouched
until Cancel is found. Normal blocking input retains its existing Escape
timeout behavior.

Three deterministic queue-boundary regressions fail on the old decoder and
pass with the fix. The [negative-control receipt](split-sequence-negative-control.json)
records their old-source failures. Production PTY cases also send SS3 and CSI
keys in two writes separated by 600 ms while a disposable search runs. Those
cases pass on both the old and new exact production ELFs; ncurses appears to
withhold incomplete terminal sequences until the final byte. They are
supplementary artifact checks, not negative-control proof of the poll fix.
The direct PTY runner saves every case's raw output and timed events on both
success and failure. It verifies the saved output's size and SHA-256 before
reporting a pass.

## Incomplete-prefix ambiguity and complete PTY traces

`ESC [` and `ESC O` can also mean standalone Meta keys. The private search
decoder examines at most 64 following raw codes for a complete terminal
sequence. If none is present, it waits up to 150 ms from the first observed
incomplete prefix before treating the introducer as Meta. A control byte,
Escape, Delete, or nonbyte key before the final byte ends that wait immediately;
those codes remain available for Cancel matching. A complete sequence already
queued at the next check wins even if the clock passed 150 ms between checks.
This policy applies only to search polling's private decoder; normal input's
Escape handling is unchanged. The timeout adds at most 150 ms of ambiguity
plus the search check cadence and scheduler delay. A final byte arriving only
after the fallback has been decoded cannot retroactively form a terminal key.

The old integrated production ELF missed Cancel for both partial CSI plus
Ctrl-C and standalone `M-[`, while the candidate passes. Default and tiny
SearchPoll tests also fail against the old decoder and pass with the fix;
[the negative-control receipt](prefix-ambiguity-negative-control.json) pins
the old artifact and raw results. Tests retain split F1/CSI recognition and
the 16,384-code boundary. The PTY runner now reads through process exit to
PTY EOF (Linux EIO counts as EOF), verifies alternate-screen and bracketed-
paste reset bytes, and records teardown and completeness for successes and
failures. A synthetic early-exit test checks that failed runs still save and
hash their complete raw stream. The runner uses a disposable 24 MiB fixture;
its timing bounds are host-local checks, not a guarantee under arbitrary load.
