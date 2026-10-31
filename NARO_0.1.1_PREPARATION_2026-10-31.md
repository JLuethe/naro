# NARO 0.1.1 preparation — October 31, 2026

The published experimental prerelease remains **0.1.0**. Its tag, downloadable
archives, checksums and qualification evidence are unchanged. This development
tree is preparing **0.1.1** to correct product identity which the original nano
parity checks did not independently establish.

John authorized steps 1–3: finish the identity audit, introduce explicit
NARO-specific expectations while preserving the nano reference, and prepare
0.1.1 with frozen host and Ubuntu builds. Full step 4 qualification, final
packaging and publication are later work; this record does not claim they have
been performed or authorized by that bounded request.

## Step 1 — focused identity audit

Implemented and locally checked:

- The editing title identifies `NARO 0.1.1`, using the Cargo package version.
- CLI version output identifies NARO as an independent Rust port, names GNU
  nano 9.3 as its reference, states GPL-3.0-or-later, and reports the default or
  tiny profile with UTF-8 support.
- CLI usage names the `naro` executable. In-editor help, welcome, suspend and
  panic messages identify NARO. The configuration recovery suggestion names the
  lowercase executable `naro`.
- All 41 bundled catalogs were inspected for the relevant welcome/help product
  names. Explicit observed Arabic, Finnish, Japanese, Korean and Serbian aliases
  are branded at those runtime call sites, preserving inflection suffixes.
  Main-help headings lacking a product name receive `NARO — `.

GNU attribution, licenses, reference-source comments, gettext keys and catalog
files remain intact. Compatible nanorc/history paths, lock-file metadata and
temporary-file conventions are intentionally unchanged. No generic rewriting of
user text, filenames or all status messages was introduced.

The focused tests cover header placement at widths 32–35, 40, 80 and 120, clean
and modified file state, CLI profiles, translated aliases and preserved terms
such as `nanorc`, `нанорц`, `nanometer` and `nano_data`.

## Step 2 — explicit candidate identity policy

`Q-IDENTITY-001` records the intended product identity difference. The reviewed
candidate overlays are bound to the original scenario's complete SHA-256 and
the package version. Original reference scenarios, observations and assertions
remain unchanged. The raw terminal comparator remains unchanged as well.

The initial 88 overlays change 165 complete title-row assertions, one header
substring assertion, three panic diagnostic assertions and one welcome wait.
They preserve typed bytes, key sequences, files, exits, cursor expectations,
attributes and assertion counts. Title changes explicitly include filename
centering and narrow-width visibility decisions; they are not broad row masks.

The evidence checker independently verifies the derived candidate scenarios and
their recording hashes. Negative controls cover wrong identity, filename,
modified state, attributes, cursor, saved bytes, exit status and stale policy
bindings. See [the identity policy](docs/NARO_IDENTITY_POLICY.md) and
`tests/naro/` for the maintained policy and targeted cases.

Raw title and help differences will still appear in fresh paired comparisons.
Future qualification and its collector must explicitly account for this policy
and investigate every other mismatch. The old **101/101** collector result is
evidence for the published 0.1.0 source only and must not be represented as a
passing gate for 0.1.1.

## Step 3 — version and frozen build preparation

`Cargo.toml` and `Cargo.lock` now identify version **0.1.1**. Local post-change
checks passed: formatting, default Rust tests (16/16), all-feature Rust tests
(11/11), and Clippy for all targets/all features with warnings denied. Earlier
development executable checks passed default CLI 5/5, tiny CLI 5/5 and an editor
identity smoke probe 5/5; the prior frozen executable failed the five CLI
identity checks as expected. The production branding helper also passed all
123 selected catalog strings across 41 catalogs. The targeted terminal layout
suite passed 21/21 cases and 105 assertions. The policy and affected Python
test batches passed with counts 6, 6, 44, 14 and 9. That catalog check is not a
claim of 41 independent live-terminal locale runs.

The pre-build checklist below is now complete; exact results follow it:

1. Review the exact staged file list, excluding unrelated local reports and
   evidence. The targeted candidate-policy checks are complete.
2. Commit the reviewed production and testing changes, then freeze that exact
   source. Record its commit and production fingerprint.
3. Build default-feature host and Ubuntu candidates from that same committed
   freeze. Record each executable's full SHA-256, embedded build identity,
   compiler, feature set and environment; keep Ubuntu's own nano reference.
4. Retain the frozen source, binaries, command records and build results, with
   a durable index identifying the inputs for subsequent qualification.

A successful build does not establish behavioral qualification. These build
records must describe only checks actually completed; no editor test hooks may
be included in release candidates.

## Subsequent release work

Step 4 still requires fresh host, Ubuntu and guest-VT qualification of those
exact candidates under the explicit identity policy, followed by final package
validation and a newly justified technical release gate. Package/source
archives and checksums must be regenerated for the selected 0.1.1 source and
verified before publication is considered. No 0.1.1 package or release has been
published by this preparation work.

Local development evidence is retained under
`target/branding-identity-2026-10-31/` and
`target/branding-0.1.1-2026-10-31/production-checks-attempt02/`. These directories
are development evidence, not replacements for the eventual frozen-candidate
qualification record. The initial title-only preview remains documented in
[the historical correction note](NARO_BRANDING_FIX_2026-10-31.md).

## Step 3 completed

Frozen source: `8959d927ac3de05fcd0f389ed61def7dfb4728e1`.
Host executable SHA-256: `76c45b5af7985eca1ebcc2d7198dc560f5f02df0682e4c69a3972491e92cd36a`.
Ubuntu executable SHA-256: `c0e2c2805cf46a7e9d6d6b5dceb5b0c23ee9a8aa5c5f5ff5c1e3edbf94807a6f`.
Both default-feature release builds and the independent freeze verifier passed.
Focused frozen host layout 21/21 and CLI 5/5 on host and in Ubuntu passed.
See [the build receipts](validation/branding-0.1.1-2026-10-31/README.md).
Full qualification, packaging and publication remain subsequent work.
