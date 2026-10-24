#!/usr/bin/env python3
"""Differential terminal harness for the nano behavioral specification.

Reference revision: 6ed285c3ec7a1d228def4d4e7021c6ba269f620c

The harness drives an editor executable inside a private tmux server (tmux is
the terminal emulator), feeds it exact input bytes, and records:

  * screen snapshots as cell grids (text + attributes per cell), plus cursor
    position/visibility and terminal-mode flags reported by tmux;
  * the raw byte stream the editor wrote to the terminal (pipe-pane);
  * the exact input bytes sent, with timestamps;
  * the resulting fixture tree (bytes, sizes, modes, symlinks);
  * the exit status / terminating signal.

The same scenario file can be run against the pinned nano build and, later,
against the Rust executable (select it with --binary or a profile name), so
results are directly comparable.  See spec/16-test-plan.md for the scenario
format and the normalization rules.

Only the Python standard library is used.
"""

import argparse
import base64
import ctypes
import curses
import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import time

HOME = os.path.expanduser("~")
SPEC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILES = {
    "default": os.path.join(HOME, "src/nano-install/default/bin"),
    "tiny": os.path.join(HOME, "src/nano-install/tiny/bin"),
}
REFERENCE_COMMIT = "6ed285c3ec7a1d228def4d4e7021c6ba269f620c"
WORKROOT = os.environ.get("NANOSPEC_WORK", "/tmp/nanospec-work")
SOCKET = "nanospec-%d" % os.getpid()

# ---------------------------------------------------------------- widths

_libc = ctypes.CDLL("libc.so.6")
_libc.setlocale.restype = ctypes.c_char_p
_libc.setlocale(6, b"C.UTF-8")          # LC_ALL
_libc.wcwidth.argtypes = [ctypes.c_wchar]
_libc.wcwidth.restype = ctypes.c_int


def cwidth(ch):
    w = _libc.wcwidth(ch)
    return 1 if w < 0 else w

# ---------------------------------------------------------------- tmux


def tmux(*args, check=True, capture=True):
    cmd = ["tmux", "-L", SOCKET, "-f", "/dev/null"] + list(args)
    res = subprocess.run(cmd, stdout=subprocess.PIPE if capture else None,
                         stderr=subprocess.PIPE, check=False)
    if check and res.returncode != 0:
        raise RuntimeError("tmux %s failed: %s" % (args, res.stderr.decode()))
    return res.stdout.decode("utf-8", "surrogateescape") if capture else ""


PANE_FORMAT = ("#{cursor_x}\t#{cursor_y}\t#{cursor_flag}\t#{alternate_on}\t"
               "#{keypad_flag}\t#{keypad_cursor_flag}\t#{mouse_any_flag}\t"
               "#{mouse_sgr_flag}\t#{mouse_standard_flag}\t#{mouse_button_flag}\t"
               "#{mouse_all_flag}\t#{insert_flag}\t#{wrap_flag}\t#{pane_dead}\t"
               "#{pane_dead_status}\t#{pane_dead_signal}\t#{pane_width}\t"
               "#{pane_height}\t#{pane_pid}")
PANE_KEYS = ["cursor_x", "cursor_y", "cursor_visible", "alternate_screen",
             "keypad_mode", "cursor_keys_mode", "mouse_any", "mouse_sgr",
             "mouse_standard", "mouse_button", "mouse_all", "insert_mode",
             "autowrap", "dead", "exit_status", "exit_signal", "width",
             "height", "pid"]


def pane_state():
    vals = tmux("display", "-p", "-t", "t:0.0", PANE_FORMAT).rstrip("\n").split("\t")
    out = {}
    for k, v in zip(PANE_KEYS, vals):
        out[k] = int(v) if v.lstrip("-").isdigit() else (None if v == "" else v)
    # tmux 3.4 reports signal names; newer versions may report numbers.
    sig = out.get("exit_signal")
    if isinstance(sig, str):
        name = sig.upper()
        if not name.startswith("SIG"):
            name = "SIG" + name
        value = getattr(signal, name, None)
        if value is not None:
            out["exit_signal"] = int(value)
    return out

# ---------------------------------------------------------------- capture parsing

SGR_RE = re.compile(r"\x1b\[([0-9;:]*)m")


def parse_sgr(params, st):
    codes = [p for p in re.split(r"[;:]", params)] if params else ["0"]
    i = 0
    while i < len(codes):
        c = int(codes[i] or 0)
        if c == 0:
            st.clear()
        elif c == 1: st["bold"] = True
        elif c == 2: st["dim"] = True
        elif c == 3: st["italic"] = True
        elif c == 4: st["underline"] = True
        elif c == 5: st["blink"] = True
        elif c == 7: st["reverse"] = True
        elif c == 8: st["hidden"] = True
        elif c == 9: st["strike"] = True
        elif c == 22: st.pop("bold", None); st.pop("dim", None)
        elif c == 23: st.pop("italic", None)
        elif c == 24: st.pop("underline", None)
        elif c == 25: st.pop("blink", None)
        elif c == 27: st.pop("reverse", None)
        elif c == 28: st.pop("hidden", None)
        elif c == 29: st.pop("strike", None)
        elif 30 <= c <= 37: st["fg"] = c - 30
        elif c == 39: st.pop("fg", None)
        elif 40 <= c <= 47: st["bg"] = c - 40
        elif c == 49: st.pop("bg", None)
        elif 90 <= c <= 97: st["fg"] = c - 90 + 8
        elif 100 <= c <= 107: st["bg"] = c - 100 + 8
        elif c in (38, 48):
            key = "fg" if c == 38 else "bg"
            if i + 1 < len(codes) and codes[i + 1] == "5":
                st[key] = int(codes[i + 2]); i += 2
            elif i + 1 < len(codes) and codes[i + 1] == "2":
                st[key] = "#%02x%02x%02x" % tuple(int(x) for x in codes[i + 2:i + 5]); i += 4
        i += 1


def capture_grid(width, height):
    # Each row starts from default SGR state. Batch independent row captures
    # in one tmux client, so short-lived messages cannot change between the
    # two dozen process launches used by the original implementation.
    commands = []
    for row in range(height):
        if commands:
            commands.append(";")
        commands.extend(("capture-pane", "-p", "-e", "-N", "-t", "t:0.0",
                         "-S", str(row), "-E", str(row)))
    lines = tmux(*commands).split("\n")[:height]
    rows = []
    for line in lines:
        st = {}
        cells = []
        pos = 0
        while pos < len(line):
            m = SGR_RE.match(line, pos)
            if m:
                parse_sgr(m.group(1), st)
                pos = m.end()
                continue
            if line[pos] == "\x1b":          # other escapes: skip one sequence
                m2 = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b.").match(line, pos)
                pos = m2.end() if m2 else pos + 1
                continue
            ch = line[pos]
            pos += 1
            w = cwidth(ch)
            if w == 0 and cells:             # combining: attach to previous cell
                cells[-1]["ch"] += ch
                continue
            cells.append({"ch": ch, "attr": dict(st), "w": max(w, 1)})
            if w == 2:
                cells.append({"ch": "", "attr": dict(st), "w": 0})
        while len(cells) < width:
            cells.append({"ch": " ", "attr": {}, "w": 1})
        rows.append(cells[:width])
    while len(rows) < height:
        rows.append([{"ch": " ", "attr": {}, "w": 1} for _ in range(width)])
    return rows


def attr_key(a):
    return ",".join("%s=%s" % (k, a[k]) for k in sorted(a)) if a else ""


def grid_to_snapshot(rows, state):
    """Compact representation: per row the text and a list of attribute runs."""
    out_rows = []
    for cells in rows:
        text = "".join(c["ch"] for c in cells)
        runs = []
        col = 0
        for c in cells:
            k = attr_key(c["attr"])
            if runs and runs[-1]["attr"] == k and runs[-1]["end"] == col:
                runs[-1]["end"] = col + 1
            else:
                runs.append({"start": col, "end": col + 1, "attr": k})
            col += 1
        runs = [r for r in runs if r["attr"]]
        out_rows.append({"text": text, "attrs": runs})
    return {"rows": out_rows, "cursor": {"x": state["cursor_x"], "y": state["cursor_y"],
            "visible": bool(state["cursor_visible"])},
            "modes": {k: state[k] for k in ("alternate_screen", "keypad_mode",
                      "cursor_keys_mode", "mouse_any", "mouse_sgr",
                      "mouse_standard", "mouse_button", "mouse_all",
                      "insert_mode", "autowrap")}}

# ---------------------------------------------------------------- key names


class Keys:
    def __init__(self, term):
        # setupterm in a child process to keep our own terminal untouched
        code = ("import curses,sys,json;curses.setupterm(%r,1);"
                "caps=%r;print(json.dumps({c:(curses.tigetstr(c) or b'').decode('latin-1') for c in caps}))"
                % (term, ["kcuu1", "kcud1", "kcub1", "kcuf1", "khome", "kend",
                          "kpp", "knp", "kich1", "kdch1", "kbs", "kcbt", "kent"]
                   + ["kf%d" % i for i in range(1, 25)]
                   + ["kLFT", "kRIT", "kUP", "kDN", "kHOM", "kEND", "kPRV", "kNXT", "kDC", "kIC"]
                   + [c + n for c in ("kLFT", "kRIT", "kUP", "kDN", "kHOM", "kEND", "kPRV",
                                      "kNXT", "kDC", "kIC") for n in "34567"]))
        res = subprocess.run([sys.executable, "-c", code], stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, check=True)
        self.caps = {k: v.encode("latin-1") for k, v in json.loads(res.stdout).items()}
        self.names = {
            "Up": "kcuu1", "Down": "kcud1", "Left": "kcub1", "Right": "kcuf1",
            "Home": "khome", "End": "kend", "PgUp": "kpp", "PgDn": "knp",
            "Ins": "kich1", "Del": "kdch1", "Bsp": "kbs", "S-Tab": "kcbt", "Sh-Tab": "kcbt",
        }
        for i in range(1, 25):
            self.names["F%d" % i] = "kf%d" % i
        # Modified keys use the xterm-style extended capabilities:
        # 2 = Shift, 3 = Alt, 4 = Shift+Alt, 5 = Ctrl, 6 = Shift+Ctrl, 7 = Alt+Ctrl.
        base = {"Left": "kLFT", "Right": "kRIT", "Up": "kUP", "Down": "kDN", "Home": "kHOM",
                "End": "kEND", "PgUp": "kPRV", "PgDn": "kNXT", "Del": "kDC", "Ins": "kIC"}
        mods = {"Sh-": "", "M-": "3", "Sh-M-": "4", "^": "5", "Sh-^": "6", "M-^": "7"}
        for k, cap in base.items():
            for prefix, n in mods.items():
                self.names[prefix + k] = cap + n

    def encode(self, name):
        if name in self.names:
            seq = self.caps.get(self.names[name], b"")
            if not seq:
                raise ValueError("terminfo has no sequence for %s" % name)
            return seq
        fixed = {"Enter": b"\r", "Tab": b"\t", "Esc": b"\x1b", "Space": b" ",
                 "^Space": b"\x00", "^@": b"\x00", "DEL": b"\x7f", "^?": b"\x7f",
                 "^Bsp": b"\x08"}
        if name in fixed:
            return fixed[name]
        # Alt+letter sends ESC + lowercase letter; Shift+Alt+letter sends ESC + uppercase.
        if name.startswith("Sh-M-") and len(name) == 6 and name[5].isalpha():
            return b"\x1b" + name[5].upper().encode()
        if name.startswith("M-") and len(name) == 3:
            c = name[2]
            return b"\x1b" + (c.lower() if c.isalpha() else c).encode()
        if name.startswith("M-") and len(name) > 3:
            return b"\x1b" + self.encode(name[2:])
        if name.startswith("^") and len(name) == 2:
            c = name[1].upper()
            if c == "?":
                return b"\x7f"
            return bytes([ord(c) & 0x1F])
        if len(name) == 1:
            return name.encode()
        raise ValueError("unknown key name %r" % name)

# ---------------------------------------------------------------- fixtures


def make_fixture(root, spec):
    for d in spec.get("dirs", []):
        os.makedirs(os.path.join(root, d), exist_ok=True)
    for path, f in spec.get("files", {}).items():
        full = os.path.join(root, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        if "b64" in f:
            data = base64.b64decode(f["b64"])
        elif "hex" in f:
            data = bytes.fromhex(f["hex"])
        else:
            data = f.get("text", "").encode("utf-8")
        with open(full, "wb") as fh:
            fh.write(data)
        if "mode" in f:
            os.chmod(full, int(f["mode"], 8))
    for path, target in spec.get("symlinks", {}).items():
        full = os.path.join(root, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        os.symlink(target, full)
    for path, target in spec.get("hardlinks", {}).items():
        os.link(os.path.join(root, target), os.path.join(root, path))
    for path in spec.get("fifos", []):
        os.mkfifo(os.path.join(root, path))
    for path, mode in spec.get("chmod", {}).items():
        os.chmod(os.path.join(root, path), int(mode, 8))


def manifest(root, inline_limit=4096):
    out = {}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames.sort()
        for name in sorted(dirnames + filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            st = os.lstat(full)
            entry = {"ino": st.st_ino, "nlink": st.st_nlink, "mtime_ns": st.st_mtime_ns,
                     "uid": st.st_uid, "gid": st.st_gid,
                     "mode": oct(stat.S_IMODE(st.st_mode)), "type":
                     "link" if stat.S_ISLNK(st.st_mode) else "dir" if stat.S_ISDIR(st.st_mode)
                     else "file" if stat.S_ISREG(st.st_mode) else "other"}
            if entry["type"] == "link":
                entry["target"] = os.readlink(full)
            elif entry["type"] == "file":
                with open(full, "rb") as fh:
                    data = fh.read()
                entry["size"] = len(data)
                entry["sha256"] = hashlib.sha256(data).hexdigest()
                if len(data) <= inline_limit:
                    entry["b64"] = base64.b64encode(data).decode()
                    try:
                        entry["text"] = data.decode("utf-8")
                    except UnicodeDecodeError:
                        pass
            out[rel] = entry
    return out

# ---------------------------------------------------------------- running


class Run:
    def __init__(self, scenario, binary, outdir, keep=False):
        self.sc = scenario
        self.binary = binary
        self.outdir = outdir
        self.keep = keep
        self.inputs = []
        self.snapshots = {}
        self.notes = []
        self.step_checks = []

    def raw_size(self):
        try:
            return os.path.getsize(self.rawfile)
        except OSError:
            return 0

    def settle(self, quiet_ms=250, timeout=5.0):
        """Wait until neither the output stream nor the screen changed for quiet_ms."""
        deadline = time.time() + timeout
        last = (self.raw_size(), tmux("capture-pane", "-p", "-e", "-t", "t:0.0", check=False))
        stable_since = time.time()
        while time.time() < deadline:
            time.sleep(0.03)
            now = (self.raw_size(), tmux("capture-pane", "-p", "-e", "-t", "t:0.0", check=False))
            if now != last:
                last = now
                stable_since = time.time()
            elif (time.time() - stable_since) * 1000 >= quiet_ms:
                return True
        self.notes.append("settle timed out after %.1fs" % timeout)
        return False

    def wait_text(self, pattern, timeout=5.0, regex=False):
        deadline = time.time() + timeout
        while time.time() < deadline:
            screen = tmux("capture-pane", "-p", "-t", "t:0.0", check=False)
            if (re.search(pattern, screen) if regex else pattern in screen):
                return True
            if pane_state().get("dead") == 1:
                break
            time.sleep(0.03)
        self.notes.append("wait for %r timed out" % pattern)
        return False

    def wait_dead(self, timeout=5.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            st = pane_state()
            # The PTY may close before tmux has reaped its child. Do not
            # mistake a dead pane without wait status for completed evidence.
            if st.get("dead") == 1 and (st.get("exit_status") is not None or
                                        st.get("exit_signal") is not None):
                return True
            time.sleep(0.03)
        return False

    def send(self, data):
        self.inputs.append({"t": round(time.time() - self.t0, 3), "hex": data.hex()})
        tmux("send-keys", "-t", "t:0.0", "-H", *["%02x" % b for b in data])

    def execute(self):
        global SOCKET
        # A fresh socket also isolates server teardown between consecutive
        # scenarios on older tmux versions; kill-server is asynchronous.
        SOCKET = "nanospec-%d-%d" % (os.getpid(), time.monotonic_ns())
        sc = self.sc
        cols, rows = sc.get("cols", 80), sc.get("rows", 24)
        term = sc.get("term", "tmux-256color")
        keys = Keys(term)
        work = os.path.join(WORKROOT, sc["id"])
        shutil.rmtree(work, ignore_errors=True)
        root = os.path.join(work, "fx")
        os.makedirs(os.path.join(root, "home"), exist_ok=True)
        os.makedirs(os.path.join(root, "work"), exist_ok=True)
        make_fixture(root, sc)
        tempdir = os.path.join(work, "tmp")
        os.makedirs(tempdir, exist_ok=True)
        self.root = root
        self.captured = {}
        self.initial_manifest = manifest(root)
        os.makedirs(self.outdir, exist_ok=True)
        self.rawfile = os.path.join(self.outdir, "raw-output.bin")
        if os.path.exists(self.rawfile):
            os.remove(self.rawfile)
        gofile = os.path.join(work, "go")
        env = {"HOME": os.path.join(root, "home"), "TERM": term,
               "PATH": os.path.join(root, "bin") + ":/usr/bin:/bin",
               "LANG": sc.get("lang", "en_US.UTF-8"), "SHELL": "/bin/sh", "TZ": "UTC",
               "TMPDIR": tempdir}
        if "locpath" in sc:
            env["LOCPATH"] = sc["locpath"]
        for k, v in sc.get("env", {}).items():
            if v is None:
                env.pop(k, None)
            else:
                env[k] = v.replace("$FX", root)
        argv0 = sc.get("argv0", "nano")
        exe = os.path.join(self.binary, argv0) if os.path.isdir(self.binary) else self.binary
        with open(exe, "rb") as binary_file:
            binary_sha256 = hashlib.file_digest(binary_file, "sha256").hexdigest()
        args = [a.replace("$FX", root) for a in sc.get("args", [])]
        cwd = os.path.join(root, sc.get("cwd", "work"))
        envs = " ".join("%s=%s" % (k, shlex.quote(v)) for k, v in sorted(env.items()))
        redir = " 3<>/dev/tty" if sc.get("hold_tty") else ""
        if "stdin" in sc:
            stdin_path = os.path.join(work, "stdin.bin")
            with open(stdin_path, "wb") as fh:
                fh.write(sc["stdin"].encode() if isinstance(sc["stdin"], str) else bytes(sc["stdin"]))
            redir += " < " + shlex.quote(stdin_path)
        if sc.get("stdout_redirect"):
            redir += " > " + shlex.quote(os.path.join(work, "stdout.bin"))
        stderr_path = os.path.join(work, "stderr.bin")
        # exec -a applied to env changes env's argv[0], not the editor's.
        # A tiny exec launcher preserves the exact requested editor argv[0].
        launch = [sys.executable, "-c", "import os,sys,json; os.execve(sys.argv[1], sys.argv[3:], json.loads(sys.argv[2]))", exe, json.dumps(env), argv0] + args
        inner = ("umask %s; cd %s; while [ ! -e %s ]; do sleep 0.01; done; "
                 "exec 2>%s; exec env -i %s %s%s" % (
                     sc.get("umask", "022"), shlex.quote(cwd), shlex.quote(gofile),
                     shlex.quote(stderr_path), envs,
                     " ".join(shlex.quote(a) for a in launch), redir))
        tmux("new-session", "-d", "-s", "t", "-x", str(cols), "-y", str(rows),
             "sh", "-c", inner)
        tmux("set", "-g", "remain-on-exit", "on")
        tmux("set", "-g", "status", "off")
        tmux("set", "-g", "window-size", "manual")
        tmux("set", "-g", "history-limit", "0")
        tmux("resize-window", "-t", "t:0", "-x", str(cols), "-y", str(rows))
        tmux("pipe-pane", "-O", "-t", "t:0.0", "cat > " + shlex.quote(self.rawfile))
        time.sleep(0.1)
        self.t0 = time.time()
        open(gofile, "w").close()
        ok = True
        for index, step in enumerate(sc.get("steps", [])):
            passed = self.do_step(step, keys, cols, rows)
            ok &= passed
            self.step_checks.append({"step": index, "pass": bool(passed)})
        if not pane_state().get("dead"):
            self.settle(quiet_ms=150, timeout=2)
        st = pane_state()
        if not st.get("dead") and sc.get("finally_kill", True):
            self.notes.append("editor still running at end of scenario; sent SIGKILL")
            try:
                os.kill(st["pid"], signal.SIGKILL)
            except (ProcessLookupError, TypeError):
                pass
            self.wait_dead(2)
        st = pane_state()
        final = grid_to_snapshot(capture_grid(st["width"], st["height"]), st)
        tmux("kill-server", check=False)
        result = {
            "scenario": sc["id"], "reference_commit": REFERENCE_COMMIT,
            "binary": exe, "binary_sha256": binary_sha256, "argv": [argv0] + args, "env": env, "cwd": cwd,
            "inputs": self.inputs, "snapshots": self.snapshots,
            "after_exit_screen": final,
            "exit_status": st.get("exit_status"), "exit_signal": st.get("exit_signal"),
            "pane_state": st,
            "fixture": manifest(root), "initial_fixture": self.initial_manifest, "captured_files": self.captured, "notes": self.notes,
            "stderr": open(stderr_path, "rb").read().decode("utf-8", "replace")
                      if os.path.exists(stderr_path) else None,
        }
        if sc.get("stdout_redirect"):
            p = os.path.join(work, "stdout.bin")
            result["stdout"] = open(p, "rb").read().decode("utf-8", "replace") if os.path.exists(p) else None
        raw = open(self.rawfile, "rb").read() if os.path.exists(self.rawfile) else b""
        result["raw_output_bytes"] = len(raw)
        result["raw_output_sha256"] = hashlib.sha256(raw).hexdigest()
        result["bracketed_paste_set"] = raw.count(b"\x1b[?2004h")
        result["bracketed_paste_reset"] = raw.count(b"\x1b[?2004l")

        # tmux reports a dead pane's cursor as hidden regardless of what the
        # program sent, so derive the final terminal modes from the trace.
        def last_of(on, off):
            a, b = raw.rfind(on), raw.rfind(off)
            return None if a < 0 and b < 0 else a > b
        result["trace_final_modes"] = {
            "cursor_visible": last_of(b"\x1b[?25h", b"\x1b[?25l"),
            "alternate_screen": last_of(b"\x1b[?1049h", b"\x1b[?1049l"),
            "bracketed_paste": last_of(b"\x1b[?2004h", b"\x1b[?2004l"),
            "keypad_transmit": last_of(b"\x1b[?1h\x1b=", b"\x1b[?1l\x1b>"),
            "mouse_tracking": last_of(b"\x1b[?1000h", b"\x1b[?1000l"),
        }
        result["checks"] = self.check(result)
        result["step_checks"] = self.step_checks
        result["steps_ok"] = bool(ok) and not any("timed out" in n for n in self.notes)
        with open(os.path.join(self.outdir, "result.json"), "w") as fh:
            json.dump(result, fh, indent=1, ensure_ascii=False)
        if not self.keep:
            shutil.rmtree(work, ignore_errors=True)
        return result

    def inside(self, rel):
        """Resolve a fixture-relative path; refuse anything outside the fixture."""
        path = os.path.realpath(os.path.join(self.root, rel))
        if not path.startswith(os.path.realpath(self.root) + os.sep):
            raise ValueError("path escapes the fixture: %r" % rel)
        return path

    def do_step(self, step, keys, cols, rows):
        if "keys" in step:
            data = b"".join(keys.encode(k) for k in step["keys"])
            self.send(data)
        elif "text" in step:
            self.send(step["text"].encode("utf-8"))
        elif "hex" in step:
            self.send(bytes.fromhex(step["hex"]))
        elif "paste" in step:
            self.send(b"\x1b[200~" + step["paste"].encode("utf-8") + b"\x1b[201~")
        elif "wait" in step:
            w = step["wait"]
            return self.wait_text(w["text"], w.get("timeout", 5), w.get("regex", False))
        elif "settle" in step:
            return self.settle(quiet_ms=step["settle"], timeout=step.get("timeout", 5))
        elif "sleep" in step:
            time.sleep(step["sleep"] / 1000.0)
        elif "snapshot" in step:
            self.settle(quiet_ms=step.get("quiet", 250))
            st = pane_state()
            self.snapshots[step["snapshot"]] = grid_to_snapshot(
                capture_grid(st["width"], st["height"]), st)
        elif "resize" in step:
            c, r = step["resize"]
            tmux("resize-window", "-t", "t:0", "-x", str(c), "-y", str(r))
        elif "signal" in step:
            pid = pane_state()["pid"]
            os.kill(pid, getattr(signal, step["signal"]))
        elif "capture_file" in step:
            path = self.inside(step["capture_file"])
            try:
                data = open(path, "rb").read()
                self.captured.setdefault(step["capture_file"], []).append(base64.b64encode(data).decode())
            except OSError as exc:
                self.captured.setdefault(step["capture_file"], []).append("ERROR: %s" % exc)
        elif "write_file" in step:
            path = self.inside(step["write_file"])
            with open(path, "wb") as fh:
                fh.write(step.get("content", "").encode())
            if "mtime_offset" in step:
                st = os.stat(path)
                os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + int(step["mtime_offset"] * 1e9)))
        elif "wait_exit" in step:
            passed = self.wait_dead(step["wait_exit"])
            if not passed:
                self.notes.append("wait_exit timed out after %ss" % step["wait_exit"])
            return passed
        else:
            raise ValueError("unknown step %r" % step)
        return True

    def check(self, result):
        exp = self.sc.get("expect", {})
        checks = []

        def add(name, ok, detail=""):
            checks.append({"check": name, "pass": bool(ok), "detail": detail})
        if "exit_status" in exp:
            add("exit_status", result["exit_status"] == exp["exit_status"],
                "got %r" % result["exit_status"])
        for path, want in exp.get("files", {}).items():
            got = result["fixture"].get(path)
            if want is None:
                add("absent:" + path, got is None, "present" if got else "")
                continue
            if got is None:
                add("file:" + path, False, "missing")
                continue
            for k in ("text", "b64", "mode", "size", "type", "target"):
                if k in want:
                    add("file:%s:%s" % (path, k), got.get(k) == want[k],
                        "got %r" % got.get(k))
            if "hex" in want:
                add("file:%s:hex" % path, base64.b64decode(got.get("b64", "")).hex() == want["hex"],
                    "got %s" % base64.b64decode(got.get("b64", "")).hex())
        for item in exp.get("screen", []):
            snap = result["snapshots"].get(item["snapshot"]) if item["snapshot"] != "after_exit" \
                else result["after_exit_screen"]
            if snap is None:
                add("screen", False, "no snapshot %s" % item["snapshot"])
                continue
            if "row" in item:
                text = snap["rows"][item["row"]]["text"]
                if "equals" in item:
                    add("row%d==" % item["row"], text.rstrip() == item["equals"].rstrip(), repr(text))
                if "contains" in item:
                    add("row%d~" % item["row"], item["contains"] in text, repr(text))
            if "cursor" in item:
                cur = snap["cursor"]
                ok = all(cur.get(k) == v for k, v in item["cursor"].items())
                add("cursor", ok, repr(cur))
            if "anywhere" in item:
                add("anywhere", any(item["anywhere"] in r["text"] for r in snap["rows"]), "")
            if "attr_at" in item:
                r, c, want = item["attr_at"]
                runs = snap["rows"][r]["attrs"]
                got = next((x["attr"] for x in runs if x["start"] <= c < x["end"]), "")
                add("attr@%d,%d" % (r, c), got == want, "got %r" % got)
        if "stderr_contains" in exp:
            add("stderr", exp["stderr_contains"] in (result["stderr"] or ""), repr(result["stderr"]))
        if "stdout_contains" in exp:
            add("stdout", exp["stdout_contains"] in (result.get("stdout") or ""), repr(result.get("stdout")))
        return checks


def render(snap):
    lines = []
    for i, r in enumerate(snap["rows"]):
        lines.append("%2d|%s|" % (i, r["text"]))
    c = snap["cursor"]
    lines.append("cursor=(%d,%d) visible=%s modes=%s" % (c["x"], c["y"], c["visible"],
                 json.dumps(snap["modes"], sort_keys=True)))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("scenarios", nargs="+", help="scenario JSON files")
    ap.add_argument("--profile", default=None, help="default|tiny (overrides scenario)")
    ap.add_argument("--binary", default=None, help="explicit executable or bin dir")
    ap.add_argument("--out", default=os.path.join(SPEC, "evidence", "runs"))
    ap.add_argument("--keep", action="store_true", help="keep fixture work dir")
    ap.add_argument("--show", action="store_true", help="print snapshots")
    args = ap.parse_args()
    summary = []
    for path in args.scenarios:
        with open(path) as fh:
            doc = json.load(fh)
        for sc in (doc if isinstance(doc, list) else [doc]):
            binary = args.binary or PROFILES[args.profile or sc.get("profile", "default")]
            outdir = os.path.join(args.out, sc["id"])
            try:
                res = Run(sc, binary, outdir, keep=args.keep).execute()
            except Exception as exc:
                tmux("kill-server", check=False)
                print("%-28s ERROR    %s" % (sc["id"], exc))
                summary.append((sc["id"], "ERROR", 0, 0))
                continue
            npass = sum(c["pass"] for c in res["checks"])
            status = ("PASS" if npass == len(res["checks"]) else "FAIL") if res["checks"] else "RECORDED"
            if not res["steps_ok"]:
                status = "FAIL"
            summary.append((sc["id"], status, npass, len(res["checks"])))
            print("%-28s %-8s %d/%d checks  exit=%s sig=%s %s" % (
                sc["id"], status, npass, len(res["checks"]), res["exit_status"],
                res["exit_signal"], "; ".join(res["notes"])))
            if args.show or status == "FAIL":
                for name, snap in res["snapshots"].items():
                    print("--- snapshot", name)
                    print(render(snap))
                print("--- final pane state", res["pane_state"])
                print("--- after exit / final pane")
                print(render(res["after_exit_screen"]))
                if res.get("stderr"):
                    print("--- stderr", res["stderr"])
                for c in res["checks"]:
                    if not c["pass"]:
                        print("   FAILED", c)
    with open(os.path.join(args.out, "last-summary.json"), "w") as fh:
        json.dump(summary, fh, indent=1)
    return int(any(s[1] in ("FAIL", "ERROR") for s in summary))


if __name__ == "__main__":
    sys.exit(main())
