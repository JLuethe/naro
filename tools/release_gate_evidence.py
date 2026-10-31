"""Versioned release evidence checks. Reopen observations; never trust acceptance flags."""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'spec/tools'))
from candidate_expectations import candidate_case, case_sha256
from compare_runs import fixture_root
from identity_review import classify, policy_identity, summary_counts
from nanoharness import Keys, Run

GATE_SCHEMA = 'naro-release-gate/v2'
CORPUS_EXCLUSIONS = frozenset({'TEST-CLI-035', 'TEST-CLI-032', 'TEST-BROWSE-003',
                              'TEST-CLI-025', 'TEST-CLI-033', 'TEST-KEY-007'})
CORPUS_DEVIATIONS = frozenset({'TEST-CLI-057', 'TEST-PROMPT-NUL-001'})
TOOL_DEVIATIONS = frozenset({'TEST-NEXT-TOOL-003-SIGTERM', 'TEST-NEXT-TOOL-003-SIGHUP'})
REFERENCE_COMMIT = '6ed285c3ec7a1d228def4d4e7021c6ba269f620c'


def read(path):
    return json.loads(Path(path).read_text())


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def same_json(left, right):
    # JSON equality must not coerce booleans to integers.
    return json.dumps(left, sort_keys=True, separators=(',', ':'), allow_nan=False) == json.dumps(right, sort_keys=True, separators=(',', ':'), allow_nan=False)


def classification_counts(results):
    results = list(results)
    return {'recorded': len(results),
            'raw_exact': sum(r['raw_exact'] for r in results),
            'identity_reviewed': sum(bool(r['accepted'] and r['identity_reviewed']
                                         and not r['declared_deviation']) for r in results),
            'declared_deviations': sum(bool(r['accepted'] and r['declared_deviation']) for r in results),
            'unexpected': sum(not r['accepted'] for r in results),
            'accepted': sum(r['accepted'] for r in results)}


def corpus_coverage_problems(run, tid):
    """Prove the seeded history probe restored its recorded GNU position.

    Its fixture contains a literal /tmp/nanospec-work path. A different work
    root makes both editors ignore that entry while still comparing equal.
    The retained GNU observation independently establishes cursor 1,11 on l40.
    """
    if tid != 'TEST-FEAT-015':
        return []
    screen = run.get('snapshots', {}).get('s0', {})
    problems = []
    if not same_json(screen.get('cursor'), {'x': 1, 'y': 11, 'visible': True}):
        problems.append('seeded position-history cursor was not restored; canonical fixture root required')
    rows = screen.get('rows', [])
    if len(rows) <= 11 or rows[11].get('text', '').rstrip() != 'l40':
        problems.append('seeded position-history probe did not reach line 40')
    return problems


def recording_problems(run, case, side, digest, directory):
    """Recompute assertions and bind fresh recordings to inputs and raw bytes."""
    problems = []
    selected = candidate_case(case) if side == 'candidate' else case
    for key, expected in [('scenario', case['id']), ('reference_commit', REFERENCE_COMMIT),
                          ('binary_sha256', digest), ('scenario_sha256', case_sha256(selected))]:
        if run.get(key) != expected:
            problems.append(side + ': ' + key + ' mismatch')
    if run.get('steps_ok') is not True:
        problems.append(side + ': steps failed or missing')
    steps = run.get('step_checks', [])
    if (len(steps) != len(selected['steps'])
            or any(s.get('step') != i or s.get('pass') is not True for i, s in enumerate(steps))):
        problems.append(side + ': incomplete/failed step checks')
    keys = Keys(selected.get('term', 'tmux-256color'))
    expected_inputs = []
    for step in selected['steps']:
        if 'keys' in step:
            data = b''.join(keys.encode(key) for key in step['keys'])
        elif 'text' in step:
            data = step['text'].encode()
        elif 'hex' in step:
            data = bytes.fromhex(step['hex'])
        elif 'paste' in step:
            data = b'\x1b[200~' + step['paste'].encode() + b'\x1b[201~'
        else:
            continue
        expected_inputs.append(data.hex())
    if not isinstance(run.get('inputs'), list) or [item.get('hex') for item in run['inputs']] != expected_inputs:
        problems.append(side + ': input bytes/order differ from source scenario')
    runner = Run(selected, '/unused', '/unused')
    runner.root = fixture_root(run)
    expected_checks = runner.check(run)
    if expected_checks != run.get('checks') or any(c['pass'] is not True for c in expected_checks):
        problems.append(side + ': recomputed assertions differ/fail')
    raw = Path(directory) / 'raw-output.bin'
    if not raw.is_file() or sha256(raw) != run.get('raw_output_sha256') or raw.stat().st_size != run.get('raw_output_bytes'):
        problems.append(side + ': raw terminal bytes/hash mismatch')
    problems.extend(side + ': ' + problem for problem in corpus_coverage_problems(run, case['id']))
    return problems


def validate_follow_up(directory, suite, candidate_sha256, source_sha256, reference_sha256,
                       allowed_deviations=None, portable_locale=False):
    """Validate historical/root suites with their exact source-case membership."""
    directory = Path(directory)
    report = read(directory / 'report.json')
    cases = [environment_case(case, portable_locale) for case in
             read(ROOT / 'tests/follow-up/scenarios' / (suite + '.json'))]
    problems, results = [], {}
    ids = {c['id'] for c in cases}
    if len(ids) != len(cases) or set(report.get('results', {})) != ids:
        problems.append('suite recording inventory mismatch')
    if report.get('identity_policy') != policy_identity():
        problems.append('suite identity policy mismatch')
    if (report.get('candidate_sha256') != candidate_sha256
            or report.get('reference_sha256') != reference_sha256
            or report.get('candidate_build', {}).get('source_sha256') != source_sha256
            or report.get('candidate_build', {}).get('features') != ''
            or report.get('candidate_status') != 0 or report.get('reference_status') != 0):
        problems.append('suite executable/source/status mismatch')
    for side, digest in [('reference', reference_sha256), ('candidate', candidate_sha256)]:
        if sha256(directory / (side + '.bin')) != digest:
            problems.append(side + ': frozen executable hash mismatch')
        folders = {p.parent.name for p in (directory / side).glob('TEST-*/result.json')}
        if folders != ids:
            problems.append(side + ': raw recording membership mismatch')
        expected_cases = [candidate_case(c) for c in cases] if side == 'candidate' else cases
        if read(directory / (side + '-scenarios.json')) != expected_cases:
            problems.append(side + ': scenario contents mismatch')
    if read(directory / 'scenarios.json') != cases:
        problems.append('frozen source scenarios mismatch')
    for case in cases:
        tid = case['id']
        pair = []
        for side, digest in [('reference', reference_sha256), ('candidate', candidate_sha256)]:
            folder = directory / side / tid
            run = read(folder / 'result.json')
            pair.append(run)
            problems.extend(tid + ': ' + p for p in recording_problems(run, case, side, digest, folder))
        result = classify(*pair, case_id=tid, case=case)
        results[tid] = result
        saved = report.get('results', {}).get(tid, {})
        if saved.get('match') is not result['raw_exact']:
            problems.append(tid + ': raw match alias differs from reopened comparison')
        if saved.get('reference_checks') is not True or saved.get('candidate_checks') is not True:
            problems.append(tid + ': reported assertions failed or missing')
        for key, value in result.items():
            if key not in saved or not same_json(saved[key], value):
                problems.append(tid + ': stored classification mismatch: ' + key)
        if not result['accepted']:
            problems.append(tid + ': unexpected differences')
        if result['declared_deviation'] and (allowed_deviations or {}).get(tid) != result['deviation_id']:
            problems.append(tid + ': unapproved declared deviation')
    observed = {tid: r['deviation_id'] for tid, r in results.items() if r['declared_deviation']}
    if observed != (allowed_deviations or {}):
        problems.append('required historical deviation inventory mismatch')
    expected_summary = {**summary_counts(results), 'matches': sum(r['raw_exact'] for r in results.values())}
    for key, value in expected_summary.items():
        if type(report.get('summary', {}).get(key)) is not int or report['summary'][key] != value:
            problems.append('suite summary differs from reopened records: ' + key)
    return report, classification_counts(results.values()), problems


def environment_case(case, portable_locale=False):
    """The established Ubuntu adaptation changes only an explicit locale path."""
    selected = copy.deepcopy(case)
    if portable_locale and selected.get('locpath'):
        selected['locpath'] = '/opt/nano-locales'
    return selected


def corpus_cases():
    cases = [case for path in sorted((ROOT / 'spec/evidence/scenarios').glob('*.json'))
             for case in read(path)]
    if (len(cases) != 309 or len({c['id'] for c in cases}) != 309
            or not CORPUS_EXCLUSIONS <= {c['id'] for c in cases}):
        raise ValueError('corpus must contain the fixed 309 unique source cases')
    return {c['id']: c for c in cases if c['id'] not in CORPUS_EXCLUSIONS}


def candidate_recording(directory, tid):
    directory = Path(directory)
    candidates = [directory / tid / 'result.json', *directory.glob('part-*/' + tid + '/result.json')]
    found = [p for p in candidates if p.is_file()]
    if len(found) != 1:
        raise ValueError(tid + ': missing or duplicate candidate recording')
    return found[0]


def validate_corpus(directory, candidate_sha256, reference_sha256, portable_locale=False):
    directory = Path(directory)
    report = read(directory / 'report.json')
    cases = {tid: environment_case(case, portable_locale) for tid, case in corpus_cases().items()}
    problems, results = [], {}
    if set(report.get('results', {})) != set(cases) or set(report.get('skipped', {})) != CORPUS_EXCLUSIONS:
        problems.append('terminal inventory must contain exactly 303 records and six fixed exclusions')
    if (report.get('identity_policy') != policy_identity()
            or report.get('binary_sha256') != candidate_sha256
            or not report.get('worker_statuses') or any(report['worker_statuses'])):
        problems.append('terminal policy/executable/worker status mismatch')
    if report.get('reference_runs_relative') != '../reference':
        problems.append('terminal reference location is not the canonical sibling directory')
    recorded_paths = [*directory.glob('TEST-*/result.json'), *directory.glob('part-*/TEST-*/result.json')]
    if len(recorded_paths) != 303 or {p.parent.name for p in recorded_paths} != set(cases):
        problems.append('terminal raw candidate recording membership mismatch')
    reference_runs = directory.parent / 'reference'
    if {p.parent.name for p in reference_runs.glob('TEST-*/result.json')} != set(cases):
        problems.append('fresh reference recording membership mismatch')
    inventory = read(reference_runs / 'inventory.json')
    if (inventory.get('expected') != 303 or inventory.get('recorded') != 303
            or inventory.get('missing') != [] or inventory.get('binary_sha256') != reference_sha256
            or not inventory.get('worker_statuses') or any(inventory['worker_statuses'])):
        problems.append('fresh environment reference inventory/provenance failed')
    files_matches = 0
    from compare_runs import compare
    for tid, case in cases.items():
        candidate_path = candidate_recording(directory, tid)
        reference_path = reference_runs / tid / 'result.json'
        pair = [read(reference_path), read(candidate_path)]
        for side, run, digest, path in zip(['reference', 'candidate'], pair,
                                         [reference_sha256, candidate_sha256],
                                         [reference_path, candidate_path]):
            problems.extend(tid + ': ' + p for p in recording_problems(run, case, side, digest, path.parent))
        result = classify(*pair, case_id=tid, case=case)
        results[tid] = result
        file_equal = not compare(*pair, True)
        files_matches += file_equal
        saved = report['results'].get(tid, {})
        if saved.get('full_match') is not result['raw_exact'] or saved.get('files_match') is not file_equal:
            problems.append(tid + ': raw full/file match aliases differ from reopened comparison')
        for key, value in result.items():
            if key not in saved or not same_json(saved[key], value):
                problems.append(tid + ': stored classification mismatch: ' + key)
        if not result['accepted']:
            problems.append(tid + ': unexpected terminal difference')
    observed = {tid: result['deviation_id'] for tid, result in results.items() if result['declared_deviation']}
    if observed != {'TEST-CLI-057': 'Q-DEF-001', 'TEST-PROMPT-NUL-001': 'Q-PROMPT-001'}:
        problems.append('terminal named historical deviation inventory mismatch')
    expected_summary = {**summary_counts(results), 'full_matches': sum(r['raw_exact'] for r in results.values()),
                        'files_matches': files_matches, 'skipped': len(CORPUS_EXCLUSIONS)}
    for key, value in expected_summary.items():
        if type(report.get('summary', {}).get(key)) is not int or report['summary'][key] != value:
            problems.append('terminal summary differs from reopened records: ' + key)
    counts = classification_counts(results.values())
    counts.update(files_matches=files_matches, excluded=len(report.get('skipped', {})))
    return report, counts, problems
