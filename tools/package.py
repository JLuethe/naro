#!/usr/bin/env python3
"""Build a versioned Naro archive and matching source archive with provenance."""
import argparse
import hashlib
import json
from pathlib import Path
import os
import platform
import re
import shutil
import subprocess
import tarfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = ('LICENSE', 'NOTICE', 'CREDITS.md', 'README.md', 'INSTALL.md',
             'IMPLEMENTATION.md', 'RELEASE_NOTES.md', 'COVERAGE_REVIEW.md',
             'CONTRIBUTING.md', 'SECURITY.md')
REFERENCE_COMMIT = '6ed285c3ec7a1d228def4d4e7021c6ba269f620c'


def validate_status_document(text, version):
    """Keep current status versioned; artifact identities belong in receipts."""
    current = re.split(r'^## Historical\b', text, maxsplit=1, flags=re.MULTILINE)[0]
    identity = re.search(r'^NARO (\d+\.\d+\.\d+) is\b', current, re.MULTILINE)
    versions = re.findall(r'\bNARO (\d+\.\d+\.\d+)\b', current)
    if identity is None or identity.group(1) != version or any(v != version for v in versions):
        raise ValueError(f'IMPLEMENTATION.md must describe current NARO {version}; '
                         'put older qualification under a Historical heading')
    # The pinned GNU reference is stable. Current NARO executable/source/commit
    # identities change per build or repack and must come from machine receipts.
    # Installed repository links are pinned to the documentation revision.
    prose = re.sub(r'\]\([^\s)]+\)', ']', current).replace(REFERENCE_COMMIT, '')
    if re.search(r'\b(?:[0-9a-f]{40}|[0-9a-f]{64})\b', prose):
        raise ValueError('IMPLEMENTATION.md current status must use package receipts '
                         'instead of hardcoded candidate hashes')


def installed_document(text, revision):
    """Keep shipped links local; pin repository-only links to the source commit."""
    def replace(match):
        destination = match.group(1)
        if destination.startswith('#') or re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:', destination):
            return match.group(0)
        path, separator, fragment = destination.partition('#')
        target = (ROOT / path).resolve()
        relative = target.relative_to(ROOT).as_posix()
        if not target.exists():
            raise ValueError(f'missing documentation target: {destination}')
        if relative in DOCUMENTS:
            return match.group(0)
        kind = 'tree' if target.is_dir() else 'blob'
        return f'](https://github.com/JLuethe/naro/{kind}/{revision}/{relative}{separator}{fragment})'
    return re.sub(r'\]\(([^\s)]+)\)', replace, text)


def run(args):
    return subprocess.check_output(args, text=True, cwd=ROOT).strip()


def require_clean_release_tree():
    """Reject tracked changes and untracked files that can enter a package."""
    if Path(run(['git', 'rev-parse', '--show-toplevel'])).resolve() != ROOT.resolve():
        raise SystemExit('release packaging requires the Git checkout root')
    changed = subprocess.check_output(
        ['git', 'status', '--porcelain=v1', '--untracked-files=no',
         '--ignore-submodules=none'], cwd=ROOT)
    if changed:
        raise SystemExit('release packaging requires a clean tracked tree (including the index)')
    relevant = ['src', 'native', 'assets', 'Cargo.toml', 'Cargo.lock', 'build.rs',
                *DOCUMENTS, 'tools/package.py', 'tools/release/install.py']
    untracked = subprocess.check_output(
        ['git', 'ls-files', '--others', '-z', '--', *relevant], cwd=ROOT)
    if untracked:
        names = [os.fsdecode(name) for name in untracked.split(b'\0') if name]
        raise SystemExit('release packaging refuses untracked package inputs: '
                         + ', '.join(names[:5]) + (' ...' if len(names) > 5 else ''))
    tracked = [os.fsdecode(name) for name in subprocess.check_output(
        ['git', 'ls-files', '-z'], cwd=ROOT).split(b'\0') if name]
    if any((ROOT / name).is_symlink() or not (ROOT / name).is_file() for name in tracked):
        raise SystemExit('release source archive requires regular tracked files')


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
    require_clean_release_tree()
    version = tomllib.loads((ROOT / 'Cargo.toml').read_text())['package']['version']
    try:
        validate_status_document((ROOT / 'IMPLEMENTATION.md').read_text(), version)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    if args.features == 'test-hooks' or b'NARO_TEST_PANIC_DIR' in args.binary.read_bytes():
        raise SystemExit('refusing to package recovery-test instrumentation')
    build = json.loads(subprocess.check_output([str(args.binary.resolve())], env={**os.environ,'NARO_BUILD_INFO':'1'}, text=True))
    inputs = sorted([p for directory in ['src','native','assets'] for p in (ROOT/directory).rglob('*')if p.is_file()] + [ROOT/n for n in ['Cargo.toml','Cargo.lock','build.rs','CREDITS.md']])
    sums = subprocess.check_output(['sha256sum',*[str(p.relative_to(ROOT))for p in inputs]],cwd=ROOT)
    if hashlib.sha256(sums).hexdigest()!=build['source_sha256']:
        raise SystemExit('binary source fingerprint does not match this checkout; rebuild first')
    if build['features'] != ('' if args.features=='default' else args.features):
        raise SystemExit('binary features do not match requested package features')
    tracked = set(os.fsdecode(name) for name in subprocess.check_output(
        ['git', 'ls-files', '-z'], cwd=ROOT).split(b'\0') if name)
    if any(str(path.relative_to(ROOT)) not in tracked for path in inputs):
        raise SystemExit('source input is untracked; add it before packaging')
    args.out.mkdir(parents=True)
    name = f'naro-{version}-{args.target}'
    stage = args.out / name
    stage.mkdir()

    def copy(source, relative):
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    copy(args.binary, 'bin/naro')
    tiny = 'tiny' in build['features'].split(',')
    for folder in (['locale'] if tiny else ['locale', 'syntax']):
        shutil.copytree(ROOT / 'assets' / folder, stage / 'share/naro' / folder)
    shutil.copytree(ROOT / 'assets/po', stage / 'share/doc/naro/po')
    revision = run(['git', 'rev-parse', 'HEAD'])
    for file in DOCUMENTS:
        copy(ROOT / file, 'share/doc/naro/' + file)
        if file.endswith('.md'):
            (stage / 'share/doc/naro' / file).write_text(
                installed_document((ROOT / file).read_text(), revision))
    if not tiny:
        examples = stage / 'share/doc/naro/examples'
        examples.mkdir()
        (examples / 'nanorc.example').write_text('# Include installed syntax files explicitly. Replace /your/prefix.\ninclude "/your/prefix/share/naro/syntax/*.nanorc"\n')
    metadata = {
        'format': 1, 'product_version': version, 'compiled_build':build,
        'reference_commit': REFERENCE_COMMIT,
        'source_revision': revision,
        'documentation': {'files': list(DOCUMENTS),
                          'repository_links': 'immutable source revision; source archive text unchanged'},
        'dirty': False, 'provenance': 'clean-commit',
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
    names = sorted(tracked)
    with tarfile.open(source, 'w:gz') as tar:
        for name in names:
            tar.add(ROOT / name, arcname=f'naro-{version}-source/{name}')
    source_files = {}
    source_file_modes = {}
    prefix = f'naro-{version}-source/'
    with tarfile.open(source, 'r:gz') as tar:
        for member in tar:
            if not member.isfile() or not member.name.startswith(prefix):
                raise SystemExit('unexpected source archive member')
            relative = member.name[len(prefix):]
            if relative in source_files:
                raise SystemExit('duplicate source archive member')
            source_files[relative] = hashlib.file_digest(tar.extractfile(member), 'sha256').hexdigest()
            source_file_modes[relative] = member.mode
    if set(source_files) != tracked:
        raise SystemExit('source archive differs from tracked file inventory')
    require_clean_release_tree()
    metadata['source_files'] = source_files
    metadata['source_file_modes'] = source_file_modes
    metadata['source_archive_sha256'] = sha(source)
    (args.out / 'build.json').write_text(json.dumps(metadata, indent=2) + '\n')
    (args.out / 'SHA256SUMS').write_text('\n'.join(f'{sha(path)}  {path.name}' for path in [archive, source]) + '\n')
    print(json.dumps({'archive': str(archive), 'source': str(source), 'binary_sha256': metadata['binary_sha256']}))


if __name__ == '__main__':
    main()
