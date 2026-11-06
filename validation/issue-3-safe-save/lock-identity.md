# Lock ownership and save-as integration correction

The ordinary save-as operation could target the buffer's own `.swp` pathname.
Atomic save committed the document, then pathname-only lock cleanup deleted
that document and marked the buffer saved with no recorded file metadata.
Lock refresh could likewise delete an entry substituted for the owned lock.

The correction retains the opened lock file and checks its device/inode before
cleanup or refresh. New sidecars use exclusive creation. Only accepting the
opening lock-conflict question authorizes replacing an unowned sidecar. A
save-as destination's existing sidecar is preserved and reported as a warning;
the document remains successfully saved. The saved-point, modified flag and
metadata are tested alongside output bytes and normal owned-lock cleanup.

Base revision: `c26b11ca8f144ef60c8e12460c9cc8e330c0c28a`.
The tested source fingerprint is
`7b6ef4e024bc5d25f59fb66eebad7f8297d4be4f49a34d1037c3b8d4f928e636`.
The precommit build info records the base revision and this source fingerprint;
it does not describe an unmodified base build. Exact commands, hashes and
results are in [the receipt](lock-identity.json). Local raw evidence is preserved
under `target/issue-3-lock-validation/`; no historical recordings were changed.

## Negative control

`final-negative-control/source/` contains a fresh `git archive` of the base
revision plus the final core regression and its test-module declaration. The
actual `files::write` returns success, but reading the destination fails with
ENOENT. The process exits 101 as expected. Its source, command, log and test
source hash are retained in `final-negative-control/`. Earlier negative and
intermediate failed runs remain present as well.

## Final checks

With `PATH=/home/john/.cargo/bin:$PATH`:

- `cargo fmt --check`: pass.
- `cargo test`: 72 passed, 10 intentionally ignored.
- `cargo test --features tiny`: 39 passed, 10 intentionally ignored.
- `cargo test --all-features`: 39 passed, 10 intentionally ignored.
- `cargo clippy --all-targets -- -D warnings`: pass.
- `cargo clippy --all-targets --all-features -- -D warnings`: pass.
- `cargo test files::lock_tests` and the same with `--features tiny`: 7/7 each.
  The main collision, substitution, cleanup/refresh and new-sidecar cases run
  both ordinary and confined fixtures. Tiny does not recreate UI locks or
  provide undo; the applicable output/saved-state checks still execute.
- `python3 tests/undo/stress.py --out <fresh-directory>`: pass with the
  field-equivalent `Parent`/`OwnedLock` declaration in the standalone harness.
- `python3 tests/safe-save/test_progress_cases.py`: 7/7, including actual backup
  temporary-fd sync gating, save-temp bypass and unchanged screen/cursor checks.
- `python3 spec/tools/test_compare_runs.py` and `test_nanoharness.py`: pass.
- `tests/safe-save/run.py`, default and tiny test executables: **448/448 each**,
  no skipped matrix cases.
- `tests/safe-save/locking.json` plus four historical locking flows:
  **6/6 scenarios, 35/35 assertions**. The two new cases contribute 23 assertions.
- Regenerated save-progress/save-safety terminal suites:
  **32/32 scenarios, 1718/1718 assertions**.
- `tests/signals/terminal.py`: **12/12 default and 10/10 tiny**, including normal
  lock removal on fatal signal cleanup.

The first broader terminal attempt passed 29/32 cases. Its failures revealed
stale adapters following the backup publication change: the backup progress
gate recognized the published name and later save temporary rather than the
new backup temporary, and two unreadable-source cases expected empty partial
backups. The focused adapter now gates `.naro-backup-*` and requires unpublished
backup absence. Original screen, cursor, style and successful content assertions
are retained, with executable checks enforcing the screen/cursor preservation.
The failed attempt remains in `save-terminal/`; the final passing rerun is in
`verified-save-terminal/`.

## Limits

These are fixture-owned Linux host checks, not a new release, guest-VT or
physical power-loss qualification. Identity comparison and unlink remain
separate filesystem operations; concurrent external writers require
coordination. No race or exploitation claim is made. No global installation,
push, publication or unrelated untracked-file change is part of this correction.
