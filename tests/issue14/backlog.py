#!/usr/bin/env python3
"""Bounded direct-PTY regressions for buffered search cancellation."""
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

FILE_BYTES = 24 * 1024 * 1024
PREFIX_BYTES = 8192
MAX_CANCEL_SECONDS = 3.0
MAX_BASELINE_SECONDS = 10.0


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run_case(binary, source, home, prefix, latency_bound, raw_path,
             split=None, rcfile=None):
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
    options = ["-I", "-v"] if rcfile is None else [f"--rcfile={rcfile}", "-v"]
    process = subprocess.Popen([str(binary), *options, str(source)],
                               cwd=source.parent, env=env, stdin=slave,
                               stdout=slave, stderr=slave, preexec_fn=setup)
    os.close(slave)
    raw = bytearray()
    sent = 0
    elapsed = None
    epoch = time.monotonic()
    events = []

    def event(name):
        events.append({"name": name, "seconds": round(time.monotonic() - epoch, 6)})

    event("process_started")
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
        event("editor_ready")
        drain(.3)
        if os.write(master, b"\x17") != 1:
            raise AssertionError("partial search-key input")
        wait_for(b"Search", 4)
        event("search_prompt")
        if os.write(master, b"zzzz\r") != 5:
            raise AssertionError("partial search-text input")
        event("search_submitted")
        drain(.08)
        if b"not found" in raw:
            raise AssertionError("search finished before cancellation burst")
        burst = b"g" * prefix + b"\x03X" if split is None else split[0]
        start = time.monotonic()
        sent = os.write(master, burst)
        event("first_input_sent")
        if sent != len(burst):
            raise AssertionError(f"partial cancellation burst: {sent}/{len(burst)}")
        if split is not None:
            drain(.6)  # Cross several 50 ms search-poll intervals.
            if b"Cancelled" in raw or b"not found" in raw:
                raise AssertionError("search completed before split key's final bytes")
            final_sent = os.write(master, split[1] + b"X")
            event("final_input_sent")
            if final_sent != len(split[1]) + 1:
                raise AssertionError(f"partial final-key input: {final_sent}")
            sent += final_sent
        deadline = start + latency_bound
        while b"Cancelled" not in raw and b"not found" not in raw and time.monotonic() < deadline:
            drain(.02)
        elapsed = time.monotonic() - start
        event("cancellation_wait_ended")
        if b"Cancelled" not in raw or b"not found" in raw:
            raise AssertionError("cancel was absent or search completed")
        if elapsed >= latency_bound:
            raise AssertionError(f"cancel latency {elapsed:.3f}s exceeded bound")
        drain(.2)
        if os.write(master, b"\x18") != 1:
            raise AssertionError("partial exit-key input")
        drain(.2)
        process.wait(timeout=5)
        event("process_exited")
        if process.returncode != 0:
            raise AssertionError(f"editor exit status {process.returncode}")
        return {"status": "PASS", "prefix_bytes": prefix, "burst_bytes": sent,
                "latency_bound_seconds": latency_bound,
                "cancel_seconds": round(elapsed, 3), "exit_status": process.returncode,
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "raw_bytes": len(raw), "raw_path": raw_path.name,
                "events": events}
    except Exception as error:
        event("case_failed")
        return {"status": "FAIL", "prefix_bytes": prefix, "burst_bytes": sent,
                "latency_bound_seconds": latency_bound,
                "cancel_seconds": None if elapsed is None else round(elapsed, 3),
                "error": str(error), "exit_status": process.poll(),
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "raw_bytes": len(raw), "raw_path": raw_path.name,
                "events": events}
    finally:
        raw_path.write_bytes(raw)
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
        cases = [("baseline", 0, None, None),
                 ("backlog", PREFIX_BYTES, None, None)]
        for name, binding, first, final in (
            ("split-ss3-f1", "bind F1 cancel search\nset rawsequences\n", b"\x1bO", b"P"),
            ("split-csi-meta-left", "bind M-Left cancel search\n", b"\x1b[1;", b"3D"),
        ):
            rcfile = root / f"{name}.rc"
            rcfile.write_text("unbind ^C search\n" + binding)
            cases.append((name, 0, (first, final), rcfile))
        for name, prefix, split, rcfile in cases:
            if prefix == 0:
                bound = MAX_BASELINE_SECONDS
            elif results[0]["status"] == "PASS":
                bound = max(MAX_CANCEL_SECONDS, 2 * results[0]["cancel_seconds"] + .5)
            else:
                bound = MAX_CANCEL_SECONDS
            result = run_case(binary, source, home, prefix, bound,
                              args.out / f"{name}.raw", split, rcfile)
            result["id"] = name
            result["file_unchanged"] = digest(source) == original
            raw_file = args.out / result["raw_path"]
            result["raw_verified"] = (digest(raw_file) == result["raw_sha256"]
                                      and raw_file.stat().st_size == result["raw_bytes"])
            if not result["file_unchanged"] or not result["raw_verified"]:
                result["status"] = "FAIL"
            results.append(result)
            print(f"{name} prefix={prefix}: {result['status']} "
                  f"latency={result['cancel_seconds']}s "
                  f"exit={result['exit_status']}")
    report = {"binary": str(binary), "binary_sha256": digest(binary),
              "fixture_size": FILE_BYTES, "fixture_sha256": original,
              "minimum_backlog_bound_seconds": MAX_CANCEL_SECONDS, "cases": results}
    (args.out / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0 if all(row["status"] == "PASS" for row in results) else 1


if __name__ == "__main__":
    sys.exit(main())
