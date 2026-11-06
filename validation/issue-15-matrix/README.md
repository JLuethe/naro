# Issue #15 exact-artifact differential matrix

Preparation only: final frozen binaries have not yet been supplied. No current
release qualification is claimed by this inventory.

`tests/remediation/differential.py` inventories and executes every applicable
production scenario in `spec/evidence/scenarios` and
`tests/follow-up/scenarios`. It runs fresh paired GNU nano/NARO recordings in
private fixtures and retains raw comparisons. The default inventory contains
593 cases: 303 baseline, 252 follow-up and 38 original CLI cases. Tiny contains 202: the 195
retained-feature/CLI/VT/safety cases, the original explicitly tiny key case and six original CLI cases.

Five original baseline probes and two original CLI probes use external absolute pathnames or root-directory
browsing and remain excluded by fixture safety policy. Other-profile cases and
the three test-hooks panic cases have explicit exclusions; these are not passes.
Tiny does not claim default-only feature coverage. The eight VT-ioctl cases in
each profile use fixture stubs and are not genuine guest-VT qualification.

The runner rejects missing evidence, incorrect binary identities, failed
reference steps/assertions and failed candidate steps/assertions. Its accounting
regression tests cover these boundaries. Successful recording alone is not a
pass. Missing namespace/reference prerequisites are reported separately.

The comparator and existing identity policy remain unchanged. The safe-save
policy in `docs/safe-save.md` deliberately changes final symlink rejection,
hardlink inode relationships and preservation on failed saves. Original
in-place scenarios remain in the raw corpus, with differences visible; separate
semantic checks must establish the new policy. No blanket safe-save acceptance
or new normalization is supplied by this runner.

Raw preparation artifacts: `target/remediation-2026-11-05/matrix-inventory-*`.
Reference HEAD: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`, clean pinned worktree.
Host executable SHA-256 values match existing pinned receipts:

- default: `b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2`
- tiny: `0e6343fe60e7c55f16cef7ecd99c7087885706d7065023cf12e7641728ea6439`
- namespace reference: `fe02ea07dc9a1e0afa009ef97dc034728995e39c65b75455985b0cf980fa3def`

Separate runners exercise the 81-case regex corpus in C and en_US.UTF-8 against
a fresh environment-local libc oracle (`tests/remediation/regex.py`), and the
32 issue-3 semantic save-progress/save-safety terminal scenarios
(`tests/remediation/safe_save_semantics.py`). Neither reuses historical verdicts.

The integrated review found that the seeded position-history scenario embeds a
canonical work pathname. The runner now substitutes only that exact seeded
pathname in its private input copy, records the before/after input, and requires
the established `(1, 11)` cursor on line `l40` in both observations. The original
scenario and normalization stay unchanged. Every recording is also reopened to
check scenario hashes, complete steps and inputs, assertions and raw trace hashes.
Eight accounting tests and a fresh focused history pair pass.

Requested locales are prerequisites: a locale command that warns and falls back
to ASCII cannot count as success even when its process returns zero. The host's
historical private LOCPATH lacks `en_US.UTF-8` for two follow-up scenarios; these
will be reported as missing prerequisites. Ubuntu preparation includes that
locale in its own directory. The existing Ubuntu image lacks bubblewrap, so its
28 root-namespace scenarios are unavailable rather than passing. Summary counts
separate accounted cases from pairs that were actually recorded.

The first host attempt was interrupted at the parent's request for a separate
configuration fix. Its raw directories and `matrix-interruption.json` are kept;
those incomplete artifacts are not final qualification. Ubuntu reference prep
also preserves two failed attempts (missing auxiliary-script paths, then missing
documentation generator) before successful executable-only lib/src builds.
