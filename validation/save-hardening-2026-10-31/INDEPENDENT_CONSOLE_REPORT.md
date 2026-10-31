# Frozen identity and qualification monitor — final audit

Read-only review, 2026-10-31. No production, VM, or release files were modified.

Frozen identity checks:

- `target/release-freeze-narrow-progress-2026-10-31/freeze.json` is present and records production source commit `b934b1fcefa74adcf631c39b20ecd133c70edc59`, production source SHA-256 `3ce5c0ee2d62983b32c1d71664c3404c799ff8fc08c16f6bfdb0b90d2acc21bd`, host binary `5767ed4938e25b0b49c0a9c546959a88260a9e2cbffb6dd472fe160c4ea666a7`, and Ubuntu binary `9af710dbb614423b53425c093a41a95b4733cfd539bfe40047b1bdac0bd7419d`.
- `source-identities.json` agrees with freeze metadata.
- `python3 target/release-freeze-narrow-progress-2026-10-31/verify-freeze.py` exited 0: “Frozen source, tools, binaries, references, and recorded inputs match.”
- Host and Ubuntu build records bind revision, source SHA, features, reference hashes, and toolchain/environment metadata. Host and Ubuntu candidate hashes match freeze.json.

Independent final audit:

- Reproducible executable audit: `audit_final.py`, rerun as `python3 target/frozen-console-review-2026-10-31/audit_final.py`, status `0`, output `final-audit-rerun.json`, with exact timestamp/status in `rerun-status.log`. It passes 47 checks and 38 suite rows. It verifies both candidate inventories contain exactly 19 named suites; every host and Ubuntu report result has `match=true` and no differences; report candidate hashes equal the frozen host/Ubuntu binaries; report reference hashes equal the frozen guest reference; and actual candidate/reference JSON files exist with independently recomputed SHA-256 values.
- Scope clarification: the executable independently checks report verdicts/differences, raw candidate/reference artifact presence and hashes, frozen binary identities, transport, upload, and runtime provenance. The candidate/reference JSON files are snapshot artifacts rather than comparator result-schema objects, so it does not rerun the comparator directly on those raw snapshot files; comparator verdicts are independently checked from the completed reports.
- Guest-VT host and Ubuntu reports each contain 19/19 matches. This is genuine guest `/dev/tty1` QEMU/KVM evidence, not the separate 303-case host terminal qualification.
- Transport report independently has six checks, all true: incomplete, offset, digest, disconnect partial-request discard, chunked install, and running-editor rejection. Before and installed SHA-256 both equal the frozen Ubuntu binary; upload SHA/size also match.
- `vm-exit.json` records exit `0`; Ubuntu VM provenance has checker exit `0`, tested candidate SHA equal to frozen Ubuntu binary, and matching candidate upload. Runtime image, kernel/initrd, guest reference, source commit, and runtime export hashes match the recorded provenance.
