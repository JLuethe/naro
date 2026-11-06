#!/usr/bin/env python3
"""Compile a private signal driver, including an exact consume-window injection.
Use --revision for old-code proof. --out must be a fresh directory.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('--revision')
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=False)
out = args.out.resolve()
root = Path(__file__).resolve().parents[2]
source = subprocess.check_output(['git', 'show', f'{args.revision}:native/bridge.c'], cwd=root).decode() if args.revision else (root/'native/bridge.c').read_text()
original_hash = hashlib.sha256(source.encode()).hexdigest()
old = 'int nr_signal(void) { int s=pending; pending=0; return s; }'
new = '        if(atomic_compare_exchange_weak_explicit(&pending,&snapshot,'
if old in source:
    source = source.replace(old, 'int nr_signal(void) { int s=pending; nr_test_window(); pending=0; return s; }', 1)
    seam = 'after pending snapshot, before stale clear'
else:
    assert source.count(new) == 1
    source = source.replace(new, '        nr_test_window();\n' + new, 1)
    seam = 'after pending snapshot, before compare-and-exchange'
source = 'extern void nr_test_window(void);\n' + source
(out/'bridge.c').write_text(source)
command = ['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-D_DEFAULT_SOURCE', '-D_XOPEN_SOURCE=700', '-I'+str(root/'native'), str(out/'bridge.c'), str(root/'tests/signals/native.c'), '-lncursesw', '-lmagic', '-pthread', '-o', str(out/'native-test')]
subprocess.run(command, check=True)
result = subprocess.run([str(out/'native-test')], capture_output=True, timeout=30)
(out/'native.log').write_bytes(result.stdout+result.stderr)
report = dict(revision=args.revision, original_bridge_sha256=original_hash, injection=seam, command=command, exit_status=result.returncode, output=result.stdout.decode(), binary_sha256=hashlib.sha256((out/'native-test').read_bytes()).hexdigest())
(out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
print(result.stdout.decode(), end='')
raise SystemExit(result.returncode)
