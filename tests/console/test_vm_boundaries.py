#!/usr/bin/env python3
"""Host boundary checks; these tests never connect to a VM or open a console."""
import importlib.util,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from console_vm import VM
class VMTests(unittest.TestCase):
    def test_non_fixture_socket_target_is_rejected(self):
        with self.assertRaises(ValueError):VM('/home')
    def test_screenshot_cannot_target_user_files(self):
        base=Path(os.environ.get('NANOSPEC_WORK','/tmp/nanospec-work'));base.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='TEST-VT-GUARD-',dir=base)as work:
            vm=VM.__new__(VM);vm.fixture=Path(work)/'fx';vm.fixture.mkdir();vm.command=Mock()
            with self.assertRaises(ValueError):vm.screenshot(Path(work)/'escape.ppm')
            vm.command.assert_not_called()
    def test_guest_controller_refuses_host_execution(self):
        result=subprocess.run([sys.executable,str(ROOT/'tests/console/guest.py')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        self.assertNotEqual(result.returncode,0);self.assertIn('requires the disposable VM root',result.stderr)
if __name__=='__main__':unittest.main()
