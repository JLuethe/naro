# Hard-wrap and filter qualification after Pi review

Reference GNU nano 9.3: clean commit
`6ed285c3ec7a1d228def4d4e7021c6ba269f620c`, executable SHA-256
`b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2`.

Current measured scope is **58 wrap cases and six filter cases**.
[Review](../../NARO_PI_TEST_REVIEW.md),
[development evidence](../../NARO_DEVELOPMENT_PROGRESS.md) and
[next testing assignment](../../NARO_TEST_AGENT_HANDOFF.md) give causes,
before/after results, identities and remaining limits. `coverage.json` is a
tracked summary, not a substitute for the complete local evidence bundle.
Q-UNDO-002 remains partial.

The prior 39-case `next-wrap3` checkpoint was real evidence for those inputs.
It missed two mark-transform defects, including two caught crashes. Its
candidate/build/report hashes identify historical artifacts. They cannot be
used to claim the current expanded suite was replayed.

## Cases

`tests/follow-up/scenarios/wrap-undo.json` retains 001–039 for wrap grouping,
saved points, node identity/lifetime, NUL, prefixes, fill geometry, quoting,
continuation indentation, paste and lower-line mark shifting. Added cases:

| IDs | Decisive behavior |
|---|---|
| 040/041 | Mark from the split line moves to its continuation once; cut preserves TAIL or handles EOF without panic. |
| 042/043 | Mark from the eaten successor receives prefix and extra-blank deletion mapping. |
| 044 | Burst ` eee ` reaches the guard that skips adding another separating space. It is reachable through typing. |
| 045/046 | Additional forward selection and mark-inside-removed-prefix reproductions. |
| 047–050 | Marks before, at and after the split; zero/end-boundary controls. |
| 051–055 | Marks before, inside and after duplicated indentation on a live successor. |
| 056–058 | UTF-8, quoted and trimblanks marked splits with subsequent cut/undo/redo. |

New cases assert oracle-derived saved bytes, cursor and selected-cell attributes;
paired replay compares full visible cells/modes/files/exit. Old expectations
were preserved. Case 017 actually saves `aa bb ccc  \neee fff ddd\n`;
022 loads `aaab\0bbb cccc` with NUL at offset 4, before the split at byte 9;
039 saves `aaa bbb \ncccdeTAIL\n`, removing only the selected line break.

`tests/follow-up/scenarios/filter.json` contains six additional cases: identity
filter through magic EOF, uppercase midline filter/end cursor, ordinary newline
paste control, wrapped filter/history, failed-filter mark clearing/history and
immediate full save after failure. Nano cuts, restores magic EOF and then
inserts output, so a marked EOF identity filter can retain an extra blank line.
Marked filters retain insertion-end cursor; unmarked filters return to the
original line/x=0. Failed in-place filters clear the selection.

## Reproduce with fresh evidence paths

```sh
cd /home/john/Code/naro
export NARO_VERIFY_RUN="$(mktemp -d /tmp/naro-verify-XXXXXX)"
/home/john/.cargo/bin/cargo build --release --target-dir "$NARO_VERIFY_RUN/build"
env NANOSPEC_WORK="$NARO_VERIFY_RUN/wrap-work" python3 tools/check_follow_up.py --suite wrap-undo --binary "$NARO_VERIFY_RUN/build/release/naro" --out "$NARO_VERIFY_RUN/wrap"
python3 tools/check_wrap_undo.py --report "$NARO_VERIFY_RUN/wrap/report.json"
env NANOSPEC_WORK="$NARO_VERIFY_RUN/filter-work" python3 tools/check_follow_up.py --suite filter --binary "$NARO_VERIFY_RUN/build/release/naro" --out "$NARO_VERIFY_RUN/filter"
```

Stop on a failed build or replay; preserve each actual exit code. The runner
freezes binaries and scenarios. The report checker requires those artifacts,
side-scenario files, every recording and raw trace. It recomputes expectations
and comparisons, checks full step/snapshot membership, byte metadata, pinned
reference, default features and production/tools fingerprints. Missing evidence
fails. It never executes an arbitrary report-supplied binary. Artifact integrity
is not signed authenticity. Manifest-only validation still works without nano.

Keep source and verification tools stable during replay. Source fingerprints
follow build.rs; test/scenario/tool identities are separate. A Git revision
change alters embedded revision and can change binary hash with the same source
fingerprint. Do not relabel an earlier frozen executable as a newer build.

The retained 303-case baseline requires `/tmp/nanospec-work`: path-bearing
messages were centered before normalization, so longer roots create false
padding differences. Run it serially with a fresh output path. New two-sided
suites use private work roots and do not need the retained path.

## Limits

Hard+soft wrap, scrolled viewport and resize mid-history, magic-EOF followed by
a decisive accepted join, and structural callers beyond the measured cases
remain incomplete. Pi's case named SOFTWRAP omitted `-S`; scenario names alone
do not establish coverage. Unicode lead/blank/quote combinations, invalid bytes,
input chunking and full sanitizer/physical-console qualification remain open.
Tiny intentionally omits hard wrapping and history. No full-parity or release
certification is claimed.
