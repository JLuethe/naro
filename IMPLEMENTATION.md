# Implementation status

Reference: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.

Naro builds and runs as a Rust terminal editor. The default-profile follow-up
spec is implemented and verified for the ordinary-user Linux/tmux preview
scope. Source-derived requirements and test evidence are distinct: these results
do not prove every behavior on every platform.

The optional tiny profile is also complete for the pinned contract: 192/192
fresh exact comparisons, 194 CI/assertion cases, and 31 linked acceptance gates.
It is 58.07% smaller after stripping and needs no libmagic. Both new profile
packages pass source rebuilding and installation checks. See
[tiny validation](validation/tiny/README.md) for binary hashes and limits.

The editor uses byte vectors, transactional undo, a Rust state machine and cell
renderer, generated reference key/function data, and a small C bridge for
ncursesw, libc locale/POSIX regex/getopt, and libmagic. It ships syntax definitions,
translation catalogs and PO sources. The GNU nano executable is an oracle for
testing and is never used at runtime. Cargo has no package dependencies.

Current evidence is in [follow-up validation](validation/follow-up/README.md).
Parent reports describe the historical first build and remain unchanged.

| Check | Result |
|---|---|
| Host default terminal corpus | 303 recorded, 301 full matches, 302 file/exit matches |
| New paired cases | 53 recorded, 51 full matches, two explicit tool cleanup differences |
| Noninteractive CLI / regex | 38/38 and 162/162 |
| Safety | Six assertions across invalid-regex recovery and NUL rejection |
| Controlled Rust panic | Named, unnamed and multibuffer recovery; separate test-hooks build |
| Rust / comparator / harness tests | 6 / 13 / 3 pass; formatting and strict Clippy pass |
| Installed assets | All 41 catalogs resolve; syntax, overrides, spaces and symlink launcher checked |
| Archives / installer | Source rebuild, checksums, rejection and ownership/removal checks pass |
| Large files | Exact output hashes for 1 MiB and 10 MiB edit/save operations |
| Interactive installed copy | Agent-operated PTY trial, including spelling, errors, paste and resize |

Selection-aware spelling preserves outside bytes and reference state. Formatting
processes the whole buffer and clears the mark at the reference-defined point.
New cases also cover compound wrapping/history, lazy syntax, configuration,
ENOSPC, short/EINTR writes, backup fallback, linked files and bounded FIFOs.

The original invalid-regex crash and NUL-as-Yes behavior remain deliberate safety
differences. Tool HUP/TERM cleanup is a separately reported ownership improvement.
Reference observations are retained; comparisons are not globally masked to
hide new differences. The only new filename normalization is the named backup
fallback scenario, retaining file bytes, permissions and link checks.

Five original terminal cases still involve host paths and are excluded; one
requires optional tiny. Three new fixture absolute-path variants have fresh
reference observations and are mapped individually. Physical keyboard/operator
console checks remain deferred. Isolated-root special-device/root-browser checks
and root-account home precedence are tested in private namespaces; broader root-account configuration,
other architectures/OSes, static linking and translation quality are outside
this certification. Byte-locale screens inherit tmux's UTF-8 capture limits.
Tiny is now implemented as an optional compile-time profile; its separate
qualification is described in [tiny validation](validation/tiny/README.md).
Optional `credits` is implemented and default-off.

The host executable is `target/release/naro`. Distribution uses the Ubuntu-built
artifact with measured native dependencies; see [INSTALL.md](INSTALL.md).
Rust/Cargo is installed under `~/.cargo/bin`, without shell-profile changes or
host system-package installation. CI builds checksum-pinned tmux 3.8 and checks
Rust, comparator/harness, terminal smoke/safety, panic recovery, optional credits,
packaging, source rebuild and installation. It does not replace full local
release validation or publish a release automatically.

Use `tools/check_follow_up.py` for fresh paired suites and
`tools/validate_parallel.py` for the safe original corpus. Use new output folders
and avoid simultaneous runs sharing scenario IDs. Never overwrite original
`spec/evidence/runs` or run editing tests against real user files.


The newer root/home implementation (`4292ead`) is covered by
[root-phase evidence](validation/root-console/README.md): 27 exact comparisons
with genuine namespace uid/NSS/device observations, and a separate asserted
no-home tilde recovery difference. Its ordinary regression retains 301/303 full
matches, CLI 38/38 and regex 162/162. The prior release archives and two-environment
reports identify earlier binaries; a new release requires refreshed artifact
validation. The newer [console qualification](validation/console-vm/README.md)
records 19 exact comparisons on a genuine guest Linux VT for each optimized host
and Ubuntu candidate. Modifiers, console rendering and raw-key macro replay are
implemented. This uses emulated PS/2 keys, not physical operator observations.

[Closure evidence](validation/closure/README.md) links final regression and
package results to those executable hashes. Earlier tables above describe their
historical phase. Current harness checks include 14 comparator, five harness,
seven namespace and nine console/upload tests, plus six Rust tests. Optional
physical-console operator certification and other platforms remain outside
the preview scope. No release tag or hosted GitHub Release is created by testing.
