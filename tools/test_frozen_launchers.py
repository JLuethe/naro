"""Unit checks for explicit frozen-launcher inputs and non-mutating failures."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from prepare_console_vm_fixtures import validate_fixture_socket_paths  # noqa: E402


class FrozenLauncherPreflightTests(unittest.TestCase):
    def run_command(self, command):
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True, timeout=10)

    def test_required_path_arguments_are_explicit(self):
        required = {
            "tools/run_closure_host.py": ("--source-dir", "--binary", "--out"),
            "tools/run_closure_ubuntu.py": ("--source-dir", "--binary", "--out"),
            "tools/prepare_console_vm_fixtures.py": ("--source-dir", "--host-binary", "--ubuntu-binary", "--out"),
        }
        for script, options in required.items():
            with self.subTest(script=script):
                result = self.run_command([sys.executable, str(ROOT / script), "--help"])
                self.assertEqual(result.returncode, 0, result.stderr)
                for option in options:
                    self.assertIn(option, result.stdout)
        result = self.run_command([sys.executable, str(ROOT / "tools/check_cli.py"), "--help"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--binary", result.stdout)
        self.assertIn("--out", result.stdout)

    def test_failed_frozen_source_preflight_does_not_create_output(self):
        with tempfile.TemporaryDirectory(prefix="naro-launcher-preflight-") as temp:
            base = Path(temp)
            source = base / "missing-source"
            manifest = base / "missing-freeze.json"
            candidate = Path(sys.executable)
            common = ["--source-dir", str(source), "--binary", str(candidate),
                      "--freeze-manifest", str(manifest)]
            commands = [
                [sys.executable, str(ROOT / "tools/run_closure_host.py"), *common,
                 "--reference", str(candidate), "--root-reference", str(candidate)],
                [sys.executable, str(ROOT / "tools/run_closure_ubuntu.py"), *common,
                 "--reference", str(candidate), "--root-reference", str(candidate),
                 "--reference-install", str(base / "missing-reference-install")],
                [sys.executable, str(ROOT / "tools/prepare_console_vm_fixtures.py"), *common,
                 "--reference", str(candidate), "--root-reference", str(candidate),
                 "--exported-root", str(base / "missing-root"), "--runtime-archive", str(base / "missing.tar"),
                 "--vm-environment-manifest", str(manifest), "--kernel", str(candidate),
                 "--host-binary", str(candidate), "--ubuntu-binary", str(candidate)],
            ]
            for index, command in enumerate(commands):
                output = base / f"out-{index}"
                result = self.run_command(command + ["--out", str(output)])
                with self.subTest(script=command[1]):
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(output.exists())

    def test_cli_output_inside_source_is_rejected(self):
        output = ROOT / "target" / f"frozen-cli-should-not-create-{os.getpid()}"
        result = self.run_command([sys.executable, str(ROOT / "tools/check_cli.py"),
                                   "--binary", sys.executable, "--out", str(output)])
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output.exists())

    def test_vm_fixture_preflight_rejects_long_unix_socket_paths(self):
        with tempfile.TemporaryDirectory(prefix="naro-vm-path-") as temp:
            short = Path(temp) / "nv011"
            records = validate_fixture_socket_paths(short)
            self.assertEqual(len(records), 4)
            self.assertTrue(all(record["path_bytes"] <= record["limit_bytes"] for record in records))
            long = Path(temp) / ("qualification-output-" * 5)
            with self.assertRaisesRegex(ValueError, "choose a shorter --out"):
                validate_fixture_socket_paths(long)


if __name__ == "__main__":
    unittest.main()
