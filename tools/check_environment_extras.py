#!/usr/bin/env python3
"""Fresh environment-local CLI/regex oracles and candidate recovery assertions."""
import argparse,copy,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'spec/tools'))
import nanoharness as h
p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
report={'candidate_sha256':hashlib.sha256(a.binary.read_bytes()).hexdigest(),'reference_sha256':hashlib.sha256(a.reference.read_bytes()).hexdigest(),'cli':{},'regex':{},'safety':{}}
reference=json.loads((ROOT/'spec/evidence/cli/cli-probes.json').read_text())
for r in reference['results']:
 if r['profile']=='tiny'or any(x.startswith('/')for x in r['args']):continue
 files={}
 for k,data in reference['rc_files'].items():files['work/'+{'$RC1':'rc1','$RCBAD':'rcbad','$RCVITAL':'rcvital','$RCSYN':'rcsyn'}[k]]={'text':data}
 if r['id']=='CLI-P-043':files['home/.nanorc']={'text':'syntax one "\\.one$"\ncolor red "a"\n'}
 sc=dict(id='TEST-NEXT-ENV-CLI-'+r['id'][-3:],argv0=r['argv0'],args=[x.replace('$TMP/','$FX/work/')for x in r['args']],dirs=['work/rcdir'],files=files,stdin='',stdout_redirect=True,hold_tty=True,steps=[{'wait_exit':5}])
 results={}
 for name,binary in [('reference',a.reference),('candidate',a.binary)]:results[name]=h.Run(sc,str(binary.resolve()),str(a.out/name/sc['id'])).execute()
 ok=all(results['reference'][k]==results['candidate'][k]for k in ['stdout','stderr','exit_status'])and all(x['steps_ok']for x in results.values())
 report['cli'][r['id']]={'pass':ok}
source=(ROOT/'spec/tools/regex/regex_probe.c').read_text();report['regex_probe_sha256']=hashlib.sha256(source.encode()).hexdigest()
for lang in ['C','en_US.UTF-8']:
 outputs={}
 for name in ['reference','candidate']:
  tid='TEST-NEXT-ENV-REGEX-'+lang.replace('.','-').replace('_','-')+'-'+name
  sc=dict(id=tid,lang=lang,stdin=(ROOT/'spec/evidence/regex/cases.tsv').read_text(),stdout_redirect=True,hold_tty=True,steps=[{'wait_exit':5}],expect={'exit_status':0})
  if name=='reference':
   sc['files']={'bin/probe.c':{'text':source}};sc['build_helpers']=[{'source':'bin/probe.c','output':'bin/probe','shared':False}];binary=Path(h.WORKROOT)/tid/'fx/bin/probe'
  else:sc['env']={'NARO_REGEX_PROBE':'1'};binary=a.binary
  result=h.Run(sc,str(binary.resolve()),str(a.out/name/tid)).execute()
  assert result['steps_ok']and all(c['pass']for c in result['checks'])
  rows=[json.loads(line)for line in result['stdout'].splitlines()]
  for row in rows:row['compile']=bool(row['compile'])
  outputs[name]=rows
 report['regex'][lang]={'pass':outputs['reference']==outputs['candidate'],'cases':len(outputs['candidate'])}
for sc in json.loads((ROOT/'tests/scenarios/safety.json').read_text()):
 r=h.Run(sc,str(a.binary.resolve()),str(a.out/'safety'/sc['id'])).execute();report['safety'][sc['id']]={'pass':r['steps_ok']and all(c['pass']for c in r['checks'])}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:{'cases':len(report[k]),'passed':sum(x['pass']for x in report[k].values())}for k in ['cli','regex','safety']}));raise SystemExit(int(any(not x['pass']for k in ['cli','regex','safety']for x in report[k].values())))
