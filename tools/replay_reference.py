#!/usr/bin/env python3
"""Record disjoint reference fixture IDs concurrently, preserving every worker result."""
import argparse,hashlib,json,subprocess,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--scenarios',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--jobs',type=int,default=4);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
cases=json.loads(a.scenarios.read_text());ids={s['id']for s in cases};assert len(ids)==len(cases)
workers=[]
for i in range(a.jobs):
 part=a.out/f'part-{i}';part.mkdir();scenario=part/'cases.json';scenario.write_text(json.dumps(cases[i::a.jobs]));log=(part/'replay.log').open('w')
 process=subprocess.Popen([sys.executable,str(ROOT/'spec/tools/nanoharness.py'),str(scenario.resolve()),'--binary',str(a.binary.resolve()),'--out',str(part.resolve())],stdout=log,stderr=log)
 workers.append((process,log,part))
statuses=[];found=set()
for process,log,part in workers:
 statuses.append(process.wait());log.close()
 for folder in part.glob('TEST-*'):
  if (folder/'result.json').exists():shutil.copytree(folder,a.out/folder.name);found.add(folder.name)
report={'worker_statuses':statuses,'expected':len(ids),'recorded':len(found),'missing':sorted(ids-found),'binary_sha256':hashlib.sha256(a.binary.read_bytes()).hexdigest()};(a.out/'inventory.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));raise SystemExit(int(any(statuses)or ids!=found))
