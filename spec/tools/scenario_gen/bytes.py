"""Generate evidence/scenarios/bytes.json. Reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c"""
import json, os, base64
SPEC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOC = os.path.expanduser("~/src/nano-locales")
K = lambda *k: {"keys": list(k)}; T = lambda t: {"text": t}; H = lambda h: {"hex": h}
B = lambda b: {"b64": base64.b64encode(b).decode()}
def sc(id, args, files, keys, lang=None, end=None):
    steps = [{"settle": 400}, {"snapshot": "s0"}]
    for i, k in enumerate(keys):
        steps.append(k); steps.append({"snapshot": "s%02d" % (i + 1), "quiet": 200})
    steps += end if end is not None else [{"keys": ["^X"]}, {"settle": 300}, {"text": "n"}, {"wait_exit": 3}]
    d = {"id": id, "args": args, "files": files, "steps": steps}
    if lang: d["lang"] = lang; d["locpath"] = LOC
    return d
MIX = b"a\xe9b\xc0\x80c\xed\xa0\x80d\xf0\x9f\x98\x80e\xcc\x81\xe6\x97\xa5\xc2\x85f\n"
steps = []
for _ in range(14): steps += [K("Right"), K("^C")]
S = [
 sc("TEST-BYTE-001", ["-I", "m.txt"], {"work/m.txt": B(MIX)}, [K("^C")] + steps),
 sc("TEST-BYTE-002", ["-I", "m.txt"], {"work/m.txt": B(b"xe\xcc\x81y\n")},
    [K("Right", "Right"), K("^C"), K("Bsp"), K("^C"), K("M-U"), K("Home", "Right"), K("Del"), K("^C")]),
 sc("TEST-BYTE-003", ["-I", "n.txt"], {"work/n.txt": B(b"a\x00b\n\x00\n")},
    [K("Right"), K("^C"), K("End"), T("Z"), K("^O"), K("Enter")]),
 sc("TEST-BYTE-004", ["-I", "l.txt"], {"work/l.txt": B(b"\xe4bc d\xe4f g\n\x85\x9f\xa0x\n")},
    [K("^Right"), T("|"), K("^Right"), T("#"), K("^W"), H("c4"), K("Enter"), T("@"), K("^Home"), K("^Del"), K("^O"), K("Enter")], lang="de_DE.ISO-8859-1"),
 sc("TEST-BYTE-005", ["-I", "u.txt"], {"work/u.txt": B(b"\xc3\xa9x\n")}, [K("Right"), K("^C"), K("Right"), K("^C")], lang="C"),
 sc("TEST-BYTE-006", ["-I", "-T", "4", "t.txt"], {"work/t.txt": B(b"\tab\tc\xe6\x97\xa5\td\n")},
    [K("End"), K("^C"), K("Home", "Down", "Up"), K("Right", "Right"), K("Down"), K("Up")]),
]
for s in S:
    if s.get("lang") == "C": s.pop("locpath")
json.dump(S, open(os.path.join(SPEC, "evidence", "scenarios", "bytes.json"), "w"), indent=1)
