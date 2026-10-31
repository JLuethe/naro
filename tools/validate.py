#!/usr/bin/env python3
"""Run pinned scenarios safely against a frozen Naro binary and compare results.
Reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c.
"""
import argparse,hashlib,json,os,pathlib,shutil,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'spec/tools'))
from compare_runs import compare
from identity_review import classify, policy_identity, summary_counts
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--binary',type=pathlib.Path,default=ROOT/'target/debug/naro');p.add_argument('--out',type=pathlib.Path,default=ROOT/'spec/evidence/naro-validation');p.add_argument('--ids',nargs='*');p.add_argument('--resume',action='store_true');p.add_argument('--compare-only',action='store_true',help='recompare existing recordings without changing the frozen binary or scenario list');args=p.parse_args()
args.out.mkdir(parents=True,exist_ok=True)
frozen=args.out/'naro';source=args.binary.resolve()
if not args.resume and not args.compare_only:shutil.copy2(source,frozen)
selected=[];skipped={};case_by_id={}
for file in sorted((ROOT/'spec/evidence/scenarios').glob('*.json')):
 for s in json.loads(file.read_text()):
  case_by_id[s['id']]=s
  if args.ids and s['id']not in args.ids:continue
  reason=None
  if s.get('profile')=='tiny':reason='optional tiny profile; Naro default build only'
  if any(a.startswith('/')for a in s.get('args',[])):reason='external absolute path probe excluded by fixture-only policy'
  if s['id']=='TEST-BROWSE-003':reason='root-directory browser probe excluded by fixture-only policy'
  if reason:skipped[s['id']]=reason;continue
  if not args.resume or not (args.out/s['id']/'result.json').exists():selected.append(s)
scenarios=args.out/'scenarios.json'
if not args.compare_only:scenarios.write_text(json.dumps(selected,indent=1)+'\n')
reference_runs=pathlib.Path(os.environ.get('NARO_REFERENCE_RUNS',str(ROOT/'spec/evidence/runs'))).resolve()
report=dict(identity_policy=policy_identity(),reference_runs=str(reference_runs),reference_runs_relative=os.path.relpath(reference_runs,args.out),reference_commit='6ed285c3ec7a1d228def4d4e7021c6ba269f620c',binary_sha256=hashlib.sha256(frozen.read_bytes()).hexdigest(),skipped=skipped,results={})
(args.out/'provenance.json').write_text(json.dumps(report,indent=2)+'\n')
if selected and not args.compare_only:
 env=os.environ.copy();env['PYTHONUNBUFFERED']='1';env.setdefault('NANOSPEC_WORK','/tmp/nanospec-work')
 run=subprocess.run([sys.executable,str(ROOT/'spec/tools/nanoharness.py'),str(scenarios),'--candidate-expectations','--binary',str(frozen.resolve()),'--out',str(args.out.resolve())],env=env)
 report['harness_status']=run.returncode
for path in sorted(args.out.glob('TEST-*/result.json')):
 tid=path.parent.name;ref=reference_runs/tid/'result.json'
 if not ref.exists():continue
 a,b=json.loads(ref.read_text()),json.loads(path.read_text());full=compare(a,b);files=compare(a,b,True)
 result=classify(a,b,tid,case_by_id[tid]);result.update(full_match=not full,files_match=not files,reference_recording=str(ref),candidate_recording=str(path.resolve()))
 if not b.get('steps_ok') or not all(x['pass']for x in b.get('checks',[])):result['accepted']=False
 report['results'][tid]=result
report['summary']=summary_counts(report['results']);report['summary'].update(full_matches=sum(v['full_match']for v in report['results'].values()),files_matches=sum(v['files_match']for v in report['results'].values()),skipped=len(skipped))
(args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['summary']))
raise SystemExit(int(report.get('harness_status',0) or any(not v['accepted']for v in report['results'].values())))
