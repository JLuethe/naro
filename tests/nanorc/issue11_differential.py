#!/usr/bin/env python3
"""Bounded nano 9.3 comparisons for the three issue #11 nanorc gaps."""

import fcntl
import hashlib
import os
from pathlib import Path
import pty
import select
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import termios
import time


ROOT = Path(__file__).resolve().parents[2]
NANO = Path("/home/john/src/nano-install/default/bin/nano")
NARO = ROOT / "target/debug/naro"
WORK = ROOT / "target/issue-11-config"
ENV = dict(os.environ, TERM="xterm", LANG="C.UTF-8", LC_ALL="C.UTF-8")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_list(binary, rc=None, env=ENV, prefix=()):
    args = [*prefix, str(binary)]
    if rc is not None:
        args += ["-f", str(rc)]
    args += ["-z"]
    result = subprocess.run(args, env=env, capture_output=True, timeout=5, check=True)
    assert result.stderr == b"", result.stderr
    return result.stdout


def run_editor(binary, rc, operand=None, env=ENV):
    pid, fd = pty.fork()
    if pid == 0:
        os.environ.clear()
        os.environ.update(env)
        fcntl.ioctl(0, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
        args = [os.fsencode(str(binary)), b"-f", os.fsencode(rc)]
        if operand is not None:
            args.append(os.fsencode(operand))
        os.execv(args[0], args)
    output = bytearray()
    start = time.monotonic()
    sent_exit = False
    status = None
    while time.monotonic() - start < 5:
        if not sent_exit and time.monotonic() - start > 0.25:
            try:
                os.write(fd, b"\x18")
            except OSError:
                pass
            sent_exit = True
        ready, _, _ = select.select([fd], [], [], 0.05)
        if ready:
            try:
                output.extend(os.read(fd, 65536))
            except OSError:
                break
        ended, value = os.waitpid(pid, os.WNOHANG)
        if ended:
            status = value
            break
    if status is None:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        _, status = os.waitpid(pid, 0)
    os.close(fd)
    assert os.waitstatus_to_exitcode(status) == 0, bytes(output[-500:])
    return bytes(output)


def main():
    for binary in (NANO, NARO):
        if not binary.is_file():
            raise SystemExit(f"missing prerequisite: {binary}")
    if shutil.which("bwrap") is None:
        raise SystemExit("missing prerequisite: bwrap")
    WORK.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="differential-", dir=WORK) as temporary:
        fixture = Path(temporary)
        syntax = fixture / "syntax"
        syntax.mkdir()
        for name in "abc":
            (syntax / f"{name}.nanorc").write_text(
                f'syntax {name} "{name}$"\ncolor red "{name}"\n'
            )
        main_rc = fixture / "glob.nanorc"
        main_rc.write_text(f'include "{syntax}/[ab].nanorc"\n')
        expected = b"Available syntaxes:\n b a\n"
        for binary in (NANO, NARO):
            assert run_list(binary, main_rc) == expected, binary
        print("bracket include: identical syntax list and order")

        nested = fixture / "group_a"
        nested.mkdir()
        (nested / "rules.nanorc").write_text(
            'syntax grouped "grouped$"\ncolor red "grouped"\n'
        )
        nested_rc = fixture / "nested-glob.nanorc"
        nested_rc.write_text(f'include "{fixture}/group_[ab]/rules.nanorc"\n')
        for binary in (NANO, NARO):
            assert run_list(binary, nested_rc) == b"Available syntaxes:\n grouped\n"
        print("bracket directory: identical nested expansion")

        invalid = fixture / "invalid.nanorc"
        invalid.write_bytes(b"set tabsize 3\nset wordchars A\xffB\n")
        error = (
            f"Error in {invalid} on line 2: "
            "Argument is not a valid multibyte string\r\n"
        ).encode()
        for binary in (NANO, NARO):
            output = run_editor(binary, invalid)
            assert output.count(error) == 1, (binary, output[-500:])
        print("UTF-8 malformed argument: identical file, line, and diagnostic")

        byte_dir = os.fsencode(fixture) + b"/dir_\xff"
        os.mkdir(byte_dir)
        with open(byte_dir + b"/opened.txt", "wb") as stream:
            stream.write(b"BYTE_DIR_MARKER\n")
        byte_rc = fixture / "byte.nanorc"
        byte_rc.write_bytes(b'set operatingdir "' + byte_dir + b'"\n')
        c_env = dict(ENV, LANG="C", LC_ALL="C")
        for binary in (NANO, NARO):
            output = run_editor(binary, byte_rc, "opened.txt", c_env)
            assert b"BYTE_DIR_MARKER" in output, (binary, output[-500:])
            assert b"Invalid operating directory" not in output, binary
        print("C locale: raw non-UTF-8 directory bytes open the expected file")

        system = fixture / "system.nanorc"
        system.write_text('syntax system "system$"\ncolor red "system"\n')
        home = fixture / "home"
        home.mkdir()
        (home / ".nanorc").write_text('syntax user "user$"\ncolor blue "user"\n')
        xdg = fixture / "xdg/nano"
        xdg.mkdir(parents=True)
        (xdg / "nanorc").write_text('syntax ignored "ignored$"\ncolor green "ignored"\n')
        copied_nano = fixture / "pinned-nano"
        shutil.copy2(NANO, copied_nano)
        assert digest(copied_nano) == digest(NANO)
        sysenv = dict(ENV, HOME=str(home), XDG_CONFIG_HOME=str(xdg.parent.parent))
        nano_prefix = [
            "bwrap", "--ro-bind", "/", "/", "--dev-bind", "/dev", "/dev",
            "--proc", "/proc", "--tmpfs", "/home/john/src/nano-install/default",
            "--dir", "/home/john/src/nano-install/default/etc", "--ro-bind",
            str(system), "/home/john/src/nano-install/default/etc/nanorc",
            "--",
        ]
        naro_prefix = [
            "bwrap", "--ro-bind", "/", "/", "--dev-bind", "/dev", "/dev",
            "--proc", "/proc", "--tmpfs", "/etc", "--ro-bind", str(system),
            "/etc/nanorc", "--",
        ]
        expected = b"Available syntaxes:\n user system\n"
        assert run_list(copied_nano, env=sysenv, prefix=nano_prefix) == expected
        assert run_list(NARO, env=sysenv, prefix=naro_prefix) == expected
        print("isolated system + first user rcfile: identical syntax list and order")

    print(f"nano_sha256={digest(NANO)}")
    print(f"naro_sha256={digest(NARO)}")


if __name__ == "__main__":
    main()
