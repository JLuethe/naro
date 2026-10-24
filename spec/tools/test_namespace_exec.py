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
        source={'reference_commit':h.REFERENCE_COMMIT,'scenario':tid,'fixture':{'x':{'type':'file','mode':'0o644','b64':'YWJj'}},'exit_status':1,'stderr':'Sorry! Nano crashed!  Code: 11.','steps_ok':True,'checks':[{'pass':True}],'root_namespace':{'euid':0,'passwd_home':None,'HOME':None}}
        target=copy.deepcopy(source);target.update(exit_status=0,stderr='')
        differences=[{'field':'exit_status'},{'field':'stderr'}]
        self.assertEqual(policy.deviation(tid,source,target,differences),'Q-ROOT-NOHOME-001')
        changed=copy.deepcopy(target);changed['fixture']['x']['mode']='0o600'
        self.assertIsNone(policy.deviation(tid,source,changed,differences))
        changed=copy.deepcopy(source);changed['root_namespace']['euid']=1000
        self.assertIsNone(policy.deviation(tid,changed,target,differences))
        self.assertIsNone(policy.deviation('TEST-UNRELATED-001',source,target,differences))
        self.assertIsNone(policy.deviation(tid,source,target,differences+[{'field':'inputs'}]))

    def test_term_linux_on_pty_does_not_certify_vt(self):
        with patch.object(console.os,'isatty',return_value=True),patch.object(console.os,'ttyname',return_value='/dev/pts/123'),patch.object(console,'attrs',return_value=[]),patch.object(console.fcntl,'ioctl',side_effect=OSError(errno.ENOTTY,'not a VT'))as ioctl,patch.dict(console.os.environ,{'TERM':'linux'}):
            result=console.probe()
        self.assertFalse(result['real_vt']);self.assertEqual(result['status'],'deferred')
        self.assertEqual([call.args[1]for call in ioctl.call_args_list],[0x5603,0x5603])

    def test_different_console_descriptors_are_not_operator_ready(self):
        with patch.object(console.os,'isatty',return_value=True),patch.object(console.os,'ttyname',side_effect=['/dev/tty1','/dev/tty2']),patch.object(console,'attrs',return_value=[]),patch.object(console.fcntl,'ioctl',return_value=0):
            self.assertFalse(console.probe()['real_vt'])

if __name__=='__main__':unittest.main()
