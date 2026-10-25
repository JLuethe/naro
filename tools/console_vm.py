#!/usr/bin/env python3
"""Host control for the disposable Linux VT guest and emulated PS/2 keyboard."""
import base64,json,os,socket,time
from pathlib import Path

class VM:
    def __init__(self,fixture):
        self.fixture=Path(fixture).absolute()
        if self.fixture.resolve()!=self.fixture or self.fixture.name!='fx'or not self.fixture.parent.name.startswith('TEST-')or self.fixture.parent.parent!=Path(os.environ.get('NANOSPEC_WORK','/tmp/nanospec-work')).absolute():raise ValueError('VM requires a private harness fixture')
        self.control=socket.socket(socket.AF_UNIX);self.control.settimeout(8);self.control.connect(str(self.fixture/'control.sock'));self.reader=self.control.makefile('rb')
        self.qmp=socket.socket(socket.AF_UNIX);self.qmp.settimeout(8);self.qmp.connect(str(self.fixture/'qmp.sock'));self.qreader=self.qmp.makefile('rb');json.loads(self.qreader.readline());self.command('qmp_capabilities')
        self.keys=[]
    def rpc(self,op,**args):
        self.control.sendall(json.dumps({'op':op,**args}).encode()+b'\n');data=json.loads(self.reader.readline())
        if not data['ok']:raise RuntimeError(data['error'])
        return data['result']
    def command(self,name,args=None):
        self.qmp.sendall(json.dumps({'execute':name,'arguments':args or{}}).encode()+b'\n')
        while True:
            result=json.loads(self.qreader.readline())
            if 'error'in result:raise RuntimeError(result['error'])
            if 'return'in result:return result['return']
    def event(self,key,down):
        return self.command('input-send-event',{'events':[{'type':'key','data':{'down':down,'key':{'type':'qcode','data':key}}}]})
    def press(self,key,mods=()):
        for mod in mods:self.event(mod,True)
        expected=sum({'shift':1,'ctrl':4,'alt':8}[mod]for mod in mods)
        deadline=time.monotonic()+1
        while True:
            state=self.rpc('ping')['info']['shift_state']
            if state==expected:break
            if time.monotonic()>deadline:raise RuntimeError('guest keyboard modifiers did not settle')
            time.sleep(.01)
        try:
            self.event(key,True);time.sleep(.06);self.event(key,False);time.sleep(.04)
        finally:
            for mod in reversed(mods):self.event(mod,False)
        time.sleep(.10);self.keys.append({'key':key,'mods':list(mods),'kernel_modifier_bits':state})
    def start(self,kind,tid,content='one two three\nfour five six\n',args=None,files=None):
        contents={'sample.txt':content.encode()}if files is None else files
        result=self.rpc('start',binary=kind,id=tid,args=args or['-I','sample.txt'],files={p:base64.b64encode(v).decode()for p,v in contents.items()});time.sleep(.3);return result
    def snapshot(self):return self.rpc('snapshot')
    def finish(self,timeout=4):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            result=self.rpc('poll')
            if result is not None:return result
            time.sleep(.03)
        raise TimeoutError('guest editor did not exit')
    def install(self,kind,binary):return self.rpc('install',name=kind,b64=base64.b64encode(Path(binary).read_bytes()).decode())
    def screenshot(self,path):
        path=Path(path).absolute()
        if not path.is_relative_to(self.fixture)or path.resolve()!=path:raise ValueError('screenshot must stay inside fixture')
        self.command('screendump',{'filename':str(path)})
    def close(self):self.reader.close();self.control.close();self.qreader.close();self.qmp.close()

def rows(snapshot):
    chars=snapshot['chars'];cols=snapshot['cols']
    return [''.join(chr(c)if 0<=c<=0x10ffff and not 0xd800<=c<=0xdfff else'�'for c in chars[n:n+cols])for n in range(0,len(chars),cols)]
