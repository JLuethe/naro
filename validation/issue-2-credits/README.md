# Issue #2 credits and 0.1.2 candidate checks — 2026-11-05

The 0.1.2 development tree makes `naro --credits` available in default and tiny
builds. The existing `credits` feature remains accepted for older Cargo commands.
`CREDITS.md` names this as a separate Rust port of GNU nano 9.3 at reference
revision `6ed285c3ec7a1d228def4d4e7021c6ba269f620c` and retains the named
project, native-service, license, notice, and asset-header acknowledgments.

## Focused results

Commands ran from the checkout root on 2026-11-05. Cargo was invoked with
`PATH=/home/john/.cargo/bin:$PATH` because this shell's initial PATH omitted it.

| Command or check | Result |
| --- | --- |
| `cargo build --locked --target-dir target/issue-2-credits/default` | Pass; dev build reports 0.1.2. |
| `cargo build --locked --features tiny --target-dir target/issue-2-credits/tiny` | Pass; dev build reports 0.1.2. |
| `cargo build --locked --features credits --target-dir target/issue-2-credits/legacy` | Pass; compatibility feature still builds. |
| Each executable's `--credits` stdout compared byte-for-byte to `CREDITS.md` | Pass; exit 0, empty stderr, all 797 source bytes matched. |
| `python3 tools/check_extensions.py --default target/issue-2-credits/default/debug/naro --credits target/issue-2-credits/legacy/debug/naro --panic-runs target/issue-2-credits/absent-panic-runs --out target/issue-2-credits/extensions-check` | Pass for both credits variants and the production no-panic-hook check. This invocation supplied no panic runs; recovery is outside this check. |
| `python3 tools/check_branding.py --binary target/issue-2-credits/default/debug/naro --out target/issue-2-credits/branding-check` | Pass, 5/5 CLI branding assertions. |
| `python3 -m unittest discover -s spec/tools -p 'test_candidate_expectations.py'` | Pass, 6 tests. |
| `python3 spec/tools/test_identity_review.py` | Pass, 23 tests, including exact 0.1.2 titles and rejection of old-brand residuals. |
| `python3 -m unittest discover -s tools -p 'test_package_provenance.py'` | Pass, 6 isolated package tests. The clean fixture asserted source-archive credits bytes and installed-archive transformed credits text. |
| `cargo fmt --check`; `git diff --check` | Pass. |

`tools/package.py` includes `CREDITS.md` in both its runtime document list and
source archive's tracked-file inventory. Its installed-document conversion only
changes link targets; a direct comparison confirmed all credits prose and link
labels are unchanged. LICENSE and NOTICE links remain local. The package test
uses a clean temporary Git fixture because this integration checkout has
uncommitted work and strict release packaging correctly requires a clean tree.
No 0.1.2 release archive or integrated qualification is claimed here. Actual
candidate packages and their exact source/binary identities must be checked
after the clean integration commit and release build.
