"""Generate evidence/scenarios/prompts.json. Reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c"""
import json, os
SPEC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
K = lambda *k: {"keys": list(k)}; T = lambda t: {"text": t}; H = lambda h: {"hex": h}
def click(col, row):   # X10 mouse press+release, 0-based col/row
    return H("1b5b4d20%02x%02x1b5b4d23%02x%02x" % (33 + col, 33 + row, 33 + col, 33 + row))
def sc(id, args, files, keys, end=None):
    steps = [{"settle": 400}, {"snapshot": "s0"}]
    for i, k in enumerate(keys):
        steps.append(k); steps.append({"snapshot": "s%02d" % (i + 1), "quiet": 250})
    steps += end if end is not None else [{"keys": ["^C"]}, {"settle": 200}, {"keys": ["^X"]}, {"settle": 300}, {"text": "n"}, {"wait_exit": 3}]
    return {"id": id, "args": args, "files": files, "steps": steps}
D = {"work/f.txt": {"text": "x\n"}, "work/alpha.txt": {"text": "a\n"}, "work/alps/inner": {"text": "i\n"},
     "work/beta1": {"text": ""}, "work/beta2": {"text": ""}, "home/hfile": {"text": ""}}
MANY = dict(D, **{"work/file-number-%02d.txt" % i: {"text": ""} for i in range(100)})
S = [
 sc("TEST-PROMPT-001", ["-I", "f.txt"], D, [K("^R"), T("al"), K("Tab"), K("Tab"), T("s"), K("Tab"), K("Tab")]),
 sc("TEST-PROMPT-002", ["-I", "f.txt"], D, [K("^R"), T("bet"), K("Tab"), K("Tab"), K("Bsp"), K("Bsp"), K("Tab")]),
 sc("TEST-PROMPT-003", ["-I", "f.txt"], MANY, [K("^R"), T("file"), K("Tab")]),
 sc("TEST-PROMPT-004", ["-I", "f.txt"], D, [K("^R"), T("alp"), K("Left"), K("Tab"), T("~/h"), K("End"), K("Tab"), K("^K"), T("zzz"), K("Tab")]),
 sc("TEST-PROMPT-005", ["-I", "-H", "f.txt"], dict(D, **{"home/.local/share/nano/search_history": {"text": "one\ntwo\nthree\n\n\n"}}),
    [K("^W"), T("par"), K("Up"), K("Up"), K("Down"), K("Down"), K("^K"), K("^K"), T("t"), K("Tab"), K("Tab"), K("Tab"), K("Up")]),
 sc("TEST-PROMPT-006", ["-I", "f.txt"], D, [K("^W"), T("0123456789" * 10), K("Home"), K("End"), K("Left") ]),
 sc("TEST-PROMPT-007", ["-I", "f.txt"], D, [K("^W"), T("hello world"), K("M-6"), K("End"), K("^K"), K("^U"), K("^U"), K("Home"), K("^Right"), K("^K")]),
 sc("TEST-PROMPT-008", ["-I", "f.txt"], D, [K("^W"), {"paste": "a\tb\rc"}, K("M-V"), K("^A"), T("z")]),
 sc("TEST-PROMPT-009", ["-I", "-R", "f.txt"], D, [T("q"), K("^O"), T("zz"), K("Bsp"), K("^K"), K("Home"), K("Del")],
    end=[{"keys": ["Enter"]}, {"settle": 300}, {"snapshot": "wrote"}, {"keys": ["^X"]}, {"wait_exit": 3}]),
 sc("TEST-PROMPT-010", ["-I", "-m", "f.txt"], D, [K("^W"), T("abcdef"), click(9, 21), T("X"), click(3, 21), T("Y")]),
 sc("TEST-PROMPT-011", ["-I", "f.txt"], D, [K("^W"), T("abc"), K("^G")], end=[{"keys": ["^X"]}, {"settle": 300}, {"snapshot": "back"}, {"keys": ["^C"]}, {"settle": 200}, {"keys": ["^X"]}, {"wait_exit": 3}]),
 sc("TEST-PROMPT-012", ["-I", "f.txt"], D, [K("^W"), T("abc"), {"resize": [50, 15]}, {"settle": 300}]),
]
json.dump(S, open(os.path.join(SPEC, "evidence", "scenarios", "prompts.json"), "w"), indent=1)
