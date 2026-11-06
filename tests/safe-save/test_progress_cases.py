#!/usr/bin/env python3
"""Execute generated preload gates through glibc's fortified open calls."""
import errno
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
HELPER = r'''
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
static void interrupted(int sig) {(void)sig;}
int main(int argc,char **argv) {
 if(argc!=4)return 2;
 struct sigaction action={0};action.sa_handler=interrupted;
 if(sigaction(SIGUSR1,&action,NULL))return 3;
 umask(0);
 int flags=atoi(argv[2]),fd;
 if(!strcmp(argv[1],"open"))fd=open(argv[3],flags);
 else if(!strcmp(argv[1],"open64"))fd=open64(argv[3],flags);
 else if(!strcmp(argv[1],"openat")) {
  int dirfd=open(".",O_RDONLY|O_DIRECTORY);
  if(dirfd<0)return 4;
  fd=openat(dirfd,argv[3],flags);
  close(dirfd);
 } else if(!strcmp(argv[1],"openat-cwd"))fd=openat(AT_FDCWD,argv[3],flags);
 else if(!strcmp(argv[1],"create"))fd=open(argv[3],flags,0640);
 else if(!strcmp(argv[1],"create64"))fd=open64(argv[3],flags,0640);
 else if(!strcmp(argv[1],"createat"))fd=openat(AT_FDCWD,argv[3],flags,0640);
 else return 5;
 int error=fd<0?errno:0;
 if(fd>=0){
  if(!strncmp(argv[1],"create",6)){
   struct stat info;if(fstat(fd,&info)||(info.st_mode&0777)!=0640)return 6;
  }
  close(fd);
 }
 printf("%d\n",error);
 return 0;
}
'''


class ProgressGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        (cls.root / 'helper.c').write_text(HELPER)
        cls.helper = cls.root / 'helper'
        subprocess.run(['cc', '-O2', '-D_FORTIFY_SOURCE=2', str(cls.root / 'helper.c'),
                        '-o', str(cls.helper)], check=True)
        symbols = subprocess.check_output(['readelf', '-Ws', str(cls.helper)], text=True)
        for name in ('__open_2', '__open64_2', '__openat_2'):
            if name + '@' not in symbols:
                raise AssertionError(f'helper does not import fortified {name}')
        cases = json.loads(subprocess.check_output(
            [sys.executable, str(ROOT / 'tests/safe-save/progress_cases.py')], text=True))
        cls.gates = {}
        for kind, case_id in [('progress', 'TEST-SAVE-PROGRESS-ERROR-OPEN'),
                              ('interrupt', 'TEST-SAVE-PROGRESS-FIFO-INTERRUPT')]:
            case = next(c for c in cases if c['id'] == case_id)
            source = cls.root / (kind + '.c')
            source.write_text(case['files']['gate.c']['text'])
            gate = source.with_suffix('.so')
            subprocess.run(['cc', '-shared', '-fPIC', str(source), '-o', str(gate), '-ldl'], check=True)
            cls.gates[kind] = gate

    def setUp(self):
        self.fixture = tempfile.TemporaryDirectory(dir=self.root)
        self.addCleanup(self.fixture.cleanup)
        self.work = Path(self.fixture.name)
        self.target = self.work / 'target'
        self.target.write_bytes(b'original')

    def start(self, kind, operation, flags, target=None, **extra):
        env = {**os.environ, 'HOME': str(self.work), 'LD_PRELOAD': str(self.gates[kind]),
               'PROGRESS_TARGET': str(self.target), 'FIFO_TARGET': str(self.target),
               'PROGRESS_OPEN': '1', **extra}
        process = subprocess.Popen([str(self.helper), operation, str(flags), target or 'target'],
                                   cwd=self.work, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True)
        self.addCleanup(lambda: self.stop(process))
        return process

    @staticmethod
    def stop(process):
        if process.poll() is None:
            process.kill()
        process.communicate()

    def wait_for(self, process, predicate):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if predicate():
                return
            if process.poll() is not None:
                self.fail(f'helper exited before gate: {process.communicate()}')
            time.sleep(.01)
        self.fail('helper did not reach the expected open gate')

    def result(self, process, expected):
        stdout, stderr = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 0, stderr)
        self.assertEqual(stdout, str(expected) + '\n', stderr)

    def test_fortified_progress_gate_release_and_fault(self):
        for operation in ('open', 'open64', 'openat', 'openat-cwd'):
            for fault in (False, True):
                with self.subTest(operation=operation, fault=fault):
                    for name in ('OPEN.ready', 'OPEN.release'):
                        (self.work / name).unlink(missing_ok=True)
                    process = self.start('progress', operation, os.O_WRONLY,
                                         **({'FAIL_OPEN': '1'} if fault else {}))
                    self.wait_for(process, lambda: (self.work / 'OPEN.ready').exists())
                    self.assertIsNone(process.poll())
                    (self.work / 'OPEN.release').touch()
                    self.result(process, errno.EACCES if fault else 0)
                    self.assertEqual(self.target.read_bytes(), b'original')

    def test_fortified_fifo_open_can_be_interrupted_after_marker(self):
        self.target.unlink()
        os.mkfifo(self.target)
        for operation in ('open', 'open64', 'openat', 'openat-cwd'):
            with self.subTest(operation=operation):
                marker = self.work / 'open.pid'
                marker.unlink(missing_ok=True)
                process = self.start('interrupt', operation, os.O_WRONLY)
                self.wait_for(process, marker.exists)
                self.assertEqual(marker.read_text(), str(process.pid) + '\n')
                self.wait_for(process, lambda: 'wait_for_partner' in
                              Path(f'/proc/{process.pid}/wchan').read_text())
                process.send_signal(signal.SIGUSR1)
                self.result(process, errno.EINTR)

    def test_reads_and_unrelated_paths_bypass_gate_and_fault(self):
        for kind in self.gates:
            for operation in ('open', 'open64', 'openat'):
                for path, flags in [('target', os.O_RDONLY), ('other', os.O_WRONLY)]:
                    with self.subTest(kind=kind, operation=operation, path=path):
                        (self.work / 'other').write_bytes(b'other')
                        self.result(self.start(kind, operation, flags, path, FAIL_OPEN='1'), 0)
                        self.assertFalse((self.work / 'OPEN.ready').exists())
                        self.assertFalse((self.work / 'open.pid').exists())

    def test_variadic_creation_modes_are_preserved(self):
        for kind in self.gates:
            for operation in ('create', 'create64', 'createat'):
                with self.subTest(kind=kind, operation=operation):
                    path = self.work / (kind + operation)
                    self.result(self.start(kind, operation, os.O_CREAT | os.O_WRONLY,
                                           str(path)), 0)
                    self.assertEqual(path.stat().st_mode & 0o777, 0o640)
                    # O_TMPFILE also consumes a mode argument, without O_CREAT.
                    self.result(self.start(kind, operation, os.O_TMPFILE | os.O_RDWR,
                                           str(self.work)), 0)


if __name__ == '__main__':
    unittest.main()
