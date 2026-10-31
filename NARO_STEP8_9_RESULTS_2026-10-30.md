# Steps 8–9 completion — October 30, 2026

Step 8 documentation adoption and package reconciliation are complete. Step 9
attribution, corresponding-source, reporting-route and publication-content review
are complete for the scoped experimental 0.1.0 candidate. Final CI acceptance and
publication remain step 10; an earlier CI failure is explicitly open below.

## Delivered changes

Seventeen reviewed files were adopted, including README, installation guidance,
implementation status, release notes, coverage review, reporting guidance, bug
template, progress/indexes and historical handoff notices. John Luethe is named
and OpenAI is thanked for their generous support. Security reports go through
public GitHub issues as requested; issues are enabled and the policy explains
how to avoid posting confidential information.

All nine unresolved coverage citations, declared behavioral differences and six
baseline exclusions remain explicit. No editor code, permanent behavior tests,
reference expectations, or normalization was changed. A focused packaging change
ships ten documentation/license files and pins unshipped repository links to the
packaging source commit. Three link-handling unit tests were added and pass.

The content/package source commit is
`536d09160e4f65f8372c781ba389a59fdb5e52c7`. The compiled source remains
`fd91763c4f14d9bed8187d64d44f2136440b7b3e` and production fingerprint remains
`4cabd71741ffc8ee0357d945c67904c8a2fd0089c12e9b32a1c5b3e35c394ae6`.
The Ubuntu executable is unchanged:
`33a39eb339492720ec6166e84fea421749e0b2ec3bd612b276c2377f91b7c4a1`.
Only an isolated verification rebuild was made; it did not replace that binary.

## Exact refreshed downloads

Preferred preserved directory:
`/home/john/Backups/naro/2026-10-30-step8-9/downloads/`.
Working copy: `target/step8-release-2026-10-30/downloads/`.
The original step 7 archives and backup are intact and have their original hashes.

| Archive | SHA-256 |
| --- | --- |
| `naro-0.1.0-x86_64-unknown-linux-gnu.tar.gz` | `e8ff4445dba2bebd58c396ca1186d8d2d161efe5016bc4cd7791ed5bce5640d0` |
| `naro-0.1.0-source.tar.gz` | `c23aad0b96132b17d0da9fd8e33ee791de4aadc3d5a9d861fa2ee9795cae7e8b` |

The seven-file set also includes `build.json`, `BUILD-ENVIRONMENT.json`,
`RUNTIME-REQUIREMENTS.md`, `QUALIFICATION.json` and `SHA256SUMS`. See the
[download checksums](validation/step8-9-release-2026-10-30/download-SHA256SUMS).
The source archive contains 1,230 committed files; the binary has 138 installed
payload files. Local session exports, draft workspace, `.git`, builds and private
fixtures are excluded. Original copyright notices and per-file asset licenses
are preserved; [step 9 review](NARO_STEP9_REVIEW_2026-10-30.md) records scope and
the community announcement draft. No comprehensive rights clearance is claimed.

## Verification and preservation

| Check | Result |
| --- | --- |
| Refreshed Ubuntu package checks, including offline source rebuild | 15/15 |
| Installed assets | 44/44; 41 catalogs |
| Ordinary-prefix installation/removal | 5/5 |
| Archive inventory, hashes, source linkage and notices | 20/20 |
| Complete collector with host, Ubuntu, both VTs, transport and new packages | 97/97 |
| Documentation links | 162 active-document links; 45 installed links; 11 pinned repository links |
| Packaging link unit tests | 3/3 |
| Specification audit | Pass; same nine disclosed citation gaps |
| Freeze verification | Pass; unchanged production inputs and executable hashes |

[Compact evidence](validation/step8-9-release-2026-10-30/README.md) is checked in.
Full evidence, original review history and exact downloads are preserved outside
`target/` under `/home/john/Backups/naro/2026-10-30-step8-9/`. The evidence archive
SHA-256 is `1d28ce5c834744da4cc10bcea946926ac3f24c89524a7e6d2755079a39f91527`;
6,196 archived files were reopened and verified. Step 5/6 backup dependencies
were rehashed. These are same-disk backups, not off-machine protection.

Package construction and each validation stage ran once with exit zero. No
failed package attempts occurred. Containers were disposable; no owned test
processes remain. The original and refreshed evidence are not overwritten.

## Step 10 — exact remaining work

1. Resolve or explicitly disposition the earlier CI failure in
   [run 41168721954](https://github.com/JLuethe/naro/actions/runs/41168721954),
   commit 3629b8f. `TEST-STEP3-EOF-NOFINAL-LIVE` passed 19/20 assertions: the saved
   snapshot still showed the write prompt at cursor (20,21), while expected saved
   cursor was (2,2). File bytes and exit passed. A capture-timing race is plausible
   but unproven; do not call it resolved or relax the expectation. The failed log
   excerpt is retained. Reproduce with raw trace capture if the new CI recurs.
2. Verify successful CI and remote HEAD for the final delivery. The packaging
   commit's [run 41170067321](https://github.com/JLuethe/naro/actions/runs/41170067321)
   was in progress during packaging; check the final receipt commit's run too.
   No release-readiness claim may hide an outstanding failed assertion.
3. Recheck the seven preserved download hashes, prepare the exact `v0.1.0` tag
   target and release description, and obtain separate publication authorization.
   Publish binary and matching source together. Do not substitute another build.
4. After authorized publication, verify uploaded bytes/links and add the real
   release URL to the announcement. Off-machine backup remains optional follow-up.

No tag, GitHub Release, asset upload, public announcement, or system installation
was performed. A passing technical collector does not close the separate CI and
publication gates.
