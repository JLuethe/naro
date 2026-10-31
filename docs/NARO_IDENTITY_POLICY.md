# NARO identity policy — Q-IDENTITY-001

Requested by John on October 31, 2026. NARO identifies itself as NARO with its
Cargo package version. GNU nano 9.3 is the behavior reference and receives its
original attribution; NARO does not claim to be the GNU executable.

## Intentional presentation differences

The editing header is `NARO <package version>`. Version output names NARO, its
independent Rust port/reference relationship, GPL-3.0-or-later license and
compiled profile. CLI usage names `naro`. Runtime welcome, help, unbound-key,
suspend and panic messages identify NARO. Help/welcome branding happens after
lookup using the original GNU gettext message IDs. Catalogs and attribution are
retained. Configuration/history paths, lock formats, gettext domain and temporary
compatibility names remain unchanged.

The shorter title is a real layout change. For ordinary complete titles it moves
the centered filename one column left while preserving the right state position.
At some narrow widths NARO's label fits where nano's does not. Tests assert
these cases instead of erasing the title row from comparison.

## Separate candidate assertions

Original reference scenario files and `tests/follow-up/tiny-cli-oracle.json`
remain unchanged. `tests/naro/identity-overrides.json` supplies 88 candidate
expectation sets bound to each original case's canonical SHA-256 and the reviewed
package version. A source edit or version change fails closed until reviewed.
File, exit, cursor, attribute and other nonidentity assertions are retained. One
smoke wait changes from `Welcome to nano` to `Welcome to NARO`; fed input bytes
are unchanged.

`nanoharness.py --candidate-expectations` selects these candidate assertions.
Without that flag the original reference assertions run. The paired follow-up
runner writes separate original reference and selected candidate scenarios. Its
strict checker reopens the proper per-side case, including its scenario hash,
steps, inputs and assertions.

CLI checking projects only exact recognized expected version/help stdout from
the unchanged reference oracle. Actual candidate output is never rewritten;
stderr stays exact. Unrecognized version text fails instead of accepting an
arbitrary replacement.

## No broad comparison normalization

`spec/tools/compare_runs.py` is unchanged. Raw grids, attributes, cursor, files,
inputs, exits and help text remain strictly compared. This policy does not turn
a branding mismatch into a raw exact match. The existing exact-count collector
therefore does not qualify the changed source by itself. The next qualification
must explicitly review the raw identity differences and adjust acceptance/count
reporting while retaining every other assertion. Old 0.1.0 qualification is not
evidence for new 0.1.1 bytes.

## Focused regression coverage

`test_candidate_expectations.py` checks binding, preservation of other assertions,
centering/fit boundaries and CLI projections. Negative controls reject wrong
filenames, state, attributes, cursor, saved bytes, exits, old branding, stale
cases and stale versions. Raw comparison still flags title and cursor changes.
Evidence-checker tests reject incorrectly selected candidate scenarios and
reference-style candidate hashes.

`tests/naro/identity-layout.json` contains 21 candidate-only terminal cases:
clean, modified and view titles at 32, 33, 34, 35, 40, 80 and 120 columns. The
independent ASCII oracle reproduces each affected original GNU title before
deriving the NARO expectation; it does not infer expectations from captures.

Full host/Ubuntu/guest-VT/package qualification and patch publication are later
steps. This policy does not change the published 0.1.0 tag or assets.
