#!/usr/bin/env python3
"""Replay noninteractive CLI probes in harness fixtures (including exact argv[0])."""
import argparse,hashlib,json,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--binary',default=str(ROOT/'target/release/naro'));a=p.parse_args()
out=ROOT/'spec/evidence/naro-cli';out.mkdir(parents=True,exist_ok=True)
reference=json.loads((ROOT/'spec/evidence/cli/cli-probes.json').read_text());sc=[];expected={};skipped={}
for r in reference['results']:
 if r['profile']=='tiny':skipped[r['id']]='optional tiny profile';continue
 if any(v.startswith('/')for v in r['args']):skipped[r['id']]='absolute path probe outside fixture';continue
 files={}
 for k,data in reference['rc_files'].items():
  name={'$RC1':'rc1','$RCBAD':'rcbad','$RCVITAL':'rcvital','$RCSYN':'rcsyn'}[k]
  files['work/'+name]={'text':data}
 env={}
 if r['id']=='CLI-P-043':files['home/.nanorc']={'text':'syntax one "\\.one$"\ncolor red "a"\n'}
 tid='TEST-NARO-CLI-'+r['id'].split('-')[-1]
 sc.append(dict(id=tid,argv0=r['argv0'],args=[v.replace('$TMP/','$FX/work/')for v in r['args']],dirs=['work/rcdir'],files=files,env=env,stdin='',stdout_redirect=True,hold_tty=True,steps=[{'wait_exit':5}],expect={'exit_status':r['exit_status']}))
 expected[tid]=r
path=out/'scenarios.json';path.write_text(json.dumps(sc,indent=1)+'\n')
status=subprocess.run([sys.executable,str(ROOT/'spec/tools/nanoharness.py'),str(path),'--binary',str(pathlib.Path(a.binary).resolve()),'--out',str(out)]).returncode
report={'reference_commit':'6ed285c3ec7a1d228def4d4e7021c6ba269f620c','binary_sha256':hashlib.sha256(pathlib.Path(a.binary).read_bytes()).hexdigest(),'skipped':skipped,'results':{}}
for tid,r in expected.items():
 result=json.loads((out/tid/'result.json').read_text());diff=[]
 for field in ('exit_status','stdout','stderr'):
  if result.get(field)!=r[field]:diff.append(dict(field=field,expected=r[field],actual=result.get(field)))
 report['results'][tid]=diff
report['summary']={'compared':len(expected),'matches':sum(not d for d in report['results'].values()),'skipped':len(skipped)}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary']))
raise SystemExit(status or int(any(report['results'].values())))
