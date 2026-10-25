#!/usr/bin/env python3
"""Check tiny against pinned assertions without requiring a GNU nano build.

Fresh paired qualification still uses check_follow_up.py with the tiny oracle.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--binary', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
binary = a.binary.resolve()
build = json.loads(subprocess.check_output([str(binary)], env={**os.environ, 'NARO_BUILD_INFO':'1'}, text=True))
dynamic = subprocess.check_output(['readelf', '-d', str(binary)], text=True)
report = {'build': build, 'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(), 'checks': {
    'tiny_feature': 'tiny' in build['features'].split(','), 'no_libmagic': 'libmagic' not in dynamic}, 'suites': {}}
oracle = json.loads((ROOT / 'tests/follow-up/tiny-cli-oracle.json').read_text())
for suite in ['tiny', 'tiny-cli', 'tiny-vt', 'tiny-safety']:
    scenarios = ROOT / 'tests/follow-up/scenarios' / (suite + '.json')
    cases = json.loads(scenarios.read_text())
    out = a.out / suite
    with (a.out / (suite + '.log')).open('w') as log:
        status = subprocess.run([sys.executable, str(ROOT / 'spec/tools/nanoharness.py'), str(scenarios),
            '--binary', str(binary), '--out', str(out.resolve())], stdout=log, stderr=log).returncode
    results = {}
    for case in cases:
        tid = case['id']
        path = out / tid / 'result.json'
        if not path.exists():
            results[tid] = {'pass': False, 'error': 'missing recording'}
            continue
        r = json.loads(path.read_text())
        ok = r['steps_ok'] and all(c['pass'] for c in r['checks'])
        if suite == 'tiny-cli':
            ok &= all(r.get(k) == v for k, v in oracle['results'][tid].items())
        # Tiny must neither enable nor disable a bracketed-paste mode it does
        # not own. Raw escape-input fixtures are included in this assertion.
        ok &= not r.get('bracketed_paste_set') and not r.get('bracketed_paste_reset')
        results[tid] = {'pass': bool(ok), 'assertions': len(r['checks']), 'scenario_sha256': r['scenario_sha256']}
    report['suites'][suite] = {'status': status, 'results': results}
    report['checks'][suite] = status == 0 and all(r['pass'] for r in results.values())
    print(suite, sum(r['pass'] for r in results.values()), '/', len(cases), flush=True)
(a.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
raise SystemExit(int(not all(report['checks'].values())))
