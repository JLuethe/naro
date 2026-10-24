#!/usr/bin/env python3
"""Generate fixture-only cases for reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c."""
from pathlib import Path
import copy,json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tests/follow-up/scenarios';OUT.mkdir(parents=True,exist_ok=True)
ALT='''#!/usr/bin/python3
import os,sys,stat,json,signal,time
p=sys.argv[-1]; data=open(p,'rb').read();home=os.environ['HOME']
open(home+'/tool-input','wb').write(data)
json.dump({'args':sys.argv[1:-1],'mode':oct(stat.S_IMODE(os.stat(p).st_mode)),'extension':os.path.splitext(p)[1],'private':os.path.dirname(p)==os.environ['TMPDIR']},open(home+'/tool-meta','w'),sort_keys=True)
mode=os.environ.get('TOOL_MODE','replace'); code=int(os.environ.get('TOOL_EXIT','0'))
if mode=='sleep':
 open(home+'/ready','w').write('ready');time.sleep(2)
if mode!='unchanged':
 value=data.replace(b'teh',b'RIGHT\\nNEW' if mode=='grow' else b'the')
 stamp=os.stat(p).st_mtime_ns
 open(p,'wb').write(value);os.utime(p,ns=(stamp+1000000000,stamp+1000000000))
if code<0:os.kill(os.getpid(),-code)
sys.exit(code)
'''
SPELL='''#!/usr/bin/python3
import os,sys,re
value=sys.stdin.buffer.read();open(os.environ['HOME']+'/tool-input','wb').write(value)
for word in re.findall(rb'\\bteh\\b',value):sys.stdout.buffer.write(word+b'\\n')
'''
def snap(name):return {'snapshot':name,'quiet':80}
def selection(start,end,back=False):
 a,b=(end,start)if back else(start,end)
 return [{'keys':['Right']*a+['M-A']+(['Right']*(b-a)if b>=a else['Left']*(a-b))}]
def close():return [{'keys':['^X']},{'sleep':100},{'text':'y\r'},{'wait_exit':5}]
def base(tid,data=b'pre teh post\nout teh end\n',args=None):
 return dict(id=tid,args=args or ['-I','-s','altspell --flag','f.txt'],files={'work/f.txt':{'hex':data.hex()},'bin/altspell':{'text':ALT,'mode':'0755'}},steps=[{'settle':200}],expect={'exit_status':0,'temp_empty':True})
def spellcase(tid,start=4,end=7,back=False,mode='replace',data=b'pre teh post\nout teh end\n'):
 s=base(tid,data);s['env']={'TOOL_MODE':mode};s['steps']+=selection(start,end,back)+[snap('selection'),{'keys':['^T','^T']},{'settle':200},snap('corrected'),{'keys':['M-U']},snap('undo'),{'keys':['M-E']},snap('redo')]+close()
 s['expect']['files']={'home/tool-input':{'hex':data[start:end].hex()}}
 return s
cases=[spellcase('TEST-NEXT-SPELL-001-F'),spellcase('TEST-NEXT-SPELL-001-B',back=True)]
for name,data,mark in [('MARK',b'pre teh post\n',True),('BUFFER',b'',False)]:
 s=base('TEST-NEXT-SPELL-002-'+name,data)
 s['steps']+=([{'keys':['M-A']}]if mark else[])+[{'keys':['^T','^T']},snap('empty')]+close()
 s['expect']['files']={'home/tool-input':None};cases.append(s)
s=spellcase('TEST-NEXT-SPELL-003-BYTES',4,13,data=b'pre \xc3\xa9\xff\x00 teh\r\nend\r\n')
# Selection uses End to include the converted line payload without CRLF.
s['steps']=[{'settle':200}]+[{'keys':['Right']*4+['M-A','End']}]+s['steps'][2:]
s['expect']['files']={'home/tool-input':{'hex':b'\xc3\xa9\xff\x00 teh'.hex()}};cases.append(s)
for back in [False,True]:cases.append(spellcase('TEST-NEXT-SPELL-004-'+('B'if back else'F'),back=back,mode='grow'))
for code in [0,1,2,9,-15]:
 s=spellcase('TEST-NEXT-SPELL-005-EXIT'+str(abs(code))+('S'if code<0 else''));s['env']['TOOL_EXIT']=str(code);cases.append(s)
cases.append(spellcase('TEST-NEXT-SPELL-005-MTIME',mode='unchanged'))
for name,cancel in [('ALL',False),('CANCEL',True)]:
 data=b'teh pre teh mid teh post teh\n';s=base('TEST-NEXT-SPELL-006-'+name,data,args=['-I','f.txt']);s['files']['bin/hunspell']={'text':SPELL,'mode':'0755'}
 s['steps']+=selection(8,19)+[snap('selection'),{'keys':['^T','^T']},{'wait':{'text':'Edit a replacement'}},snap('prompt')]
 if cancel:s['steps']+=[{'keys':['^C']}]
 else:s['steps']+=[{'keys':['^A','^K']},{'text':'correct\r'},{'wait':{'text':'Replace this instance?'}},{'text':'a'}]
 s['steps']+=[{'wait':{'text':'Finished checking spelling'}},snap('finished')]+close();s['expect']['files']={'home/tool-input':{'text':'teh mid teh'}};cases.append(s)
s=base('TEST-NEXT-SPELL-002-INTERNAL',args=['-I','f.txt']);s['files']['bin/hunspell']={'text':SPELL,'mode':'0755'};s['steps']+=[{'keys':['M-A','^T','^T']},{'wait':{'text':'Finished checking spelling'}},snap('empty')]+close();s['expect']['files']={'home/tool-input':{'text':''}};cases.append(s)
for name,available in [('MARK',True),('MISSING',False)]:
 s=base('TEST-NEXT-TOOL-001-'+name,args=['f.txt']);s['files']['home/.nanorc']={'text':'syntax text "\\.txt$"\ncolor red "NOPE"\n'+('formatter altspell\n'if available else'')};s['steps']+=selection(4,7)+[{'keys':['^T','^O']},snap('formatted')]+close()
 s['expect']['files']={'home/tool-input':{'text':'pre teh post\nout teh end\n'}if available else None};cases.append(s)
for name,arg in [('SPACE','  --one  --two '),('TAB','--one\t--two')]:
 s=spellcase('TEST-NEXT-TOOL-002-'+name);s['args']=['-I','-s','altspell '+arg,'f.txt'];cases.append(s)
(OUT/'tools.json').write_text(json.dumps(cases,indent=1)+'\n')
print(len(cases),'tool scenarios')
# Compound edits/configuration and true syscall faults, separate from old goldens.
extra=[]
for n,(text,rc)in enumerate([('aaa bbb ccc ddd eee','set fill 15\nunset nowrap\n'),('aa  bb\tcc dddd','set fill 8\nunset nowrap\nset autoindent\n'),('unbreakablelongword xyz','set fill 8\nunset nowrap\n')],1):
 s=base(f'TEST-NEXT-EDIT-001-{n}',b'\n',args=['f.txt']);s['files']['home/.nanorc']={'text':rc};s['steps']+=[{'text':text},snap('wrapped'),{'keys':['M-U']},snap('undo'),{'keys':['M-E']},snap('redo')]+close();extra.append(s)
s=base('TEST-NEXT-EDIT-002',b'\n',args=['-I','-b','-r','12','f.txt']);s['steps']+=[{'text':'one two three four'},snap('wrap'),{'keys':['^S']},{'wait':{'text':'Wrote'}},{'text':' X'},{'keys':['M-U']},snap('saved-point'),{'keys':['M-U']},snap('original'),{'keys':['M-E']},snap('redo')]+close();extra.append(s)
s=base('TEST-NEXT-EDIT-003',b'aaa bbb ccc ddd\n',args=['-I','-b','-r','10','f.txt']);s['steps']+=selection(0,7)+[{'keys':['^K','^U']},snap('paste'),{'keys':['M-U']},snap('undo'),{'keys':['M-E']},snap('redo')]+close();extra.append(s)
for n,rc in enumerate(['set tabsize 3\nunset nowrap\nset fill 10\n','include "~/nested/*.nanorc"\n','syntax unused "\\.unused$"\ncolor INVALID "a"\nsyntax used "\\.txt$"\ncolor red "teh"\nextendsyntax used color blue "pre"\n'],1):
 s=base(f'TEST-NEXT-RC-00{1 if n<3 else 2}-{n}',args=['-T','5','f.txt']);s['files']['home/.nanorc']={'text':rc};s['files']['home/nested/a.nanorc']={'text':'syntax other "\\.other$"\ncolor green "a"\ninclude "child.nanorc"\n'};s['steps']+=[snap('configured'),{'text':'\tX'},snap('typed')]+close();extra.append(s)
FAULT=(ROOT/'tests/follow-up/stubs/faultwrap.c').read_text()
for mode in ['enospc','short','eintr']:
 s=base('TEST-NEXT-IO-001-'+mode.upper(),b'original\n',args=['-I','f.txt']);s['files']['bin/faultwrap.c']={'text':FAULT};s['build_helpers']=[{'source':'bin/faultwrap.c','output':'bin/faultwrap','shared':False}];s['fault_supervisor']='bin/faultwrap';s['env']={'NARO_FIXTURE_ROOT':'$FX','NARO_FAULT_TARGET':'$FX/work/f.txt','NARO_FAULT_MODE':mode,'NARO_FAULT_AFTER':'4'}
 s['steps']+=[{'text':'X'},{'keys':['^S']},{'settle':150},snap('outcome'),*([{'wait':{'text':'Maybe ^T^Z','timeout':12}},snap('warning')]if mode=='enospc'else[]),{'keys':['^X']},{'sleep':100},{'text':'n'},{'wait_exit':5}];extra.append(s)
s=copy.deepcopy(extra[-3]);s['id']='TEST-NEXT-IO-002-LINK-BACKUP';s['args']=['-I','-B','f.txt'];s['hardlinks']={'work/hard':'work/f.txt'};s['symlinks']={'work/link':'f.txt'};extra.append(s)
s=base('TEST-NEXT-IO-003',b'',args=['-I']);s['fifos']=['work/pipe'];s['files']['bin/reader']={'text':'#!/usr/bin/python3\nimport os\nwith open("pipe","rb")as f:data=f.read()\nopen(os.environ["HOME"]+"/received","wb").write(data)\n','mode':'0755'};s['helpers']=[['bin/reader']];s['steps']+=[{'text':'fifo bytes'},{'keys':['^O']},{'text':'pipe\r'},{'wait':{'text':'OVERWRITE?'}},{'text':'y'},{'wait':{'text':'Wrote'}},snap('written'),{'keys':['^X']},{'wait_exit':5}];s['expect']['helper_statuses']=[0];s['expect']['files']={'home/received':{'text':'fifo bytes\n'}};extra.append(s)
(OUT/'edges.json').write_text(json.dumps(extra,indent=1)+'\n')
# Live child plus handled termination. Cleanup differences remain visible.
for signame in ['SIGTERM','SIGHUP']:
 s=base('TEST-NEXT-TOOL-003-'+signame,b'original\n');s['env']={'TOOL_MODE':'sleep'};s['steps']+=[{'text':'X'},{'keys':['^T','^T']},{'wait_file':{'path':'home/ready','contains':'ready'}},{'signal':signame},{'wait_exit':5}];s['expect']={'exit_status':1};s['candidate_expect']={'exit_status':1,'temp_empty':True};
 (OUT/('signal-'+signame+'.json')).write_text(json.dumps([s],indent=1)+'\n')
print(len(extra),'edge scenarios')

s=base('TEST-NEXT-IO-002-BACKUP-FAIL',b'original\n',args=['-I','-B','f.txt']);s['files']['work/f.txt~']={'text':'old backup\n'};s['files']['bin/faultwrap.c']={'text':(ROOT/'tests/follow-up/stubs/faultwrap.c').read_text()};s['build_helpers']=[{'source':'bin/faultwrap.c','output':'bin/faultwrap','shared':False}];s['fault_supervisor']='bin/faultwrap';s['env']={'NARO_FIXTURE_ROOT':'$FX','NARO_FAULT_TARGET':'$FX/work/f.txt~','NARO_FAULT_MODE':'backup-open'};s['steps']+=[{'text':'X'},{'keys':['^S']},{'wait':{'text':'Cannot make regular backup'}},snap('fallback'),{'wait':{'text':'Wrote','timeout':8}},snap('written'),{'keys':['^X']},{'wait_exit':5}]
(OUT/'backup.json').write_text(json.dumps([s],indent=1)+'\n')
# Recovery hooks exist only in the separate test build; no native memory faults.
panics=[]
for name,args,data in [('NAMED',['-I','-G','f.txt'],b'original\n'),('NAMELESS',['-I'],None),('MULTI',['-I','-G','f.txt','g.txt'],b'original\n')]:
 s={'id':'TEST-NEXT-RECOVER-002-'+name,'args':args,'dirs':['work/hook'],'files':{},'env':{'NARO_TEST_PANIC_DIR':'$FX/work/hook'},'steps':[{'settle':200},{'text':'X'}],'expect':{'exit_status':1,'stderr_contains':'Sorry! Nano crashed!  Code: 6.','trace_final_modes':{'cursor_visible':True,'alternate_screen':False,'bracketed_paste':False}}}
 if data is not None:s['files']['work/f.txt']={'hex':data.hex()};s['expect']['files']={'work/f.txt.save':{'text':'Xoriginal\n','mode':'0o600'},'work/.f.txt.swp':None}
 if name=='MULTI':
  s['files']['work/g.txt']={'text':'other\n'};s['steps']+=[{'keys':['M-.']},{'text':'Y'},{'wait':{'text':'Yother'}}];s['expect']['files']['work/g.txt.save']={'text':'Yother\n','mode':'0o600'};s['expect']['files']['work/.g.txt.swp']=None
 s['steps']+=[{'wait_file':{'path':'work/hook/ready','contains':'modified'}},{'write_file':'work/hook/trigger','content':'panic'},{'wait_exit':5}];panics.append(s)
(OUT/'panic.json').write_text(json.dumps(panics,indent=1)+'\n')
# A bounded FIFO writer is terminated after supplying data, producing EOF.
s=base('TEST-NEXT-IO-003-EOF',args=['-I','pipe']);s['files'].pop('work/f.txt');s['fifos']=['work/pipe'];s['files']['bin/writer']={'text':'#!/usr/bin/python3\nimport os,signal\nwith open("pipe","wb")as f:f.write(b"pipe line\\n")\nos.kill(os.getpid(),signal.SIGTERM)\n','mode':'0755'};s['helpers']=[['bin/writer']];s['steps']=[{'wait':{'text':'Read 1 line'}},snap('read'),{'keys':['^X']},{'wait_exit':5}];s['expect']['helper_statuses']=[-15]
(OUT/'fifo-eof.json').write_text(json.dumps([s],indent=1)+'\n')
