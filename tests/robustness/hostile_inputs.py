#!/usr/bin/env python3
"""Benign malformed catalogs and invalid-byte rcfile in private editor PTYs."""
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
import shutil
import struct
import subprocess
import termios
import time

MSGID = 'Write Out'
TRANSLATED = 'FIXOUT'
ERROR = b'Argument is not a valid multibyte string'


class InfrastructureError(Exception):
    pass


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def editor(binary, root, tiny, language, locale_root, rc=None):
    root.mkdir()
    home = root / 'home'
    home.mkdir()
    document = root / 'document.txt'
    original = b'unchanged synthetic fixture\n'
    document.write_bytes(original)
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 24, 80, 0, 0))

    def setup():
        os.setsid()
        fcntl.ioctl(0, termios.TIOCSCTTY, 0)
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024,) * 2)

    options = ['-f', str(rc)] if rc else ([] if tiny else ['-I'])
    command = [str(binary), *options, str(document)]
    env = dict(os.environ, TERM='xterm-256color', LC_ALL='en_US.UTF-8',
               LANGUAGE=language, NARO_LOCALEDIR=str(locale_root),
               HOME=str(home), XDG_CONFIG_HOME=str(home), XDG_DATA_HOME=str(home))
    child = None
    trace = bytearray()
    try:
        try:
            child = subprocess.Popen(command, cwd=root, env=env, stdin=slave,
                                     stdout=slave, stderr=slave, preexec_fn=setup)
        except OSError as error:
            raise InfrastructureError(f'cannot start PTY fixture: {error}') from error

        def drain(seconds):
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                if select.select([master], [], [], min(.02, max(0, deadline-time.monotonic())))[0]:
                    try:
                        trace.extend(os.read(master, 65536))
                    except OSError as error:
                        if error.errno != errno.EIO:
                            raise
                        break
                    if len(trace) > 1024 * 1024:
                        raise AssertionError('terminal trace exceeded 1 MiB')

        deadline = time.monotonic() + 5
        while b'^X' not in trace and time.monotonic() < deadline:
            drain(.02)
        if b'^X' not in trace:
            raise AssertionError('editor startup marker absent')
        os.write(master, b'\x18')
        deadline = time.monotonic() + 5
        while child.poll() is None and time.monotonic() < deadline:
            drain(.02)
        if child.poll() is None:
            raise AssertionError('editor exit timeout')
        drain(.05)
        if child.returncode != 0:
            raise AssertionError(f'editor exited {child.returncode}')
        if document.read_bytes() != original:
            raise AssertionError('unmodified input document changed')
        return command, bytes(trace), digest(document)
    finally:
        if child is not None and child.poll() is None:
            child.kill()
            child.wait()
        os.close(master)
        os.close(slave)
        (root / 'terminal.raw').write_bytes(trace)


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
    if info['features'] != ('tiny' if args.tiny else ''):
        raise InfrastructureError('binary feature profile differs from requested profile')
    if not shutil.which('msgfmt'):
        raise InfrastructureError('missing prerequisite: msgfmt')
    locale_env = dict(os.environ, LC_ALL='en_US.UTF-8', LANG='en_US.UTF-8')
    locale_check = subprocess.run(['/usr/bin/locale', 'charmap'], env=locale_env,
                                  text=True, capture_output=True, timeout=10)
    locale_result = {'command': ['/usr/bin/locale', 'charmap'],
                     'exit_code': locale_check.returncode,
                     'stdout': locale_check.stdout, 'stderr': locale_check.stderr}
    (out / 'locale-probe.json').write_text(json.dumps(locale_result, indent=2) + '\n')
    if (locale_check.returncode != 0 or locale_check.stderr or
            locale_check.stdout.strip().upper() != 'UTF-8'):
        raise InfrastructureError('missing prerequisite: en_US.UTF-8 locale')
    locale_root = out / 'locale'
    po = out / 'control.po'
    po.write_text('msgid ""\nmsgstr ""\n'
                  '"Content-Type: text/plain; charset=UTF-8\\n"\n\n'
                  f'msgid {json.dumps(MSGID)}\nmsgstr {json.dumps(TRANSLATED)}\n')
    control = out / 'control.mo'
    compiled = subprocess.run(['msgfmt', '--check', '-o', str(control), str(po)],
                              capture_output=True)
    (out / 'msgfmt.log').write_bytes(compiled.stdout + compiled.stderr)
    if compiled.returncode:
        raise InfrastructureError('control catalog compilation failed')
    data = control.read_bytes()
    variants = {'valid-control': data, 'empty': b'', 'truncated-header': data[:8],
                'invalid-magic': b'not-a-catalog'}
    report = {'binary': str(binary), 'binary_sha256': digest(binary),
              'build_info': info, 'native_libraries': subprocess.check_output(
                  ['ldd', str(binary)], text=True),
              'locale_probe': locale_result, 'tiny': args.tiny, 'catalog_variants': {},
              'cases': []}
    for label, content in variants.items():
        language = 'fixture_' + label.replace('-', '_')
        mo = locale_root / language / 'LC_MESSAGES/nano.mo'
        mo.parent.mkdir(parents=True)
        mo.write_bytes(content)
        report['catalog_variants'][label] = {'sha256': digest(mo), 'bytes': len(content)}
        try:
            command, trace, document_hash = editor(binary, out / label, args.tiny,
                                                    language, locale_root)
            wanted = TRANSLATED.encode() if label == 'valid-control' else MSGID.encode()
            if wanted not in trace:
                raise AssertionError(f'expected catalog outcome {wanted!r} absent')
            other = MSGID.encode() if label == 'valid-control' else TRANSLATED.encode()
            if other in trace:
                raise AssertionError('unexpected catalog outcome present')
            row = {'status': 'pass', 'command': command, 'trace_sha256': hashlib.sha256(trace).hexdigest(),
                   'document_sha256': document_hash}
        except InfrastructureError as error:
            row = {'status': 'infrastructure-failure', 'error': repr(error)}
        except Exception as error:
            row = {'status': 'product-or-assertion-failure', 'error': repr(error)}
        report['cases'].append({'name': label, **row})
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(f"{label}: {row['status']}" + (f" {row['error']}" if 'error' in row else ''), flush=True)

    if not args.tiny:
        invalid = out / 'invalid-byte.nanorc'
        invalid.write_bytes(b'set tabsize 3\nset wordchars A\xffB\n')
        try:
            command, trace, document_hash = editor(binary, out / 'invalid-byte-rc', False,
                                                    'C', locale_root, invalid)
            expected = (f'Error in {invalid} on line 2: '.encode() + ERROR + b'\r\n')
            if trace.count(expected) != 1:
                raise AssertionError('invalid-byte rcfile diagnostic absent or repeated')
            row = {'status': 'pass', 'command': command,
                   'rcfile_sha256': digest(invalid),
                   'trace_sha256': hashlib.sha256(trace).hexdigest(),
                   'document_sha256': document_hash}
        except InfrastructureError as error:
            row = {'status': 'infrastructure-failure', 'error': repr(error)}
        except Exception as error:
            row = {'status': 'product-or-assertion-failure', 'error': repr(error)}
        report['cases'].append({'name': 'invalid-byte-rc', **row})
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(f"invalid-byte-rc: {row['status']}" + (f" {row['error']}" if 'error' in row else ''), flush=True)

    raise SystemExit(0 if all(row['status'] == 'pass' for row in report['cases']) else 1)


if __name__ == '__main__':
    main()
