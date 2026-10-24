"""Generate evidence/scenarios/signals.json. Reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c
All targets are fixture files; signals go to the nano process under test only."""
import json, os
SPEC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
K = lambda *k: {"keys": list(k)}; T = lambda t: {"text": t}
def sc(id, args, files, steps):
    return {"id": id, "args": args, "files": files, "steps": [{"settle": 400}, {"snapshot": "s0"}] + steps}
S = [
 sc("TEST-SIG-001", ["-I", "f.txt"], {"work/f.txt": {"text": "x\n"}}, [T("abc"), {"settle": 200}, {"signal": "SIGTERM"}, {"wait_exit": 3}]),
 sc("TEST-SIG-002", ["-I"], {}, [T("nameless"), {"settle": 200}, {"signal": "SIGHUP"}, {"wait_exit": 3}]),
 sc("TEST-SIG-003", ["-I", "f.txt"], {"work/f.txt": {"text": "x\n"}, "work/f.txt.save": {"text": "old save\n"}},
    [T("abc"), {"settle": 200}, {"signal": "SIGTERM"}, {"wait_exit": 3}]),
 sc("TEST-SIG-004", ["-I", "-R", "f.txt"], {"work/f.txt": {"text": "x\n"}}, [T("abc"), {"settle": 200}, {"signal": "SIGTERM"}, {"wait_exit": 3}]),
 sc("TEST-SIG-005", ["-I", "f.txt"], {"work/f.txt": {"text": "x\n"}},
    [{"signal": "SIGINT"}, {"settle": 300}, {"signal": "SIGQUIT"}, {"settle": 300}, {"snapshot": "alive"}, K("^X"), {"wait_exit": 3}]),
 sc("TEST-SIG-006", ["-I", "a.txt", "b.txt"], {"work/a.txt": {"text": "a\n"}, "work/b.txt": {"text": "b\n"}},
    [T("1"), K("M-."), T("2"), {"settle": 200}, {"signal": "SIGTERM"}, {"wait_exit": 3}]),
 sc("TEST-SIG-007", ["-I", "f.txt"], {"work/f.txt": {"text": "x\n"}},
    [K("^Z"), {"snapshot": "s1"}, K("^T"), K("^Z"), {"settle": 600}, {"snapshot": "stopped"}, {"signal": "SIGCONT"}, {"settle": 600},
     {"snapshot": "resumed"}, K("^X"), {"wait_exit": 3}]),
 sc("TEST-SIG-008", ["-I", "-G", "f.txt"], {"work/f.txt": {"text": "x\n"}},
    [T("abc"), {"settle": 300}, {"capture_file": "work/.f.txt.swp"}, {"signal": "SIGTERM"}, {"wait_exit": 3}]),
 sc("TEST-SIG-009", ["-I", "f.txt"], {"work/f.txt": {"text": "x\n"}},
    [{"signal": "SIGTERM"}, {"wait_exit": 3}]),
 sc("TEST-SIG-010", ["-I", "-v", "f.txt"], {"work/f.txt": {"text": "x\n"}}, [{"signal": "SIGTERM"}, {"wait_exit": 3}]),
]
json.dump(S, open(os.path.join(SPEC, "evidence", "scenarios", "signals.json"), "w"), indent=1)
