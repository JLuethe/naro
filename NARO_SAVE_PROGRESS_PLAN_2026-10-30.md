# Save-progress repair and renewed release qualification

John selected implementation and requalification after Claude's independent
step 10 report identified the missing save-progress message. The previous
release proposal is superseded pending new production candidates and evidence.
No tag or publication is authorized.

1. Preserve and verify Claude's evidence. Completed: 8,501 manifest entries,
   zero mismatches; full archive outside target under
   `/home/john/Backups/naro/2026-10-30-claude-step10/`.
2. Match nano's transient regular-file `Writing...` status after successful open
   and before writing/syncing. Match `Writing to FIFO...` before blocking FIFO
   open, followed by `Writing...` after open. Preserve translated text, status
   style, hidden cursor, errors, final saved bytes and restoration.
3. Add deterministic regression scenarios that hold the editor inside the write
   operation until the in-progress snapshot is captured. Use explicit synthetic
   acknowledgments, not timing luck or settled final screens. Compare nano first,
   retain those observations, and assert messages/cursor plus final outcomes.
   Cover slow regular saves, FIFO open/write, narrow/color/locale behavior,
   selection/append/prepend, failed open/sync and completion/restoration.
4. Make the new suite mandatory in host/Ubuntu runners, evidence validation,
   CI and the final collector. Preserve historical suite counts and accepted
   differences. Run focused code/tool checks and full affected regressions.
5. Commit the tested production change, freeze clean host and Ubuntu default
   builds from that exact source, and retain compiler/native/reference identities.
   Do not overwrite any previous candidate or evidence directory.
6. Requalify host and Ubuntu: 303-case corpus, CLI/regex, historical follow-ups,
   all mandatory suites, failures/backups/recovery/signals/terminal restoration,
   root/home cases on host, locales/assets, large files, package/source checks.
   Ubuntu must use its own reference observations. New unexplained differences
   block qualification; no normalization or expectation weakening.
7. Repeat both 19-case guest-VT qualifications and transport checks, then collect
   the complete gate for the new candidates. Preserve reports and full evidence
   outside target. Record every attempt and leave no owned processes running.
8. Refresh public identities, source archive (including the repaired save test),
   source/binary packages, qualification sidecars and checksums. Correct the tag
   history wording and record Claude's completed review of the OLD candidate
   without claiming it qualifies new binaries. Prepare updated independent
   verification handoff and exact release proposal; final publication remains
   John's separate decision.

Stale tmux socket cleanup is unrelated and is not part of this repair.
