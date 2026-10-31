> Published and verified: [NARO v0.1.0](https://github.com/JLuethe/naro/releases/tag/v0.1.0).
> See the [publication record](NARO_RELEASE_PUBLICATION_2026-10-31.md).
> The preparation and approval text below is retained as historical context.

# NARO 0.1.0 — overnight summary and remaining work

**Prepared October 31, 2026.** The first release candidate is technically
qualified and ready for John’s review. It has not been published. The exact
proposal is in the [release review packet](NARO_RELEASE_REVIEW_2026-10-31.md).

## What happened overnight

Claude had identified a missing save-progress message required by the project
specification. John chose to implement the behavior, add regressions, and rebuild
and requalify the candidates. Further review found related save-safety and
terminal-display issues, which Codex fixed before creating a new freeze.

The fixes include `Writing...`, `Writing to FIFO...`, and `Making backup...`
messages; preserving the destination when prepend cannot read it; requiring
confirmation when a backup source cannot be read; cancellation during a blocked
FIFO open; and corrections for completion lists, translated text clipping, and
narrow terminal footers. The permanent suites contain 22 save-progress and 10
save-safety cases.

Both candidates were rebuilt from production commit
`b934b1fcefa74adcf631c39b20ecd133c70edc59` and qualified separately. Ubuntu used
its own nano executable and fresh reference observations. No new unexplained
mismatch was accepted.

| Qualification area | Result |
| --- | --- |
| Terminal corpus, each environment | 303 recorded; 301 full and 302 file/exit matches; six exclusions |
| CLI and regex, each | 38 and 162 checks passed |
| Historical follow-ups, each | 53 cases, 51 exact; two declared signal-cleanup differences |
| Newer regressions, each | 151/151 exact, including the 22 progress and 10 safety cases |
| Guest VT and transport | 19/19 per candidate; transport 6/6 |
| Host root/home | 27 exact, plus the separately asserted no-home case |
| Complete technical collector | 101/101 passed |
| Final package verification | 15/15 package checks, 5/5 ordinary-prefix checks, 23/23 archive checks; 41 catalogs and 44 asset checks |

Recovery, controlled write failures, signals, terminal restoration, installed
assets and locales, and 1 MiB and 10 MiB file checks also passed. The source
archive built offline with the matching production fingerprint. A byte-for-byte
reproducible binary rebuild is not claimed.

Independent agents rechecked the host and Ubuntu evidence and reran selected
frozen-candidate tests. Claude independently reran the complete collector,
examined raw evidence, source, packages, CI and backups, and found no technical
release blocker or unexplained mismatch. A subsequent narrow Claude review passed
after the qualification metadata and checksums were updated. Reviewers’ actual
scopes and retained setup or script errors are in the
[qualification record](validation/save-hardening-2026-10-31/README.md); those
errors were not counted as product failures or successful tests.

The qualification and final review were committed and pushed. CI succeeded for
the [production commit](https://github.com/JLuethe/naro/actions/runs/41179989844),
the [packaging commit](https://github.com/JLuethe/naro/actions/runs/41181383327),
and the [final review-delivery commit](https://github.com/JLuethe/naro/actions/runs/41183479791).
The final delivery commit is `35d2a2f7a8c7bd8adc832e13bc31ec74f3e1d2b9`.

## The proposed release

- **Release:** NARO 0.1.0 — experimental Linux x86_64 GitHub prerelease.
- **Tag:** annotated `v0.1.0` at packaging commit
  `6473fe2043f8a7c3805e2994fea3f4f1bc8d4b50`, not the later review-delivery commit.
- **Primary executable:** frozen Ubuntu build, SHA-256
  `9af710dbb614423b53425c093a41a95b4733cfd539bfe40047b1bdac0bd7419d`.
- **Binary archive:** `naro-0.1.0-x86_64-unknown-linux-gnu.tar.gz`, SHA-256
  `3d6b4d4f67fa97060993d31f4e75b6a83f65f52a465ce3efaf7334dead42179f`.
- **Source archive:** `naro-0.1.0-source.tar.gz`, SHA-256
  `062b8f73b3d6aaa6b32f421a0cc182e142804ea8b6c295a01af707c8023362be`.
- **Exact seven-file set:** [asset manifest](docs/release-v0.1.0-save-hardening-review-2026-10-31/asset-manifest.json).
- **Proposed public text:** [release description](docs/release-v0.1.0-save-hardening-review-2026-10-31/RELEASE_BODY.md).

The source archive matches the packaging commit’s tracked files and the
production fingerprint of the tested executable. The later delivery commit
adds review documentation and receipts; it is not the proposed tag target.

## What remains

1. **John reviews and approves the exact proposal:** the tag target, prerelease
   setting, release description, and all seven files. Technical test results do
   not themselves authorize publication.
2. **Immediately before publication, recheck** the remote branch and tags,
   successful CI for the proposed tag and final delivery, and all seven hashes
   against the manifest and `SHA256SUMS`. Investigate any changed state or new
   unexplained mismatch before proceeding.
3. **After approval, publish** the annotated tag at the approved packaging
   commit and create the GitHub prerelease with precisely the approved binary,
   corresponding source, and sidecars. Follow the
   [publication plan](docs/release-v0.1.0-save-hardening-review-2026-10-31/PUBLICATION_PLAN.md).
4. **Verify the published release:** download all seven assets into a fresh
   directory, check their hashes and `SHA256SUMS`, confirm tag resolution and
   anonymous links, and record the release URL and verification results.
5. **Community announcement:** prepare or post one only with John’s separate
   authorization. Update candidate wording with the actual release URL after
   publication and verification.

No tag, release, asset upload, or announcement was made during preparation.

## Known limits and preservation

The declared differences remain invalid-regex recovery, NUL as a Yes response,
two external-tool signal-cleanup cases, and isolated-root no-home tilde recovery.
Six baseline cases are excluded and nine specification-to-test citations remain
unresolved. Tiny has separate CI assertions but is not a downloadable build or a
full parity qualification. Guest-VT tests used emulated PS/2 input; physical
keyboard certification, other platforms, exhaustive nano parity, and a security
audit are outside the measured scope.

Working downloads are in
`target/narrow-progress-release-2026-10-31/downloads/`. The frozen candidates,
qualification evidence, review records, final archives, and seven download files
were preserved and verified outside `target/` under
`/home/john/Backups/naro/2026-10-31-narrow-progress/`. The final evidence archive
receipt records 14,660 files reopened and verified. These backups are on the
**same filesystem**, not off-device; an off-device copy would add protection
against loss of the laptop or drive.

Unrelated untracked files in the repository were left untouched. Full operational
details and evidence paths are in the
[overnight handoff](NARO_OVERNIGHT_HANDOFF_2026-10-30.md).
