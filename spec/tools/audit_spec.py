#!/usr/bin/env python3
"""Reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c: reproducible structural audit."""
import csv
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '6ed285c3ec7a1d228def4d4e7021c6ba269f620c'
# A test-ID citation. The suffix may carry a case name
# (`TEST-NEXT-UNDO-WRAP-001-MID`).
TEST_ID = re.compile(r'TEST-[A-Z0-9][A-Za-z0-9-]*')


def cited_test_ids(text):
    """Return the test IDs cited in a requirement block.

    A citation that names a family of cases rather than one case is not
    an inventory candidate: a glob (`TEST-CLI-*`) or a path prefix
    (`TEST-NEXT-EDIT/RC`). A compound list of case names
    (`TEST-UNDO-001/-002`) cites `TEST-UNDO-001`. Range endpoints
    (`TEST-UNDO-001…023`) are candidates too: they are resolved against
    the recorded inventory afterwards, because a range may name cases that
    exist (`TEST-CLI-001…007`) or a family whose members carry a case
    name (`TEST-NEXT-UNDO-WRAP-001…027`).
    """
    found = set()
    for match in TEST_ID.finditer(text):
        token = match.group(0)
        rest = text[match.end():]
        if rest.startswith('*'):
            continue
        if rest.startswith('/'):
            tail = rest.lstrip('/-')
            if not tail[:1].isdigit():
                continue
        found.add(token)
    return sorted(found)


def main():
    problems, warnings, requirements = [], [], []
    docs = sorted(ROOT.glob('[0-9][0-9]-*.md'))
    expected = [f'{n:02d}' for n in range(19)] + ['97', '98', '99']
    for prefix in expected:
        if not list(ROOT.glob(prefix + '-*.md')):
            problems.append('missing document prefix ' + prefix)
    follow_up_docs = []
    for p in docs + [ROOT / 'data/README.md']:
        text = p.read_text()
        phase = 'follow-up' if p.name in ('19-completion-and-release.md', '20-root-and-console.md', '21-console-release-closure.md', '22-tiny-profile.md') else 'baseline'
        if phase == 'follow-up' and p in docs:
            follow_up_docs.append(p.name)
        if COMMIT not in '\n'.join(text.splitlines()[:5]):
            problems.append(str(p.relative_to(ROOT)) + ': missing top commit')
        for target in re.findall(r'\]\(([^)]+)\)', text):
            if '://' in target or target.startswith('#'):
                continue
            target = target.split('#')[0].split(':')[0]
            if target and not (p.parent / target).exists():
                problems.append(f'{p.name}: broken link {target}')
        blocks = re.split(r'(?=^### [A-Z][A-Z0-9-]+ —)', text, flags=re.M)
        for block in blocks:
            m = re.match(r'### ([A-Z][A-Z0-9-]+) — ([^\n]+)', block)
            if m:
                tests = cited_test_ids(block)
                requirements.append([m[1], p.name, m[2], ' '.join(tests), phase])
    follow_up_ids = {r[0] for r in requirements if r[4] == 'follow-up'}
    follow_up_tests = []
    matrices = [ROOT / 'data/follow-up-tests.csv', ROOT / 'data/root-console-tests.csv', ROOT / 'data/closure-tests.csv', ROOT / 'data/tiny-tests.csv']
    if any(matrix.exists() for matrix in matrices):
        for matrix in matrices:
            if matrix.exists():
                with matrix.open(newline='') as f:
                    follow_up_tests.extend(csv.DictReader(f))
        seen_tests, covered = set(), set()
        for row in follow_up_tests:
            tid = row['test_id']
            reqs = set(row['requirement_ids'].split(';'))
            if tid in seen_tests or row['reference_commit'] != COMMIT:
                problems.append('follow-up test identity mismatch: ' + tid)
            seen_tests.add(tid)
            covered.update(reqs)
            if not reqs <= follow_up_ids:
                problems.append('unknown follow-up requirement: ' + tid)
            if row['status'] not in ('planned', 'recorded', 'verified', 'blocked', 'deferred'):
                problems.append('invalid follow-up status: ' + tid)
            if row['release_gate'] not in ('required', 'conditional', 'optional'):
                problems.append('invalid follow-up gate: ' + tid)
            if row['status'] in ('recorded', 'verified') and not row['evidence']:
                problems.append('missing follow-up evidence: ' + tid)
            if row['evidence'] and not (ROOT / row['evidence']).exists():
                problems.append('absent follow-up evidence path: ' + tid)
        for req in sorted(follow_up_ids - covered):
            problems.append('follow-up requirement has no test: ' + req)
    elif follow_up_ids:
        problems.append('missing follow-up test matrix')
    ids, recorded, checks, killed = set(), 0, 0, []
    suites = {}
    for p in sorted((ROOT / 'evidence/scenarios').glob('*.json')):
        data = json.loads(p.read_text())
        scenarios = data if isinstance(data, list) else [data]
        suites[p.name] = len(scenarios)
        for s in scenarios:
            tid = s['id']
            if tid in ids:
                problems.append('duplicate scenario ' + tid)
            ids.add(tid)
            result = ROOT / 'evidence/runs' / tid / 'result.json'
            if not result.exists():
                problems.append('missing evidence ' + tid); continue
            r = json.loads(result.read_text()); recorded += 1
            if r.get('reference_commit') != COMMIT or r['scenario'] != tid:
                problems.append('identity mismatch ' + tid)
            checks += len(r['checks'])
            if any(not c['pass'] for c in r['checks']):
                problems.append('failed reference assertion ' + tid)
            if r['exit_signal'] == 9:
                killed.append(tid)
            for note in r['notes']:
                if 'timed out' in note:
                    problems.append(tid + ': ' + note)
    # The follow-up suites live outside the specification tree; their case
    # IDs are recorded cases too and may be cited by a requirement.
    follow_up_scenarios = ROOT.parent / 'tests/follow-up/scenarios'
    if follow_up_scenarios.is_dir():
        for p in sorted(follow_up_scenarios.glob('*.json')):
            data = json.loads(p.read_text())
            for s in (data if isinstance(data, list) else [data]):
                ids.add(s['id'])
    known = set(ids) | {r['test_id'] for r in follow_up_tests}
    # The inventory lists only cases that exist. A citation that names a
    # planned case or a range endpoint of a family is reported as a warning
    # instead of being listed as if it were a recorded scenario.
    unresolved = []
    for requirement in requirements:
        keep = []
        for tid in requirement[3].split():
            if tid in known:
                keep.append(tid)
            else:
                unresolved.append(f'{requirement[0]}: {tid}')
        requirement[3] = ' '.join(keep)
    if unresolved:
        warnings.append('cited test IDs without a recorded scenario: '
                        + ', '.join(sorted(unresolved)))
    source = Path.home() / 'src/nano-ref'
    if source.exists():
        head = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
        dirty = subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True)
        if head != COMMIT or dirty:
            problems.append('reference worktree changed')
    else:
        warnings.append('reference worktree absent; integrity check skipped')
    with (ROOT / 'data/requirements.csv').open('w', newline='') as f:
        w = csv.writer(f); w.writerow(['requirement', 'document', 'title', 'explicit_test_ids', 'phase']); w.writerows(requirements)
    report = dict(reference_commit=COMMIT, documents=len(docs), requirements=len(requirements),
                  baseline_documents=len(docs) - len(follow_up_docs),
                  baseline_requirements=len(requirements) - len(follow_up_ids),
                  follow_up_documents=follow_up_docs, follow_up_requirements=len(follow_up_ids),
                  follow_up_tests=len(follow_up_tests),
                  follow_up_statuses={s: sum(r['status'] == s for r in follow_up_tests)
                                      for s in sorted({r['status'] for r in follow_up_tests})},
                  scenarios=len(ids), recorded=recorded, explicit_assertions=checks,
                  intentional_sigkill=killed, suites=suites, warnings=warnings, problems=problems)
    (ROOT / 'evidence/audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return bool(problems)

if __name__ == '__main__':
    raise SystemExit(main())
