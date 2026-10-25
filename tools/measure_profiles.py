#!/usr/bin/env python3
"""Measure equal-setting full/tiny builds using copies in a harness fixture."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'spec/tools'))
import nanoharness as h

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--full', type=Path, required=True)
p.add_argument('--tiny', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
fixture = Path(h.WORKROOT) / ('TEST-TINY-SIZE-' + uuid.uuid4().hex[:12]) / 'fx'
h.make_fixture(str(fixture), {})
report = {'reference_commit': h.REFERENCE_COMMIT, 'profiles': {}, 'checks': {}}
for name, source in [('full', a.full), ('tiny', a.tiny)]:
    binary = fixture / 'work' / name
    binary.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, binary)
    build = json.loads(subprocess.check_output([str(binary)], env={**os.environ, 'NARO_BUILD_INFO':'1'}, text=True))
    dynamic = subprocess.check_output(['readelf', '-d', str(binary)], text=True)
    original = binary.read_bytes()
    subprocess.run(['strip', '--strip-all', str(binary)], check=True)
    report['profiles'][name] = {'build': build, 'bytes': len(original),
        'sha256': hashlib.sha256(original).hexdigest(), 'stripped_bytes': binary.stat().st_size,
        'stripped_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
        'needed': re.findall(r'\(NEEDED\).*?\[(.*?)\]', dynamic)}
full, tiny = report['profiles']['full'], report['profiles']['tiny']
deps = subprocess.check_output(['cc', '-DNARO_TINY', '-D_DEFAULT_SOURCE', '-D_XOPEN_SOURCE=700',
    '-M', 'native/bridge.c'], cwd=ROOT, text=True)
report['tiny_native_dependencies'] = deps
report['checks'] = {
    'same_source': full['build']['source_sha256'] == tiny['build']['source_sha256'],
    'same_compiler': full['build']['rustc'] == tiny['build']['rustc'],
    'full_features': full['build']['features'] == '',
    'tiny_features': tiny['build']['features'] == 'tiny',
    'tiny_smaller': tiny['stripped_bytes'] < full['stripped_bytes'],
    'full_magic': 'libmagic.so.1' in full['needed'],
    'tiny_no_magic': not any('magic' in lib for lib in tiny['needed']),
    'tiny_no_magic_header': not re.search(r'\bmagic\.h\b', deps),
}
report['reduction_percent'] = round(100 * (1 - tiny['stripped_bytes'] / full['stripped_bytes']), 2)
(a.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'stripped_full': full['stripped_bytes'], 'stripped_tiny': tiny['stripped_bytes'],
                  'reduction_percent': report['reduction_percent'], 'checks': report['checks']}))
raise SystemExit(int(not all(report['checks'].values())))
