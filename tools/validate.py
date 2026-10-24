#!/usr/bin/env python3
"""Run pinned scenarios safely against a frozen Naro binary and compare results.
Reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c.
"""
import argparse,hashlib,json,os,pathlib,shutil,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'spec/tools'))
from compare_runs import compare
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--binary',type=pathlib.Path,default=ROOT/'target/debug/naro');p.add_argument('--out',type=pathlib.Path,default=ROOT/'spec/evidence/naro-validation');p.add_argument('--ids',nargs='*');p.add_argument('--resume',action='store_true');args=p.parse_args()
args.out.mkdir(parents=True,exist_ok=True)
frozen=args.out/'naro';source=args.binary.resolve()
if not args.resume:shutil.copy2(source,frozen)
selected=[];skipped={}
for file in sorted((ROOT/'spec/evidence/scenarios').glob('*.json')):
 for s in json.loads(file.read_text()):
  if args.ids and s['id']not in args.ids:continue
  reason=None
  if s.get('profile')=='tiny':reason='optional tiny profile; Naro default build only'
  if any(a.startswith('/')for a in s.get('args',[])):reason='external absolute path probe excluded by fixture-only policy'
  if s['id']=='TEST-BROWSE-003':reason='root-directory browser probe excluded by fixture-only policy'
  if reason:skipped[s['id']]=reason;continue
  if not args.resume or not (args.out/s['id']/'result.json').exists():selected.append(s)
scenarios=args.out/'scenarios.json';scenarios.write_text(json.dumps(selected,indent=1)+'\n')
report=dict(reference_commit='6ed285c3ec7a1d228def4d4e7021c6ba269f620c',binary_sha256=hashlib.sha256(frozen.read_bytes()).hexdigest(),skipped=skipped,results={})
(args.out/'provenance.json').write_text(json.dumps(report,indent=2)+'\n')
if selected:
 env=os.environ.copy();env['PYTHONUNBUFFERED']='1';env.setdefault('NANOSPEC_WORK','/tmp/nanospec-work')
 run=subprocess.run([sys.executable,str(ROOT/'spec/tools/nanoharness.py'),str(scenarios),'--binary',str(frozen.resolve()),'--out',str(args.out.resolve())],env=env)
 report['harness_status']=run.returncode
for path in sorted(args.out.glob('TEST-*/result.json')):
 tid=path.parent.name;ref=ROOT/'spec/evidence/runs'/tid/'result.json'
 if not ref.exists():continue
 a,b=json.loads(ref.read_text()),json.loads(path.read_text());full=compare(a,b);files=compare(a,b,True)
 deviation=tid in ('TEST-CLI-057','TEST-PROMPT-NUL-001')
 report['results'][tid]=dict(full_match=not full,files_match=not files,declared_deviation=deviation,differences=full)
report['summary']=dict(recorded=len(report['results']),full_matches=sum(v['full_match']for v in report['results'].values()),files_matches=sum(v['files_match']for v in report['results'].values()),skipped=len(skipped))
(args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['summary']))
raise SystemExit(int(any(not v['full_match']and not v['declared_deviation']for v in report['results'].values())))
