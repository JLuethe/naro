#!/usr/bin/env python3
"""Compare editors on guest /dev/tty1 using QEMU keyboard hardware events."""
import argparse,base64,hashlib,json,sys,time
from pathlib import Path
from console_vm import VM,rows
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'spec/tools'))
from identity_review import project_identity_rows, policy_identity
from release_gate_evidence import classification_counts, same_json

def norm(snapshot):
    return {'cols':snapshot['cols'],'rows':snapshot['rows'],'cursor':snapshot['cursor'],
            'chars':snapshot['chars'],'attrs':[a if i < snapshot['cols'] or c not in (0,32) else None for i,(c,a) in enumerate(zip(snapshot['chars'],snapshot['attrs']))], 'info':snapshot.get('info')}

def console_cases():
 data='one two three\nfour five six\n\nseven eight\nlast\n'
 return [
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


def console_case_sha256(case):
    return hashlib.sha256(json.dumps(case, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def expected_keyboard(case):
    keys = list(case['keys'])
    if 'signal' not in case:
        if case.get('save'):
            keys.append(('s', ('ctrl',)))
        keys.append((case.get('exit_key', 'x'), ('ctrl',)))
        if case.get('discard'):
            keys.append(('n', ()))
        keys.extend((case.get('exit_key', 'x'), ('ctrl',))
                    for _ in range(case.get('close_count', 1) - 1))
    return [{'key': key, 'mods': list(mods),
             'kernel_modifier_bits': sum({'shift': 1, 'ctrl': 4, 'alt': 8}[m] for m in mods)}
            for key, mods in keys]


def compare_console_case(case, reference, candidate):
    """Recompute identity acceptance from complete guest captures, without masks."""
    differences, identity_fields, unexpected = [], [], []
    tid = case['id']
    names = {'start', *(str(i) for i in range(len(case['keys'])))}
    if set(reference['frames']) != names or set(candidate['frames']) != names:
        unexpected.append({'field': 'frame_inventory'})
    for name in sorted(names):
        if name not in reference['frames'] or name not in candidate['frames']:
            continue
        r, c = reference['frames'][name], candidate['frames'][name]
        for side, snap in [('reference', r), ('candidate', c)]:
            if (len(snap['chars']) != snap['cols'] * snap['rows']
                    or len(snap['attrs']) != snap['cols'] * snap['rows']):
                unexpected.append({'frame': name, 'field': side + '.grid_dimensions'})
        left, right = norm(r), norm(c)
        for field in left:
            if left[field] != right[field]:
                differences.append({'frame': name, 'field': field})
                if field != 'chars':
                    unexpected.append({'frame': name, 'field': field})
        # The expected grid is derived solely from the reference and the
        # independent identity oracle. No candidate character enters it.
        try:
            expected, evidence = project_identity_rows(rows(r), r['cols'], allow_help=tid == 'TEST-VT-VM-HELP' and name in ('0', '1'), status_rows=(r['rows'] - 3,))
        except ValueError as error:
            expected, evidence = rows(r), []
            unexpected.append({'frame': name, 'field': 'identity_oracle', 'detail': str(error)})
        if rows(r)[0].startswith('  GNU nano 9.3') and not any(e.get('kind') == 'editing-title' for e in evidence):
            unexpected.append({'frame': name, 'field': 'unreviewed_reference_title'})
        expected_chars = [ord(ch) for row in expected for ch in row.ljust(r['cols'])]
        if len(expected_chars) != len(r['chars']):
            unexpected.append({'frame': name, 'field': 'identity_oracle_dimensions'})
        elif c['chars'] != expected_chars:
            unexpected.append({'frame': name, 'field': 'chars'})
        elif expected_chars != r['chars']:
            identity_fields.append({'frame': name, 'field': 'chars', 'evidence': evidence})
    if reference['exited']['exit'] != candidate['exited']['exit']:
        differences.append({'field': 'exit'})
        unexpected.append({'field': 'exit'})
    for side, value in [('reference', reference), ('candidate', candidate)]:
        exited, started = value['exited'], value['started']
        if value.get('case_sha256') != console_case_sha256(case):
            unexpected.append({'field': side + '.case_sha256'})
        if exited['exit'] != (1 if 'signal' in case else 0):
            unexpected.append({'field': side + '.expected_exit'})
        if value.get('keyboard') != expected_keyboard(case):
            unexpected.append({'field': side + '.keyboard'})
        before, after = started['before_console'], exited['after']
        if (exited.get('termios_restored') is not True
                or started['before'] != after.get('termios')):
            unexpected.append({'field': side + '.termios_restored'})
        if (exited.get('console_modes_restored') is not True
                or any(before.get(k) != after.get(k)
                       for k in ['keyboard_mode', 'meta_mode'])):
            unexpected.append({'field': side + '.console_modes_restored'})
        probe = json.loads(base64.b64decode(exited['files']['probe.json']['b64'], validate=True))
        if (probe['uid'] != 1000 or probe['euid'] != 1000
                or probe['isatty'] != [True, True] or probe['vt_state'][0] != 1
                or before.get('device') != '/dev/tty1' or after.get('device') != '/dev/tty1'):
            unexpected.append({'field': side + '.real_vt_identity'})
        if tid in ('TEST-VT-VM-MACRO', 'TEST-VT-VM-MACRO-CTRL'):
            if ('Recording a macro' not in rows(value['frames']['1'])[-3]
                    or value['frames']['6']['cursor'] != ([4, 1] if tid == 'TEST-VT-VM-MACRO' else [13, 1])):
                unexpected.append({'field': side + '.macro_assertion'})
        if tid == 'TEST-VT-VM-CTRL' and value['frames']['3']['cursor'] != [0, 6]:
            unexpected.append({'field': side + '.ctrl_end_assertion'})
        if tid == 'TEST-VT-VM-UNICODE' and not rows(value['frames']['start'])[1].startswith('cafe xx'):
            unexpected.append({'field': side + '.unicode_assertion'})
    appfiles = lambda value: {k: v for k, v in value['exited']['files'].items() if k != 'probe.json'}
    if appfiles(reference) != appfiles(candidate):
        differences.append({'field': 'files'})
        unexpected.append({'field': 'files'})
    return {'match': not differences, 'raw_exact': not differences,
            'identity_reviewed': bool(identity_fields) and not unexpected,
            'declared_deviation': False, 'deviation_id': None,
            'accepted': not unexpected, 'differences': differences,
            'identity_fields': identity_fields, 'unexpected_differences': unexpected,
            'reference_sha256': reference['started']['binary_sha256'],
            'candidate_sha256': candidate['started']['binary_sha256']}


def validate_console_evidence(folder, candidate_sha256, reference_sha256):
    """Reopen all 19 captures and independently verify guest provenance."""
    folder = Path(folder)
    report = json.loads((folder / 'report.json').read_text())
    provenance = json.loads((folder / 'vm-provenance.json').read_text())
    problems, results = [], {}
    cases = console_cases()
    if (report.get('schema') != 'naro-console/v2'
            or report.get('reference_commit') != '6ed285c3ec7a1d228def4d4e7021c6ba269f620c'
            or report.get('identity_policy') != policy_identity()):
        problems.append('console schema/policy mismatch')
    if set(report.get('results', {})) != {case['id'] for case in cases} or len(cases) != 19:
        problems.append('console inventory must contain exactly the 19 required cases')
    expected_files = {case['id'] + '-' + side + '.json' for case in cases for side in ['reference', 'candidate']}
    actual_files = {p.name for suffix in ['-reference.json', '-candidate.json'] for p in folder.glob('TEST-*' + suffix)}
    if actual_files != expected_files:
        problems.append('raw console recording membership mismatch')
    guest = report['guest']
    if (guest['info'].get('device') != '/dev/tty1' or guest['info']['vt_state'][0] != 1
            or not guest.get('keymap') or not guest.get('keyboard_devices')
            or not guest['info'].get('kernel') or not guest.get('kernel_command_line')):
        problems.append('guest device/kernel/keymap provenance incomplete')
    controller_hash = hashlib.sha256((ROOT / 'tests/console/guest.py').read_bytes()).hexdigest()
    if guest.get('controller_sha256') != controller_hash:
        problems.append('guest controller differs from reviewed source')
    tables = {str(n) for n in [0, 1, 4, 5, 8, 9, 12, 13]}
    keys = {str(n) for n in [14, 15, 26, 27, 39, 58, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111]}
    keymap = guest.get('keymap', {})
    if (set(keymap) != tables or any(set(mapping) != keys or any(type(v) is not int for v in mapping.values())
                                   for mapping in keymap.values())):
        problems.append('guest keymap inventory incomplete')
    for key in ['kernel_sha256', 'initrd_sha256', 'runtime_export_sha256']:
        digest = provenance.get(key)
        if not isinstance(digest, str) or len(digest) != 64 or any(ch not in '0123456789abcdef' for ch in digest):
            problems.append('invalid provenance ' + key)
    if (provenance.get('tested_candidate_sha256') != candidate_sha256
            or provenance.get('guest_reference_sha256') != reference_sha256
            or provenance.get('checker_exit') != 0):
        problems.append('console executable provenance mismatch')
    inputs = provenance.get('inputs', {})
    if (inputs.get('vmlinuz') != provenance.get('kernel_sha256')
            or inputs.get('initrd.cpio.gz') != provenance.get('initrd_sha256')
            or [inputs[k] for k in ('reference', 'nano') if k in inputs] != [reference_sha256]):
        problems.append('guest boot/reference input hashes mismatch')
    upload = provenance.get('candidate_upload')
    if upload is None:
        if [inputs[k] for k in ('naro', 'naro-host', 'naro-ubuntu') if k in inputs] != [candidate_sha256]:
            problems.append('guest installed candidate differs from prepared image')
    elif upload.get('sha256') != candidate_sha256 or not isinstance(upload.get('size'), int) or upload['size'] <= 0:
        problems.append('guest upload hash/size mismatch')
    for case in cases:
        tid = case['id']
        pair = [json.loads((folder / f'{tid}-{side}.json').read_text())
                for side in ['reference', 'candidate']]
        for side, run, digest in zip(['reference', 'candidate'], pair, [reference_sha256, candidate_sha256]):
            if run['started']['binary_sha256'] != digest:
                problems.append(tid + ': ' + side + ' installed executable mismatch')
            for snap in run['frames'].values():
                if snap.get('info', {}).get('kernel') != guest['info']['kernel']:
                    problems.append(tid + ': frame kernel differs from guest provenance')
        result = compare_console_case(case, *pair)
        results[tid] = result
        if not same_json(report.get('results', {}).get(tid), result):
            problems.append(tid + ': stored classification differs from reopened captures')
        if not result['accepted']:
            problems.append(tid + ': unexpected console differences/assertion failure')
    summary = classification_counts(results.values())
    if not same_json(report.get('summary'), summary):
        problems.append('console summary differs from recomputed counts')
    return report, summary, problems


def main():
 p=argparse.ArgumentParser();p.add_argument('--fixture',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--ids',nargs='*');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
 cases=console_cases()
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
   exited=v.finish();collected[kind]={'case_sha256':console_case_sha256(c),'started':started,'frames':frames,'keyboard':v.keys,'exited':exited}
   (a.out/(tid+'-'+kind+'.json')).write_text(json.dumps(collected[kind],indent=1)+'\n')
  result=compare_console_case(c,collected['reference'],collected['candidate'])
  report['results'][tid]=result;print(tid,'ACCEPTED'if result['accepted']else result['unexpected_differences'],flush=True)
 report.update(schema='naro-console/v2',identity_policy=policy_identity(),summary=classification_counts(report['results'].values()))
 (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');v.close();raise SystemExit(int(any(not x['accepted']for x in report['results'].values())))
if __name__=='__main__':main()
