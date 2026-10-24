#!/usr/bin/env python3
"""Install verified Naro files; remove only unchanged manifest-owned files."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile

STATE = '.naro-install.json'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def relative(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or '\\' in name or str(p) != name:
        raise ValueError('unsafe package path: ' + name)
    return Path(*p.parts)


def destination(prefix, name):
    target = prefix / relative(name)
    # Never follow pre-existing directory/file symlinks during install/removal.
    for node in [target, *target.parents]:
        if node.is_symlink():
            raise ValueError('symlink in destination: ' + str(node))
    return target


def extract(archive, into):
    with tarfile.open(archive, 'r:*') as tar:
        members = tar.getmembers()
        names, total = set(), 0
        for member in members:
            name = relative(member.name)
            if member.name in names or not (member.isdir() or member.isfile()):
                raise ValueError('unsupported/duplicate archive entry: ' + member.name)
            names.add(member.name)
            total += member.size
            if member.size > 64 * 1024 * 1024 or total > 512 * 1024 * 1024:
                raise ValueError('package exceeds extraction budget')
            target = into / name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as source, target.open('xb') as output:
                    shutil.copyfileobj(source, output)
                target.chmod(member.mode & 0o777)
    roots = list(into.iterdir())
    if len(roots) != 1 or not roots[0].is_dir():
        raise ValueError('package must have one root directory')
    return roots[0]


def install(root, prefix):
    manifest = json.loads((root / 'manifest.json').read_text())
    if manifest.get('format') != 1:
        raise ValueError('unsupported package manifest')
    destination(prefix, STATE)
    previous = json.loads((prefix / STATE).read_text()) if (prefix / STATE).is_file() else {'files': {}}
    # Validate every source and destination before changing the prefix.
    for name, info in manifest['files'].items():
        if not isinstance(info['mode'], int) or not 0 <= info['mode'] <= 0o777:
            raise ValueError('unsafe file mode: ' + name)
        source = destination(root, name)
        if not source.is_file() or digest(source) != info['sha256']:
            raise ValueError('package checksum mismatch: ' + name)
        target = destination(prefix, name)
        if target.exists():
            prior = previous['files'].get(name)
            if not target.is_file() or prior is None or digest(target) != prior['sha256']:
                raise ValueError('existing/modified file conflict: ' + name)
    if previous['files'] and set(previous['files']) != set(manifest['files']):
        raise ValueError('file set changed; remove the prior installation first')
    prefix.mkdir(parents=True, exist_ok=True)
    for name, info in manifest['files'].items():
        source, target = root / relative(name), destination(prefix, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Atomic replacement here is installer behavior, not editor saving.
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as output:
            staged = Path(output.name)
            try:
                with source.open('rb') as stream:
                    shutil.copyfileobj(stream, output)
                output.flush()
                os.fsync(output.fileno())
                staged.chmod(info['mode'])
                staged.replace(target)
            finally:
                staged.unlink(missing_ok=True)
    (prefix / STATE).write_text(json.dumps(manifest, indent=2) + '\n')
    return {'installed': len(manifest['files']), 'prefix': str(prefix)}


def uninstall(prefix):
    state = destination(prefix, STATE)
    manifest = json.loads(state.read_text())
    conflicts, directories, removed = {}, set(), 0
    for name, info in manifest['files'].items():
        try:
            target = destination(prefix, name)
        except ValueError:
            conflicts[name] = info
            continue
        if target.exists():
            if not target.is_file() or digest(target) != info['sha256']:
                conflicts[name] = info
                continue
            target.unlink()
            removed += 1
        directories.update(p for p in target.parents if p != prefix and prefix in p.parents)
    for directory in sorted(directories, key=lambda p: len(p.parts), reverse=True):
        try:
            directory.rmdir()  # Only empty, known package directories.
        except OSError:
            pass
    if conflicts:
        manifest['files'] = conflicts
        state.write_text(json.dumps(manifest, indent=2) + '\n')
    else:
        state.unlink()
    return {'removed': removed, 'conflicts': sorted(conflicts)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'uninstall'])
    parser.add_argument('--prefix', type=Path, default=Path.home() / '.local')
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--from-directory', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    # absolute(), not resolve(): resolving would conceal a destination symlink.
    prefix = args.prefix.absolute()
    if prefix.is_symlink() or prefix == Path('/'):
        raise ValueError('unsafe installation prefix')
    if args.action == 'uninstall':
        result = uninstall(prefix)
    elif args.archive:
        with tempfile.TemporaryDirectory(prefix='naro-unpack-') as scratch:
            result = install(extract(args.archive, Path(scratch)), prefix)
    else:
        result = install(args.from_directory.resolve(), prefix)
    print(json.dumps(result))
    return int(bool(result.get('conflicts')))


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, tarfile.TarError) as error:
        raise SystemExit(str(error))
