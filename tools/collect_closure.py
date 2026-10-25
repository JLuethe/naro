#!/usr/bin/env python3
"""Collect hash-linked closure evidence and reject incomplete or mixed results."""
import argparse,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REF='6ed285c3ec7a1d228def4d4e7021c6ba269f620c'
p=argparse.ArgumentParser()
for name in ['host','ubuntu','vm-host','vm-ubuntu','transport','package','package-check','out']:p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args()
if a.out.exists() and any(p.name!='README.md'for p in a.out.iterdir()):raise SystemExit('preserve evidence: output may contain only README.md before collection')
a.out.mkdir(parents=True,exist_ok=True);checks=[]
def read(path):return json.loads(path.read_text())
def copy(path,name):
    value=read(path);(a.out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n');return value
def check(name,value):checks.append({'name':name,'pass':bool(value)})
h=copy(a.host/'checkpoint.json','host-checks');u=copy(a.package/'build.json','ubuntu-build')
hd=h['binary_sha256'];ud=u['binary_sha256'];source=h['build']['source_sha256']
check('host-command-completion',h['state']=='complete' and h['active'] is None and all(v['status']==0 for v in h['checks'].values()))
check('source-fingerprint',u['compiled_build']['source_sha256']==source)
check('default-features',h['build']['features']==u['compiled_build']['features']=='')
check('reference-identity',u['reference_commit']==REF)
check('ubuntu-pipeline-complete',(a.ubuntu/'complete').read_text().strip()=='completed')
check('host-frozen-binary',hashlib.sha256((a.host/'naro').read_bytes()).hexdigest()==hd)
check('ubuntu-frozen-binary',hashlib.sha256((a.ubuntu/'naro').read_bytes()).hexdigest()==ud)
suites=['tools','edges','environments','supplement','backup','fifo-eof','signal-SIGTERM','signal-SIGHUP']
for label,base,digest in [('host',a.host,hd),('ubuntu',a.ubuntu,ud)]:
    terminal=copy(base/('terminal'if label=='host'else'candidate')/'report.json',label+'-terminal')
    check(label+'-terminal',terminal['binary_sha256']==digest and terminal['summary']==dict(recorded=303,full_matches=301,files_matches=302,skipped=6) and not any(terminal['worker_statuses']))
    total=matches=0
    for suite in suites+['vt-ioctl']:
        r=copy(base/suite/'report.json',label+'-'+suite)
        expected={s['id']for s in read(ROOT/f'tests/follow-up/scenarios/{suite}.json')}
        check(label+'-'+suite+'-identity',set(r['results'])==expected and r['candidate_sha256']==digest and r['candidate_build']['source_sha256']==source and r['reference_status']==r['candidate_status']==0)
        check(label+'-'+suite+'-assertions',all(v['accepted'] and v['reference_checks'] and v['candidate_checks'] for v in r['results'].values()))
        if suite=='vt-ioctl':check(label+'-ioctl-exact',len(r['results'])==8 and all(v['match']for v in r['results'].values()))
        else:
            total+=len(r['results']);matches+=sum(v['match']for v in r['results'].values())
            check(label+'-'+suite+'-only-declared-differences',all(v['match']or (suite.startswith('signal-') and v['deviation_id']=='Q-TOOL-001')for v in r['results'].values()))
    check(label+'-follow-up-counts',total==53 and matches==51)
    r=copy(base/'extras/report.json',label+'-extras')
    check(label+'-cli-regex-safety',r['candidate_sha256']==digest and len(r['cli'])==38 and sum(v['cases']for v in r['regex'].values())==162 and len(r['safety'])==2 and all(v['pass']for k in ['cli','regex','safety']for v in r[k].values()))
    r=copy(base/'large/report.json',label+'-large')
    check(label+'-large',r['binary_sha256']==digest and len(r['results'])==2 and all(v['pass']for v in r['results'].values()))
    panic={}
    for path in sorted((base/'panic').glob('TEST-*/result.json')):
        r=read(path);panic[path.parent.name]={'binary_sha256':r['binary_sha256'],'pass':r['steps_ok']and all(v['pass']for v in r['checks']),'checks':r['checks']}
    (a.out/(label+'-panic.json')).write_text(json.dumps(panic,indent=2)+'\n')
    check(label+'-panic',len(panic)==3 and all(v['pass']for v in panic.values()))
for suite,count in [('root',27),('root-nohome-tilde',1)]:
    r=copy(a.host/suite/'report.json','host-'+suite)
    check(suite+'-identity',r['candidate_sha256']==hd and r['candidate_build']['source_sha256']==source and r['candidate_status']==r['reference_status']==0 and set(r['results'])=={s['id']for s in read(ROOT/f'tests/follow-up/scenarios/{suite}.json')} and len(r['results'])==count)
    check(suite+'-assertions',all(v['accepted']and v['reference_checks']and v['candidate_checks']and (v['match']if suite=='root'else v['deviation_id']=='Q-ROOT-NOHOME-001')for v in r['results'].values()))
r=copy(a.host/'extensions/report.json','host-extensions');check('extensions',len(r)==6 and r['default']['binary_sha256']==hd and all(v['pass']for v in r.values()))
for label,folder,digest in [('host',a.vm_host,hd),('ubuntu',a.vm_ubuntu,ud)]:
    r=copy(folder/'report.json',label+'-console')
    check(label+'-console',r['reference_commit']==REF and len(r['results'])==19 and all(v['match']and not v['differences']and v['candidate_sha256']==digest for v in r['results'].values()))
    check(label+'-console-identity',r['guest']['info']['vt_state'][0]==1 and r['guest']['info']['device']=='/dev/tty1')
    provenance=folder/'vm-provenance.json'
    check(label+'-console-provenance',provenance.exists())
    if provenance.exists():copy(provenance,label+'-console-provenance')
r=copy(a.transport/'report.json','transport');check('transport',len(r['checks'])==6 and all(r['checks'].values()))
r=copy(a.package_check/'report.json','ubuntu-package');check('ubuntu-package',r['binary_sha256']==ud and len(r['checks'])==15 and all(v['pass']for v in r['checks']))
r=copy(a.host/'package-check/report.json','host-package');check('host-package',r['binary_sha256']==hd and all(v['pass']for v in r['checks']))
shutil.copy2(a.package/'SHA256SUMS',a.out/'SHA256SUMS')
gate={'reference_commit':REF,'source_sha256':source,'host_binary_sha256':hd,'ubuntu_binary_sha256':ud,'checks':checks,'pass':all(v['pass']for v in checks),'deferred':['optional tiny profile','physical keyboard/operator console certification'],'scope':'Recorded Linux host and Ubuntu userspace; genuine guest VT with emulated PS/2 keys; private root namespaces. No physical hardware or general host-root certification.'}
(a.out/'gate.json').write_text(json.dumps(gate,indent=2)+'\n');print(json.dumps({'checks':len(checks),'passed':sum(v['pass']for v in checks),'failures':[v['name']for v in checks if not v['pass']]}));raise SystemExit(int(not gate['pass']))
