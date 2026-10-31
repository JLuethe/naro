# Independent verification attempts

Commands were read-only except creation of this owned verification directory.

* `sha256sum target/save-progress-release-2026-10-30/downloads/* /home/john/Backups/naro/2026-10-30-save-progress/downloads/* | sort` — exit 0; all seven working/preserved hashes matched, including byte sizes.
* `python3 target/asset-independent-verify-2026-10-30/verify_assets.py` — exit 0; all checks passed.
* `git -C target/save-progress-release-2026-10-30/source rev-parse HEAD` — exit 0; `d5ddabe592d50912aa7b9fb932267783a9867190`.
* `git -C target/release-freeze-save-progress-2026-10-30/source rev-parse HEAD` — exit 0; `16f6398968adc1f815055a4413cf0465aed28126`.

No package rebuild, full terminal matrix, editor regression run, or network
publication action was performed. Existing package reports were independently
recomputed/inspected and remain untouched.

## Attempt 02 — corrected audit

At `2026-10-30T23:23:56-07:00`, `python3 verify_assets.py | tee
verify_assets_attempt02.json` exited 0 with 114/114 checks passing. This pass
adds exact SHA256SUMS coverage, package/download equality, tar inventories,
source/compiled identity equality, exact step3 waits, exact prior check-name
sets, and direct packaged-doc destination validation. The JSON separates
recomputed checks from prior runtime results inspected only.
