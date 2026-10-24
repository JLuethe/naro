#!/usr/bin/env python3
"""Build a versioned Naro archive and matching source archive with provenance."""
import argparse
import hashlib
import json
from pathlib import Path
import os
import platform
import shutil
import subprocess
import tarfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def run(args):
    return subprocess.check_output(args, text=True, cwd=ROOT).strip()


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--features', default='default')
    parser.add_argument('--target', default='x86_64-unknown-linux-gnu')
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit('preserve artifacts: use a new output directory')
    if args.features == 'test-hooks' or b'NARO_TEST_PANIC_DIR' in args.binary.read_bytes():
        raise SystemExit('refusing to package recovery-test instrumentation')
    build = json.loads(subprocess.check_output([str(args.binary.resolve())], env={**os.environ,'NARO_BUILD_INFO':'1'}, text=True))
    inputs = sorted([p for directory in ['src','native','assets'] for p in (ROOT/directory).rglob('*')if p.is_file()] + [ROOT/n for n in ['Cargo.toml','Cargo.lock','build.rs','CREDITS.md']])
    sums = subprocess.check_output(['sha256sum',*[str(p.relative_to(ROOT))for p in inputs]],cwd=ROOT)
    if hashlib.sha256(sums).hexdigest()!=build['source_sha256']:
        raise SystemExit('binary source fingerprint does not match this checkout; rebuild first')
    if build['features'] != ('' if args.features=='default' else args.features):
        raise SystemExit('binary features do not match requested package features')
    tracked = set(run(['git', 'ls-files']).splitlines())
    if any(str(path.relative_to(ROOT)) not in tracked for path in inputs):
        raise SystemExit('source input is untracked; add it before packaging')
    args.out.mkdir(parents=True)
    version = tomllib.loads((ROOT / 'Cargo.toml').read_text())['package']['version']
    name = f'naro-{version}-{args.target}'
    stage = args.out / name
    stage.mkdir()

    def copy(source, relative):
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    copy(args.binary, 'bin/naro')
    for folder in ['locale', 'syntax']:
        shutil.copytree(ROOT / 'assets' / folder, stage / 'share/naro' / folder)
    shutil.copytree(ROOT / 'assets/po', stage / 'share/doc/naro/po')
    for file in ['LICENSE', 'NOTICE', 'CREDITS.md', 'README.md', 'INSTALL.md', 'IMPLEMENTATION.md']:
        copy(ROOT / file, 'share/doc/naro/' + file)
    examples = stage / 'share/doc/naro/examples'
    examples.mkdir()
    (examples / 'nanorc.example').write_text('# Include installed syntax files explicitly. Replace /your/prefix.\ninclude "/your/prefix/share/naro/syntax/*.nanorc"\n')
    metadata = {
        'format': 1, 'product_version': version, 'compiled_build':build,
        'reference_commit': '6ed285c3ec7a1d228def4d4e7021c6ba269f620c',
        'source_revision': run(['git', 'rev-parse', 'HEAD']),
        'dirty': bool(run(['git', 'status', '--porcelain'])),
        'target': args.target, 'features': args.features,
        'rustc': build['rustc'],
        'system': platform.platform(), 'binary_sha256': sha(args.binary),
        'linked_libraries': run(['ldd', str(args.binary.resolve())]),
        'required_symbols': run(['readelf', '--version-info', str(args.binary.resolve())]),
        'files': {},
    }
    for file in sorted(stage.rglob('*')):
        if file.is_file():
            metadata['files'][file.relative_to(stage).as_posix()] = {'sha256': sha(file), 'mode': file.stat().st_mode & 0o777}
    (stage / 'manifest.json').write_text(json.dumps(metadata, indent=2) + '\n')
    shutil.copy2(ROOT / 'tools/release/install.py', stage / 'install.py')
    archive = args.out / (name + '.tar.gz')
    with tarfile.open(archive, 'w:gz') as tar:
        tar.add(stage, arcname=name)
    source = args.out / f'naro-{version}-source.tar.gz'
    names = run(['git', 'ls-files']).splitlines()
    source_files = {}
    with tarfile.open(source, 'w:gz') as tar:
        for name in names:
            path = ROOT / name
            if path.is_file():
                tar.add(path, arcname=f'naro-{version}-source/{name}')
                source_files[name] = sha(path)
    metadata['source_files'] = source_files
    (args.out / 'build.json').write_text(json.dumps(metadata, indent=2) + '\n')
    (args.out / 'SHA256SUMS').write_text('\n'.join(f'{sha(path)}  {path.name}' for path in [archive, source]) + '\n')
    print(json.dumps({'archive': str(archive), 'source': str(source), 'binary_sha256': metadata['binary_sha256']}))


if __name__ == '__main__':
    main()
