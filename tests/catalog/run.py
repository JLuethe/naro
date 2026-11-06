#!/usr/bin/env python3
"""Validate shipped catalogs and typed position substitution in private fixtures.

Only the fixed Rust test entry point handles malformed templates. The native
bridge must first pass the compiler's nonliteral-format rejection rule.
"""
import argparse
import gettext
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
MSGID = 'line %*zd/%zd (%2d%%), col %2zu/%2zu (%3d%%), char %*zu/%zu (%2d%%)'
TEST = 'native::position_catalog_tests::catalog_position_message'
VALUES = [
    [1, 3, 33, 2, 6, 33, 1, 11, 9],
    [123, 4567, 2, 123, 1234, 9, 12345, 123456, 9],
    [1, 1, 100, 1, 1, 100, 0, 0, 0],
]


def reference(template, values):
    """Independent Python printf oracle for benign, msgfmt-checked catalogs."""
    line, lines, lp, col, cols, cp, count, total, hp = values
    adapted = re.sub(r'%([*0-9]*)z[du]', r'%\1d', template)
    return (adapted % (max(2, len(str(lines))), line, lines, lp, col, cols,
                       cp, max(2, len(str(total))), count, total, hp)).encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', required=True, type=Path,
                        help='Cargo unit-test executable, default or tiny')
    parser.add_argument('--out', required=True, type=Path,
                        help='new private raw-output directory')
    parser.add_argument('--locale', default='en_US.UTF-8',
                        help='installed non-C UTF-8 locale used for gettext')
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    out.chmod(0o700)
    for tool in ['msgfmt', os.environ.get('CC', 'cc')]:
        if not shutil.which(tool):
            raise SystemExit(f'missing prerequisite: {tool}')
    records = []

    def run(label, command, **kwargs):
        result = subprocess.run(command, capture_output=True, timeout=30, **kwargs)
        (out / f'{label}.log').write_bytes(result.stdout + result.stderr)
        records.append({'check': label, 'command': list(map(str, command)),
                        'exit_code': result.returncode})
        if result.returncode:
            raise RuntimeError(f'{label} failed; see {out / (label + ".log")}')
        return result

    run('strict-native-format', [os.environ.get('CC', 'cc'), '-std=c11',
        '-D_DEFAULT_SOURCE', '-D_XOPEN_SOURCE=700', '-Wall', '-Wextra',
        '-Wformat=2', '-Werror=format', '-Werror=format-nonliteral',
        '-fsyntax-only', str(ROOT / 'native/bridge.c')])
    run('literal-native-formats', [sys.executable,
        str(ROOT / 'tests/catalog/check_native_formats.py'), str(ROOT / 'native/bridge.c')])
    run('literal-rule-tests', [sys.executable, '-m', 'unittest', 'discover',
        '-s', str(ROOT / 'tests/catalog'), '-p', 'test_*.py'])
    available = run('test-entry-point', [str(binary), '--list']).stdout.decode()
    if f'{TEST}: test' not in available:
        raise RuntimeError('required fixed formatter test entry point is missing')
    source = (ROOT / 'native/bridge.c').read_text()
    if 'nr_position(' in source:
        raise RuntimeError('legacy position variadic boundary must be removed')
    locale_root = out / 'locale'
    env = dict(os.environ, LC_ALL=args.locale, NARO_LOCALEDIR=str(locale_root))
    expected = out / 'expected.bin'
    env['NARO_POSITION_EXPECTED'] = str(expected)
    template_file = out / 'template.bin'
    env['NARO_POSITION_TEMPLATE'] = str(template_file)
    count = 0

    def check(label, language, values, wanted, template):
        nonlocal count
        expected.write_bytes(wanted)
        template_file.write_bytes(template.encode())
        result = run(label, [str(binary), '--exact', TEST, '--ignored', '--nocapture'],
                     env=dict(env, LANGUAGE=language,
                              NARO_POSITION_VALUES=','.join(map(str, values))))
        if b'1 passed; 0 failed; 0 ignored;' not in result.stdout:
            raise RuntimeError(f'{label} did not execute the required assertion')
        count += 1

    catalogs = sorted((ROOT / 'assets/po').glob('*.po'))
    if not catalogs:
        raise RuntimeError('no shipped catalogs found')
    for po in catalogs:
        mo = locale_root / po.stem / 'LC_MESSAGES/nano.mo'
        mo.parent.mkdir(parents=True)
        run(f'msgfmt-{po.stem}', ['msgfmt', '--check', '--check-format',
                                 '-o', str(mo), str(po)])
        with mo.open('rb') as stream:
            translated = gettext.GNUTranslations(stream).gettext(MSGID)
        for index, values in enumerate(VALUES):
            check(f'catalog-{po.stem}-{index}', po.stem, values,
                  reference(translated, values), translated)

    # These exercise only the fixed Rust formatter through real gettext lookup.
    # They are deliberately non-operational incomplete/unknown syntax examples.
    for label, template in [('missing', 'translated position'),
                            ('trailing', 'translated position %'),
                            ('unknown', 'translated position %q'),
                            ('extra', MSGID + ' extra %2d'),
                            ('oversized', 'x' * 4097)]:
        language = f'fixture_{label}'
        po = out / f'{language}.po'
        po.write_text('msgid ""\nmsgstr ""\n'
                      '"Content-Type: text/plain; charset=UTF-8\\n"\n\n'
                      f'msgid {json.dumps(MSGID)}\n'
                      f'msgstr {json.dumps(template)}\n')
        mo = locale_root / language / 'LC_MESSAGES/nano.mo'
        mo.parent.mkdir(parents=True)
        run(f'msgfmt-{language}', ['msgfmt', '-o', str(mo), str(po)])
        # Require an actual translated entry, rather than accidental fallback.
        with mo.open('rb') as stream:
            assert gettext.GNUTranslations(stream).gettext(MSGID) == template
        check(f'catalog-{language}', language, VALUES[0], reference(MSGID, VALUES[0]), template)

    receipt = {'pass': True, 'catalogs_checked': len(catalogs),
               'position_assertions': count, 'malformed_fixed_only': 5,
               'binary': str(binary),
               'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
               'bridge_sha256': hashlib.sha256((ROOT / 'native/bridge.c').read_bytes()).hexdigest(),
               'commands': records}
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: v for k, v in receipt.items() if k != 'commands'}, indent=2))


if __name__ == '__main__':
    main()
