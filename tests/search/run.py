#!/usr/bin/env python3
"""Private, bounded search resource regressions using frozen production sources."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import tarfile
import time

ROOT = Path(__file__).resolve().parents[2]
CASES = ('stress_find_literal', 'stress_find_regex', 'stress_replace_literal',
         'stress_replace_regex', 'stress_replace_backward_regex', 'stress_replace_multiline')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def freeze(out, revision):
    out.mkdir()
    paths = ['src', 'native', 'assets', 'Cargo.toml', 'Cargo.lock', 'build.rs', 'CREDITS.md']
    if revision:
        archive = subprocess.check_output(['git', 'archive', revision, *paths], cwd=ROOT)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(out, filter='data')
    else:
        for name in paths:
            source = ROOT / name
            if source.is_dir(): shutil.copytree(source, out / name)
            else: shutil.copy2(source, out / name)
    (out / 'tests/search').mkdir(parents=True)
    shutil.copy2(ROOT / 'tests/search/regressions.rs', out / 'tests/search/regressions.rs')
    search = out / 'src/search.rs'
    if 'mod tests;' not in search.read_text():
        with search.open('a') as f:
            f.write('\n#[cfg(test)]\n#[path = "../tests/search/regressions.rs"]\nmod tests;\n')
    manifest = {str(p.relative_to(out)): digest(p) for p in out.rglob('*') if p.is_file()}
    (out / 'source-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')

def build(source, profile):
    command = [str(Path.home() / '.cargo/bin/cargo'), 'test', '--release', '--no-run', '--message-format=json']
    if profile == 'tiny': command += ['--features', 'tiny']
    result = subprocess.run(command, cwd=source, capture_output=True, text=True)
    (source / f'build-{profile}.log').write_text(result.stdout + result.stderr)
    if result.returncode: raise RuntimeError(f'build failed: {source}, {profile}')
    executables = [json.loads(line)['executable'] for line in result.stdout.splitlines()
                   if line.startswith('{') and json.loads(line).get('executable')]
    if len(executables) != 1: raise RuntimeError('expected exactly one test binary')
    binary = source / f'tests-{profile}'
    shutil.copy2(executables[0], binary)
    return binary, command

def run(binary, case, out, before):
    out.mkdir()
    address_mib = 96 if 'find_' in case else 256
    rss_mib = 48 if 'find_' in case else 192
    timeout = 5
    def limits():
        resource.setrlimit(resource.RLIMIT_AS, (address_mib * 1024 * 1024,) * 2)
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    command = [str(binary), f'search::tests::{case}', '--exact', '--ignored', '--nocapture']
    start = time.monotonic()
    timed_out = False
    with (out / 'stdout.txt').open('w') as stdout, (out / 'stderr.txt').open('w') as stderr:
        child = subprocess.Popen(command, stdout=stdout, stderr=stderr, preexec_fn=limits)
        while True:
            pid, status, usage = os.wait4(child.pid, os.WNOHANG)
            if pid: break
            if time.monotonic() - start >= timeout:
                timed_out = True
                child.kill()
                _, status, usage = os.wait4(child.pid, 0)
                break
            time.sleep(0.01)
        child.returncode = os.waitstatus_to_exitcode(status)
    output = (out / 'stdout.txt').read_text()
    error = (out / 'stderr.txt').read_text()
    passed = child.returncode == 0 and not timed_out and usage.ru_maxrss <= rss_mib * 1024 and '1 passed' in output
    expected = (timed_out or ('memory allocation' in error and child.returncode != 0)) if before else passed
    return dict(case=case, command=command, binary_sha256=digest(binary), passed=passed,
                expected_result=expected, exit_code=child.returncode, timeout=timed_out,
                elapsed_seconds=time.monotonic()-start, peak_rss_kib=usage.ru_maxrss,
                timeout_seconds=timeout, address_space_bound_mib=address_mib, peak_rss_bound_mib=rss_mib)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--before-revision')
    args = ap.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    summary = []
    for label, revision in ([('before', args.before_revision)] if args.before_revision else []) + [('after', None)]:
        source = out / label
        freeze(source, revision)
        for profile in ['default', 'tiny']:
            binary, command = build(source, profile)
            # Tiny disables undo, isolating the old search algorithm from #6.
            cases = CASES[:2] if label == 'before' and profile == 'default' else CASES
            if label == 'before': cases = cases[:4]
            for case in cases:
                report = run(binary, case, out / f'{label}-{profile}-{case}', label == 'before')
                report.update(label=label, profile=profile, revision=revision, build_command=command,
                              source_manifest_sha256=digest(source / 'source-manifest.json'))
                summary.append(report)
                print(label, profile, case, report['exit_code'], round(report['elapsed_seconds'], 3),
                      report['peak_rss_kib'], report['expected_result'], flush=True)
            (out / 'results.json').write_text(json.dumps(summary, indent=2) + '\n')
    return int(not all(r['expected_result'] for r in summary))

if __name__ == '__main__':
    raise SystemExit(main())
