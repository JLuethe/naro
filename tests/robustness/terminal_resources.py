#!/usr/bin/env python3
"""Bound real production-editor file loading with private PTY fixtures."""
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
import signal
import struct
import subprocess
import termios
import time

ADDRESS_MIB = 512
RSS_MIB = 128
TIME_SECONDS = 30
TRACE_LIMIT = 2 * 1024 * 1024


class InfrastructureError(Exception):
    pass


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def fixture(path, letter, lines):
    line = letter * 4095 + b'\n'
    with path.open('wb') as stream:
        for _ in range(lines):
            stream.write(line)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest(path)}


def run_case(binary, out, multi, tiny):
    out.mkdir()
    home = out / 'home'
    home.mkdir()
    paths = ([out / f'buffer-{i:02d}.txt' for i in range(8)] if multi
             else [out / 'large.txt'])
    inputs = [fixture(path, bytes([ord('A') + i]), 512 if multi else 3072)
              for i, path in enumerate(paths)]
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 24, 80, 0, 0))
    command = [str(binary)] + ([] if tiny else ['-I']) + list(map(str, paths))
    env = dict(os.environ, TERM='xterm-256color', LC_ALL='C.UTF-8',
               HOME=str(home), XDG_CONFIG_HOME=str(home), XDG_DATA_HOME=str(home))

    def setup():
        os.setsid()
        fcntl.ioctl(0, termios.TIOCSCTTY, 0)
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_AS, (ADDRESS_MIB * 1024 * 1024,) * 2)
        resource.setrlimit(resource.RLIMIT_CPU, (TIME_SECONDS,) * 2)

    process = None
    trace = bytearray()
    started = time.monotonic()
    reaped = False
    try:
        try:
            process = subprocess.Popen(command, stdin=slave, stdout=slave, stderr=slave,
                                       cwd=out, env=env, preexec_fn=setup)
        except OSError as error:
            raise InfrastructureError(f'cannot start PTY fixture: {error}') from error

        def drain(seconds):
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                if select.select([master], [], [], min(.02, max(0, deadline - time.monotonic())))[0]:
                    try:
                        block = os.read(master, 65536)
                    except OSError as error:
                        if error.errno != errno.EIO:
                            raise
                        break
                    if len(trace) + len(block) > TRACE_LIMIT:
                        raise AssertionError('terminal trace exceeded bounded limit')
                    trace.extend(block)

        def wait_for(marker, seconds=15, offset=0):
            deadline = time.monotonic() + seconds
            while marker not in trace[offset:] and time.monotonic() < deadline:
                drain(.02)
            if marker not in trace[offset:]:
                raise AssertionError(f'missing terminal marker {marker!r}')

        wait_for(b'^X')
        wait_for(b'A' * 8)
        if multi:
            for i in range(1, len(paths)):
                offset = len(trace)
                os.write(master, b'\x1b.')
                wait_for(bytes([ord('A') + i]) * 8, offset=offset)

        # Each ^X closes one unmodified buffer; waitid observes without reaping
        # so wait4 can report the true child peak RSS after exit.
        for _ in range(len(paths) + 2):
            os.write(master, b'\x18')
            drain(.1)
            if os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT):
                break
        else:
            raise AssertionError('editor did not close its unmodified buffers')
        _, status, usage = os.wait4(process.pid, 0)
        reaped = True
        process.returncode = os.waitstatus_to_exitcode(status)
        elapsed = time.monotonic() - started
        if process.returncode != 0:
            raise AssertionError(f'editor exited {process.returncode}')
        if elapsed > TIME_SECONDS:
            raise AssertionError(f'elapsed {elapsed:.3f}s exceeds {TIME_SECONDS}s')
        if usage.ru_maxrss > RSS_MIB * 1024:
            raise AssertionError(f'peak RSS {usage.ru_maxrss} KiB exceeds {RSS_MIB} MiB')
        for row in inputs:
            if digest(Path(row['path'])) != row['sha256']:
                raise AssertionError(f'input changed: {row["path"]}')
        return {'status': 'pass', 'command': command, 'inputs': inputs,
                'exit_code': process.returncode, 'elapsed_seconds': elapsed,
                'peak_rss_kib': usage.ru_maxrss, 'buffers_seen': len(paths),
                'trace_sha256': hashlib.sha256(trace).hexdigest()}
    finally:
        if process is not None and not reaped:
            os.kill(process.pid, signal.SIGKILL)
            os.wait4(process.pid, 0)
        os.close(master)
        os.close(slave)
        (out / 'terminal.raw').write_bytes(trace)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--expected-revision', required=True)
    parser.add_argument('--tiny', action='store_true')
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    out.chmod(0o700)
    info = json.loads(subprocess.check_output([str(binary)],
                        env=dict(os.environ, NARO_BUILD_INFO='1')))
    if info['revision'] != args.expected_revision:
        raise InfrastructureError('binary revision differs from requested revision')
    if ('tiny' in info['features'].split(',')) != args.tiny:
        raise InfrastructureError('binary feature profile differs from requested profile')
    report = {'binary': str(binary), 'binary_sha256': digest(binary),
              'build_info': info, 'native_libraries': subprocess.check_output(
                  ['ldd', str(binary)], text=True), 'limits': {
                      'address_space_mib': ADDRESS_MIB, 'peak_rss_mib': RSS_MIB,
                      'elapsed_seconds': TIME_SECONDS, 'trace_bytes': TRACE_LIMIT},
              'cases': []}
    for name, multi in [('large-file', False)] + ([] if args.tiny else [('eight-buffers', True)]):
        try:
            row = run_case(binary, out / name, multi, args.tiny)
        except InfrastructureError as error:
            row = {'status': 'infrastructure-failure', 'error': repr(error)}
        except Exception as error:
            row = {'status': 'product-or-assertion-failure', 'error': repr(error)}
        report['cases'].append({'name': name, **row})
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(f"{name}: {row['status']}" + (f" {row['error']}" if 'error' in row else ''), flush=True)
    raise SystemExit(0 if all(row['status'] == 'pass' for row in report['cases']) else 1)


if __name__ == '__main__':
    main()
