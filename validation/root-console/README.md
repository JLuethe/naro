# Root and console phase

GNU reference: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.
Implementation commit: `4292ead60f1b93bc811b651a97bbfe8f46e455fd`.
The exact optimized executable and source-input fingerprint are in `build.json`.
Historical reports and release archives from the prior phase remain unchanged.

The automated gate passes 16 checks:

- 27 new root/home/filesystem comparisons are full matches, with independent
  reference and candidate assertions.
- A separate no-home tilde case records GNU nano's Code 11 crash. Naro preserves
  the literal pathname, remains usable and leaves file bytes/modes unchanged.
  Q-ROOT-NOHOME-001 permits that exact recovery difference; all differences are
  retained in the report. Namespace identities, files and inputs are not masked.
- The original safe corpus remains 301/303 full and 302/303 file/exit matches;
  the same two original safety differences remain. CLI is 38/38, regex 162/162,
  and the existing safety assertions pass. Ordinary-user backup fallback matches.
- Six Rust tests, 14 comparator tests, five harness tests and seven namespace/
  console/policy tests pass; formatting and strict Clippy pass.

`root.json` and `namespace-probes.json` cover genuine effective uids 0 and 1000
inside bubblewrap user/mount/PID/IPC/UTS/network namespaces. Host users are not
promoted to root. The private root uses fixture NSS files, a real private null
character device (1:3), read-only runtime mounts and writable fixture paths.
The harness also rejects uid-0 callers without a declared private namespace;
clean-container asset checks use an ordinary mapped uid. The actual backend source hash is checked at launch and retained in each raw
result; changing it during a run fails closed. No host home, passwd, device or
active console is used as editing test data. These results certify the listed
namespace cases, not host-root privilege behavior in general.

Cases include HOME set/unset/empty, passwd found/missing/empty, non-root
precedence, cached home, configuration, XDG, history/positions, normal and failed
backup fallback, bare/named/double-slash tildes, an invalid-UTF-8 home pathname,
private /dev/null and filesystem-root/parent browsing. The root oracle is a new
build of the same source with `--sysconfdir=/etc`, matching the no-home startup
origin label. `reference-build.json` retains its source hashes and configuration.
This phase does not add global host configuration loading.

`console-probe.json` records a tool-owned PTY: VT_GETSTATE returns ENOTTY and
termios is unchanged. Physical-key verification is deferred. No arbitrary
/dev/ttyN was opened, no VT switched, and no keymap modified. Console modifier
support is not certified. `console-checklist.json` has no prefilled passes.

To perform the conditional trial, an ordinary user must explicitly run this
from their own real Linux VT:

```sh
python3 tools/console_check.py probe --out target/vt-probe.json
python3 tools/console_check.py run --binary "$PWD/target/release/naro" \
  --reference "$HOME/src/nano-install/default/bin/nano" --out target/vt-trial.json
```

The runner refuses a PTY and launches no editor there. On a real VT it prepares
fresh fixture files and asks the operator for actual keymap, keys and observed
results for both editors. Use only those copied files. It records termios and
file manifests; it leaves manual results `recorded` for review, never auto-verified.
Current Naro still needs real-VT modifier/rendering validation before a console
compatibility claim. Missing native branches must be implemented and tested if
that trial finds differences.

Reproduce automated root cases with bubblewrap installed and user namespaces
available, after rebuilding the pinned oracle with the recorded configure flags:

```sh
python3 tools/check_follow_up.py --suite root --binary target/release/naro \
  --reference target/root-reference/install/bin/nano --out target/new-root
python3 tools/check_follow_up.py --suite root-nohome-tilde --binary target/release/naro \
  --reference target/root-reference/install/bin/nano --out target/new-root-safety
python3 tools/check_root_gate.py --out target/new-root-gate.json
```

Raw observations and frozen binaries remain in `spec/evidence/follow-up-runs/root-final*`,
`spec/evidence/naro-root-regression` and the other named root run directories.
Failed drafts are retained: root-v1 identified literal title mismatches and an
incorrect browser cancellation sequence; root-nohome-v1 sent an unnecessary
Enter; root-xdg-bytes exposed a partial JSON write for a surrogateescaped path.
The fixes have separate passing runs and serializer/atomicity regressions. No
failed draft was counted as a pass or used to replace original reference files.
