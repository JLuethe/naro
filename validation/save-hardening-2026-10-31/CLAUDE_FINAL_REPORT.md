# Claude final evidence and package review — attempt02

**Result: PASS for the reviewed scope. No technical release blocker and no unexplained
mismatch found.** This is a technical readiness finding only. It does not approve,
tag or publish anything. Publication still needs John's explicit approval, and the
pending metadata reconciliation (item N1) still has to happen.

| Item | Value (confirmed) |
| --- | --- |
| Production commit | `b934b1fcefa74adcf631c39b20ecd133c70edc59` |
| Production fingerprint | `3ce5c0ee2d62983b32c1d71664c3404c799ff8fc08c16f6bfdb0b90d2acc21bd` |
| Host frozen executable | `5767ed4938e25b0b49c0a9c546959a88260a9e2cbffb6dd472fe160c4ea666a7` |
| Ubuntu frozen = archived executable | `9af710dbb614423b53425c093a41a95b4733cfd539bfe40047b1bdac0bd7419d` |
| Packaging / proposed tag target | `6473fe2043f8a7c3805e2994fea3f4f1bc8d4b50` (HEAD = origin/main) |
| Binary archive | `3d6b4d4f67fa97060993d31f4e75b6a83f65f52a465ce3efaf7334dead42179f` |
| Source archive | `062b8f73b3d6aaa6b32f421a0cc182e142804ea8b6c295a01af707c8023362be` |
| closure/gate.json | `6898b6f2bae9be8a31f7c517483b67e7f78a35b68ec687886fdc5c053fe0389e` |

No `v0.1.0` tag exists locally or on origin, and `gh release list` is empty.

## A. Executed in this session

Every command's argv, cwd, UTC start/end, stdout, stderr and status are in `cmd/`;
`COMMANDS.json` indexes them.

1. **Freeze** (cmd 013, 044): `verify-freeze.py` exited 0 before and after.
   - Frozen source HEAD is `b934b1f` with no tracked changes.
   - No active Git hooks (samples only) and no `core.hooksPath` in the repo, frozen
     source or packaging source (cmd 016, 019, 020).
2. **Tracked state:**
   - HEAD, show-ref, status and diff-stat are byte-identical before and after.
   - The production-to-tag diff touches only docs and validation files (cmd 008).
3. **Assets** (cmd 021-023, `scratch/assets/verify-assets.json`):
   - **Seven files:** exactly seven working and seven backup files. They are identical
     in bytes and SHA-256 and match `asset-manifest.json`.
   - **SHA256SUMS:** covers the other six, and every line verifies in both locations.
   - **Package copies:** the `package/` copies equal the downloads.
   - **build.json identity:** revision `b934b1f`, fingerprint `3ce5c0ee…`,
     source_revision `6473fe2`, `dirty=false`, features `default` with an empty
     compiled list.
   - **Source inventory:** the 1433 `source_files` entries equal the Git blobs of
     `6473fe2`. The source archive members are safe and equal those blobs.
   - **Fingerprint:** the frozen tool's `source_fingerprint()` of the extracted source
     archive, and of the repo tree, is `3ce5c0ee…`.
   - **Executable:** the archived `bin/naro` is `9af710db…`.
   - **Payload:** all 138 files match build.json hashes and modes.
   - **Installer:** `install.py` equals the tag's `tools/release/install.py`. Its hash
     `3350386c…` matches the ordinary-prefix report.
   - **manifest.json:** equals build.json minus `source_files`.
   - **Docs:** all ten packaged docs equal the tag text, except for relative links
     rewritten to pinned `6473fe2` URLs.
4. **Complete collector rerun** (cmd 024-025):
   - `collect_closure.py` ran from the packaging checkout with the recorded inputs into
     the new private output `scratch/closure-rerun/`.
   - Result: 101/101 checks, no failures.
   - All 52 output files are byte-identical to the recorded `closure/`.
5. **Strict validator** (cmd 027 host, 028 Ubuntu):
   - I ran `check_closure_regressions.py` with the frozen binaries and references
     taken from the freeze directory.
   - All six suites pass with zero problems in each environment.
   - This validator reopens every recording and recomputes expectations and
     comparisons.
6. **Independent raw audit** (cmd 026, `scratch/raw-audit/raw-audit.json`):
   - This is my own script; it imports no project code. Zero failures.
   - **New regressions:** 151 named regressions per environment (58/6/15/40/22/10).
   - **Every recording, both sides:** binary identity, steps_ok, step checks, checks,
     helper statuses 0, exit 0 with no signal or notes, and raw-output hash and size
     all verified.
   - **Ubuntu's own reference:** its reference recordings bind to `6540492f…`, not the
     host's `b4fe2cb3…`.
   - **Historical:** 53/51. The only non-matches are `TEST-NEXT-TOOL-003-SIGTERM` and
     `-SIGHUP`, under `Q-TOOL-001`. VT-ioctl is 8/8.
   - **Terminal corpus:** 303/301/302 with six skipped and worker statuses 0.
     - Skipped: BROWSE-003, CLI-025/032/033/035 and KEY-007 (tiny).
     - Declared non-matches: `TEST-CLI-057` (Q-DEF-001) and `TEST-PROMPT-NUL-001`
       (Q-PROMPT-001).
     - These sets are identical on host and Ubuntu.
   - **Other suites:** CLI 38, regex 162, safety 2, large 2, panic 3.
   - **Host-only:** checkpoint 35/35 checks at status 0. Root is 27/27 exact. No-home
     has 1 case, asserted as `Q-ROOT-NOHOME-001`. Extensions 6/6.
   - **Console and transport:** console 19/19 per candidate, transport 6/6.
7. **Source suites** (cmd 029-034):
   - save-progress has 22 cases, and the original 13 from `16f6398` are retained
     unchanged.
   - tiny-safety has 3 cases, and the original 2 are retained unchanged.
   - save-safety has 10 cases.
   - step3-gaps keeps its 40 cases, including the synchronized
     `TEST-STEP3-EOF-NOFINAL-LIVE` that waits for "Wrote 2 lines".
   - All of these are identical between production and the tag.
8. **CI** (cmd 035-038):
   - A read-only `gh run view` confirms run 41179989844 on `b934b1f` and run
     41181383327 on `6473fe2`. Both are push events on main, completed with `success`.
   - Every step succeeded, including the save-feedback, prepend/backup and optional
     tiny steps.
   - The tiny step runs `check_tiny_ci.py` over `tiny-safety`.
   - The workflow is identical at production and at the tag.
9. **Independent review inputs** (cmd 039):
   - All five reports and manifests in `independent-inputs.json` match their recorded
     hashes.
   - Every file listed in those manifests rehashes correctly (119/69/12/17/8 files),
     and no files are unlisted.
10. **Backups** (cmd 041, `scratch/backup-verify-attempt2/backup-verify.json`):
    - **Receipts:** every archive's bytes and SHA-256 match its receipt.
    - **Members:** all are safe; hardlinks resolve inside the archive.
    - **Freeze archive:** contains every `freeze.json` file entry, plus `.git` admin
      files.
    - **Qualification archive:** equals the live `EVIDENCE-SHA256SUMS` (6081 entries),
      and the live tree still matches that manifest.
    - **Packaging archive:** equals the packaging snapshot manifest (1762 entries), and
      the live workspace still matches that snapshot.
    - **Independent behavior archive:** 203/203 payloads.
    - **Development archive:** equals its inventory (6822 entries).
11. **Credential-format scan** (cmd 042, `scratch/cred-scan/cred-scan.json`):
    - **Scope:** 1580 objects (seven downloads plus every member of both archives),
      checked against 10 patterns.
    - **Result:** no hits.
    - **Limits:** this is a bounded format scan, not a security audit. The project's own
      scan covers source-archive files only, with four patterns; it is correct but
      narrower.
12. **Processes** (cmd 054): no process owned by this review remains.

## B. Inspected, not re-executed

- **Package checks:**
  - package-check/report.json has 15/15 named checks, bound to the archive hash.
    package-check.log's "44" is the separate asset report.
  - The rejection tests feed real tampered inputs.
  - The offline `cargo build --release --offline` log succeeds, and the rebuilt
    fingerprint and features pass.
- **Other package reports:** ordinary-prefix 5/5 (install 138, uninstall 138,
  translation "Hilfe"). archive-audit 23/23. publication-audit has 45 links, 11 pinned.
- **Release commands:** every stage in release commands.json exits 0, and the
  containers ran with networking disabled.
- **Negative controls:** in the development evidence, the old and pre-fix binaries fail
  the new assertions. This covers old-final01, the fallback, short-footer and
  footer-layout negative01 runs, and the pre-fix progress completion. The FIFO control
  matches, as designed.
- **Prior Claude findings:**
  - The cache review's tiny-only caveat is resolved: production `src/editor.rs:608-615`
    keeps the alert only for tiny `Interrupted`.
  - Default resize behavior is unchanged.
- **Review packet:** RELEASE_BODY.md's hash matches the manifest.
  - Identities agree with package/build.json across the review file, PUBLICATION_PLAN,
    RUNTIME-REQUIREMENTS and QUALIFICATION.json.
  - QUALIFICATION.json's gate hash equals my rerun.
  - Known limits are disclosed consistently.
- **Independent agents' scope:**
  - **Host (Luna):** strict check of 151 cases plus a fresh save-progress replay of 22
    cases. Timestamps are unavailable, which the report discloses; not treated as a
    failure.
  - **Ubuntu:** revalidation of 151 cases plus a fresh save-safety replay of 10 cases.
  - **Console:** report and provenance audit only, not a raw comparator replay.
  - **Package and asset agents:** recomputed identities; runtime results were inspected,
    not repeated.
  - **Not covered:** no agent reran the 303-case corpus, CLI/regex, historical, VT,
    transport or root suites. Those rest on the single root qualification. I
    revalidated them at report level, and the 151 from raw recordings.

## C. Non-blocking notes

- **N1 – pending metadata (expected):** QUALIFICATION.json, the asset-manifest status
  and NARO_RELEASE_REVIEW_2026-10-31.md still say the final review is pending or in
  progress. This is accurate for this checkpoint, and Codex will reconcile it.
- **N2 – uncommitted tracked edit:** `NARO_OVERNIGHT_HANDOFF_2026-10-30.md` has 20
  uncommitted added lines (git diff SHA-256 `b1a7dc4fef45b372f35534eb6a26301196d2a5f1e55eb27855518e31d5b770e1`).
  - The edit was present and unchanged before and after this review.
  - It is not in the tag commit or the packages.
  - Commit or drop it deliberately before the review-delivery commit.
- **N3 – stale status text:** `validation/save-hardening-2026-10-31/development-checks.json`
  still says "fresh frozen qualification pending". The README supersedes it; this is
  cosmetic.
- **N4 – local paths:** the source archive contains `/home/john/...` paths in tracked
  handoff documents and spec evidence. These are informational, not credentials.
- **N5 – leftover process:** a shell loop from an earlier session (PID 1390429, polling
  a tiny-builds pgrep) is still running. It is not owned by this review.

## D. Remaining limits

- **Tiny:** the final tiny-only guard is covered by CI assertions only. Tiny is not
  downloadable and not a full-parity claim.
- **Console:** guest VT with emulated PS/2 input, not a physical keyboard.
- **Not claimed:** byte-for-byte reproducible rebuilds, other platforms, a security
  audit or exhaustive nano parity.
- **Backups:** on the same filesystem, not off-device.
- **Packaging snapshot:** `EVIDENCE-SHA256SUMS` in the release workspace is the
  snapshot from before the independent review, bound to
  `packaging-before-independent-review.tar.gz`. It is not a current full-workspace
  inventory; `independent-inputs.json` and Git admin files are outside it, as intended.

## Evidence index

- **Reports:** `CLAUDE_FINAL_REPORT.md`, `PROGRESS.md`, `ATTEMPTS.md`.
- **Command index:** `COMMANDS.json`.
- **Input hashes:** `INPUT-HASHES.json`, the SHA-256 of the key inputs reviewed.
- **Raw records:** `cmd/001-054`.
- **My scripts:** `tools/` and `batches/`.
- **Private outputs:** `scratch/`.
- **Checksums:** `EVIDENCE-SHA256SUMS` covers every file here except itself.
