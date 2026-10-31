# NARO title correction — October 31, 2026

This is the historical snapshot of the initial title-only correction. The work
has since expanded to the approved identity audit, explicit candidate policy,
and 0.1.1 preparation. Start with the
[current preparation record](NARO_0.1.1_PREPARATION_2026-10-31.md); statements below
about unfinished CLI/help branding and the preview's version describe that
earlier snapshot.

John reported that the released editor still says GNU nano 9.3 in its title.
The cause is a hardcoded string in src/render.rs:title. Nano parity assertions
also encode that string, so passing parity tests did not establish correct NARO
branding. The release review missed this separate product requirement.

## Implemented locally

The editing header now uses `concat!("NARO ", env!("CARGO_PKG_VERSION"))`.
It displays NARO 0.1.0 for the current Cargo version and updates automatically
when Cargo.toml changes. No nano-reference spec or stored oracle was rewritten.

A permanent Rust regression renders actual title cells at 40/80/120 columns for
clean and modified buffers, asserting NARO branding, filename and state. It
passes with default and all features. Four real-terminal preview cases pass:
normal 80-column, narrow 40-column, view mode and new buffer. The old public binary
fails precisely the eight branding assertions across those four cases, with all
other checks and exits passing. Evidence is in target/branding-fix-2026-10-31/.

Try the development preview from the repository root:

```sh
./target/branding-fix-2026-10-31/try-naro.sh
```

It opens the existing disposable sample with the newly built host preview. The
published archive and the separate installed-public-binary prefix are unchanged.
This preview is not a newly qualified release candidate.

## Before shipping the correction

1. Finish a focused identity audit. CLI --version and usage/help still use nano
   wording; the present patch addresses the screenshot's editing header only.
2. Declare the requested NARO identity as an intentional difference from GNU
   nano. Update candidate-specific expectations without rewriting nano's own
   observed baseline or broadly masking title/file/state differences. Existing
   smoke, progress/safety and tiny title assertions still expect GNU nano.
   A shorter brand also changes filename centering and some narrow-width layout
   decisions, so test those explicitly. Do not call the old parity suite green
   for this new source; it has not been requalified.
3. Prepare version 0.1.1, add the matching branding and CLI tests, then freeze
   production source and rebuild both host and Ubuntu candidates.
4. Run the required host/Ubuntu/guest-VT/package qualification with the explicit
   identity policy. Retain the published 0.1.0 results under their original hashes.
5. Package and review the patch-release files. Obtain approval for the new
   release proposal; preserve the existing 0.1.0 tag and uploads.

The earlier off-device backup task still awaits a USB mount path or remote
destination. Its source inventory is in target/off-device-backup-2026-10-31/.
