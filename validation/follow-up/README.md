# Follow-up validation

Reference: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.

This directory covers implementation revision
`4952ca020e72425d04acf12639d222b7a33a9245` and the exact binaries identified
in the reports. The executable source fingerprint is shared across the host and
Ubuntu builds; binary hashes differ because the native environment differs.
Historical baseline reports in the parent directory remain unchanged.

`gate.json` checks binary attribution and the required outcomes across the
terminal, CLI, regex, safety, new differential, packaging, installed asset,
recovery, performance and interactive operator reports. `checks.json` retains
formatting, strict Clippy and unit/comparator/harness test output.

The host terminal corpus has 303 recordings: 301 full matches and the original
two declared safety differences. The 53 new paired cases have 51 full matches;
two separately reported HUP/TERM cases assert Naro cleans its child/temp file
where the reference leaves the file. Both reference and candidate assertions
must pass. The reference recordings have their own binary hashes and scenario
hashes. New results never replace the original 309 reference observations.

The Ubuntu reports use a fresh reference built from the pinned source with
Ubuntu libraries, then ordinary-user fixtures in a rootless Ubuntu 24.04
container. Running that reference as uid 0 was an invalid setup for fixture HOME:
GNU nano deliberately consults root's passwd home. Failed setup attempts remain
on disk and are listed in `limits.json`; they are not certification evidence.

`operator.json` records an interactive installed-copy trial performed by the
Codex agent through a tool-owned PTY. It is not a human usability study. The
large-file report checks exact output hashes for deterministic 1 MiB and 10 MiB
inputs. Timings include the harness operation and carry no promised budget.
The asset report resolves every installed catalog through the actual native
gettext calls; it does not assess translation quality.

The package reports test prefix spaces, a symlink launcher, catalog overrides,
installed syntax, source-archive hashes/rebuild/fingerprint, payload tampering,
unsafe archive paths/symlinks and uninstall conflicts. Clean-container asset
checks mount the test scripts at a different location from either build checkout.
The Ubuntu artifact is the portable preview; its measured runtime envelope and
library/symbol requirements are retained in `ubuntu-build.json`.

`limits.json` maps the five excluded original path scenarios individually and
lists deferred real-VT, isolated-root and optional tiny cases. Three new private
absolute-path cases have fresh reference recordings; they do not execute the
unchanged excluded originals. No root-account, real-console, other-platform,
static-linking or tiny compatibility claim is made.

Raw evidence and frozen binaries remain in `spec/evidence/naro-release-candidate`,
`spec/evidence/follow-up-runs/rc-*` and `target/follow-up-env-user2`. These are
ignored task artifacts. Reproduce the paired suites with:

```sh
python3 tools/check_follow_up.py --suite tools --binary target/release/naro --out target/new-tools-run
python3 tools/check_release_gate.py --out target/new-gate.json
```

`tests/follow-up/environment.sh` runs the second-environment gate with read-only
inputs. It must run as an ordinary uid; `tools/replay_reference.py` checks all
reference worker IDs/statuses before candidate comparisons. See the progress
log for the rootless container invocation. No tag or GitHub release is published
by this validation process.
