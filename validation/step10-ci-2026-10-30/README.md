# Saved-screen CI synchronization diagnosis — October 30, 2026

CI run 41168721954 captured `TEST-STEP3-EOF-NOFINAL-LIVE` while NARO still
showed the write prompt (20,21). Only the saved cursor assertion failed; bytes,
exit, and the other 19 assertions passed. Original job trace timing was not
retained, so its precise syscall latency cannot be recovered from the log.

Controlled probes interpose fsync only inside synthetic private fixtures. At
0 ms delay the original scenario passes. At 600 and 1,200 ms it captures the
identical NARO prompt/cursor failure on both frozen host and Ubuntu candidates.
The pinned host nano also fails the original saved-cursor assertion during its
own write-in-progress display. Within each executable the complete raw output
hash is unchanged between delayed and non-delayed runs: this is sampling an
intermediate frame, not different final output or saved bytes.

The scenario now waits for `Write to File:` before Enter and `Wrote 2 lines`
before the saved snapshot, each with a five-second failure timeout. All existing
expectations and input bytes are unchanged; no comparator, normalization,
harness implementation, production source or executable changed. The synchronized
scratch case passes all three delays on all three tested executables (9/9).
This demonstrates and fixes a test synchronization defect matching the CI symptom;
it does not claim direct measurement of the historical CI filesystem latency.

Full-suite follow-up and final CI receipts are recorded in the step 10 release
review. Claude's independent verification is separate and must not be described
as completed by these Codex results. The preserved original failure remains
under validation/step8-9-release-2026-10-30/previous-ci-failure.log.
