"""Release packages must identify one clean commit and its exact archive files."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import package


class PackageProvenance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'checkout'
        self.root.mkdir()
        root_patch = patch.object(package, 'ROOT', self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)
        for folder in ('src', 'native', 'assets/locale', 'assets/syntax',
                       'assets/po', 'tools/release'):
            (self.root / folder).mkdir(parents=True)
        for name in package.DOCUMENTS:
            (self.root / name).write_text('Naro documentation\n')
        (self.root / 'IMPLEMENTATION.md').write_text('NARO 0.1.1 is a fixture port.\n')
        (self.root / 'Cargo.toml').write_text('[package]\nname = "naro"\nversion = "0.1.1"\n')
        for name in ('Cargo.lock', 'build.rs', 'src/main.rs', 'native/bridge.c',
                     'assets/locale/catalog', 'assets/syntax/nanorc', 'assets/po/source',
                     'tools/package.py', 'tools/release/install.py'):
            (self.root / name).write_text(name + '\n')
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.out = self.root / 'target/package'

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, text=True).strip()

    def assert_package_rejected(self, message):
        with patch.object(sys, 'argv', ['package.py', '--binary', str(self.root / 'missing-binary'),
                                        '--out', str(self.out)]), self.assertRaisesRegex(SystemExit, message):
            package.main()
        self.assertFalse(self.out.exists())

    def test_clean_package_records_exact_archive_contents(self):
        # A review note is untracked but does not enter either archive.
        (self.root / 'review.txt').write_text('private review\n')
        inputs = sorted([p for folder in ('src', 'native', 'assets')
                         for p in (self.root / folder).rglob('*') if p.is_file()]
                        + [self.root / n for n in ('Cargo.toml', 'Cargo.lock',
                                                    'build.rs', 'CREDITS.md')])
        sums = subprocess.check_output(['sha256sum', *[str(p.relative_to(self.root))
                                                    for p in inputs]], cwd=self.root)
        fingerprint = hashlib.sha256(sums).hexdigest()
        binary = self.root / 'target/release/naro'
        binary.parent.mkdir(parents=True)
        info = {'source_sha256': fingerprint, 'features': '', 'rustc': 'fixture rustc'}
        binary.write_text('#!' + sys.executable + '\nimport json\nprint(' +
                          repr(json.dumps(info)) + ')\n')
        binary.chmod(0o755)
        original_run = package.run

        def fixture_run(args):
            if args[0] in ('ldd', 'readelf'):
                return 'fixture native requirements'
            return original_run(args)

        with patch.object(package, 'run', side_effect=fixture_run), patch.object(
                sys, 'argv', ['package.py', '--binary', str(binary), '--out', str(self.out)]):
            package.main()

        metadata = json.loads((self.out / 'build.json').read_text())
        source = self.out / 'naro-0.1.1-source.tar.gz'
        self.assertEqual(metadata['source_revision'], self.git('rev-parse', 'HEAD'))
        self.assertEqual(metadata['provenance'], 'clean-commit')
        self.assertFalse(metadata['dirty'])
        self.assertEqual(metadata['source_archive_sha256'], package.sha(source))
        with tarfile.open(source) as archive:
            members = archive.getmembers()
            actual = {member.name.removeprefix('naro-0.1.1-source/'):
                      hashlib.sha256(archive.extractfile(member).read()).hexdigest()
                      for member in members}
            modes = {member.name.removeprefix('naro-0.1.1-source/'): member.mode
                     for member in members}
        self.assertEqual(metadata['source_files'], actual)
        self.assertEqual(metadata['source_file_modes'], modes)
        self.assertNotIn('review.txt', actual)
        self.assertEqual(actual['CREDITS.md'], package.sha(self.root / 'CREDITS.md'))
        with tarfile.open(self.out / 'naro-0.1.1-x86_64-unknown-linux-gnu.tar.gz') as archive:
            installed = archive.extractfile(
                'naro-0.1.1-x86_64-unknown-linux-gnu/share/doc/naro/CREDITS.md'
            ).read().decode()
        self.assertEqual(installed, package.installed_document(
            (self.root / 'CREDITS.md').read_text(), self.git('rev-parse', 'HEAD')))

    def test_modified_tracked_document_is_rejected_before_output(self):
        (self.root / 'README.md').write_text('modified\n')
        self.assert_package_rejected('clean tracked tree')

    def test_committed_stale_status_is_rejected_before_binary_or_output(self):
        (self.root / 'Cargo.toml').write_text('[package]\nname = "naro"\nversion = "0.1.2"\n')
        self.git('add', 'Cargo.toml')
        self.git('commit', '-qm', 'version bump without status update')
        self.assert_package_rejected('current NARO 0.1.2')

    def test_committed_stale_candidate_is_rejected_before_binary_or_output(self):
        with (self.root / 'IMPLEMENTATION.md').open('a') as stream:
            stream.write('Production commit: `' + 'a' * 40 + '`.\n')
        self.git('add', 'IMPLEMENTATION.md')
        self.git('commit', '-qm', 'stale candidate identity')
        self.assert_package_rejected('candidate hashes')

    def test_staged_change_is_rejected(self):
        (self.root / 'README.md').write_text('staged\n')
        self.git('add', 'README.md')
        self.assert_package_rejected('clean tracked tree')

    def test_untracked_source_input_is_rejected(self):
        (self.root / 'assets/locale/new-catalog').write_text('new\n')
        self.assert_package_rejected('untracked package inputs: assets/locale/new-catalog')

    def test_ignored_untracked_source_input_is_rejected(self):
        (self.root / '.gitignore').write_text('assets/locale/new-catalog\n')
        self.git('add', '.gitignore')
        self.git('commit', '-qm', 'ignore fixture catalog')
        (self.root / 'assets/locale/new-catalog').write_text('new\n')
        self.assert_package_rejected('untracked package inputs: assets/locale/new-catalog')

    def test_tracked_symlink_is_rejected(self):
        (self.root / 'src/link.rs').symlink_to('main.rs')
        self.git('add', 'src/link.rs')
        self.git('commit', '-qm', 'tracked symlink')
        self.assert_package_rejected('requires regular tracked files')


if __name__ == '__main__':
    unittest.main()
