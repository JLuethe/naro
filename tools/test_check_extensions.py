#!/usr/bin/env python3
"""Recovery extension checks reject absent, empty and unrelated evidence."""
import base64
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import shlex
import tempfile
import unittest
from unittest.mock import patch

import check_extensions as extensions
from candidate_expectations import candidate_case, case_sha256
from nanoharness import Keys, Run, REFERENCE_COMMIT


class ExtensionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.binary = self.root / 'hooks.bin'
        self.binary.write_bytes(b'owned test-hook executable fixture')
        self.runs = self.root / 'runs'
        self.cases = json.loads((extensions.ROOT / 'tests/follow-up/scenarios/panic.json').read_text())
        for original in self.cases:
            case = candidate_case(original)
            folder = self.runs / case['id']
            folder.mkdir(parents=True)
            raw = b'owned terminal fixture'
            (folder / 'raw-output.bin').write_bytes(raw)
            fixture = {}
            for name, value in case['expect'].get('files', {}).items():
                if value is not None:
                    fixture[name] = dict(value)
                    if 'text' in value:
                        fixture[name]['b64'] = base64.b64encode(value['text'].encode()).decode()
            if 'NAMELESS' in case['id']:
                fixture['work/nano.123.save'] = {'b64': 'WAo=', 'mode': '0o600'}
            keys = Keys(case.get('term', 'tmux-256color'))
            inputs = []
            for step in case['steps']:
                if 'keys' in step:
                    data = b''.join(keys.encode(key) for key in step['keys'])
                elif 'text' in step:
                    data = step['text'].encode()
                else:
                    continue
                inputs.append({'hex': data.hex()})
            run = dict(scenario=case['id'], scenario_sha256=case_sha256(case),
                       reference_commit=REFERENCE_COMMIT,
                       binary_sha256=hashlib.sha256(self.binary.read_bytes()).hexdigest(),
                       steps_ok=True, step_checks=[{'step': i, 'pass': True} for i in range(len(case['steps']))],
                       inputs=inputs, fixture=fixture, exit_status=1,
                       stderr=case['expect']['stderr_contains'],
                       trace_final_modes=case['expect']['trace_final_modes'],
                       cwd=str(folder / 'fx/work'), raw_output_bytes=len(raw),
                       raw_output_sha256=hashlib.sha256(raw).hexdigest())
            runner = Run(case, '/unused', '/unused')
            runner.root = str(folder / 'fx')
            run['checks'] = runner.check(run)
            (folder / 'result.json').write_text(json.dumps(run))

    def checks(self):
        return extensions.recovery_checks(self.runs, self.binary)

    def test_complete_evidence_passes(self):
        checks = self.checks()
        self.assertEqual(set(checks), {case['id'] for case in self.cases})
        self.assertTrue(all(check['pass'] for check in checks.values()), checks)

    def test_missing_required_record_fails(self):
        case = self.cases[0]['id']
        (self.runs / case / 'result.json').unlink()
        self.assertFalse(self.checks()[case]['pass'])

    def test_named_record_requires_real_assertions_and_identity(self):
        case = self.cases[0]['id']
        path = self.runs / case / 'result.json'
        original = json.loads(path.read_text())
        mutations = {
            'empty checks': lambda r: r.update(checks=[]),
            'unrelated checks': lambda r: r.update(checks=[{'check': 'unrelated', 'pass': True}]),
            'scenario': lambda r: r.update(scenario='TEST-UNRELATED'),
            'scenario inputs': lambda r: r.update(scenario_sha256='0' * 64),
            'artifact': lambda r: r.update(binary_sha256='0' * 64),
            'failed steps': lambda r: r.update(steps_ok=False),
            'truthy steps': lambda r: r.update(steps_ok=1),
            'incomplete steps': lambda r: r.update(step_checks=[]),
            'wrong bytes': lambda r: r['fixture']['work/f.txt.save'].update(text='wrong'),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                run = copy.deepcopy(original)
                mutate(run)
                path.write_text(json.dumps(run))
                self.assertFalse(self.checks()[case]['pass'])

    def test_raw_terminal_artifact_is_required(self):
        case = self.cases[0]['id']
        (self.runs / case / 'raw-output.bin').write_bytes(b'changed')
        self.assertFalse(self.checks()[case]['pass'])

    def test_recovery_requires_expected_binary(self):
        args = ['--default', str(self.binary), '--credits', str(self.binary),
                '--panic-runs', str(self.runs), '--out', str(self.root / 'out')]
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as outcome:
            extensions.main(args)
        self.assertEqual(outcome.exception.code, 2)

    def test_ci_workflow_supplies_matching_recovery_binary(self):
        commands = [shlex.split(line.strip()) for line in
                    (extensions.ROOT / '.github/workflows/rust.yml').read_text().splitlines()
                    if line.strip().startswith('python3 ')]
        extension_commands = [command for command in commands
                              if command[1] == 'tools/check_extensions.py']
        self.assertEqual(len(extension_commands), 1)
        argv = extension_commands[0][2:]
        panic_commands = [command for command in commands
                          if command[1] == 'spec/tools/nanoharness.py'
                          and 'tests/follow-up/scenarios/panic.json' in command]
        self.assertEqual(len(panic_commands), 1)
        panic = panic_commands[0]
        self.assertNotIn('--credits-only', argv)
        self.assertIn('--panic-binary', argv)
        self.assertIn('--panic-runs', argv)
        self.assertEqual(argv[argv.index('--panic-binary') + 1],
                         panic[panic.index('--binary') + 1].removeprefix('$PWD/'))
        self.assertEqual(argv[argv.index('--panic-runs') + 1],
                         panic[panic.index('--out') + 1])
        for option, path in [('--default', self.binary), ('--credits', self.binary),
                             ('--panic-runs', self.runs), ('--panic-binary', self.binary),
                             ('--out', self.root / 'out')]:
            argv[argv.index(option) + 1] = str(path)
        run = dict(steps_ok=True, checks=[{'pass': True}],
                   stdout=(extensions.ROOT / 'CREDITS.md').read_text(), stderr='',
                   fixture={}, initial_fixture={}, bracketed_paste_set=0,
                   bracketed_paste_reset=0, trace_final_modes={'alternate_screen': False})
        with patch.object(extensions.h.Run, 'execute', return_value=run), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(extensions.main(argv), 0)
        report = json.loads((self.root / 'out/report.json').read_text())
        self.assertEqual(set(report), {case['id'] for case in self.cases}
                         | {'default', 'credits', 'production-no-panic-hook'})
        self.assertTrue(all(check['pass'] for check in report.values()), report)

    def test_explicit_credits_only_omits_recovery(self):
        run = dict(steps_ok=True, checks=[{'pass': True}],
                   stdout=(extensions.ROOT / 'CREDITS.md').read_text(), stderr='',
                   fixture={}, initial_fixture={}, bracketed_paste_set=0,
                   bracketed_paste_reset=0, trace_final_modes={'alternate_screen': False})
        args = ['--default', str(self.binary), '--credits', str(self.binary),
                '--credits-only', '--out', str(self.root / 'out')]
        with patch.object(extensions.h.Run, 'execute', return_value=run), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(extensions.main(args), 0)
        report = json.loads((self.root / 'out/report.json').read_text())
        self.assertEqual(set(report), {'default', 'credits', 'production-no-panic-hook'})


if __name__ == '__main__':
    unittest.main()
