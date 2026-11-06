#!/usr/bin/env python3
"""Signal/paste cleanup checks in disposable Linux PTYs. --out must be fresh."""
import argparse
import errno
import fcntl
import hashlib
import itertools
import json
import os
from pathlib import Path
import pty
import select
import signal
import stat
import struct
import subprocess
import termios
import time


def run_case(binary, root, signals, paste=False, modified=True, burst=False, tiny=False):
    root.mkdir(parents=True)
    home = root/'home'
    home.mkdir()
    target = root/'fixture.txt'
    target.write_bytes(b'original\n')
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 24, 80, 0, 0))
    before = termios.tcgetattr(slave)
    trace = bytearray()
    def controlling_terminal():
        os.setsid()
        fcntl.ioctl(0, termios.TIOCSCTTY, 0)
    env = dict(os.environ, TERM='xterm-256color', LC_ALL='C.UTF-8', HOME=str(home), XDG_CONFIG_HOME=str(home))
    for key in ('LD_PRELOAD', 'NARO_TEST_PANIC_DIR', 'NARO_SAVE_FIXTURE'):
        env.pop(key, None)
    args = [str(binary)] + ([] if tiny else ['-I', '-G']) + [str(target)]
    proc = subprocess.Popen(args, cwd=root, env=env,
                            stdin=slave, stdout=slave, stderr=slave, preexec_fn=controlling_terminal)
    def drain():
        if select.select([master], [], [], .03)[0]:
            try:
                trace.extend(os.read(master, 65536))
            except OSError as e:
                if e.errno != errno.EIO:
                    raise
    def settle(seconds):
        deadline = time.monotonic()+seconds
        while time.monotonic()<deadline:
            drain()
    try:
        deadline = time.monotonic()+5
        while b'^X' not in trace and time.monotonic()<deadline:
            drain()
        assert b'^X' in trace, 'startup timeout'
        lock = root/'.fixture.txt.swp'
        assert lock.exists() == (not tiny), 'unexpected startup lock state'
        if modified:
            os.write(master, b'X')
            settle(.2)
            assert b'Modified' in trace, 'modified state not rendered'
        if paste:
            os.write(master, b'\x1b[200~Y')
            settle(.2)
        if burst:
            os.kill(proc.pid, signal.SIGSTOP)
            stopped, status = os.waitpid(proc.pid, os.WUNTRACED)
            assert stopped==proc.pid and os.WIFSTOPPED(status)
        for sig in signals:
            os.kill(proc.pid, sig)
        if burst:
            os.kill(proc.pid, signal.SIGCONT)
        deadline = time.monotonic()+3
        while proc.poll() is None and time.monotonic()<deadline:
            drain()
        timed_out = proc.poll() is None
        if timed_out:
            proc.kill()
        proc.wait(timeout=3)
        settle(.1)
        after = termios.tcgetattr(slave)
        recovery = root/'fixture.txt.save'
        checks = dict(exited=not timed_out, exit_status=proc.returncode==1,
                      diagnostic=b'Received SIGHUP or SIGTERM' in trace, termios_restored=before==after,
                      alternate_screen_off=b'\x1b[?1049l' in trace, paste_off=b'\x1b[?2004l' in trace,
                      cursor_visible=b'\x1b[?25h' in trace, lock_removed=not lock.exists(),
                      original_unchanged=target.read_bytes()==b'original\n', recovery_present=recovery.exists()==modified)
        if tiny:
            del checks['paste_off']
            checks['paste_never_enabled'] = b'\x1b[?2004h' not in trace
        if modified and recovery.exists():
            checks['recovery_bytes'] = recovery.read_bytes()==(b'XYoriginal\n' if paste else b'Xoriginal\n')
            checks['recovery_mode'] = stat.S_IMODE(recovery.stat().st_mode)==0o600
        return dict(checks=checks, passed=all(checks.values()), exit_status=proc.returncode,
                    timed_out=timed_out, signals=[s.name for s in signals], paste=paste, modified=modified)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        os.close(master)
        os.close(slave)
        (root/'terminal.raw').write_bytes(trace)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--tiny', action='store_true')
    parser.add_argument('--paste-only', action='store_true')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    out, binary = args.out.resolve(), args.binary.resolve()
    rows, cases = [], []
    if not args.paste_only:
        for sig in (signal.SIGHUP,signal.SIGTERM):
            cases.extend([(sig.name,[sig],False,True,False),(sig.name+'-clean',[sig],False,False,False)])
        for i,perm in enumerate(itertools.permutations((signal.SIGHUP,signal.SIGTERM,signal.SIGWINCH))):
            cases.append((f'burst-{i}',list(perm),False,True,True))
    if not args.tiny:
        for sig in (signal.SIGHUP,signal.SIGTERM):
            cases.append((sig.name+'-paste',[sig],True,True,False))
    for name,sigs,paste,modified,burst in cases:
        try:
            row=run_case(binary,out/name,sigs,paste,modified,burst,args.tiny)
        except Exception as e:
            row=dict(passed=False,error=repr(e))
        row['name']=name
        rows.append(row)
        print(name, 'PASS' if row['passed'] else 'FAIL', {k:v for k,v in row.get('checks',{}).items() if not v}, row.get('error',''), flush=True)
    report=dict(binary=str(binary), binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                build_info=subprocess.check_output([str(binary)],env=dict(os.environ,NARO_BUILD_INFO='1')).decode(),
                passed=sum(x['passed'] for x in rows),total=len(rows),cases=rows)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f"{report['passed']}/{report['total']} passed")
    return int(report['passed']!=report['total'])

if __name__=='__main__':
    raise SystemExit(main())
