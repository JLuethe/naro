"""Production runners must refuse instrumented and extension builds."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
RUNNERS = ('terminal_resources.py', 'hostile_inputs.py')


class ProductionIdentityTests(unittest.TestCase):
    def test_extra_features_fail_before_editor_execution(self):
        for runner in RUNNERS:
            for tiny, features in ((False, 'test-hooks'), (False, 'credits'),
                                   (True, 'test-hooks,tiny'), (True, 'credits,tiny')):
                with self.subTest(runner=runner, features=features), tempfile.TemporaryDirectory() as directory:
                    fixture = Path(directory)
                    binary = fixture / 'fake-naro'
                    info = {'revision': 'test-revision', 'features': features}
                    binary.write_text('#!/usr/bin/env python3\n'
                                      'import json, os\n'
                                      f'print(json.dumps({info!r})) if os.environ.get("NARO_BUILD_INFO") == "1" '
                                      'else exit(77)\n')
                    binary.chmod(0o700)
                    command = [sys.executable, str(ROOT / 'tests/robustness' / runner),
                               '--binary', str(binary), '--expected-revision', 'test-revision',
                               '--out', str(fixture / 'out')]
                    if tiny:
                        command.append('--tiny')
                    result = subprocess.run(command, capture_output=True, text=True, timeout=10)
                    self.assertNotEqual(result.returncode, 0, command)
                    self.assertIn('binary feature profile differs', result.stderr)
                    self.assertFalse((fixture / 'out/report.json').exists())


if __name__ == '__main__':
    unittest.main()
