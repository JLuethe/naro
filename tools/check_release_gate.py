#!/usr/bin/env python3
"""Verify hash-linked preview evidence; never tag, upload or publish."""
import argparse,json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--reports',type=Path,default=ROOT/'validation/follow-up');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
checks=[]
def check(name,value):checks.append({'name':name,'pass':bool(value)})
def read(name):return json.loads((a.reports/(name+'.json')).read_text())
host=read('host-environment');digest=host['binary_sha256'];source=host['build']['source_sha256']
for name in ['terminal','cli','regex','safety','tools','edges','environments','supplement','backup','fifo-eof','signal-SIGTERM','signal-SIGHUP','large','package','assets','assets-without-checkout']:
 r=read('host-'+name);key='candidate_sha256'if 'candidate_sha256'in r else 'binary_sha256'
 check('host-'+name+'-binary',r.get(key)==digest)
 if name=='terminal':check('host-terminal',r['summary']==dict(recorded=303,full_matches=301,files_matches=302,skipped=6)and not any(r['worker_statuses']))
 elif name=='cli':check('host-cli',r['summary']['compared']==38 and r['summary']['matches']==38)
 elif name=='regex':check('host-regex',sum(x['cases']for x in r['locales'])==162 and not any(x['differences']for x in r['locales']))
 elif name=='safety':check('host-safety',len(r['results'])==2 and all(x['steps_ok']and all(c['pass']for c in x['checks'])for x in r['results'].values()))
 elif 'candidate_status'in r:check('host-'+name,r['candidate_status']==r['reference_status']==0 and all(x['accepted']and x['reference_checks']and x['candidate_checks']for x in r['results'].values()))
 elif 'checks'in r:check('host-'+name,all(c['pass']for c in r['checks']))
 else:check('host-'+name,all(c['pass']for c in r['results'].values()))
r=read('host-extensions');check('extensions-and-panic',len(r)==6 and all(c['pass']for c in r.values())and r['default']['binary_sha256']==digest)
r=read('operator');check('interactive-installed-copy',r['binary_sha256']==digest and all(c['pass']for c in r['checks']))
r=read('checks');check('format-clippy-unit-comparator-harness',all(v['status']==0 for v in r['checks'].values()))
r=read('ubuntu-terminal');ubuntu=r['binary_sha256'];check('ubuntu-full-corpus',r['summary']==dict(recorded=303,full_matches=301,files_matches=302,skipped=6)and not any(r['worker_statuses']))
for name in ['tools','edges','environments','supplement','backup','fifo-eof','signal-SIGTERM','signal-SIGHUP']:
 r=read('ubuntu-'+name);check('ubuntu-'+name,r['candidate_sha256']==ubuntu and r['candidate_build']['source_sha256']==source and r['candidate_status']==r['reference_status']==0 and all(x['accepted']and x['reference_checks']and x['candidate_checks']for x in r['results'].values()))
r=read('ubuntu-extras');check('ubuntu-cli-regex-safety',r['candidate_sha256']==ubuntu and len(r['cli'])==38 and sum(x['cases']for x in r['regex'].values())==162 and len(r['safety'])==2 and all(x['pass']for k in ['cli','regex','safety']for x in r[k].values()))
r=read('ubuntu-panic');check('ubuntu-panic',len(r)==3 and all(x['pass']for x in r.values()))
r=read('ubuntu-large');check('ubuntu-large',r['binary_sha256']==ubuntu and all(x['pass']for x in r['results'].values()))
r=read('ubuntu-package');check('ubuntu-archive-install-source-assets',r['binary_sha256']==ubuntu and all(c['pass']for c in r['checks']))
result={'reference_commit':'6ed285c3ec7a1d228def4d4e7021c6ba269f620c','host_binary_sha256':digest,'ubuntu_binary_sha256':ubuntu,'source_sha256':source,'checks':checks,'automated_and_agent_operator_gates_pass':all(c['pass']for c in checks),'scope':read('limits')['scope'],'deferred':[x['test']for x in read('limits')['deferred']],'publication':'No tag or release published; separate explicit action.'}
a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'passed':sum(c['pass']for c in checks)}));raise SystemExit(int(not result['automated_and_agent_operator_gates_pass']))
