#!/usr/bin/env python3
"""Partition fixture IDs between independent validation processes.

Reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c. Never run another full suite
at the same time: each partition is disjoint, but fixtures are keyed by test ID.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--binary', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--jobs', type=int, default=4, choices=range(1, 9))
a = p.parse_args()
if a.out.exists():
    raise SystemExit('use a new output directory to preserve existing evidence')
a.out.mkdir(parents=True)
frozen = (a.out / 'naro').resolve()
shutil.copy2(a.binary.resolve(), frozen)
digest = hashlib.sha256(frozen.read_bytes()).hexdigest()
ids = sorted(s['id'] for path in (ROOT / 'spec/evidence/scenarios').glob('*.json')
             for s in json.loads(path.read_text()))
if len(ids) != len(set(ids)):
    raise SystemExit('duplicate scenario IDs')
workers = []
for i in range(a.jobs):
    part = a.out / f'part-{i}'
    log = (a.out / f'part-{i}.log').open('w')
    process = subprocess.Popen([sys.executable, str(ROOT / 'tools/validate.py'),
                                '--binary', str(frozen), '--out', str(part),
                                '--ids', *ids[i::a.jobs]], stdout=log, stderr=log)
    workers.append((process, log, part))
results, skipped, statuses = {}, {}, []
for process, log, part in workers:
    statuses.append(process.wait())
    log.close()
    report = json.loads((part / 'report.json').read_text())
    if report['binary_sha256'] != digest or results.keys() & report['results'].keys():
        raise SystemExit('inconsistent binary or overlapping partitions')
    results.update(report['results'])
    skipped.update(report['skipped'])
if set(results) | set(skipped) != set(ids):
    raise SystemExit('incomplete partition results')
summary = dict(recorded=len(results), full_matches=sum(v['full_match'] for v in results.values()),
               files_matches=sum(v['files_match'] for v in results.values()), skipped=len(skipped))
report = dict(reference_commit='6ed285c3ec7a1d228def4d4e7021c6ba269f620c',
              binary_sha256=digest, skipped=skipped, results=dict(sorted(results.items())),
              summary=summary, partitions=a.jobs, worker_statuses=statuses)
(a.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(summary))
raise SystemExit(int(any(statuses)))
