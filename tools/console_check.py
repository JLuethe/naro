#!/usr/bin/env python3
"""Read-only Linux VT readiness and explicit operator trial; reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c."""
import argparse,copy,fcntl,hashlib,json,os,platform,struct,subprocess,sys,termios,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'spec/tools'))
import nanoharness as h
CHECKS=['arrows-home-end-pages','backspace-delete-shift-tab','ctrl-arrows-home-end-delete','shift-selection-arrows-delete','alt-and-combined-modifiers','macro-and-rc-replay','combining-and-wide-display','save-exit-cancel','recoverable-tool-error','handled-termination-restoration']


def attrs(fd):
    try:
        value=termios.tcgetattr(fd);value[-1]=[x.hex()if isinstance(x,bytes)else x for x in value[-1]];return value
    except termios.error:return None


def probe():
    descriptors={}
    for fd in [0,1]:
        item={'isatty':os.isatty(fd),'tty':os.ttyname(fd)if os.isatty(fd)else None,'termios':attrs(fd)}
        data=bytearray(6)
        try:
            fcntl.ioctl(fd,0x5603,data,True) # VT_GETSTATE, read-only struct vt_stat
            item.update(vt_getstate=True,vt_state=list(struct.unpack('HHH',data)))
        except OSError as error:item.update(vt_getstate=False,errno=error.errno,error=error.strerror)
        descriptors[str(fd)]=item
    real=all(v['isatty']and v['vt_getstate']for v in descriptors.values())and descriptors['0']['tty']==descriptors['1']['tty']
    return {'kernel':platform.release(),'TERM':os.environ.get('TERM'),'locale':{k:os.environ.get(k)for k in ['LANG','LC_ALL','LC_CTYPE']},'descriptors':descriptors,'real_vt':real,'status':'available'if real else'deferred','reason':None if real else'The calling descriptors do not identify a real Linux VT; no console was opened or switched.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['probe','template','run']);p.add_argument('--out',type=Path,required=True);p.add_argument('--binary',type=Path);p.add_argument('--reference',type=Path);a=p.parse_args()
    if a.out.exists():raise SystemExit('preserve evidence: use a new output path')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    before=attrs(0);report={'reference_commit':h.REFERENCE_COMMIT,'probe':probe(),'checks':{key:{'status':'unobserved','reference':None,'candidate':None}for key in CHECKS},'status':'deferred'}
    if a.action=='run'and report['probe']['real_vt']:
        if os.geteuid()==0:raise SystemExit('run operator trials as an ordinary uid so private HOME is honored by GNU nano')
        if not a.binary or not a.reference:p.error('run requires --binary and --reference')
        report['operator']=input('Operator name: ').strip();report['keymap']=input('Console/keymap description (no keymap changes are made): ').strip();report['runs']={}
        for label,binary in [('reference',a.reference),('candidate',a.binary)]:
            fx=Path(h.WORKROOT)/('TEST-VT-OPERATOR-'+uuid.uuid4().hex[:10])/ 'fx';fx.mkdir(parents=True)
            h.make_fixture(str(fx),{'dirs':['home','tmp'],'files':{'work/sample.txt':{'text':'one two three\nfour five six\ncafe\u0301 \u754c\n'},'work/policy':{'text':''}}})
            binary=binary.resolve();digest=hashlib.sha256(binary.read_bytes()).hexdigest()
            print('\n'+label+': use only sample files inside '+str(fx/'work'))
            print('Perform the physical-key checklist, save changes, and exit. For handled-termination checks use a separate copied fixture and record the actual signal/observation.')
            print('\n'.join(CHECKS));saved=attrs(0)
            code=subprocess.run([str(binary),'--rcfile',str(fx/'work/policy'),'-o',str(fx/'work'),'sample.txt'],cwd=fx/'work',env={**os.environ,'HOME':str(fx/'home'),'TMPDIR':str(fx/'tmp')}).returncode
            report['runs'][label]={'fixture':str(fx),'binary_sha256':digest,'exit_status':code,'termios_restored':saved==attrs(0),'files':h.manifest(str(fx/'work'))}
            assert digest==hashlib.sha256(binary.read_bytes()).hexdigest(),'binary changed during trial'
            for key in CHECKS:report['checks'][key][label]=input(key+' — actual keys and observations (or not tested): ').strip()
        for key in CHECKS:
            value=input(key+' — match / difference / unsupported / not-tested: ').strip()
            report['checks'][key]['status']=value if value in ['match','difference','unsupported']else'not-tested'
        # Preserve observations for review. Manual unsupported entries require an
        # explicit reason and agreement with the source, never an automatic pass.
        report['status']='recorded'
    elif a.action=='run':report['reason']='Real-console gate unavailable; no editor launched.'
    report['probe_preserved_termios']=before==attrs(0)if a.action!='run'else None
    a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'real_vt':report['probe']['real_vt'],'report':str(a.out)}))
    return 77 if a.action!='template'and report['status']=='deferred'else 0

if __name__=='__main__':raise SystemExit(main())
