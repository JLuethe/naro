#!/usr/bin/env python3
"""Verify upload/reconnect on the disposable VM, preserving its installed binary."""
import argparse,base64,hashlib,json,time
from pathlib import Path
from console_vm import VM

p=argparse.ArgumentParser();p.add_argument('--fixture',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=False)
v=VM(a.fixture);checks={}
def installed():
    started=v.start('candidate','TEST-VT-TRANSPORT-VERIFY');v.press('x',['ctrl']);ended=v.finish()
    assert ended['exit']==0 and ended['termios_restored']
    return started['binary_sha256']
def rejected(op,**args):
    try:v.rpc(op,**args)
    except RuntimeError:return
    raise AssertionError('invalid upload accepted')
before=installed()
for label,step in [('incomplete',lambda:rejected('upload-finish')),
                   ('offset',lambda:rejected('upload-chunk',offset=1,b64='YQ==')),
                   ('digest',lambda:(v.rpc('upload-chunk',offset=0,b64='YQ=='),rejected('upload-finish')))]:
    v.rpc('upload-start',name='candidate',size=1,sha256='0'*64);step()
    assert installed()==before;checks[label]=True
v.rpc('upload-start',name='candidate',size=2,sha256=hashlib.sha256(b'ab').hexdigest())
v.rpc('upload-chunk',offset=0,b64='YQ==')
v.control.sendall(b'{"op":"upload-chunk","offset":1,"b64":"')
v.close();time.sleep(.3)
v=VM(a.fixture);assert v.rpc('ping')['ready'];assert installed()==before
checks['disconnect_discards_partial_request_and_upload']=True
result=v.install('candidate',a.binary);assert installed()==result['sha256'];checks['verified_chunked_install']=True
v.start('candidate','TEST-VT-TRANSPORT-BUSY');rejected('upload-start',name='candidate',size=1,sha256='0'*64);v.press('x',['ctrl']);assert v.finish()['exit']==0;checks['running_editor_rejects_upload']=True
report={'checks':checks,'before_sha256':before,'installed':result,'guest':v.rpc('metadata')};v.close()
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(checks))
