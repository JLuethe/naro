#!/usr/bin/env python3
"""Reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c: reproducible structural audit."""
import csv
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '6ed285c3ec7a1d228def4d4e7021c6ba269f620c'

def main():
    problems, warnings, requirements = [], [], []
    docs = sorted(ROOT.glob('[0-9][0-9]-*.md'))
    expected = [f'{n:02d}' for n in range(19)] + ['97', '98', '99']
    for prefix in expected:
        if not list(ROOT.glob(prefix + '-*.md')):
            problems.append('missing document prefix ' + prefix)
    for p in docs + [ROOT / 'data/README.md']:
        text = p.read_text()
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
                tests = sorted(set(re.findall(r'TEST-[A-Z0-9-]+-\d{3}', block)))
                requirements.append([m[1], p.name, m[2], ' '.join(tests)])
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
    source = Path.home() / 'src/nano-ref'
    if source.exists():
        head = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
        dirty = subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True)
        if head != COMMIT or dirty:
            problems.append('reference worktree changed')
    else:
        warnings.append('reference worktree absent; integrity check skipped')
    with (ROOT / 'data/requirements.csv').open('w', newline='') as f:
        w = csv.writer(f); w.writerow(['requirement', 'document', 'title', 'explicit_test_ids']); w.writerows(requirements)
    report = dict(reference_commit=COMMIT, documents=len(docs), requirements=len(requirements),
                  scenarios=len(ids), recorded=recorded, explicit_assertions=checks,
                  intentional_sigkill=killed, suites=suites, warnings=warnings, problems=problems)
    (ROOT / 'evidence/audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return bool(problems)

if __name__ == '__main__':
    raise SystemExit(main())
