#!/usr/bin/env python3
"""Validate archives/install/removal only in nanoharness-owned private fixtures."""
import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'spec/tools'))
import nanoharness as h

p = argparse.ArgumentParser()
p.add_argument('--archive', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--clean-container', help='rootless image with matching native libraries/locales')
p.add_argument('--source-archive', type=Path)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
fixture = Path(h.WORKROOT) / ('TEST-NEXT-PACKAGE-' + uuid.uuid4().hex[:12]) / 'fx'
for directory in ['home', 'work', 'tmp']:
    (fixture / directory).mkdir(parents=True)
h.make_fixture(str(fixture), {})
prefix = fixture / 'work/Prefix With Spaces'
env = {**os.environ, 'HOME': str(fixture / 'home'), 'TMPDIR': str(fixture / 'tmp')}
script = ROOT / 'tools/release/install.py'
checks = []


def check(name, passed, detail=None):
    checks.append({'name': name, 'pass': bool(passed), 'detail': detail})
    print(name, 'PASS' if passed else 'FAIL')


def installer(*args):
    return subprocess.run([sys.executable, str(script), *map(str, args)], cwd=fixture / 'work',
                          env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


result = installer('install', '--archive', a.archive.resolve(), '--prefix', prefix)
check('install-prefix-with-spaces', result.returncode == 0, result.stdout + result.stderr)
if result.returncode:
    raise SystemExit(1)
binary = prefix / 'bin/naro'
manifest = json.loads((prefix / '.naro-install.json').read_text())
check('installed-hashes', all(hashlib.sha256((prefix / path).read_bytes()).hexdigest() == info['sha256']
                              for path, info in manifest['files'].items()))
link = fixture / 'work/launcher'
link.symlink_to(binary)
probe = subprocess.run([str(link)], env={**env, 'LANG': 'en_US.UTF-8', 'LC_ALL':'en_US.UTF-8', 'LANGUAGE': 'de',
                       'NARO_TRANSLATION_PROBE': 'Help'}, stdout=subprocess.PIPE, text=True)
check('symlink-launcher-assets', probe.returncode == 0 and probe.stdout == 'Hilfe\n')
assets_out = (a.out / 'assets').resolve()
result = subprocess.run([sys.executable, str(ROOT / 'tools/check_installed_assets.py'),
                         '--prefix', str(prefix), '--out', str(assets_out)], env=env)
check('installed-native-catalogs-and-syntax', result.returncode == 0)

if a.clean_container:
    output = a.out / 'clean-environment'
    output.mkdir()
    result = subprocess.run(['podman', 'run', '--rm', '--network', 'none',
        '-v', str(ROOT) + ':/test-runtime:ro', '-v', str(prefix) + ':/Prefix With Spaces:ro',
        '-v', str(output.resolve()) + ':/out', a.clean_container, 'python3',
        '/test-runtime/tools/check_installed_assets.py', '--prefix', '/Prefix With Spaces', '--out', '/out/assets'])
    check('assets-without-build-checkout', result.returncode == 0)

# Verify and rebuild the corresponding source inside the private fixture.
if a.source_archive:
    spec = importlib.util.spec_from_file_location('naro_installer', script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source_dir = fixture / 'work/source'
    source_dir.mkdir()
    source = module.extract(a.source_archive.resolve(), source_dir)
    metadata = json.loads((a.archive.parent / 'build.json').read_text())
    check('source-archive-hashes', all((source / path).is_file() and
          hashlib.sha256((source / path).read_bytes()).hexdigest() == value
          for path, value in metadata['source_files'].items()))
    build_env = {**env, 'CARGO_TARGET_DIR': str(fixture / 'work/rebuild'),
                 'RUSTUP_HOME':os.environ.get('RUSTUP_HOME',str(Path.home()/'.rustup')),
                 'CARGO_HOME':os.environ.get('CARGO_HOME',str(Path.home()/'.cargo'))}
    cargo = os.environ.get('CARGO', str(Path.home() / '.cargo/bin/cargo'))
    result = subprocess.run([cargo, 'build', '--release', '--offline'], cwd=source,
                            env=build_env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    (a.out / 'source-build.log').write_text(result.stdout)
    check('source-archive-build', result.returncode == 0)
    if result.returncode == 0:
        rebuilt = fixture / 'work/rebuild/release/naro'
        info = json.loads(subprocess.check_output([str(rebuilt)],env={**env,'NARO_BUILD_INFO':'1'},text=True))
        check('rebuilt-source-fingerprint', info['source_sha256'] == manifest['compiled_build']['source_sha256'])

# A changed payload must be rejected before any prefix is written.
tampered = fixture / 'tmp/tampered.tar'
with tarfile.open(a.archive, 'r:*') as original_tar, tarfile.open(tampered, 'w') as output_tar:
    changed = False
    for entry in original_tar.getmembers():
        data = original_tar.extractfile(entry).read() if entry.isfile() else None
        if entry.name.endswith('/bin/naro'):
            data += b'tampered'
            entry.size = len(data)
            changed = True
        output_tar.addfile(entry, io.BytesIO(data) if data is not None else None)
result = installer('install', '--archive', tampered, '--prefix', fixture / 'work/tampered-prefix')
check('reject-checksum-mismatch', changed and result.returncode != 0 and not (fixture/'work/tampered-prefix').exists())

for name, member_name, kind in [('traversal', 'top/../escape', tarfile.REGTYPE),
                                 ('absolute', str(fixture / 'work/escape'), tarfile.REGTYPE),
                                 ('symlink', 'top/link', tarfile.SYMTYPE)]:
    archive = fixture / 'tmp' / (name + '.tar')
    with tarfile.open(archive, 'w') as tar:
        info = tarfile.TarInfo(member_name)
        info.type = kind
        if kind == tarfile.SYMTYPE:
            info.linkname = str(fixture / 'work/protected')
            tar.addfile(info)
        else:
            info.size = 1
            tar.addfile(info, io.BytesIO(b'x'))
    destination = fixture / 'work' / ('reject-' + name)
    result = installer('install', '--archive', archive, '--prefix', destination)
    check('reject-' + name, result.returncode != 0 and not destination.exists(), result.stderr)

bad = fixture / 'work/symlink-prefix'
bad.symlink_to(fixture / 'work/protected')
result = installer('install', '--archive', a.archive.resolve(), '--prefix', bad)
check('reject-destination-symlink', result.returncode != 0)
owned = prefix / 'share/doc/naro/README.md'
original = owned.read_bytes()
owned.write_bytes(original + b'local change\n')
unrelated = prefix / 'unrelated.txt'
unrelated.write_bytes(b'keep\n')
result = installer('uninstall', '--prefix', prefix)
check('uninstall-preserves-conflicts', result.returncode == 1 and owned.read_bytes() == original + b'local change\n'
      and unrelated.read_bytes() == b'keep\n', result.stdout + result.stderr)
owned.write_bytes(original)
result = installer('uninstall', '--prefix', prefix)
check('uninstall-owned-only', result.returncode == 0 and unrelated.read_bytes() == b'keep\n'
      and not binary.exists() and not (prefix / '.naro-install.json').exists())

(a.out / 'report.json').write_text(json.dumps({'fixture': str(fixture),
    'archive_sha256': hashlib.sha256(a.archive.read_bytes()).hexdigest(),
    'binary_sha256': manifest['binary_sha256'], 'checks': checks}, indent=2) + '\n')
raise SystemExit(int(any(not c['pass'] for c in checks)))
