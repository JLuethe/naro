# NARO 0.1.2 final-candidate qualification and Daybreak handoff — 2026-11-06

This retest binds the repaired product to commit
`2888560a9a2709469334a417d1ad9ac3a91c30ba`, tree
`549be4d398231ae2681ed5eb9f201764c638836c`, and production-source
fingerprint
`7b6ef4e024bc5d25f59fb66eebad7f8297d4be4f49a34d1037c3b8d4f928e636`.
It does not transfer historical qualification to the rebuilt artifacts.
Verification-only receipt commit `b12dc150312a9d75475fd0add7b2b393672aab09`
adds the final adapted-boundary and backup negative-control record without
changing production source.

The review sequence was an Astra/xhigh read-only audit, focused Sol 6.1/high
corrections, a fresh committed-tree qualification run, and a final Astra/xhigh
evidence review. Astra returned a technical GO for the exact Linux artifacts
recorded here, subject to the explicit limits below. No Daybreak Blue model or
runtime was available in this session: the existing `daybreak-*` path names are
campaign labels, not model provenance. The bundled
[Daybreak retest prompt](DAYBREAK_RETEST_PROMPT.txt) is the handoff for the
requested independent rerun. No global
installation, push, publication, tag, PR, or issue closure was performed.

## Design and compatibility decision

The default regular-file save is an atomic replacement transaction. NARO
creates an exclusive sibling temporary in the destination directory, writes
until complete while retrying `EINTR`, syncs the file, checks close, renames it
over the destination, and syncs the containing directory. Failure before rename
preserves the old pathname; failure after rename is reported as failure and is
not marked durably saved. Cleanup is identity-aware.

Backup publication follows the same safety principle: an existing backup inode
is never opened for writing, including under `INSECURE_BACKUP`. A uniquely
created sibling is written, metadata is applied, the file is synced and closed,
identity is rechecked, then it is renamed and the directory is synced. The
legacy option remains accepted for configuration compatibility but does not
restore alias-truncating behavior.

Lock ownership now retains the created lock descriptor. Refresh and cleanup
compare device/inode identity before unlinking. Only an explicitly accepted
opening conflict may take over an unowned lock. Save-as to an old lock pathname
therefore preserves the new document, and a pre-existing new sidecar is
preserved with a warning.

Atomic replacement intentionally differs from nano's in-place behavior:

- final symlinks are refused rather than followed;
- a hard-linked destination is replaced with a new inode, splitting the link;
- successful overwrite replaces the inode;
- mode, applicable ownership, xattrs/ACLs, and set-ID policy are deliberately
  copied/tested rather than inherited through an in-place write; normal saves
  do not restore the old destination timestamps, while backups deliberately
  preserve source timestamps;
- append and prepend compose complete destination bytes and commit them through
  the same replacement path; prepend to a FIFO is rejected and FIFO output is a
  documented streaming exception without filesystem durability.

## Exact frozen host artifacts

All files were installed mode `0555` under
`target/remediation-2026-11-06/daybreak-final5-frozen/` and report revision
`2888560`, Rust `1.99.1`, and the production fingerprint above.

| Artifact | Features | SHA-256 |
|---|---|---|
| `naro-default` | default | `4e64b3ad0b3e7287272d163741adf053287c16dd69e2ca764bf5e57194b2ff3d` |
| `naro-tiny` | tiny | `81ebc62e917fe967361420fbebedc9e1715d0471c1a21ac357aa5b3262844829` |
| `naro-credits` | credits | `a8b2d99affa9e8c96dc598c98a7981a99fc6dd01b459301984e96ea5e1c1747b` |
| `naro-hooks` | test-hooks | `f59f503b27a35e6bf396439418ca8ddcc10482bc2a2f13fe7220b2605645062a` |
| `naro-hooks-tiny` | tiny,test-hooks | `74052cc3c865a911a3cebabbc20231d4b36667a4069c90136c21e1c7c52b30ab` |

## Host results

| Gate | Result |
|---|---|
| Rust default / tiny / all-features | 72 / 39 / 39 passed; 10 documented ignored fixtures in each profile |
| Formatting and strict Clippy | passed |
| Safe-save fault matrix | 448/448 default and 448/448 tiny; no skips |
| Backup-enabled matrix | 1200/1200: 672 save-phase and 528 backup-phase cases |
| Adapted historical fault boundaries | 6/6 cases, 67/67 steps, 52/52 harness assertions plus marker/inode/link/home checks |
| Recovery fault matrix | 41/41 per profile |
| Explicit issue #3 semantics | 22/22 progress and 10/10 safety |
| Lock terminal flows | 6/6, 35/35 assertions |
| Save terminal flows | 32/32, 1718/1718 assertions |
| Panic recordings and extension checker | 3/3 recordings; exact hook identity; extension checker passed |
| Signal cleanup | 37/37 native; 12/12 default PTY; 10/10 tiny PTY |
| Search | 12/12 bounded resource runs plus two PTY cancellation cases per profile |
| Undo stress | passed; 73,260 KiB peak below the 96 MiB limit |
| Native fuzz | 100,000 runs per profile |
| Catalogs | 41 catalogs, 128 position assertions, 5 malformed cases per profile |
| Regex | 81 cases in `C` and 81 in `en_US.UTF-8` per profile |
| Branding / credits / profile | 5/5 each profile; credits byte-exact; 8/8 profile checks, 56.6% reduction |
| Tiny CI | 59 + 125 + 8 + 3 = 195/195 |
| Python discovery | spec 66, tools 125, remediation 11, safe-save gate 7, catalog 5, console 9 |
| Packages | default and tiny built from a clean self-contained clone; 15/15 package checks and 44/44 asset checks each |
| Large files | 1 MiB and 10 MiB checks passed |
| Rootless backup ownership | both ignored-by-default namespace cases passed when run in owned containers |

The host default differential run accounted and recorded all 593 cases. Its raw
summary is 550 accepted: 474 identity-reviewed, 71 raw exact, five declared
deviations, two missing locale prerequisites, six deliberate product/policy
differences, and 35 candidate execution/assertion failures. The latter remain
visible and are not relabeled as passes: 29 are historical nano/in-place save
expectations; four historical backup-open supervisors aim at the published
backup pathname rather than the new `.naro-backup-*` temporary; and two old
destination-write supervisors aim at the destination rather than the new
`.naro-save-*` temporary. The adapted issue #3 semantic and 1200-case backup
suites above execute the new commit points and pass. A separate focused run
retains the raw scenarios but adapts disposable candidate copies to the new
boundaries: all six intended syscall markers fired, 67/67 steps and 52/52
harness assertions passed, and independent inode/link/fallback-home checks
passed, including all three root namespaces. The tiny run accounted/recorded
202, accepted 200, with one deliberate FIFO policy difference and one GNU nano
reference failure.

## Ubuntu results

The source clone is self-contained, detached at `2888560`, has no alternates,
and passed `git fsck --full`. The container used a pinned Ubuntu 24.04 image,
`--network none`, and an immutable source mount.

- Default differential: 593 accounted, 565 recorded, 524 accepted. Twenty-eight
  root namespace cases are missing prerequisites because bubblewrap is absent;
  the same 35 raw historical save/backup failures and six policy differences
  remain explicit.
- Tiny differential: 202 accounted/recorded, 200 accepted with the same one
  policy difference and one reference failure.
- Regex passed all 81 cases in both `C` and `en_US.UTF-8` for each profile.
- Explicit safe-save semantics passed 22/22 and 10/10.
- Ubuntu issue #3 matrices passed 378/378 per profile. Three supplementary-group
  categories per profile were skipped because no supplementary group exists in
  the container; the host executed the corresponding 448/448 inventories.
- Backup passed 1200/1200; recovery passed 41/41 per profile; tiny CI passed
  195/195; the fortified-open gate unit tests passed.

## Negative controls

The old safe-save behavior is retained in the scoped issue #3 receipts. The
lock negative control at base `c26b11c` returns successful save and then fails
to read the destination with `ENOENT`. The fortified-open negative control
demonstrates that the old tiny gate failed to observe the intended open. The
clean source-bound backup-alias negative control at exact c26 parent `2c63ec3`
exits 101 after observing `source=[]`; the identical regression passes final5.
Each uses disposable ordinary fixtures; no adversarial race or weaponized
reproduction was created. See the [focused boundary and negative-control
receipt](../final5-adapted-faults-2026-11-06.md).

## Failed attempts and classification

- The first extension invocation pointed the checker at the 41-case fault
  matrix rather than the required three terminal panic recordings. Default,
  credits, and production-no-hook checks passed; the three missing records were
  an evidence-input error. Fresh exact-hook recordings were then generated and
  the checker passed.
- Default and tiny package checks were initially launched concurrently with the
  same implicit `NANOSPEC_WORK`, colliding in one catalog fixture and yielding
  14/15 package checks and 40/44 asset checks. Those attempts are preserved.
  Sequential reruns with distinct absolute fixture roots passed 15/15 package
  checks and 44/44 asset checks each.
- One environment inventory command first attempted bare `rustc` before the
  configured Cargo path, and one broad `sha256sum` glob included package
  directories. Both diagnostic command errors are retained and are not product
  failures.
- Raw differential exit 1 is expected from recorded policy differences,
  historical step failures, reference failure, and missing prerequisites; it is
  not treated as either an automatic pass or an unclassified product failure.

## Remaining uncertainty

Deterministic tests cannot prove physical power-loss behavior. The comparison
and unlink in identity-aware cleanup are separate filesystem operations; the
issue #12 adversarial symlink-swap/rename-exchange race remains explicitly
unverified, as do genuine guest-VT input, other architectures/Miri, and broader
native-library sanitizer coverage. These limits do not contradict the ordinary
issue #3 fixtures, but they prohibit an unqualified security or all-platform
claim.

The integrated review found no remaining product blocker. The candidate is
technically ready as a local 0.1.2 point-release candidate within the tested
scope and explicit limits above. This is not an unqualified security,
power-loss, all-platform, or guest-VT certification. Publication remains
unauthorized and no GitHub issue is closed by this report.

See [commands.md](commands.md) for the executed command ledger and
[receipt.json](receipt.json) for machine-readable identities and counts. The
earlier scoped [issue #3 index](../issue-3-safe-save/README.md) links the Sol
backup/lock receipts and negative controls.
