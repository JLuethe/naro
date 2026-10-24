"""Generate evidence/scenarios/i18n.json. Reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c"""
import json, os
SPEC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOC = os.path.expanduser("~/src/nano-locales")
K = lambda *k: {"keys": list(k)}; T = lambda t: {"text": t}
def sc(id, lang, args, files, keys, env=None, end=None):
    steps = [{"settle": 400}, {"snapshot": "s0"}]
    for i, k in enumerate(keys):
        steps.append(k); steps.append({"snapshot": "s%02d" % (i + 1), "quiet": 250})
    steps += end if end is not None else [{"keys": ["^X"]}, {"settle": 300}, {"text": "n"}, {"wait_exit": 3}]
    d = {"id": id, "lang": lang, "locpath": LOC, "args": args, "files": files, "steps": steps}
    if env: d["env"] = env
    if lang.startswith("en_US.UTF"): del d["locpath"]   # system locale; private LOCPATH lacks it
    return d
F = {"work/f.txt": {"text": "eins\nzwei\n"}}
S = [
 sc("TEST-I18N-001", "de_DE.UTF-8", ["-I", "f.txt"], F, [T("x"), K("^X"), T("q"), K("^C"), K("^W"), T("zzz\r"), K("M-D"), K("^C")]),
 sc("TEST-I18N-002", "de_DE.UTF-8", ["-I", "f.txt"], F, [T("x"), K("^X"), T("j"), K("Enter")], end=[{"wait_exit": 3}]),
 sc("TEST-I18N-003", "de_DE.ISO-8859-1", ["-I", "l1.txt"], {"work/l1.txt": {"b64": "w6RiYwrkYmMK"}}, [K("^C"), K("End"), K("^C")]),
 sc("TEST-I18N-004", "ja_JP.UTF-8", ["-I", "f.txt"], F, [K("^C"), K("^W"), K("^C")]),
 sc("TEST-I18N-005", "en_US.UTF-8", ["-I", "f.txt"], F, [K("^W"), K("^C")], env={"LANGUAGE": "fr:de"}),
 sc("TEST-I18N-006", "C", ["-I", "f.txt"], F, [K("^W"), K("^C")], env={"LANGUAGE": "de"}),
 sc("TEST-I18N-007", "de_DE.UTF-8", ["-I", "f.txt"], F, [K("^G")], end=[{"keys": ["^X"]}, {"settle": 300}, {"keys": ["^X"]}, {"wait_exit": 3}]),
 sc("TEST-I18N-008", "de_DE.UTF-8", ["-I", "missing.txt"], {}, [K("^R"), T("nonexist\r")]),
]
json.dump(S, open(os.path.join(SPEC, "evidence", "scenarios", "i18n.json"), "w"), indent=1)
