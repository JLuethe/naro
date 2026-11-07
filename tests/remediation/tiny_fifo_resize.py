#!/usr/bin/env python3
"""Assert NARO's 70-column redraw after a tiny-profile FIFO interruption.

The pinned GNU scenario remains unchanged. This candidate-only check retains
its file, exit, terminal-reset, and interruption assertions, then adds exact
title and status rows for NARO's documented full redraw on resize. The existing
fortified-open adapter makes the FIFO gate reach NARO's open path.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "spec/tools"))
from open_gate import adapt_tiny_safety_case

ORIGINAL = ROOT / "tests/follow-up/scenarios/tiny-safety.json"
CASE_ID = "TEST-TINY-FIFO-RESIZE-SAFETY"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    source = json.loads(ORIGINAL.read_text())
    case = adapt_tiny_safety_case(copy.deepcopy(next(
        row for row in source if row["id"] == CASE_ID)))
    case["id"] = "TEST-NARO-TINY-FIFO-RESIZE-70"
    case["expect"]["screen"].extend([
        {"snapshot": "after-interrupted", "row": 0,
         "equals": "  NARO 0.1.3                     f.txt                      Modified  "},
        {"snapshot": "after-interrupted", "row": 21,
         "equals": "                           [ Interrupted ]                            "},
    ])
    case["note"] = ("NARO redraws the title and Interrupted message at the "
                    "new 70-column width after FIFO interruption.")
    args.out.mkdir(parents=True, exist_ok=False)
    scenarios = args.out / "scenario.json"
    scenarios.write_text(json.dumps([case], indent=2) + "\n")
    environment = dict(os.environ,
                       NANOSPEC_WORK=str((args.out / "scratch").resolve()))
    command = [sys.executable, str(ROOT / "spec/tools/nanoharness.py"),
               "--candidate-expectations", str(scenarios.resolve()),
               "--binary", str(binary), "--out", str((args.out / "run").resolve())]
    return subprocess.run(command, cwd=ROOT, env=environment, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
