#!/usr/bin/env python3
"""Bounded direct-PTY regressions for buffered search cancellation."""
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
import sys
import tempfile
import termios
import time

FILE_BYTES = 24 * 1024 * 1024
PREFIX_BYTES = 8192
MAX_CANCEL_SECONDS = 3.0
MAX_BASELINE_SECONDS = 10.0
RESET_MARKERS = (b"\x1b[?1049l", b"\x1b[?2004l")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run_case(binary, source, home, prefix, latency_bound, raw_path,
             split=None, rcfile=None, early_cancel=False):
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
    raw_complete = False
    teardown = "normal"
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

        def wait_for_count(marker, count, seconds):
            deadline = time.monotonic() + seconds
            while raw.count(marker) < count and time.monotonic() < deadline:
                drain(.02)
            if raw.count(marker) < count:
                raise AssertionError(f"missing {count} occurrences of {marker!r}")

        def drain_to_eof(seconds):
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                if not select.select([master], [], [],
                                     max(0, min(.02, deadline - time.monotonic())))[0]:
                    continue
                try:
                    part = os.read(master, 65536)
                except OSError as error:
                    if error.errno == errno.EIO:  # Linux PTY master at slave close.
                        event("pty_eof")
                        return True
                    raise
                if not part:
                    event("pty_eof")
                    return True
                raw.extend(part)
            event("pty_drain_timeout")
            return False

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
        if early_cancel:
            # Confirm that prompt input was consumed before testing a key
            # that could otherwise cancel the prompt itself.
            wait_for_count(b"\x1b[0;7mz", 4, 4)
            drain(.15)
        else:
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
            if not early_cancel:
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
        raw_complete = drain_to_eof(2)
        if not raw_complete:
            raise AssertionError("PTY output did not reach EOF after editor exit")
        if not all(marker in raw for marker in RESET_MARKERS):
            raise AssertionError("terminal reset bytes missing from complete output")
        if process.returncode != 0:
            raise AssertionError(f"editor exit status {process.returncode}")
        return {"status": "PASS", "prefix_bytes": prefix, "burst_bytes": sent,
                "latency_bound_seconds": latency_bound,
                "cancel_seconds": round(elapsed, 3), "exit_status": process.returncode,
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "raw_bytes": len(raw), "raw_path": raw_path.name,
                "events": events, "raw_complete": raw_complete,
                "terminal_reset": True, "teardown": teardown}
    except Exception as error:
        event("case_failed")
        if process.poll() is None:
            teardown = "killed_after_failure"
            process.kill()
            event("process_killed")
            process.wait(timeout=5)
        else:
            teardown = "already_exited_after_failure"
        event("process_reaped")
        raw_complete = drain_to_eof(2)
        return {"status": "FAIL", "prefix_bytes": prefix, "burst_bytes": sent,
                "latency_bound_seconds": latency_bound,
                "cancel_seconds": None if elapsed is None else round(elapsed, 3),
                "error": str(error), "exit_status": process.poll(),
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "raw_bytes": len(raw), "raw_path": raw_path.name,
                "events": events, "raw_complete": raw_complete,
                "terminal_reset": all(marker in raw for marker in RESET_MARKERS),
                "teardown": teardown}
    finally:
        raw_path.write_bytes(raw)
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
        cases = [("baseline", 0, None, None, False),
                 ("backlog", PREFIX_BYTES, None, None, False)]
        for name, binding, first, final in (
            ("split-ss3-f1", "bind F1 cancel search\nset rawsequences\n", b"\x1bO", b"P"),
            ("split-csi-meta-left", "bind M-Left cancel search\n", b"\x1b[1;", b"3D"),
        ):
            rcfile = root / f"{name}.rc"
            rcfile.write_text("unbind ^C search\n" + binding)
            cases.append((name, 0, (first, final), rcfile, False))
        cases.append(("split-csi-control", 0,
                      (b"\x1b[1;3", b"\x03"), None, False))
        meta_rc = root / "standalone-meta-bracket.rc"
        meta_rc.write_text("unbind ^C search\nbind M-[ cancel search\nset rawsequences\n")
        cases.append(("standalone-meta-bracket", 0,
                      (b"\x1b[", b""), meta_rc, True))
        for name, prefix, split, rcfile, early_cancel in cases:
            if prefix == 0:
                bound = MAX_BASELINE_SECONDS
            elif results[0]["status"] == "PASS":
                bound = max(MAX_CANCEL_SECONDS, 2 * results[0]["cancel_seconds"] + .5)
            else:
                bound = MAX_CANCEL_SECONDS
            result = run_case(binary, source, home, prefix, bound,
                              args.out / f"{name}.raw", split, rcfile, early_cancel)
            result["id"] = name
            result["file_unchanged"] = digest(source) == original
            raw_file = args.out / result["raw_path"]
            result["raw_verified"] = (digest(raw_file) == result["raw_sha256"]
                                      and raw_file.stat().st_size == result["raw_bytes"])
            if (not result["file_unchanged"] or not result["raw_verified"]
                    or not result["raw_complete"]):
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
