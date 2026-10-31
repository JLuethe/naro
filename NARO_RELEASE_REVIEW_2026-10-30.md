> Superseded candidate checkpoint: a confirmed narrow-terminal hidden-cursor
> mismatch requires a replacement freeze and full qualification. See
> `NARO_OVERNIGHT_HANDOFF_2026-10-30.md`. The results below remain historical.

# NARO 0.1.0 — replacement candidate release review

Preparation began October 30, 2026. Technical qualification and packaging pass.
Two independent Luna reviews pass; Claude's resumed static review is pending
the 11:50 PM quota reset. Nothing
has been published; John must separately approve publication.

## What changed

Codex implemented nano-compatible `Writing...` before writing/syncing and
`Writing to FIFO...` before a blocking FIFO open. The status uses translations,
configured styling and nano-compatible hidden-cursor behavior. Thirteen permanent
regressions hold private syscall gates until the transient screen is captured.
Both new candidates match nano on all 13; the old candidate fails all 13.

Production commit: `16f6398968adc1f815055a4413cf0465aed28126`.
Packaging and proposed tag commit: `d5ddabe592d50912aa7b9fb932267783a9867190`.
The exact source archive matches the packaging commit's tracked files and includes
both the synchronized step3 save test and the new save-progress suite. Its
production fingerprint matches the frozen executable. No editor rebuild was
substituted during final documentation packaging.

## Completed qualification

| Area | Host | Ubuntu |
| --- | --- | --- |
| Terminal corpus | 303 recorded / 301 full / 302 file-exit, six exclusions | Same, against its own reference and fresh observations |
| CLI / regex | 38 / 162 pass | 38 / 162 pass |
| Historical follow-ups | 53 cases, 51 exact | Same two declared cleanup differences |
| Newer exact suites | 132/132 | 132/132 |
| Root/home | 27 exact plus asserted no-home behavior | Not applicable |
| Guest-VT | 19/19 exact | 19/19 exact |
| Recovery, signals, write failures, locales, large files | Pass | Pass |
| Package and offline source rebuild | Pass | 15/15 for final archive |

The complete technical gate passes **99/99** with the final packages.
Transport passes 6/6; final ordinary-prefix checks 5/5; archive audit 22/22;
41 catalogs and 44 asset checks; 45 installed documentation links audited,
including 11 repository links pinned to the packaging revision. Archive/source
destinations were checked; external endpoints were not fetched by that audit.

No new difference was accepted. The existing invalid-regex, NUL-as-Yes, two
signal-cleanup and isolated-root no-home differences remain explicit. The six
corpus exclusions and nine unresolved specification citations remain disclosed.
Optional tiny binaries, physical keyboard trials, other platforms and a security
audit remain outside this release's qualification scope.

[Qualification evidence](validation/save-progress-2026-10-30/README.md),
[final package gate](validation/save-progress-2026-10-30/final-package-gate.json),
and [source CI](https://github.com/JLuethe/naro/actions/runs/41173595090)
identify the measured results. The proposed tag's CI is
[41174872521](https://github.com/JLuethe/naro/actions/runs/41174872521).

## Exact proposal to review

- Annotated tag **v0.1.0**, targeting **d5ddabe592d50912aa7b9fb932267783a9867190**.
- GitHub **prerelease**, titled **NARO 0.1.0 — experimental Linux x86_64 release**.
- [Release description](docs/release-v0.1.0-save-progress-review-2026-10-30/RELEASE_BODY.md).
- Exactly the seven files in the [asset manifest](docs/release-v0.1.0-save-progress-review-2026-10-30/asset-manifest.json).
- [Publication and post-upload verification plan](docs/release-v0.1.0-save-progress-review-2026-10-30/PUBLICATION_PLAN.md).

The primary executable is the qualified Ubuntu build, SHA-256
`b95bb4f9984f8e321fbd69e2a4e3058c7f184d6b35a8ae7650f6f5b7897f90bf`.
The host executable is retained as qualification evidence, not another download.

Working downloads: `target/save-progress-release-2026-10-30/downloads/`.
Verified preservation: `/home/john/Backups/naro/2026-10-30-save-progress/`.
The freeze, full matrix and package evidence are preserved outside target.
These are same-disk backups, not off-device protection. Prior candidates and
reports remain intact; unrelated local files and old tmux sockets were untouched.

## Completed independent reviews

- [GPT 6 Luna behavioral review](validation/save-progress-2026-10-30/LUNA_SAVE_PROGRESS_REPORT.md):
  fresh 13/13 host and 13/13 Ubuntu, old-binary and wrong-assertion negative
  controls, complete raw-evidence checks for 132 cases per environment, and a
  fresh 99/99 whole-release collector. No editor blocker found.
- [GPT 5.6 Luna asset/source review](validation/save-progress-2026-10-30/ASSET_REVIEW_REPORT.md):
  final 116/116 checks, including exact asset inventories, checksums, archived
  executable/source identities, original synchronized test and packaged links.
  Prior runtime package results were inspected and bound to these exact archives.
- [Verified review backups](validation/save-progress-2026-10-30/independent-luna-backups.json)
  preserve both reviewers' reports, raw results and all attempts. Root reviewed
  the conclusions and independently reopened the backup payloads.

## Remaining review

Claude's resumed static review and final evidence/metadata review must finish;
any blocker must be repaired and requalified. The completed Luna reviews remain
separately attributed and are not described as Claude testing.
After that, update the qualification sidecar and hashes with the actual review
result, verify final CI and remote identities, and obtain John's approval of the
exact proposal. Testing alone does not authorize tag creation or publication.
