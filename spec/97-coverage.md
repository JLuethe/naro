Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

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

## Planned follow-up coverage

[Document 19](19-completion-and-release.md) and
[data/follow-up-tests.csv](data/follow-up-tests.csv) add planned implementation,
verification and release requirements. Their cases have not been executed.
The audit reports their counts and statuses separately from the original 248
requirements and 309 recorded reference scenarios. Required gates, conditional
environment checks and optional tiny/runtime-credits work remain distinct.
