"""Installed documentation must work without the source checkout."""
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

import package


class InstalledDocumentation(unittest.TestCase):
    def test_current_status_matches_package_version(self):
        version = tomllib.loads((package.ROOT / 'Cargo.toml').read_text())['package']['version']
        text = (package.ROOT / 'IMPLEMENTATION.md').read_text()
        package.validate_status_document(text, version)
        package.validate_status_document(package.installed_document(text, 'a' * 40), version)

    def test_stale_status_version_rejected(self):
        with self.assertRaisesRegex(ValueError, 'current NARO 0.1.2'):
            package.validate_status_document('NARO 0.1.1 is an experimental port.\n', '0.1.2')

    def test_missing_or_conflicting_current_identity_rejected(self):
        for text in ('No version declared.\n',
                     'NARO 0.1.2 is a port.\nNARO 0.1.1 candidate is current.\n'):
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, 'current NARO 0.1.2'):
                package.validate_status_document(text, '0.1.2')

    def test_stale_candidate_hash_rejected_even_with_current_version(self):
        for digest in ('a' * 40, 'b' * 64):
            with self.subTest(digest=digest), self.assertRaisesRegex(ValueError, 'candidate hashes'):
                package.validate_status_document('NARO 0.1.2 is an experimental port.\n'
                                                 f'Production commit: `{digest}`.\n', '0.1.2')

    def test_pinned_reference_and_explicit_history_allowed(self):
        package.validate_status_document('NARO 0.1.2 is an experimental port.\n'
                                         f'Reference: `{package.REFERENCE_COMMIT}`.\n'
                                         '## Historical 0.1.1 qualification\n'
                                         'NARO 0.1.1 receipts apply only to their named artifacts.\n',
                                         '0.1.2')

    def test_shipped_external_and_anchor_links_stay_usable(self):
        text = '[read](README.md#scope) [site](https://example.com) [here](#intro)'
        self.assertEqual(package.installed_document(text, 'abc'), text)

    def test_repository_file_and_directory_are_pinned(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(package, 'ROOT', Path(folder)):
            (Path(folder) / 'spec').mkdir()
            (Path(folder) / 'spec/info.md').write_text('info')
            result = package.installed_document('[x](spec/info.md#section) [y](spec)', 'abc123')
            self.assertEqual(result, '[x](https://github.com/JLuethe/naro/blob/abc123/spec/info.md#section) '
                             '[y](https://github.com/JLuethe/naro/tree/abc123/spec)')

    def test_missing_and_escaping_targets_rejected(self):
        for link in ('missing-file.md', '../outside.md'):
            with self.subTest(link=link), self.assertRaises(ValueError):
                package.installed_document(f'[x]({link})', 'abc')


if __name__ == '__main__':
    unittest.main()
