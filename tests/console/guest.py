#!/usr/bin/python3
"""Disposable VM controller: app fds use a genuine guest VT, never a PTY."""
import base64,ctypes,fcntl,hashlib,json,os,pwd,signal,stat,struct,subprocess,sys,termios,time
from pathlib import Path
if os.getpid()!=1 or not Path("/.naro-vm-fixture").is_file():raise SystemExit("guest controller requires the disposable VM root")
from upload import Upload
upload=Upload('/opt/naro')
libc=ctypes.CDLL(None,use_errno=True)
for name in ['proc','sys','dev']:
 kind={'proc':'proc','sys':'sysfs','dev':'devtmpfs'}[name];Path('/'+name).mkdir(exist_ok=True)
 if libc.mount(kind.encode(),('/'+name).encode(),kind.encode(),0,None)!=0:print('mount',name,ctypes.get_errno(),flush=True)
print('NARO_VM_BOOT '+os.uname().release,flush=True)
for n in range(200):
 if Path('/dev/vport0p1').exists():break
 time.sleep(.05)
channel=open('/dev/vport0p1','r+b',buffering=0)
pid=None;current=None;tty=os.open('/dev/tty1',os.O_RDWR|os.O_NOCTTY);original=termios.tcgetattr(tty)

def attrs():
 global tty
 try:value=termios.tcgetattr(tty)
 except termios.error:
  os.close(tty);tty=os.open("/dev/tty1",os.O_RDWR|os.O_NOCTTY);value=termios.tcgetattr(tty)
 value[-1]=[x.hex()if isinstance(x,bytes)else x for x in value[-1]];return value

def info():
 terminal=attrs()
 data=bytearray(6);fcntl.ioctl(tty,0x5603,data,True);mods=bytearray([6]);fcntl.ioctl(tty,0x541c,mods,True)
 options={}
 for name,request in [('keyboard_mode',0x4b44),('meta_mode',0x4b62)]:
  value=bytearray(4);fcntl.ioctl(tty,request,value,True);options[name]=struct.unpack('i',value)[0]
 return {**options,'vt_state':list(struct.unpack('HHH',data)),'shift_state':mods[0],'termios':terminal,'kernel':os.uname().release,'device':os.ttyname(tty)}

def poll():
 global pid
 if pid is None:return None
 found,status=os.waitpid(pid,os.WNOHANG)
 if not found:return None
 pid=None
 return {'exit':os.waitstatus_to_exitcode(status),'termios_restored':attrs()==current['before'],'console_modes_restored':all(info()[k]==current['before_console'][k]for k in ['keyboard_mode','meta_mode']),'after':info(),'files':files()}

def files():
 out={}
 if current:
  for p in sorted(current['fx'].rglob('*')):
   if p.is_file():
    raw=p.read_bytes();out[str(p.relative_to(current['fx']))]={'b64':base64.b64encode(raw).decode(),'mode':oct(stat.S_IMODE(p.stat().st_mode))}
 return out

def snapshot():
 data=Path('/dev/vcsa1').read_bytes();rows,cols,x,y=data[:4];cells=data[4:];unicode=Path('/dev/vcsu1').read_bytes()
 chars=list(struct.unpack('<'+'I'*(len(unicode)//4),unicode))
 return {'cols':cols,'rows':rows,'cursor':[x,y],'chars':chars,'attrs':list(cells[1::2]),'info':info()}

def dispatch(cmd):
 global pid,current,original
 op=cmd['op']
 if op=='ping':return {'ready':True,'info':info()}
 if op=='metadata':
  mapping={}
  for table in [0,1,4,5,8,9,12,13]:
   mapping[str(table)]={}
   for index in [14,15,26,27,39,58,102,103,104,105,106,107,108,109,110,111]:
    entry=bytearray(struct.pack('BBH',table,index,0));fcntl.ioctl(tty,0x4b46,entry,True);mapping[str(table)][str(index)]=struct.unpack('BBH',entry)[2]
  return {'keyboard_devices':Path('/proc/bus/input/devices').read_text(),'kernel_command_line':Path('/proc/cmdline').read_text(),'keymap':mapping,'info':info(),'controller_sha256':hashlib.sha256(Path('/init').read_bytes()).hexdigest()}

 if op=='snapshot':return snapshot()
 if op=='poll':
  result=poll()
  if result:current['exit_result']=result
  return current.get('exit_result')if current else None
 if op.startswith('upload-'):
  if pid is not None:raise ValueError('editor running')
  if op=='upload-start':return upload.begin(cmd['name'],cmd['size'],cmd['sha256'])
  if op=='upload-chunk':return upload.chunk(cmd['offset'],cmd['b64'])
  if op=='upload-finish':return upload.finish()
  if op=='upload-abort':upload.abort();return True
  raise ValueError('unknown upload operation')
 if op=='start':
  if pid is not None:raise ValueError('editor running')
  if upload.pending is not None:raise ValueError('upload pending')
  if cmd['binary']not in ['reference','candidate']:raise ValueError('binary name')
  tid=cmd['id']
  if not tid.startswith('TEST-')or any(x in tid for x in ['/','..']):raise ValueError('test id')
  import shutil
  fx=Path('/fixtures')/tid
  if fx.exists():shutil.rmtree(fx)
  for name in ['home','work','tmp']:(fx/name).mkdir(parents=True)
  for name,content in cmd['files'].items():
   p=fx/'work'/name
   if p.is_absolute()and not p.is_relative_to(fx/'work')or '..'in Path(name).parts:raise ValueError('unsafe fixture path')
   p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(content))
  for p in [fx,*fx.rglob('*')]:os.chown(p,1000,1000)
  termios.tcsetattr(tty,termios.TCSANOW,original);os.write(tty,b'\x1bc');time.sleep(.05)
  before=attrs();before_console=info();binary=Path('/opt/naro')/cmd['binary'];current={'fx':fx,'before':before,'before_console':before_console,'binary':str(binary),'sha256':hashlib.sha256(binary.read_bytes()).hexdigest()}
  pid=os.fork()
  if pid==0:
   os.setsid();fd=os.open('/dev/tty1',os.O_RDWR);fcntl.ioctl(fd,termios.TIOCSCTTY,0)
   os.tcsetpgrp(fd,os.getpid())
   for target in [0,1]:os.dup2(fd,target)
   error=os.open(str(fx/'stderr'),os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600);os.dup2(error,2)
   os.setgid(1000);os.setuid(1000);os.chdir(fx/'work')
   probe={'uid':os.getuid(),'euid':os.geteuid(),'isatty':[os.isatty(i)for i in [0,1]],'vt_getstate':True}
   state=bytearray(6);fcntl.ioctl(1,0x5603,state,True);probe['vt_state']=list(struct.unpack('HHH',state));(fx/'probe.json').write_text(json.dumps(probe))
   os.execve(binary,['nano']+cmd.get('args',['-I','sample.txt']),{'HOME':str(fx/'home'),'TMPDIR':str(fx/'tmp'),'TERM':'linux','LANG':'C.UTF-8','PATH':'/usr/bin:/bin','SHELL':'/bin/sh'})
  return {'pid':pid,'binary_sha256':current['sha256'],'before':before,'before_console':before_console}
 if op=='signal':
  if pid is None:raise ValueError('editor not running')
  os.kill(pid,int(cmd['signal']));return True
 if op=='shutdown':libc.reboot(0x4321fedc);return True
 raise ValueError('unknown op')

buffer=bytearray()
while True:
 try:
  chunk=channel.read(65536)
  if not chunk:buffer.clear();upload.abort();time.sleep(.01);continue
  buffer.extend(chunk)
  if len(buffer)>256*1024:buffer.clear();upload.abort();raise OSError('request too large')
  while b'\n'in buffer:
   line,buffer=buffer.split(b'\n',1)
   try:response={'ok':True,'result':dispatch(json.loads(line))}
   except Exception as error:response={'ok':False,'error':repr(error)}
   data=memoryview(json.dumps(response).encode()+b'\n')
   while data:
    written=channel.write(data);data=data[written:]
 except OSError:buffer.clear();upload.abort();time.sleep(.1)
