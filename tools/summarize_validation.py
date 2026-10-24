#!/usr/bin/env python3
"""Publish compact validation evidence; raw candidate recordings stay local."""
import argparse
import json
from pathlib import Path
import platform
import subprocess

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('terminal', type=Path, help='completed validate.py output directory')
args = p.parse_args()
out = ROOT / 'validation'
out.mkdir(exist_ok=True)


def save(name, value):
    (out / name).write_text(json.dumps(value, indent=2) + '\n')


report = json.loads((args.terminal / 'report.json').read_text())
binary_hash = report['binary_sha256']
for result in report['results'].values():
    result['difference_fields'] = [d['field'] for d in result.pop('differences')]
save('terminal.json', report)
for name in ('cli', 'regex'):
    value = json.loads((ROOT / f'spec/evidence/naro-{name}/report.json').read_text())
    if value['binary_sha256'] != binary_hash:
        raise SystemExit(f'{name} report is for a different binary; rerun it')
    save(name + '.json', value)

safety = {}
for path in sorted((ROOT / 'spec/evidence/naro-safety').glob('TEST-*/result.json')):
    result = json.loads(path.read_text())
    if result.get('binary_sha256') != binary_hash:
        raise SystemExit('safety report is for a different binary; rerun it')
    safety[path.parent.name] = {k: result.get(k) for k in
                               ('exit_status', 'exit_signal', 'steps_ok', 'checks')}
    if not result.get('steps_ok') or not all(c['pass'] for c in result['checks']):
        raise SystemExit('safety assertion failed: ' + path.parent.name)
if len(safety) != 2:
    raise SystemExit('expected two safety scenarios')
save('safety.json', {'binary_sha256': binary_hash, 'results': safety})

def version(command):
    return subprocess.check_output(command, text=True).strip()


save('environment.json', {
    'reference_commit': report['reference_commit'],
    'binary_sha256': binary_hash,
    'source_revision': version(['git', '-C', str(ROOT), 'rev-parse', 'HEAD']),
    'system': platform.platform(),
    'rustc': version([str(Path.home() / '.cargo/bin/rustc'), '--version']),
    'cargo': version([str(Path.home() / '.cargo/bin/cargo'), '--version']),
    'tmux': version(['tmux', '-V']),
    'python': platform.python_version(),
    'terminal_report': str(args.terminal),
})
print(json.dumps(report['summary']))
