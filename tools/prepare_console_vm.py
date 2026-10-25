#!/usr/bin/env python3
"""Build an unprivileged initramfs from private Ubuntu runtime inputs."""
import argparse,gzip,hashlib,json,os,shutil,stat,struct,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--reuse',action='store_true');p.add_argument('--exported-root',type=Path,required=True);p.add_argument('--fixture',type=Path,required=True);p.add_argument('--kernel',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);a=p.parse_args()
compile((ROOT/'tests/console/guest.py').read_text(),'guest.py','exec')
fx=a.fixture.absolute()
if fx.resolve()!=fx or fx.name!='fx'or not fx.parent.name.startswith('TEST-'):raise SystemExit('private fixture required')
if fx.parent.parent!=Path(os.environ.get('NANOSPEC_WORK','/tmp/nanospec-work')).absolute():raise SystemExit('harness work root required')
root=fx/'init-root'
if a.reuse:
 shutil.copy2(ROOT/'tests/console/guest.py',root/'init')
else:
 root.mkdir(exist_ok=False)
if not a.reuse:
 for name in ['dev','proc','sys','run','tmp','etc','root','fixtures','opt/naro','usr/bin','usr/lib/x86_64-linux-gnu','usr/lib64']:(root/name).mkdir(parents=True,exist_ok=True)
 for name,target in [('bin','usr/bin'),('sbin','usr/bin'),('lib','usr/lib'),('lib64','usr/lib64')]: (root/name).symlink_to(target)
 def copy(source,target):
  target.parent.mkdir(parents=True,exist_ok=True)
  if source.is_dir():shutil.copytree(source,target,symlinks=True)
  elif source.is_symlink():target.symlink_to(os.readlink(source))
  else:shutil.copy2(source,target)
 for name in ['python3.12','dash'] :copy(a.exported_root/'usr/bin'/name,root/'usr/bin'/name)
 (root/'usr/bin/python3').symlink_to('python3.12');(root/'usr/bin/sh').symlink_to('dash')
 for file in (a.exported_root/'usr/lib/x86_64-linux-gnu').glob('*.so*'):copy(file,root/'usr/lib/x86_64-linux-gnu'/file.name)
 for file in (a.exported_root/'usr/lib64').iterdir():copy(file,root/'usr/lib64'/file.name)
 for name in ['usr/lib/python3.12','usr/share/terminfo','lib/terminfo','usr/lib/locale/C.utf8']:
  source=a.exported_root/name
  if source.exists():copy(source,root/name)
 (root/'etc/passwd').write_text('root:x:0:0:Root:/root:/bin/sh\nfixture:x:1000:1000:Fixture:/fixtures:/bin/sh\n');(root/'etc/group').write_text('root:x:0:\nfixture:x:1000:\n');(root/'etc/nsswitch.conf').write_text('passwd: files\ngroup: files\n')
 copy(a.reference,root/'opt/naro/reference');copy(a.binary,root/'opt/naro/candidate');copy(ROOT/'tests/console/guest.py',root/'init');(root/'init').chmod(0o755)
(root/'init').chmod(0o755)
(root/'.naro-vm-fixture').write_text('naro-console-fixture-v1\n')
archive=fx/'initrd.cpio.gz';ino=1
with gzip.open(archive,'wb',compresslevel=1)as stream:
 def entry(name,mode,data=b'',major=0,minor=0):
  global ino
  encoded=name.encode()+b'\0';fields=[ino,mode,0,0,1,0,len(data),0,0,major,minor,len(encoded),0];ino+=1
  header=b'070701'+b''.join(f'{v:08x}'.encode()for v in fields);stream.write(header+encoded);stream.write(b'\0'*((-(110+len(encoded)))%4));stream.write(data);stream.write(b'\0'*((-len(data))%4))
 for path in [root,*sorted(root.rglob('*'))]:
  name='.'if path==root else str(path.relative_to(root));s=path.lstat()
  if path.is_symlink():entry(name,s.st_mode,os.readlink(path).encode())
  elif path.is_file():entry(name,s.st_mode,path.read_bytes())
  elif path.is_dir():entry(name,s.st_mode)
 entry('dev/console',stat.S_IFCHR|0o600,major=5,minor=1);entry('dev/null',stat.S_IFCHR|0o666,major=1,minor=3);entry('TRAILER!!!',0)

if not a.reuse:copy(a.kernel,fx/'vmlinuz')
(fx/'inputs.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in [a.kernel,archive,a.reference,a.binary]},indent=2)+'\n');print(archive)
