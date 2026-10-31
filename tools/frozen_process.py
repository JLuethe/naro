"""Run bounded frozen qualification commands with narrowly owned cleanup."""
from __future__ import annotations

import os
import signal
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path


def make_private_tmux_tmpdir() -> tuple[Path, str]:
    """Make a short socket root under /tmp, independent of potentially long --out."""
    path = Path(tempfile.mkdtemp(prefix="nt-", dir="/tmp"))
    path.chmod(0o700)
    token = uuid.uuid4().hex
    (path / ".naro-owned").write_text(token + "\n", encoding="utf-8")
    return path, token


def remove_private_tmux_tmpdir(path: Path, token: str) -> None:
    """Remove only the exact marked short socket directory created above."""
    path = path.resolve(strict=True)
    if path.parent != Path("/tmp") or not path.name.startswith("nt-") or path.is_symlink():
        raise RuntimeError(f"refusing to remove non-owned tmux directory: {path}")
    marker = path / ".naro-owned"
    if marker.read_text(encoding="utf-8").strip() != token:
        raise RuntimeError(f"tmux ownership token mismatch: {path}")
    socket_dir = path / f"tmux-{os.getuid()}"
    if socket_dir.exists() and any(child.is_socket() for child in socket_dir.iterdir()):
        raise RuntimeError(f"owned tmux sockets remain: {socket_dir}")
    shutil.rmtree(path)


def _signal_group(pgid: int, sig: int) -> bool:
    try:
        os.killpg(pgid, sig)
        return True
    except ProcessLookupError:
        return False


def _stop_process(process: subprocess.Popen[bytes], grace_seconds: float = 5.0) -> dict[str, object]:
    term_sent = _signal_group(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=grace_seconds)
        return {"term_sent": term_sent, "kill_sent": False, "reaped": True}
    except subprocess.TimeoutExpired:
        kill_sent = _signal_group(process.pid, signal.SIGKILL)
        process.wait()
        return {"term_sent": term_sent, "kill_sent": kill_sent, "reaped": True}


def cleanup_owned_tmux(tmux_tmpdir: Path, timeout: float = 5.0) -> list[dict[str, object]]:
    """Stop only tmux servers whose sockets are inside this run's private dir."""
    tmux_tmpdir = tmux_tmpdir.resolve(strict=True)
    socket_dir = tmux_tmpdir / f"tmux-{os.getuid()}"
    if not socket_dir.exists():
        return []
    if socket_dir.is_symlink() or not socket_dir.is_dir():
        raise RuntimeError(f"refusing unsafe tmux ownership directory: {socket_dir}")
    results = []
    for socket in sorted(socket_dir.iterdir()):
        if not socket.is_socket():
            results.append({"socket": str(socket), "status": "not-a-socket-preserved"})
            continue
        command = ["tmux", "-S", str(socket), "kill-server"]
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                start_new_session=True)
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            status = proc.returncode
            stop = {"term_sent": False, "kill_sent": False, "reaped": True}
        except subprocess.TimeoutExpired:
            stop = _stop_process(proc)
            stdout, stderr = proc.communicate()
            status = proc.returncode
        stale_socket_removed = False
        if socket.is_socket():
            deadline = time.monotonic() + min(timeout, 1.0)
            while socket.is_socket():
                probe = subprocess.run(["tmux", "-S", str(socket), "list-sessions"],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
                if probe.returncode != 0 and b"no server running on " in probe.stderr:
                    socket.unlink()
                    stale_socket_removed = True
                    break
                if time.monotonic() >= deadline:
                    break
                time.sleep(0.05)
        results.append({
            "socket": str(socket),
            "command": command,
            "status": status,
            "stdout": stdout.decode("utf-8", "replace"),
            "stderr": stderr.decode("utf-8", "replace"),
            "client_cleanup": stop,
            "socket_removed": not socket.exists(),
            "stale_socket_removed": stale_socket_removed,
        })
    return results


def run_owned_process(command: list[str], *, cwd: Path, env: dict[str, str],
                      log_path: Path, timeout: float,
                      tmux_tmpdir: Path | None = None) -> dict[str, object]:
    """Execute one command in its own session/process group and preserve logs."""
    process = None
    timed_out = interrupted = False
    stop = None
    try:
        with log_path.open("wb") as log:
            process = subprocess.Popen(command, cwd=cwd, env=env, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            try:
                status = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                stop = _stop_process(process)
                status = 124
    except KeyboardInterrupt:
        interrupted = True
        if process is not None and process.poll() is None:
            stop = _stop_process(process)
        status = 130
    cleanup = cleanup_owned_tmux(tmux_tmpdir) if tmux_tmpdir is not None else []
    return {
        "status": status,
        "timed_out": timed_out,
        "interrupted": interrupted,
        "process_group_cleanup": stop,
        "owned_tmux_cleanup": cleanup,
    }
