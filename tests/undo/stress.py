#!/usr/bin/env python3
"""Bounded production-Buffer stress; freezes source, binary, and measurements."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
HARNESS = r'''
#![allow(dead_code)]
mod native {
    unsafe extern "C" {
        pub fn nr_width(c: u32) -> i32;
        pub fn nr_class(c: u32, class: i32) -> i32;
        pub fn nr_print_byte(c: i32) -> i32;
    }
}
mod bytes;
mod buffer;
use buffer::{Buffer, Pos};
fn main() {
    let bytes = 10 * 1024 * 1024;
    let mut b = Buffer::new(vec![], vec![vec![b'x'; bytes], vec![]]);
    b.state.pos = Pos { line: 0, x: bytes };
    for _ in 0..10_000 { b.insert(b"z", "addition", false, false); }
    assert_eq!(b.state.lines[0].len(), bytes + 10_000);
    for _ in 0..10_000 { assert!(b.undo(false).is_some()); }
    assert_eq!(b.state.lines[0].len(), bytes);
    assert!(b.state.lines[0].iter().all(|v| *v == b'x'));
    assert!(!b.modified);
    for _ in 0..10_000 { assert!(b.undo(true).is_some()); }
    assert_eq!(&b.state.lines[0][bytes..], vec![b'z'; 10_000]);
    b.saved();
    // Force many complete-group evictions without enlarging the source much.
    for _ in 0..200_000 { b.insert(b"q", "addition", false, false); }
    let retained = b.hist;
    assert!(retained > 0 && retained < 200_000);
    for _ in 0..retained { assert!(b.undo(false).is_some()); }
    assert!(b.undo(false).is_none());
    assert!(b.modified);
    assert_eq!(b.state.lines[0].len(), bytes + 210_000 - retained);
    for _ in 0..retained { assert!(b.undo(true).is_some()); }
    assert_eq!(&b.state.lines[0][bytes + 10_000..], vec![b'q'; 200_000]);
    assert_eq!(b.state.lines.len(), 2);
    assert!(b.state.lines[1].is_empty());
    println!("10MiB; 210000 edits; initial full undo/redo; budget eviction; {} retained groups", retained);
}
'''


def limits():
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def run(label, out, revision=None):
    dest = out / label
    dest.mkdir()
    for name in ("buffer.rs", "bytes.rs"):
        content = (subprocess.check_output(["git", "show", f"{revision}:src/{name}"], cwd=ROOT)
                   if revision else (ROOT / "src" / name).read_bytes())
        (dest / name).write_bytes(content)
    (dest / "main.rs").write_text(HARNESS)
    compiler = str(Path.home() / ".cargo/bin/rustc")
    compile_cmd = [compiler, "--edition=2024", "-O", str(dest / "main.rs"), "-o", str(dest / "stress")]
    built = subprocess.run(compile_cmd, capture_output=True, text=True)
    (dest / "build.log").write_text(built.stdout + built.stderr)
    if built.returncode:
        raise RuntimeError(f"{label}: compilation failed; see {dest / 'build.log'}")
    command = [str(dest / "stress")]
    start = time.monotonic()
    timed_out = False
    with (dest / "stdout.txt").open("w") as stdout, (dest / "stderr.txt").open("w") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr, preexec_fn=limits)
        while True:
            pid, status, usage = os.wait4(process.pid, os.WNOHANG)
            if pid:
                break
            if time.monotonic() - start >= 15:
                timed_out = True
                process.kill()
                _, status, usage = os.wait4(process.pid, 0)
                break
            time.sleep(0.01)
        process.returncode = os.waitstatus_to_exitcode(status)
    elapsed = time.monotonic() - start
    rss = usage.ru_maxrss
    passed = process.returncode == 0 and rss <= 96 * 1024 and not timed_out
    expected = passed if revision is None else (process.returncode != 0 and "memory allocation" in (dest / "stderr.txt").read_text())
    report = dict(label=label, revision=revision, commands=[compile_cmd, command],
                  exit_code=process.returncode, elapsed_seconds=elapsed, peak_rss_kib=rss,
                  timed_out=timed_out,
                  timeout_seconds=15, address_space_bound_mib=256, peak_rss_bound_mib=96,
                  passed=passed, expected_result=expected,
                  sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in dest.iterdir() if p.suffix == ".rs" or p.name == "stress"})
    (dest / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--baseline", help="optional historical revision for the failure comparison")
    args = parser.parse_args()
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    reports = []
    if args.baseline:
        reports.append(run("before", args.out, args.baseline))
    reports.append(run("after", args.out))
    (args.out / "report.json").write_text(json.dumps(reports, indent=2) + "\n")
    print(json.dumps(reports, indent=2))
    return int(not all(r["expected_result"] for r in reports))


if __name__ == "__main__":
    raise SystemExit(main())
