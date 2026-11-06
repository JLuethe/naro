#!/usr/bin/env python3
"""Run backup ownership tests in rootless, isolated Podman userspaces."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile

REPO = Path(__file__).resolve().parents[2]
IMAGE = "localhost/naro-followup:ubuntu24"
ROOT_TEST = "files::backup_tests::backup_preserves_foreign_owner_in_private_root_namespace"
DENIED_TEST = "files::backup_tests::backup_warns_when_foreign_ownership_is_denied"


def run(*args, show_output=True):
    print("+", " ".join(map(str, args)), flush=True)
    result = subprocess.run(args, cwd=REPO, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    if show_output:
        print(result.stdout, end="", flush=True)
    result.check_returncode()
    return result.stdout


def container(uid, environment, *command, show_output=True):
    args = [
        "podman", "run", "--rm", "--network=none", "--user", str(uid),
        "--security-opt", "label=disable",
        "-v", f"{REPO}:/work:ro", "-v", f"{REPO / 'target'}:/work/target:rw",
        "-w", "/work",
    ]
    for key, value in environment.items():
        args.extend(["-e", f"{key}={value}"])
    return run(*args, IMAGE, *command, show_output=show_output)


def test_container(uid, environment, binary, name):
    listing = container(uid, environment, binary, "--list", show_output=False)
    if f"{name}: test" not in listing.splitlines():
        raise RuntimeError(f"test entrypoint missing: {name}")
    output = container(uid, environment, binary, "--ignored", "--exact", name,
                       "--nocapture")
    if not re.search(r"test result: ok\. 1 passed; 0 failed; 0 ignored;", output):
        raise RuntimeError(f"test did not execute exactly once: {name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path, help="compiled Rust test binary under target/")
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    try:
        inside = binary.relative_to(REPO / "target")
    except ValueError:
        parser.error("test binary must be inside this repository's target directory")
    if os.geteuid() == 0:
        parser.error("run as an ordinary host user, not host root")
    info = subprocess.run(
        ["podman", "info", "--format", "{{.Host.Security.Rootless}}"],
        check=True, capture_output=True, text=True,
    )
    if info.stdout.strip() != "true":
        parser.error("rootless Podman is required")
    run("podman", "image", "exists", IMAGE)
    container_binary = "/work/target/" + inside.as_posix()
    test_container(0, {"NARO_BACKUP_ROOT_NAMESPACE": "1"}, container_binary, ROOT_TEST)

    fixture_root = REPO / "target" / "issue-9-backup-fixtures"
    fixture_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="denied-", dir=fixture_root) as directory:
        fixture = Path(directory)
        fixture.chmod(0o777)
        source = fixture / "source"
        source.write_bytes(b"foreign owned bytes\n")
        relative_source = source.relative_to(REPO).as_posix()
        container(0, {}, "chown", "1234:1235", relative_source)
        container(0, {}, "chmod", "0644", relative_source)
        test_container(1000, {"NARO_BACKUP_DENIED_SOURCE": relative_source},
                       container_binary, DENIED_TEST)


if __name__ == "__main__":
    main()
