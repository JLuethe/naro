#!/usr/bin/env python3
"""Reproduce the formatter save snapshot race behind a private fsync gate.

The negative control uses the original input steps and expectations, and must
capture Writing... with the cursor hidden. The corrected case must wait for
save completion and pass every original assertion. Raw terminal output, final
files, syscall timestamps and harness step timestamps are retained under --out.
"""
import argparse
import base64
import copy
import json
from pathlib import Path
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "spec/tools"))
import nanoharness as h
from candidate_expectations import candidate_case

CASE_ID = "TEST-STEP3-EOF-L-STRUCT-07-FORMATTER-FAIL"
COMPLETED = {"wait": {"text": "Wrote 5 lines", "timeout": 10}}
GATE = r'''
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>
static int blocked;
static int owned(int fd) {
 char link[64],path[4096];
 snprintf(link,sizeof link,"/proc/self/fd/%d",fd);
 ssize_t n=readlink(link,path,sizeof path-1);
 if(n<0)return 0;path[n]=0;
 const char *root=getenv("FORMATTER_SAVE_ROOT");
 if(!root)return 0;
 size_t len=strlen(root);
 return !strncmp(path,root,len)&&(path[len]=='/'||!path[len]);
}
static void event(const char *stage,int fd) {
 char path[4096];struct timespec now;struct stat info;
 clock_gettime(CLOCK_MONOTONIC,&now);
 snprintf(path,sizeof path,"%s/save-events",getenv("HOME"));
 FILE *stream=fopen(path,"a");
 if(!stream)_exit(91);
 if(fstat(fd,&info))_exit(92);
 fprintf(stream,"%lld %s %s\n",(long long)now.tv_sec*1000000000+now.tv_nsec,
         stage,S_ISDIR(info.st_mode)?"directory":"file");
 fclose(stream);
}
int fsync(int fd) {
 int (*real_sync)(int)=dlsym(RTLD_NEXT,"fsync");
 if(!owned(fd))return real_sync(fd);
 event("fsync-enter",fd);
 if(!blocked++){
  char ready[4096],release[4096];
  snprintf(ready,sizeof ready,"%s/sync-ready",getenv("HOME"));
  snprintf(release,sizeof release,"%s/sync-release",getenv("HOME"));
  int marker=open(ready,O_WRONLY|O_CREAT|O_TRUNC,0600);
  if(marker<0)_exit(93);close(marker);
  int i;for(i=0;i<1500&&access(release,F_OK);i++)usleep(10000);
  if(i==1500){errno=ETIMEDOUT;return -1;}
  event("gate-released",fd);
 }
 int result=real_sync(fd),error=errno;
 event("fsync-return",fd);errno=error;return result;
}
'''


class GatedRun(h.Run):
    def __init__(self, *args, legacy=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.legacy = legacy
        self.events = []
        self.release_timer = None

    def release(self):
        Path(self.inside("home/sync-release")).touch()

    def do_step(self, step, keys, cols, rows):
        if step == COMPLETED or (self.legacy and step.get("snapshot") == "saved"):
            ready = super().do_step(
                {"wait_file": {"path": "home/sync-ready", "timeout": 5}}, keys, cols, rows)
            if not ready:
                raise AssertionError("save never reached the fsync gate")
            if not self.wait_text("Writing...", 5):
                raise AssertionError("save never displayed Writing...")
            if not self.legacy:
                # Stay silent longer than the scenario's 200 ms quiet period.
                # A correct completion wait must span this entire delay.
                self.release_timer = threading.Timer(0.65, self.release)
                self.release_timer.start()
        start = time.monotonic_ns()
        passed = super().do_step(step, keys, cols, rows)
        self.events.append({"step": step, "start_ns": start,
                            "end_ns": time.monotonic_ns(), "raw_bytes": self.raw_size()})
        if self.legacy and step.get("snapshot") == "saved":
            self.release()
        return passed


def run_case(case, binary, out, legacy):
    scenario = copy.deepcopy(case)
    if legacy:
        scenario["steps"].remove(COMPLETED)
    scenario["files"]["gate.c"] = {"text": GATE}
    scenario["build_helpers"] = [{"source": "gate.c", "output": "gate.so"}]
    scenario.setdefault("env", {}).update({"LD_PRELOAD": "$FX/gate.so",
                                            "FORMATTER_SAVE_ROOT": "$FX/work"})
    out.mkdir(parents=True)
    (out / "scenario.json").write_text(json.dumps(scenario, indent=1) + "\n")
    runner = GatedRun(scenario, binary, str(out), keep=True, legacy=legacy)
    try:
        result = runner.execute()
    finally:
        if runner.release_timer:
            runner.release_timer.join()
        runner.cleanup_helpers()
        h.tmux("kill-server", check=False)
        (out / "step-times.json").write_text(json.dumps(runner.events, indent=1) + "\n")
    # Retain these separately: a subsequent repetition uses a fresh fixture.
    events = Path(runner.inside("home/save-events")).read_text()
    (out / "save-events.txt").write_text(events)
    final = Path(runner.inside("work/f.txt")).read_bytes()
    (out / "final-file.bin").write_bytes(final)
    expected = bytes.fromhex(case["expect"]["files"]["work/f.txt"]["hex"])
    assert final == expected, "final file bytes changed"
    assert result["steps_ok"], result["notes"]
    failed = [check for check in result["checks"] if not check["pass"]]
    snap = result["snapshots"]["saved"]
    snapshot_end = next(event["end_ns"] for event in runner.events
                        if event["step"].get("snapshot") == "saved")
    released = int(next(line.split()[0] for line in events.splitlines()
                        if "gate-released" in line))
    if legacy:
        assert [check["check"] for check in failed] == ["cursor"], failed
        assert snap["cursor"]["visible"] is False, snap["cursor"]
        assert "Writing..." in snap["rows"][21]["text"]
        assert snapshot_end < released, "negative control did not capture an in-flight save"
    else:
        assert not failed, failed
        assert "Wrote 5 lines" in snap["rows"][21]["text"]
        assert snapshot_end > released, "snapshot preceded save completion"
        completion = next(event for event in runner.events if event["step"] == COMPLETED)
        assert completion["end_ns"] - completion["start_ns"] >= 600_000_000
        captured = result["captured_files"]["work/f.txt"]
        assert len(captured) == 1 and base64.b64decode(captured[0]) == expected
    return {"negative_control": legacy, "checks": len(result["checks"]),
            "failed_checks": failed, "cursor": snap["cursor"],
            "binary_sha256": result["binary_sha256"], "out": str(out)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", default=str(ROOT / "target/release/naro"))
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--repeat", default=1, type=int)
    args = parser.parse_args()
    if args.repeat < 1:
        parser.error("--repeat must be positive")
    cases = json.loads((ROOT / "tests/follow-up/scenarios/step3-gaps.json").read_text())
    case = candidate_case(next(case for case in cases if case["id"] == CASE_ID))
    summary = []
    for repeat in range(args.repeat):
        for legacy, label in ((True, "legacy"), (False, "completed")):
            result = run_case(case, args.binary, args.out / str(repeat) / label, legacy)
            summary.append(result)
            print(f"{repeat} {label}: PASS ({result['checks']} original checks; "
                  f"{len(result['failed_checks'])} expected failures)", flush=True)
    (args.out / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")


if __name__ == "__main__":
    main()
