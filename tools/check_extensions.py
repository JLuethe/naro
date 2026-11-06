#!/usr/bin/env python3
"""Check credits in normal and legacy-feature builds plus recovery instrumentation."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'spec/tools'))
import nanoharness as h
from release_gate_evidence import recording_problems


def recovery_checks(directory, binary):
    """Require the complete panic inventory and recheck its artifact-bound evidence."""
    cases = json.loads((ROOT / 'tests/follow-up/scenarios/panic.json').read_text())
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    checks = {}
    for case in cases:
        path = directory / case['id'] / 'result.json'
        problems = []
        run = {}
        try:
            run = json.loads(path.read_text())
            problems = recording_problems(run, case, 'candidate', digest, path.parent)
            if not isinstance(run.get('checks'), list) or not run['checks']:
                problems.append('recovery recording has no meaningful assertions')
            if 'NAMELESS' in case['id']:
                saves = [value for name, value in run['fixture'].items()
                         if re.fullmatch(r'work/nano\.\d+\.save', name)]
                if (len(saves) != 1 or saves[0]['mode'] != '0o600'
                        or base64.b64decode(saves[0]['b64'], validate=True) != b'X\n'):
                    problems.append('nameless recovery bytes/mode mismatch')
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
            problems.append('invalid or missing recovery recording: ' + str(error))
        checks[case['id']] = {'pass': not problems,
                              'binary_sha256': run.get('binary_sha256') if isinstance(run, dict) else None,
                              'expected_binary_sha256': digest, 'problems': problems}
    return checks


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--default', type=Path, required=True)
    parser.add_argument('--credits', type=Path, required=True)
    parser.add_argument('--panic-runs', type=Path)
    parser.add_argument('--panic-binary', type=Path, help='expected test-hook executable for recovery recordings')
    parser.add_argument('--credits-only', action='store_true', help='explicitly omit recovery qualification')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    if not args.credits_only:
        if args.panic_runs is None or not args.panic_runs.is_dir():
            parser.error('recovery recordings are required; use --credits-only for a credits-only check')
        if args.panic_binary is None or not args.panic_binary.is_file():
            parser.error('--panic-binary must name the expected recovery test-hook executable')
    args.out.mkdir(parents=True, exist_ok=False)
    checks = {} if args.credits_only else recovery_checks(args.panic_runs, args.panic_binary)
    for name, binary in [('default', args.default), ('credits', args.credits)]:
        scenario = dict(id='TEST-NEXT-CREDITS-002-' + name, args=['--credits'], stdin='',
                        stdout_redirect=True, hold_tty=True, steps=[{'wait_exit': 5}],
                        expect={'exit_status': 0})
        run = h.Run(scenario, str(binary.resolve()), str(args.out / name)).execute()
        ok = run['steps_ok'] is True and bool(run['checks']) and all(c['pass'] is True for c in run['checks'])
        ok = (ok and run['stdout'] == (ROOT / 'CREDITS.md').read_text() and run['stderr'] == ''
              and run['fixture'] == run['initial_fixture']
              and run['bracketed_paste_set'] == run['bracketed_paste_reset'] == 0
              and not run['trace_final_modes']['alternate_screen'])
        checks[name] = {'pass': ok, 'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest()}
    checks['production-no-panic-hook'] = {'pass': b'NARO_TEST_PANIC_DIR' not in args.default.read_bytes()}
    (args.out / 'report.json').write_text(json.dumps(checks, indent=2) + '\n')
    print(json.dumps(checks, indent=2))
    return int(any(not check['pass'] for check in checks.values()))


if __name__ == '__main__':
    raise SystemExit(main())
