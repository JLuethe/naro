#!/usr/bin/env python3
"""Bounded host qualification with an atomic checkpoint after each command."""
import argparse,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
from check_closure_regressions import SUITES
from check_wrap_undo import REFERENCE_SHA256
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
binary=a.out/'naro';shutil.copy2(a.binary,binary)
reference=a.out/'reference.bin';shutil.copy2(Path.home()/'src/nano-install/default/bin/nano',reference)
reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest()
if reference_sha256!=REFERENCE_SHA256:raise SystemExit('host reference differs from pinned executable')
env={**os.environ,'PATH':str(Path.home()/'.cargo/bin')+':'+os.environ['PATH']}
report={'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'reference_sha256':reference_sha256,'build':json.loads(subprocess.check_output([str(binary)],env={**env,'NARO_BUILD_INFO':'1'},text=True)),'checks':{},'state':'running'}
def save():
    tmp=a.out/'checkpoint.tmp';tmp.write_text(json.dumps(report,indent=2)+'\n');tmp.replace(a.out/'checkpoint.json')
def run(name,args):
    report['active']=name;save();start=time.time()
    with (a.out/(name+'.log')).open('w')as log:
        try:code=subprocess.run(args,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=3600).returncode
        except subprocess.TimeoutExpired:code=124
    report['checks'][name]={'status':code,'seconds':round(time.time()-start,2),'command':args};save()
    print(name,code,flush=True)
    if code:report['state']='failed';save();raise SystemExit(code)
def py(name,script,*args):run(name,[sys.executable,script,*map(str,args)])
for name,args in [('fmt',['cargo','fmt','--check']),('clippy',['cargo','clippy','--all-targets','--all-features','--','-D','warnings']),('rust',['cargo','test','--all-features'])]:run(name,args)
for name,script in [('comparator','spec/tools/test_compare_runs.py'),('harness','spec/tools/test_nanoharness.py'),('namespace','spec/tools/test_namespace_exec.py')]:py(name,script)
run('console-unit',[sys.executable,'-m','unittest','discover','-s','tests/console','-p','test_*.py'])
run('closure-unit',[sys.executable,'-m','unittest','discover','-s','tools','-p','test_closure_regressions.py'])
py('terminal','tools/validate_parallel.py','--binary',binary,'--out',a.out/'terminal','--jobs','4')
for suite in ['tools','edges','environments','supplement','backup','fifo-eof','signal-SIGTERM','signal-SIGHUP','vt-ioctl','root','root-nohome-tilde']:
    args=['--suite',suite,'--binary',binary,'--out',a.out/suite]
    if suite.startswith('root'):args+=['--reference',ROOT/'target/root-reference/install/bin/nano']
    py(suite,'tools/check_follow_up.py',*args)
for suite in SUITES:
    py(suite,'tools/check_follow_up.py','--suite',suite,'--binary',binary,'--reference',reference,'--out',a.out/suite)
py('closure-regressions','tools/check_closure_regressions.py','--base',a.out,'--binary',binary,'--reference',reference)
py('extras','tools/check_environment_extras.py','--binary',binary,'--reference',Path.home()/'src/nano-install/default/bin/nano','--out',a.out/'extras')
run('hooks-build',['cargo','build','--features','test-hooks','--target-dir',str(a.out/'hooks')])
py('panic','spec/tools/nanoharness.py','tests/follow-up/scenarios/panic.json','--binary',a.out/'hooks/debug/naro','--out',a.out/'panic')
run('credits-build',['cargo','build','--release','--features','credits','--target-dir',str(a.out/'credits')])
py('extensions','tools/check_extensions.py','--default',binary,'--credits',a.out/'credits/release/naro','--panic-runs',a.out/'panic','--out',a.out/'extensions')
py('large','tools/check_large_files.py','--binary',binary,'--out',a.out/'large')
py('package','tools/package.py','--binary',binary,'--out',a.out/'package')
py('package-check','tools/check_package.py','--archive',a.out/'package/naro-0.1.0-x86_64-unknown-linux-gnu.tar.gz','--source-archive',a.out/'package/naro-0.1.0-source.tar.gz','--out',a.out/'package-check')
report['state']='complete';report['active']=None;save()
