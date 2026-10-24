#!/usr/bin/env python3
"""Check optional credits and recovery instrumentation without touching user files."""
import argparse,base64,hashlib,json,os,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'spec/tools'))
import nanoharness as h
p=argparse.ArgumentParser();p.add_argument('--default',type=Path,required=True);p.add_argument('--credits',type=Path,required=True);p.add_argument('--panic-runs',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
checks={}
for name,binary,status in [('default',a.default,1),('credits',a.credits,0)]:
 sc=dict(id='TEST-NEXT-CREDITS-002-'+name,args=['--credits'],stdin='',stdout_redirect=True,hold_tty=True,steps=[{'wait_exit':5}],expect={'exit_status':status})
 r=h.Run(sc,str(binary.resolve()),str(a.out/name)).execute()
 ok=r['steps_ok'] and all(c['pass']for c in r['checks'])
 if name=='credits':ok=ok and r['stdout']==(ROOT/'CREDITS.md').read_text()and r['stderr']=='' and r['fixture']==r['initial_fixture'] and r['bracketed_paste_set']==r['bracketed_paste_reset']==0 and not r['trace_final_modes']['alternate_screen']
 else:ok=ok and 'unrecognized option'in r['stderr']
 checks[name]={'pass':ok,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest()}
checks['production-no-panic-hook']={'pass':b'NARO_TEST_PANIC_DIR'not in a.default.read_bytes()}
for path in sorted(a.panic_runs.glob('TEST-*/result.json')):
 r=json.loads(path.read_text());ok=r['steps_ok']and all(c['pass']for c in r['checks'])
 if 'NAMELESS'in path.parent.name:
  saves=[v for k,v in r['fixture'].items()if re.fullmatch(r'work/nano\.\d+\.save',k)]
  ok=ok and len(saves)==1 and saves[0]['mode']=='0o600'and base64.b64decode(saves[0]['b64'])==b'X\n'
 checks[path.parent.name]={'pass':ok,'binary_sha256':r['binary_sha256']}
(a.out/'report.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks,indent=2));raise SystemExit(int(any(not c['pass']for c in checks.values())))
