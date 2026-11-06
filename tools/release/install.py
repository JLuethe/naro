#!/usr/bin/env python3
"""Install verified Naro files; remove only unchanged manifest-owned files."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile

STATE = '.naro-install.json'
PENDING = '.naro-install.pending.json'
STAGE_PREFIX = '.naro-install-stage-'


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


def validate_manifest(manifest):
    if not isinstance(manifest, dict) or manifest.get('format') != 1 or not isinstance(manifest.get('files'), dict):
        raise ValueError('unsupported package manifest')
    for name, info in manifest['files'].items():
        path = relative(name)
        if not path.parts or path.parts[0].startswith('.naro-'):
            raise ValueError('reserved package path: ' + name)
        if not isinstance(info, dict) or type(info.get('mode')) is not int or not 0 <= info['mode'] <= 0o777:
            raise ValueError('unsafe file mode: ' + name)
        checksum = info.get('sha256')
        if not isinstance(checksum, str) or len(checksum) != 64 or any(c not in '0123456789abcdef' for c in checksum):
            raise ValueError('invalid checksum: ' + name)
    # A file cannot also be another installed file's parent directory.
    names = set(manifest['files'])
    if any(str(parent) in names for name in names for parent in relative(name).parents):
        raise ValueError('overlapping package paths')
    return manifest


def sync_directory(directory):
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def make_directory(directory):
    if not directory.exists():
        make_directory(directory.parent)
        directory.mkdir()
    # Also retry a directory-link sync that failed after an earlier mkdir.
    sync_directory(directory.parent)


@contextmanager
def locked_prefix(prefix, create=False):
    if not prefix.is_absolute() or prefix == Path('/') or '..' in prefix.parts:
        raise ValueError('unsafe installation prefix')
    destination(prefix, STATE)
    if create:
        make_directory(prefix)
    fd = os.open(prefix, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        # Lock the directory inode, without creating an unowned lock file.
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def read_state(prefix):
    path = destination(prefix, STATE)
    return validate_manifest(json.loads(path.read_text())) if path.exists() else None


def matches(path, info, mode=False):
    return (info is not None and path.is_file() and digest(path) == info['sha256']
            and (not mode or path.stat().st_mode & 0o777 == info['mode']))


def atomic_write(target, writer, mode):
    # Keep the temporary file on the target filesystem, even with nested mounts.
    with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.naro-tmp-', delete=False) as output:
        temporary = Path(output.name)
        try:
            writer(output)
            output.flush()
            os.fchmod(output.fileno(), mode)
            os.fsync(output.fileno())
            output.close()
            temporary.replace(target)
            sync_directory(target.parent)
        finally:
            temporary.unlink(missing_ok=True)


def write_json(target, value):
    data = (json.dumps(value, indent=2) + '\n').encode()
    atomic_write(target, lambda output: output.write(data), 0o600)


def copy_file(source, target, info):
    with source.open('rb') as stream:
        atomic_write(target, lambda output: shutil.copyfileobj(stream, output), info['mode'])


def remove_stage(stage, count):
    # Remove only the exact journal-owned names; never recursively delete a tree.
    for index in range(count):
        path = destination(stage, str(index))
        path.unlink(missing_ok=True)
    if stage.exists():
        stage.rmdir()
        sync_directory(stage.parent)


def recover(prefix):
    pending = destination(prefix, PENDING)
    if not pending.exists():
        return False
    journal = json.loads(pending.read_text())
    if not isinstance(journal, dict) or journal.get('format') != 1:
        raise ValueError('unsupported installer journal')
    manifest = validate_manifest(journal['manifest'])
    previous = journal['previous']
    if previous is not None:
        validate_manifest(previous)
    stage_name = journal['stage']
    if not isinstance(stage_name, str) or not stage_name.startswith(STAGE_PREFIX) or len(relative(stage_name).parts) != 1:
        raise ValueError('unsafe installer staging path')
    if manifest.get('install_transaction') != stage_name:
        raise ValueError('installer journal transaction identity mismatch')
    stage = destination(prefix, stage_name)
    current = read_state(prefix)
    if current != previous and current != manifest:
        raise ValueError('installation state changed during pending transaction')
    before = journal['before']
    if not isinstance(before, dict) or set(before) != set(manifest['files']):
        raise ValueError('invalid installer journal ownership')
    for name, info in before.items():
        if info is not None and (previous is None or previous['files'].get(name) != info):
            raise ValueError('invalid installer journal ownership: ' + name)
    committed = current == manifest
    # Preflight the complete recovery before modifying any further destination.
    for index, (name, info) in enumerate(manifest['files'].items()):
        target = destination(prefix, name)
        if committed:
            accepted = matches(target, info, mode=True)
        else:
            accepted = (matches(target, info, mode=True) or matches(target, before[name])
                        or (not target.exists() and before[name] is None))
            if not matches(destination(stage, str(index)), info, mode=True):
                raise ValueError('pending installer staging checksum/mode mismatch: ' + name)
        if not accepted:
            raise ValueError('existing/modified file conflict in pending transaction: ' + name)
    if not committed:
        for index, (name, info) in enumerate(manifest['files'].items()):
            target = destination(prefix, name)
            make_directory(target.parent)
            copy_file(destination(stage, str(index)), target, info)
        write_json(destination(prefix, STATE), manifest)
    else:
        # A previous process may have stopped between state rename and dir sync.
        sync_directory(prefix)
    remove_stage(stage, len(manifest['files']))
    pending.unlink()
    sync_directory(prefix)
    return True


def install(root, prefix):
    manifest = validate_manifest(json.loads((root / 'manifest.json').read_text()))
    for name, info in manifest['files'].items():
        if not matches(destination(root, name), info):
            raise ValueError('package checksum mismatch: ' + name)
    with locked_prefix(prefix, create=True):
        recover(prefix)
        previous = read_state(prefix)
        before = {}
        # Validate every source and destination before publishing a transaction.
        for name, info in manifest['files'].items():
            if not matches(destination(root, name), info):
                raise ValueError('package checksum mismatch: ' + name)
            target = destination(prefix, name)
            prior = previous['files'].get(name) if previous else None
            if target.exists() and not matches(target, prior):
                raise ValueError('existing/modified file conflict: ' + name)
            before[name] = prior if target.exists() else None
        if previous and previous['files'] and set(previous['files']) != set(manifest['files']):
            raise ValueError('file set changed; remove the prior installation first')
        stage = Path(tempfile.mkdtemp(prefix=STAGE_PREFIX, dir=prefix))
        # Distinguish a repeated installation of identical package contents from
        # a transaction whose final state was already committed before a crash.
        manifest = dict(manifest, install_transaction=stage.name)
        # No installed file changes until the stage and journal are durable.
        # On errors retain staging: journal publication may have succeeded even
        # when the following directory fsync failed. Recovery needs these bytes.
        for index, (name, info) in enumerate(manifest['files'].items()):
            copy_file(destination(root, name), stage / str(index), info)
            if not matches(stage / str(index), info, mode=True):
                raise ValueError('package changed during staging: ' + name)
        sync_directory(stage)
        sync_directory(prefix)
        write_json(destination(prefix, PENDING), {'format': 1, 'manifest': manifest,
                   'previous': previous, 'before': before, 'stage': stage.name})
        recover(prefix)
        return {'installed': len(manifest['files']), 'prefix': str(prefix)}


def uninstall(prefix):
    with locked_prefix(prefix):
        recover(prefix)
        return remove_installed(prefix)


def remove_installed(prefix):
    state = destination(prefix, STATE)
    manifest = validate_manifest(json.loads(state.read_text()))
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
            sync_directory(target.parent)
            removed += 1
        directories.update(p for p in target.parents if p != prefix and prefix in p.parents)
    for directory in sorted(directories, key=lambda p: len(p.parts), reverse=True):
        try:
            directory.rmdir()  # Only empty, known package directories.
        except OSError:
            pass
        else:
            sync_directory(directory.parent)
    if conflicts:
        manifest['files'] = conflicts
        write_json(state, manifest)
    else:
        state.unlink()
        sync_directory(prefix)
    return {'removed': removed, 'conflicts': sorted(conflicts)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'uninstall', 'recover'])
    parser.add_argument('--prefix', type=Path, default=Path.home() / '.local')
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--from-directory', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    # absolute(), not resolve(): resolving would conceal a destination symlink.
    prefix = args.prefix.absolute()
    if prefix.is_symlink() or prefix == Path('/'):
        raise ValueError('unsafe installation prefix')
    if args.action == 'recover':
        with locked_prefix(prefix):
            result = {'recovered': recover(prefix), 'prefix': str(prefix)}
    elif args.action == 'uninstall':
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
