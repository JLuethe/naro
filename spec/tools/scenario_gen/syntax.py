"""Generate evidence/scenarios/syntax.json. Reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c"""
import json, os
SPEC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RC = ('syntax first "\\.x$"\ncolor red "a"\n'
      'syntax second "\\.x$"\ncolor green "a"\n'
      'syntax hdr\nheader "^#!hdr"\ncolor blue "a"\n'
      'syntax default\ncolor yellow "a"\n'
      'syntax ml "\\.ml$"\ncolor cyan start="<<" end=">>"\nicolor magenta "zz"\ncolor red "^q"\ncolor bold,white "q"\n'
      'syntax zero "\\.z0$"\ncolor red start="^" end="$"\n'
      'syntax path "/sub/"\ncolor blue "a"\n')
def sc(id, args, files, keys=()):
    steps = [{"settle": 400}, {"snapshot": "s0"}]
    for i, k in enumerate(keys):
        steps.append(k); steps.append({"snapshot": "s%d" % (i + 1)})
    steps += [{"keys": ["^X"]}, {"settle": 200}, {"text": "n"}, {"settle": 200}, {"keys": ["^X"]}, {"settle": 200}, {"text": "n"}, {"wait_exit": 3}]
    return {"id": id, "args": args, "files": dict({"home/.nanorc": {"text": RC}}, **files), "steps": steps}
S = [
 sc("TEST-SYN-001", ["t.x"], {"work/t.x": {"text": "a b\n"}}),
 sc("TEST-SYN-002", ["t.none"], {"work/t.none": {"text": "#!hdr a\n"}}),
 sc("TEST-SYN-003", ["plain"], {"work/plain": {"text": "a b\n"}}),
 sc("TEST-SYN-004", ["-Y", "first", "t.x"], {"work/t.x": {"text": "a b\n"}}),
 sc("TEST-SYN-005", ["-Y", "none", "t.x"], {"work/t.x": {"text": "a b\n"}}),
 sc("TEST-SYN-006", ["t.ml"], {"work/t.ml": {"text": "x << y\nmid ZZ\nend >> q\nq << a >> b << c >> d\n"}},
    keys=[{"keys": ["^Home"]}, {"text": ">>"}, {"keys": ["M-U"]}, {"keys": ["Down", "Down", "Down", "End"]}, {"text": " <<"}]),
 sc("TEST-SYN-007", ["t.z0"], {"work/t.z0": {"text": "ab\ncd\n"}}),
 sc("TEST-SYN-008", ["sub/f.txt"], {"work/sub/f.txt": {"text": "a\n"}}),
 sc("TEST-SYN-009", ["t.txt"], {"work/t.txt": {"text": "a\n"}}, keys=[{"keys": ["^O"]}, {"keys": ["^K"]}, {"text": "t.x\r"}, {"text": "y"}]),
 sc("TEST-SYN-010", ["t.x"], {"work/t.x": {"text": "a b\n"}}, keys=[{"keys": ["M-Y"]}, {"keys": ["M-Y"]}]),
]
json.dump(S, open(os.path.join(SPEC, "evidence", "scenarios", "syntax.json"), "w"), indent=1)
