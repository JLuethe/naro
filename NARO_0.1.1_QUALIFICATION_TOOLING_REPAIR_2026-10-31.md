# NARO 0.1.1 qualification tooling repair — 2026-10-31

Claude stopped after Phase A because the frozen tools could not represent the
reviewed NARO identity difference. No editor failure was reported. The remaining
`configuring nano` CLI-help wording is corrected in a separate production commit,
so replacement candidates are required. Nothing here authorizes publication.

## Preserved evidence

The original 761 manifest entries and manifest are unchanged at
`target/naro-test-runs/claude-0.1.1-step4-2026-10-31-attempt01/`.
All 762 files were verified and backed up at:

`/home/john/Backups/naro/2026-10-31-claude-0.1.1-phaseA/claude-phaseA-evidence.tar.gz`

SHA-256:
`3e76a3d1426a5735a4a6cab01d457cbed9d890b7499933a28c10241ecd6e2d00`.
This copy is outside `target/` on the same filesystem, not off-device.

## Repair contract

1. **T1: paired identity review.** Preserve strict raw comparisons. Derive the
   expected NARO presentation independently from the GNU reference and policy.
   Report raw exact, identity reviewed, declared historical deviation and
   unexpected counts separately. Never rewrite observed output.
2. **T2: evidence recomputation.** Reopen recordings, select the correct per-side
   scenario, verify provenance/raw hashes, recompute assertions and identity
   classification, and reject forged flags or counts.
3. **T3: terminal corpus.** Apply NARO expectations only to NARO. Retain 303 cases
   and six fixed exclusions. Collect fresh nano observations in each environment,
   including host, using that environment's pinned executable. Merge worker
   results without relabeling identity changes as exact matches.
4. **T4: closure gate.** Version the acceptance schema and bind the reviewed
   policy/fingerprint. Retain fixed membership and narrow historical deviations.
   Recompute acceptance instead of requiring the old 0.1.0 exact-match totals.
   Every new unexplained difference blocks qualification.
5. **T5: guest VT.** Prepare fresh fixtures for both replacement candidates.
   Derive expected identity text independently; preserve filename/state layout,
   attributes, cursor, other rows, keyboard inputs, files, signals, restoration
   and guest provenance. Require all 19 cases per candidate.
6. **T6: frozen launchers.** Require explicit source, default candidate,
   references, freeze and output paths. Use private spaces for builds/checks and
   optional variants. Do not rebuild the supplied default executable or write
   into its frozen checkout. Record locale edits in private Ubuntu case copies.

Production and tooling changes have separate commits. Build both default-feature
candidates from one final committed tree, without test hooks. Verify production
and verification fingerprints independently. Earlier qualification is historical
evidence and does not qualify the replacement bytes.

The production correction is commit
`548a6682b8567ea670a71f9e51cc44abdd3be085`, with production fingerprint
`63936243e73d0a3fb536d3c0a0fb0e6fe57be09da5f5bc0387ee10250b3d7093`.
Its five Rust identity tests and five rebuilt CLI branding checks pass. The old
frozen executable fails the three added help checks, as expected, while its two
version checks still pass.

## Readiness before Claude resumes

- Test normal/narrow title layouts, state and supported identity messages using
  expectations independent of candidate captures.
- Reject wrong filenames, state, title attributes, cursor, other cells, files,
  exits, old branding, stale bindings and forged evidence in negative controls.
- Exercise the original paired-run blocker and corpus welcome wait. Check real
  corpus presentation coverage before handing back the long matrix.
- Check launchers fail closed on altered inputs, preserve output directories and
  leave frozen source/default executables unchanged.
- Freeze/rebuild host and Ubuntu, verify the freeze, preserve it and proof outside
  `target/`, then provide exact hashes and commands in a new Claude handoff.

## Remaining qualification

Claude must run the full host/Ubuntu matrix with fresh references and repaired
frozen tools, both guest-VT runs and the closure collector. Package and publication
material must then be refreshed for the qualified bytes. The published 0.1.0 tag
and assets remain immutable.

Current work: `target/qualification-tooling-0.1.1-2026-10-31/`. Final identities
and readiness results will be recorded there and in the resume handoff after
review and builds complete.
