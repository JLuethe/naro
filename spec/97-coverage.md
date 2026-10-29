Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

Current Pi-review qualification is recorded in `../NARO_DEVELOPMENT_PROGRESS.md`: 58 wrap and six filter cases, with explicit remaining gaps in `../NARO_TEST_AGENT_HANDOFF.md`. Earlier 39-case coverage did not detect all mark failures. Historical inventories below remain distinct from runtime qualification.

# 97 — Coverage and confidence

The behavioral spec is complete as a documented implementation contract for the
reference envelope. Runtime verification is broad but not exhaustive. There are
248 baseline requirement headings, 309 unique terminal scenarios in 23 files, 46
non-tty CLI probes, 81 POSIX regex cases in each of two locales, and 13 debugger
key-table profiles. Only the smoke scenario has explicit assertions (four);
other terminal runs are observations, requiring differential comparison.

## Behavioral areas and recorded evidence

| Docs / area | Terminal suite | Unique scenarios | Confidence / gaps |
|---|---|---:|---|
| 01 CLI | cli, cli-extra | 65 | Options/positions/startup broadly observed; merge branches and parser combinations not exhaustive; 46 additional CLI probes |
| 02 bindings | keys | 12 | 13 effective table dumps supplement scenarios; real VT modifiers unverified |
| 03 input | input | 15 | Escapes, paste, verbatim, selection, resize, click; wheel, interrupts/timing edge cases source-only |
| 04 rendering | render | 25 | Layout, tiny/narrow terminals, decorations, scrolling, colors; one emulator and width table |
| 05 editing | edit, move | 44 | File bytes and screen observations for core edits/movement; hard-wrap combinations remain source-only |
| 06 undo | undo | 11 | Grouping, saved point, join quirks; hard-wrap and all compound combinations incomplete |
| 07 search | search | 19 | Literal/regex/replace/region/zero-length/Unicode; long search cancellation source-only |
| 08 files | files, files2 | 31 | CRLF, bytes, metadata/links, backup, locks, exit, emergency; disk-full/interrupted/FIFO writes not exhausted |
| 09 browser | browser | 4 | Sorting/navigation/search/directories; mouse source-only |
| 10 rc | rc | 11 | Lookup/grammar/errors/precedence examples; full option cross-product source-only |
| 11 syntax | syntax | 10 | Selection/precedence/multiline/update; libmagic source-only; 162 regex executions supplement |
| 12 features | features, features2 | 20 | Justify/tools/macros/history/help/count; credits optional; stub tool behavior is deterministic |
| 13 signals | signals, signals2 | 14 | HUP/TERM, ignore, suspend/resume, exit status, lock cleanup; reentrant die/source-only |
| 14 i18n | i18n | 8 | German/Japanese/French/byte locale; not all 41 translations runtime-tested |
| 17 prompts | prompts, prompt-nul | 13 | Editing/completion/history/restriction, NUL Yes quirk; username listings host-specific |
| 18 byte model | bytes | 6 | Invalid UTF-8/NUL/combining/Latin-1/columns; libc width versions outside envelope unverified |
| Integration | smoke | 1 | Four explicit assertions, normal unsaved exit |

Cross-area evidence is cited in the individual docs. Table counts count suite
ownership once, not every related requirement. `data/requirements.csv` is a
heading/nearby-test index; range/shorthand references and source-derived claims
need the prose/evidence tables for precise interpretation.

## Evidence audit

`tools/audit_spec.py` checks document presence/hash headers/local links, unique
scenario IDs, matching full reference hashes, missing/failed evidence, timeouts
and the clean pinned worktree. It writes `evidence/audit.json` and
`data/requirements.csv`. `tools/test_inventory.py` writes the run inventory.
`tools/test_compare_runs.py` checks comparator failure detection, wide/combining
cell indexing, lock masks, blank attributes, stdout, timeouts, dead cursor and truncated dead-pane timestamps.
Self-comparison of all 309 runs yields zero differences. A separate fresh smoke
replay checks reproducibility; this is not candidate validation.

The audit found three superseded definitions in `files.json` (014, 016, 017)
that duplicated corrected definitions in `files2.json`. Original definitions
are preserved in `evidence/superseded-scenarios.json`; only the corrected ones
remain runnable. The reference result directories already correspond to the
corrected definitions. This eliminates ambiguous replays without inventing data.

Ten runs deliberately ended with harness SIGKILL; see audit JSON for IDs.
Their inherited final `wait_exit` steps timed out. Runnable definitions now
use equal-duration `sleep` steps, accurately requesting a recording instead of
a clean exit; original steps are archived in
`evidence/recording-timeout-corrections.json`. Raw reference results are intact. They
still contain observations but do not prove clean exit or restoration. The
reference crash TEST-CLI-057 is recorded normally through nano's handler and
must be treated as a declared candidate deviation, not a reproduced defect.

## Known limits and acceptance boundary

All 18 C files and the three man pages were read in the inherited session.
Final audit cross-checked the Texinfo editor basics, invocation, exit status,
options and build feature descriptions against the contracts. This is a
behavioral specification derived from source plus experiments, not a formal
proof of exhaustive behavior. Existing L-1…L-7 limits remain explicit in 00.
Planned IDs appearing in earlier docs are backlog suggestions, not missing
recorded evidence. In particular TEST-EDIT-WRAP-*, TEST-RC-PREC-* and
TEST-INPUT-020… must not be counted as executed.

Implementation acceptance requires the whole default-profile corpus (apart
from explicitly listed deviations), regex corpus, safety-deviation assertions
and additional probes for implementation-specific risks. New platform, libc,
locale or terminal combinations need separate evidence. Native compilation,
a smoke pass, or file-only agreement alone cannot satisfy the complete target.

## Follow-up coverage

[Document 19](19-completion-and-release.md) and
[data/follow-up-tests.csv](data/follow-up-tests.csv) add implementation,
verification and release requirements. Their evidence-linked statuses are
recorded separately in the matrix and [validation](../validation/follow-up/README.md).
The audit reports their counts and statuses separately from the original 248
requirements and 309 recorded reference scenarios. Required gates, conditional
environment checks and optional tiny work remain distinct. Runtime credits are verified in an opt-in build.


## Root and console phase

[Doc 20](20-root-and-console.md) adds nine requirements and a separate ten-row
matrix. Eight automated rows are verified; two physical-console rows remain
deferred. The isolated-root gate from doc 19 is now verified by fresh private
null-device and filesystem-root browser observations. See
[root-phase validation](../validation/root-console/README.md): 27 exact new
comparisons, one named source-crash recovery difference, and unchanged ordinary
regression results. This does not certify general host-root privilege behavior
or real Linux console input. Earlier reports retain their historical scope.

## Console and delivery closure

[Doc 21](21-console-release-closure.md) adds seven requirements and the
[closure matrix](data/closure-tests.csv). The full guest-console suite has 19
exact matches for each optimized host and Ubuntu candidate; transport and ioctl
model evidence are separate. See [console evidence](../validation/console-vm/README.md).
This closes the recorded guest-VT scope, while physical keyboard/operator rows
remain deferred. Final cross-environment regression, artifact verification and
delivery outcomes are linked from [closure evidence](../validation/closure/README.md).
The audit now counts 248 baseline and 38 follow-up requirements, 286 total.

Final closure outcome: all seven doc 21 matrix rows are verified. Across the
three follow-up matrices, 53 rows are verified and five optional/physical-console
rows remain deferred. The 85-check combined gate and GitHub delivery receipt are
in `../validation/closure`; this does not expand the original baseline corpus.

## Optional tiny closure (2026-10-25)

Doc 22 is verified by [31 linked gates](../validation/tiny/gate.json): 59 exact
editing/terminal cases, 125 CLI probes, eight modeled VT cases, 194 CI/assertion
cases and paired size/dependency measurements. Default regression remains
301/303 exact with the two documented safety differences. Both profile packages
pass source-rebuild/feature/installation checks. The two optional tiny rows in
the follow-up matrix are now verified; only three physical-console operator
rows remain deferred. Earlier tiny deferrals above describe historical scopes.
These results do not erase source-only caveats or certify arbitrary build flags.

## Hard-wrap undo/redo combinations (2026-10-28, updated again)

The documented runtime gap **Q-UNDO-002** (hard-wrap undo in all chunk
combinations) is **partially covered** for the default profile by
thirty-nine fresh differential scenarios in
[`tests/follow-up/scenarios/wrap-undo.json`](../tests/follow-up/scenarios/wrap-undo.json),
replayed against the pinned GNU nano 9.3 default build. See
[`../validation/wrap-undo/README.md`](../validation/wrap-undo/README.md):
39/39 exact matches across file bytes, modified/saved state, cursor and
screen through undo and redo, with `capture_file` saved-byte checks for the
structural, save, prefix, NUL, cut, mark, quote, fill, indent and
production-NUL-join scenarios. No declared deviations. A machine-checked
manifest ([`tools/check_wrap_undo.py`](../tools/check_wrap_undo.py))
validates the exact 39 scenario IDs, no gaps, the per-side assertions of a
recorded report, the pinned reference and candidate provenance and the
scenario digest; it is CI-checked via `.github/workflows/rust.yml` together
with its negative tests (`tools/test_check_wrap_undo.py`).

The cases cover mid-line wrap; group break; two separate wraps; autoindent;
spillage join with redo and continued editing; short-overflow/non-matching
prefix; the spillage **generation identity** model through structural
undo/redo (Delete/Backspace join with a fill-accepted remainder), whole-line
cut of the target, and ordinary-addition redo; divergent edit; save/
`Modified` round trip; autoindent+spillage; mismatching nonempty prefix; an
empty and a one-character target; tabs; UTF-8; whitespace at the join point;
fill-rejected join; trimblanks; embedded NUL before/after the wrap point and
through a production live-overflow join; the explicit mark through a join;
the quote prefix; the continuation indent; the nonpositive fill geometry;
and a paste that edits or shifts the live target.

The spillage marker is a stable per-line generation and every splice states
which node survives (a join keeps the top node, a whole-line cut keeps the
bottom node, a partial multiline cut keeps the top node), so a freed line's
identity is not restored when text is recreated by undo/redo and a detached
(cut) target does not retarget the following line. The explicit mark now
follows the reference's `expunge`/`do_enter` rules through the join, the
added space, the prefix removal, the blank trimming and the split instead
of collapsing to column zero. F1 unsafe prefix removal (crash), F2
embedded-NUL corruption (including the production join path), F3/R1 stale
spillage identity across structural edits and whole-line cut, F4/R2
structural and ordinary spillage lifetime through history, R3 trimblanks
cursor hazard, the explicit-mark corruption, the operation-specific survivor
identity, the missing quote prefix, the reduced-width fill geometry and the
continuation indent sampling were reproduced and fixed in
`src/features.rs`/`src/buffer.rs`/`src/files.rs`. The formerly ineffective
branches (`007`, `008`, `012`, `013`, `014`, `015`, `017`) were repaired so
that each one reaches its advertised branch. Default regression remains
301/303 exact with the two documented safety differences.

Remaining limits: the interactions of hard wrapping with soft wrap, view
mode, terminal resize and the magic-line `WAS_BACKSPACE_AT_EOF` undo quirk
are not separately verified. The **tiny profile** has no undo/redo or hard
wrap by design (doc 22). Q-UNDO-002 remains partially open until those are
covered or explicitly scoped out.
