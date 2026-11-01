# NARO 0.1.1 Ubuntu launcher repair — 2026-10-31

## Confirmed diagnosis

Phase B attempt02 host qualification completed all 46 stages with exit 0.
Ubuntu stopped at CLI with 25 of 32 required receipts written. CLI was 37/38;
tmux cleanup also failed and replaced the original failure exit with 125.
Guest VT, transport and closure were not run. Frozen inputs remain unchanged.

The CLI rcfile includes the historical absolute GNU syntax installation path.
It exists on the host but was missing in the Ubuntu container. An independent
pinned-container reproduction confirms that both NARO and Ubuntu's own nano print
nothing without that path. All 44 bundled syntax files match the historical GNU
installation byte for byte. Providing those frozen assets at the same path as a
read-only mount restores the expected output; all 38 CLI comparisons pass.
No original scenario, recorded GNU output or acceptance policy needs changing.
The same mount also supplies the historical absolute c.nanorc render include.

The EXIT trap treated tmux's already-dead sockets as cleanup errors. Cleanup now
uses the shared bounded Python helper, retains each real tmux client exit/stdout/
stderr and probe result, removes only confirmed dead sockets in the private root,
and records a separate cleanup success boolean. Unknown errors, timeouts,
unremoved sockets and socket symlinks fail. Host cleanup honors the same result.
The trap retains the original command exit when cleanup succeeds. CLI checks run
earlier, before the long terminal corpus; required stage membership stays 32.

Production source, assets, default features and identity policy are unchanged.
A new complete source/tool freeze and provenance-bound builds are still required.

## Evidence and preservation

Work: `target/ubuntu-launcher-repair-0.1.1-2026-10-31/`.
Original stopped attempt: `target/naro-test-runs/claude-0.1.1-phaseB-2026-10-31-attempt02/`.
Verified archive: `/home/john/Backups/naro/2026-10-31-phaseB-attempt02-blocked/blocked-phaseB-attempt02.tar.gz`.
SHA-256: `93fe887be9b70ca71e321414f29ecfd5ed343cb10503b6e23b90f57dd4432317`.
The archive preserves 14,543 files and 18,631 total members, including verified
bytes, permission modes and exact membership. Original evidence was not edited.
This is outside target on the same filesystem, not an off-device backup.

The focused Ubuntu development proof uses prior frozen production executables
and an explicitly overlaid repaired tools directory. It is a reproduction and
tooling test, not qualification of the replacement candidate hashes.
It includes the absent-path control, full CLI 38, launcher/process unit checks,
and actual EXIT-trap tests retaining original exits 0 and 17 with stale sockets.
The first host process-unit run caught an overly eager shutdown probe; bounded
retry was restored before the successful rerun. Both attempts are retained.

## Completion tasks

1. Finish affected tooling tests and record the final verification fingerprint.
2. Commit the reviewed tooling, freeze that exact commit, rebuild default host
   and Ubuntu candidates, and prepare fresh guest fixtures without booting them.
3. Exercise the complete Ubuntu launcher, requiring all 32 receipts, package
   checks, complete sentinel, unchanged inputs and owned cleanup; investigate any
   failed or missing stage. Run focused host readiness for the replacement hash.
4. Preserve the replacement freeze and evidence outside target and deliver a new
   exact-hash Claude handoff for independent qualification/closure. Never mix
   attempt02 candidate hashes with replacement reports or publish a release.

Final identities, validation and remaining work belong in the completion handoff.

## Collector contract audit

Review of the complete Ubuntu-to-collector contract found that the launcher also
failed to retain top-level `naro` and `reference.bin` copies. Per-suite copies
existed, but the collector requires these two exact root inputs. The launcher now
retains both verified frozen executables before starting the container, preserves
their modes and writes a source/destination/hash receipt. Wrong inputs and existing
evidence fail closed. This regression is covered before the final freeze. The
first complete repaired Ubuntu run remains diagnostic evidence for its own older
source/tool fingerprint; replacement candidates require their own validation.
