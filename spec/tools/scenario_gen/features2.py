"""Generate evidence/scenarios/features2.json. Reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c"""
import json, os
SPEC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
K = lambda *k: {"keys": list(k)}; T = lambda t: {"text": t}
def sc(id, args, files, keys=(), end=None, **kw):
    steps = [{"settle": 400}, {"snapshot": "s0"}]
    for i, k in enumerate(keys):
        steps.append(k); steps.append({"snapshot": "s%02d" % (i + 1), "quiet": 250})
    steps += end if end is not None else [{"keys": ["^X"]}, {"settle": 300}, {"text": "n"}, {"wait_exit": 3}]
    d = {"id": id, "args": args, "files": files, "steps": steps}; d.update(kw); return d
HIST = "old1\nold2\n\nrep1\n\ncmd1\n"
S = [
 sc("TEST-FEAT-013", ["-I", "-H", "f.txt"], {"work/f.txt": {"text": "abc\nold2\n"}, "home/.local/share/nano/search_history": {"text": HIST}},
    [K("^W"), K("Up"), K("Up"), K("Enter"), K("^W"), T("new\x00z"), K("Enter"), K("^\\"), T("abc\r"), T("XY\r"), T("a")],
    end=[{"keys": ["^X"]}, {"settle": 300}, {"text": "n"}, {"wait_exit": 3}]),
 sc("TEST-FEAT-014", ["-I", "-P", "f.txt"], {"work/f.txt": {"text": "".join("l%d\n" % i for i in range(1, 60))}},
    [K("M-G"), T("40,2\r"), K("M-Ins"), K("Down"), K("M-Ins")], end=[{"keys": ["^X"]}, {"wait_exit": 3}]),
 sc("TEST-FEAT-015", ["-I", "-P", "f.txt"], {"work/f.txt": {"text": "".join("l%d\n" % i for i in range(1, 60))},
    "home/.local/share/nano/filepos_history": {"text": "/elsewhere 3 1\n41 42 $FX/work/f.txt 40 2\n"}}, [], end=[{"keys": ["^X"]}, {"wait_exit": 3}]),
 sc("TEST-FEAT-016", ["-I", "f.txt"], {"work/f.txt": {"text": "x\n"}}, [K("^T"), K("^Z"), {"sleep": 500}, {"signal": "SIGCONT"}, {"settle": 500}]),
 sc("TEST-FEAT-017", ["-I", "f.txt"], {"work/f.txt": {"text": "a\nb\n"}},
    [K("^T"), K("M-F"), T("echo hi\r"), K("^T"), K("M-\\"), T("rev\r"), K("M-,"), K("^T"), T("|rev\r"), K("^T"), K("^V")]),
 sc("TEST-FEAT-018", ["-I", "f.txt"], {"work/f.txt": {"text": "x\n"}}, [K("^G"), K("PgDn"), K("End"), K("^W"), T("Justify\r"), K("M-W"), K("Home"), K("^X")]),
 sc("TEST-FEAT-019", ["-I", "-l", "f.txt"], {"work/f.txt": {"text": "abc\ndef\n"}}, [K("Right"), K("^C"), K("^End"), K("^C")]),
 sc("TEST-FEAT-020", ["-I", "f.txt"], {"work/f.txt": {"text": "x\n"}}, [T("y"), K("^X"), K("Enter")],
    end=[{"snapshot": "noname"}, {"keys": ["^C"]}, {"settle": 200}, {"keys": ["^X"]}, {"settle": 200}, {"text": "n"}, {"wait_exit": 3}]),
]
json.dump(S, open(os.path.join(SPEC, "evidence", "scenarios", "features2.json"), "w"), indent=1)
