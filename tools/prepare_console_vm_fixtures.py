#!/usr/bin/env python3
"""Prepare two fresh guest-VT fixtures bound to explicit frozen 0.1.1 inputs.

This creates initramfs fixtures only. It does not launch QEMU, upload binaries,
run console comparisons, or modify any frozen input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path
from pathlib import PurePosixPath

sys.dont_write_bytecode = True

MAX_UNIX_SOCKET_PATH_BYTES = 107  # Linux sockaddr_un.sun_path includes a trailing NUL.


def fixture_socket_paths(output: Path) -> list[Path]:
    work = output.absolute() / "nanospec-work"
    return [
        work / f"TEST-VT-VM-011-{kind}" / "fx" / socket_name
        for kind in ("HOST", "UBUNTU")
        for socket_name in ("qmp.sock", "control.sock")
    ]


def validate_fixture_socket_paths(output: Path) -> list[dict[str, object]]:
    records = []
    for path in fixture_socket_paths(output):
        encoded_length = len(os.fsencode(path))
        records.append({"path": str(path), "path_bytes": encoded_length,
                        "limit_bytes": MAX_UNIX_SOCKET_PATH_BYTES})
        if encoded_length > MAX_UNIX_SOCKET_PATH_BYTES:
            raise ValueError(
                f"VM Unix socket pathname is too long ({encoded_length} > "
                f"{MAX_UNIX_SOCKET_PATH_BYTES} bytes): {path}; choose a shorter --out"
            )
    return records


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def tree_digest(root: Path) -> dict[str, object]:
    h = hashlib.sha256()
    files = symlinks = 0
    for base, dirs, names in os.walk(root, followlinks=False):
        base_path = Path(base)
        keep = []
        for name in dirs:
            path = base_path / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                target = os.readlink(path)
                h.update(b"L\0" + rel.encode() + b"\0" + target.encode() + b"\0")
                symlinks += 1
            else:
                keep.append(name)
        dirs[:] = sorted(keep)
        for name in sorted(names):
            path = base_path / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                h.update(b"L\0" + rel.encode() + b"\0" + os.readlink(path).encode() + b"\0")
                symlinks += 1
            elif path.is_file():
                h.update(b"F\0" + rel.encode() + b"\0" + sha256_file(path).encode() + b"\0")
                files += 1
    return {"sha256_inventory": h.hexdigest(), "files": files, "symlinks": symlinks}


def verify_export_tree(archive: Path, root: Path, expected_archive_sha256: str) -> dict[str, object]:
    if sha256_file(archive) != expected_archive_sha256:
        raise ValueError("runtime archive SHA-256 differs from VM environment provenance")
    with tarfile.open(archive, "r:") as stream:
        members = {}
        for member in stream.getmembers():
            rel = PurePosixPath(member.name)
            if rel.is_absolute() or ".." in rel.parts:
                raise ValueError(f"unsafe path in runtime archive: {member.name}")
            name = rel.as_posix().removeprefix("./")
            if name in members:
                raise ValueError(f"duplicate path in runtime archive: {name}")
            if not (member.isfile() or member.issym() or member.islnk() or member.isdir()):
                raise ValueError(f"unsupported runtime archive member: {name}")
            members[name] = member

        hashes: dict[str, str] = {}

        def member_hash(name: str, visiting: set[str] | None = None) -> str:
            if name in hashes:
                return hashes[name]
            visiting = set() if visiting is None else visiting
            if name in visiting:
                raise ValueError(f"hard-link cycle in runtime archive: {name}")
            visiting.add(name)
            member = members[name]
            if member.islnk():
                target = PurePosixPath(member.linkname)
                if target.is_absolute() or ".." in target.parts:
                    raise ValueError(f"unsafe hard-link target in runtime archive: {name} -> {member.linkname}")
                digest = member_hash(target.as_posix().removeprefix("./"), visiting)
            else:
                content = stream.extractfile(member)
                if content is None:
                    raise ValueError(f"cannot read runtime archive member: {name}")
                h = hashlib.sha256()
                for block in iter(lambda: content.read(1024 * 1024), b""):
                    h.update(block)
                digest = h.hexdigest()
            hashes[name] = digest
            visiting.remove(name)
            return digest

        archive_files = {name: member_hash(name) for name, member in members.items()
                         if member.isfile() or member.islnk()}
        archive_links = {name: member.linkname for name, member in members.items() if member.issym()}

    root_files: dict[str, str] = {}
    root_links: dict[str, str] = {}
    for base, dirs, names in os.walk(root, followlinks=False):
        base_path = Path(base)
        keep = []
        for name in dirs:
            path = base_path / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                root_links[rel] = os.readlink(path)
            else:
                keep.append(name)
        dirs[:] = sorted(keep)
        for name in names:
            path = base_path / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                root_links[rel] = os.readlink(path)
            elif path.is_file():
                root_files[rel] = sha256_file(path)
    file_differences = sorted(name for name in set(archive_files) | set(root_files)
                              if archive_files.get(name) != root_files.get(name))
    link_differences = sorted(name for name in set(archive_links) | set(root_links)
                              if archive_links.get(name) != root_links.get(name))
    if file_differences or link_differences:
        raise ValueError(f"runtime tree/archive content mismatch: files={file_differences[:10]}, symlinks={link_differences[:10]}")
    return {
        "archive_sha256": expected_archive_sha256,
        "archive_regular_and_hardlink_files": len(archive_files),
        "archive_symlinks": len(archive_links),
        "verified_file_entries": len(root_files),
        "verified_symlink_entries": len(root_links),
        "file_differences": 0,
        "symlink_differences": 0,
    }


def git(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=path, text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--freeze-manifest", type=Path, required=True)
    parser.add_argument("--exported-root", type=Path, required=True, help="private Ubuntu runtime root for the guest initramfs")
    parser.add_argument("--runtime-archive", type=Path, required=True, help="tar export whose contents must match --exported-root")
    parser.add_argument("--vm-environment-manifest", type=Path, required=True, help="provenance JSON binding image, kernel and runtime export")
    parser.add_argument("--kernel", type=Path, required=True, help="pinned Linux kernel image")
    parser.add_argument("--reference", type=Path, required=True, help="pinned Ubuntu nano executable")
    parser.add_argument("--root-reference", type=Path, required=True, help="pinned host-root nano; recorded for input identity")
    parser.add_argument("--host-binary", type=Path, required=True)
    parser.add_argument("--ubuntu-binary", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="new fixture/provenance directory")
    args = parser.parse_args()

    source = args.source_dir.resolve(strict=True)
    manifest_path = args.freeze_manifest.resolve(strict=True)
    exported_root = args.exported_root.resolve(strict=True)
    runtime_archive = args.runtime_archive.resolve(strict=True)
    vm_environment_manifest = args.vm_environment_manifest.resolve(strict=True)
    kernel = args.kernel.resolve(strict=True)
    reference = args.reference.resolve(strict=True)
    root_reference = args.root_reference.resolve(strict=True)
    host_binary = args.host_binary.resolve(strict=True)
    ubuntu_binary = args.ubuntu_binary.resolve(strict=True)
    out = args.out.absolute()
    if out.resolve().is_relative_to(source):
        parser.error("--out must be outside the frozen source checkout")
    if out.exists():
        parser.error(f"preserve evidence: output already exists: {out}")
    try:
        socket_paths = validate_fixture_socket_paths(out)
    except ValueError as error:
        parser.error(str(error))

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    vm_environment = json.loads(vm_environment_manifest.read_text(encoding="utf-8"))
    source_commit = git(source, "rev-parse", "HEAD")
    if source_commit != manifest["source_commit"] or git(source, "status", "--porcelain", "--untracked-files=all"):
        parser.error("source checkout is not the clean frozen source from freeze manifest")
    source_tree = git(source, "rev-parse", "HEAD^{tree}")
    if source_tree != manifest["source_tree"]:
        parser.error("source tree differs from freeze manifest")
    sys.path.insert(0, str(source / "tools"))
    from check_wrap_undo import source_fingerprint, verification_fingerprint
    if source_fingerprint(source) != manifest["production_source_sha256"]:
        parser.error("source fingerprint differs from freeze manifest")
    if verification_fingerprint() != manifest["verification_sha256"]:
        parser.error("verification fingerprint differs from freeze manifest")
    input_hashes = {
        "host_binary": sha256_file(host_binary),
        "ubuntu_binary": sha256_file(ubuntu_binary),
        "reference": sha256_file(reference),
        "root_reference": sha256_file(root_reference),
        "kernel": sha256_file(kernel),
    }
    expected = {
        "host_binary": manifest["host_binary_sha256"],
        "ubuntu_binary": manifest["ubuntu_binary_sha256"],
        "reference": manifest["ubuntu_reference_sha256"],
        "root_reference": manifest["files"]["references/host-root/nano"],
    }
    if any(input_hashes[key] != value for key, value in expected.items()):
        parser.error(f"frozen input mismatch: actual={input_hashes}, expected={expected}")
    if vm_environment.get("runtime_image_id") != manifest["ubuntu_image"]["id"]:
        parser.error("VM runtime image ID differs from frozen Ubuntu build image")
    if vm_environment.get("kernel_sha256") != input_hashes["kernel"]:
        parser.error("VM kernel differs from the recorded VM environment")
    if vm_environment.get("guest_reference_sha256") != input_hashes["reference"]:
        parser.error("VM guest nano reference differs from the frozen Ubuntu reference")
    try:
        runtime_export = verify_export_tree(runtime_archive, exported_root,
                                            vm_environment["runtime_export_sha256"])
    except (OSError, ValueError, KeyError) as error:
        parser.error(f"VM runtime export validation failed: {error}")
    reference_version = subprocess.check_output([str(reference), "--version"], text=True)
    if "GNU nano 9.3" not in reference_version:
        parser.error("VM guest reference is not the pinned GNU nano 9.3 build")
    candidate_builds = {}
    for kind, candidate in (("host", host_binary), ("ubuntu", ubuntu_binary)):
        info = json.loads(subprocess.check_output([str(candidate)], env={**os.environ, "NARO_BUILD_INFO": "1"}, text=True))
        if info.get("revision") != source_commit or info.get("source_sha256") != manifest["production_source_sha256"] or info.get("features") != "":
            parser.error(f"{kind} candidate build info is not the default build for the frozen source")
        candidate_builds[kind] = info

    out.mkdir(parents=True, exist_ok=False)
    work = out / "nanospec-work"
    work.mkdir()
    fixture_inputs = out / "fixture-inputs"
    fixture_inputs.mkdir()
    kernel_copy = fixture_inputs / "vmlinuz"
    reference_copy = fixture_inputs / "nano"
    import shutil
    shutil.copy2(kernel, kernel_copy)
    shutil.copy2(reference, reference_copy)
    exported = tree_digest(exported_root)
    fixtures = {}
    helper = source / "tools/prepare_console_vm.py"
    if not helper.is_file():
        parser.error(f"missing fixture builder in frozen source: {helper}")
    for kind, binary in (("host", host_binary), ("ubuntu", ubuntu_binary)):
        case_id = f"TEST-VT-VM-011-{kind.upper()}"
        fx = work / case_id / "fx"
        fx.parent.mkdir()
        binary_copy = fixture_inputs / f"naro-{kind}"
        shutil.copy2(binary, binary_copy)
        env = os.environ.copy()
        env.update({"NANOSPEC_WORK": str(work), "PYTHONDONTWRITEBYTECODE": "1"})
        command = [sys.executable, str(helper), "--exported-root", str(exported_root), "--fixture", str(fx),
                   "--kernel", str(kernel_copy), "--reference", str(reference_copy), "--binary", str(binary_copy)]
        status = subprocess.run(command, cwd=source, env=env).returncode
        if status:
            raise SystemExit(status)
        input_record = json.loads((fx / "inputs.json").read_text(encoding="utf-8"))
        if input_record.get("vmlinuz") != input_hashes["kernel"]:
            raise SystemExit(f"{kind} fixture kernel hash mismatch")
        if input_record.get("nano") != input_hashes["reference"]:
            raise SystemExit(f"{kind} fixture nano hash mismatch")
        if input_record.get(f"naro-{kind}") != input_hashes[f"{kind}_binary"]:
            raise SystemExit(f"{kind} fixture candidate hash mismatch")
        fixtures[kind] = {
            "fixture": str(fx),
            "inputs": input_record,
            "command": command,
            "builder_status": status,
            "controller_hashes": {
                "init": sha256_file(fx / "init-root/init"),
                "upload_py": sha256_file(fx / "init-root/upload.py"),
            },
        }
    if git(source, "status", "--porcelain", "--untracked-files=all"):
        raise SystemExit("fixture preparation changed the frozen source checkout")
    report = {
        "schema": 1,
        "state": "prepared_not_booted",
        "unix_socket_paths": socket_paths,
        "source_commit": source_commit,
        "source_tree": manifest["source_tree"],
        "production_source_sha256": manifest["production_source_sha256"],
        "verification_sha256": manifest["verification_sha256"],
        "ubuntu_builder_image": manifest["ubuntu_image"],
        "input_hashes": input_hashes,
        "candidate_builds": candidate_builds,
        "reference_version": reference_version,
        "expected_hashes": expected,
        "kernel_path": str(kernel),
        "exported_root": {"path": str(exported_root), **exported},
        "runtime_archive": {"path": str(runtime_archive), **runtime_export},
        "vm_environment_manifest": {"path": str(vm_environment_manifest), "sha256": sha256_file(vm_environment_manifest)},
        "fixtures": fixtures,
        "next_step": "review identity-aware VM checker and fixture provenance before any QEMU launch",
    }
    (out / "fixture-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
