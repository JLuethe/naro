# NARO next steps: hard-wrap parity handoff

> **Status (2026-10-28):** the outstanding work that this handoff
> describes has since been implemented and verified; the hard-wrap undo/redo
> suite now has 39 cases and matches the pinned reference exactly. See
> `spec/98-progress.md` (the final checkpoint) and
> `validation/wrap-undo/README.md` for the current state. This document is
> kept as the handoff that motivated that work; the steps below describe the
> tree *before* it.

Reviewed 2026-10-28. Start with [NARO_SESSION_REVIEW.md](NARO_SESSION_REVIEW.md),
whose current review precedes a retained historical review. This is an
implementation handoff, not a certificate of parity.

## Starting state and first action

Repository: `/home/john/Code/naro`; branch `main`; HEAD and verified live
`origin/main`: `823cb96cc6aba9281b58da7ad33dfa3dd4a6a138`.
The hard-wrap implementation, scenarios and verification changes are still
uncommitted. Do not reset, clean, discard or blindly stage the user's tree.
No application source was modified by this review; no commit or push was made.

**First preserve the current diff and reproduce the explicit-mark failure and
the empty-predecessor Delete/Backspace failures below against the pinned
reference and a fresh default build. Add failing permanent scenarios before
fixing them.** These are demonstrated saved-byte discrepancies, despite the
existing 27/27 pass. Do not begin with another full baseline run.

Read `CONTRIBUTING.md`, `spec/05-buffer-and-editing.md` (EDIT-015, EDIT-020,
cuts/paste), `spec/06-undo-redo.md`, `spec/12-features.md` (FEAT-QUOTE and
paragraph boundaries), `spec/97-coverage.md`, the hard-wrap checkpoint near
the beginning of `spec/98-progress.md`, and Q-UNDO-002 in
`spec/99-open-questions.md`. `NARO_HARDWRAP_REVIEW.md` is the earlier review;
its old defects are partly fixed and its proposed reproductions must not be
confused with this review's observed failures.

Capture `git status --short --branch`, `git diff HEAD`, `git diff --cached`,
`git branch -vv`, `git remote -v`, relevant untracked inputs and fingerprints
in a new directory. Never delete an earlier attempt to reuse its path.
Use a unique `NANOSPEC_WORK` for each run; output paths alone do not isolate
fixtures. Do not run overlapping full baseline validations.

## Priority 1: preserve the live explicit mark during a wrap join

**Severity P1: a later cut removes unintended text.**

Files/functions:

- `src/features.rs:418`, `Editor::hard_wrap`, especially the full two-line
  replacement at lines 520–530 and the following split.
- `src/buffer.rs:314`, `Buffer::replace`, especially its generic mark offset
  clamp at lines 382–391.
- `src/basic_features.rs:112`, `Editor::cut`, for the downstream observation.

Reproducer `REVIEW-MARK`, default `-I -b -r 12 f.txt`, initial file `\n`:

1. Type `aaa bbb ccc ddd` to create a live overflow `ddd`.
2. Home, Right, M-A (explicit mark at column 1 in `ddd`).
3. Up, End, type ` eee` to perform a fill-accepted spillage join.
4. Snapshot selected cells and cursor; cut with Ctrl-K; snapshot and save.

Reference saved bytes: `b'aaa bbb ccc  \neeedd\n'`.
Current NARO saves: `b' ddd\n'`.
The visible text initially agrees after the join, but selection attributes
already differ. The generic replacement treats surviving text as deleted,
clamps the mark to the start of the replaced span, and the following cut
exposes the error.

Suggested fix: perform the join, optional inserted space, duplicate-prefix
deletion, blank trimming and split with explicit logical-position mapping,
or introduce primitives that preserve marks in surviving segments. Map marks
on both source lines through each actual byte change; do not just restore
the old numeric offset. Preserve external/internal NUL conversion. Inspect
pinned nano `src/cut.c:expunge` and `src/text.c:do_enter`/`do_wrap` for exact
mark movement. **Undo and redo themselves clear the mark in nano**; retain
that behavior instead of preserving a selection across history indiscriminately.

Permanent tests must cover marks before/inside/after the moved remainder,
inside a stripped prefix and on the overflow, both selection directions,
then cut and subsequent undo/redo. Assert selected-cell attributes, cursor,
saved bytes and Modified state, not just the text before the cut.

## Priority 2: distinguish operation-specific line survivors

**Severity P1: spillage retargets a node that GNU nano deleted/detached.**

Files/functions:

- `src/buffer.rs:314`, `Buffer::replace`; `single_survivor` at line 346.
- `src/buffer.rs:453`, `Buffer::delete`; `Buffer::cut` at line 549;
  `Buffer::enter`, `Buffer::undo` and generation remapping.
- `src/features.rs:418`, live-generation comparison in `Editor::hard_wrap`.
- `src/basic_features.rs:112`, operation/range selection in `Editor::cut`.

The predicate `count == 1 && b.line > a.line && a.x == 0 && raw.is_empty()`
does not identify a whole-line cut. It also matches Delete on an empty line,
Backspace onto an empty line, and a partial multiline selection ending at
`b.x > 0`. These operations have different node survivor rules.

Observed reproducers, all `-I -b -r 12`, initial file
`b'aaa bbb ccc\n\nTAIL\n'`:

1. Down; type `aaa bbb ccc ddd` (wrap on the initially empty second line).
2. Up, Home; Delete twelve characters, leaving an empty predecessor above
   the live overflow `ddd`.
3. Delete to join it with `ddd`; alternatively Down, Home, Bsp.
4. Up, End; type ` eee`; save.

`REVIEW-EMPTY-DEL` and `REVIEW-EMPTY-BSP`:
reference `b'aaa bbb ccc \neee\nddd\nTAIL\n'`;
NARO `b'aaa bbb ccc \neee ddd\nTAIL\n'`.
The later join is fill-accepted (3-byte remainder plus 3-column target),
so live identity determines the outcome.

For `REVIEW-PARTIAL-CUT`, after step 1: Up, Home, M-A, Down, Home, Right,
Ctrl-K (cut from predecessor column 0 through the first `d` of overflow).
Then Up, End, type ` eee`, save.
Reference `b'aaa bbb ccc \neee\ndd\nTAIL\n'`;
NARO `b'aaa bbb ccc \neee dd\nTAIL\n'`.

Reference rules to implement, with pinned `src/cut.c:expunge`,
`extract_segment`, `ingraft_buffer`, and `src/text.c:do_enter`, JOIN/CUT/PASTE
undo/redo open beside the Rust code:

| Operation | Active node that survives |
|---|---|
| Delete/Backspace join | Top/current node survives; lower node is freed, even if top is empty |
| Cut with top and bottom x both zero | Following/bottom node survives; the whole top lines detach |
| Partial multiline cut | Top node survives; bottom suffix is copied into it and bottom node detaches |
| Enter/split | Top node survives; bottom is a new node |
| In-place character edit | Same node survives |
| History recreating deleted text | Fresh node identity; no resurrection of spillage |

Suggested fix: pass an explicit edit/survivor policy from operations that know
what happened, or use separate primitives. Adding `b.x == 0` to the heuristic
would address the partial-cut distinction but **would not fix empty-line
Delete/Backspace**, whose endpoint coordinates also look like a whole-line
cut. Do not replace the generation model with indices, clear every marker
unconditionally, or restore snapshot identity as if it were live identity.

Test target/top/bottom/surrounding nodes; whole-line and partial cuts;
paste/file insertion/filtering; cutbuffer append and replacement; joins with
empty/nonempty top; Enter before/on/after target; undo, redo and divergence.
Include a surviving target elsewhere during unrelated history. Assert
`lines.len() == generations.len()`, unique live generations, fresh IDs for
new nodes and stable IDs for survivors. Inspect direct `state.lines` writes
in `src/files.rs`, justification and external-tool paths before declaring
this shared model complete. Do not assume all generic splices reproduce
nano's operation-specific node lifetimes.

## Priority 3: make regression evidence fail closed

**Severity P1 for acceptance reliability.** This work can proceed independently
of application fixes, but merge it before declaring any parity gate complete.

`tools/check_wrap_undo.py` currently validates IDs and prints hashes; it
does **not** compare those hashes against an expected manifest. With
`--report` it ignores reference/candidate assertion booleans, summary
matches/accepted, provenance and scenario hash. It accepts a report with
27 results all `match: true`, both harness statuses 0, but **zero reported
matches, failed checks, wrong reference, wrong binary and wrong scenarios**.
The review ran this experiment; it printed `OK: report 0/27 matches` and
exited 0. CI currently calls only the manifest check, not hard-wrap replay.

Fix `scenario_hashes`/`main` in that file; add meaningful negative checker
tests. Require exact result membership, all match/accepted/check flags true,
no differences or declared deviations for this suite, consistent summary
counts, both harness statuses 0, pinned reference identity and expected
candidate/source provenance. Bind report scenario bytes/hash to the actual
scenario input. If expected hashes are maintained separately, change them
only after intentional scenario review and replay. Reject missing/malformed
fields, extra IDs, wrong types, stale reports and tampered scenario inputs.
Do not merely trust another self-reported boolean or printed digest.

Recreate the demonstrated false acceptance without changing source (use a
fresh `NARO_REVIEW_DIR` as in the scenario workflow below):

```sh
python3 - <<'PY'
import json, os
from pathlib import Path
r=json.loads(Path('validation/wrap-undo/coverage.json').read_text())
r['summary']={'recorded':27,'matches':0,'accepted':0}
r['reference_commit']='wrong-reference'
r['candidate_sha256']='wrong-binary'
r['scenario_sha256']='wrong-scenarios'
for v in r['results'].values():
    v.update(reference_checks=False, candidate_checks=False, accepted=False)
Path(os.environ['NARO_REVIEW_DIR'],'invalid-report.json').write_text(json.dumps(r))
PY
python3 tools/check_wrap_undo.py --report "$NARO_REVIEW_DIR/invalid-report.json"
```

Current result is exit 0. The corrected checker must reject this report with
nonzero status, while accepting a complete real report bound to the frozen
candidate and current scenarios.

Keep `spec/tools/audit_spec.py` structurally distinct from replay: it scans
citations and evidence paths, not actual behavior. Its expanded ID regex
captures suffixes but the inventory still contains range endpoints and
nonexistent unsuffixed identifiers such as `TEST-NEXT-UNDO-WRAP-001`.
Expand explicit case inventories or resolve citations to real scenario IDs;
add fixture tests around the new regex and range semantics. A clean audit
does not establish runtime coverage. The session ran
`build_inventories.py`; that was regeneration, not an inventory unit-test run.

## Remaining default-profile defects: P2, required before parity closure

These are now runtime reproduced, not merely source predictions.

| Defect | Reproducer and expected result | Implementation direction |
|---|---|---|
| Missing quote prefix | `REVIEW-QUOTE`: `b'> aaa bbb ccc ddd\n'`, End, type X, undo, redo, save with `-I -b -r 12`. Reference `b'> aaa bbb \n> ccc dddX\n'`, NARO drops second `> ` and cursor is x=8 instead of x=10. | `Editor::hard_wrap` uses only `e.indent`. Use quote regex + following indentation like `para_lead`; copy quote lead even with autoindent off; suspend automatic indentation during quote split; handle equal/mismatching next prefixes and undo grouping. Default quotestr already recognizes `>`, so this is not an exotic custom option. |
| Nonpositive fill uses edit width | At 80 columns, `-I -b -l -r 0`, fixture `('aaaa '*15 + 'bb\n')`, End, X: reference keeps the entire line; NARO wraps before bbX. With `-r -8`, fixture `('aaaa '*13 + 'aa bb ccc\n')`: reference second line `cccX`; NARO `bb cccX`. Removing `-l` from the negative-fill case gives an exact-match control. | At `hard_wrap` lines 422–427 use terminal `layout.cols + fill`, saturated at zero, rather than `layout.width + fill`. Keep positive fill semantics unchanged. Cover indicators, line-number digit growth, narrow sizes and resize. |
| Wrong continuation autoindent | `REVIEW-CONT-INDENT`: `b'    aaa bbb ccc\n  zzz\n'`, `-I -b -i -r 12`, End, X, undo/redo/save. Reference `b'    aaa bbb \n  cccX\n  zzz\n'`; NARO inserts four spaces before cccX instead of two. | `hard_wrap` always copies current indent. Nano `do_enter` samples next line if it is in the same paragraph and not a paragraph start. Reuse/align `in_para` and `para_start` rules, including differing quote prefixes; audit ordinary `Buffer::enter` too. |

Quote and continuation fixes overlap paragraph-lead logic; coordinate them
after agreeing on those rules. Geometry is independent of identity/mark
mapping but needs combined tests after integration.

## Repair misleading branch coverage

Keep existing passing observations; add decisive controls or repair inputs
with reference evidence. Do not label a new scenario as covering a branch
until the reference snapshots, actual byte offsets and fill calculation
demonstrate that branch was reached.

| Existing case | Actual gap and required test |
|---|---|
| 007-INSERT | Types on the newly blank first line (` eeee`), with no second wrap. Return to the actual moved predecessor and overflow, exceed fill and require an accepted join. |
| 008-DELETE | Deletes one character from `cccc dddd`, not a node; final `eeee fff` does not wrap. Separate in-place survival control from genuine target-node removal and unrelated-successor rejection. |
| 012-AUTOSpill | `    cccc ddd` is 12 columns; remainder makes join exceed fill 14. Shorten target/remainder so equal-prefix removal actually executes. |
| 013-MISMATCH | Initial `  aaa bbb c` is only ten columns; appending d still has no live target. First create a real target, change its/current prefix to unequal nonempty prefixes without deleting target, then use a fill-accepted join. |
| 014-EMPTY | Target is `cccc`, not empty or one character. Test a live target reduced to length zero by in-place deletions; prove node survives and test join/undo/redo. Add actual one-character target control. |
| 015-TABS | Tab typed interactively expands to spaces; autoindent is off. Load literal 0x09 from fixture, preserve it on a live target, choose sufficient fill, and prove matching-tab-prefix stripping. |
| 017-WSTRAIL | The second remainder is `eee`; it has no trailing blank. Put blank(s) at the end of the remainder actually joined; assert no extra added space. |
| 005/009/010 redo continuation | Their ` fff ggg` addition exceeds fill with `eee ddd`, so it cannot independently prove marker clearing. Shorten it as for 020; keep 025 as the already decisive ordinary-redo case. |

Case 022 now has NUL before the split, but the actual fixture is
`aaab\0bbb cccc` (NUL byte offset 4), not its note's `aaa\0bbb`/offset 3.
Correct the description or deliberately change and replay the fixture.
The existing `spillage_join_preserves_embedded_nul` Rust unit test manually
calls the decoder; it does not call production `hard_wrap`. Keep production
case 027 and its mutation evidence as the real join-path protection.

## Recreate this review's focused scenarios

The actual recordings, scripts/JSON and comparisons are currently under
`/tmp/naro-review-20261028/` (temporary, do not commit). The following
standalone generator reconstructs the decisive inputs if that directory is
gone. Run from the repo, choose a fresh output directory, and write only
synthetic fixtures. Add these cases to permanent scenarios with proper
`TEST-...` IDs and explicit expected saved-byte/cursor/selection assertions
before fixing source.

```sh
review_dir=$(mktemp -d /tmp/naro-hw-next.XXXXXX)
export NARO_REVIEW_DIR="$review_dir"
python3 - <<'PY'
import json, os
from pathlib import Path
out = Path(os.environ['NARO_REVIEW_DIR'])
def k(*keys): return {'keys': list(keys)}
def s(name): return {'snapshot': name, 'quiet': 100}
tail = [k('^O'), {'sleep':100}, k('Enter'), s('saved'),
        {'capture_file':'work/f.txt'}, k('^X'), {'wait_exit':5}]
def case(name, raw, steps, args=None):
    return {'id':name, 'args':args or ['-I','-b','-r','12','f.txt'],
            'files':{'work/f.txt':{'hex':raw.hex()}},
            'steps':[{'settle':200}]+steps+tail,
            'expect':{'exit_status':0,'temp_empty':True}}
def history_steps():
    return [k('End'), {'text':'X'}, s('wrap'), k('M-U'), s('undo'),
            k('M-E'), s('redo')]
first = [k('Down'), {'text':'aaa bbb ccc ddd'}, s('first-wrap')]
probe = [k('Up'), k('End'), {'text':' eee'}, s('probe-wrap')]
raw = b'aaa bbb ccc\n\nTAIL\n'
cases = [case('REVIEW-MARK', b'\n', [
    {'text':'aaa bbb ccc ddd'}, k('Home'), k('Right'), k('M-A'),
    k('Up'), k('End'), {'text':' eee'}, s('joined-mark'),
    k('^K'), s('cut-mark')])]
for name, join in [('DEL',[k('Del')]),
                   ('BSP',[k('Down'),k('Home'),k('Bsp')])]:
    cases.append(case('REVIEW-EMPTY-'+name, raw,
        first+[k('Up'),k('Home'),k(*(['Del']*12)),s('empty')]+
        join+[s('joined')]+probe))
cases.append(case('REVIEW-PARTIAL-CUT', raw, first+[
    k('Up'),k('Home'),k('M-A'),k('Down'),k('Home'),k('Right'),
    s('marked'),k('^K'),s('cut')]+probe))
cases.append(case('REVIEW-QUOTE', b'> aaa bbb ccc ddd\n', history_steps()))
cases.append(case('REVIEW-CONT-INDENT', b'    aaa bbb ccc\n  zzz\n',
    history_steps(), ['-I','-b','-i','-r','12','f.txt']))
cases.append(case('REVIEW-FILL-ZERO', ('aaaa '*15+'bb\n').encode(),
    history_steps(), ['-I','-b','-l','-r','0','f.txt']))
for label, nums in [('NUMBERS',True),('CONTROL',False)]:
    args=['-I','-b']+(['-l'] if nums else [])+['-r','-8','f.txt']
    cases.append(case('REVIEW-FILL-NEG-'+label,
        ('aaaa '*13+'aa bb ccc\n').encode(), history_steps(), args))
(out/'scenarios.json').write_text(json.dumps(cases,indent=2)+'\n')
PY
```

Before editing, run these on reference and candidate; both harnesses may
print PASS because initial expectations assert only exit/safety. **Compare
the recordings**; a per-side harness PASS is not differential parity:

```sh
/home/john/.cargo/bin/cargo build --release --target-dir "$review_dir/build"
NARO_BUILD_INFO=1 "$review_dir/build/release/naro"
NANOSPEC_WORK="$review_dir/work-ref" python3 spec/tools/nanoharness.py \
  "$review_dir/scenarios.json" --binary /home/john/src/nano-install/default/bin/nano \
  --out "$review_dir/ref"
NANOSPEC_WORK="$review_dir/work-cand" python3 spec/tools/nanoharness.py \
  "$review_dir/scenarios.json" --binary "$review_dir/build/release/naro" \
  --out "$review_dir/cand"
PYTHONPATH=spec/tools python3 - <<'PY'
import json, os
from pathlib import Path
from compare_runs import compare
p=Path(os.environ['NARO_REVIEW_DIR'])
for sc in json.loads((p/'scenarios.json').read_text()):
    tid=sc['id']
    r=json.loads((p/'ref'/tid/'result.json').read_text())
    c=json.loads((p/'cand'/tid/'result.json').read_text())
    d=compare(r,c)
    print(tid, 'MATCH' if not d else [x['field'] for x in d])
PY
```

Expected before fixes: eight mismatches, one no-margin negative-fill control
match. Test the actual logical bytes, including trailing spaces and payload
NULs, by decoding `captured_files` base64. The earlier exported session once
mistook base64/hex representations; do not infer bytes from screen text.

## Verification sequence and dependencies

1. Preserve state, verify pinned reference, add failing tests for mark and
   operation-specific identity, and fix those paths. They touch shared buffer
   logic; agree on the primitives before integrating both changes.
2. Independently repair the checker and branch scenarios; geometry can also
   proceed independently. Quote and continuation fixes share lead/paragraph
   logic. Independent work does not authorize overlapping harness fixture roots.
3. After each fix, run its decisive cases and the existing 27-case suite.
   Keep group-close behavior, 020/024 structural history, 025 ordinary redo,
   026 whole-line cut and 027 production NUL join passing. Add save/Modified,
   no-op redo and divergent-edit assertions where absent.
4. After integrating source fixes, freeze one default binary and verify all
   acceptance suites against that same hash. Build tiny in a separate target
   directory; the exported session accidentally tested a tiny binary after
   overwriting the default binary in a shared target directory.

Commands (use `/home/john/.cargo/bin/cargo`; plain cargo is absent from this
review shell's PATH):

```sh
git -C /home/john/src/nano-ref rev-parse HEAD
git -C /home/john/src/nano-ref status --short
sha256sum /home/john/src/nano-install/default/bin/nano
/home/john/.cargo/bin/cargo fmt --check
/home/john/.cargo/bin/cargo clippy --all-targets -- -D warnings
/home/john/.cargo/bin/cargo clippy --all-targets --all-features -- -D warnings
/home/john/.cargo/bin/cargo test --release
/home/john/.cargo/bin/cargo test --release --features tiny
/home/john/.cargo/bin/cargo test --all-features
PYTHONPATH=spec/tools python3 -m unittest test_compare_runs test_nanoharness test_namespace_exec
python3 spec/tools/test_inventory.py
python3 spec/tools/audit_spec.py
python3 tools/check_wrap_undo.py
```

All-features includes tiny, so it does not substitute for default wrap tests.
Add the new checker/audit regression-test command when implementing those tests.

For one frozen default binary (replace the output name with a fresh unique
one for every command and use distinct work roots):

```sh
NANOSPEC_WORK=/tmp/naro-next-wrap-work python3 tools/check_follow_up.py \
  --suite wrap-undo --binary target/next-default/release/naro --out target/next-wrap
python3 tools/check_wrap_undo.py --report target/next-wrap/report.json
NANOSPEC_WORK=/tmp/naro-next-edges-work python3 tools/check_follow_up.py \
  --suite edges --binary target/next-default/release/naro --out target/next-edges
NANOSPEC_WORK=/tmp/naro-next-tools-work python3 tools/check_follow_up.py \
  --suite tools --binary target/next-default/release/naro --out target/next-tools
NANOSPEC_WORK=/tmp/naro-next-supp-work python3 tools/check_follow_up.py \
  --suite supplement --binary target/next-default/release/naro --out target/next-supp
NANOSPEC_WORK=/tmp/naro-next-full-work python3 tools/validate_parallel.py \
  --binary target/next-default/release/naro --out target/next-full --jobs 4
```

First build `target/next-default` with `cargo build --release --target-dir
target/next-default`. Preserve finder/NUL focused suites if still useful, but
make decisive cases permanent in the integrated suite. The baseline should
retain 303 recorded, 301 full matches, 302 file/exit matches, six explicitly
excluded cases and four worker statuses 0, unless legitimate inventory
changes are separately explained. Only existing declared safety differences
`TEST-CLI-057` and `TEST-PROMPT-NUL-001` are allowed; no new unreviewed deviations.
Run the optional tiny CI/size gate after changing unconditional generation
storage; tiny intentionally omits undo/redo and hard wrap but shares Buffer.

## Acceptance criteria

- Every reproduced mismatch above has a failing-before/passing-after oracle
  comparison and a decisive permanent regression; all required formerly
  ineffective branches actually execute. Full quote-prefix, fill geometry,
  continuation indent and mark behavior are covered, not silently scoped away.
- No stale target, resurrection, retargeting or unnecessary clearing of a
  surviving target across edits, cut/paste, undo/redo and unrelated operations.
- Bytes, selection attributes, cursor, screen, terminal modes, saved/Modified
  state, exit status and payload NULs agree with the pinned reference through
  continued editing and history. Undo/redo clears explicit marks as nano does.
- The checker rejects incomplete/stale/tampered reports and scenarios; CI
  detects lost cases and the behavior has durable replay coverage.
- Default/tiny Rust checks and focused/full comparisons pass on the final
  source; feature flags, source fingerprint, scenario serialization hashes,
  executable hashes and actual child statuses are recorded accurately.
- Q-UNDO-002 and EDIT-015 coverage remain partial until these gates pass.
  Update stale 001–023 citations, misleading case descriptions and overbroad
  claims in spec/validation docs; regenerate audit inventory intentionally.
- Preserve original and failed runs, complete logs and checksums outside the
  commit. Keep compact, curated evidence/provenance only if appropriate.

Do not change expected output merely to match NARO, loosen comparator
normalization, invent a deviation, remove a failing case, or update a digest
simply to make a gate green. Establish GNU nano's behavior first; change an
expectation only when reference evidence proves the expectation was wrong,
and document the correction.

## Commit and GitHub instructions

The current review deliberately made **no commit and no push** because saved
bytes still differ and tests/gates are incomplete. Once fixes and acceptance
are complete, inspect `git diff --check`, the full staged diff and the exact
staged file list. Stage explicit source/spec/tool/scenario/review paths.
Never use `git add .` or stage `opencode-*.json`, temporary files, credentials,
`target/`, binaries, raw terminal output, complete result trees or the
untracked `validation/wrap-undo/archive/` test artifacts. Some archives embed
pre-review source patches and stale metadata; they are local evidence, not
the implementation to stage.

Fetch/check live `origin/main` before committing/pushing; stop and reconcile
if it advanced. Use a descriptive commit that states actual fixed behavior
and validation, push normally to the existing `main` branch only when ready,
and report the commit hash and branch. Never force-push or rewrite history.
Preserve an intentionally incomplete checkpoint only with an accurate scope;
do not present it as completed parity.
