#!/usr/bin/env python3
"""Boot only a disposable fixture VM; no host disks, network or console are attached."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--fixture',type=Path,required=True);p.add_argument('--timeout',type=int,default=900);a=p.parse_args();fx=a.fixture.absolute()
base=Path(os.environ.get('NANOSPEC_WORK','/tmp/nanospec-work')).absolute()
if fx.resolve()!=fx or fx.parent.parent!=base or fx.name!='fx'or not fx.parent.name.startswith('TEST-'):raise SystemExit('private harness fixture required')
if not (fx/'init-root/.naro-vm-fixture').is_file():raise SystemExit('missing fixture image marker')
if a.timeout<10 or a.timeout>3600:raise SystemExit('timeout must be 10..3600 seconds')
for name in ['qmp.sock','control.sock']:
 if (fx/name).exists():raise SystemExit('VM socket exists; stop its owner before reusing the fixture')
args=['/usr/bin/qemu-system-x86_64','-enable-kvm','-cpu','host','-smp','2','-m','1536','-kernel',str(fx/'vmlinuz'),'-initrd',str(fx/'initrd.cpio.gz'),'-append','console=tty0 console=ttyS0,115200 rdinit=/init nomodeset vt.default_utf8=1 panic=-1 quiet','-display','none','-vga','std','-nic','none','-serial','file:'+str(fx/'serial-final.log'),'-qmp','unix:'+str(fx/'qmp.sock')+',server=on,wait=off','-chardev','socket,id=control,path='+str(fx/'control.sock')+',server=on,wait=off','-device','virtio-serial-pci','-device','virtserialport,chardev=control,name=org.naro.control','-no-reboot']
report={'command':args,'qemu':subprocess.check_output([args[0],'--version'],text=True).strip(),'kernel_sha256':hashlib.sha256((fx/'vmlinuz').read_bytes()).hexdigest(),'initrd_sha256':hashlib.sha256((fx/'initrd.cpio.gz').read_bytes()).hexdigest()}
with (fx/'qemu-final.log').open('w')as log:
 child=subprocess.Popen(args,stdout=log,stderr=log);report['host_pid']=child.pid;(fx/'vm-run.json').write_text(json.dumps(report,indent=2)+'\n')
 try:code=child.wait(timeout=a.timeout)
 except subprocess.TimeoutExpired:
  child.terminate()
  try:child.wait(timeout=3)
  except subprocess.TimeoutExpired:child.kill();child.wait()
  raise SystemExit('fixture VM exceeded its bounded lifetime')
raise SystemExit(code)
