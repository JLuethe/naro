#!/usr/bin/env python3
"""Bounded direct-PTY regression for Cancel behind a retained input burst."""
import argparse
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
import sys
import tempfile
import termios
import time

FILE_BYTES = 12 * 1024 * 1024
PREFIX_BYTES = 8192
MAX_CANCEL_SECONDS = 3.0
MAX_BASELINE_SECONDS = 10.0


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run_case(binary, source, home, prefix, latency_bound):
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))

    def setup():
        os.setsid()
        fcntl.ioctl(0, termios.TIOCSCTTY, 0)
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_CPU, (25, 25))

    env = {"PATH": "/usr/bin:/bin", "HOME": str(home),
           "XDG_CONFIG_HOME": str(home), "XDG_DATA_HOME": str(home),
           "TERM": "xterm-256color", "LC_ALL": "C.UTF-8"}
    process = subprocess.Popen([str(binary), "-I", "-v", str(source)],
                               cwd=source.parent, env=env, stdin=slave,
                               stdout=slave, stderr=slave, preexec_fn=setup)
    os.close(slave)
    raw = bytearray()
    sent = 0
    elapsed = None
    try:
        def drain(seconds):
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                if not select.select([master], [], [],
                                     max(0, min(.02, deadline - time.monotonic())))[0]:
                    continue
                try:
                    part = os.read(master, 65536)
                except OSError:
                    break
                if not part:
                    break
                raw.extend(part)

        def wait_for(marker, seconds):
            deadline = time.monotonic() + seconds
            while marker not in raw and time.monotonic() < deadline:
                drain(.02)
            if marker not in raw:
                raise AssertionError(f"missing {marker!r} within {seconds}s")

        wait_for(b"^X", 4)
        drain(.3)
        if os.write(master, b"\x17") != 1:
            raise AssertionError("partial search-key input")
        wait_for(b"Search", 4)
        if os.write(master, b"zzzz\r") != 5:
            raise AssertionError("partial search-text input")
        drain(.08)
        if b"not found" in raw:
            raise AssertionError("search finished before cancellation burst")
        burst = b"g" * prefix + b"\x03X"
        start = time.monotonic()
        sent = os.write(master, burst)
        if sent != len(burst):
            raise AssertionError(f"partial cancellation burst: {sent}/{len(burst)}")
        deadline = start + latency_bound
        while b"Cancelled" not in raw and b"not found" not in raw and time.monotonic() < deadline:
            drain(.02)
        elapsed = time.monotonic() - start
        if b"Cancelled" not in raw or b"not found" in raw:
            raise AssertionError("cancel was absent or search completed")
        if elapsed >= latency_bound:
            raise AssertionError(f"cancel latency {elapsed:.3f}s exceeded bound")
        drain(.2)
        if os.write(master, b"\x18") != 1:
            raise AssertionError("partial exit-key input")
        drain(.2)
        process.wait(timeout=5)
        if process.returncode != 0:
            raise AssertionError(f"editor exit status {process.returncode}")
        return {"status": "PASS", "prefix_bytes": prefix, "burst_bytes": sent,
                "latency_bound_seconds": latency_bound,
                "cancel_seconds": round(elapsed, 3), "exit_status": process.returncode,
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "raw_bytes": len(raw)}
    except Exception as error:
        return {"status": "FAIL", "prefix_bytes": prefix, "burst_bytes": sent,
                "latency_bound_seconds": latency_bound,
                "cancel_seconds": None if elapsed is None else round(elapsed, 3),
                "error": str(error), "exit_status": process.poll(),
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "raw_bytes": len(raw)}
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    args.out.mkdir(parents=True, exist_ok=False)
    results = []
    with tempfile.TemporaryDirectory(prefix="issue14-backlog-", dir=args.out) as temp:
        root = Path(temp)
        home = root / "home"
        home.mkdir()
        source = root / "large.txt"
        source.write_bytes((b"A" * 4095 + b"\n") * (FILE_BYTES // 4096))
        original = digest(source)
        for prefix in (0, PREFIX_BYTES):
            if prefix == 0:
                bound = MAX_BASELINE_SECONDS
            elif results[0]["status"] == "PASS":
                bound = max(MAX_CANCEL_SECONDS, 2 * results[0]["cancel_seconds"] + .5)
            else:
                bound = MAX_CANCEL_SECONDS
            result = run_case(binary, source, home, prefix, bound)
            result["file_unchanged"] = digest(source) == original
            if not result["file_unchanged"]:
                result["status"] = "FAIL"
            results.append(result)
            print(f"backlog prefix={prefix}: {result['status']} "
                  f"latency={result['cancel_seconds']}s "
                  f"exit={result['exit_status']}")
    report = {"binary": str(binary), "binary_sha256": digest(binary),
              "fixture_size": FILE_BYTES, "fixture_sha256": original,
              "minimum_backlog_bound_seconds": MAX_CANCEL_SECONDS, "cases": results}
    (args.out / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0 if all(row["status"] == "PASS" for row in results) else 1


if __name__ == "__main__":
    sys.exit(main())
