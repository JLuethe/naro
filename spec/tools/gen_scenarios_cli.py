#!/usr/bin/env python3
"""Generate CLI scenario files (evidence/scenarios/cli.json).

Reference revision: 6ed285c3ec7a1d228def4d4e7021c6ba269f620c
"""
import json
import os

SPEC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINES = "".join("line %d\n" % i for i in range(1, 101))
WIDE = "alpha beta gamma\n\tTabbed line\nFoo foo FOO\nlast\n"


def sc(id, args, steps=None, files=None, expect=None, **kw):
    d = {"id": id, "args": args, "files": files or {}, "steps": steps or
         [{"settle": 400}, {"snapshot": "start"}, {"keys": ["^X"]}, {"wait_exit": 3}]}
    if expect:
        d["expect"] = expect
    d.update(kw)
    return d


F100 = {"work/f.txt": {"text": LINES}}
FW = {"work/w.txt": {"text": WIDE}}

S = [
    sc("TEST-CLI-001", ["-I", "+50", "f.txt"], files=F100),
    sc("TEST-CLI-002", ["-I", "+50,3", "f.txt"], files=F100),
    sc("TEST-CLI-003", ["-I", "+-1", "f.txt"], files=F100),
    sc("TEST-CLI-004", ["-I", "+", "f.txt"], files=F100),
    sc("TEST-CLI-005", ["-I", "+,4", "f.txt"], files=F100),
    sc("TEST-CLI-006", ["-I", "+999", "f.txt"], files=F100),
    sc("TEST-CLI-007", ["-I", "+3,-2", "w.txt"], files=FW),
    sc("TEST-CLI-008", ["-I", "+x5", "f.txt"], files=F100),
    sc("TEST-CLI-009", ["-I", "+/foo", "w.txt"], files=FW),
    sc("TEST-CLI-010", ["-I", "+c/foo", "w.txt"], files=FW),
    sc("TEST-CLI-011", ["-I", "+?foo", "w.txt"], files=FW),
    sc("TEST-CLI-012", ["-I", "+r/^l.st", "w.txt"], files=FW),
    sc("TEST-CLI-013", ["-I", "+/", "w.txt"], files=FW),
    sc("TEST-CLI-014", ["-I", "+q/foo", "w.txt"], files=FW),
    sc("TEST-CLI-015", ["-I", "+/nomatch", "w.txt"], files=FW),
    sc("TEST-CLI-016", ["-I", "+50"]),
    sc("TEST-CLI-017", ["-I", "--", "+50"]),
    sc("TEST-CLI-018", ["-I", "-@", "f.txt:7"], files=F100),
    sc("TEST-CLI-019", ["-I", "-@", "f.txt:7:3"], files=F100),
    sc("TEST-CLI-020", ["-I", "-@", "nofile:7"]),
    sc("TEST-CLI-021", ["-I", "f.txt:7"], files=F100),
    sc("TEST-CLI-022", ["-I", "-@", "+2", "f.txt:7"], files=F100),
    sc("TEST-CLI-023", ["-I", "newfile.txt"]),
    sc("TEST-CLI-024", ["-I", "."]),
    sc("TEST-CLI-025", ["-I", "/dev/null"]),
    sc("TEST-CLI-026", ["-I", "dir/"]),
    sc("TEST-CLI-027", ["-I", "f.txt", "w.txt"], files=dict(F100, **FW)),
    sc("TEST-CLI-028", ["-I", "-v", "f.txt"], files=F100),
    sc("TEST-CLI-029", ["-I", "-v"]),
    sc("TEST-CLI-030", ["-I", "-"], stdin="piped data\nsecond line\n"),
    sc("TEST-CLI-031", ["-I", "-", "f.txt"], stdin="piped\n", files=F100),
    sc("TEST-CLI-032", ["-I", "-o", "/nonexistent-dir"]),
    sc("TEST-CLI-033", ["-I", "-B", "-C", "/nonexistent-dir"]),
    sc("TEST-CLI-034", ["-I", "-Q", "("]),
    sc("TEST-CLI-035", ["-I", "-R", "-B", "-C", "/nonexistent-dir"]),
    sc("TEST-CLI-036", ["-I"], stdin="ignored\n"),
    sc("TEST-CLI-037", [], files={"home/.nanorc": {"text": "set bogus\nset tabsize 0\nbind ^Q nosuch main\n"}}),
    sc("TEST-CLI-038", ["-I", "-x", "-c"]),
    sc("TEST-CLI-039", ["-I", "-0"]),
    sc("TEST-CLI-040", ["-I", "-_", "f.txt"], files=F100),
    sc("TEST-CLI-041", ["-I", "-%", "-i", "f.txt"], files=F100),
    sc("TEST-CLI-042", ["-I", "-e", "f.txt"], files=F100),
    sc("TEST-CLI-043", ["-I", "-l", "f.txt"], files=F100),
    sc("TEST-CLI-044", ["-I", "-q", "f.txt"], files=F100),
    sc("TEST-CLI-045", ["-I", "-J", "10", "w.txt"], files=FW),
    sc("TEST-CLI-046", ["-I", "-D", "f.txt"], files=F100),
    sc("TEST-CLI-047", ["-I", "-Y", "nosuchsyntax", "f.txt"], files=F100),
    sc("TEST-CLI-048", ["-I", "+2", "f.txt", "+3", "w.txt"], files=dict(F100, **FW)),
    sc("TEST-CLI-049", ["-I", "-R"]),
    sc("TEST-CLI-050", ["-I", "f.txt", "nonexist.txt", "."], files=F100),
    sc("TEST-CLI-051", ["-I", "-f", "$FX/home/rcdir"], dirs=["home/rcdir"]),
    sc("TEST-CLI-052", ["-I", "+0,0", "f.txt"], files=F100),
    sc("TEST-CLI-053", ["-I", "+2.5", "f.txt"], files=F100),
    sc("TEST-CLI-054", ["-I", "+2:5", "f.txt"], files=F100),
    sc("TEST-CLI-055", ["-I", "+cr/F.o", "w.txt"], files=FW),
]
for s in S:
    if s["id"] == "TEST-CLI-026":
        s["dirs"] = ["work/dir"]
    if s["id"] == "TEST-CLI-028":
        s["steps"] = [{"settle": 400}, {"snapshot": "start"}, {"text": "x"}, {"snapshot": "typed"},
                      {"keys": ["^X"]}, {"wait_exit": 3}]
    if s["id"] in ("TEST-CLI-027", "TEST-CLI-050", "TEST-CLI-048"):
        s["steps"] = [{"settle": 400}, {"snapshot": "start"}, {"keys": ["M-."]}, {"settle": 300},
                      {"snapshot": "second"}, {"keys": ["^X"]}, {"settle": 300}, {"keys": ["^X"]},
                      {"settle": 300}, {"keys": ["^X"]}, {"wait_exit": 3}]
    if s["id"] == "TEST-CLI-030":
        s["steps"] = [{"settle": 600}, {"snapshot": "start"}, {"keys": ["^X"]}, {"settle": 300},
                      {"snapshot": "ask"}, {"text": "n"}, {"wait_exit": 3}]
json.dump(S, open(os.path.join(SPEC, "evidence", "scenarios", "cli.json"), "w"), indent=1)
print(len(S), "scenarios")
