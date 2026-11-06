#!/usr/bin/env python3
"""Measure frozen executables without changing their bytes or file identity."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MeasureProfilesTest(unittest.TestCase):
    def test_readonly_sources_are_preserved_and_only_copies_are_writable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources, identities, builds = {}, {}, {}
            for name in ('full', 'tiny'):
                build = {'source_sha256': 'a' * 64, 'rustc': 'fixture compiler',
                         'features': '' if name == 'full' else 'tiny'}
                builds[name] = build
                source = root / (name + '.c')
                # The data survives strip and gives the full fixture a larger size.
                source.write_text('#include <stdio.h>\n'
                                  f'volatile char payload[{65536 if name == "full" else 1}]={{1}};\n'
                                  'int main(void) {\n'
                                  f' puts({json.dumps(json.dumps(build))});\n'
                                  ' return payload[0] != 1;\n}\n')
                binary = root / name
                command = ['cc', '-g', str(source), '-o', str(binary)]
                if name == 'full':
                    command += ['-Wl,--no-as-needed', '-l:libmagic.so.1']
                subprocess.run(command, check=True)
                binary.chmod(0o555)
                sources[name] = binary
                identities[name] = self.identity(binary)
            # Assert the permission at the actual strip boundary, including when
            # tests run as root (which can otherwise strip a mode-0555 file).
            shimdir = root / 'bin'
            shimdir.mkdir()
            strip = shimdir / 'strip'
            strip.write_text('#!' + sys.executable + '\n'
                             'import os, stat, sys\n'
                             'from pathlib import Path\n'
                             'binary = Path(sys.argv[-1])\n'
                             'assert binary.stat().st_mode & stat.S_IWUSR\n'
                             'assert str(binary) not in os.environ["FROZEN_INPUTS"].split(os.pathsep)\n'
                             f'os.execv({shutil.which("strip")!r}, ["strip", *sys.argv[1:]])\n')
            strip.chmod(0o755)
            output = root / 'report'
            env = {**os.environ, 'NANOSPEC_WORK': str(root / 'fixtures'),
                   'PATH': str(shimdir) + os.pathsep + os.environ['PATH'],
                   'FROZEN_INPUTS': os.pathsep.join(str(p) for p in sources.values())}
            result = subprocess.run([sys.executable, str(ROOT / 'tools/measure_profiles.py'),
                                     '--full', str(sources['full']), '--tiny', str(sources['tiny']),
                                     '--out', str(output)], cwd=ROOT, env=env,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads((output / 'report.json').read_text())
            self.assertTrue(all(report['checks'].values()), report)
            for name, binary in sources.items():
                with self.subTest(profile=name):
                    self.assertEqual(self.identity(binary), identities[name])
                    profile = report['profiles'][name]
                    self.assertEqual(profile['build'], builds[name])
                    self.assertEqual(profile['sha256'], identities[name]['sha256'])
                    self.assertEqual(profile['bytes'], binary.stat().st_size)
                    self.assertLess(profile['stripped_bytes'], profile['bytes'])
                    self.assertNotEqual(profile['stripped_sha256'], profile['sha256'])
            copies = list((root / 'fixtures').glob('TEST-TINY-SIZE-*/fx/work/*'))
            self.assertEqual({p.name for p in copies}, {'full', 'tiny'})
            for copy in copies:
                self.assertEqual(stat.S_IMODE(copy.stat().st_mode), 0o755)
                self.assertNotEqual(copy.stat().st_ino, sources[copy.name].stat().st_ino)
                self.assertEqual(hashlib.sha256(copy.read_bytes()).hexdigest(),
                                 report['profiles'][copy.name]['stripped_sha256'])

    @staticmethod
    def identity(path):
        info = path.stat()
        return {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                **{key: getattr(info, key) for key in
                   ('st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_gid', 'st_size',
                    'st_mtime_ns', 'st_ctime_ns')}}


if __name__ == '__main__':
    unittest.main()
