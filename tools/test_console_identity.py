#!/usr/bin/env python3
"""Negative controls for reference-derived guest-console identity."""
import base64, copy, hashlib, json, tempfile, unittest
from pathlib import Path
from check_console_vm import compare_console_case, console_case_sha256, console_cases, expected_keyboard, validate_console_evidence
from candidate_expectations import title_row
from identity_review import policy_identity, project_identity_rows
from release_gate_evidence import classification_counts

class ConsoleIdentityTests(unittest.TestCase):
    def pair(self, case=None):
        case=case or console_cases()[0]
        info={'keyboard_mode':3,'meta_mode':4,'vt_state':[1,0,3],'termios':[1,2,3],'kernel':'test-kernel','device':'/dev/tty1'}
        text=[title_row(80,'sample.txt',label='GNU nano 9.3').ljust(80)]+[' '*80]*23
        text[1]='cafe xx'.ljust(80)
        snap={'cols':80,'rows':24,'cursor':[0,1],'chars':[ord(c) for row in text for c in row],'attrs':[112]*80+[7]*(80*23),'info':info}
        frames={name:copy.deepcopy(snap) for name in ['start',*(str(i)for i in range(len(case['keys'])))]}
        if case['id']=='TEST-VT-VM-CTRL':frames['3']['cursor']=[0,6]
        if case['id']in('TEST-VT-VM-MACRO','TEST-VT-VM-MACRO-CTRL'):
            frames['1']['chars'][21*80:22*80]=list(map(ord,'Recording a macro'.ljust(80)))
            frames['6']['cursor']=[4,1]if case['id']=='TEST-VT-VM-MACRO'else[13,1]
        probe={'uid':1000,'euid':1000,'isatty':[True,True],'vt_state':[1,0,3]}
        ref={'case_sha256':console_case_sha256(case),'started':{'binary_sha256':'a'*64,'before':[1,2,3],'before_console':info},'frames':frames,'keyboard':expected_keyboard(case),'exited':{'exit':1 if 'signal'in case else 0,'termios_restored':True,'console_modes_restored':True,'after':info,'files':{'probe.json':{'b64':base64.b64encode(json.dumps(probe).encode()).decode()},'work/sample.txt':{'b64':'b2sK','mode':'0o644'}}}}
        cand=copy.deepcopy(ref);cand['started']['binary_sha256']='b'*64
        for frame in cand['frames'].values():
            rows=[''.join(map(chr,frame['chars'][i:i+80]))for i in range(0,len(frame['chars']),80)]
            expected,_=project_identity_rows(rows,80)
            frame['chars']=[ord(c)for row in expected for c in row]
        return case,ref,cand

    def test_projection_keeps_raw_differences(self):
        case,ref,cand=self.pair();r=compare_console_case(case,ref,cand)
        self.assertTrue(r['accepted']);self.assertTrue(r['identity_reviewed']);self.assertFalse(r['raw_exact'])
        self.assertEqual({x['field']for x in r['differences']},{'chars'})

    def test_negative_controls(self):
        case,ref,cand=self.pair()
        def title(run,name='wrong.txt',state=''):
            run['frames']['start']['chars'][:80]=list(map(ord,title_row(80,name,state).ljust(80)))
        mutations={
            'filename':lambda r:title(r),
            'state':lambda r:title(r,'sample.txt','Modified'),
            'blank-title-attribute':lambda r:r['frames']['start']['attrs'].__setitem__(0,7),
            'cursor':lambda r:r['frames']['start'].__setitem__('cursor',[1,1]),
            'body':lambda r:r['frames']['start']['chars'].__setitem__(80,ord('X')),
            'bytes':lambda r:r['exited']['files']['work/sample.txt'].__setitem__('b64','bm8K'),
            'exit':lambda r:r['exited'].__setitem__('exit',3),
            'keyboard':lambda r:r['keyboard'].pop(),
            'forged-restoration':lambda r:r['exited']['after'].__setitem__('termios',[99]),
            'case-binding':lambda r:r.__setitem__('case_sha256','0'*64),
            'missing-frame':lambda r:r['frames'].pop('0')}
        for name,mutate in mutations.items():
            broken=copy.deepcopy(cand);mutate(broken)
            with self.subTest(name=name):self.assertFalse(compare_console_case(case,ref,broken)['accepted'])

    def test_old_brand_is_unexpected_even_if_raw_exact(self):
        case,ref,cand=self.pair();cand['frames']=copy.deepcopy(ref['frames'])
        r=compare_console_case(case,ref,cand)
        self.assertTrue(r['raw_exact']);self.assertFalse(r['accepted'])

    def test_unparseable_title_is_not_accepted_as_raw_exact(self):
        case,ref,cand=self.pair()
        bad=list(map(ord,'  GNU nano 9.3 bad-layout'.ljust(80)))
        ref['frames']['start']['chars'][:80]=bad
        cand['frames']['start']['chars'][:80]=bad
        self.assertFalse(compare_console_case(case,ref,cand)['accepted'])

    def evidence(self,folder):
        results={}
        for case in console_cases():
            _,ref,cand=self.pair(case)
            for side,run in [('reference',ref),('candidate',cand)]:
                (folder/(case['id']+'-'+side+'.json')).write_text(json.dumps(run))
            results[case['id']]=compare_console_case(case,ref,cand)
        report={'schema':'naro-console/v2','reference_commit':'6ed285c3ec7a1d228def4d4e7021c6ba269f620c','identity_policy':policy_identity(),'guest':{'info':{'device':'/dev/tty1','kernel':'test-kernel','vt_state':[1]},'controller_sha256':hashlib.sha256((Path(__file__).resolve().parents[1]/'tests/console/guest.py').read_bytes()).hexdigest(),'keymap':{str(t):{str(k):0 for k in [14,15,26,27,39,58,102,103,104,105,106,107,108,109,110,111]}for t in [0,1,4,5,8,9,12,13]},'keyboard_devices':'PS/2','kernel_command_line':'test'},'results':results,'summary':classification_counts(results.values())}
        provenance={'kernel_sha256':'c'*64,'initrd_sha256':'d'*64,'runtime_export_sha256':'e'*64,'tested_candidate_sha256':'b'*64,'guest_reference_sha256':'a'*64,'checker_exit':0,'candidate_upload':{'sha256':'b'*64,'size':123},'inputs':{'vmlinuz':'c'*64,'initrd.cpio.gz':'d'*64,'reference':'a'*64}}
        (folder/'report.json').write_text(json.dumps(report));(folder/'vm-provenance.json').write_text(json.dumps(provenance))

    def test_reopen_records_and_membership(self):
        with tempfile.TemporaryDirectory()as temp:
            folder=Path(temp);self.evidence(folder)
            self.assertEqual(validate_console_evidence(folder,'b'*64,'a'*64)[2],[])
            path=folder/'TEST-VT-VM-NAV-candidate.json';run=json.loads(path.read_text())
            run['frames']['start']['cursor']=[20,20];path.write_text(json.dumps(run))
            self.assertTrue(validate_console_evidence(folder,'b'*64,'a'*64)[2])
            self.evidence(folder);path=folder/'report.json';report=json.loads(path.read_text())
            report['results']['TEST-VT-VM-NAV']['accepted']=1;path.write_text(json.dumps(report))
            self.assertTrue(validate_console_evidence(folder,'b'*64,'a'*64)[2])
            self.evidence(folder);path=folder/'report.json';report=json.loads(path.read_text())
            report['results'].pop('TEST-VT-VM-NAV');path.write_text(json.dumps(report))
            self.assertTrue(validate_console_evidence(folder,'b'*64,'a'*64)[2])

    def test_stale_policy_and_upload_rejected(self):
        with tempfile.TemporaryDirectory()as temp:
            folder=Path(temp);self.evidence(folder)
            path=folder/'vm-provenance.json';p=json.loads(path.read_text())
            p['candidate_upload']['sha256']='f'*64;path.write_text(json.dumps(p))
            self.assertTrue(validate_console_evidence(folder,'b'*64,'a'*64)[2])
            self.evidence(folder);path=folder/'report.json';r=json.loads(path.read_text())
            r['identity_policy']['sha256']='0'*64;path.write_text(json.dumps(r))
            self.assertTrue(validate_console_evidence(folder,'b'*64,'a'*64)[2])

if __name__=='__main__':unittest.main()
