Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

# 96 — Specification completion report

The requested documentation phase is complete for the declared Linux/glibc/
ncursesw envelope. Added the overview, Rust architecture, test plan and exact
normalization policy, comparison tool, coverage report, decision register, data
README, progress checkpoint, structural audit and comparator regression tests.
All inherited behavior documents remain available with the full source hash.

Audit: 248 requirement headings; 309 unique recorded terminal scenarios;
46 non-tty probes; 81 regex cases in two locales; 13 effective binding profiles.
All required documents and local links validate. No failed recorded assertions
or timeouts. Ten intentional SIGKILL observations and extensive source-only
branches are explicitly listed, not claimed as full verification.

Twelve comparator regression tests pass. All 309 original runs compare equal to
themselves. A fresh reference smoke replay passes four assertions and matches
the original after the documented normalizations. This exposed and fixed the
tmux dead-pane date banner and historical result-schema differences. The audit
also removed three obsolete duplicate scenario definitions from the runnable
corpus, preserving them in an archive. Ten recording definitions now end with
equal-duration sleeps instead of failed wait_exit steps; archived originals and
raw reference recordings preserve the distinction. The pinned source worktree remains clean.

The spec is ready for implementation; it does not claim that Naro already
implements nano. Implementation/build/test results belong to the repository
status report. Open runtime gaps and deliberate safety deviations are recorded
in 97/99. Original reference observations have not been rewritten to hide them.
