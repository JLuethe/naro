#!/usr/bin/env python3
"""NARO identity policy tests; no reference data or recorded grids are rewritten."""
import base64
import copy
import json
from pathlib import Path
import unittest

import candidate_expectations as policy
import nanoharness as h
from compare_runs import compare


class IdentityTests(unittest.TestCase):
    def test_all_overrides_bind_to_untouched_source_cases(self):
        data = json.loads(policy.OVERLAYS.read_text())
        self.assertGreater(len(data['cases']), 50)
        for tid, override in data['cases'].items():
            cases = json.loads((policy.ROOT / override['source']).read_text())
            original = next(c for c in cases if c['id'] == tid)
            before = copy.deepcopy(original)
            selected = policy.candidate_case(original)
            self.assertEqual(original, before)
            self.assertEqual(override['reference_case_sha256'], policy.case_sha256(original))
            # Identity overlays preserve data, exits and every nonidentity
            # screen assertion. Panic text is an explicitly named identity.
            ref = original.get('candidate_expect', original.get('expect', {}))
            self.assertEqual(set(ref), set(selected['expect']), tid)
            self.assertEqual(len(ref.get('screen', [])), len(selected['expect'].get('screen', [])), tid)
            for key in ref:
                if key not in ('screen', 'stderr_contains'):
                    self.assertEqual(selected['expect'][key], ref[key], (tid, key))
            for a, b in zip(ref.get('screen', []), selected['expect'].get('screen', [])):
                if 'GNU nano' not in json.dumps(a):
                    self.assertEqual(a, b, tid)
            self.assertEqual(selected['args'] if 'args' in selected else [], original.get('args', []))
            self.assertEqual(len(original.get('steps', [])), len(selected.get('steps', [])), tid)
            for a, b in zip(original.get('steps', []), selected.get('steps', [])):
                if a != b:
                    self.assertEqual(a, {'wait': {'text': 'Welcome to nano'}}, tid)
                    self.assertEqual(b, {'wait': {'text': 'Welcome to NARO'}}, tid)
            if ref.get('stderr_contains') != selected['expect'].get('stderr_contains'):
                self.assertTrue(ref['stderr_contains'].startswith('Sorry! Nano crashed!'), tid)
                self.assertEqual(selected['expect']['stderr_contains'],
                                 ref['stderr_contains'].replace('Sorry! Nano crashed!', 'Sorry! NARO crashed!', 1), tid)

    def fixture(self):
        reference = {'id': 'TEST-IDENTITY-NEGATIVE', 'steps': [], 'expect': {
            'exit_status': 0, 'files': {'work/f.txt': {'hex': '6f6b0a'}},
            'screen': [{'snapshot': 's', 'row': 0,
                        'equals': policy.title_row(80, 'notes.txt', 'Modified', 'GNU nano 9.3')},
                       {'snapshot': 's', 'cursor': {'x': 3, 'y': 1, 'visible': True}},
                       {'snapshot': 's', 'attr_at': [0, 2, 'reverse=1']}]}}
        expected = copy.deepcopy(reference['expect'])
        expected['screen'][0]['equals'] = policy.title_row(80, 'notes.txt', 'Modified')
        overlays = {'policy': policy.POLICY, 'package_version': '0.1.1', 'cases': {
            reference['id']: {'reference_case_sha256': policy.case_sha256(reference), 'expect': expected}}}
        case = policy.candidate_case(reference, overlays)
        result = {'exit_status': 0, 'fixture': {'work/f.txt': {'b64': base64.b64encode(b'ok\n').decode()}},
                  'snapshots': {'s': {'rows': [{'text': expected['screen'][0]['equals'],
                    'attrs': [{'start': 0, 'end': 80, 'attr': 'reverse=1'}]}],
                    'cursor': {'x': 3, 'y': 1, 'visible': True}}}}
        return reference, overlays, case, result

    def test_positive_and_orthogonal_negative_controls(self):
        _, _, case, good = self.fixture()
        runner = h.Run(case, '/unused', '/unused')
        self.assertTrue(all(c['pass'] for c in runner.check(good)))
        changes = {
            'filename': lambda r: r['snapshots']['s']['rows'][0].update(text=policy.title_row(80, 'wrong.txt', 'Modified')),
            'state': lambda r: r['snapshots']['s']['rows'][0].update(text=policy.title_row(80, 'notes.txt')),
            'attributes': lambda r: r['snapshots']['s']['rows'][0].update(attrs=[]),
            'cursor': lambda r: r['snapshots']['s']['cursor'].update(x=4),
            'saved-bytes': lambda r: r['fixture']['work/f.txt'].update(b64=base64.b64encode(b'wrong\n').decode()),
            'exit': lambda r: r.update(exit_status=1),
            'old-brand': lambda r: r['snapshots']['s']['rows'][0].update(text=policy.title_row(80, 'notes.txt', 'Modified', 'GNU nano 9.3')),
        }
        for name, change in changes.items():
            broken = copy.deepcopy(good); change(broken)
            self.assertTrue(any(not c['pass'] for c in runner.check(broken)), name)

    def test_stale_case_and_version_are_rejected(self):
        reference, overlays, _, _ = self.fixture()
        reference['steps'].append({'text': 'X'})
        with self.assertRaisesRegex(ValueError, 'stale'):
            policy.candidate_case(reference, overlays)
        overlays['package_version'] = '0.0.0'
        with self.assertRaisesRegex(ValueError, 'version'):
            policy.candidate_case(reference, overlays)

    def test_title_centering_and_boundary_decisions_are_explicit(self):
        for width in [40, 80, 120]:
            for state in ['', 'Modified', 'View']:
                old = policy.title_row(width, 'notes.txt', state, 'GNU nano 9.3')
                new = policy.title_row(width, 'notes.txt', state)
                self.assertEqual(new.index('notes.txt'), old.index('notes.txt') - 1)
                if state:
                    self.assertEqual(new.index(state), old.index(state))
                self.assertEqual(policy.candidate_title(old, width), new)
        # At the exact fit boundary NARO's shorter identity is visible while
        # the longer nano identity is hidden. This is not a row mask.
        self.assertIn('NARO', policy.title_row(33, 'notes.txt'))
        self.assertNotIn('GNU nano', policy.title_row(33, 'notes.txt', label='GNU nano 9.3'))
        self.assertNotIn('NARO', policy.title_row(32, 'notes.txt'))
        with self.assertRaises(ValueError):
            policy.candidate_title('  GNU nano 9.3 bad/unreviewed-layout')

    def test_cli_projection_is_limited_to_expected_identity(self):
        self.assertEqual(policy.expected_cli_output('unchanged filename nano\n'), 'unchanged filename nano\n')
        self.assertTrue(policy.expected_cli_output('Usage: nano [OPTIONS]\n').startswith('Usage: naro '))
        old = ' GNU nano, version 9.3\n Compiled options: --enable-tiny --enable-utf8\n'
        self.assertIn('NARO, version 0.1.1', policy.expected_cli_output(old, 'tiny'))
        with self.assertRaises(ValueError):
            policy.expected_cli_output(old + 'unreviewed line\n', 'tiny')

    def test_raw_comparator_still_exposes_identity_and_other_differences(self):
        baseline = json.loads((policy.ROOT / 'spec/evidence/runs/TEST-SMOKE-001/result.json').read_text())
        candidate = copy.deepcopy(baseline)
        candidate['snapshots']['start']['rows'][0]['text'] = policy.title_row(80, 'notes.txt')
        self.assertIn('snapshot.start.row0.text', {d['field'] for d in compare(baseline, candidate)})
        candidate['snapshots']['start']['cursor']['x'] += 1
        self.assertIn('snapshot.start.cursor', {d['field'] for d in compare(baseline, candidate)})


if __name__ == '__main__':
    unittest.main()
