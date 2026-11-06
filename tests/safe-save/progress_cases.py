#!/usr/bin/env python3
"""Emit candidate-only safe-save progress cases; never alter nano recordings.

Retains applicable full screen/cursor/style assertions and reviewed identity
mapping. Only extends the private syscall gate to the new temporary inode and
openat, and asserts the deliberate preserved-original outcome on fsync failure.
"""
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "spec/tools"))
from candidate_expectations import candidate_case


def error_expectation(case, snapshot, message):
    width = min(len(message), case.get("cols", 80))
    start = (case.get("cols", 80) - width) // 2
    text = " " * (start - 2) + "[ " + message[:width] + " ]" if start > 1 else " " * start + message[:width]
    for entry in case["expect"]["screen"]:
        if entry.get("snapshot") != snapshot:
            continue
        if entry.get("row") == case.get("rows", 24) - 3 and "equals" in entry:
            entry["equals"] = text
        if "attr_at" in entry and entry["attr_at"][0] == case.get("rows", 24) - 3:
            entry["attr_at"][1] = start - 2 if start > 1 else start


def open_wrappers(interrupt=False):
    """Interpose the existing open surface and its glibc fortified aliases.

    Keep fortified calls on their real two-argument entry points so libc still
    validates missing modes. No openat64 surface is needed by these fixtures.
    """
    if interrupt:
        before = 'if(is_target(path,flags))mark();'
    else:
        before = '''if((flags&(O_WRONLY|O_RDWR))&&target_path(path)){
  if(gate("OPEN",&once_open)<0)return -1;
  if(getenv("FAIL_OPEN")){errno=EACCES;return -1;}
 }'''
    source = '''
static int before_open(const char *path,int flags) {
 BEFORE
 return 0;
}
static int before_openat(int dirfd,const char *path,int flags) {
 char resolved[PATH_MAX];
 if(path[0]=='/' || dirfd==AT_FDCWD)return before_open(path,flags);
 snprintf(resolved,sizeof resolved,"/proc/self/fd/%d/%s",dirfd,path);
 return before_open(resolved,flags);
}
static int needs_mode(int flags) {
 return (flags&O_CREAT) || ((flags&O_TMPFILE)==O_TMPFILE);
}
'''.replace('BEFORE', before)
    # open64 was already interposed; cover its fortified counterpart too.
    for symbol in ('open', 'open64', 'openat'):
        at = symbol == 'openat'
        args = 'int dirfd,const char *path,int flags' if at else 'const char *path,int flags'
        types = 'int,const char*,int' if at else 'const char*,int'
        call = 'dirfd,path,flags' if at else 'path,flags'
        check = 'before_openat(dirfd,path,flags)' if at else 'before_open(path,flags)'
        source += f'''
int {symbol}({args},...) {{
 mode_t mode=0;
 if(needs_mode(flags)){{va_list a;va_start(a,flags);mode=va_arg(a,mode_t);va_end(a);}}
 int (*real_fn)({types},...)=dlsym(RTLD_NEXT,"{symbol}");
 if({check}<0)return -1;
 return needs_mode(flags)?real_fn({call},mode):real_fn({call});
}}
int __{symbol}_2({args}) {{
 int (*real_fn)({types})=dlsym(RTLD_NEXT,"__{symbol}_2");
 if({check}<0)return -1;
 return real_fn({call});
}}
'''
    return source


def adapt_open_gate(text, interrupt=False):
    if interrupt:
        start = text.index('static int(*real_open_fn)')
        end = text.index('static int is_target', start)
        text = text[:start] + text[end:]
        start = text.index('int open(')
        return text[:start] + open_wrappers(interrupt=True)
    start = text.index('static int do_open(')
    end = text.index('int fsync(', start)
    return text[:start] + open_wrappers() + text[end:]


def main():
    suite = sys.argv[1] if len(sys.argv) > 1 else "save-progress"
    assert suite in ("save-progress", "save-safety")
    cases = json.loads((REPO / f"tests/follow-up/scenarios/{suite}.json").read_text())
    for index, original in enumerate(cases):
        case = candidate_case(original)
        gate = case.get("files", {}).get("gate.c")
        if gate and case["id"] != "TEST-SAVE-PROGRESS-FIFO-INTERRUPT":
            old = 'const char *target=getenv("PROGRESS_TARGET");return target&&!strcmp(path,target);'
            new = '''const char *target=getenv("PROGRESS_TARGET");
 if(!target)return 0;
 if(!strcmp(path,target))return 1;
 const char *slash=strrchr(target,'/');
 size_t parent=slash?(size_t)(slash-target):0;
 return slash && !strncmp(path,target,parent) && !strncmp(path+parent,"/.naro-save-",12);'''
            assert old in gate["text"]
            gate["text"] = gate["text"].replace(old, new)
        if gate:
            gate["text"] = adapt_open_gate(
                gate["text"], case["id"] == "TEST-SAVE-PROGRESS-FIFO-INTERRUPT")
        if case["id"] == "TEST-SAVE-PROGRESS-ERROR-SYNC":
            assert case["expect"]["files"]["work/f.txt"] == {"text": "Xhello\n"}
            case["expect"]["files"]["work/f.txt"] = {"text": "hello\n"}
        if "TEST-SAVE-SAFETY-BACKUP-FALLBACK" in case["id"]:
            # A read-only parent now rejects save before file-sync. Keep all
            # terminal cells from the saved-state oracle, explicitly replacing
            # the title/status with the documented failure and dirty state.
            screen = case["expect"]["screen"]
            title = next((e["equals"] for e in screen if e.get("snapshot") == "writing" and e.get("row") == 0), None)
            case["expect"]["screen"] = [e for e in screen if e.get("snapshot") == "saved"]
            if "--minibar" not in case["args"]:
                for entry in case["expect"]["screen"]:
                    if entry.get("row") == 0 and "equals" in entry:
                        entry["equals"] = title
            error_expectation(case, "saved", "Error writing dir/f.txt: Permission denied (original file unchanged)")
            for entry in case["expect"]["screen"]:
                if "attr_at" in entry and entry["attr_at"][0] == case.get("rows", 24) - 3:
                    entry["attr_at"][2] = "bg=1,bold=True,fg=7"
            case["expect"]["files"]["work/dir/f.txt"] = {"text": "hello\n"}
            steps = []
            for step in case["steps"]:
                if step.get("wait_file", {}).get("path") == "home/SYNC.ready" or step.get("snapshot") == "writing" or step.get("write_file") == "home/SYNC.release":
                    continue
                if "wait" in step and (step["wait"].get("text") == "Wrote 1 line" or "(1 line)" in step["wait"].get("text", "")):
                    step = {"wait": {"text": "Permission denied"}}
                steps.append(step)
                if step.get("keys") == ["^X"]:
                    steps.extend([{"wait": {"text": "Save modified buffer?"}}, {"text": "n"}])
            case["steps"] = steps
        if case["id"] == "TEST-SAVE-PROGRESS-ERROR-OPEN":
            # Atomic save enters Writing before opening its transaction files.
            for entry in case["expect"]["screen"]:
                if entry.get("snapshot") != "writing":
                    continue
                if "cursor" in entry:
                    entry["cursor"] = {"x": 47, "y": 21, "visible": False}
                if entry.get("row") == 21:
                    entry["equals"] = "                                 [ Writing... ]"
                if "attr_at" in entry and entry["attr_at"][0] == 21:
                    entry["attr_at"][1] = 33
        errors = {
            "TEST-SAVE-PROGRESS-ERROR-OPEN": ("error", "Error writing f.txt: Permission denied"),
            "TEST-SAVE-PROGRESS-ERROR-SYNC": ("error", "Error writing f.txt: Input/output error"),
            "TEST-SAVE-SAFETY-PREPEND-UNREADABLE": ("result", "Error writing target: Permission denied"),
            "TEST-SAVE-SAFETY-PREPEND-MISSING": ("result", "Error writing target: No such file or directory"),
        }
        if case["id"] in errors:
            snapshot, message = errors[case["id"]]
            error_expectation(case, snapshot, message + " (original file unchanged)")
            for step in case["steps"]:
                if "wait" in step and "Error reading target:" in step["wait"].get("text", ""):
                    step["wait"]["text"] = step["wait"]["text"].replace("Error reading", "Error writing")
        case["note"] = "Issue #3 candidate semantics; historical reference remains unchanged. " + case.get("note", "")
        cases[index] = case
    print(json.dumps(cases, indent=2))


if __name__ == "__main__":
    main()
