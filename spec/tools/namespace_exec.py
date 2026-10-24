#!/usr/bin/env python3
"""Fixture-only bubblewrap backend. Reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c."""
import json,os,pwd,signal,stat,subprocess,sys
from pathlib import Path


def validate_fixture(root, workroot, uid):
    root=Path(root).absolute();base=Path(workroot).absolute()
    if root.resolve()!=root or base.resolve()!=base or root.name!='fx' or root.parent.parent!=base or not root.parent.name.startswith('TEST-'):
        raise ValueError('namespace requires a canonical harness fixture')
    if uid not in (0,1000):raise ValueError('supported namespace uids are 0 and 1000')
    return root


def prepare(root,workroot,config):
    uid=config.get('uid',0);root=validate_fixture(root,workroot,uid);work=root.parent
    tree=work/'namespace-root';tree.mkdir()
    for name in ['usr','runtime','dev','proc','etc','tmp','alpha','omega']:(tree/name).mkdir()
    for name,target in [('bin','usr/bin'),('sbin','usr/sbin'),('lib','usr/lib'),('lib64','usr/lib64' if Path('/usr/lib64').exists()else'usr/lib')]:
        (tree/name).symlink_to(target)
    for name in ['runtime/editor','runtime/launcher','etc/passwd','etc/group','etc/nsswitch.conf']:(tree/name).touch()
    for path in [root,work/'tmp']:(tree/str(path).lstrip('/')).mkdir(parents=True,exist_ok=True)
    nss=root/'namespace-nss';nss.mkdir()
    entries=config.get('passwd_entries',[{'name':'fixture-root','uid':uid,'home':'account'}])
    lines=[]
    for entry in entries:
        name=entry['name'];home=entry['home'];entry_uid=entry['uid']
        if entry_uid not in (0,1000)or not name or any(c in name+home for c in ':\n\x00')or (home and (home.startswith('/')or '..'in Path(home).parts)):
            raise ValueError('unsafe fixture passwd entry')
        value=str(root/home)if home else''
        lines.append(f'{name}:x:{entry_uid}:{entry_uid}:Fixture:{value}:/bin/sh\n')
    (nss/'passwd').write_text(''.join(lines));(nss/'group').write_text(f'fixture:x:{uid}:\n');(nss/'nsswitch.conf').write_text('passwd: files\ngroup: files\nhosts: files\n')
    state={'fixture':str(root),'root':str(tree),'uid':uid,'backend':'bubblewrap user/mount/pid/ipc/uts/network namespaces'}
    path=work/'namespace.json';path.write_text(json.dumps(state))
    return path


# This code runs only after entering the new root. It asserts the actual uid and
# private device, records observations, then execs the editor with exact argv[0].
PROBE='''import os,pwd,stat,json,sys
uid=int(sys.argv[1]);root=sys.argv[2];exe=sys.argv[3];argv=json.loads(sys.argv[4])
assert os.geteuid()==uid and os.getuid()==uid
try:home=pwd.getpwuid(uid).pw_dir
except KeyError:home=None
s=os.stat('/dev/null');assert stat.S_ISCHR(s.st_mode)and os.major(s.st_rdev)==1 and os.minor(s.st_rdev)==3
probe={'euid':os.geteuid(),'uid':os.getuid(),'passwd_home':home,'HOME':os.environ.get('HOME'),'null_device':[1,3],'null_is_character_device':True,'cwd':os.getcwd(),'root':'/'}
with open(root+'/namespace-nss/probe.json','w')as f:json.dump(probe,f,sort_keys=True)
os.execv(exe,argv)
'''


def main():
    state_path,exe,binary,env_json,argv_json=sys.argv[1:];state=json.loads(Path(state_path).read_text());root=Path(state['fixture']);uid=state['uid']
    validate_fixture(root,root.parent.parent,uid)
    tree=Path(state['root'])
    if tree!=root.parent/'namespace-root' or tree.resolve()!=tree or not tree.is_dir():
        raise ValueError('unsafe namespace mount root')
    if not Path.cwd().is_relative_to(root):raise ValueError('namespace cwd must stay inside fixture')
    for name in ['passwd','group','nsswitch.conf']:
        path=root/'namespace-nss'/name
        if path.resolve()!=path or not path.is_file():raise ValueError('unsafe NSS fixture')
    env=json.loads(env_json)
    command=['/usr/bin/bwrap','--unshare-all','--uid',str(uid),'--gid',str(uid),'--die-with-parent','--new-session',
        '--ro-bind',state['root'],'/','--ro-bind','/usr','/usr','--proc','/proc','--dev','/dev',
        '--bind',str(root),str(root),'--bind',str(root.parent/'tmp'),str(root.parent/'tmp'),
        '--ro-bind',binary,'/runtime/editor']
    entry='/runtime/editor'
    if exe!=binary:
        command+=['--ro-bind',exe,'/runtime/launcher'];entry='/runtime/launcher';env['NARO_FAULT_BINARY']='/runtime/editor'
    for name in ['passwd','group','nsswitch.conf']:command+=['--ro-bind',str(root/'namespace-nss'/name),'/etc/'+name]
    command+=['--chdir',os.getcwd(),sys.executable,'-c',PROBE,str(uid),str(root),entry,argv_json]
    result=subprocess.run(command,env=env)
    if result.returncode<0:
        sig=-result.returncode;signal.signal(sig,signal.SIG_DFL);os.kill(os.getpid(),sig)
    return result.returncode

if __name__=='__main__':raise SystemExit(main())
