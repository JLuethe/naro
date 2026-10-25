#!/usr/bin/env python3
"""Link tiny qualification reports and reject missing or inconsistent evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
for name in ['terminal', 'cli', 'vt', 'full', 'extras', 'ci', 'measurement', 'quality', 'package', 'full-package']:
    p.add_argument('--' + name, type=Path, required=True, help='Directory containing report.json')
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
report = {'reference_commit': '6ed285c3ec7a1d228def4d4e7021c6ba269f620c',
          'qualification_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
          'reports': {}, 'checks': {}}
reports = {}
for name in ['terminal', 'cli', 'vt', 'full', 'extras', 'ci', 'measurement', 'quality', 'package', 'full_package']:
    path = getattr(a, name) / 'report.json'
    raw = path.read_bytes()
    reports[name] = json.loads(raw)
    report['reports'][name] = {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()}

def check(name, ok):
    report['checks'][name] = bool(ok)
    print(name, 'PASS' if ok else 'FAIL')

m = reports['measurement']
tiny, full = m['profiles']['tiny'], m['profiles']['full']
report['profiles'] = m['profiles']
check('measurement', all(m['checks'].values()) and len(m['checks']) == 8)
inputs = sorted([p for d in ['src', 'native', 'assets'] for p in (ROOT/d).rglob('*') if p.is_file()]
                + [ROOT/n for n in ['Cargo.toml', 'Cargo.lock', 'build.rs', 'CREDITS.md']])
sums = subprocess.check_output(['sha256sum', *[str(p.relative_to(ROOT)) for p in inputs]], cwd=ROOT)
check('current-source', hashlib.sha256(sums).hexdigest() == tiny['build']['source_sha256'] == full['build']['source_sha256'])
references = set()
for name, count in [('terminal', 59), ('cli', 125), ('vt', 8)]:
    r = reports[name]
    references.add(r['reference_sha256'])
    check(name + '-identity', r['reference_commit'] == report['reference_commit']
          and r['candidate_sha256'] == tiny['sha256'] and r['candidate_build'] == tiny['build'])
    check(name + '-complete', len(r['results']) == count and r['summary']['matches'] == count
          and r['reference_status'] == r['candidate_status'] == 0)
    check(name + '-exact', all(v['match'] and not v['differences'] and v['reference_checks'] and v['candidate_checks']
                             for v in r['results'].values()))
check('same-tiny-oracle', len(references) == 1)
report['tiny_reference_sha256'] = sorted(references)
r = reports['full']
check('full-binary', r['binary_sha256'] == full['sha256'])
check('full-corpus', r['summary'] == {'recorded':303, 'full_matches':301, 'files_matches':302, 'skipped':6}
      and all(s == 0 for s in r['worker_statuses']))
check('full-only-declared-differences', {k for k,v in r['results'].items() if not v['full_match']}
      == {'TEST-CLI-057', 'TEST-PROMPT-NUL-001'})
r = reports['extras']
check('extras-binary', r['candidate_sha256'] == full['sha256'])
check('full-cli', len(r['cli']) == 38 and all(v['pass'] for v in r['cli'].values()))
check('full-regex', sum(v['cases'] for v in r['regex'].values()) == 162 and all(v['pass'] for v in r['regex'].values()))
check('full-safety', len(r['safety']) == 2 and all(v['pass'] for v in r['safety'].values()))
r = reports['ci']
check('tiny-assertion-binary', r['binary_sha256'] == tiny['sha256'] and r['build'] == tiny['build'])
check('tiny-ci-checks', len(r['checks']) == 6 and all(r['checks'].values()))
check('tiny-assertions', sum(len(v['results']) for v in r['suites'].values()) == 194
      and all(v['status'] == 0 and all(s['pass'] for s in v['results'].values()) for v in r['suites'].values()))
check('quality', len(reports['quality']['checks']) == 10 and all(v['status'] == 0 for v in reports['quality']['checks']))
for name, profile in [('package', tiny), ('full_package', full)]:
    r = reports[name]
    check(name + '-identity', r['binary_sha256'] == profile['sha256'])
    check(name + '-checks', len(r['checks']) == 15 and all(v['pass'] for v in r['checks']))

# Assert terminal-mode ownership on both sides of every terminal recording.
for kind in ['reference', 'candidate']:
    records = [json.loads(path.read_text()) for path in (a.terminal/kind).glob('*/result.json')]
    check(kind + '-no-bracketed-paste', len(records) == 59 and all(not r['bracketed_paste_set'] and not r['bracketed_paste_reset'] for r in records))
    modes = [r for r in records if r['scenario'].startswith('TEST-TINY-TERM-')]
    check(kind + '-restoration', len(modes) == 3 and all(json.loads(r['fixture']['home/terminal.json']['text']) == {'restored':True} for r in modes))
report['summary'] = {'checks':len(report['checks']), 'passed':sum(report['checks'].values()),
                     'tiny_exact':192, 'default_exact':301, 'default_cases':303}
(a.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
raise SystemExit(int(not all(report['checks'].values())))
