#!/usr/bin/env python3
"""Compare editors on guest /dev/tty1 using QEMU keyboard hardware events."""
import argparse,base64,hashlib,json,sys,time
from pathlib import Path
from console_vm import VM,rows
ROOT=Path(__file__).resolve().parents[1]

def norm(snapshot):
    return {'cols':snapshot['cols'],'rows':snapshot['rows'],'cursor':snapshot['cursor'],
            'chars':snapshot['chars'],'attrs':[a if c not in (0,32)else None for c,a in zip(snapshot['chars'],snapshot['attrs'])]}

def main():
 p=argparse.ArgumentParser();p.add_argument('--fixture',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--ids',nargs='*');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
 data='one two three\nfour five six\n\nseven eight\nlast\n'
 cases=[
  {'id':'TEST-VT-VM-NAV','data':data,'keys':[('right',()),('end',()),('home',()),('down',()),('up',()),('pgdn',()),('pgup',())]},
  {'id':'TEST-VT-VM-CTRL','data':data,'keys':[(k,('ctrl',))for k in ['right','right','left','end','home','down','up']]},
  {'id':'TEST-VT-VM-SHIFT','data':data,'keys':[(k,('shift',))for k in ['right','right','down','home','end']]},
  {'id':'TEST-VT-VM-CTRL-SHIFT','data':data,'keys':[(k,('ctrl','shift'))for k in ['right','down','home','end']]},
  {'id':'TEST-VT-VM-DELETE','data':data,'keys':[('right',('ctrl',)),('delete',('shift',)),('delete',('ctrl',)),('delete',('ctrl','shift'))],'save':True},
  {'id':'TEST-VT-VM-TAB','data':'    indented\n\tsecond\n','keys':[('tab',('shift',)),('tab',()),('tab',('shift',))],'save':True},
  {'id':'TEST-VT-VM-ALT','data':data,'keys':[(k,('alt',))for k in ['up','down','home','end','pgup','pgdn']]},
  {'id':'TEST-VT-VM-SHIFT-ALT','data':data,'keys':[(k,('shift','alt'))for k in ['right','left','up','down']]},
  {'id':'TEST-VT-VM-ALT-HORIZONTAL','data':data,'extra_files':{'second.txt':'second buffer\n'},'close_count':2,'args':['-I','sample.txt','second.txt'],'keys':[('right',('alt',)),('left',('alt',))]},
  {'id':'TEST-VT-VM-UNICODE','data':'cafe\u0301 xx 界\n','keys':[('right',()),('end',()),('left',()),('backspace',())],'save':True},
  {'id':'TEST-VT-VM-EXPANSION','data':data,'policy':'bind ^] "{right}{right}" main\n','keys':[('bracket_right',('ctrl',))]},
  {'id':'TEST-VT-VM-CANCEL','data':data,'keys':[('x',()),('x',('ctrl',)),('c',('ctrl',))],'discard':True},
  {'id':'TEST-VT-VM-TOOL','data':data,'policy':'syntax text "\\.txt$"\ncolor red "ZZZ"\nformatter missing-naro-formatter\n','keys':[('t',('ctrl',)),('o',('ctrl',))],'settle':.3},
  {'id':'TEST-VT-VM-MACRO','data':data,'keys':[('esc',()),('semicolon',('shift',)),('right',()),('right',()),('esc',()),('semicolon',('shift',)),('semicolon',('alt',))]},
  {'id':'TEST-VT-VM-MACRO-CTRL','data':data,'keys':[('esc',()),('semicolon',('shift',)),('end',('ctrl',)),('esc',()),('semicolon',('shift',)),('home',('ctrl',)),('semicolon',('alt',))]},
  {'id':'TEST-VT-VM-HELP','data':data,'keys':[('g',('ctrl',)),('pgdn',()),('x',('ctrl',))]},
  {'id':'TEST-VT-VM-MODERN','data':data,'args':['-I','-/','sample.txt'],'keys':[('right',('ctrl',)),('end',('ctrl',))],'exit_key':'q'},
  {'id':'TEST-VT-VM-TERM','data':data,'keys':[('x',())],'signal':15},
  {'id':'TEST-VT-VM-HUP','data':data,'keys':[('x',())],'signal':1}]
 cases=[c for c in cases if not a.ids or c['id']in a.ids]
 v=VM(a.fixture);report={'reference_commit':'6ed285c3ec7a1d228def4d4e7021c6ba269f620c','backend':'QEMU/KVM Linux VT1 with emulated PS/2 keyboard; no PTY for app fds','guest':v.rpc('metadata'),'results':{}}
 for c in cases:
  tid=c['id'];collected={}
  for kind in ['reference','candidate']:
   files={'sample.txt':c['data'].encode()};args=c.get('args',['-I','sample.txt'])
   for name,value in c.get('extra_files',{}).items():files[name]=value.encode()
   if 'policy'in c:files['policy']=c['policy'].encode();args=['--rcfile','policy','sample.txt']
   started=v.start(kind,tid,args=args,files=files);frames={'start':v.snapshot()};v.keys=[]
   for i,(key,mods)in enumerate(c['keys']):
    v.press(key,mods)
    if v.rpc('ping')['info']['vt_state'][0]!=1:v.press('f1',['alt'])
    time.sleep(c.get('settle',0));frames[str(i)]=v.snapshot()
   if 'signal'in c:v.rpc('signal',signal=c['signal'])
   else:
    if c.get('save'):v.press('s',['ctrl'])
    v.press(c.get('exit_key','x'),['ctrl'])
    if c.get('discard'):v.press('n')
    for _ in range(c.get('close_count',1)-1):v.press(c.get('exit_key','x'),['ctrl'])
   exited=v.finish();collected[kind]={'started':started,'frames':frames,'keyboard':v.keys,'exited':exited}
   (a.out/(tid+'-'+kind+'.json')).write_text(json.dumps(collected[kind],indent=1)+'\n')
  diffs=[];r,t=collected['reference'],collected['candidate']
  for name in r['frames']:
   left,right=norm(r['frames'][name]),norm(t['frames'][name])
   for field in left:
    if left[field]!=right[field]:diffs.append({'frame':name,'field':field})
  if r['exited']['exit']!=t['exited']['exit']:diffs.append({'field':'exit'})
  for kind in ['reference','candidate']:
   if not collected[kind]['exited']['termios_restored']:diffs.append({'field':kind+'.termios_restored'})
   if not collected[kind]['exited']['console_modes_restored']:diffs.append({'field':kind+'.console_modes_restored'})
  for kind in ['reference','candidate']:
   probe=json.loads(base64.b64decode(collected[kind]['exited']['files']['probe.json']['b64']))
   if probe['uid']!=1000 or probe['euid']!=1000 or probe['isatty']!=[True,True]or probe['vt_state'][0]!=1:diffs.append({'field':kind+'.real_vt_identity'})
  appfiles=lambda x:{k:v for k,v in x['exited']['files'].items()if k!='probe.json'}
  if appfiles(r)!=appfiles(t):diffs.append({'field':'files'})
  for kind,value in collected.items():
   if tid in ('TEST-VT-VM-MACRO','TEST-VT-VM-MACRO-CTRL'):
    if 'Recording a macro'not in rows(value['frames']['1'])[-3]or value['frames']['6']['cursor']!=([4,1]if tid=='TEST-VT-VM-MACRO'else[13,1]):diffs.append({'field':kind+'.macro_assertion'})
   if tid=='TEST-VT-VM-CTRL'and value['frames']['3']['cursor']!=[0,6]:diffs.append({'field':kind+'.ctrl_end_assertion'})
   if tid=='TEST-VT-VM-UNICODE'and not rows(value['frames']['start'])[1].startswith('cafe xx'):diffs.append({'field':kind+'.unicode_assertion'})
  report['results'][tid]={'match':not diffs,'differences':diffs,'reference_sha256':r['started']['binary_sha256'],'candidate_sha256':t['started']['binary_sha256']};print(tid,'MATCH'if not diffs else diffs,flush=True)
 (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');v.close();raise SystemExit(int(any(not x['match']for x in report['results'].values())))
if __name__=='__main__':main()
