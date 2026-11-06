"""Installer fault tests. Every mutation is confined to TemporaryDirectory fixtures."""
from contextlib import ExitStack
import errno
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parent / 'release/install.py'
spec = importlib.util.spec_from_file_location('installer', SCRIPT)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)
MATRIX = []


class InstallerTransactions(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix='naro-installer-test-')
        self.addCleanup(self.scratch.cleanup)
        self.base = Path(self.scratch.name)
        self.root = self.base / 'package'
        self.prefix = self.base / 'Prefix With Spaces'
        self.root.mkdir()

    def package(self, version):
        files = {}
        for name, mode in [('bin/naro', 0o755), ('share/naro/data', 0o644)]:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((version + ':' + name).encode())
            files[name] = {'sha256': installer.digest(path), 'mode': mode}
        manifest = {'format': 1, 'files': files}
        (self.root / 'manifest.json').write_text(json.dumps(manifest))
        return manifest

    def prepare(self, upgrade):
        if self.prefix.exists():
            shutil.rmtree(self.prefix)
        if upgrade:
            self.package('old')
            installer.install(self.root, self.prefix)
        return self.package('new')

    def assert_installed(self, manifest):
        state = installer.read_state(self.prefix)
        self.assertEqual(state['files'], manifest['files'])
        for name, info in manifest['files'].items():
            self.assertTrue(installer.matches(self.prefix / name, info, mode=True), name)
        self.assertFalse((self.prefix / installer.PENDING).exists())

    def instrument(self, stack, events, stop=None, failure='after'):
        def wrap(function, label):
            def operation(*args, **kwargs):
                event = label(*args, **kwargs)
                events.append(event)
                triggered = stop == len(events)
                if triggered and failure == 'before':
                    raise OSError(errno.EIO, 'injected before ' + event)
                result = function(*args, **kwargs)
                if triggered:
                    if failure == 'exit':
                        os._exit(73)
                    raise OSError(errno.EIO, 'injected after ' + event)
                return result
            return operation

        def path_label(kind, path):
            path = Path(path)
            if path.name.startswith('.naro-tmp-'):
                path = path.with_name('.naro-tmp-*')
            name = str(path.relative_to(self.prefix)) if path.is_relative_to(self.prefix) else '<fixture-parent>'
            if name.startswith(installer.STAGE_PREFIX):
                name = installer.STAGE_PREFIX + '*' + ('/' + path.name if path.parent != self.prefix else '')
            return kind + ':' + name

        for name in ('replace', 'unlink', 'mkdir', 'rmdir'):
            original = getattr(Path, name)
            if name == 'replace':
                label = lambda path, target: path_label('replace', target)
            else:
                label = lambda path, *args, _kind=name, **kwargs: path_label(_kind, path)
            stack.enter_context(patch.object(Path, name, wrap(original, label)))
        original_fsync = os.fsync
        stack.enter_context(patch.object(os, 'fsync', wrap(original_fsync,
            lambda fd: path_label('fsync', os.readlink('/proc/self/fd/' + str(fd))))))

    def test_all_mutation_and_sync_boundaries_restart(self):
        # Count actual operations, then fail before/after each or terminate a
        # child immediately after it. No production fault-injection controls.
        for upgrade in (False, True):
            manifest = self.prepare(upgrade)
            events = []
            with ExitStack() as stack:
                self.instrument(stack, events)
                installer.install(self.root, self.prefix)
            self.assertIn('replace:bin/naro', events)
            self.assertIn('replace:share/naro/data', events)
            self.assertIn('replace:' + installer.STATE, events)
            for failure in ('before', 'after', 'exit'):
                for stop, event in enumerate(events, 1):
                    with self.subTest(upgrade=upgrade, failure=failure, stop=stop, event=event):
                        manifest = self.prepare(upgrade)
                        actual = []
                        if failure == 'exit':
                            child = os.fork()
                            if child == 0:
                                with ExitStack() as stack:
                                    self.instrument(stack, actual, stop, failure)
                                    installer.install(self.root, self.prefix)
                                os._exit(99)
                            _, status = os.waitpid(child, 0)
                            self.assertEqual(os.waitstatus_to_exitcode(status), 73)
                        else:
                            with ExitStack() as stack, self.assertRaises(OSError):
                                self.instrument(stack, actual, stop, failure)
                                installer.install(self.root, self.prefix)
                            self.assertEqual(actual[stop - 1], event)
                        pending = (self.prefix / installer.PENDING).exists()
                        # Without a published journal, installed data must be
                        # wholly old/uninstalled or wholly new and state-owned.
                        if not pending:
                            state = installer.read_state(self.prefix)
                            if state:
                                for name, info in state['files'].items():
                                    self.assertTrue(installer.matches(self.prefix / name, info, mode=True))
                            else:
                                self.assertFalse((self.prefix / 'bin/naro').exists())
                                self.assertFalse((self.prefix / 'share/naro/data').exists())
                        installer.install(self.root, self.prefix)
                        self.assert_installed(manifest)
                        MATRIX.append({'upgrade': upgrade, 'failure': failure,
                                       'boundary': stop, 'event': event, 'pending': pending, 'pass': True})

    def interrupt_after(self, target_name):
        replace = Path.replace
        def interrupted(path, target):
            result = replace(path, target)
            if target == self.prefix / target_name:
                raise OSError(errno.EIO, 'injected replacement interruption')
            return result
        with patch.object(Path, 'replace', interrupted), self.assertRaises(OSError):
            installer.install(self.root, self.prefix)

    def test_pending_uninstall_after_each_file_and_state(self):
        for upgrade in (False, True):
            for target in ('bin/naro', 'share/naro/data', installer.STATE):
                with self.subTest(upgrade=upgrade, target=target):
                    self.prepare(upgrade)
                    self.interrupt_after(target)
                    unrelated = self.prefix / 'unrelated'
                    unrelated.write_text('keep')
                    result = installer.uninstall(self.prefix)
                    self.assertEqual(result, {'removed': 2, 'conflicts': []})
                    self.assertEqual(unrelated.read_text(), 'keep')
                    self.assertFalse((self.prefix / installer.STATE).exists())
                    self.assertFalse((self.prefix / installer.PENDING).exists())
                    self.assertFalse((self.prefix / 'bin/naro').exists())

    def test_recover_without_original_package(self):
        manifest = self.prepare(True)
        self.interrupt_after('bin/naro')
        shutil.rmtree(self.root)
        result = subprocess.run([sys.executable, str(SCRIPT), 'recover', '--prefix', str(self.prefix)],
                                text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['recovered'])
        self.assert_installed(manifest)

    def test_repeated_package_can_restore_missing_owned_file(self):
        manifest = self.package('same')
        installer.install(self.root, self.prefix)
        (self.prefix / 'bin/naro').unlink()
        installer.install(self.root, self.prefix)
        self.assert_installed(manifest)

    def test_partial_copy_failure_preserves_old_state_and_recovers(self):
        for stage_copy in (True, False):
            with self.subTest(stage_copy=stage_copy):
                manifest = self.prepare(True)
                copy = shutil.copyfileobj
                fired = False
                def partial(source, output, *args, **kwargs):
                    nonlocal fired
                    in_stage = Path(output.name).parent.name.startswith(installer.STAGE_PREFIX)
                    if in_stage == stage_copy and not fired:
                        fired = True
                        output.write(source.read(3))
                        raise OSError(errno.ENOSPC, 'injected partial copy')
                    return copy(source, output, *args, **kwargs)
                with patch.object(shutil, 'copyfileobj', partial), self.assertRaises(OSError):
                    installer.install(self.root, self.prefix)
                self.assertTrue(fired)
                self.assertEqual((self.prefix / 'bin/naro').read_text(), 'old:bin/naro')
                installer.install(self.root, self.prefix)
                self.assert_installed(manifest)

    def test_partial_state_write_keeps_old_json_and_pending_recovery(self):
        manifest = self.prepare(True)
        old = (self.prefix / installer.STATE).read_bytes()
        atomic_write = installer.atomic_write
        def partial(target, writer, mode):
            if target.name == installer.STATE:
                def partial_writer(output):
                    output.write(b'{"format":')
                    raise OSError(errno.ENOSPC, 'injected partial state write')
                return atomic_write(target, partial_writer, mode)
            return atomic_write(target, writer, mode)
        with patch.object(installer, 'atomic_write', partial), self.assertRaises(OSError):
            installer.install(self.root, self.prefix)
        self.assertEqual((self.prefix / installer.STATE).read_bytes(), old)
        self.assertTrue((self.prefix / installer.PENDING).exists())
        installer.install(self.root, self.prefix)
        self.assert_installed(manifest)

    def test_state_data_and_mode_sync_precede_replace_then_directory_sync(self):
        self.prefix.mkdir()
        target = self.prefix / installer.STATE
        target.write_text('{"old": true}')
        events = []
        fsync, replace = os.fsync, Path.replace
        def synced(fd):
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                events.append('directory-sync')
            else:
                self.assertEqual(os.fstat(fd).st_mode & 0o777, 0o600)
                events.append('file-sync')
            return fsync(fd)
        def replaced(path, destination):
            self.assertEqual(json.loads(target.read_text()), {'old': True})
            self.assertEqual(json.loads(path.read_text()), {'new': True})
            events.append('state-replace')
            return replace(path, destination)
        with patch.object(os, 'fsync', synced), patch.object(Path, 'replace', replaced):
            installer.write_json(target, {'new': True})
        self.assertEqual(events, ['file-sync', 'state-replace', 'directory-sync'])

    def test_close_failure_prevents_destination_replacement(self):
        manifest = self.prepare(True)
        original = tempfile._TemporaryFileWrapper.close
        fired = False
        def failed_close(output):
            nonlocal fired
            result = original(output)
            if Path(output.name).parent == self.prefix / 'bin' and not fired:
                fired = True
                raise OSError(errno.EIO, 'injected close failure')
            return result
        with patch.object(tempfile._TemporaryFileWrapper, 'close', failed_close), self.assertRaises(OSError):
            installer.install(self.root, self.prefix)
        self.assertTrue(fired)
        self.assertEqual((self.prefix / 'bin/naro').read_text(), 'old:bin/naro')
        installer.install(self.root, self.prefix)
        self.assert_installed(manifest)

    def test_uninstall_partial_state_write_retains_accurate_ownership(self):
        self.package('new')
        installer.install(self.root, self.prefix)
        owned = self.prefix / 'bin/naro'
        original = owned.read_bytes()
        owned.write_text('edit')
        with patch.object(installer, 'write_json', side_effect=OSError(errno.EIO, 'injected state write failure')):
            with self.assertRaises(OSError):
                installer.uninstall(self.prefix)
        self.assertFalse((self.prefix / 'share/naro/data').exists())
        self.assertEqual(owned.read_text(), 'edit')
        self.assertEqual(installer.uninstall(self.prefix)['conflicts'], ['bin/naro'])
        owned.write_bytes(original)
        self.assertEqual(installer.uninstall(self.prefix)['conflicts'], [])
        self.assertFalse((self.prefix / installer.STATE).exists())

    def test_pending_modified_file_and_symlink_protections(self):
        for kind in ('modified', 'file-link', 'directory-link', 'stage-link'):
            with self.subTest(kind=kind):
                self.prepare(True)
                self.interrupt_after('bin/naro')
                owned = self.prefix / 'bin/naro'
                protected = self.base / 'protected'
                protected.write_text('untouched')
                if kind == 'modified':
                    owned.write_text('my edit')
                elif kind == 'file-link':
                    owned.unlink()
                    owned.symlink_to(protected)
                elif kind == 'directory-link':
                    shutil.rmtree(self.prefix / 'bin')
                    (self.prefix / 'bin').symlink_to(self.base, target_is_directory=True)
                else:
                    journal = json.loads((self.prefix / installer.PENDING).read_text())
                    staged = self.prefix / journal['stage'] / '0'
                    staged.unlink()
                    staged.symlink_to(protected)
                for action in (lambda: installer.install(self.root, self.prefix),
                               lambda: installer.uninstall(self.prefix)):
                    with self.assertRaises(ValueError):
                        action()
                    self.assertEqual(protected.read_text(), 'untouched')
                    self.assertTrue((self.prefix / installer.PENDING).exists())
                if kind == 'modified':
                    self.assertEqual(owned.read_text(), 'my edit')

    def test_normal_conflicts_and_symlinks_remain_protected(self):
        self.package('new')
        installer.install(self.root, self.prefix)
        owned = self.prefix / 'bin/naro'
        original = owned.read_bytes()
        owned.write_bytes(b'edit')
        with self.assertRaises(ValueError):
            installer.install(self.root, self.prefix)
        self.assertEqual(installer.uninstall(self.prefix)['conflicts'], ['bin/naro'])
        self.assertEqual(owned.read_bytes(), b'edit')
        owned.write_bytes(original)
        self.assertEqual(installer.uninstall(self.prefix)['conflicts'], [])
        owned.parent.mkdir(exist_ok=True)
        owned.symlink_to(self.root / 'bin/naro')
        with self.assertRaises(ValueError):
            installer.install(self.root, self.prefix)

    def test_reserved_and_overlapping_paths_rejected_before_prefix_creation(self):
        for name in (installer.STATE, installer.PENDING, '../escape', '.', 'bin/naro/data'):
            with self.subTest(name=name):
                manifest = self.package('new')
                manifest['files'][name] = dict(manifest['files']['bin/naro'])
                (self.root / 'manifest.json').write_text(json.dumps(manifest))
                with self.assertRaises(ValueError):
                    installer.install(self.root, self.prefix)
                self.assertFalse(self.prefix.exists())

    def test_bad_source_rejected_before_prefix_creation(self):
        self.package('new')
        (self.root / 'bin/naro').write_text('tampered')
        with self.assertRaises(ValueError):
            installer.install(self.root, self.prefix)
        self.assertFalse(self.prefix.exists())

    def test_archive_install_and_uninstall_cli(self):
        manifest = self.package('archive')
        archive = self.base / 'package.tar.gz'
        with tarfile.open(archive, 'w:gz') as tar:
            tar.add(self.root, arcname='naro-fixture')
        result = subprocess.run([sys.executable, str(SCRIPT), 'install', '--archive', str(archive),
                                 '--prefix', str(self.prefix)], text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_installed(manifest)
        result = subprocess.run([sys.executable, str(SCRIPT), 'uninstall', '--prefix', str(self.prefix)],
                                text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.prefix / installer.STATE).exists())

    def test_archive_symlink_and_traversal_rejected(self):
        for name, kind in (('top/../outside', tarfile.REGTYPE), ('top/link', tarfile.SYMTYPE)):
            with self.subTest(name=name):
                archive = self.base / 'bad.tar'
                with tarfile.open(archive, 'w') as tar:
                    entry = tarfile.TarInfo(name)
                    entry.type = kind
                    if kind == tarfile.SYMTYPE:
                        entry.linkname = str(self.base / 'protected')
                        tar.addfile(entry)
                    else:
                        entry.size = 1
                        tar.addfile(entry, io.BytesIO(b'x'))
                unpack = self.base / 'unpack'
                unpack.mkdir(exist_ok=True)
                with self.assertRaises(ValueError):
                    installer.extract(archive, unpack)

    def test_concurrent_installer_is_rejected(self):
        self.package('new')
        with installer.locked_prefix(self.prefix, create=True):
            result = subprocess.run([sys.executable, str(SCRIPT), 'install', '--from-directory', str(self.root),
                                     '--prefix', str(self.prefix)], text=True, capture_output=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((self.prefix / installer.PENDING).exists())
            self.assertFalse((self.prefix / 'bin/naro').exists())


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(InstallerTransactions))
    if args.report:
        args.report.write_text(json.dumps({'installer_sha256': installer.digest(SCRIPT),
            'tests': result.testsRun, 'successful': result.wasSuccessful(), 'matrix': MATRIX}, indent=2) + '\n')
    raise SystemExit(not result.wasSuccessful())
