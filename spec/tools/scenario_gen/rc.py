"""Generate evidence/scenarios/rc.json (nanorc parsing probes).
Reference revision: 6ed285c3ec7a1d228def4d4e7021c6ba269f620c"""
import json, os
SPEC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def rcs(id, files, args=(), env=None, keys=()):
    steps = [{"settle": 400}, {"snapshot": "s0"}]
    for i, k in enumerate(keys):
        steps.append(k); steps.append({"snapshot": "s%d" % (i + 1)})
    steps += [{"keys": ["^X"]}, {"settle": 300}, {"text": "n"}, {"wait_exit": 3}]
    d = {"id": id, "args": list(args), "files": files, "steps": steps}
    if env: d["env"] = env
    return d

BAD = ("# comment\n   \n\tset    autoindent  extra words\nset whitespace \"ab\"\n"
       "set whitespace \"\u00bb\u00b7\"\nset matchbrackets \"(<\"\nset matchbrackets \"( )\"\n"
       "unset tabsize\nset tabsize\nset\nset nonexistent\nset fill abc\nset guidestripe 0\n"
       "set punct \"a b\"\nset speller \"  aspell -c\"\nset titlecolor bold,lightred,blue\n"
       "set numbercolor pink\nset keycolor brightyellow\nset functioncolor bold\n"
       "set statuscolor ,green\nset errorcolor bold,italic,#f00,#0f0\nset spotlightcolor lightpink\n"
       "set selectedcolor #12\nbind\r\nset quotestr \"unterminated\nsyntax\nsyntax \"\"\n"
       "syntax none \"x\"\nsyntax \"q\ncolor red \"x\"\nfoo bar\ninclude \"/nonexistent/*.nanorc\"\n"
       "include \"/nonexistent-home/missing.nanorc\"\nextendsyntax nosuch color red \"x\"\n"
       "set whitespacedisplay\r\n")
S = [
 rcs("TEST-RC-001", {"home/.nanorc": {"text": "set tabsize 4\n"}, "home/.config/nano/nanorc": {"text": "set tabsize 3\n"},
     "xdg/nano/nanorc": {"text": "set tabsize 2\n"}, "work/t.txt": {"text": "\tx\n"}}, ["t.txt"], env={"XDG_CONFIG_HOME": "$FX/xdg"}),
 rcs("TEST-RC-002", {"home/.config/nano/nanorc": {"text": "set tabsize 3\n"}, "xdg/nano/nanorc": {"text": "set tabsize 2\n"},
     "work/t.txt": {"text": "\tx\n"}}, ["t.txt"], env={"XDG_CONFIG_HOME": "$FX/xdg"}),
 rcs("TEST-RC-003", {"home/.config/nano/nanorc": {"text": "set tabsize 3\n"}, "work/t.txt": {"text": "\tx\n"}}, ["t.txt"]),
 rcs("TEST-RC-004", {"home/.nanorc": {"text": BAD}}),
 rcs("TEST-RC-005", {"home/.nanorc": {"text": "syntax foo \"\\.foo$\"\ncolor red \"aa\"\nset autoindent\ncolor blue \"bb\"\n"},
     "work/x.foo": {"text": "aa bb\n"}}, ["x.foo"]),
 rcs("TEST-RC-006", {"home/.nanorc": {"text": "include \"~/syn/*.nanorc\"\nextendsyntax foo color green \"bb\"\nextendsyntax foo header \"^#!foo\"\n"},
     "home/syn/foo.nanorc": {"text": "syntax foo \"\\.foo$\"\ncolor red \"aa\"\nset autoindent\n"},
     "work/x.foo": {"text": "aa bb\n"}, "work/hdr": {"text": "#!foo aa bb\n"}}, ["x.foo", "hdr"], keys=[{"keys": ["M-."]}]),
 rcs("TEST-RC-007", {"home/.nanorc": {"text": "set autoindent\n"}, "work/t.txt": {"text": "  x\n"}}, ["t.txt"],
     keys=[{"keys": ["End", "Enter"]}, {"text": "y"}]),
 rcs("TEST-RC-008", {"home/.nanorc": {"text": "set tabsize 4\nset fill 20\n"}, "work/t.txt": {"text": "\tx\n"}}, ["-T", "6", "t.txt"]),
 rcs("TEST-RC-009", {"home/.nanorc": {"text": "set autoindent\nset nonewlines\n"}, "work/t.txt": {"text": "  x"}}, ["-i", "t.txt"],
     keys=[{"keys": ["End"]}, {"text": "q"}, {"keys": ["^O"]}, {"keys": ["Enter"]}]),
 rcs("TEST-RC-010", {"home/.nanorc": {"text": "unset nowrap\nset fill 15\n"}, "work/t.txt": {"text": "\n"}}, ["t.txt"],
     keys=[{"text": "aaa bbb ccc ddd eee"}]),
 rcs("TEST-RC-011", {"home/.nanorc": {"text": "set operatingdir \"/\"\n"}}, ["-R"]),
]
json.dump(S, open(os.path.join(SPEC, "evidence", "scenarios", "rc.json"), "w"), indent=1)
print(len(S))
