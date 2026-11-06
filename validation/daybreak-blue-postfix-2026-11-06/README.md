# Daybreak Blue post-fix retest — NARO 0.1.2

**Verdict: GO for the named repaired default and tiny package/source artifacts
within the stated deterministic Linux scope.** No new product failure was
observed. This is technical qualification evidence, not publication approval or
closure of issues #12, #14, #15 or #16.

## Provenance

The authoritative outer invocation selected Codex CLI 0.166.0, access program
`daybreak_blue`, model `gpt-6-sol`, and high reasoning effort. Daybreak Blue is
the access-program selection, not a separate model name or version. Thread:
`01a1b03f-60ed-70d2-b236-a6a064479d6d`.

```sh
codex exec --cyber-access-program daybreak_blue -m gpt-6-sol \
  -c 'model_reasoning_effort="high"' --approve-for-me \
  -C /home/john/Code/naro --json \
  -o target/daybreak-blue-retest-2026-11-06/attempt03/final-message.md \
  - < target/daybreak-blue-retest-2026-11-06/attempt03-prompt.txt \
  2>&1 | tee target/daybreak-blue-retest-2026-11-06/attempt03/events.jsonl
```

| Role | Identity |
| --- | --- |
| Compiled runtime base | `2888560a9a2709469334a417d1ad9ac3a91c30ba` |
| Repaired package/source commit | `9d7cd10530501cf7f352b043d25e80756ff7d939` |
| Repaired package/source tree | `11e6441073fb06637b526cc742d750171697a43c` |
| Receipt-only descendant | `5e2bcc47068f76a17817055cc463a32dafeb4187` |
| Production-source SHA-256 | `7b6ef4e024bc5d25f59fb66eebad7f8297d4be4f49a34d1037c3b8d4f928e636` |
| Verification-input SHA-256 | `d5fadd77e0676fe91e8b6f0f09295b8837df7ce9e16c279034ebb5fcc010d3f1` |

Testing used a fresh detached `git clone --no-local --no-checkout` at the exact
package commit. It ended clean, had no alternates, and passed `git fsck --full
--no-reflogs`. The main checkout remained at `5e2bcc4`, tree `72abf08`, branch
`main`, 26 commits ahead of upstream, with no tracked or staged changes. Its
1,998 pre-existing untracked files were hashed before and after and preserved.

## Repair and package decision

`IMPLEMENTATION.md` now identifies 0.1.2, labels 0.1.1 qualification as
historical, and points exact artifact identity to `manifest.json`, `build.json`,
`SHA256SUMS` and `NARO_BUILD_INFO`. The package builder rejects a missing,
mismatched or conflicting current version and a hardcoded current candidate hash
before reading the candidate binary or creating output. The package verifier
checks the installed and source status documents.

The compiled editor source did not change after the original runtime
qualification. Package verification input did change, so all package checks and
the relevant runtime continuity matrices were rerun. The source archives contain
the exact corrected status document. Installed copies contain the expected
immutable-revision link transformation. Each binary archive contains only the
intended production ELF and no test-hook executable.

| Artifact | SHA-256 |
| --- | --- |
| Production default | `894e0dcaf37d9a2ec7ee2380b0b705e35b3f0a0168455fa025523463da503e2a` |
| Production tiny | `93e990da049e779d1164e76776a7c42d01fe5d42980974f2c5b78521438177ba` |
| Test-hook default | `d1fef1e6d18117e0247e3c88b2e840acba07e859c87b871562d028c606032dee` |
| Test-hook tiny | `0eb14b9f40d2ae3b3d5060a3da5fc701b0041817ee4c8f850d042adf21dc5bea` |
| Rust-test default | `f9ce8abbc10109962474a170d06dab5ffd1768af3a35fa141e475f73fda345d4` |
| Rust-test tiny | `fa08afc4d1696cd344348fb8b3dd1b4c6b1edc73f39cd535576035b40c463ad6` |
| Replacement default binary archive | `ba132527f9c77c9eea47dc03fe2d9deeac0e6f49dadf8cdb74b7bd23d2668cf3` |
| Replacement default source archive | `de9c66b1843f7b33fb441f13524df03dc64b61329bb28761e097bcdf56f8dd22` |
| Replacement tiny binary archive | `d930a0b9051a6e4d6aa1769baaabd04a01266181cdfefda2b475abfc95474f2f` |
| Replacement tiny source archive | `662850ddf67bf777d8f1f7c4893f333ae0dd279052cadca0f1d457c7d2158db9` |

Earlier archive hashes are historical and do not identify these replacements.

## Results

- Package-document and provenance unit tests: 8/8 and 8/8.
- Installer transactions: 16/16.
- `cargo fmt --check`, strict all-feature Clippy and strict tiny Clippy: pass.
- Host Rust tests: default 72/72, tiny 39/39, all-feature 39/39; ten
  intentionally ignored tests in each profile.
- Spec/tool Python tests: 66/66 and 132/132.
- Default and tiny archive verification: 17/17 package checks and 44/44 asset
  checks each, including offline source rebuild, fingerprint/features, install,
  uninstall, malformed-archive rejection and status-document checks.
- Safe-save fault matrix: 448/448 default and 448/448 tiny, zero skips.
- Backup matrix: 1200/1200, comprising 672 save-phase and 528 backup-phase cases.
- Recovery matrix: 41/41 default and 41/41 tiny.
- Explicit save semantics: 22/22 progress and 10/10 safety.
- Lock terminal semantics: six scenarios, 35/35 assertions.
- Focused backup-alias and save-as/lock positive controls: pass.
- Two clean pre-fix regression receipts were reopened and rehashed; each still
  exits 101 for its expected historical corruption defect. The fortified
  `__open_2` parent marker remains absent and the fixed-candidate marker present.
- All 20 artifacts in the first run's final audit were reopened and rehashed.

The [command record](commands.md) lists every qualification command and outcome.
The full local evidence root is
`target/daybreak-blue-postfix-20261106T094550Z`; it contains timestamps, raw
logs, reports, fixtures, archive audits, classified attempts and before/after
checkout manifests.

## Classified non-product failures and limits

Three sandboxed Rust attempts failed only because the sandbox GID mapping made
`chown(..., 65534)` return `EINVAL`; unchanged host-permission reruns passed all
three profiles. Four operator attempts used an incorrect relative path or
inconsistent `git status` untracked formatting; corrected attempts passed. All
seven nonzero attempts are preserved and classified.

This verdict does not establish adversarial symlink-swap or rename-exchange
safety from issue #12, physical power-loss behavior, unavailable locale or
Ubuntu namespace cases, additional architectures, meaningful Miri, broader
native-library matrices, new guest-VT coverage, or closure of issue #14's nine
runtime assertion gaps. Assertion-free differential observations remain
observations. Nothing was pushed, published, tagged, globally installed or
closed.
