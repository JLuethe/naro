#!/usr/bin/env python3
"""Accounting regressions: missing work and failing reference cannot pass."""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent))
import differential as d


class Accounting(unittest.TestCase):
    def setUp(self):
        self.case = {'id': 'TEST-ACCOUNTING'}
        self.record = {'scenario': self.case['id'], 'binary_sha256': 'hash', 'steps_ok': True, 'checks': []}
        self.hashes = {'reference': 'hash', 'candidate': 'hash'}

    def inspect(self, r, c):
        with patch.object(d, 'classify', return_value={'accepted': True, 'classification': 'raw_exact'}):
            return d.inspect_pair(r, c, self.case, self.hashes, 'default')

    def test_missing_not_pass(self):
        for r, c in [(None, self.record), (self.record, None), (None, None)]:
            result = self.inspect(r, c)
            self.assertFalse(result['accepted'])
            self.assertEqual(result['classification'], 'missing_evidence')

    def test_failed_reference_not_pass(self):
        for key, value in [('steps_ok', False), ('checks', [{'pass': False}])]:
            r = {**self.record, key: value}
            result = self.inspect(r, self.record)
            self.assertFalse(result['accepted'])
            self.assertEqual(result['classification'], 'reference_failure')

    def test_failed_candidate_not_pass(self):
        result = self.inspect(self.record, {**self.record, 'steps_ok': False})
        self.assertFalse(result['accepted'])
        self.assertEqual(result['classification'], 'candidate_execution_or_assertion_failure')

    def test_artifact_substitution_not_pass(self):
        result = self.inspect(self.record, {**self.record, 'binary_sha256': 'other'})
        self.assertFalse(result['accepted'])
        self.assertEqual(result['classification'], 'infrastructure_failure')

    def test_equal_noop_history_is_rejected(self):
        self.case = {'id': 'TEST-FEAT-015'}
        r = {**self.record, 'scenario': self.case['id']}
        result = self.inspect(r, r)
        self.assertFalse(result['accepted'])
        self.assertTrue(result['coverage_problems']['reference'])
        self.assertTrue(result['coverage_problems']['candidate'])

    def test_private_history_input_relocation(self):
        case = next(c for c in d.inventory('default')[0]['baseline'] if c['id'] == 'TEST-FEAT-015')
        old = copy.deepcopy(case)
        adapted = d.private_case(case, Path('/tmp/owned-m15'))
        value = adapted['files']['home/.local/share/nano/filepos_history']['text']
        self.assertIn('/tmp/owned-m15/TEST-FEAT-015/fx/work/f.txt 40 2', value)
        self.assertEqual(case, old)
        broken = copy.deepcopy(case)
        broken['files']['home/.local/share/nano/filepos_history']['text'] = 'changed'
        with self.assertRaises(ValueError):
            d.private_case(broken, Path('/tmp/owned-m15'))

    def test_locale_warning_is_not_success_even_with_zero_status(self):
        outcome = type('Outcome', (), {'returncode': 0, 'stdout': 'ANSI_X3.4-1968\n', 'stderr': 'Cannot set locale'})()
        d.locale_probe.cache_clear()
        with patch.object(d.subprocess, 'run', return_value=outcome):
            self.assertFalse(d.case_locale({'lang': 'missing.UTF-8'})['available'])
        d.locale_probe.cache_clear()

    def test_profile_inventory(self):
        default, excluded = d.inventory('default')
        tiny, _ = d.inventory('tiny')
        self.assertEqual(sum(map(len, default.values())), 593)
        self.assertEqual(sum(map(len, tiny.values())), 202)
        self.assertEqual(len(default['baseline']), 303)
        self.assertEqual(len(tiny['baseline']), 1)
        self.assertEqual(sum('fixture safety' in reason for reason in excluded.values()), 7)
        self.assertFalse(set(default) & {'panic', 'tiny'})


if __name__ == '__main__':
    unittest.main()
