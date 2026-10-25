# Final preview qualification

GNU reference: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.
Production source was frozen at `390a72dc63da0f0f5b6d516282033fb1c4d6adad`.

This directory collects the final host/Ubuntu regression and packaging gate for
spec 21. Until `gate.json` exists with `pass: true`, this directory is a
qualification workspace, not a completed release certification. The executable
fingerprint is independent of later documentation and evidence commits.

The tested host executable SHA-256 is
`283abffeda8ab42a6fe982ba54c355c459c7378632d50f8f132201fd76a2059d`.
The tested Ubuntu executable SHA-256 is
`eeb8ebb50fd3709aaa004897df3e589364e536a6a1eaf006ae3b8be5f6031541`.
The portable preview must package the latter byte for byte, with the matching
source-input fingerprint and measured Ubuntu library/symbol requirements.

`gate.json` checks full inventories, assertion outcomes and binary/source links
across the 303-case terminal corpus, 53 follow-up comparisons, CLI/regex/safety,
root/home cases, eight ioctl models, recovery, large files, both 19-case console
suites and packaging. Existing deviations remain explicit: invalid startup regex,
NUL answer handling, tool termination cleanup and no-home tilde recovery. A
successful process exit alone does not establish behavioral equivalence.

`host-checks.json` records bounded command results. `ubuntu-build.json` describes
the packaged executable and source archive; `ubuntu-package.json` records clean
installation, all catalogs/syntax, offline source rebuild, archive rejection and
ownership/removal checks. `SHA256SUMS` identifies the local binary/source archives.
These files are added only when their source runs finish. Delivery/CI status is
reported separately because a tested executable can predate documentation commits.

Raw recordings remain in `target/host-closure-v1`, `target/ubuntu-closure-v1` and
`spec/evidence/follow-up-runs/vt-closure-{host,ubuntu}-v1`. Their old counterparts
remain unchanged. These ignored directories are local artifacts, not part of a
GitHub clone. The tracked tools reproduce results with new output directories:

```sh
python3 tools/run_closure_host.py --binary target/release/naro --out target/new-host-closure
# Run tests/follow-up/environment.sh in the private rootless Ubuntu environment
# described in spec/98-progress.md; use an ordinary mapped uid and new /out.
python3 tools/check_console_vm.py --fixture /tmp/nanospec-work/TEST-VT-VM/fx \
  --out spec/evidence/follow-up-runs/new-console-run
```

`tools/collect_closure.py --help` describes the required report/artifact inputs.
It refuses an existing evidence output (except an initial README), checks the
gate and copies compact reports. Keep raw failed attempts distinct from passing
runs. Never overwrite original reference goldens or reuse fixture IDs concurrently.

Console results use genuine guest Linux VT descriptors and emulated PS/2 keys.
They qualify the recorded kernel/keymap/Ubuntu runtime, not physical keyboards.
Root results use private namespace uid/NSS/device observations, not general host
root-account certification. Tiny mode, physical operator trials, other platforms
and the remaining source-only runtime gaps remain outside this preview's scope.
No GitHub Release or tag is published automatically. Source and evidence are
pushed to GitHub; large archives remain local until publication is requested.
