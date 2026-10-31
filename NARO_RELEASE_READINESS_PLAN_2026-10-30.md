# NARO 0.1 release-readiness plan

Date: October 30, 2026 (America/Los_Angeles, PDT)

Repository: `/home/john/Code/naro` — <https://github.com/JLuethe/naro>

Source checkpoint: `088dc176ba7ae8078784d086320ef2c1ac530560` (`088dc17`)

This is a planning document. Creating it does not implement changes, run
qualification, or publish a release. Status statements below describe the
review on this date; verify live CI and repository state before resuming.

## Current position

NARO is past the latest bug-fixing round, but the final release artifacts still
need qualification. Remaining work is primarily release testing, packaging,
evidence, and documentation rather than a large feature-development push.

- GitHub `main` contains `088dc17`, fixing all six Claude findings plus a related
  End/tab-boundary defect.
- Recorded local results include 15/15 permanent regressions, 86/86 broader
  comparisons, and 86/86 ASan comparisons.
- The retained baseline remains 301/303 full matches and 302/303 file/exit
  matches, with the two documented intentional differences.
- GitHub CI passed the new regressions. At the review's last check, tiny/package
  checks were still running. This document does not claim final CI success.
- No GitHub releases were published at the time of review.
- Older portable-package and console qualification passed, but those results
  belong to older binaries.

Recommended target: **0.1.0 as an explicitly experimental Linux x86_64 release**,
with the default editor as the primary download.

## Working ownership and evidence

Codex owns implementation, permanent regression tests, specifications, and Git
delivery. Independent testing models can validate frozen candidates and report
findings without changing production code or weakening expectations.

Start with these records:

- [Development progress](NARO_DEVELOPMENT_PROGRESS.md)
- [Latest verification summary](validation/claude-review.json)
- [Next steps and historical restart context](NARO_NEXT_STEPS.md)
- [Independent tester handoff](NARO_TEST_AGENT_HANDOFF.md)
- [Console and release closure specification](spec/21-console-release-closure.md)
- [Historical closure evidence](validation/closure/README.md)
- [Installation and packaging instructions](INSTALL.md)

Local evidence, not included in a normal GitHub clone:

- Claude report: `target/naro-test-runs/claude-zSR4qq/CLAUDE_TEST_REPORT.md`
- Codex verification: `target/naro-test-runs/codex-claude-x1n2fz12/`
- Verified fixed binary in that directory: `candidate-v2.bin`

The fixed binary was built before the delivery commit and correctly retains its
original build revision. Its SHA-256 is
`cb8e5566abeae2e18b2cb38ea5f67fc77e20aa197eb9fee00a971b691d2cdad2`.
Do not substitute the earlier `candidate-final.bin` or relabel a historical
binary. The evidence directory's progress and attempts records explain them.

## 1. Set release scope and acceptance criteria

Status: completed locally. See [the release checklist](RELEASE_CHECKLIST.md).

Priority: required before final qualification.

- [x] State supported architecture, Linux runtime requirements, tested
  environments, and known compatibility differences.
- [x] Decide whether tiny is a release download or remains an optional source
  build. Decision: ship the default profile; tiny remains source-build only.
- [x] Separate required release gates, accepted differences, and deferred work.
- [x] Keep physical keyboard certification, additional operating systems, and
  exhaustive nano compatibility outside the stated scope unless explicitly
  added and tested.

**Completion:** one release checklist defines the supported preview and its
acceptance criteria. Distributing tiny requires its own artifact qualification
and installation guidance.

## 2. Bring release qualification tools up to date

Status: implemented and locally tested. Full candidate qualification remains
pending in later steps.

Priority: required before relying on the final release gate.

The original review found that the [host runner](tools/run_closure_host.py),
[Ubuntu environment runner](tests/follow-up/environment.sh), and
[closure collector](tools/collect_closure.py) used the older closure inventory.
The collector checked the historical 53 follow-up comparisons without the
newer wrap, filter, and release-fixes suites. All three are now mandatory
on both environments, with complete artifact validation.

- [x] Extend both runners and the final gate to require those newer suites.
- [x] Check exact scenario inventories, assertions, binary identities, and
  actual subprocess results.
- [x] Preserve the original 53-case expectations and declared differences
  separately; do not replace them with a larger unexplained aggregate count.
- [x] Add focused gate tests proving missing reports, wrong binaries, incomplete
  scenarios, and failed assertions prevent acceptance.

**Completion:** final gate success necessarily includes recent regression
coverage. Running the old collector unchanged is insufficient.

## 3. Close targeted behavioral gaps

Priority: before final source freeze.

Use the pinned GNU nano reference and identical inputs. Verify that each probe
actually executes its named operation.

| Area | Work to finish |
| --- | --- |
| View mode | Combine `-v` with bracketed paste; check buffer bytes and modified state. |
| End-of-file wrapping | Exercise `-L`, wrapped final lines, and a subsequent join that actually meets the fill condition. |
| Structural edits | After each relevant operation at the special final empty line, demonstrate that the intended join actually occurs. |
| Soft-wrap navigation | Cover PageUp/PageDown, additional tab widths, narrow/wide resizing, and cursor/viewport behavior. |
| Selections | Reverse mark direction across a wrap split, then cut and undo/redo. |
| Quoted text | Exercise Unicode whitespace in quote prefixes through wrapping and history. |

- [ ] Retain reference observations and explicit assertions for each case.
- [ ] Use corrected structural probes rather than treating the original
  operation-free matching probes as coverage.
- [ ] Add a permanent regression before fixing any newly discovered defect.
- [ ] Record any proposed deviation individually for review.

Three new permanent tests already partly close the tab-boundary gap. Do not
describe that area as completely untested or repeat completed work without a
new coverage reason.

**Completion:** cases match the oracle or have individually reviewed deviations;
saved bytes, cursor/history state, and the intended operation are checked.

## 4. Freeze a release candidate with unambiguous provenance

Priority: required after necessary development is complete.

- [ ] Build from a clean, committed checkout.
- [ ] Keep host, portable Ubuntu, tiny, and sanitizer builds separate.
- [ ] Record commit, production-source fingerprint, compiler, features, native
  dependencies, executable hash, and reference identity.
- [ ] Preserve existing tester exports and historical attempts; use fresh
  output directories.
- [ ] Preserve the original identity of `candidate-v2.bin`; do not relabel it as
  a build of the later delivery commit.

**Completion:** every report identifies its exact executable, and the eventual
downloadable binary is the executable tested. Later documentation-only commits
may be recorded separately without claiming they produced that binary.

## 5. Refresh host and portable Linux qualification

Priority: required for the final artifacts.

Build host and Ubuntu candidates from the same frozen production source.

- [ ] Run the 303-case terminal corpus, CLI checks, and regex checks on both.
- [ ] Run historical follow-ups plus wrap, filter, and release-fixes on both.
- [ ] Refresh file-write failure, backup, recovery, signal, and terminal-mode
  restoration checks.
- [ ] Refresh installed assets, locale behavior, and existing 1 MiB/10 MiB file
  checks.
- [ ] Run host-only isolated root/home cases and the separate no-home assertion.
- [ ] Build and use the portable environment's own reference executable and
  observations; host results do not certify another libc or locale setup.
- [ ] Record measured runtime and native-library requirements.

Keep existing declared differences visible. Any new unexplained mismatch blocks
qualification rather than being absorbed into comparison normalization.

**Completion:** passing, attributable reports for both environments with no new
unexplained failures.

## 6. Refresh genuine console qualification

Priority: required by the existing scoped release contract.

- [ ] Run all 19 guest-VT cases against each optimized host and portable
  candidate.
- [ ] Separately run the eight ioctl-model scenarios.
- [ ] Check keyboard handling, cursor position, screen attributes, saved bytes,
  and restoration of terminal and keyboard modes.
- [ ] Use the isolated VM fixtures in the console release specification.

**Completion:** current-binary results for both environments. Describe them as
guest Linux VT testing with emulated keyboard input. Physical keyboard/operator
testing remains deferred.

## 7. Build and verify distribution packages

Priority: required after artifact qualification.

- [ ] Package the qualified portable binary with matching source, checksums,
  provenance, licenses, credits, translations, syntax files, and installer.
- [ ] Test private-prefix installation, paths containing spaces, symlink
  launching, catalog discovery, and syntax loading.
- [ ] Verify offline source rebuild and malformed archive rejection.
- [ ] Verify uninstall ownership and preservation of modified/unrelated files.
- [ ] Confirm distributed artifacts do not enable `test-hooks`.
- [ ] Verify the packaged executable is byte-identical to the qualified one.
- [ ] Resolve full/tiny archive naming before distributing both profiles.

Full and tiny currently produce identical archive names and install the same
executable name. Either publish only the default package for 0.1 or establish
distinct download names and explain that profiles occupy the same installation
slot. Do not overwrite historical package directories.

**Completion:** the archive contains the exact qualified binary, matching source
builds successfully, and installation/removal checks pass. Source rebuildability
is not a claim of bit-for-bit reproducibility unless separately demonstrated.

## 8. Reconcile documentation, coverage, and public claims

Priority: required before announcement.

- [ ] Update README, INSTALL, IMPLEMENTATION, release notes, progress, handoffs,
  and validation indexes around the final candidate.
- [ ] Replace ambiguous wording such as “the tested release” with an actual
  candidate or release identity.
- [ ] Clearly mark historical qualification and superseded restart instructions.
- [ ] Explain intentional nano differences and remaining limitations.
- [ ] Review all nine unresolved audit citations: connect them to real evidence,
  correct stale references, or explicitly retain them as uncovered.
- [ ] Document prerequisites for external tools and optional features.
- [ ] Explain the native C bridge and system libraries; avoid claims of pure
  Rust, complete compatibility, or a completed security audit.

A passing audit currently does not mean every citation is resolved.

**Completion:** a new user can determine support, install the editor, understand
limitations, and report a useful bug without reading development history.

## 9. Prepare community distribution and reporting

Priority: required review before announcement.

- [ ] Review final archives for copyright notices, upstream attribution,
  per-file license information, and corresponding source.
- [ ] Preserve GNU nano and reused asset notices.
- [ ] Verify GitHub's actual private vulnerability-reporting configuration and
  align SECURITY.md with it; its current text says it is not enabled.
- [ ] Prepare release notes and a bug-report template requesting version/build
  identity, OS, terminal, locale, synthetic reproduction, and expected/actual
  behavior.
- [ ] Inspect the publication file list to exclude unrelated local session
  exports and private material.

This review has not established comprehensive licensing clearance.

**Completion:** clear attribution, matching source, accurate installation
guidance, and working public/private reporting routes.

## 10. Preserve evidence and complete the release decision

Priority: required for continuity and publication.

- [ ] Back up final evidence and artifacts outside `target/`. That directory
  survives a reboot but not `cargo clean` or disk loss.
- [ ] Keep compact reports in Git with hashes and locations for larger
  recordings.
- [ ] After each stage, record completed work, failures, owned running
  processes, and the exact next action.
- [ ] Verify the final gate, final GitHub CI, remote commit, archive checksums,
  and release contents.
- [ ] Prepare a concrete tag, release description, and asset list for review.
- [ ] Publish only as a separately authorized action; preparing this plan does
  not publish a tag, release, or replace the system editor.

**Completion:** another person can identify the tested source and binaries,
locate the evidence, reproduce qualification, and resume without reconstructing
the conversation.

## Recommended execution order

1. Agree scope and update the qualification gate.
2. Close targeted gaps and repair any demonstrated defects.
3. Freeze the final production source and candidates.
4. Qualify host, Ubuntu, and console behavior.
5. Package and verify the exact qualified executable.
6. Reconcile documentation, reporting routes, and distribution contents.
7. Verify evidence, CI, and remote state; then make the publication decision.

Documentation drafting and distribution review can proceed while qualification
runs, provided they retain accurate candidate identities and pending statuses.

## Work that can remain deferred

The existing 86-case ASan run is completed coverage, although external native
libraries were not instrumented. Broader memory/stress work remains useful but
should not be described as wholly absent sanitizer testing.

For this scoped experimental release, Miri, Valgrind, broader fuzzing, physical
console trials, additional platforms, and extra package formats can remain
follow-up work. Tiny artifact publication is optional if the release scope says
so. These deferrals do not excuse failures in required gates or newly confirmed
data-integrity defects.

The immediate objective is to qualify and package the exact binary the community
will download.
