# Candidate identity expectation work

Passed within focused scope: six identity policy tests with orthogonal negative
controls, six harness tests, 44 strict evidence tests, 14 unchanged raw-comparator
tests and nine closure-validator tests. New 21 real-terminal layout cases pass
all 105 assertions and all steps/exits on the recorded 0.1.1 development binary.
This is not full host/Ubuntu/guest-VT qualification.

Source integration and exact hashes are in SUMMARY.json. All existing reference
scenario files, tiny CLI oracle and raw comparator were left unchanged. 88
candidate overlays bind to original case hashes and 0.1.1. CI now opts into
candidate expectations and exercises CLI branding in default/tiny builds. The
strict checker separately validates selected candidate scenario hashes.

Raw identity differences remain exposed. The old exact-count collector cannot
qualify the new source until the next qualification step explicitly reviews and
reports those differences. No code here suppresses those raw differences.

The initial pure-model unit test placed the hide boundary one column too high;
it was corrected from 33 to 32 after checking the independent fit arithmetic.
No real candidate capture was used as the oracle. Dispatch interruptions were
transient; no failed product recording was accepted.

Unit command outcomes were recorded from tool results; start/end timing and raw
unit stdout were not persisted here. Layout terminal recordings/stdout/stderr
are complete under layout/. Parent owns final source commit and candidate freeze.
