# Optional tiny qualification

Reference: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.

Complete on 2026-10-25. The [combined gate](gate.json) passes **31/31 checks**.
The implementation was committed as `0a7cd514506ac59badd5f11219bfb0a108b66472`;
its [GitHub CI](https://github.com/JLuethe/naro/actions/runs/40173120098) passed.
Compiled source fingerprint: `2c81a3fc062fbc6d35bb2c55f1bd1cdb903833029f53361611b1a7db7bc5a03f`. The binaries report the earlier
checkout HEAD at build time; their content fingerprint matches the committed
production inputs. [Delivery metadata](delivery.json) records both identities.

| Check | Result |
|---|---|
| Tiny retained editing, prompts, bytes and terminal lifecycle | 59/59 exact fresh reference matches |
| Tiny short/long CLI, help and restricted help | 125/125 exact matches |
| Tiny Linux VT modifier ioctl models | 8/8 exact matches |
| Pinned CI assertions, including two candidate safety cases | 194/194 pass |
| Full default terminal regression | 301/303 exact; 302/303 file/exit matches; two established safety differences |
| Full CLI / regex / safety | 38/38; 162/162; both recovery/rejection cases pass |
| Rust tests | Full 6; tiny 5; all features 5 |
| Comparator / harness / namespace / console tests | 14 / 5 / 7 / 9 pass |
| Formatting and strict Clippy | Full and all-features builds pass |
| Full and tiny installation/source-rebuild checks | 15/15 each, including feature identity |
| Installed catalogs / profile-appropriate syntax checks | 44/44 each |

Both the reference and candidate restore terminal attributes on normal exit,
SIGHUP and SIGTERM; emergency saves have exact expected bytes. Neither tiny
binary requests or resets bracketed paste. Tiny retains the intentional NUL
answer rejection; invalid interactive regex is handled safely.

Equal-compiler release builds with LTO and one codegen unit measure **2,042,368
bytes full** and **856,296 bytes tiny** after stripping: **58.07% smaller**.
Tiny links ncursesw, libgcc_s and libc, with no libmagic dependency or header.
See [measurement](measurement.json); measurements use copies in harness fixtures.
The tiny package includes catalogs and PO sources, with no unused syntax files
or nanorc example. Source archives rebuild with their declared feature set.

Fresh oracle comparisons use `tools/check_follow_up.py` with suites `tiny`,
`tiny-cli`, and `tiny-vt`, explicitly selecting `~/src/nano-install/tiny/bin/nano`.
`tools/check_tiny_ci.py` checks pinned file/screen/cursor/CLI assertions and
candidate safety without needing that oracle executable. Raw runs remain in
`target/tiny-final-v1`, `target/tiny-final-cli-v1`, `target/tiny-final-vt-v1`,
`target/tiny-ci-local-v1`, `target/tiny-full-regression-v2`, and
`target/tiny-full-extras-v2`. JSON reports here are exact copies with SHA-256
links from the gate. `quality-logs/` preserves the ten quality-command outputs.

```sh
python3 tools/collect_tiny.py --terminal target/tiny-final-v1 \
  --cli target/tiny-final-cli-v1 --vt target/tiny-final-vt-v1 \
  --full target/tiny-full-regression-v2 --extras target/tiny-full-extras-v2 \
  --ci target/tiny-ci-local-v1 --measurement target/tiny-size-final \
  --quality target/tiny-quality-final --package target/tiny-package-check-v1 \
  --full-package target/tiny-full-package-check-v1 --out target/tiny-gate-recheck
```

The local executables are `target/full/release/naro` and
`target/tiny/release/naro`. Verified archives and matching source archives are
in `target/tiny-full-package-v1` and `target/tiny-package-v1`; their checksums
and exact packaging revision are recorded in the delivery receipt. These are
host-runtime artifacts; this phase does not claim a new portable Ubuntu archive
or publish a GitHub Release/tag.

The eight ioctl cases are models, not physical-console certification. Tiny is
limited to the tested pinned profile, not arbitrary upstream configure
combinations. Prior full preview, guest-VT and Ubuntu package evidence remains
historical and unchanged. Physical keyboard/operator certification, broader
platform support and the remaining source-only coverage caveats are separate.
