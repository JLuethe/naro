# Step 8 plan — documentation and public claims

Completed: see the [steps 8–9 results](NARO_STEP8_9_RESULTS_2026-10-30.md) for refreshed
archive identities, validation, backup and the outstanding step 10 CI gate.

Date: October 30, 2026 (America/Los_Angeles).
Status: approved for application and package refresh on October 30, 2026.
The original preparation plan below is historical; the adoption receipt and
subsequent step 8/9 results record execution.

## Objective

A new user should be able to determine what NARO supports, install/remove it,
understand known differences and coverage limits, and report a useful bug without
reading the development conversation. Every qualification claim must identify
current evidence rather than an older artifact.

Start with [the review index](NARO_STEP8_REVIEW_2026-10-30.md). Proposed destination
files are under `docs/release-review/2026-10-30/files/`; they mirror repository
paths. The review patch is not applied automatically.

## Baseline to preserve

- Production source fd91763; default Ubuntu executable SHA-256
  `33a39eb339492720ec6166e84fea421749e0b2ec3bd612b276c2377f91b7c4a1`.
- Complete technical gate: 97/97; host and Ubuntu matrices and guest-VT pass.
- Step 7 binary/source archives, checksums and backups remain unchanged.
- No claim of publication, universal Linux support, pure Rust, complete nano
  parity, a security audit, or physical keyboard certification.
- Existing deviations, six corpus exclusions, nine unresolved audit citations
  and historical evidence remain explicit.

## Work sequence and acceptance

1. **Inventory claims and evidence.** Replace stale top-level links and ambiguous
   “tested release” wording. Separate current candidate reports from older
   follow-up, tiny, console and closure records. Completed in the drafts.
2. **Rewrite the user entry points.** Review README, INSTALL and IMPLEMENTATION
   as complete replacements. Explain build/runtime dependencies, external tools,
   profiles, configuration, install/removal and exact build identity.
3. **Prepare release and reporting text.** Review candidate release notes and
   contributor guidance. SECURITY and the ordinary bug template are companion
   drafts for step 9; their wording does not assume GitHub private reporting is
   enabled. Verify the actual reporting route before publication.
4. **Reconcile coverage honestly.** Review COVERAGE_REVIEW and the spec coverage
   introduction. All nine unresolved citations are retained with a per-citation
   disposition; historical probe IDs and table dumps are not invented as passing
   candidate scenarios. No permanent tests or audit rules are changed.
5. **Update continuity and indexes.** Review the validation index, progress/next-step
   introductions, and historical notices on the five relevant tester handoffs.
   Preserve the old instructions below their notices without treating them as
   active assignments.
6. **Validate the proposed document set.** Check links against the combined
   proposed/current repository, parse JSON receipts, verify claim counts/hashes,
   check the patch without applying it, and run the spec audit in an isolated
   preview tree. Keep live documents and frozen artifacts untouched.
7. **Apply only reviewed files.** After review, copy the selected replacements
   into their intended paths, review their diff, run the document/spec checks,
   and commit the documentation revision separately from the build commit.
   Do not stage unrelated reviews or the draft workspace by accident.
8. **Reconcile packaged documentation.** Refresh the packages as described below,
   then hand off attribution/reporting review and final publication approval.
   Step 8 is complete only once approved public text and package contents agree.

## Package impact and recommended adoption path

README.md, INSTALL.md and IMPLEMENTATION.md are in the binary archive. All
tracked documentation is in the source archive. Applying these revisions means
the old archives do not contain the new text. Do not claim otherwise.

Recommended: preserve the current step 7 downloads and repackage the **same
qualified executable** from a clean documentation delivery checkout. The
production fingerprint must still match; no editor rebuild is needed. Record
the compiled revision fd91763 and newer packaging/source-documentation revision
separately. Include new release/coverage guidance in the selected shipped docs
where appropriate; this may need a small reviewed packaging-tool change because
its document list is explicit. Ensure installed Markdown links have useful local
or repository destinations rather than promising unshipped files.

Use new output directories. Verify payload identities and notices, regenerate
archive checksums/provenance, rerun package installation/rejection/removal and
offline source-build checks in Ubuntu, and rerun the collector with the updated
package inputs and unchanged behavioral/VM evidence. Repeat ordinary-prefix
coverage if its artifact changed. Back up the revised set. Do not replace the
previous verified archive files in place or reuse their hashes/check results
for different bytes.

Alternative for review: keep current archives byte-for-byte and publish updated
repository docs as clearly separate guidance. This avoids a package refresh but
leaves historical README/INSTALL/IMPLEMENTATION inside the archives. The refresh
route above is preferred for a consistent first release.

## What remains outside this draft task

Comprehensive licensing/attribution review, actual GitHub reporting configuration,
publication authorization, tags, releases and asset uploads are steps 9–10.
No private-reporting setting is changed. No source/editor fixes, package builds,
new qualification claims or production-source fingerprints are created here.
The current backups are on the same disk; external backup remains separate.

## Review decisions

- Approve or edit the plain experimental-release positioning and known limits.
- Approve explicit retention of the nine citation gaps rather than implying full coverage.
- Select the documentation-package reconciliation route; refreshing archives with
  the unchanged executable is recommended.

The prepared drafts are concrete review material. No active documentation,
package, commit or published release has been changed during preparation.

## Draft verification completed

- Seventeen proposed destination files prepared, plus a unified review patch.
- Patch passes `git apply --check`; it has not been applied.
- All 132 local links in the proposed files resolve against the proposed/current
  repository overlay; no broken local links were found.
- Spec audit passes in an isolated preview tree and retains the exact same nine
  warning citations; live generated audit files were not modified.
- Candidate identity and 97-check claim checked against the tracked gate receipts.
- Active tracked file contents are unchanged. No package rebuild or Git delivery.

See the review packet's verification.json for the recorded checks. Document
approval, application and package reconciliation remain pending.
