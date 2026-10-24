#!/usr/bin/env python3
"""Validate root-phase evidence without expanding historical release claims."""
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--reports',type=Path,default=ROOT/'validation/root-console');p.add_argument('--out',type=Path,required=True);a=p.parse_args();checks=[]
def read(name):return json.loads((a.reports/(name+'.json')).read_text())
def check(name,value):checks.append({'name':name,'pass':bool(value)})
build=read('build');digest=build['binary_sha256'];root=read('root');expected={s['id']for s in json.loads((ROOT/'tests/follow-up/scenarios/root.json').read_text())}
check('root-binary',root['candidate_sha256']==digest)
check('root-inventory',set(root['results'])==expected and len(expected)==27)
check('root-differential',all(x['match']and x['reference_checks']and x['candidate_checks']for x in root['results'].values()))
probes=read('namespace-probes');check('namespace-real-uids-and-device',set(probes)==expected and all(v['reference']==v['candidate']and v['reference']['euid']in (0,1000)and v['reference']['null_is_character_device']and v['reference']['null_device']==[1,3]for v in probes.values()))
check('backend-same-source',len(root['backend_sha256'])==64)
r=read('reference-build');check('reference-build',r['reference_sha256']==root['reference_sha256']and '--sysconfdir=/etc'in r['configure']and r['backend_sha256']==root['backend_sha256'])
r=read('safety-no-home');check('no-home-recovery',r['candidate_sha256']==digest and r['reference_status']==r['candidate_status']==0 and len(r['results'])==1 and all(x['deviation_id']=='Q-ROOT-NOHOME-001'and x['accepted']and x['reference_checks']and x['candidate_checks']for x in r['results'].values()))
r=read('ordinary-terminal');check('ordinary-binary',r['binary_sha256']==digest);check('ordinary-terminal',r['summary']==dict(recorded=303,full_matches=301,files_matches=302,skipped=6)and not any(r['worker_statuses']))
r=read('cli');check('cli',r['binary_sha256']==digest and r['summary']['compared']==r['summary']['matches']==38)
r=read('regex');check('regex',r['binary_sha256']==digest and sum(x['cases']for x in r['locales'])==162 and all(not x['differences']for x in r['locales']))
r=read('existing-safety');check('existing-safety',r['binary_sha256']==digest and len(r['results'])==2 and all(x['steps_ok']and x['binary_sha256']==digest and all(c['pass']for c in x['checks'])for x in r['results'].values()))
r=read('normal-backup');check('normal-backup',r['candidate_sha256']==digest and r['reference_status']==r['candidate_status']==0 and all(x['match']and x['reference_checks']and x['candidate_checks']for x in r['results'].values()))
r=read('checks');check('rust-and-harness-checks',all(v['status']==0 for v in r['checks'].values()))
r=read('console-probe');check('console-probe-preserves-terminal',r['probe_preserved_termios']is True);check('console-gate-honest',r['status']=='deferred'and r['probe']['real_vt']is False and all(v['status']=='unobserved'for v in r['checks'].values()))
result={'reference_commit':'6ed285c3ec7a1d228def4d4e7021c6ba269f620c','binary_sha256':digest,'source_sha256':build['build']['source_sha256'],'checks':checks,'automated_gates_pass':all(x['pass']for x in checks),'physical_vt':'deferred; probe identified a PTY, not a real console','scope':'Fixture user/mount namespaces, effective uid 0/1000, private NSS and root/device paths; no host-root privilege certification.'}
a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'passed':sum(x['pass']for x in checks)}));raise SystemExit(int(not result['automated_gates_pass']))
