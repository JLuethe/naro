#!/usr/bin/env python3
"""Run Ubuntu qualification against immutable, explicit frozen inputs.

The default candidate is mounted read-only and copied into a private workspace;
only test-hooks and credits variants are built, into distinct output directories.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

sys.dont_write_bytecode = True
from frozen_process import run_owned_process

HISTORICAL_SYNTAX_PATH = "/home/john/src/nano-install/default/share/nano"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=path, text=True).strip()


def tree_inventory(root: Path) -> tuple[set[str], dict[str, str]]:
    files: set[str] = set()
    symlinks: dict[str, str] = {}
    for base, dirs, names in os.walk(root, followlinks=False):
        base_path = Path(base)
        keep = []
        for name in dirs:
            path = base_path / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                symlinks[rel] = os.readlink(path)
            else:
                keep.append(name)
        dirs[:] = keep
        for name in names:
            path = base_path / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                symlinks[rel] = os.readlink(path)
            elif path.is_file():
                files.add(rel)
    return files, symlinks


def syntax_install_record(source: Path, manifest: dict) -> dict:
    """Bind historical absolute includes to this freeze's read-only syntax assets."""
    syntax = source / "assets/syntax"
    if syntax.is_symlink() or not syntax.is_dir():
        raise ValueError("frozen syntax assets must be a real directory")
    files, symlinks = tree_inventory(syntax)
    prefix = "source/assets/syntax/"
    expected = {name.removeprefix(prefix): digest for name, digest in manifest["files"].items()
                if name.startswith(prefix)}
    actual = {name: sha256(syntax / name) for name in files}
    if not expected or symlinks or actual != expected:
        raise ValueError("syntax installation differs from frozen asset inventory")
    return {"source_path": str(syntax), "container_path": HISTORICAL_SYNTAX_PATH,
            "read_only": True, "file_hashes": actual}


def cleanup_container(container_name: str, cidfile: Path, owner_token: str) -> tuple[str | None, list[dict[str, object]]]:
    cid = cidfile.read_text(encoding="utf-8").strip() if cidfile.is_file() else None
    if not cid:
        by_name = subprocess.run(
            ["podman", "inspect", "--format", '{{.Id}}|{{ index .Config.Labels "org.naro.qualification-owner" }}', container_name],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30,
        )
        if by_name.returncode == 0:
            observed = by_name.stdout.strip().split("|", 1)
            if len(observed) == 2 and observed[1] == owner_token:
                cid = observed[0]
            else:
                return None, [{"cleanup_refused": True, "reason": "unique name did not carry this run's ownership label",
                               "inspect": by_name.stdout.strip(), "error": by_name.stderr.strip()}]
        else:
            return None, [{"cleanup_refused": True, "reason": "no cidfile and owned container name not found",
                           "inspect_status": by_name.returncode, "error": by_name.stderr.strip()}]
    if not re.fullmatch(r"[0-9a-f]{64}", cid):
        return cid, [{"cleanup_refused": True, "reason": "cidfile did not contain a full container ID"}]
    inspected = subprocess.run(
        ["podman", "inspect", "--format", '{{.Id}}|{{ index .Config.Labels "org.naro.qualification-owner" }}', cid],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30,
    )
    expected_inspection = f"{cid}|{owner_token}"
    if inspected.returncode != 0 or inspected.stdout.strip() != expected_inspection:
        return cid, [{"container_id": cid, "inspect_status": inspected.returncode,
                      "inspect": inspected.stdout.strip(), "inspect_error": inspected.stderr.strip(),
                      "cleanup_refused": True}]
    stop = subprocess.run(["podman", "stop", "--time", "5", cid],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20)
    remove = subprocess.run(["podman", "rm", "--force", cid],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20)
    return cid, [{"container_id": cid, "inspect_status": inspected.returncode,
                  "inspect": inspected.stdout.strip(),
                  "stop_status": stop.returncode, "stop_output": stop.stdout.strip(),
                  "stop_error": stop.stderr.strip(),
                  "remove_status": remove.returncode, "remove_output": remove.stdout.strip(),
                  "remove_error": remove.stderr.strip()}]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True, help="clean detached frozen source checkout")
    parser.add_argument("--binary", type=Path, required=True, help="frozen default-feature Ubuntu candidate")
    parser.add_argument("--reference", type=Path, required=True, help="frozen Ubuntu GNU nano executable")
    parser.add_argument("--root-reference", type=Path, required=True, help="pinned host-root GNU nano executable; recorded, not run in Ubuntu")
    parser.add_argument("--reference-install", type=Path, required=True, help="frozen Ubuntu nano installation tree with catalogs")
    parser.add_argument("--freeze-manifest", type=Path, required=True, help="freeze.json binding all inputs")
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory; must not exist")
    parser.add_argument("--timeout", type=int, default=43200)
    args = parser.parse_args()

    source = args.source_dir.resolve(strict=True)
    binary = args.binary.resolve(strict=True)
    reference = args.reference.resolve(strict=True)
    root_reference = args.root_reference.resolve(strict=True)
    reference_install = args.reference_install.resolve(strict=True)
    manifest_path = args.freeze_manifest.resolve(strict=True)
    out = args.out.absolute()
    if out.resolve().is_relative_to(source):
        parser.error("--out must be outside the frozen source checkout")
    if out.exists():
        parser.error(f"preserve evidence: output already exists: {out}")
    if args.timeout < 60:
        parser.error("timeout must be at least 60 seconds")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_commit = manifest["source_commit"]
    if git(source, "rev-parse", "HEAD") != source_commit:
        parser.error("source HEAD does not match freeze manifest")
    if git(source, "status", "--porcelain", "--untracked-files=all"):
        parser.error("source checkout is not clean")
    source_tree = git(source, "rev-parse", "HEAD^{tree}")
    if source_tree != manifest["source_tree"]:
        parser.error("source tree does not match freeze manifest")

    expected_hashes = {
        "candidate": manifest["ubuntu_binary_sha256"],
        "reference": manifest["ubuntu_reference_sha256"],
        "root_reference": manifest["files"]["references/host-root/nano"],
    }
    actual_hashes = {
        "candidate": sha256(binary),
        "reference": sha256(reference),
        "root_reference": sha256(root_reference),
    }
    if actual_hashes != expected_hashes:
        parser.error(f"binary hash mismatch: actual={actual_hashes}, expected={expected_hashes}")
    if sha256(reference_install / "bin/nano") != actual_hashes["reference"]:
        parser.error("reference-install/bin/nano differs from explicit --reference")
    install_files, install_symlinks = tree_inventory(reference_install)
    expected_install_files = {
        path.removeprefix("ubuntu/reference-install/"): digest
        for path, digest in manifest["files"].items()
        if path.startswith("ubuntu/reference-install/")
    }
    expected_install_symlinks = {
        path.removeprefix("ubuntu/reference-install/"): target
        for path, target in manifest["symlinks"].items()
        if path.startswith("ubuntu/reference-install/")
    }
    actual_install_hashes = {path: sha256(reference_install / path) for path in install_files}
    if actual_install_hashes != expected_install_files or install_symlinks != expected_install_symlinks:
        parser.error("Ubuntu nano installation tree differs from freeze manifest")
    syntax_install = syntax_install_record(source, manifest)

    image = manifest["ubuntu_image"]
    image_text = subprocess.check_output([
        "podman", "image", "inspect", image["id"],
        "--format", "{{.Id}}|{{.Digest}}|{{.Os}}|{{.Architecture}}",
    ], text=True).strip()
    expected_image = "|".join((image["id"], image["digest"], image["os"], image["architecture"]))
    if image_text != expected_image:
        parser.error(f"offline Ubuntu image identity mismatch: observed={image_text!r}")
    toolchain = manifest["toolchain"]
    toolchain_path = Path(toolchain["path"]).resolve(strict=True)
    for name, expected_sha in toolchain["executables"].items():
        if sha256(toolchain_path / "bin" / name) != expected_sha:
            parser.error(f"frozen toolchain hash mismatch: {name}")

    out.mkdir(parents=True, exist_ok=False)
    inner = out / "ubuntu-inner.sh"
    inner_source = source / "tools/closure_ubuntu_inner.sh"
    if not inner_source.is_file():
        parser.error(f"missing private-workspace Ubuntu entrypoint: {inner_source}")
    inner.write_bytes(inner_source.read_bytes())
    owner_token = uuid.uuid4().hex
    container_name = "naro-qualify-" + owner_token[:16]
    cidfile = out / "container.cid"
    command = [
        "podman", "run", "--network", "none", "--pull=never",
        "--name", container_name, "--cidfile", str(cidfile),
        "--label", f"org.naro.qualification-owner={owner_token}",
        "--userns=keep-id", "--user", "0:0",
        "-v", f"{source}:/project:ro",
        "-v", f"{binary}:/frozen/naro:ro",
        "-v", f"{reference_install}:/reference-built:ro",
        "-v", f"{syntax_install['source_path']}:{syntax_install['container_path']}:ro",
        "-v", f"{root_reference}:/root-reference.bin:ro",
        "-v", f"{toolchain_path}:/opt/rust:ro",
        "-v", f"{inner}:/qualification.sh:ro",
        "-v", f"{out}:/out:rw",
        "-e", f"NARO_SOURCE_COMMIT={source_commit}",
        "-e", f"NARO_SOURCE_FINGERPRINT={manifest['production_source_sha256']}",
        "-e", f"NARO_NANO_REFERENCE_COMMIT={manifest['nano_reference_commit']}",
        "-e", f"NARO_EXPECTED_VERSION={manifest['package_version']}",
        image["id"],
        "bash", "-c",
        "mkdir -p /work /opt/nano-locales /out && chown 1000:1000 /work /opt/nano-locales /out && exec setpriv --reuid=1000 --regid=1000 --clear-groups bash /qualification.sh",
    ]
    record = {
        "schema": 1,
        "state": "running",
        "source_commit": source_commit,
        "source_tree": source_tree,
        "production_source_sha256": manifest["production_source_sha256"],
        "candidate_build_sha256": expected_hashes["candidate"],
        "reference_sha256": expected_hashes["reference"],
        "root_reference_sha256": expected_hashes["root_reference"],
        "container_name": container_name,
        "container_owner_token": owner_token,
        "container_cidfile": str(cidfile),
        "reference_install_file_count": len(install_files),
        "reference_install_symlink_count": len(install_symlinks),
        "syntax_install": syntax_install,
        "ubuntu_image": image,
        "toolchain": toolchain,
        "command": command,
        "started_epoch": time.time(),
    }
    (out / "launch.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    started = time.time()
    run_outcome = {"status": 125, "error": None}
    status = 125
    cid = None
    cleanup = []
    try:
        run_outcome = run_owned_process(command, cwd=source, env=os.environ.copy(),
                                        log_path=out / "launcher.log", timeout=args.timeout)
        status = int(run_outcome["status"])
    except KeyboardInterrupt:
        status = 130
        run_outcome = {"status": status, "interrupted": True}
    except Exception as error:
        status = 125
        run_outcome = {"status": status, "error": f"{type(error).__name__}: {error}"}
    finally:
        try:
            cid, cleanup = cleanup_container(container_name, cidfile, owner_token)
        except Exception as error:
            cleanup = [{"cleanup_error": f"{type(error).__name__}: {error}", "cleanup_refused": True}]
        if any(item.get("cleanup_refused") or item.get("remove_status", 0) != 0 for item in cleanup):
            if status == 0:
                status = 125
        tmux_cleanup_status = out / "tmux-cleanup.status"
        if status == 0 and (not tmux_cleanup_status.is_file() or tmux_cleanup_status.read_text().strip() != "0"):
            status = 125
    record["finished_epoch"] = time.time()
    record["elapsed_seconds"] = round(time.time() - started, 2)
    record["status"] = status
    record["run_process"] = run_outcome
    record["container_id"] = cid
    record["container_cleanup"] = cleanup
    record["tmux_cleanup_status"] = (out / "tmux-cleanup.status").read_text().strip() if (out / "tmux-cleanup.status").is_file() else None
    record["state"] = "complete" if status == 0 else "failed"
    (out / "launch.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
