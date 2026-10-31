# NARO 0.1.0 release scope and acceptance checklist

Scope adopted October 30, 2026 (America/Los_Angeles), implementing steps 1 and 2
of the [release-readiness plan](NARO_RELEASE_READINESS_PLAN_2026-10-30.md).
This checklist defines the next release; it does not certify an artifact or
authorize publication. Historical reports retain their original identities.

## Current candidate status

The save-progress repair is committed as `b934b1f`. Both replacement candidates
passed fresh complete qualification, including all 151 newer exact cases per
environment and the expanded 101-check gate. See the
[new qualification record](validation/save-hardening-2026-10-31/README.md).
Final archives and independent Claude review passed, including the metadata
check. See the [approval packet](NARO_RELEASE_REVIEW_2026-10-31.md). Publication
approval remains separate; no release is published.

## Release scope

- Experimental independent GNU nano 9.3 port, version 0.1.0.
- One primary binary download: **default-feature Linux x86_64 GNU/glibc build**.
  No `test-hooks`, `tiny`, or optional `credits` features in this artifact.
- Portable binary built and qualified in the recorded Ubuntu environment, with
  matching source archive, checksums, build provenance, installer, licenses,
  credits, translations, and syntax definitions.
- Runtime dependencies include glibc, ncursesw, and libmagic. Record actual
  library/symbol requirements and Ubuntu version in the release manifest;
  do not promise an unmeasured minimum glibc or universal Linux compatibility.
- Qualify the frozen source on the development host and the recorded Ubuntu
  userspace. Console claims cover the recorded guest Linux VT/kernel/keymap
  with emulated PS/2 keyboard input.
- Tiny remains an optional **source-build profile**, with existing CI coverage.
  No tiny binary archive is included in this first release's asset set. This
  avoids publishing the current full/tiny archive-name collision; tiny
  distribution can be qualified and named separately later.
- Installation uses the supplied installer and a user-selected prefix. It does
  not replace the system editor or change shell profiles automatically.
- This is not a promise of complete nano parity, pure Rust implementation,
  security-audited behavior, physical keyboard certification, or other-platform
  support. Native system libraries and the C bridge remain part of the product.

## Required gates

All unchecked items below are pending for the final release candidate. Previous
passes do not qualify a newly built executable automatically.

- [x] Define the scope, required gates, accepted differences, and deferrals.
- [x] Require wrap-undo (58), filter (6), and release-fixes (15) in both closure
  runners and the final collector, separately from historical follow-ups.
- [x] Complete the bounded step 3 host matrix: 40/40 exact, with the newly
  discovered paging defect fixed. See [results](NARO_STEP3_RESULTS_2026-10-30.md).
- [x] Freeze committed production source; record source fingerprint, revision,
  compiler/features, native environment, candidate hashes, and pinned reference.
- [x] Pass formatting, Clippy, Rust/Python tests, specification audit, and CI for
  the delivered changes. Resolve or disclose remaining audit citations.
- [x] Qualify host and Ubuntu terminal corpora: 303 recorded, 301 full matches,
  302 file/exit matches, and six explicit exclusions; no new unexplained mismatch.
- [x] Pass CLI 38 and regex 162 checks in each environment.
- [x] Preserve historical follow-up acceptance: 53 cases, 51 exact, only the
  two named tool-cleanup differences. Pass all eight ioctl-model comparisons.
- [x] Pass all 151 additional exact comparisons in **each** environment:
  wrap-undo 58, filter 6, release-fixes 15, step3-gaps 40, save-progress 22, save-safety 10. Both harnesses must exit zero, all
  assertions and steps must pass, and complete evidence must validate.
- [x] Pass host isolated-root/home cases (27 exact), with the separate asserted
  no-home recovery deviation.
- [x] Refresh safety, controlled write failures, backup/lock behavior, recovery,
  signals, installed assets/locales, and 1 MiB/10 MiB file checks.
- [x] Pass all 19 genuine guest-VT comparisons for each optimized host and
  Ubuntu candidate, including terminal/keyboard restoration and VM provenance.
- [x] Package the exact qualified Ubuntu executable and corresponding source.
  Verify hash linkage, source rebuild, all shipped catalogs/syntax, private and
  spaced-prefix installation, symlink launch, archive rejection, and uninstall
  ownership/conflicts. Exclude test hooks.
- [x] Pass the updated final closure collector with complete inputs. Retain
  compact tracked reports and back up full evidence outside `target/`.
- [x] Update public documentation, attribution/license review, release notes,
  support/reporting routes, and the final download list.
- [x] Complete independent archive/evidence review and final metadata verification.
- [x] Verify successful production and proposed-tag CI. Final review-delivery CI
  is recorded after that commit in the delivery receipt.
- [ ] Obtain John’s publication approval for the exact tag, release description
  and seven assets, then recheck remote refs, CI and hashes before publication.

## Accepted differences and exclusions

These are existing, bounded policies, not permission to accept new mismatches.
Keep their explicit semantic assertions and reference observations.

| Area | Accepted behavior |
| --- | --- |
| `TEST-CLI-057` / `Q-DEF-001` | Intentional invalid-regex recovery difference. |
| `TEST-PROMPT-NUL-001` / `Q-PROMPT-001` | Reject NUL as a Yes response. |
| `Q-TOOL-001` | Handled HUP/TERM owns tool cleanup; the two historical comparisons differ only as allowed by the field-level policy. |
| `Q-ROOT-NOHOME-001` | Assert the established no-home tilde recovery behavior in the isolated-root case. |
| Baseline exclusions | Retain the six recorded safe-corpus exclusions; do not silently treat skipped cases as passing. |

Any newly demonstrated crash, data-integrity defect, failed required assertion,
unexplained mismatch, or missing required evidence blocks acceptance until
repaired or explicitly reviewed with a documented scope decision. Do not weaken
goldens or normalization to reach a passing count.

## Evidence contract for the new suites

`tools/check_closure_regressions.py` reopens each suite's report, frozen candidate
and reference, scenario inputs, per-side recordings, and raw traces. It checks
the fixed suite count and exact IDs, source/features/tool identities, real
harness statuses, complete step/snapshot membership, input bytes, recomputed
expectations and comparisons, and artifact hashes. Summary booleans alone are
insufficient. No executable named by a report is run during collection.

Each runner freezes its environment reference as `reference.bin` at the run
root. Host qualification requires the existing pinned host executable hash;
Ubuntu uses its own built reference hash rather than the host's executable.
The collector binds all six suites to the corresponding frozen reference and
candidate. Missing reports fail the gate even when old closure checks pass.
This is evidence integrity checking, not signed build authentication.

The historical 53-case totals remain unchanged. The final gate records the
additional 58/6/15/40/22/10 inventory separately. New checker/tool identities require
fresh qualification records; historical bundles are not relabeled.

Useful entry points after the source freeze:

```sh
python3 tools/run_closure_host.py --binary PATH_TO_FROZEN_HOST_BINARY --out NEW_HOST_OUTPUT
# Run tests/follow-up/environment.sh in the documented private Ubuntu environment.
python3 tools/check_closure_regressions.py --base RUN_OUTPUT --binary RUN_OUTPUT/naro --reference RUN_OUTPUT/reference.bin
python3 tools/collect_closure.py --help
```

Use new output directories and the complete invocation described by the closure
specification. Do not concurrently reuse fixture IDs or overwrite old evidence.

## Deferred work

Tiny binary downloads, additional architectures/OSes, other package formats,
physical keyboard/operator trials, and exhaustive nano parity are outside this
release. Broader fuzzing, Miri, Valgrind, and further memory/stress coverage remain
follow-up work. The completed 86-case ASan run remains useful evidence; external
native libraries were not instrumented. New defects found during any optional
testing must still be assessed against release safety and integrity criteria.

## Next action

Review [the final approval packet](NARO_RELEASE_REVIEW_2026-10-31.md). Technical
qualification, packaging and independent reviews are complete. Final delivery CI
is verified after its commit and recorded in the outside-target delivery receipt.
John must approve the exact prerelease/tag/body/assets proposal before publication.
All earlier candidates and evidence remain historical under their original identities.
