#!/usr/bin/env python3
"""Exercise complete exact-match evidence and reject tampered release bundles."""
import copy
import io
import json
import runpy
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import check_closure_regressions as closure
import check_wrap_undo as wrap
from test_check_wrap_undo import valid_artifacts


class ClosureRegressionsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.scenarios = self.root / 'tests/follow-up/scenarios'
        self.scenarios.mkdir(parents=True)
        self.source = wrap.source_fingerprint()
        self.candidate = wrap.sha256(b'candidate fixture')
        self.reference = wrap.sha256(b'reference fixture')
        self.make_bundle(self.root / 'runs')

    def make_bundle(self, base):
        for suite, count in closure.SUITES.items():
            cases = [{
                'id': f'TEST-{suite.upper()}-{i:03}-FIXTURE',
                'files': {'work/f.txt': {'hex': '0a'}},
                'steps': [{'text': 'ok'}, {'snapshot': 'edited'},
                          {'capture_file': 'work/f.txt'}, {'wait_exit': 5}],
                'expect': {'exit_status': 0, 'temp_empty': True,
                           'files': {'work/f.txt': {'hex': '6f6b0a'}}},
            } for i in range(count)]
            (self.scenarios / (suite + '.json')).write_text(json.dumps(cases))
            directory = base / suite
            directory.mkdir(parents=True)
            self.write(directory / 'report.json', valid_artifacts(directory, cases))

    @staticmethod
    def write(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))

    def problems(self, suite='filter', candidate=None, reference=None):
        return closure.validate_suite(
            self.root / 'runs' / suite, suite, candidate or self.candidate,
            self.source, reference or self.reference, self.scenarios,
        )[1]

    def test_complete_bundles_pass(self):
        for suite in closure.SUITES:
            with self.subTest(suite=suite):
                self.assertEqual(self.problems(suite), [])

    def test_report_tampering_is_rejected(self):
        path = self.root / 'runs/filter/report.json'
        original = json.loads(path.read_text())
        tid = next(iter(original['results']))
        mutations = {
            'candidate identity': lambda r: r.update(candidate_sha256='0' * 64),
            'reference identity': lambda r: r.update(reference_sha256='0' * 64),
            'reference commit': lambda r: r.update(reference_commit='wrong'),
            'tools identity': lambda r: r.update(verification_sha256='0' * 64),
            'scenario identity': lambda r: r.update(scenario_sha256='0' * 64),
            'candidate failed': lambda r: r.update(candidate_status=1),
            'reference failed': lambda r: r.update(reference_status=1),
            'boolean status': lambda r: r.update(candidate_status=False),
            'missing scenario': lambda r: r['results'].pop(tid),
            'extra scenario': lambda r: r['results'].update(EXTRA=r['results'][tid]),
            'failed candidate assertion': lambda r: r['results'][tid].update(candidate_checks=False),
            'failed reference assertion': lambda r: r['results'][tid].update(reference_checks=False),
            'truthy assertion': lambda r: r['results'][tid].update(candidate_checks=1),
            'mismatch': lambda r: r['results'][tid].update(match=False),
            'unaccepted': lambda r: r['results'][tid].update(accepted=False),
            'deviation': lambda r: r['results'][tid].update(declared_deviation=True),
            'false summary': lambda r: r['summary'].update(matches=0),
            'wrong source': lambda r: r['candidate_build'].update(source_sha256='0' * 64),
            'instrumented build': lambda r: r['candidate_build'].update(features='test-hooks'),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                report = copy.deepcopy(original)
                mutate(report)
                self.write(path, report)
                self.assertTrue(self.problems(), name)
        self.write(path, original)

    def test_missing_and_malformed_reports_fail(self):
        path = self.root / 'runs/filter/report.json'
        path.unlink()
        self.assertTrue(self.problems())
        for data in ('{', 'null', '[]'):
            path.write_text(data)
            self.assertTrue(self.problems())

    def test_missing_artifacts_fail(self):
        directory = self.root / 'runs/filter'
        tid = next(iter(json.loads((directory / 'report.json').read_text())['results']))
        for name in ('candidate.bin', 'reference.bin', 'scenarios.json',
                     'candidate-scenarios.json', f'candidate/{tid}/result.json',
                     f'reference/{tid}/raw-output.bin'):
            with self.subTest(name=name):
                path = directory / name
                original = path.read_bytes()
                path.unlink()
                self.assertTrue(self.problems())
                path.write_bytes(original)

    def test_recordings_are_rechecked_not_just_report_flags(self):
        directory = self.root / 'runs/filter'
        tid = next(iter(json.loads((directory / 'report.json').read_text())['results']))
        path = directory / 'candidate' / tid / 'result.json'
        original = json.loads(path.read_text())
        mutations = {
            'incomplete steps': lambda r: r['step_checks'].pop(),
            'false assertion flag': lambda r: r['checks'][0].update({'pass':False}),
            'failed recomputed expectation': lambda r: r['fixture']['work/f.txt'].update(b64='YmFkCg=='),
            'changed cursor': lambda r: r['snapshots']['edited']['cursor'].update(x=1),
            'missing snapshot': lambda r: r['snapshots'].clear(),
            'wrong executable': lambda r: r.update(binary_sha256='0' * 64),
            'wrong input': lambda r: r['inputs'][0].update(hex='00'),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                recording = copy.deepcopy(original)
                mutate(recording)
                self.write(path, recording)
                self.assertTrue(self.problems(), name)
        self.write(path, original)

    def test_wrong_closure_binary_and_environment_reference_fail(self):
        self.assertTrue(self.problems(candidate='1' * 64))
        self.assertTrue(self.problems(reference='1' * 64))

    def test_duplicate_scenario_manifest_fails(self):
        path = self.scenarios / 'filter.json'
        cases = json.loads(path.read_text())
        cases[-1] = cases[0]
        self.write(path, cases)
        self.assertTrue(self.problems())

    def test_cli_requires_all_three_suites(self):
        base = self.root / 'runs'
        binary = base / 'filter/candidate.bin'
        reference = base / 'filter/reference.bin'
        argv = ['checker', '--base', str(base), '--binary', str(binary), '--reference', str(reference)]
        with patch.object(closure, 'ROOT', self.root), patch.object(sys, 'argv', argv), redirect_stdout(io.StringIO()):
            self.assertEqual(closure.main(), 0)
            (base / 'release-fixes/report.json').unlink()
            self.assertEqual(closure.main(), 1)

    def test_final_collector_requires_new_suites_for_both_environments(self):
        """Run the real collector with synthetic historical and new evidence."""
        host, ubuntu = self.root / 'host', self.root / 'ubuntu'
        self.make_bundle(host)
        self.make_bundle(ubuntu)
        build = {'source_sha256': self.source, 'features': ''}
        historical = ['tools','edges','environments','supplement','backup','fifo-eof','signal-SIGTERM','signal-SIGHUP','vt-ioctl','root','root-nohome-tilde']
        checkpoint = {'binary_sha256': self.candidate, 'reference_sha256': self.reference,
                      'build': build, 'state': 'complete', 'active': None,
                      'checks': {name: {'status': 0} for name in [*closure.SUITES, 'closure-regressions']}}
        self.write(host / 'checkpoint.json', checkpoint)
        package = self.root / 'package'
        self.write(package / 'build.json', {'binary_sha256': self.candidate,
                   'compiled_build': build, 'reference_commit': wrap.REFERENCE_COMMIT})
        (package / 'SHA256SUMS').write_text('synthetic package checksum fixture\n')
        for label, base in [('host', host), ('ubuntu', ubuntu)]:
            (base / 'naro').write_bytes(b'candidate fixture')
            (base / 'reference.bin').write_bytes(b'reference fixture')
            (base / 'complete').write_text('completed')
            self.write(base / ('terminal' if label == 'host' else 'candidate') / 'report.json',
                       {'binary_sha256': self.candidate, 'summary': {'recorded':303,'full_matches':301,'files_matches':302,'skipped':6}, 'worker_statuses':[0]})
            for suite in historical:
                cases = json.loads((wrap.ROOT / f'tests/follow-up/scenarios/{suite}.json').read_text())
                issue = 'Q-TOOL-001' if suite.startswith('signal-') else 'Q-ROOT-NOHOME-001' if suite == 'root-nohome-tilde' else None
                self.write(base / suite / 'report.json', {
                    'candidate_sha256': self.candidate, 'candidate_build': build,
                    'candidate_status':0, 'reference_status':0,
                    'results': {c['id']: {'accepted':True,'reference_checks':True,'candidate_checks':True,'match':issue is None,'deviation_id':issue} for c in cases}})
            self.write(base / 'extras/report.json', {'candidate_sha256':self.candidate,
                       'cli': {str(i):{'pass':True} for i in range(38)},
                       'regex': {'all':{'cases':162,'pass':True}},
                       'safety': {'a':{'pass':True},'b':{'pass':True}}})
            self.write(base / 'large/report.json', {'binary_sha256':self.candidate,'results':{'1MiB':{'pass':True},'10MiB':{'pass':True}}})
            for i in range(3):
                self.write(base / f'panic/TEST-{i}/result.json', {'binary_sha256':self.candidate,'steps_ok':True,'checks':[{'pass':True}]})
            self.write(base / 'package-check/report.json', {'binary_sha256':self.candidate,'checks':[{'pass':True}]*15})
        self.write(host / 'extensions/report.json', {'default':{'binary_sha256':self.candidate,'pass':True}, **{str(i):{'pass':True} for i in range(5)}})
        for label in ('host', 'ubuntu'):
            vm = self.root / ('vm-' + label)
            self.write(vm / 'report.json', {'reference_commit':wrap.REFERENCE_COMMIT,
                       'results':{str(i):{'match':True,'differences':[],'candidate_sha256':self.candidate} for i in range(19)},
                       'guest':{'info':{'vt_state':[1],'device':'/dev/tty1'}}})
            self.write(vm / 'vm-provenance.json', {'fixture':True})
        self.write(self.root / 'transport/report.json', {'checks':dict.fromkeys(map(str,range(6)),True)})
        args = {'host':host,'ubuntu':ubuntu,'package':package,
                'package-check':ubuntu/'package-check','transport':self.root/'transport',
                'vm-host':self.root/'vm-host','vm-ubuntu':self.root/'vm-ubuntu'}

        def collect(name, expected):
            out = self.root / name
            argv = ['collector', *[v for k,p in args.items() for v in ('--'+k,str(p))], '--out',str(out)]
            with patch.object(closure,'ROOT',self.root), patch.object(wrap,'REFERENCE_SHA256',self.reference), patch.object(sys,'argv',argv), redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as result:
                    runpy.run_path(str(wrap.ROOT/'tools/collect_closure.py'),run_name='__main__')
            self.assertEqual(result.exception.code, expected)
            gate = json.loads((out/'gate.json').read_text())
            self.assertEqual(gate['pass'], expected == 0)
            self.assertEqual(gate['required_exact_regressions'], closure.SUITES)

        collect('valid', 0)
        for label, base in [('host', host), ('ubuntu', ubuntu)]:
            for suite in closure.SUITES:
                path = base / suite / 'report.json'
                data = path.read_bytes()
                path.unlink()
                collect(label+'-missing-'+suite, 1)
                path.write_bytes(data)
        checkpoint['checks'].pop('release-fixes')
        self.write(host / 'checkpoint.json',checkpoint)
        collect('missing-command-status',1)


if __name__ == '__main__':
    unittest.main()
