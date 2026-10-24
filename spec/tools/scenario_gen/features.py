"""Generate evidence/scenarios/features.json: justify, spell, linter, formatter, macros.
Reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c
External programs are STUBS in the fixture's bin/ directory (front of PATH)."""
import json, os
SPEC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
X = lambda text: {"text": text, "mode": "0755"}
HUNSPELL = X("#!/bin/sh\n# stub: report fixed misspellings, ignore stdin content\ncat > /dev/null\nprintf 'teh\\nwrold\\nteh\\n'\n")
ALTSPELL = X("#!/bin/sh\n# stub alternative speller: argv[1] is the temp file; uppercase it\necho \"$@\" > \"$HOME/spell-args\"\nfor last; do :; done; sed -i 's/teh/the/g' \"$last\"\nexit 0\n")
LINTER = X("#!/bin/sh\necho \"$@\" > \"$HOME/lint-args\"\nfor last; do :; done; echo \"$last:2:3: second line problem\"\necho \"$last:1: first line problem\"\necho \"garbage line\"\necho \"other.txt:1:1: elsewhere\"\nexit 1\n")
FORMATTER = X("#!/bin/sh\necho \"$@\" > \"$HOME/fmt-args\"\nfor last; do :; done; tr a-z A-Z < \"$last\" > \"$last.tmp\" && cat \"$last.tmp\" > \"$last\"\n")
RC = 'syntax txt "\\.txt$"\ncolor red "zzz"\nlinter mylint --flag\nformatter myfmt -x\n'
def sc(id, args, files, keys=(), end=None):
    steps = [{"settle": 400}, {"snapshot": "s0"}]
    for i, k in enumerate(keys):
        steps.append(k); steps.append({"snapshot": "s%02d" % (i + 1), "quiet": 250})
    steps += end if end is not None else [{"keys": ["^O"]}, {"settle": 200}, {"keys": ["Enter"]}, {"settle": 300}, {"keys": ["^X"]}, {"settle": 300}, {"text": "n"}, {"wait_exit": 3}]
    return {"id": id, "args": args, "files": files, "steps": steps}
K = lambda *k: {"keys": list(k)}; T = lambda t: {"text": t}
PARA = "  Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor.\n  Second line of\nthe paragraph.\n\n> quoted text that is rather long and needs to be wrapped around nicely here\n> more quoted\n\nlast\n"
S = [
 sc("TEST-FEAT-001", ["-I", "-r", "30", "f.txt"], {"work/f.txt": {"text": PARA}}, [K("^J"), K("^J"), K("^J"), K("M-U")]),
 sc("TEST-FEAT-002", ["-I", "-r", "30", "f.txt"], {"work/f.txt": {"text": PARA}}, [K("M-J")]),
 sc("TEST-FEAT-003", ["-I", "-r", "30", "-M", "f.txt"], {"work/f.txt": {"text": "one.  two.   three four five six seven eight nine ten\n"}}, [K("^J")]),
 sc("TEST-FEAT-004", ["-I", "f.txt"], {"work/f.txt": {"text": "teh cat sat on teh wrold\n"}, "bin/hunspell": HUNSPELL},
    [K("^T"), K("^T"), T("the\r"), T("a"), K("^C")]),
 sc("TEST-FEAT-005", ["-I", "-s", "altspell --opt", "f.txt"], {"work/f.txt": {"text": "teh x\n"}, "bin/altspell": ALTSPELL},
    [K("^T"), K("^T"), K("M-U"), K("M-E")]),
 sc("TEST-FEAT-006", ["f.txt"], {"work/f.txt": {"text": "line one\nline two\n"}, "home/.nanorc": {"text": RC}, "bin/mylint": LINTER},
    [K("^T"), K("^Y"), K("PgDn"), K("PgDn"), K("PgUp"), K("PgUp"), K("^C")]),
 sc("TEST-FEAT-007", ["f.txt"], {"work/f.txt": {"text": "abc\n"}, "home/.nanorc": {"text": RC}, "bin/myfmt": FORMATTER},
    [K("^T"), K("^O"), K("M-U")]),
 sc("TEST-FEAT-008", ["-I", "f.txt"], {"work/f.txt": {"text": "a\nb\nc\n"}},
    [K("M-:"), T("<"), K("End"), T(">"), K("Down", "Home"), K("M-:"), K("M-;"), K("M-;"), K("M-;")]),
 sc("TEST-FEAT-009", ["-I", "f.txt"], {"work/f.txt": {"text": "a\n"}}, [K("M-;"), K("M-:"), K("M-:"), K("M-:"), K("M-;"), K("M-:")]),
 sc("TEST-FEAT-010", ["-I", "f.txt"], {"work/f.txt": {"text": "x\n"}}, [K("^T"), K("^T")],
    end=[{"snapshot": "spellfail"}, {"keys": ["^X"]}, {"settle": 200}, {"text": "n"}, {"wait_exit": 3}]),
 sc("TEST-FEAT-011", ["-I", "f.txt"], {"work/f.txt": {"text": "x\n"}}, [K("^T"), K("^Y")]),
 sc("TEST-FEAT-012", ["-I", "-R", "f.txt"], {"work/f.txt": {"text": "x\n"}}, [K("^T"), K("^R"), K("F12")]),
]
json.dump(S, open(os.path.join(SPEC, "evidence", "scenarios", "features.json"), "w"), indent=1)
