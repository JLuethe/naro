# Step 4 — committed source and candidate freeze

Date: October 30, 2026 (America/Los_Angeles).

Status: **complete**. Full host/Ubuntu qualification is step 5 and remains pending.
No release or tag was published; no system editor was replaced.

## Plan and execution

1. Reviewed and committed the step 3 fix, permanent tests, and evidence receipts.
2. Pushed `main`, verified remote equality, and verified source CI succeeded.
3. Created a clean, detached standalone checkout of the selected commit.
4. Built separate default-feature host and Ubuntu candidates, offline and locked.
5. Recorded source, tools, compiler, native dependencies, reference identities,
   commands, executable hashes, linkage, locales, and build logs.
6. Preserved frozen executable copies and checksummed inputs without changing
   historical tester exports or relabeling previous candidates.
7. Prepared the [Claude qualification handoff](NARO_CLAUDE_QUALIFICATION_HANDOFF_2026-10-30.md)
   and local launch scripts for the exact frozen executables.

Selected production commit:
[`fd91763c4f14d9bed8187d64d44f2136440b7b3e`](https://github.com/JLuethe/naro/commit/fd91763c4f14d9bed8187d64d44f2136440b7b3e).
[Source CI run 41164011073](https://github.com/JLuethe/naro/actions/runs/41164011073)
completed successfully. A later documentation receipt commit is distinct from
this build commit; these executables must continue to identify `fd91763`.

Production fingerprint: `4cabd71741ffc8ee0357d945c67904c8a2fd0089c12e9b32a1c5b3e35c394ae6`.
Verification fingerprint: `604c032c865701dac6f5fc0f0c9ce5e3764ed3e434b51e2ccea5fdf8172d45aa`.
Both builds report version 0.1.0, an empty/default feature list, and rustc
`1.99.1 (58cf8f9c3 2026-10-13)`. Tiny, sanitizer, credits, and test-hooks artifacts
are not these release candidates.

## Frozen artifacts

Local bundle: `/home/john/Code/naro/target/release-freeze-2026-10-30`.

| Artifact | Relative path | SHA-256 |
| --- | --- | --- |
| Host candidate | `host/naro` | `cae387c78619520aacbf61690e675496b82f8ccf04af2824beb9e864004f0a96` |
| Ubuntu candidate | `ubuntu/naro` | `33a39eb339492720ec6166e84fea421749e0b2ec3bd612b276c2377f91b7c4a1` |
| Host nano reference | `references/host/nano` | `b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2` |
| Ubuntu nano reference | `ubuntu/reference.bin` | `6540492f810998a20a4dba4ac8048cd8b76d37a39e642f14f9f9c3d30c621ba7` |
| Host isolated-root reference | `references/host-root/nano` | `fe02ea07dc9a1e0afa009ef97dc034728995e39c65b75455985b0cf980fa3def` |

GNU nano source is pinned to `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.
Ubuntu's reference was built in Ubuntu from the recorded bootstrap tree, with
16 C files and two headers checked against the pinned source. Its install tree,
configure/build/install logs, and source check are retained. Host reference
results do not stand in for Ubuntu observations.

Host: Linux x86_64, glibc 2.44, Python 3.14.8, tmux 3.8.
Ubuntu: 24.04, glibc 2.39, Python 3.12.3, tmux 3.8.
The records include native package versions, compiler, locales, libmagic data,
`ldd`, and symbol-version output. These are measured environments, not a claim
that every Linux distribution or a guessed minimum glibc is supported.

Ubuntu image ID: `093817959dc26bb88c4f8df915372db75dee73f9356eb94f2ba428ea04fe9735`.
Image digest: `sha256:7434f9d20c1d41cfd2d5ecd98ed8228b424910d51be7640a06262ccd3650c3ee`.
It was built from the selected Containerfile because the older cached image
lacked the required `file` executable. Build and test containers used the
immutable image ID, no network, read-only inputs, and private output mounts.

Host build command, from `source/`:

```sh
/home/john/.cargo/bin/cargo build --release --offline --locked --target-dir /home/john/Code/naro/target/release-freeze-2026-10-30/host-build
```

Ubuntu build command inside its private `/work/naro`:

```sh
cargo build --release --offline --locked
```

Exact setup is retained in `build-ubuntu.sh`; compiler executable hashes are in
`toolchain.json`. `host/build-record.json` and `ubuntu/build-record.json` contain
the full provenance. Do not rebuild over these frozen outputs.

## Verification and limits

- Host smoke: 4/4 assertions passed on the frozen host executable.
- Ubuntu smoke: 4/4 assertions passed on the frozen Ubuntu executable.
- Ubuntu minimal paging comparisons: 2/2 exact against its new nano reference,
  both harnesses successful.
- Frozen source is clean; candidate metadata, hashes, references, recorded
  inputs, and symlink targets pass `verify-freeze.py`.
- All local shell helpers pass `bash -n`. Full qualification wrappers have not
  yet been run; their successful execution is not claimed by this step.

Manifest SHA-256 (`freeze.json`): `d404c22dc97a5554c47004fb25d21e7c96b510023fddfd25307a8118603409ea`.
The [compact receipt](validation/release-freeze-2026-10-30.json) pins this hash;
`freeze-manifest.sha256` is the local verification sidecar. The manifest hashes
selected source files, references, build outputs, helpers, image metadata, and
compiler identities. This is integrity checking, not signed authentication.

Full evidence is local and ignored by Git. It survives reboot but not
`cargo clean` or disk loss. Back up the bundle outside `target/` before cleanup
or eventual distribution. No new qualification or package acceptance is implied
by smoke results. Actual guest-VT work remains step 6, distribution acceptance
step 7, and final documentation/publication gates steps 8–10.
