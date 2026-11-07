# NARO 0.1.3 local integrated retest

This is evidence for a local development candidate, not a published release or
a broad GNU nano compatibility claim. The code tested here is clean commit
`dbc46bbc1d3f8bc464bf1ad3298a00583b8ffb26`, source fingerprint
`005ea77002dbf76e107ce1babb0fa2464d6d5e4664bee846b7b412c8453ba561`.
The pinned GNU nano source is `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.
All test output lives in ignored, disposable `target/` directories. Reports for
older commits, including `e8f1a10` and `2209f87`, are historical and do not
qualify these executables.

## Executables

| Build | SHA-256 | Use |
| --- | --- | --- |
| Host default | `eacc6a18c7fdd88146538ed29acfeccb0835b87e44e03fae1dedfd460b87ce91` | Production terminal, differential, package input |
| Host tiny | `f0ce816afbfb7be838402a6c379df3a6e21d0f5fc1f75d66647891db8d4c53fa` | Tiny differential and package input |
| Ubuntu 24 default | `cee126078e8a71264d89fb71b5b1b36035e8ea8e1c4d825f2a5769f01c7752b2` | x86 guest-VT input |
| ARM64 glibc/QEMU default | `56f176a2a7939a395dd1485fec881c0b9a060dcdac162552dd32ff40e93fc428` | Resource and hostile-input gates |
| ARM64 glibc/QEMU tiny | `0000cc6c51fddfff0ada49fec7feda992e8ab1c95507eea0cce897b809ffb6d6` | Resource and hostile-input gates |

All five builds report version `0.1.3`, revision `dbc46bb`, the source
fingerprint above, and their exact feature sets. The host used glibc 2.44,
ncursesw 6.6.20251230, libmagic 5.48 and Rust 1.99.1. The ARM64 image used
glibc 2.36, ncursesw 6.4.20221231, libmagic 5.44 and Rust 1.99.1. ARM64 ran
under QEMU user emulation, not physical ARM64 hardware.

## Issue-specific results

- [Issue #12](../issue-12-confinement/README.md): independent fresh test
  executables passed 1,296/1,296 backup faults, 659/659 safe-save cases in
  each profile, 77/77 bounded confinement cases, eight parent-policy cases,
  and mapped distinct-UID sticky-parent cases. A separately built production
  executable with the same code revision passed 22/22 save-progress and 10/10
  save-safety terminal cases. Its ELF hash is distinct from the host default
  executable above; its result is not silently transferred to that ELF. The
  exact host default ELF above also passed 22/22 and 10/10 terminal cases.
- [Issue #14](../issue-14-runtime/README.md): the exact host default ELF above
  passed both live GNU and recorded-oracle runs. Each ran 10 production, 13
  default-hook and four tiny-hook terminal cases, plus six direct PTY cases.
  The 12 saved PTY traces reached EOF, contain terminal reset bytes, and match
  their recorded sizes and SHA-256 hashes. The old production ELF failed the
  new incomplete-CSI/Ctrl-C and standalone Meta-[ cancellation cases. A focused
  Astra/xhigh review found no defect in the final prefix fix or capture path.
- [Issue #15](../issue-15-matrix/README.md): all 202 tiny differential cases
  were recorded and accounted for; 200 were accepted, one is a reference-side
  failure, and one remains a product/policy difference. The runner returned
  failure as required. All 593 default cases were recorded and accounted for;
  554 were accepted. Thirty-five candidate execution/assertion failures and
  four product/policy differences remain. These are nonpassing compatibility
  results, not 39 independently established data-integrity defects. The
  original comparisons and expected exclusions were not weakened. The 35
  failing IDs match the earlier `a140d6e` run: 32 use legacy in-place save or
  backup fault gates, and three root-state cases became observable on this host
  but still target the old backup path. Separate current safe-save semantic
  tests pass; the legacy cases remain nonaccepted. The four default residuals
  cover intentional symlink/hard-link replacement policy, unchanged-original
  error text, and an EINTR outcome. Tiny's two residuals are one historical
  GNU reference timeout and one historical FIFO interruption presentation
  difference. These dispositions do not turn the strict differential green.

## Final gate ledger

| Check | Outcome | Local evidence |
| --- | --- | --- |
| `cargo fmt --check`; default, tiny and all-features `cargo test` | Pass; 82/49/49 tests, 10 ignored per mode | `target/retest-dbc46bb/{fmt,test-default,test-tiny,test-all}.log` |
| Default, tiny and all-features `cargo clippy --all-targets -- -D warnings` | Pass | `target/retest-dbc46bb/clippy-*.log` |
| Spec audit and issue #14 citation check | Pass | `target/retest-dbc46bb/{spec-audit,citation}.log` |
| Native bridge sanitizer/fuzz run; quick Miri check | Pass; 100,000 runs per profile; one Miri boundary test | `target/retest-dbc46bb/{native-fuzz,miri}.log` |
| Wrap/undo inventory; closure regressions | Pass; 58 scenarios; nine tests | `target/retest-dbc46bb/{wrap-undo,closure-regressions}.log` |
| Python validation scripts | Pass; 23 scripts, including spec, save, package, VM and accounting checks | `target/retest-dbc46bb/python-validation-batch.log` |
| Production gate accounting unit test | Pass; one test | `target/retest-dbc46bb/production-gates-unit.log` |
| Save terminal semantics; regex corpus | Pass; 22/22 progress, 10/10 safety; `C` and `en_US.UTF-8` | `target/retest-dbc46bb/{save-sem-default,regex-corpus}.log` |
| Tiny full differential | Nonpass; 202/202 recorded and accounted, 200 accepted | `target/retest-dbc46bb/diff-tiny/report.json` |
| Default full differential | Nonpass; 593/593 recorded and accounted, 554 accepted | `target/retest-dbc46bb/diff-default/report.json` |
| Host production resource and hostile-input gates | Pass; default two resource and five hostile, tiny one resource and four hostile cases | `target/retest-dbc46bb/{terminal_resources,hostile_inputs}-*.log` |
| ARM64 glibc under QEMU user emulation | Pass; default/tiny CLI and resource gates, default 5/5 and tiny 4/4 hostile inputs | `target/issue15-arm64-dbc/target/arm64-qualification/` |
| Bounded search and undo stress | Pass; 12 search cases across default/tiny, undo stress | `target/retest-dbc46bb/{search-stress,undo-stress}.log` |
| Ubuntu guest-VT | Pass; 19/19 accepted with exact Ubuntu default build; independent provenance replay 19/19, zero problems | `target/retest-dbc46bb/vt-report/{report,vm-provenance}.json` and `vt-provenance-check.log` |
| Host package/source archive checks at source revision `22450f1` | Pass; default and tiny each 17/17 package and 44/44 asset checks, including offline source rebuild | `target/retest-dbc46bb/check-{default,tiny}-final/` |
| Independent Daybreak Blue fresh retest | Supported gates pass: production resource/hostile default and tiny, live/recorded #14, backup 1,296/1,296, confinement 77/77 default and 72/72 tiny, and exact host save semantics 22/22 progress plus 10/10 safety. ACL fixture setup returns `EINVAL`, so safe-save 409/659 in each profile and parent-policy ACL cases are incomplete in its managed sandbox; distinct-UID mapping is unavailable there. | `target/retest-dbc46bb/daybreak-final/` |
| Safe-save and parent-policy harness corrections | Six safe-save and three parent-policy classifier unit tests pass; unrestricted default/tiny matrices each pass 659/659. An old #3 binary fails all three preservation controls. An unmapped-UID/no-supplementary-group control accounts for every planned row and exits nonzero. | `target/retest-dbf686e/{save-default,save-tiny,old-preservation-control,parent-unmapped,backup-parent-unmapped,daybreak-postfix}/` |
| Concurrent package-check regression | Both checks against the earlier archives pass 17/17 package and 44/44 asset cases with distinct fixture roots; the original shared-root failure is retained. | `target/retest-dbc46bb/check-concurrency-{default,tiny}/` |
| Daybreak Blue focused post-fix retest | Unit tests pass 6/6 and 3/3; its managed sandbox reports 659/659 planned rows in each profile, with 409 passes and 250 missing prerequisites, exit 1. ACL parent controls are missing prerequisites, exit 1. No false success is reported. | `target/retest-dbf686e/daybreak-postfix/REPORT.md` |

The safe-save policy is [documented separately](../../docs/safe-save.md):
publication replaces the inode, rejects final symlinks, preserves old hard-link
targets, and uses explicitly selected compatibility behavior where documented.
The retained GNU differential does not erase those deliberate differences.
Synthetic faults and namespace fixtures do not establish physical power-loss
persistence, exhaustive races, or protection from an actor with the same UID.
The first Daybreak invocation was interrupted after its read-only audit because
its sandbox root could not write to the sibling evidence directory. The rerun
used the repository root as its writable sandbox root. Its ACL fixture failures
are missing prerequisites, not product passes or independent evidence of a
product defect. An unrestricted independent exact-revision run passed the full
659-case matrices and mapped-UID cases, as listed above. These environments'
results are kept separate.
Daybreak observed that the VM report lacked `vm-provenance.json` at the time of
its audit. After that report, the provenance was generated from the retained
VM launch, boot inputs, installed guest binary hashes and runtime archive;
`validate_console_evidence` independently reopened all 19 captures and found
zero problems. This provenance was created after capture; Daybreak did not
independently audit the completed file. Archive manifests distinguish the
compiled `dbc46bb` code from their later documentation/source revision.
The later Astra/xhigh integrated review found no production defect but identified
three qualification-tooling gaps: incomplete safe-save coverage could return
success, an unmapped ACL setup error was misclassified as a product failure,
and simultaneous package checks could remove one another's asset fixtures.
Commits `dbf686e`, `adee23b`, and `fddc519` correct these respectively. The
post-fix Daybreak report verifies that its constrained environment now exits
nonzero with explicit missing-prerequisite rows; unrestricted exact-revision
matrices pass all 659 cases per profile. The package source revision and archive
checks after these fixes are recorded separately from the frozen `dbc46bb`
executables.
The first pushed CI run at `4b3c759` passed atomic save faults but exposed a
namespace-fixture assumption in the subsequent bounded confinement step:
`unshare --map-subids` succeeded while UID/GID 100000 was not mapped inside
that runner. The foreign-owner setup returned `EINVAL`; CI correctly stopped.
The parent-policy fixture now selects an ID that appears in both actual
namespace maps and records it in the observation. This is a test-environment
correction; the production code and frozen executable hashes remain unchanged.
The next CI run at `da0bd60` advanced past mapped-ID selection but returned
`EPERM` while its namespace tried to `chown` the foreign-owned fixture. The
fixture now has the mapped actor create that file under a disposable directory,
then restores the directory's permissions before the editor operation. The
first actor-created attempt exposed this host's private home-directory traversal;
using a relative fixture path from the inherited working directory corrected
it. Both failed attempts remain nonpassing evidence, not product passes.
The `e20d7c8` CI run passed atomic save and ordinary confinement but the
rootless namespace could not establish the distinct actor's credentials;
Python reported a `preexec_fn` failure before the candidate operation. CI now
probes the exact group/UID/GID transition first. If the environment cannot
support it, the five optional distinct-UID cases are explicitly marked
unqualified with a CI notice; unexpected probe errors still fail CI. The
independent mapped-UID receipts remain separate and passing.
No tag, download, release, PR, or issue closure follows from this local report.
