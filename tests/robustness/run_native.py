#!/usr/bin/env python3
"""Bounded sanitizer/libFuzzer exercise of the actual native bridge."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--runs', type=int, default=100000)
    args = parser.parse_args()
    if args.runs < 1:
        parser.error('runs must be positive')
    compiler = shutil.which('clang')
    if not compiler:
        parser.error('missing prerequisite: clang with libFuzzer/ASan/UBSan')
    args.out.mkdir(parents=True, exist_ok=False)
    out = args.out.resolve()
    corpus = out / 'corpus'
    corpus.mkdir()
    for name, data in {'empty': b'', 'nul': b'a\0ab\0', 'utf8': 'aé界'.encode(),
                       'boundary': b'ab' * 2048, 'all-bytes': bytes(range(256))}.items():
        (corpus / name).write_bytes(data)
    records = []
    sources = ['native/bridge.c', 'native/options.inc', 'native/confinement.inc',
               'tests/robustness/native_fuzz.c']
    report = {'sources': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                          for name in sources}, 'commands': records, 'profiles': {}}
    report['compiler'] = subprocess.check_output([compiler, '--version'], text=True)

    def run(label, command, **kwargs):
        result = subprocess.run(command, capture_output=True, timeout=90, **kwargs)
        (out / (label + '.log')).write_bytes(result.stdout + result.stderr)
        records.append({'label': label, 'command': list(map(str, command)), 'exit_code': result.returncode})
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        if result.returncode:
            raise RuntimeError(f'{label} failed: see {out / (label + ".log")}')
        return result

    for profile in ['default', 'tiny']:
        binary = out / ('native-' + profile)
        command = [compiler, '-std=c11', '-O1', '-g', '-fno-omit-frame-pointer',
                   '-fsanitize=fuzzer,address,undefined', '-D_DEFAULT_SOURCE',
                   '-D_XOPEN_SOURCE=700']
        if profile == 'tiny':
            command.append('-DNARO_TINY')
        command.extend([str(ROOT / 'native/bridge.c'), str(ROOT / 'tests/robustness/native_fuzz.c'),
                        '-lncursesw'])
        if profile == 'default':
            command.append('-lmagic')
        command.extend(['-o', str(binary)])
        run('build-' + profile, command)
        result = run('fuzz-' + profile, [str(binary), str(corpus), f'-runs={args.runs}',
                     '-max_len=4096', '-timeout=2', '-rss_limit_mb=512', '-seed=20261105',
                     '-artifact_prefix=' + str(out) + '/'],
                     env={**os.environ, 'ASAN_OPTIONS': 'quarantine_size_mb=16:detect_leaks=1',
                          'UBSAN_OPTIONS': 'halt_on_error=1:print_stacktrace=1'})
        if f'#{args.runs}\tDONE'.encode() not in result.stderr:
            raise RuntimeError('fuzzer did not report the required completed operation count')
        report['profiles'][profile] = {'passed': True, 'runs': args.runs,
                                       'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest()}
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['profiles']))


if __name__ == '__main__':
    main()
