#!/usr/bin/env python3
"""Measure bounded fixture operations and verify every output byte."""
import argparse,base64,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'spec/tools'))
import nanoharness as h
p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
report={'binary_sha256':hashlib.sha256(a.binary.read_bytes()).hexdigest(),'timing_scope':'whole harness startup, load, edit, save, exit and capture; no performance budget','results':{}}
for mib in [1,10]:
 size=mib*1024*1024;line=b'0123456789 abcdefghijklmnopqrstuvwxyz\n';data=(line*(size//len(line))+b'x'*(size%len(line)-1)+b'\n')if size%len(line)else line*(size//len(line))
 assert len(data)==size
 tid='TEST-NEXT-UX-002-'+str(mib)+'MiB'
 sc=dict(id=tid,args=['-I','large.txt'],files={'work/large.txt':{'b64':base64.b64encode(data).decode()}},steps=[{'wait':{'text':'Read','timeout':30}},{'text':'X'},{'keys':['^S']},{'wait':{'text':'Wrote','timeout':30}},{'keys':['^X']},{'wait_exit':10}],expect={'exit_status':0})
 start=time.monotonic();r=h.Run(sc,str(a.binary.resolve()),str(a.out/tid)).execute();elapsed=time.monotonic()-start
 got=r['fixture']['work/large.txt'];expected=hashlib.sha256(b'X'+data).hexdigest();ok=got['sha256']==expected and got['size']==size+1 and r['steps_ok']and all(x['pass']for x in r['checks'])
 report['results'][tid]={'pass':ok,'input_bytes':size,'output_bytes':got['size'],'elapsed_seconds':elapsed,'output_sha256':got['sha256']}
 print(tid,ok,round(elapsed,3),flush=True)
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');raise SystemExit(int(any(not x['pass']for x in report['results'].values())))
