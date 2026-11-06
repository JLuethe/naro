#!/usr/bin/env python3
"""Bounded cancellation through actual PTY input; writes only private fixtures."""
import argparse
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pty
import resource
import select
import struct
import subprocess
import termios
import time


def run(binary, root, replace, tiny):
    root.mkdir()
    home = root / 'home'
    home.mkdir()
    path = root / 'fixture.txt'
    size = (8 if replace else 32) * 1024 * 1024
    original = (b'a' * 4096 + b'\n') * (size // 4096)
    path.write_bytes(original)
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 24, 80, 0, 0))
    trace = bytearray()
    def setup():
        os.setsid()
        fcntl.ioctl(0, termios.TIOCSCTTY, 0)
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_AS, (384 * 1024 * 1024,) * 2)
    env = dict(os.environ, TERM='xterm-256color', LC_ALL='C.UTF-8', HOME=str(home), XDG_CONFIG_HOME=str(home))
    command = [str(binary)] + ([] if tiny else ['-I']) + [str(path)]
    process = subprocess.Popen(command, cwd=root, env=env, stdin=slave, stdout=slave, stderr=slave, preexec_fn=setup)
    def drain(seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if select.select([master], [], [], min(.02, max(0, end-time.monotonic())))[0]:
                try: trace.extend(os.read(master, 65536))
                except OSError as error:
                    if error.errno != errno.EIO: raise
                    break
    def wait(marker, timeout=5):
        end = time.monotonic()+timeout
        while marker not in trace and time.monotonic()<end:
            drain(.02)
        assert marker in trace, f'missing {marker!r}; exit={process.poll()}'
    try:
        wait(b'^X')
        os.write(master, b'\x1c' if replace else b'\x17')
        drain(.1)
        os.write(master, b'a\r' if replace else b'z\r')
        if replace:
            wait(b'Replace with')
            os.write(master, b'bb\r')
            wait(b'this instance?')
            os.write(master, b'a')
        drain(.03)
        sent = time.monotonic()
        os.write(master, b'\x03')
        wait(b'Replaced' if replace else b'Cancelled', 2)
        latency = time.monotonic()-sent
        if replace:
            os.write(master, b'\x0f')
            drain(.1)
            os.write(master, b'\r')
            wait(b'Wrote', 5)
        os.write(master, b'\x18')
        end=time.monotonic()+3
        while process.poll() is None and time.monotonic()<end: drain(.02)
        assert process.poll()==0, 'editor did not exit cleanly'
        data=path.read_bytes()
        if replace:
            replaced=len(data)-len(original)
            assert 0<replaced<size, 'cancel must leave some occurrences unchanged'
            assert data==original.replace(b'a',b'bb',replaced), 'partial replacement bytes'
        else:
            replaced=0
            assert data==original, 'find changed file'
        return dict(passed=True, command=command, cancelled_latency_seconds=latency,
                    input_bytes=len(original), replaced=replaced, exit_code=process.returncode)
    finally:
        if process.poll() is None: process.kill(); process.wait(timeout=3)
        os.close(master);os.close(slave)
        (root/'terminal.raw').write_bytes(trace)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--tiny', action='store_true')
    args=parser.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    binary=args.binary.resolve()
    rows=[]
    for name,replace in [('find',False),('replace',True)]:
        try: row=run(binary,out/name,replace,args.tiny)
        except Exception as error: row=dict(passed=False,error=repr(error))
        row['case']=name;rows.append(row)
        print(name,row,flush=True)
    report=dict(binary=str(binary),binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                build_info=subprocess.check_output([str(binary)],env=dict(os.environ,NARO_BUILD_INFO='1')).decode(),
                cases=rows,passed=all(row['passed'] for row in rows))
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    return int(not report['passed'])

if __name__=='__main__':raise SystemExit(main())
