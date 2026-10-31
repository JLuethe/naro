# Attempts

## Attempt 01 (previous CLI session) — permission-blocked, no verification, no pass

- Result retained (not modified) at
  `target/narrow-progress-2026-10-31/claude-final-evidence-attempt01-result.json`,
  SHA-256 `4f39ac53b456e3d4edc866b1d294a47c0b119ecce8469e890a71fd3737f63b06`.
- Four Bash calls were denied (`set -e`/`mkdir`/`cat` logger setup, two `mkdir -p`
  retries, and `git -C /home/john/Code/naro rev-parse HEAD`). The session ran no tests,
  hashed nothing, wrote no files in this directory and explicitly gave no pass.
- Its inspected-only notes are superseded by this attempt; none were reused as evidence.

## Attempt 02 (this session)

All commands ran through `tools/run.py` (python3 + subprocess, explicit cwd); each has
`cmd/NNN-label/argv.json` (argv, cwd, UTC start/end, status), `stdout`, `stderr`, `status`.
`COMMANDS.json` indexes all 54 commands with output hashes.

Failed or corrected steps inside this attempt (all preserved):

1. Two Bash tool calls were rejected by the harness before execution (not run):
   one began with a shell variable assignment, one heredoc contained a brace/quote
   pattern. Both were rewritten as plain `python3` invocations. No command output exists
   for them because nothing executed.
2. `cmd/021-verify-assets` exited 0 but recorded 4 FAIL checks
   (`scratch/assets/verify-assets.json`). Cause: wrong expectations in my script, not
   artifact defects. (a) The binary archive also has `install.py` and `manifest.json`
   beyond the 138 `build.json` payload entries. (b) Six packaged docs differ from the
   commit only because relative repository links are rewritten to pinned
   `blob/6473fe2…` URLs. Resolved by `cmd/022-doc-diff` and `cmd/023-payload-extra`:
   the installer equals `tools/release/install.py` at the tag, `manifest.json` equals
   build.json minus `source_files`, and all ten docs equal the commit text once the
   pinned-URL prefix is removed.
3. `cmd/040-backup-verify` exited 1. Cause: my script treated tar hardlinks and FIFOs as
   unsafe without hashing them, did not discount the manifest file stored inside the
   archives, and crashed while printing. The original script is preserved as
   `tools/backup_verify_attempt1.py`, with its partial output in `cmd/040-*`.
   The corrected `cmd/041-backup-verify-attempt2` passed every check against new output
   `scratch/backup-verify-attempt2/`.

No assertion, normalization or expectation in project tooling was changed. No new
behavior probe was needed (no concrete gap found).
