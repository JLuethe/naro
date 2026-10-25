#!/usr/bin/env python3
"""Exercise actual installed gettext and syntax through private harness fixtures."""
import argparse
import gettext
import hashlib
import json
import os
from pathlib import Path
import sys
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'spec/tools'))
import nanoharness as h

p = argparse.ArgumentParser()
p.add_argument('--prefix', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
binary = a.prefix / 'bin/naro'
build = json.loads(subprocess.check_output([str(binary.resolve())], env={**os.environ, 'NARO_BUILD_INFO':'1'}, text=True))
tiny = 'tiny' in build['features'].split(',')
results = {}
for catalog in sorted((a.prefix / 'share/naro/locale').glob('*/LC_MESSAGES/nano.mo')):
    with catalog.open('rb') as stream:
        translation = gettext.GNUTranslations(stream)
    pairs = [(key, value) for key, value in translation._catalog.items()
             if isinstance(key, str) and key and isinstance(value, str) and value != key]
    if not pairs:
        raise SystemExit('catalog has no translated messages: ' + str(catalog))
    message, expected = min(pairs, key=lambda pair: len(pair[0]))
    language = catalog.parent.parent.name
    tid = 'TEST-NEXT-CATALOG-' + language
    scenario = dict(id=tid, args=[], lang='en_US.UTF-8',
                    env={'LANGUAGE': language, 'NARO_TRANSLATION_PROBE': message},
                    stdin='', stdout_redirect=True, hold_tty=True,
                    steps=[{'wait_exit': 5}], expect={'exit_status': 0, 'stdout_contains': expected})
    result = h.Run(scenario, str(binary.resolve()), str(a.out / tid)).execute()
    ok = result['steps_ok'] and result['exit_status'] == 0 and result['stdout'] == expected + '\n'
    results[language] = {'pass': ok, 'catalog_sha256': hashlib.sha256(catalog.read_bytes()).hexdigest(),
                         'message': message, 'expected': expected, 'actual': result['stdout']}

for name, override, expected in [('override', str(a.prefix / 'share/naro/locale'), 'Hilfe'),
                                  ('invalid-override', str(a.prefix / 'missing'), 'Help')]:
    tid = 'TEST-NEXT-ASSET-' + name
    scenario = dict(id=tid, args=[], lang='en_US.UTF-8',
                    env={'LANGUAGE': 'de', 'NARO_TRANSLATION_PROBE': 'Help', 'NARO_LOCALEDIR': override},
                    stdin='', stdout_redirect=True, hold_tty=True, steps=[{'wait_exit': 5}],
                    expect={'exit_status': 0, 'stdout_contains': expected})
    result = h.Run(scenario, str(binary), str(a.out / tid)).execute()
    results[name] = {'pass': result['steps_ok'] and result.get('stdout') == expected + '\n'}

tid = 'TEST-NEXT-ASSET-SYNTAX'
syntax = a.prefix / 'share/naro/syntax/c.nanorc'
scenario = dict(id=tid, args=['sample.c'], files={'home/.nanorc': {'text': f'include "{syntax}"\n'},
                 'work/sample.c': {'text': 'int main(void) { return 0; }\n'}},
                steps=[{'wait': {'text': 'Read 1 line'}}, {'snapshot': 'syntax'},
                       {'keys': ['^X']}, {'wait_exit': 5}],
                expect={'exit_status': 0, 'screen': [{'snapshot': 'syntax', 'attr_at': [1, 0, '' if tiny else 'fg=2']}]})
result = h.Run(scenario, str(binary), str(a.out / tid)).execute()
results['syntax'] = {'pass': result['steps_ok'] and all(c['pass'] for c in result['checks']) and (not tiny or not syntax.exists()),
                     'behavior': 'nanorc ignored, no syntax installed' if tiny else 'installed syntax applied'}

(a.out / 'report.json').write_text(json.dumps({'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
    'catalogs': len(list((a.prefix / 'share/naro/locale').glob('*/LC_MESSAGES/nano.mo'))), 'results': results}, indent=2) + '\n')
print(json.dumps({'checks': len(results), 'passed': sum(r['pass'] for r in results.values())}))
raise SystemExit(int(any(not r['pass'] for r in results.values())))
