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


The counts above describe the original completed behavioral baseline. Document
19 is a planned follow-up covering remaining implementation, verification and
release work; its requirements and proposed test matrix are counted separately.
Adding that plan does not implement it or change historical validation results.

## Follow-up implementation and verification (2026-10-24)

The doc 19 default-profile preview requirements are implemented and verified.
The matrix has 37 verified rows and four deferred rows: conditional real VT and
isolated-root checks, and two optional tiny checks. Runtime credits are now
implemented as a default-off feature. Historical counts above remain historical.

The [follow-up gate](../validation/follow-up/gate.json) passes all 48 checks.
Host and ordinary-user Ubuntu 24.04 builds each have 301/303 full terminal matches,
38/38 CLI matches, and 162/162 local-regex matches. Each environment has 53 new
paired cases, 51 full matches and two explicitly accepted tool-cleanup differences.
Separate safety and named/unnamed/multibuffer panic assertions pass. All 41
catalogs resolve from installed layouts; source archives rebuild with matching
input fingerprints. Archive integrity, private install/removal ownership, large
file bytes and an agent-operated interactive checklist pass. Original reference
evidence and the pinned source worktree remain intact.

See [completion evidence and scope](../validation/follow-up/README.md) and
[limits](../validation/follow-up/limits.json). Root-account home precedence is
an additional known out-of-scope difference (Q-ENV-ROOT-001). No real-console,
root-account, translation-quality or tiny parity is claimed. Artifacts are staged
for review; a tag or GitHub release has not been published.


## Root phase outcome

Doc 20's automated work is implemented: eight verified matrix rows, 27 exact
new namespace comparisons, one explicit no-home source-crash recovery decision,
and unchanged ordinary-user regression results. All 16 root-phase gate checks
pass. The prior isolated-root path deferral is closed with fresh evidence.
The console readiness checker and operator protocol are built, but the current
PTY cannot provide physical-key/VT evidence, so two manual rows remain deferred.
See [current root evidence](../validation/root-console/README.md). No host console
or passwd configuration was changed, and no new release was published.
