# Release gate v2: identity-aware qualification

The `naro-release-gate/v2` schema applies to new 0.1.1 qualification. It does not
reinterpret or overwrite published 0.1.0 observations, archives, or the historical
101-check gate. An old gate must retain its original tools and identities.

`tools/collect_closure.py` reopens the reference and candidate recordings and
recomputes Q-IDENTITY-001 classification. Saved `accepted` flags are insufficient.
`tools/check_release_gate.py --reports <collector-output> --out <new-file>` repeats
the collector without writing into the evidence directories, then requires the
entire saved gate to equal the recomputed result. Missing evidence, stale policy,
changed captures, inconsistent classifications, or unexpected differences fail.

The gate carries a schema, the complete identity policy record (ID, version,
schema and SHA-256), production and executable hashes, raw-input paths, individual
checks and per-suite accounting. Counts distinguish:

- `raw_exact`: literal equality under the unchanged raw comparator.
- `identity_reviewed`: accepted identity-only differences proved from the reference.
- `declared_deviations`: accepted, specifically named historical differences.
- `unexpected`: rejected cases, including failures of independent assertions.
- `recorded` and `accepted`: inventory and acceptance totals.

A raw-exact observation can still fail mandatory NARO identity or another
assertion. Consequently `raw_exact` is an observation count, not an acceptance
shortcut; any `unexpected` count prevents qualification. Corpus accounting also
retains the observed file/exit equality count and the six exclusions. The gate
never forces historical full-match totals 301/302 or follow-up exact total 51.

Required inventories remain fixed: corpus 303 recorded plus the same six
excluded IDs; historical follow-ups 53 with exactly the two Q-TOOL-001 cases;
eight ioctl models; the six regression suites (151 cases); isolated root 27 plus
one separately asserted Q-ROOT-NOHOME-001 case; guest VT 19 for each candidate.
CLI-057 and PROMPT-NUL-001 retain their existing named policies. Anything outside
those policies remains a failure.

## Frozen launcher contract

Host output contains `naro`, `reference.bin`, `root-reference.bin`, `checkpoint.json`,
`reference/` fresh nano observations, `terminal/` candidate corpus, and the suite
directories at `<output>/<suite>`. Its checkpoint carries `state`, `active`,
`binary_sha256`, `reference_sha256`, `root_reference_sha256`, `build` and `checks`.
The six regression command keys are their suite names, plus `closure-regressions`.

Ubuntu output contains `naro`, `reference.bin`, `reference/`, `candidate/`, the
same suite directory names, and a `complete` file containing `completed`.
The collector also reopens every required Ubuntu `<stage>.status` receipt; each
must contain exactly `0` after stripping whitespace. A completion marker cannot
substitute for missing execution evidence. The gate retains these values in
`ubuntu_stage_statuses`, and verification reopens them again. Required stage names
are defined by `REQUIRED_UBUNTU_STAGES` in `tools/collect_closure.py`: reference
replay and terminal corpus, eight historical follow-ups, six regression suites
and their evidence checker, ioctl, extras, CLI, large files, panic and credits
builds, panic recovery, extensions, packaging and package checks, and tmux cleanup.
Both host and Ubuntu must additionally execute default Rust tests, candidate
expectation unit tests, the branding checks, and the 21-case identity-layout suite.
On Ubuntu these receipts are `rust-default`, `identity-expectations-unit`,
`branding`, and `identity-layout`. Collection follows container exit so the final
`tmux-cleanup.status` receipt is available. Launcher contract tests check actual
command membership against these required sets, in addition to the collector's
layout and missing/nonzero receipt tests.

Both corpus reports retain their actual `reference_runs` provenance and the
portable `reference_runs_relative` value `../reference`. The collector reopens
that canonical sibling directory, including its fresh replay inventory. Fresh
host reference observations are required in addition to fresh Ubuntu observations
so both sides carry executable/scenario hashes and complete step evidence. The
historical reference baseline remains untouched.

Both launchers use the established `/tmp/nanospec-work` fixture root. Several
original scenarios embed that literal path in history data; changing the root
can skip the named operation while preserving parity. Do not run competing host
matrices against those fixture IDs. Ubuntu has its own isolated container `/tmp`.
Builds, reports and owned tmux sockets still use separate private locations; VM
fixtures use their separately recorded short `/tmp/nv*` paths.

The gate additionally proves `TEST-FEAT-015` restored its seeded position:
snapshot `s0` must have cursor `(1,11)` and display `l40` on row 11, as observed in
the retained GNU run. A matching pair that missed restoration fails coverage.

For Ubuntu only, the collector derives the established `/opt/nano-locales`
replacement for existing nonempty `locpath` fields before checking complete
scenario hashes. Every other scenario field remains exact. This explicit
environment adaptation does not rewrite terminal captures or broaden identity
acceptance.

Other required directories retain their established names: `extras`, `large`,
`panic`, `extensions` (host), `package`, `package-check`, and the console and
transport outputs supplied separately. The source and recorded binary hashes
must identify the frozen candidates; the launcher must not rebuild a default
candidate in place.

## Guest VT proof

`naro-console/v2` retains both complete guest captures and all raw differences.
An expected character grid is derived solely from the reference and the reviewed
identity oracle. Only the known help frames enable help projection. Row-zero
attributes, dimensions, cursor, other text, input sequence, files, exit behavior,
and restored termios/console modes remain independently checked. Guest controller,
device, kernel, keymap inventory, boot-input hashes, and uploaded/installed binary
identities remain part of the proof. A report flag cannot replace those checks.

The fixed 19-case membership and all classifications are recomputed when collecting
the gate. No old guest recordings qualify new executable bytes.

Unit checks:

```sh
python3 tools/test_release_gate_evidence.py
python3 tools/test_console_identity.py
```

These include a canonical launcher-layout integration fixture and tampered-evidence
negative controls. They are tooling tests, not a substitute for fresh host,
Ubuntu, real guest-VT and package qualification.
