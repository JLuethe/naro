#!/usr/bin/env python3
"""Execute the explicit issue-3 terminal expectations on one exact artifact."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from frozen_process import make_private_tmux_tmpdir, remove_private_tmux_tmpdir, run_owned_process


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binary', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    a.out = a.out.absolute()
    a.out.mkdir(parents=True, exist_ok=False)
    binary = a.out / 'candidate.bin'
    shutil.copy2(a.binary.resolve(strict=True), binary)
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    build = json.loads(subprocess.check_output([str(binary)], env={**os.environ, 'NARO_BUILD_INFO': '1'}, text=True))
    if build['features']:
        raise ValueError('these full-feature progress expectations require default profile')
    report = {'binary_sha256': digest, 'build': build, 'suites': {}, 'policy': 'docs/safe-save.md', 'generator_sha256': hashlib.sha256((ROOT / 'tests/safe-save/progress_cases.py').read_bytes()).hexdigest()}
    scratch = tempfile.mkdtemp(prefix='nanospec-m15-sem-', dir='/tmp')
    tmux, owner = make_private_tmux_tmpdir()
    try:
        for suite in ['save-progress', 'save-safety']:
            scenarios = json.loads(subprocess.check_output([sys.executable, str(ROOT / 'tests/safe-save/progress_cases.py'), suite], text=True))
            path = a.out / (suite + '.json')
            path.write_text(json.dumps(scenarios, indent=2) + '\n')
            env = {**os.environ, 'NANOSPEC_WORK': scratch, 'TMUX_TMPDIR': str(tmux), 'PYTHONDONTWRITEBYTECODE': '1'}
            command = [sys.executable, str(ROOT / 'spec/tools/nanoharness.py'), str(path), '--binary', str(binary), '--out', str(a.out / suite)]
            outcome = run_owned_process(command, cwd=ROOT, env=env, log_path=a.out / (suite + '.log'), timeout=1200, tmux_tmpdir=tmux)
            results = {}
            for case in scenarios:
                result_file = a.out / suite / case['id'] / 'result.json'
                if not result_file.is_file():
                    results[case['id']] = {'passed': False, 'classification': 'missing_evidence'}
                    continue
                r = json.loads(result_file.read_text())
                passed = r.get('binary_sha256') == digest and r.get('steps_ok') and bool(r.get('checks')) and all(c.get('pass') is True for c in r['checks'])
                results[case['id']] = {'passed': bool(passed), 'steps_ok': r.get('steps_ok'), 'assertions': len(r.get('checks', [])), 'failed_checks': [c for c in r.get('checks', []) if not c.get('pass')]}
            report['suites'][suite] = {'run': outcome, 'results': results, 'expected': len(scenarios)}
            print(suite, sum(r['passed'] for r in results.values()), '/', len(scenarios), flush=True)
            (a.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    finally:
        remove_private_tmux_tmpdir(tmux, owner)
    report['passed'] = hashlib.sha256(binary.read_bytes()).hexdigest() == digest and len(report['suites']) == 2 and all(s['run']['status'] == 0 and len(s['results']) == s['expected'] and all(r['passed'] for r in s['results'].values()) for s in report['suites'].values())
    (a.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return int(not report['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
