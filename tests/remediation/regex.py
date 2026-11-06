#!/usr/bin/env python3
"""Fresh libc oracle and exact NARO regex wrapper in both specified locales."""
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
from environment import snapshot


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binary', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    a.out = a.out.absolute()
    a.out.mkdir(parents=True, exist_ok=False)
    candidate = a.out / 'candidate.bin'
    source = a.out / 'regex_probe.c'
    reference = a.out / 'reference.bin'
    shutil.copy2(a.binary.resolve(strict=True), candidate)
    shutil.copy2(ROOT / 'spec/tools/regex/regex_probe.c', source)
    with (a.out / 'compile.log').open('w') as log:
        subprocess.run(['cc', '-std=c11', '-D_GNU_SOURCE', '-O2', str(source), '-o', str(reference)], stdout=log, stderr=log, check=True, timeout=60)
    hashes = {'reference': sha(reference), 'candidate': sha(candidate)}
    corpus = (ROOT / 'spec/evidence/regex/cases.tsv').read_text()
    expected_count = sum(bool(line) and not line.startswith('#') for line in corpus.splitlines())
    if expected_count != 81:
        raise ValueError('regex corpus changed; review expected membership')
    report = {'binary_sha256': hashes, 'environment': snapshot(), 'reference_source_sha256': sha(source), 'corpus_sha256': hashlib.sha256(corpus.encode()).hexdigest(), 'expected_cases_per_locale': expected_count, 'locales': {}}
    report['build'] = json.loads(subprocess.check_output([str(candidate)], env={**os.environ, 'NARO_BUILD_INFO': '1'}, text=True))
    scratch = tempfile.mkdtemp(prefix='nanospec-m15-regex-', dir='/tmp')
    tmux, owner = make_private_tmux_tmpdir()
    try:
        for locale in ['C', 'en_US.UTF-8']:
            results, outcomes, outputs = {}, {}, {}
            for side, binary in [('reference', reference), ('candidate', candidate)]:
                tid = 'TEST-M15-REGEX-' + locale.replace('.', '-').replace('_', '-')
                case = {'id': tid, 'lang': locale, 'stdin': corpus, 'stdout_redirect': True, 'hold_tty': True, 'steps': [{'wait_exit': 5}], 'expect': {'exit_status': 0}}
                if side == 'candidate':
                    case['env'] = {'NARO_REGEX_PROBE': '1'}
                scenario = a.out / (locale + '-' + side + '.json')
                scenario.write_text(json.dumps([case]) + '\n')
                out = a.out / locale / side
                env = {**os.environ, 'NANOSPEC_WORK': scratch, 'TMUX_TMPDIR': str(tmux), 'PYTHONDONTWRITEBYTECODE': '1'}
                cmd = [sys.executable, str(ROOT / 'spec/tools/nanoharness.py'), str(scenario), '--binary', str(binary), '--out', str(out)]
                outcomes[side] = run_owned_process(cmd, cwd=ROOT, env=env, log_path=a.out / (locale + '-' + side + '.log'), timeout=30, tmux_tmpdir=tmux)
                result = out / tid / 'result.json'
                results[side] = json.loads(result.read_text()) if result.is_file() else None
                if results[side] is not None:
                    rows = [json.loads(line) for line in results[side]['stdout'].splitlines()]
                    for row in rows:
                        # Existing regex contract compares compile success and exact
                        # diagnostics, not libc-specific numeric regcomp error codes.
                        row['compile'] = bool(row['compile'])
                    outputs[side] = rows
            complete = all(results[k] is not None and outcomes[k]['status'] == 0 and results[k].get('binary_sha256') == hashes[k] and results[k].get('steps_ok') and all(c.get('pass') is True for c in results[k].get('checks', [])) and len(outputs.get(k, [])) == expected_count for k in hashes)
            differences = [{'case': i + 1, 'reference': r, 'candidate': c} for i, (r, c) in enumerate(zip(outputs.get('reference', []), outputs.get('candidate', []))) if r != c]
            report['locales'][locale] = {'runs': outcomes, 'complete': complete, 'cases': {k: len(v) for k, v in outputs.items()}, 'differences': differences, 'passed': complete and not differences}
            print(locale, report['locales'][locale]['passed'], flush=True)
    finally:
        remove_private_tmux_tmpdir(tmux, owner)
    report['passed'] = len(report['locales']) == 2 and all(v['passed'] for v in report['locales'].values()) and hashes == {'reference': sha(reference), 'candidate': sha(candidate)}
    (a.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return int(not report['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
