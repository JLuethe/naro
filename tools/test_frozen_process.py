"""Negative controls for timeout and narrowly owned tmux cleanup."""
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
import socket
import json
import sys
from unittest.mock import patch, Mock

from frozen_process import (cleanup_owned_tmux, make_private_tmux_tmpdir,
                            remove_private_tmux_tmpdir, run_owned_process)


class FrozenProcessCleanupTests(unittest.TestCase):
    def stale_socket(self, root):
        folder = root / f"tmux-{os.getuid()}"
        folder.mkdir()
        path = folder / "stale"
        with socket.socket(socket.AF_UNIX) as sock:
            sock.bind(str(path))
        return path

    def test_dead_socket_cleanup_cli_is_successful_and_idempotent(self):
        with tempfile.TemporaryDirectory(prefix="naro-dead-tmux-") as temp:
            root = Path(temp)
            stale = self.stale_socket(root)
            for attempt in range(2):
                out = root / f"cleanup-{attempt}.json"
                run = subprocess.run([sys.executable, str(Path(__file__).with_name("frozen_process.py")),
                                      "--cleanup-tmux", str(root), "--out", str(out)],
                                     capture_output=True, text=True, timeout=10)
                self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
                report = json.loads(out.read_text())
                self.assertTrue(report["passed"])
                if attempt == 0:
                    self.assertEqual(report["results"][0]["status"], 1)
                    self.assertTrue(report["results"][0]["stale_socket_removed"])
                else: self.assertEqual(report["results"], [])
            self.assertFalse(stale.exists())

    def test_unexpected_client_error_is_not_hidden_by_dead_socket_cleanup(self):
        with tempfile.TemporaryDirectory(prefix="naro-tmux-error-") as temp:
            root = Path(temp)
            self.stale_socket(root)
            process = Mock(returncode=1)
            process.communicate.return_value = (b"", b"permission denied")
            # Keep the real status probe: even an independently confirmed dead
            # socket must not turn an unrelated client failure into success.
            real_run = subprocess.run
            def probe(*args, **kwargs):
                with patch("frozen_process.subprocess.Popen", subprocess_popen):
                    return real_run(*args, **kwargs)
            subprocess_popen = subprocess.Popen
            with patch("frozen_process.subprocess.Popen", return_value=process), patch("frozen_process.subprocess.run", side_effect=probe):
                records = cleanup_owned_tmux(root)
            self.assertFalse(records[0]["cleanup_ok"])
            self.assertEqual(records[0]["stderr"], "permission denied")

    def test_socket_symlink_is_preserved_without_contacting_its_target(self):
        with tempfile.TemporaryDirectory(prefix="naro-tmux-symlink-") as temp:
            root = Path(temp)
            owned = root / "owned"; owned.mkdir()
            target = self.stale_socket(root)
            folder = owned / f"tmux-{os.getuid()}"; folder.mkdir()
            (folder / "outside").symlink_to(target)
            with patch("frozen_process.subprocess.Popen") as client:
                records = cleanup_owned_tmux(owned)
            client.assert_not_called()
            self.assertFalse(records[0]["cleanup_ok"])
            self.assertTrue(target.is_socket())
            self.assertTrue((folder / "outside").is_symlink())

    def test_tmux_socket_path_stays_short_with_long_output_path(self):
        with tempfile.TemporaryDirectory(prefix="naro-long-output-") as temp:
            root = Path(temp)
            long_out = Path("/home/john/Code/naro/target") / ("naro-test-runs-" * 12) / "attempt01" / "host"
            self.assertGreater(len(os.fsencode(str(long_out))), 108)
            tmux_tmpdir, owner = make_private_tmux_tmpdir()
            env = os.environ.copy() | {"TMUX_TMPDIR": str(tmux_tmpdir)}
            try:
                subprocess.run(["tmux", "-L", "naro-long-out-test", "-f", "/dev/null",
                                "new-session", "-d", "-s", "long-out"], env=env, check=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
                socket = next((tmux_tmpdir / f"tmux-{os.getuid()}").glob("naro-long-out-test"))
                self.assertLess(len(os.fsencode(str(socket))), 108)
                self.assertTrue(socket.is_socket())
                result = run_owned_process(["true"], cwd=root, env=env, log_path=root / "true.log",
                                           timeout=5, tmux_tmpdir=tmux_tmpdir)
                self.assertEqual(result["status"], 0)
                self.assertFalse(socket.exists())
            finally:
                cleanup_owned_tmux(tmux_tmpdir)
                remove_private_tmux_tmpdir(tmux_tmpdir, owner)

    def test_timeout_terminates_only_the_owned_process_group(self):
        with tempfile.TemporaryDirectory(prefix="naro-process-group-") as temp:
            root = Path(temp)
            pid_file = root / "sleep.pid"
            log = root / "command.log"
            command = ["bash", "-c", f"sleep 60 & echo $! > {pid_file}; wait"]
            outcome = run_owned_process(command, cwd=root, env=os.environ.copy(), log_path=log,
                                        timeout=0.25)
            self.assertEqual(outcome["status"], 124)
            self.assertTrue(outcome["process_group_cleanup"]["reaped"])
            child_pid = int(pid_file.read_text())
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline and Path(f"/proc/{child_pid}").exists():
                stat_path = Path(f"/proc/{child_pid}/stat")
                if stat_path.exists() and stat_path.read_text().split()[2] == "Z":
                    break
                time.sleep(0.05)
            stat_path = Path(f"/proc/{child_pid}/stat")
            self.assertTrue(not stat_path.exists() or stat_path.read_text().split()[2] == "Z",
                            "timed out process-group child is still running")

    def test_tmux_cleanup_is_scoped_to_private_socket_directory(self):
        with tempfile.TemporaryDirectory(prefix="naro-tmux-cleanup-") as temp:
            root = Path(temp)
            owned = root / "owned"
            unowned = root / "unowned"
            owned.mkdir(mode=0o700)
            unowned.mkdir(mode=0o700)
            env_owned = os.environ.copy() | {"TMUX_TMPDIR": str(owned)}
            env_unowned = os.environ.copy() | {"TMUX_TMPDIR": str(unowned)}
            try:
                subprocess.run(["tmux", "-L", "naro-owned-test", "-f", "/dev/null", "new-session", "-d", "-s", "owned"], env=env_owned,
                               check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
                subprocess.run(["tmux", "-L", "naro-unowned-test", "-f", "/dev/null", "new-session", "-d", "-s", "unowned"], env=env_unowned,
                               check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
                owned_socket = next((owned / f"tmux-{os.getuid()}").glob("naro-owned-test"))
                unowned_socket = next((unowned / f"tmux-{os.getuid()}").glob("naro-unowned-test"))
                self.assertTrue(owned_socket.is_socket())
                self.assertTrue(unowned_socket.is_socket())
                result = run_owned_process(["true"], cwd=root, env=env_owned, log_path=root / "true.log",
                                           timeout=5, tmux_tmpdir=owned)
                self.assertEqual(result["status"], 0)
                self.assertFalse(owned_socket.exists())
                self.assertTrue(unowned_socket.is_socket(), "cleanup crossed its private TMUX_TMPDIR boundary")
            finally:
                cleanup_owned_tmux(owned)
                cleanup_owned_tmux(unowned)


if __name__ == "__main__":
    unittest.main()
