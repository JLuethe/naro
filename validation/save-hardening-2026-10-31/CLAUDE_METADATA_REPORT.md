# Claude final narrow metadata verification

**Result: PASS.** I found no blocker. The archives, executable and release text are byte-identical
to what attempt02 reviewed. Only `QUALIFICATION.json` and `SHA256SUMS` changed, and the
new review metadata is accurate. Publication remains unapproved and has not been performed.
This receipt is deliberately kept outside the sidecar checksums to avoid circular hashes.

## Checked (executed; records in cmd/001-018 and COMMANDS.json)

1. **Assets** (cmd 007, `tools/assets_meta.py`):
   - Working, working-prior, backup and backup-prior each hold exactly seven files.
   - Both prior sets equal the attempt02 reviewed inventory byte for byte.
   - Current working equals current backup.
   - Versus the reviewed set, only `QUALIFICATION.json` and `SHA256SUMS` changed:
     - QUALIFICATION.json: `5cedfeca…` to `55431b7f7b0e8da96ff8224c75b999d13e818550ff240606be37efb9ae2e0ce3` (23003 bytes)
     - SHA256SUMS: `08314200…` to `d6ceb5f7b73862d35ad34eb5715dca73bd218ceba668a85e9901b8bacd18d228` (541 bytes)
   - Unchanged:
     - binary archive `3d6b4d4f…`
     - source archive `062b8f73…`
     - build.json `cbe18707…`
     - BUILD-ENVIRONMENT.json `c108bd27…`
     - RUNTIME-REQUIREMENTS.md `7bc65b15…`
   - SHA256SUMS covers exactly the other six files and verifies in both locations.
   - All 7 working and 7 preserved files match the sizes, hashes and paths in the updated
     `asset-manifest.json` (`1f3c3bcc7d8dd665814de65009ecb7b6265442c17f62ee2bd421b046d330202b`).
     That manifest records tag v0.1.0, target `6473fe2043f8a7c3805e2994fea3f4f1bc8d4b50`,
     prerelease true and published false.
   - RELEASE_BODY.md is unchanged (`b1cfd14f02b8e91069ccbd64ea7ff8b334b59abaad04b3daa2644e539ddbbdcd`).
2. **QUALIFICATION.json content** (cmd 008, `tools/review_meta.py`):
   - Only `status`, `independent_review`, `pending_release_gates`, `publication_approval`,
     `final_delivery_ci` and `review_reconciled_at` changed. Identity, archive, closure
     and CI fields are unchanged.
   - Six review records:
     - Each repository copy hash equals the evidence report hash.
     - Each evidence manifest hash verifies.
     - The five non-Claude records agree with `independent-inputs.json`.
     - The Claude record is report `0aab1680…`, manifest `a4afeff9…`. Both match
       attempt02, and attempt02's manifest still verifies with no added files (that
       directory is untouched).
     - The repository `CLAUDE_FINAL_ATTEMPTS.md` equals attempt02 `ATTEMPTS.md`.
   - Scopes are attributed correctly, with no reviewer credited for another's tests:
     - host: strict 151 checks, fresh 22-case replay, setup failure, no timestamps
     - Ubuntu: strict 151 checks, fresh 10-case replay
     - console: 47 checks, no comparator replay
     - package: 41 checks, with its schema-error attempt
     - assets: 94 checks, no replay
     - Claude: 54 commands, collector rerun, both strict validators, retained failed
       attempts
   - The limits state that there was no independent full 303-case or guest-VT rerun.
   - `publication_approval` is false and `published` is false.
   - The pending gates list only John's approval and the CI, ref and asset rechecks at
     publication time.
   - `final_delivery_ci` explicitly does not claim a future run has passed.
   - No pending Claude review remains in QUALIFICATION.json, asset-manifest.json or
     NARO_RELEASE_REVIEW_2026-10-31.md (`842b93d3…`).
3. **Identities and CI:**
   - QUALIFICATION.json still records production `b934b1f…`, fingerprint `3ce5c0ee…`,
     Ubuntu `9af710db…`, host `5767ed49…`, packaging `6473fe2…`, empty features, and
     both archive hashes.
   - `verify-freeze.py` passes (cmd 013).
   - Live `gh` queries (cmd 010-012) show production run 41179989844 on `b934b1f` and
     tag-target run 41181383327 on `6473fe2`, both push events with conclusion success.
   - No later run exists yet. The review-delivery commit has not been made, so its CI
     is correctly still future.
4. **Repository state:**
   - HEAD, local refs and remote refs equal `6473fe2`. No tag exists and no release
     exists (cmd 001-006).
   - Git status, refs and remote listing are identical before and after (cmd 014-017).
   - No owned process remains (cmd 018). The earlier leftover loop, PID 1390429, is gone.

## Inspected only

- Uncommitted tracked edits to `validation/save-hardening-2026-10-31/README.md` and
  `development-checks.json` (cmd 009). They are accurate: the README summary matches my
  report's scope, and development-checks is now labelled as historical.
- `NARO_OVERNIGHT_HANDOFF_2026-10-30.md` is still modified. All three files belong to the
  coming review-delivery commit.

## Non-blocking notes

- **Stale status line:** `target/narrow-progress-release-2026-10-31/independent-inputs.json`
  (`bc6781a5…`, unchanged) still says "final Claude evidence review pending". It is a
  preserved pre-review input index, not a release asset. QUALIFICATION.json and
  reconciled-reviews.json supersede it. Leave it as history, or label it, as preferred.
- **Ambiguous sentence:** PUBLICATION_PLAN.md says "Its tracked file contents match the
  proposed tag" right after a sentence about the review-delivery commit. It means the
  source archive. Consider rewording it.

## Remaining publication-only actions (not performed)

1. Make the review-delivery commit and confirm its CI succeeds.
2. Get John's explicit approval of the tag target, prerelease setting, RELEASE_BODY.md
   and the seven assets.
3. Recheck remote refs, confirm that v0.1.0 is absent, and rehash the assets at
   publication time.
4. Create the tag and prerelease, upload the assets, then verify the downloads.

## Evidence

`cmd/` (argv, cwd, UTC start/end, stdout, stderr and status for each command),
`COMMANDS.json`, `tools/`, `cmd-batch-0*.json`, `ATTEMPTS.md`, and the controller's
`PROMPT.md` (not modified). `SHA256SUMS` lists every file except itself.
