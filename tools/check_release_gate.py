#!/usr/bin/env python3
"""Recompute a v2 release gate from its raw evidence inputs; never publish."""
import argparse
import json
from pathlib import Path
from collect_closure import collect_evidence
from release_gate_evidence import GATE_SCHEMA, policy_identity, same_json

ROOT = Path(__file__).resolve().parents[1]


def verify_gate(stored):
    problems = []
    if stored.get('schema') != GATE_SCHEMA:
        return ['unsupported gate schema: historical 0.1.0 gates must retain their original tooling'], None
    if stored.get('identity_policy') != policy_identity():
        return ['gate policy identity/hash differs from reviewed tooling'], None
    try:
        current = collect_evidence(stored['inputs'])
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        return ['missing or invalid reopened evidence: ' + str(error)], None
    if not same_json(stored, current):
        problems.append('stored gate differs from independently recomputed gate')
    if current['pass'] is not True:
        problems.extend('failed check: ' + check['name'] for check in current['checks'] if not check['pass'])
    return problems, current


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reports', type=Path, default=ROOT / 'validation/closure',
                        help='v2 collector directory containing gate.json and raw-input index')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('use a new output file to preserve earlier evidence')
    try:
        stored = json.loads((args.reports / 'gate.json').read_text())
        problems, current = verify_gate(stored)
    except (OSError, ValueError, KeyError, TypeError) as error:
        problems, current = ['invalid gate: ' + str(error)], None
    result = {'schema': GATE_SCHEMA, 'identity_policy': policy_identity(),
              'pass': not problems, 'problems': problems,
              'accounting': current['accounting'] if current else None,
              'publication': 'No tag or release published; separate explicit action.'}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'pass': not problems, 'problems': problems}))
    return int(bool(problems))


if __name__ == '__main__':
    raise SystemExit(main())
