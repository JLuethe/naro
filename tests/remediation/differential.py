#!/usr/bin/env python3
"""Fresh, exhaustive profile inventories with fail-closed differential accounting.

This runner preserves raw differences. It does not grant new safe-save exceptions;
those need separately reviewed semantic assertions and remain visible failures here.
"""
from __future__ import annotations
import argparse
import copy
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from functools import lru_cache
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'spec/tools'), str(ROOT / 'tools')]
from candidate_expectations import candidate_case
from environment import snapshot, command
from frozen_process import make_private_tmux_tmpdir, remove_private_tmux_tmpdir, run_owned_process
from identity_review import classify, policy_identity
from release_gate_evidence import corpus_coverage_problems, recording_problems

PIN = '6ed285c3ec7a1d228def4d4e7021c6ba269f620c'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def verification_inputs():
    paths = list((ROOT / 'spec/tools').glob('*.py')) + list((ROOT / 'tests/remediation').glob('*.py')) + list((ROOT / 'tests/naro').glob('*.json'))
    paths += [ROOT / 'tools/frozen_process.py', ROOT / 'tools/environment.py', ROOT / 'tools/release_gate_evidence.py', ROOT / 'Cargo.toml']
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}


def inventory(profile):
    groups, excluded = {}, {}
    for path in sorted((ROOT / 'spec/evidence/scenarios').glob('*.json')):
        for case in json.loads(path.read_text()):
            key = 'baseline/' + case['id']
            if any(str(x).startswith('/') for x in case.get('args', [])) or case['id'] == 'TEST-BROWSE-003':
                excluded[key] = 'fixture safety: external pathname or root browser'
            elif (case.get('profile') == 'tiny') != (profile == 'tiny'):
                excluded[key] = 'other profile; tiny uses its retained-feature corpus'
            else:
                groups.setdefault('baseline', []).append(case)
    for path in sorted((ROOT / 'tests/follow-up/scenarios').glob('*.json')):
        for case in json.loads(path.read_text()):
            key = path.stem + '/' + case['id']
            if path.stem == 'panic':
                excluded[key] = 'test-hooks instrumented variant only; not production binary'
            elif path.stem.startswith('tiny') != (profile == 'tiny'):
                excluded[key] = 'other profile'
            else:
                groups.setdefault(path.stem, []).append(case)
    cli = json.loads((ROOT / 'spec/evidence/cli/cli-probes.json').read_text())
    for row in cli['results']:
        key = 'original-cli/' + row['id']
        if any(x.startswith('/') for x in row['args']):
            excluded[key] = 'fixture safety: external CLI pathname'
            continue
        if row['profile'] != profile:
            excluded[key] = 'other profile'
            continue
        files = {}
        for key, data in cli['rc_files'].items():
            name = {'$RC1': 'rc1', '$RCBAD': 'rcbad', '$RCVITAL': 'rcvital', '$RCSYN': 'rcsyn'}[key]
            files['work/' + name] = {'text': data}
        if row['id'] == 'CLI-P-043':
            files['home/.nanorc'] = {'text': 'syntax one "\\.one$"\ncolor red "a"\n'}
        groups.setdefault('original-cli', []).append({
            'id': 'TEST-M15-' + row['id'], 'argv0': row['argv0'],
            'args': [x.replace('$TMP/', '$FX/work/') for x in row['args']],
            'dirs': ['work/rcdir'], 'files': files, 'stdin': '',
            'stdout_redirect': True, 'hold_tty': True, 'steps': [{'wait_exit': 5}],
        })
    for name, cases in groups.items():
        ids = [c['id'] for c in cases]
        if len(ids) != len(set(ids)):
            raise ValueError('duplicate IDs: ' + name)
    return groups, excluded


@lru_cache(maxsize=None)
def locale_probe(environment_json):
    env = json.loads(environment_json)
    outcome = subprocess.run(['/usr/bin/locale', 'charmap'], env=env, text=True, capture_output=True, timeout=10)
    # Some locale implementations return zero while warning that setlocale
    # failed; stderr is therefore part of the prerequisite result.
    return {'environment': env, 'status': outcome.returncode, 'charmap': outcome.stdout.strip(),
            'stderr': outcome.stderr, 'available': outcome.returncode == 0 and not outcome.stderr}


def case_locale(case):
    env = {'PATH': '/usr/bin:/bin', 'LANG': case.get('lang', 'en_US.UTF-8')}
    if case.get('locpath'):
        env['LOCPATH'] = case['locpath']
    for key, value in case.get('env', {}).items():
        if key in ('LANG', 'LANGUAGE', 'LOCPATH') or key.startswith('LC_'):
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
    return locale_probe(json.dumps(env, sort_keys=True))


def private_case(case, scratch):
    """Relocate only the known seeded position-history fixture, fail closed.

    This is an input substitution, recorded separately from unchanged source
    scenarios; it never rewrites observations or broadens normalization.
    """
    selected = copy.deepcopy(case)
    if case['id'] == 'TEST-FEAT-015':
        entry = selected['files']['home/.local/share/nano/filepos_history']
        old = '/elsewhere 3 1\n41 42 /tmp/nanospec-work/TEST-FEAT-015/fx/work/f.txt 40 2\n'
        if entry.get('text') != old:
            raise ValueError('position-history fixture changed; review adaptation')
        entry['text'] = old.replace('/tmp/nanospec-work/TEST-FEAT-015/fx/work/f.txt', str(scratch / 'TEST-FEAT-015/fx/work/f.txt'))
    return selected


def safe_save_observations(candidate, case):
    """Independent semantic checks for the two historical link-save scenarios.

    These annotate raw differential failures; they do not waive any other field.
    """
    initial, final = candidate.get('initial_fixture', {}), candidate.get('fixture', {})
    if case['id'] == 'TEST-FILE-003':
        original, saved = initial.get('work/real.txt', {}), final.get('work/real.txt', {})
        link = final.get('work/link.txt', {})
        return {'policy': 'issue-3-final-symlink-rejected', 'checks': {
            'target_bytes_preserved': saved.get('text') == original.get('text') == 'r\n',
            'target_inode_preserved': original.get('ino') is not None and saved.get('ino') == original['ino'],
            'link_preserved': link.get('type') == 'link' and link.get('target') == 'real.txt',
            'rejection_observed': any('symbolic link' in row.get('text', '') for row in candidate.get('snapshots', {}).get('f02', {}).get('rows', [])),
            'clean_exit': candidate.get('exit_status') == 0 and candidate.get('exit_signal') is None,
        }}
    if case['id'] == 'TEST-FILE-004':
        original = initial.get('work/f.txt', {})
        other_before = initial.get('work/g.txt', {})
        saved, other = final.get('work/f.txt', {}), final.get('work/g.txt', {})
        return {'policy': 'issue-3-hardlink-replacement', 'checks': {
            'initial_links_share_inode': original.get('ino') is not None and original.get('ino') == other_before.get('ino'),
            'saved_complete_bytes': saved.get('text') == 'xh\n',
            'other_link_original_bytes': other.get('text') == original.get('text') == 'h\n',
            'saved_inode_replaced': saved.get('ino') is not None and saved.get('ino') != original.get('ino'),
            'other_link_inode_preserved': other.get('ino') == original.get('ino'),
            'link_counts_split': saved.get('nlink') == other.get('nlink') == 1,
            'metadata_preserved': all(saved.get(k) == original.get(k) for k in ['mode', 'uid', 'gid']),
            'clean_exit': candidate.get('exit_status') == 0 and candidate.get('exit_signal') is None,
        }}
    return None


def inspect_pair(reference, candidate, case, hashes, profile):
    """Separate missing/infrastructure/reference/product failures; never empty-pass."""
    if reference is None or candidate is None:
        return {'accepted': False, 'classification': 'missing_evidence',
                'missing': [k for k, v in [('reference', reference), ('candidate', candidate)] if v is None]}
    problems = []
    for side, recording in [('reference', reference), ('candidate', candidate)]:
        if recording.get('binary_sha256') != hashes[side]:
            problems.append(side + ' executable hash mismatch')
        if recording.get('scenario') != case['id']:
            problems.append(side + ' scenario ID mismatch')
    if problems:
        return {'accepted': False, 'classification': 'infrastructure_failure', 'errors': problems}
    # The profile is supplied for the CLI identity oracle without modifying source
    # scenarios or their hash-bound candidate expectation overlays.
    context = {**case, 'profile': 'tiny'} if profile == 'tiny' and any(x in ('--version', '-V') for x in case.get('args', [])) else case
    result = classify(reference, candidate, case['id'], context)
    result['coverage_problems'] = {side: corpus_coverage_problems(recording, case['id']) for side, recording in [('reference', reference), ('candidate', candidate)]}
    result['reference_checks'] = not result['coverage_problems']['reference'] and bool(reference.get('steps_ok')) and all(c.get('pass') is True for c in reference.get('checks', []))
    result['candidate_checks'] = not result['coverage_problems']['candidate'] and bool(candidate.get('steps_ok')) and all(c.get('pass') is True for c in candidate.get('checks', []))
    result['assertion_counts'] = {k: len(v.get('checks', [])) for k, v in [('reference', reference), ('candidate', candidate)]}
    if not result['reference_checks']:
        result.update(accepted=False, classification='reference_failure')
    elif not result['candidate_checks']:
        result.update(accepted=False, classification='candidate_execution_or_assertion_failure')
    elif not result['accepted']:
        result['classification'] = 'product_or_policy_difference'
    semantic = safe_save_observations(candidate, case)
    if semantic is not None:
        semantic['passed'] = result['candidate_checks'] and bool(semantic['checks']) and all(value is True for value in semantic['checks'].values())
        result['safe_save_semantics'] = semantic
        if not semantic['passed']:
            if result['accepted']:
                result['differential_classification'] = result['classification']
                result['classification'] = 'candidate_semantic_failure'
            result['accepted'] = False
    return result


def run_group(name, cases, args, binaries):
    out = args.out / name
    out.mkdir()
    scratch = Path(tempfile.mkdtemp(prefix='nanospec-m15-', dir='/tmp'))
    tmux, owner = make_private_tmux_tmpdir()
    report = {'name': name, 'expected_ids': [c['id'] for c in cases], 'scratch': str(scratch), 'results': {}}
    reference_key = 'root_reference' if name.startswith('root') else 'reference'
    selected_binaries = {'reference': binaries.get(reference_key), 'candidate': binaries['candidate']}
    missing_prerequisite = 'root reference binary required' if selected_binaries['reference'] is None else 'bubblewrap namespace backend unavailable' if any('root_namespace' in c for c in cases) and shutil.which('bwrap') is None else None
    if missing_prerequisite:
        report['results'] = {c['id']: {'accepted': False, 'classification': 'missing_prerequisite', 'recordings_present': False, 'error': missing_prerequisite} for c in cases}
        write(out / 'report.json', report)
        remove_private_tmux_tmpdir(tmux, owner)
        return report
    hashes = {k: digest(v) for k, v in selected_binaries.items()}
    report['binary_sha256'] = hashes
    report['locale_prerequisites'] = {c['id']: case_locale(c) for c in cases}
    report['input_adaptations'] = [{'id': c['id'], 'field': 'files.home/.local/share/nano/filepos_history.text', 'before': c['files']['home/.local/share/nano/filepos_history']['text'], 'after': private_case(c, scratch)['files']['home/.local/share/nano/filepos_history']['text']} for c in cases if c['id'] == 'TEST-FEAT-015']
    try:
        for side, binary in selected_binaries.items():
            selected = [private_case(candidate_case(c) if side == 'candidate' else c, scratch) for c in cases]
            scenario = out / (side + '-scenarios.json')
            write(scenario, selected)
            env = {**os.environ, 'NANOSPEC_WORK': str(scratch), 'TMUX_TMPDIR': str(tmux), 'PYTHONDONTWRITEBYTECODE': '1'}
            cmd = [sys.executable, str(ROOT / 'spec/tools/nanoharness.py'), str(scenario), '--binary', str(binary), '--out', str(out / side)]
            report[side + '_run'] = run_owned_process(cmd, cwd=ROOT, env=env, log_path=out / (side + '.log'), timeout=args.timeout, tmux_tmpdir=tmux)
        for case in cases:
            recordings = {}
            for side in selected_binaries:
                path = out / side / case['id'] / 'result.json'
                recordings[side] = json.loads(path.read_text()) if path.is_file() else None
            result = inspect_pair(**recordings, case=case, hashes=hashes, profile=args.profile)
            result['recordings_present'] = all(record is not None for record in recordings.values())
            result['recording_problems'] = {side: recording_problems(recording, private_case(case, scratch), side, hashes[side], out / side / case['id']) for side, recording in recordings.items() if recording is not None}
            if any(result['recording_problems'].values()):
                if result['accepted']:
                    result['differential_classification'] = result['classification']
                    result['classification'] = 'invalid_evidence'
                result['accepted'] = False
            if not report['locale_prerequisites'][case['id']]['available']:
                result['differential_classification'] = result['classification']
                result.update(accepted=False, classification='missing_prerequisite', missing_prerequisite='requested locale unavailable')
            report['results'][case['id']] = result
        if any(digest(v) != hashes[k] for k, v in selected_binaries.items()):
            report['infrastructure_error'] = 'binary changed during execution'
        report['complete'] = set(report['results']) == {c['id'] for c in cases}
    except Exception as exc:
        report['infrastructure_error'] = repr(exc)
        for case in cases:
            report['results'].setdefault(case['id'], {'accepted': False, 'classification': 'infrastructure_failure', 'error': repr(exc)})
    finally:
        try:
            remove_private_tmux_tmpdir(tmux, owner)
        except Exception as exc:
            report['cleanup_error'] = repr(exc)
    report['passed'] = bool(report['results']) and report.get('complete', False) and all(r['accepted'] for r in report['results'].values()) and all(report.get(k + '_run', {}).get('status') == 0 for k in selected_binaries) and not any(k in report for k in ['infrastructure_error', 'cleanup_error'])
    write(out / 'report.json', report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binary', type=Path, required=True)
    p.add_argument('--reference', type=Path, required=True)
    p.add_argument('--root-reference', type=Path)
    p.add_argument('--profile', choices=['default', 'tiny'], required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--jobs', type=int, default=4, choices=range(1, 9))
    p.add_argument('--timeout', type=int, default=1800)
    p.add_argument('--inventory-only', action='store_true')
    a = p.parse_args()
    a.out = a.out.absolute()
    a.out.mkdir(parents=True, exist_ok=False)
    groups, excluded = inventory(a.profile)
    report = {'profile': a.profile, 'inventory': {k: [c['id'] for c in v] for k, v in groups.items()}, 'exclusions': excluded, 'reference_commit': PIN, 'identity_policy': policy_identity(), 'verification_inputs': verification_inputs(), 'environment': snapshot(), 'native_versions': {k: command(v) for k, v in {'ncurses': ['pkg-config', '--modversion', 'ncursesw'], 'libmagic': ['pkg-config', '--modversion', 'libmagic'], 'rustc': ['rustc', '--version'], 'git_head': ['git', 'rev-parse', 'HEAD'], 'git_tree': ['git', 'rev-parse', 'HEAD^{tree}'], 'git_status': ['git', 'status', '--porcelain']}.items()}, 'groups': {}}
    write(a.out / 'inventory.json', report)
    if a.inventory_only:
        return 0
    binaries = {}
    for key, source in [('candidate', a.binary), ('reference', a.reference), ('root_reference', a.root_reference)]:
        if source is not None:
            destination = a.out / (key + '.bin')
            shutil.copy2(source.resolve(strict=True), destination)
            binaries[key] = destination
    report['artifacts'] = {k: {'path': str(v), 'sha256': digest(v)} for k, v in binaries.items()}
    report['build'] = json.loads(subprocess.check_output([str(binaries['candidate'])], env={**os.environ, 'NARO_BUILD_INFO': '1'}, text=True))
    expected_features = 'tiny' if a.profile == 'tiny' else ''
    if report['build']['features'] != expected_features:
        raise ValueError('candidate feature profile mismatch')
    # Baseline IDs are partitioned, never duplicated, each with private fixtures.
    baseline = groups.pop('baseline')
    for i in range(a.jobs):
        groups['baseline-' + str(i)] = baseline[i::a.jobs]
    groups = {k: v for k, v in groups.items() if v}
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        futures = {pool.submit(run_group, k, v, a, binaries): k for k, v in groups.items()}
        for future in as_completed(futures):
            name = futures[future]
            report['groups'][name] = future.result()
            print(name, len(report['groups'][name]['results']), 'passed=' + str(report['groups'][name].get('passed', False)), flush=True)
            write(a.out / 'report.json', report)
    results = [r for g in report['groups'].values() for r in g['results'].values()]
    report['summary'] = {'expected': sum(map(len, report['inventory'].values())), 'accounted': len(results), 'recorded': sum(bool(r.get('recordings_present')) for r in results), 'accepted': sum(r['accepted'] for r in results), 'classifications': {k: sum(r['classification'] == k for r in results) for k in sorted({r['classification'] for r in results})}}
    report['verification_unchanged'] = report['verification_inputs'] == verification_inputs() and report['identity_policy'] == policy_identity()
    report['passed'] = report['verification_unchanged'] and len(results) == report['summary']['expected'] and bool(results) and all(g.get('passed', False) for g in report['groups'].values())
    write(a.out / 'report.json', report)
    print(json.dumps(report['summary']))
    return int(not report['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
