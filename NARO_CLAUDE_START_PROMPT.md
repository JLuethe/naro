> Historical testing assignment — superseded; consult current next steps.
> Steps 5–7 are complete; see [current next steps](NARO_NEXT_STEPS.md) and
> [package/gate results](NARO_STEP7_RESULTS_2026-10-30.md). Do not rerun this
> assignment or replace its candidate paths without a new testing request.
> The original instructions below are preserved as historical evidence.

# Claude starter prompt

Before resuming, read the current checkpoint in `NARO_NEXT_STEPS.md`. The original
testing assignment below has been completed and its findings fixed by Codex;
use it for the testing role and workflow, with the current candidate and scope.

Work in `/home/john/Code/naro`. Read `NARO_CLAUDE_HANDOFF.md` completely and
follow its linked restart review and shared testing instructions.

Resume independent testing of NARO, the Rust nano editor, after a laptop power
interruption. Codex remains the sole development owner. You may inspect source,
build stable candidates, run tests and write new scratch probes/evidence in the
handoff's permitted directories. Do not modify application code, existing tests,
fixtures, expectations, harnesses, specs or configuration. Do not commit or push.
Return defects and proposed regressions to Codex for implementation.

Create a durable run directory under `target/naro-test-runs/` as instructed and
maintain `PROGRESS.md` there after every batch. Verify the pinned GNU nano and
freeze/hash the default NARO candidate. Run the unchanged 58 wrap and six filter
controls and full artifact checker first.

Then recover the 35 probes from `opencode-testing-report.json` using the exact
instructions in the handoff. The interrupted export reports nine differences:
prioritize the paste/redo saved-text mismatch, then soft-wrap movement/resize,
then soft-only attributes. These need independent reproduction; historical
PASS messages and the export's `succeeded` status are not acceptance evidence.
Capture actual comparator exit codes and ensure all intended cases are selected.

Minimize verified failures without changing repository files. Continue the
remaining independent matrix where possible. Preserve full two-sided recordings,
raw traces, saved bytes, commands, child statuses and failed attempts. Do not
weaken assertions or invent compatibility deviations. If changes to source or
the harness are required, report the need to Codex.

Deliver `CLAUDE_TEST_REPORT.md` in the durable run directory with findings,
reproductions, identities, results, remaining work and repository-integrity
checks. Return its absolute path. Begin with repository/evidence inspection and
candidate preparation; do not stop at proposing a plan.
