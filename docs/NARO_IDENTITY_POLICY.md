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

For the 0.1.3 development candidate, the version-bound expected titles and narrow
title contexts were reviewed at the new seven-cell version string. The named
legacy residual policy keeps its historical 0.1.1 differences; its comparator
projects only the exact branded title cells to 0.1.3. Reference case hashes and
source observations remain unchanged, and every other residual stays exact.

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
inputs, exits and help text remain strictly compared. Identity acceptance is a
separate, reference-derived decision; it never turns a branding difference into
a raw exact match. Reports distinguish raw exact, reviewed identity, declared
historical deviations and unexpected results. Unsupported title shapes fail
closed until the independent oracle is extended and reviewed.

The versioned release gate reopens recordings, verifies their provenance and
recomputes both assertions and identity decisions. Fixed suite membership and
the named historical deviations remain required; unexplained differences block
qualification. Fresh observations from each environment's own pinned nano are
required for the terminal corpus. The old 0.1.0 exact-count gate and qualification
are historical evidence, not evidence for new 0.1.1 bytes.

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

## Reviewed narrow and translated title layouts

Title painting uses terminal display cells, including the two-cell Japanese
state `変更済み`; codepoint counts do not determine terminal width or padding.
State text is selected only from the reviewed English/German names, exact
requested-catalog translations, and the known German ISO capture spellings.
Unknown non-ASCII filenames and unknown states remain unsupported.

An unbranded reference row receives no general title-row detector.
`tests/naro/identity-title-contexts.json` authorizes only the three original
`TEST-NEXT-TERM-001-*` cases' `small` snapshots at 30 columns and nine rows. Each
context binds the complete original case SHA-256 and package version and names
the original filename and state. Physical width, physical row count and effective
application width must all match before any empty-grid return, width slicing or
GNU-branded title branch. Explicit height metadata must agree too. The independent
GNU C titlebar model must reproduce the entire original row before calculating
whether the shorter NARO label fits. A changed case, version, geometry, filename or state fails closed.

A requested catalog is not proof that gettext selected it. For clean titles,
the oracle tries only the reviewed requested-catalog and C Modified-reservation
widths. Each possibility must reproduce the complete reference row exactly,
and every successful possibility must produce the same full NARO row. Zero or
multiple different projections fail. Selection never examines the candidate's
capture or the machine running the collector. This covers a requested French
locale falling back to C as well as a genuinely selected French catalog.

Identity classification preserves the state word's right-edge position, full
row attributes, cursor, modes, other rows, file bytes, input bytes and exit
checks. Literal C-derived tests cover clean, modified and view boundaries at
28, 29, 30 and 31 columns, Japanese and ISO states, French selection/fallback,
stale contexts and negative corruption controls. Historical raw observations
and raw exact-match counts remain unchanged.
