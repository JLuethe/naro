# gdb Python script: dump nano's effective shortcut list (sclist) and function
# list (allfuncs) from an UNMODIFIED reference executable that has debug info.
#
# Reference revision: 6ed285c3ec7a1d228def4d4e7021c6ba269f620c
#
# Usage (run inside a terminal, e.g. a tmux pane, because nano needs a tty):
#   DUMP_OUT=/path/out.json gdb -q -batch -x dump_tables.py --args nano [ARGS]
#
# A breakpoint on prepare_for_display() fires after the command line, the
# nanorc files, and the files on the command line have been processed, so the
# tables are the effective ones that the editor will use.  The process is then
# killed; nothing is written to the files under edit.

import gdb
import json
import os

OUT = os.environ.get("DUMP_OUT", "/tmp/nano-tables.json")

MENUS = [
    ("MMAIN", 1 << 0), ("MWHEREIS", 1 << 1), ("MREPLACE", 1 << 2),
    ("MREPLACEWITH", 1 << 3), ("MGOTOLINE", 1 << 4), ("MWRITEFILE", 1 << 5),
    ("MINSERTFILE", 1 << 6), ("MEXECUTE", 1 << 7), ("MHELP", 1 << 8),
    ("MSPELL", 1 << 9), ("MBROWSER", 1 << 10), ("MWHEREISFILE", 1 << 11),
    ("MGOTODIR", 1 << 12), ("MYESNO", 1 << 13), ("MLINTER", 1 << 14),
    ("MFINDINHELP", 1 << 15),
]


def menu_names(mask):
    return [name for name, bit in MENUS if mask & bit]


def func_name(ptr):
    addr = int(ptr)
    if addr == 0:
        return None
    # Use the minimal (ELF) symbol: block_for_pc() would report an inlined
    # callee (e.g. in_restricted_mode inside do_suspend) instead of the
    # function whose address is stored in the table.
    out = gdb.execute("info symbol 0x%x" % addr, to_string=True).split()
    return out[0] if out and out[0] != "No" else "0x%x" % addr


def cstr(val):
    if int(val) == 0:
        return None
    # Labels are UTF-8 in the source (arrow glyphs) or translated strings.
    return val.string(encoding="utf-8", errors="replace")


def has_field(val, name):
    try:
        val[name]
        return True
    except gdb.error:
        return False


class Dumper(gdb.Breakpoint):
    def stop(self):
        result = {"argv": gdb.parameter("args"), "keys": [], "funcs": [],
                  "globals": {}}
        sc = gdb.parse_and_eval("sclist")
        order = 0
        while int(sc) != 0:
            s = sc.dereference()
            entry = {
                "order": order,
                "keystr": cstr(s["keystr"]),
                "keystr_bytes": list(s["keystr"].string(encoding="latin-1").encode("latin-1")) if int(s["keystr"]) else None,
                "keycode": int(s["keycode"]),
                "menus_mask": int(s["menus"]),
                "menus": menu_names(int(s["menus"])),
                "func": func_name(s["func"]),
            }
            if has_field(s, "toggle"):
                entry["toggle"] = int(s["toggle"])
            if has_field(s, "expansion") and int(s["expansion"]) != 0 and entry["func"] == "implant":
                entry["expansion"] = cstr(s["expansion"])
            result["keys"].append(entry)
            order += 1
            sc = s["next"]
        f = gdb.parse_and_eval("allfuncs")
        order = 0
        while int(f) != 0:
            fs = f.dereference()
            entry = {
                "order": order,
                "func": func_name(fs["func"]),
                "menus_mask": int(fs["menus"]),
                "menus": menu_names(int(fs["menus"])),
                "tag": cstr(fs["tag"]),
            }
            if has_field(fs, "phrase"):
                entry["phrase"] = cstr(fs["phrase"])
                entry["blank_after"] = bool(int(fs["blank_after"]))
            result["funcs"].append(entry)
            order += 1
            f = fs["next"]
        for g in ["using_utf8", "on_a_vt", "flags[0]", "flags[1]", "COLS", "LINES",
                  "tabsize"]:
            try:
                result["globals"][g] = int(gdb.parse_and_eval(g))
            except gdb.error as e:
                result["globals"][g] = "unavailable: %s" % e
        with open(OUT, "w") as fh:
            json.dump(result, fh, indent=1, ensure_ascii=False)
        gdb.execute("kill")
        return True


gdb.execute("set pagination off")
gdb.execute("set confirm off")
Dumper("prepare_for_display")
gdb.execute("run")
