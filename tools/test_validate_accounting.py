"""Exercise the runner's inventory accounting, independently of comparison policy."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class AccountingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ('tools', 'spec/tools', 'spec/evidence/scenarios', 'reference', 'out'):
            (self.root / directory).mkdir(parents=True)
        shutil.copy2(Path(__file__).with_name('validate.py'), self.root / 'tools/validate.py')
        # Comparison itself has its own extensive tests. These stubs isolate the
        # runner's responsibility to require every requested recording.
        (self.root / 'spec/tools/compare_runs.py').write_text('def compare(*args): return []\n')
        (self.root / 'spec/tools/identity_review.py').write_text(
            'def policy_identity(): return {}\n'
            'def classify(*args): return {"accepted": True}\n'
            'def summary_counts(results): return {"accepted": sum(r["accepted"] for r in results.values())}\n')
        self.case = {'id': 'TEST-ACCOUNTING-001', 'args': []}
        (self.root / 'spec/evidence/scenarios/example.json').write_text(json.dumps([self.case]))
        (self.root / 'out/naro').write_bytes(b'fixture binary; comparison-only never executes it')
        self.record('reference')
        self.record('out')

    def record(self, kind, **updates):
        path = self.root / kind / self.case['id'] / 'result.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'steps_ok': True, 'checks': [{'pass': True}], **updates}))

    def run_case(self, *arguments):
        result = subprocess.run(
            [sys.executable, str(self.root / 'tools/validate.py'), '--compare-only',
             '--out', str(self.root / 'out'), *arguments], capture_output=True, text=True,
            env={**os.environ, 'NARO_REFERENCE_RUNS': str(self.root / 'reference')})
        self.assertTrue((self.root / 'out/report.json').is_file(), result.stderr)
        return result, json.loads((self.root / 'out/report.json').read_text())

    def test_complete_inventory_passes(self):
        result, report = self.run_case()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report['summary']['accepted'], 1)

    def test_missing_reference_is_failure(self):
        (self.root / 'reference' / self.case['id'] / 'result.json').unlink()
        result, report = self.run_case()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(report['results'][self.case['id']]['accepted'])

    def test_missing_candidate_is_failure(self):
        (self.root / 'out' / self.case['id'] / 'result.json').unlink()
        result, report = self.run_case()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(report['results'][self.case['id']]['accepted'])

    def test_unknown_selection_cannot_pass_vacuously(self):
        result, report = self.run_case('--ids', 'TEST-NONEXISTENT')
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(report['infrastructure_errors'])
        self.assertEqual(report['summary']['accepted'], 0)

    def test_failed_assertion_is_failure(self):
        self.record('out', checks=[{'pass': False}])
        result, report = self.run_case()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(report['results'][self.case['id']]['accepted'])

    def test_failed_reference_assertion_is_failure(self):
        self.record('reference', checks=[{'pass': False}])
        result, report = self.run_case()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(report['results'][self.case['id']]['accepted'])


if __name__ == '__main__':
    unittest.main()
