#!/usr/bin/env python3
"""Fresh reference/candidate replay for the follow-up spec; never modifies old goldens."""
import argparse,copy,hashlib,json,os,pathlib,shutil,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'spec/tools'))
from compare_runs import compare
from environment import snapshot
from check_wrap_undo import verification_fingerprint
from follow_up_policy import deviation
p=argparse.ArgumentParser();p.add_argument('--suite',required=True);p.add_argument('--binary',type=pathlib.Path,default=ROOT/'target/debug/naro');p.add_argument('--reference',type=pathlib.Path,default=pathlib.Path.home()/'src/nano-install/default/bin/nano');p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--ids',nargs='*');p.add_argument('--reference-only',action='store_true');a=p.parse_args()
if a.out.exists():raise SystemExit('preserve evidence: use a new output directory')
a.out.mkdir(parents=True)
cases=json.loads((ROOT/f'tests/follow-up/scenarios/{a.suite}.json').read_text());cases=[s for s in cases if not a.ids or any(s['id'].startswith(i)for i in a.ids)]
if not cases:raise SystemExit('no cases selected')
scenario=a.out/'scenarios.json';scenario.write_text(json.dumps(cases,indent=1)+'\n')
env=os.environ.copy();env['PYTHONUNBUFFERED']='1'
report={'verification_sha256':verification_fingerprint(),'environment':snapshot(),'build_flags':os.environ.get('NARO_BUILD_FLAGS','default'),'reference_commit':'6ed285c3ec7a1d228def4d4e7021c6ba269f620c','scenario_sha256':hashlib.sha256(scenario.read_bytes()).hexdigest(),'results':{}}
for kind,source in [('reference',a.reference),('candidate',a.binary)]:
 if kind=='candidate'and a.reference_only:break
 binary=(a.out/(kind+'.bin')).resolve();shutil.copy2(source.resolve(),binary);report[kind+'_sha256']=hashlib.sha256(binary.read_bytes()).hexdigest()
 selected=copy.deepcopy(cases)
 if kind=='candidate':
  for case in selected:
   if 'candidate_expect'in case:case['expect']=case['candidate_expect']
 scenario=a.out/(kind+'-scenarios.json');scenario.write_text(json.dumps(selected,indent=1)+'\n')
 log=(a.out/(kind+'.log')).open('w');status=subprocess.run([sys.executable,str(ROOT/'spec/tools/nanoharness.py'),str(scenario.resolve()),'--binary',str(binary),'--out',str((a.out/kind).resolve())],env=env,stdout=log,stderr=log).returncode;log.close();report[kind+'_status']=status
 if status:print(kind,'harness failure; see',a.out/(kind+'.log'))
 if kind=='candidate':
  report['candidate_build']=json.loads(subprocess.check_output([str(binary)],env={**os.environ,'NARO_BUILD_INFO':'1'},text=True))
  for s in cases:
   tid=s['id']
   if any(not (a.out/k/tid/'result.json').exists()for k in ['reference','candidate']):
    report['results'][tid]={'match':False,'accepted':False,'reference_checks':False,'candidate_checks':False,'differences':[{'field':'missing recording'}]};continue
   r=json.loads((a.out/'reference'/tid/'result.json').read_text());c=json.loads((a.out/'candidate'/tid/'result.json').read_text());diff=compare(r,c)
   issue=deviation(tid,r,c,diff);declared=bool(issue)
   report['results'][tid]={'match':not diff,'declared_deviation':declared,'deviation_id':issue,'accepted':not diff or declared,'reference_checks':all(x['pass']for x in r['checks'])and r['steps_ok'],'candidate_checks':all(x['pass']for x in c['checks'])and c['steps_ok'],'differences':diff}
   print(tid,'MATCH'if not diff else 'EXPECTED '+issue+' difference'if declared else ', '.join(x['field']for x in diff))
report['summary']={'recorded':len(cases),'matches':sum(x['match']for x in report['results'].values()),'accepted':sum(x['accepted']for x in report['results'].values())}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(report['summary'])
raise SystemExit(int(any(report.get(k+'_status',0)for k in ['reference','candidate'])or any(not r['accepted']for r in report['results'].values())))
