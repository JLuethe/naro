# Independent candidate identity policy review — 2026-10-31

Reviewed `spec/tools/candidate_expectations.py`, its 88-case override file, harness selection, follow-up recording validation, tiny/CLI expectation integration, and the six policy unit tests.

The policy deep-copies candidate cases and verifies each reviewed override against the original complete case SHA-256 and the package version. It preserves the source/reference cases and does not rewrite recorded output. The strict evidence checker independently requires the exact derived candidate scenarios and their per-recording scenario hashes; reference scenarios still must equal the original frozen cases.

Independent structural comparison found all 88 overrides bound to current original cases. The changes are exactly:

- 165 complete title-row equality assertions.
- One startup header substring assertion.
- Three panic diagnostic substring assertions.
- One startup welcome wait-text change.

There are no changed key sequences, typed bytes, file expectations, exit statuses, cursor expectations, attribute expectations, assertion-list lengths, or expectation key sets. All 165 title transitions validate against the explicit title-layout oracle. The raw `compare_runs.py` comparator remains unchanged, so actual screen differences remain observable and must be accounted for explicitly in fresh qualification.

The policy tests passed 6/6, including negative controls for filename, modified state, attributes, cursor, saved bytes, exit status, stale source/version binding, and old branding. A review suggestion to assert screen-list lengths and expectation key sets before zipped comparisons was incorporated and the tests passed again.

`policy-cross-review.json` retains every old/new changed value and its original scenario source. The original `assets`, `spec/evidence`, and `tests/follow-up/scenarios` have no git diff. The production locale alias follow-up affects C/German identity outputs neither in these overrides nor in the independent CLI output policy.

No blocking issue found in this bounded policy review. This is not a claim that the new release candidates have completed the full release matrix. No files owned by the policy agent were edited by this reviewer.
