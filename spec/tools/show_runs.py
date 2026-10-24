#!/usr/bin/env python3
"""Compact viewer for harness results (evidence/runs/<id>/result.json).

Usage: show_runs.py [--full] [--rows a-b] ID-or-prefix ...
Prints, per snapshot, the non-blank rows (or the selected rows), the cursor,
and per run the exit status, stderr and changed fixture files.
"""
import json
import os
import sys

SPEC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.path.join(SPEC, "evidence", "runs")


def main():
    args = sys.argv[1:]
    full = "--full" in args
    rows = None
    if "--rows" in args:
        i = args.index("--rows")
        a, b = args[i + 1].split("-")
        rows = range(int(a), int(b) + 1)
        del args[i:i + 2]
    attrs = "--attrs" in args
    args = [a for a in args if not a.startswith("--")]
    ids = sorted(d for d in os.listdir(RUNS) if any(d.startswith(a) for a in args))
    for rid in ids:
        p = os.path.join(RUNS, rid, "result.json")
        if not os.path.exists(p):
            continue
        r = json.load(open(p))
        print("=" * 30, rid, "argv=", " ".join(r["argv"]), "exit=", r["exit_status"], "sig=", r["exit_signal"])
        for name, snap in r["snapshots"].items():
            print("--", name, "cursor=(%d,%d)%s" % (snap["cursor"]["x"], snap["cursor"]["y"],
                  "" if snap["cursor"]["visible"] else " hidden"))
            for i, row in enumerate(snap["rows"]):
                if (rows and i in rows) or (not rows and (full or row["text"].strip())):
                    print("%2d|%s|" % (i, row["text"].rstrip()))
                    if attrs and row["attrs"]:
                        print("   attrs:", row["attrs"])
        if r.get("stderr"):
            print("stderr:", repr(r["stderr"]))
        if r.get("stdout"):
            print("stdout:", repr(r["stdout"]))
        if r.get("notes"):
            print("notes:", r["notes"])
        print("trace_final:", r.get("trace_final_modes"))
        files = {k: v for k, v in r["fixture"].items() if k.startswith("work/") or k.startswith("home/")}
        for k, v in files.items():
            if v["type"] == "file":
                print("file %s mode=%s size=%s %s" % (k, v["mode"], v.get("size"),
                      repr(v.get("text", ""))[:120] if "text" in v else v.get("sha256")))
            else:
                print("%s %s %s" % (v["type"], k, v.get("target", "")))


if __name__ == "__main__":
    main()
