#!/usr/bin/env python3
"""Build data/test-runs.csv: every scenario, whether it ran, its outcome, and the
spec requirements that cite it.  Reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c

Usage: python3 tools/test_inventory.py      (run from the spec directory)"""
import csv, glob, json, os, re, sys

SPEC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(SPEC)

scen = {}
for path in sorted(glob.glob("evidence/scenarios/*.json")):
    for s in json.load(open(path)):
        scen[s["id"]] = (os.path.basename(path), s)

runs = {os.path.basename(d): d for d in glob.glob("evidence/runs/TEST-*") if os.path.isdir(d)}

# Which spec documents and requirement ids mention each test id.
cites = {k: set() for k in scen}
docs = sorted(glob.glob("[0-9][0-9]-*.md"))
for doc in docs:
    text = open(doc, encoding="utf-8").read()
    found = set()
    # "TEST-X-001", "TEST-X-001…005", "TEST-X-001/-003", "TEST-X-001…005, -008, -009".
    for m in re.finditer(r"(TEST-[A-Z0-9]+(?:-[A-Z0-9]+)?-)(\d{3}(?:\s*(?:…|\.\.\.|/|,|and)\s*-?\d{3})*)", text):
        pre, tail = m.group(1), m.group(2)
        nums = re.findall(r"(…|\.\.\.)?\s*-?(\d{3})", tail)
        prev = None
        for sep, n in nums:
            n = int(n)
            if sep and prev is not None:
                found |= {"%s%03d" % (pre, k) for k in range(prev, n + 1)}
            found.add("%s%03d" % (pre, n))
            prev = n
    for t in found:
        if t in cites:
            cites[t].add(doc.split("-")[0])

rows, problems = [], []
for tid, (suite, s) in sorted(scen.items()):
    d = runs.get(tid)
    if not d or not os.path.exists(os.path.join(d, "result.json")):
        rows.append([tid, suite, " ".join(s.get("args", [])), "not-run", "", "", "", "", " ".join(sorted(cites[tid]))])
        continue
    r = json.load(open(os.path.join(d, "result.json")))
    if r.get("reference_commit", "").startswith("6ed285c") is False:
        problems.append("%s: unexpected reference commit %r" % (tid, r.get("reference_commit")))
    rows.append([tid, suite, " ".join(r["argv"][1:]), "recorded",
                 "" if r["exit_status"] is None else r["exit_status"],
                 r["exit_signal"] or "", len(r["snapshots"]),
                 "harness-killed" if r["exit_signal"] == 9 else "",
                 " ".join(sorted(cites[tid]))])
for tid in sorted(set(runs) - set(scen)):
    problems.append("%s: run directory without a scenario definition" % tid)

with open("data/test-runs.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["test_id", "scenario_file", "argv", "status", "exit_status", "exit_signal",
                "snapshots", "note", "cited_in_docs"])
    w.writerows(rows)

total = len(rows); ran = sum(1 for r in rows if r[3] == "recorded")
uncited = [r[0] for r in rows if not r[8]]
print("scenarios %d, recorded %d, not run %d, uncited %d" % (total, ran, total - ran, len(uncited)))
if uncited: print("uncited:", " ".join(uncited))
for p in problems: print("PROBLEM:", p)
