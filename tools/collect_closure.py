#!/usr/bin/env python3
"""Collect hash-linked closure evidence and reject incomplete or mixed results."""
import argparse,hashlib,json,shutil
from types import SimpleNamespace
from pathlib import Path
from check_closure_regressions import SUITES, validate_suite
from check_wrap_undo import REFERENCE_SHA256, source_fingerprint, verification_fingerprint
from release_gate_evidence import GATE_SCHEMA, classification_counts, policy_identity, validate_corpus, validate_follow_up
from check_console_vm import validate_console_evidence
ROOT=Path(__file__).resolve().parents[1]
REF='6ed285c3ec7a1d228def4d4e7021c6ba269f620c'
REQUIRED_HOST_STAGES = frozenset([
 'fmt','clippy','rust','rust-default','comparator','harness','namespace',
 'identity-expectations-unit','identity-review-unit','gate-evidence-unit',
 'console-identity-unit','frozen-launcher-unit','frozen-process-unit','console-unit',
 'closure-unit','reference-replay','terminal','tools','edges','environments',
 'supplement','backup','fifo-eof','signal-SIGTERM','signal-SIGHUP','vt-ioctl',
 'root','root-nohome-tilde','closure-regressions','extras','cli','branding',
 'identity-layout','hooks-build','credits-build','panic','extensions','large',
 'package','package-check',*SUITES])

def collect_evidence(inputs, output=None):
 a=SimpleNamespace(**{key:Path(value) for key,value in inputs.items()},out=Path(output) if output is not None else None)
 if a.out is not None and a.out.exists() and any(p.name!='README.md'for p in a.out.iterdir()):raise SystemExit('preserve evidence: output may contain only README.md before collection')
 if a.out is not None:a.out.mkdir(parents=True,exist_ok=True)
 checks=[];accounting={}
 def read(path):return json.loads(path.read_text())
 def copy(path,name):
     value=read(path)
     if a.out is not None:(a.out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
     return value
 def check(name,value):checks.append({'name':name,'pass':bool(value)})
 h=copy(a.host/'checkpoint.json','host-checks');u=copy(a.package/'build.json','ubuntu-build')
 hd=h['binary_sha256'];ud=u['binary_sha256'];source=h['build']['source_sha256']
 check('host-command-completion',h['state']=='complete' and h['active'] is None and REQUIRED_HOST_STAGES <= set(h['checks']) and all(type(v['status']) is int and v['status']==0 for v in h['checks'].values()))
 check('source-fingerprint',u['compiled_build']['source_sha256']==source)
 check('host-verification-fingerprint',h.get('verification_sha256')==verification_fingerprint())
 runtime=copy(a.ubuntu/'runtime-inputs.json','ubuntu-runtime-inputs')
 check('ubuntu-verification-fingerprint',runtime.get('verification_fingerprint')==verification_fingerprint())
 check('ubuntu-runtime-inputs',runtime.get('candidate_sha256')==ud and runtime.get('source_fingerprint')==source and runtime.get('reference_sha256')==hashlib.sha256((a.ubuntu/'reference.bin').read_bytes()).hexdigest())
 check('current-source-fingerprint',source==source_fingerprint())
 check('default-features',h['build']['features']==u['compiled_build']['features']=='')
 check('release-version',h['build']['version']==u['compiled_build']['version']=='0.1.1')
 check('reference-identity',u['reference_commit']==REF)
 check('ubuntu-pipeline-complete',(a.ubuntu/'complete').read_text().strip()=='completed')
 check('host-frozen-binary',hashlib.sha256((a.host/'naro').read_bytes()).hexdigest()==hd)
 check('host-root-reference',hashlib.sha256((a.host/'root-reference.bin').read_bytes()).hexdigest()==h['root_reference_sha256'])
 check('ubuntu-frozen-binary',hashlib.sha256((a.ubuntu/'naro').read_bytes()).hexdigest()==ud)
 suites=['tools','edges','environments','supplement','backup','fifo-eof','signal-SIGTERM','signal-SIGHUP']
 for label,base,digest in [('host',a.host,hd),('ubuntu',a.ubuntu,ud)]:
     reference_sha256=hashlib.sha256((base/'reference.bin').read_bytes()).hexdigest()
     check(label+'-frozen-reference',label!='host' or reference_sha256==h.get('reference_sha256')==REFERENCE_SHA256)
     terminal_dir=base/('terminal'if label=='host'else'candidate')
     terminal,counts,problems=validate_corpus(terminal_dir,digest,reference_sha256,portable_locale=label=='ubuntu')
     copy(terminal_dir/'report.json',label+'-terminal')
     accounting[label+'-terminal']=counts
     check(label+'-terminal-reopened-evidence',not problems);checks[-1]['problems']=problems
     historical=[]
     for suite in suites+['vt-ioctl']:
         allowed={}
         if suite in ('signal-SIGTERM','signal-SIGHUP'):
             allowed={'TEST-NEXT-TOOL-003-'+suite.split('-',1)[1]:'Q-TOOL-001'}
         r,counts,problems=validate_follow_up(base/suite,suite,digest,source,reference_sha256,allowed,portable_locale=label=='ubuntu')
         copy(base/suite/'report.json',label+'-'+suite)
         accounting[label+'-'+suite]=counts
         check(label+'-'+suite+'-reopened-evidence',not problems);checks[-1]['problems']=problems
         if suite=='vt-ioctl':check(label+'-ioctl-inventory',counts['recorded']==8 and counts['accepted']==8 and not counts['unexpected'])
         else:historical.append(counts)
     total={key:sum(c[key]for c in historical)for key in historical[0]}
     check(label+'-follow-up-inventory',total['recorded']==total['accepted']==53 and total['declared_deviations']==2 and not total['unexpected'])
     accounting[label+'-historical']=total
     for suite in SUITES:
         r,problems=validate_suite(base/suite,suite,digest,source,reference_sha256 or '')
         check(label+'-'+suite+'-evidence',not problems)
         checks[-1]['problems']=problems
         if r is not None:
             accounting[label+'-'+suite]=classification_counts(r['results'].values())
             if a.out is not None:(a.out/(label+'-'+suite+'.json')).write_text(json.dumps(r,indent=2)+'\n')
     if label=='host':
         check('host-new-suite-command-completion',all(
             type(h['checks'].get(name,{}).get('status')) is int and h['checks'][name]['status']==0
             for name in [*SUITES,'closure-regressions']))
     r=copy(base/'extras/report.json',label+'-extras')
     check(label+'-cli-regex-safety',r['candidate_sha256']==digest and len(r['cli'])==38 and sum(v['cases']for v in r['regex'].values())==162 and len(r['safety'])==2 and all(v['pass']for k in ['cli','regex','safety']for v in r[k].values()))
     r=copy(base/'large/report.json',label+'-large')
     check(label+'-large',r['binary_sha256']==digest and len(r['results'])==2 and all(v['pass']for v in r['results'].values()))
     panic={}
     for path in sorted((base/'panic').glob('TEST-*/result.json')):
         r=read(path);panic[path.parent.name]={'binary_sha256':r['binary_sha256'],'pass':r['steps_ok']and all(v['pass']for v in r['checks']),'checks':r['checks']}
     if a.out is not None:(a.out/(label+'-panic.json')).write_text(json.dumps(panic,indent=2)+'\n')
     check(label+'-panic',len(panic)==3 and all(v['pass']for v in panic.values()))
 for suite,count in [('root',27),('root-nohome-tilde',1)]:
     allowed={}if suite=='root'else{'TEST-ROOT-HOME-002-NO-HOME-TILDE':'Q-ROOT-NOHOME-001'}
     r,counts,problems=validate_follow_up(a.host/suite,suite,hd,source,h['root_reference_sha256'],allowed)
     copy(a.host/suite/'report.json','host-'+suite);accounting['host-'+suite]=counts
     check(suite+'-reopened-evidence',not problems);checks[-1]['problems']=problems
     check(suite+'-inventory',counts['recorded']==count and counts['accepted']==count and not counts['unexpected'])
 r=copy(a.host/'extensions/report.json','host-extensions');check('extensions',len(r)==6 and r['default']['binary_sha256']==hd and all(v['pass']for v in r.values()))
 guest_reference=hashlib.sha256((a.ubuntu/'reference.bin').read_bytes()).hexdigest()
 for label,folder,digest in [('host',a.vm_host,hd),('ubuntu',a.vm_ubuntu,ud)]:
     r,counts,problems=validate_console_evidence(folder,digest,guest_reference)
     copy(folder/'report.json',label+'-console');accounting[label+'-console']=counts
     check(label+'-console-reopened-evidence',not problems);checks[-1]['problems']=problems
     copy(folder/'vm-provenance.json',label+'-console-provenance')
 r=copy(a.transport/'report.json','transport');check('transport',len(r['checks'])==6 and all(r['checks'].values()))
 r=copy(a.package_check/'report.json','ubuntu-package');check('ubuntu-package',r['binary_sha256']==ud and len(r['checks'])==15 and all(v['pass']for v in r['checks']))
 r=copy(a.host/'package-check/report.json','host-package');check('host-package',r['binary_sha256']==hd and len(r['checks'])==15 and all(v['pass']for v in r['checks']))
 if a.out is not None:shutil.copy2(a.package/'SHA256SUMS',a.out/'SHA256SUMS')
 gate={'schema':GATE_SCHEMA,'verification_sha256':verification_fingerprint(),'identity_policy':policy_identity(),'inputs':{key:str(Path(value).resolve())for key,value in inputs.items()},'accounting':accounting,'reference_commit':REF,'source_sha256':source,'host_binary_sha256':hd,'ubuntu_binary_sha256':ud,'checks':checks,'pass':all(v['pass']for v in checks),'deferred':['optional tiny profile','physical keyboard/operator console certification'],'scope':'Recorded Linux host and Ubuntu userspace; genuine guest VT with emulated PS/2 keys; private root namespaces. No physical hardware or general host-root certification.'}
 gate['required_regression_inventory']=SUITES
 if a.out is not None:(a.out/'gate.json').write_text(json.dumps(gate,indent=2)+'\n')
 return gate


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['host','ubuntu','vm-host','vm-ubuntu','transport','package','package-check','out']:
  p.add_argument('--'+name,type=Path,required=True)
 args=vars(p.parse_args());out=args.pop('out')
 try:gate=collect_evidence(args,out)
 except (OSError,ValueError,KeyError,TypeError,IndexError) as error:
  print(json.dumps({'schema':GATE_SCHEMA,'pass':False,'error':str(error)}));return 1
 print(json.dumps({'schema':GATE_SCHEMA,'checks':len(gate['checks']),'passed':sum(c['pass']for c in gate['checks']),'failures':[c['name']for c in gate['checks']if not c['pass']],'accounting':gate['accounting']}))
 return int(not gate['pass'])


if __name__=='__main__':raise SystemExit(main())
