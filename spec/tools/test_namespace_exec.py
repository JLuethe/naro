#!/usr/bin/env python3
"""Isolation guard regressions; reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c."""
import copy,errno,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import namespace_exec as ns
import nanoharness as h
SPEC=importlib.util.spec_from_file_location('console_check',Path(__file__).resolve().parents[2]/'tools/console_check.py')
console=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(console)
POLICY=importlib.util.spec_from_file_location("root_policy",Path(__file__).resolve().parents[2]/"tools/follow_up_policy.py")
policy=importlib.util.module_from_spec(POLICY);POLICY.loader.exec_module(policy)

class IsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):Path(h.WORKROOT).mkdir(parents=True,exist_ok=True)
    def test_rejects_host_and_symlink_roots_and_unknown_uids(self):
        base=Path(h.WORKROOT)
        with self.assertRaises(ValueError):ns.validate_fixture('/home',base,0)
        with tempfile.TemporaryDirectory(prefix='TEST-NS-',dir=base)as work:
            root=Path(work)/'fx';root.mkdir()
            self.assertEqual(ns.validate_fixture(root,base,0),root)
            with self.assertRaises(ValueError):ns.validate_fixture(root,base,1)
            alias=Path(work)/'alias';alias.symlink_to(root)
            with self.assertRaises(ValueError):ns.validate_fixture(alias,base,0)

    def test_passwd_cannot_point_outside_fixture(self):
        with tempfile.TemporaryDirectory(prefix='TEST-NS-',dir=h.WORKROOT)as work:
            root=Path(work)/'fx';root.mkdir()
            with self.assertRaises(ValueError):ns.prepare(root,h.WORKROOT,{'uid':0,'passwd_entries':[{'name':'root','uid':0,'home':'../../escape'}]})

    def test_missing_and_empty_passwd_homes_are_distinct(self):
        for entries,want in [([],''),([{'name':'root','uid':0,'home':''}],'root:x:0:0:Fixture::/bin/sh\n')]:
            with tempfile.TemporaryDirectory(prefix='TEST-NS-',dir=h.WORKROOT)as work:
                root=Path(work)/'fx';root.mkdir()
                ns.prepare(root,h.WORKROOT,{'uid':0,'passwd_entries':entries})
                self.assertEqual((root/'namespace-nss/passwd').read_text(),want)

    def test_tampered_mount_root_never_launches(self):
        with tempfile.TemporaryDirectory(prefix='TEST-NS-',dir=h.WORKROOT)as work:
            root=Path(work)/'fx';root.mkdir();state=Path(work)/'namespace.json'
            state.write_text(json.dumps({'fixture':str(root),'root':'/','uid':0}))
            with patch.object(ns.sys,'argv',['namespace_exec',str(state),'/usr/bin/true','/usr/bin/true','{}','["nano"]']),patch.object(ns.subprocess,'run')as launch:
                with self.assertRaises(ValueError):ns.main()
                launch.assert_not_called()

    def test_crash_decision_cannot_hide_file_or_identity_changes(self):
        tid='TEST-ROOT-HOME-002-NO-HOME-TILDE'
        fixture=json.loads((Path(__file__).parent/'fixtures/namespace-nohome-reviewed.json').read_text())
        source,target=(fixture['records'][side]for side in ('reference','candidate'))
        # Whole reference-derived differences replace the old toy field whitelist.
        # This pair comes from the reviewed old qualification, not current output.
        from compare_runs import compare
        # The 0.1.3 policy rejects the historical branded title. Preserve the
        # recording and project only its reviewed version cells in this copy.
        self.assertIsNone(policy.deviation(tid,source,target,compare(source,target)))
        historical=target
        target=copy.deepcopy(historical)
        row=target['snapshots']['opened']['rows'][0]
        self.assertEqual(row['text'].count('NARO 0.1.1'),1)
        row['text']=row['text'].replace('NARO 0.1.1','NARO 0.1.3',1)
        self.assertEqual([d['field']for d in compare(historical,target)],
                         ['snapshot.opened.row0.text'])
        differences=compare(source,target)
        self.assertEqual(policy.deviation(tid,source,target,differences),'Q-ROOT-NOHOME-001')
        changed=copy.deepcopy(target);changed['fixture']['work/f.txt']['mode']='0o600'
        self.assertIsNone(policy.deviation(tid,source,changed,differences))
        self.assertIsNone(policy.deviation(tid,source,changed,compare(source,changed)))
        changed=copy.deepcopy(target);changed['root_namespace']['euid']=1000
        self.assertIsNone(policy.deviation(tid,source,changed,differences))
        self.assertIsNone(policy.deviation(tid,source,changed,compare(source,changed)))
        changed=copy.deepcopy(source);changed['root_namespace']['euid']=1000
        self.assertIsNone(policy.deviation(tid,changed,target,compare(changed,target)))
        changed=copy.deepcopy(target);changed['inputs'][0]['hex']='00'
        self.assertIsNone(policy.deviation(tid,source,changed,differences))
        self.assertIsNone(policy.deviation(tid,source,changed,compare(source,changed)))
        self.assertIsNone(policy.deviation('TEST-UNRELATED-001',source,target,differences))
        self.assertIsNone(policy.deviation(tid,source,target,differences+[{'field':'inputs'}]))
        self.assertIsNone(policy.deviation(tid,source,target,[{'field':d['field']}for d in differences]))

    def test_term_linux_on_pty_does_not_certify_vt(self):
        with patch.object(console.os,'isatty',return_value=True),patch.object(console.os,'ttyname',return_value='/dev/pts/123'),patch.object(console,'attrs',return_value=[]),patch.object(console.fcntl,'ioctl',side_effect=OSError(errno.ENOTTY,'not a VT'))as ioctl,patch.dict(console.os.environ,{'TERM':'linux'}):
            result=console.probe()
        self.assertFalse(result['real_vt']);self.assertEqual(result['status'],'deferred')
        self.assertEqual([call.args[1]for call in ioctl.call_args_list],[0x5603,0x5603])

    def test_different_console_descriptors_are_not_operator_ready(self):
        with patch.object(console.os,'isatty',return_value=True),patch.object(console.os,'ttyname',side_effect=['/dev/tty1','/dev/tty2']),patch.object(console,'attrs',return_value=[]),patch.object(console.fcntl,'ioctl',return_value=0):
            self.assertFalse(console.probe()['real_vt'])

if __name__=='__main__':unittest.main()
