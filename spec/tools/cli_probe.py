#!/usr/bin/env python3
"""Non-interactive command-line probes (no terminal needed).

Reference revision: 6ed285c3ec7a1d228def4d4e7021c6ba269f620c

Runs the reference executables with argument vectors that make nano exit
before it needs a terminal (help, version, invalid options and values, rc
problems, non-tty stdout), and records argv, stdout, stderr and exit status
in spec/evidence/cli/cli-probes.json.  stdin/stdout are NOT terminals here,
which is itself one of the probed conditions.
"""

import json
import os
import subprocess
import tempfile

HOME = os.path.expanduser("~")
BIN = {"default": HOME + "/src/nano-install/default/bin",
       "tiny": HOME + "/src/nano-install/tiny/bin"}
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "evidence", "cli", "cli-probes.json")

PROBES = [
    # id, profile, argv0, args, env-extra, stdin
    ("CLI-P-001", "default", "nano", ["--help"], {}),
    ("CLI-P-002", "default", "nano", ["-h"], {}),
    ("CLI-P-003", "default", "rnano", ["--help"], {}),
    ("CLI-P-004", "default", "nano", ["-R", "-h"], {}),
    ("CLI-P-005", "default", "nano", ["--version"], {}),
    ("CLI-P-006", "default", "nano", ["-V"], {}),
    ("CLI-P-007", "tiny", "nano", ["--help"], {}),
    ("CLI-P-008", "tiny", "nano", ["--version"], {}),
    ("CLI-P-009", "default", "nano", ["--bogus"], {}),
    ("CLI-P-010", "default", "nano", ["-q", "-%", "-y", "-k", "-^"], {}),
    ("CLI-P-011", "default", "nano", ["-T", "0"], {}),
    ("CLI-P-012", "default", "nano", ["-T", "abc"], {}),
    ("CLI-P-013", "default", "nano", ["--tabsize=4x"], {}),
    ("CLI-P-014", "default", "nano", ["-J", "-3"], {}),
    ("CLI-P-015", "default", "nano", ["-r", "x"], {}),
    ("CLI-P-016", "default", "nano", ["-T"], {}),
    ("CLI-P-017", "default", "nano", ["--tabsize"], {}),
    ("CLI-P-018", "default", "nano", ["--s"], {}),
    ("CLI-P-019", "default", "nano", ["--solo", "--vers"], {}),
    ("CLI-P-020", "default", "nano", ["-V", "--bogus"], {}),
    ("CLI-P-021", "default", "nano", ["--bogus", "-V"], {}),
    ("CLI-P-022", "default", "nano", ["-h", "-V"], {}),
    ("CLI-P-023", "default", "nano", ["file"], {}),            # stdout not a tty
    ("CLI-P-024", "default", "nano", ["-z", "-I"], {}),
    ("CLI-P-025", "default", "nano", ["-I", "-z"], {}),
    ("CLI-P-026", "default", "nano", ["-f", "/nonexistent/rc", "-z"], {}),
    ("CLI-P-027", "default", "nano", ["-f", "$RC1", "-z"], {}),
    ("CLI-P-028", "default", "nano", ["-f", "$RCBAD", "-z"], {}),
    ("CLI-P-029", "tiny", "nano", ["-A"], {}),
    ("CLI-P-030", "tiny", "nano", ["--smarthome"], {}),
    ("CLI-P-031", "tiny", "nano", ["-I"], {}),
    ("CLI-P-032", "tiny", "nano", ["-1", "-h"], {}),
    ("CLI-P-033", "default", "nano", ["-Q", "(", "-z"], {}),
    ("CLI-P-034", "default", "nano", ["--fill=-0", "--tabsize=+3", "--guidestripe= 7", "-V"], {}),
    ("CLI-P-035", "default", "nano", ["--rcfile"], {}),
    ("CLI-P-036", "default", "nano", ["-f", "$RCDIR", "-z"], {}),
    ("CLI-P-037", "default", "nano", ["-f", "$RCVITAL", "-z"], {}),
    ("CLI-P-038", "default", "nano", ["--he"], {}),
    ("CLI-P-039", "default", "nano", ["--syntax"], {}),
    ("CLI-P-040", "default", "nano", ["-Y"], {}),
    ("CLI-P-041", "default", "nano", ["--zero", "--version"], {}),
    ("CLI-P-042", "default", "xnano", ["--help"], {}),
    ("CLI-P-043", "default", "nano", ["-z"], {"HOME": "$HOMEWITHRC"}),
    ("CLI-P-044", "default", "nano", ["--listsyntaxes", "-f", "$RCSYN"], {}),
    ("CLI-P-045", "default", "nano", ["-f", "$RCSYN", "--listsyntaxes"], {}),
    ("CLI-P-046", "default", "nano", ["-o", "/nonexistent-dir", "file"], {}),
]


def main():
    tmp = tempfile.mkdtemp(prefix="nano-cli-")
    os.makedirs(tmp + "/home/.config/nano", exist_ok=True)
    os.makedirs(tmp + "/rcdir", exist_ok=True)
    rcs = {
        "$RC1": ("rc1", 'syntax "foo" "\\.foo$"\ncolor red "x"\nsyntax bar "\\.bar$"\ncolor blue "y"\n'),
        "$RCBAD": ("rcbad", 'set bogusoption\nset tabsize 0\nunset tabsize\nbind ^Q nosuchfunc main\nbind ^[ cut main\nsyntax "x"\nfoo\nset fill\n'),
        "$RCVITAL": ("rcvital", "unbind ^X main\nunbind F2 main\n"),
        "$RCSYN": ("rcsyn", 'include "%s/src/nano-install/default/share/nano/*.nanorc"\n' % HOME),
    }
    paths = {"$RCDIR": tmp + "/rcdir", "$HOMEWITHRC": tmp + "/home"}
    for key, (name, text) in rcs.items():
        p = os.path.join(tmp, name)
        open(p, "w").write(text)
        paths[key] = p
    open(tmp + "/home/.nanorc", "w").write('syntax one "\\.one$"\ncolor red "a"\n')
    results = []
    for pid, prof, argv0, args, envx in PROBES:
        args = [paths.get(a, a) for a in args]
        env = {"HOME": tmp + "/emptyhome", "PATH": "/usr/bin:/bin", "LANG": "en_US.UTF-8",
               "TERM": "tmux-256color"}
        for k, v in envx.items():
            env[k] = paths.get(v, v)
        exe = os.path.join(BIN[prof], "nano")
        try:
            res = subprocess.run([argv0] + args, executable=exe, env=env, cwd=tmp,
                                 stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, timeout=10)
            out, err, rc = res.stdout.decode("utf-8", "replace"), res.stderr.decode("utf-8", "replace"), res.returncode
        except subprocess.TimeoutExpired:
            out, err, rc = "", "", "TIMEOUT"
        results.append({"id": pid, "profile": prof, "argv0": argv0,
                        "args": [a.replace(tmp, "$TMP") for a in args],
                        "stdin": "/dev/null (not a tty)", "stdout_is_tty": False,
                        "exit_status": rc, "stdout": out.replace(tmp, "$TMP"),
                        "stderr": err.replace(tmp, "$TMP")})
        print("%-10s %-7s %-6s %-48s rc=%s out=%d err=%r" % (pid, prof, argv0, " ".join(args)[:48].replace(tmp, "$TMP"), rc, len(out), err[:70].replace(tmp, "$TMP")))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"reference_commit": "6ed285c3ec7a1d228def4d4e7021c6ba269f620c",
               "rc_files": {k: v[1] for k, v in rcs.items()}, "results": results},
              open(OUT, "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
