# Claude final review after independent Luna verification

Work in `/home/john/Code/naro`. John authorized completion of release readiness,
not publication. Codex owns implementation and Git delivery. Do not change tracked
files, frozen source/binaries, existing evidence, refs or assets. Write new review
evidence only in `target/claude-save-progress-verify-2026-10-30/`, preserving its
existing CURRENT_REVIEW_INPUTS.json. Retain attempts, commands/times/status/output,
a final CLAUDE_SAVE_PROGRESS_REPORT.md, PROGRESS.md, ATTEMPTS.md and SHA-256 manifest.

The earlier Claude static session `75cf1aee-a1c8-4198-a555-60474d10a5c7` was
interrupted by quota and is being resumed after 23:50. Its snapshot matches the
new production fix. Read that completed result and assess every finding. Do not
mistake a quota-error result for a review conclusion.

Read NARO_RELEASE_REVIEW_2026-10-30.md and CURRENT_REVIEW_INPUTS.json for current
paths. Production is `16f6398968adc1f815055a4413cf0465aed28126`; packaging and
proposed tag are `d5ddabe592d50912aa7b9fb932267783a9867190`. The exact candidates
and references are in `target/release-freeze-save-progress-2026-10-30/`.

Independent testing is now complete in two separately attributed reports:

- `target/luna-save-progress-verify-2026-10-30/LUNA_SAVE_PROGRESS_REPORT.md`:
  fresh 13/13 host and 13/13 Ubuntu; old binary fails 13/13; a wrong assertion is
  rejected by both harness status and strict collector; all 132 required suite
  recordings per environment revalidated; fresh whole-release collector 99/99.
  Setup failures and the corrected runtime/reference translation paths are
  documented in ATTEMPTS.md. Read the evidence, not only the summary.
- `target/asset-independent-verify-2026-10-30/ASSET_REVIEW_REPORT.md`:
  final attempt 04, 116/116 archive/source/inventory/checksum/link checks. Earlier
  audit iterations were strengthened at Codex's request and preserved. Runtime
  package/rebuild outcomes are explicitly inspected rather than rerun.
- `validation/save-progress-2026-10-30/independent-luna-backups.json`:
  Codex verified the full backup payload inventories. The asset reviewer's own
  manifest omitted a preserved old manifest; Codex separately checked it and
  every other file against the reopened archive, without changing original evidence.

Your remaining scope:

1. Critically review save-progress code against pinned nano source. Check FIFO
   status before blocking open, normal status after open/before write or sync,
   priority, hidden cursor, error/backup/selection paths, and rendering/translation.
   State actual issues with source evidence; distinguish hypotheses from confirmed
   regressions. A concrete concern may justify a new minimal paired scratch probe.
2. Review the two independent results and operation/negative-control evidence.
   Confirm observations bind to the exact frozen candidates and references and
   that assertion/step/status failures cannot hide behind comparison-only counts.
   Do not rerun already-passing runtime suites merely to duplicate them; rerun
   only to resolve a concrete missing check, failed check or suspected defect.
3. Rehash the exact seven current working and preserved assets against the
   asset manifest and SHA256SUMS. Verify production/package identities, code and
   regression contents in source, qualification/known-difference wording, and the
   proposed tag/source relationship. Confirm successful CI evidence for production
   and proposed tag. Final review-delivery CI will be checked after that commit.
4. Check the current evidence manifests and review scope accurately. The sidecar
   marks your review pending until it is actually complete; Codex will preserve
   that version, update metadata/checksums with your result, and request a final
   narrow verification of the resulting sidecars/manifest. Neither Luna report
   may be relabeled as Claude-executed testing.
5. Verify frozen/tracked state before and after. Leave no owned processes. Report
   a clear blocker/pass conclusion for your actual scope, with what you executed,
   what you inspected, retained limitations, and any failed attempts. Do not
   publish or approve on John's behalf.

Keep context compact: summarize manifests programmatically and inspect concrete
failures and critical traces. Preserve known differences and explicit exclusions;
never weaken expectations or normalization to accept a new mismatch.
