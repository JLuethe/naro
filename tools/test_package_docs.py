"""Installed documentation must work without the source checkout."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import package


class InstalledDocumentation(unittest.TestCase):
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
