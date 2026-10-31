# NARO 0.1.1 tooling/readiness receipt — 2026-10-31

Final frozen source: `eb9ae23a128d291a47af0ab463f322b5a36c6fd1`.
Production and verification fingerprints, candidate/reference hashes, CI and
backup identities are recorded in READINESS_RECEIPT.json.

Source CI passed: https://github.com/JLuethe/naro/actions/runs/41235061226

Host and Ubuntu focused readiness passed. This does not qualify the full release;
Claude must run the fresh full matrix, both guest-VT sets, transport/package
checks and recomputed v2 gate before publication review. No 0.1.1 release is
published by this work.

The complete 1,130,003,320-byte backup verifies 70,014 files and 645 symlinks;
archive SHA-256 is `ebdfd767ba5729511233abd71ddfa0cb50af71cfac24d829473e702aa62b39e4`.
It is outside target on the same filesystem, not off-device.

See ../../NARO_0.1.1_TOOLING_HANDOFF_2026-10-31.md and
../../CLAUDE_0.1.1_PHASE_B_RESUME_2026-10-31.md.
