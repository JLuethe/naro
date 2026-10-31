#!/usr/bin/env python3
"""Assert NARO's own CLI identity without rewriting nano reference observations."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--profile", choices=("default", "tiny"), default="default")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    binary = args.binary.resolve()
    version = tomllib.loads((ROOT / "Cargo.toml").read_text())["package"]["version"]
    expected_version = (
        f" NARO, version {version}\n"
        " Independent Rust port of GNU nano; reference version 9.3\n"
        " License: GPL-3.0-or-later\n"
        f" Compiled profile: {args.profile}; UTF-8 enabled\n"
    )
    results = []
    with tempfile.TemporaryDirectory(prefix="naro-branding-") as home:
        env = dict(os.environ, HOME=home, XDG_CONFIG_HOME=home, LC_ALL="C", TERM="xterm")
        env.pop("NARO_BUILD_INFO", None)
        env.pop("NARO_TRANSLATION_PROBE", None)
        for name, argv, expected in [
            ("version-long", ["naro", "--version"], expected_version),
            ("version-short", ["naro", "-V"], expected_version),
            ("help-default", ["naro", "--help"], None),
            ("help-restricted-flag", ["naro", "--restricted", "--help"], None),
            ("help-restricted-argv0", ["rnaro", "--help"], None),
        ]:
            run = subprocess.run(argv, executable=str(binary), env=env, cwd=home,
                                 capture_output=True, text=True, timeout=10)
            if expected is None:
                restricted = "restricted" in name
                asset = ("help-tiny.txt" if args.profile == "tiny" else
                         "help-restricted.txt" if restricted else "help.txt")
                expected = (ROOT / "assets" / asset).read_text()
                if args.profile == "tiny" and restricted:
                    expected = "".join(line for line in expected.splitlines(keepends=True)
                                       if not line.startswith(" -R "))
                expected = expected.replace("Usage: nano ", "Usage: naro ")
                expected = expected.replace(", nano reads data", ", naro reads data")
            results.append(dict(name=name, argv=argv, exit_status=run.returncode,
                                stdout=run.stdout, stderr=run.stderr, expected=expected,
                                passed=run.returncode == 0 and run.stdout == expected
                                and run.stderr == ""))
    report = dict(binary=str(binary), binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                  version=version, profile=args.profile, results=results,
                  passed=all(result["passed"] for result in results))
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"CLI branding: {sum(result['passed'] for result in results)}/{len(results)}")
    return int(not report["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
