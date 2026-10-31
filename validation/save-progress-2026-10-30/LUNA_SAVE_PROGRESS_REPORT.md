# Luna independent save-progress verification

## Conclusion

The save-progress fix passes my independent behavioral verification in both frozen environments. All 13 permanent cases match pinned GNU nano, with their expected assertions and steps passing. The old frozen NARO candidate fails all 13, including both transient FIFO phases. I found no editor behavior blocker in this review.

This report does not finalize whole-release readiness: the separate release asset/package review is still underway. Publication remains unapproved.

## Executed

- Ran `verify-freeze.py` before and after verification. Frozen source, binaries, references, scripts and recorded inputs matched; frozen source remained clean.
- Ran the host `save-progress` suite against frozen host nano with a private `NANOSPEC_WORK` root: 13/13 exact matches, 13/13 accepted, candidate and reference harness statuses 0. Every recorded assertion and interaction step passed. Raw terminal captures, result JSON, copied binaries, scenarios and logs are under `host-private/`.
- Ran the Ubuntu suite in the pinned image against the frozen Ubuntu binary and installed pinned nano. I adapted the qualification startup: private source copy, candidate at `/work/naro/target/release/naro`, installed reference at `/work/reference`, all frozen locale definitions, and scenario `locpath` rewritten only in the private copy. It passed 13/13 exact matches. Raw evidence is under `ubuntu/run6/`.
- Reopened all five required suite evidence sets (58 + 6 + 15 + 40 + 13) with fresh copied directories and `check_closure_regressions.py`. All five suites passed for host and all five passed for Ubuntu; complete evidence and exact candidate/reference/source identities validated. Logs are `reopened/host-collector.log` and `reopened/ubuntu-collector.log`.
- Ran the full `tools/collect_closure.py` using the host and Ubuntu qualification inputs, both guest VT reports, transport report, and final package/package-check inputs from the review map. It re-collected 99/99 checks with zero failures and exit 0 at 2026-10-31 06:25:42 UTC. Exact command, timestamps, status, and output are in `whole-release-collector/COMMAND.log`; the newly collected reports and gate are in `whole-release-collector/output/`.
- Ran the old frozen candidate as a negative control against the frozen host reference. Reference assertions passed; old NARO failed every case (0/13 matches), including missing cursor/status during FIFO open and subsequent write. Evidence is in `old-control2/`.
- In a private scratch copy of the scenario and verifier, changed one expected screen row to an intentionally wrong string. Both harnesses exited 1 and recorded failed checks; the required closure collector rejected this evidence with nonzero statuses and failed assertion/recomputed-expectation checks. The comparison-only `accepted` count remained 13 because the reference and candidate recordings were still identical. Evidence is in `wrong-assertion/`; no permanent scenario was changed.

## Static review

The frozen production diff follows the required ordering:

1. Existing path validation, append/prepend restrictions, backup handling, and output construction occur first.
2. FIFO writes paint “Writing to FIFO...” before the blocking open.
3. A successful open paints “Writing...” before any output bytes or `sync_all`.
4. FIFO writes continue with “Writing...” before data transfer and skip regular-file sync, matching the prior FIFO behavior.
5. Once the filename prompt is accepted, the native cursor is hidden. Progress updates translate the message, update only the status row on a clone of the last screen, and flush while retaining title, buffer, and shortcut rows. After the synchronous write returns, normal success/error rendering resumes.

Coverage includes regular and FIFO writes, direct and selection saves, append/prepend, open/sync errors, color, narrow, minibar, zero display and German translation. The gate helpers stop execution at the relevant open/write/sync entry and require an explicit release file before continuing; the captured gated snapshots therefore observe the blocked operation rather than a timing delay. I found no ordering or rendering mismatch. Tiny behavior is intentionally not qualified by these default-binary suites.

## Reviewed evidence outside the reruns

- The host and Ubuntu 19-case guest VT reports each name the frozen reference identity and their respective frozen candidate hashes, and contain 19/19 passing results. Transport evidence contains six passing checks, including the guest image digest and installed binary verification. These reports were reviewed, not rerun.
- The current 99-check closure gate was independently re-collected from the specified inputs and all 99 checks passed. This collection reopened the guest VT, transport, final package and package-check evidence. I did not repeat the full 303-case matrix, guest VMs, or transport run.
- Final asset/archive/link hashes, package rebuilds and publication metadata were not independently audited here; that work is assigned to the separate release asset reviewer.

## Attempts and limits

`ATTEMPTS.md` records each failed setup attempt and retry. In brief, the first host attempt was blocked by sandbox tmux socket restrictions and passed after scoped escalation. Early Ubuntu attempts lacked the frozen locale/reference installation setup. One intermediate Ubuntu run showed English NARO strings for the German case because it launched the binary outside the qualification executable/asset layout; the corrected run6 setup passed all 13. These were environment setup issues, not established candidate mismatches. All outputs were preserved.

I did not rerun the full historical matrix or optional tiny profile. I did not modify tracked source, permanent tests, frozen files, release files, Git refs, or publication state. No verification processes remained after the runs.
