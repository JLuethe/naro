#!/usr/bin/env python3
"""Build the machine-readable inventories under spec/data/.

Reference revision: 6ed285c3ec7a1d228def4d4e7021c6ba269f620c

Inputs:
  * the pinned source tree (~/src/nano-ref), parsed with simple, explicit
    patterns (no compilation);
  * the gdb table dumps in spec/evidence/tables/*.json (runtime-observed);
  * xgettext output regenerated from the pinned sources.

Every generated file is documented in spec/data/README.md.
"""

import csv
import glob
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ifdefs import conditions  # noqa: E402

SRC = os.path.expanduser("~/src/nano-ref")
SPEC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(SPEC, "data")
TABLES = os.path.join(SPEC, "evidence", "tables")
COMMIT = "6ed285c3ec7a1d228def4d4e7021c6ba269f620c"

MENUS = ["MMAIN", "MWHEREIS", "MREPLACE", "MREPLACEWITH", "MGOTOLINE", "MWRITEFILE",
         "MINSERTFILE", "MEXECUTE", "MHELP", "MSPELL", "MBROWSER", "MWHEREISFILE",
         "MGOTODIR", "MYESNO", "MLINTER", "MFINDINHELP"]
RC_MENU = {"MMAIN": "main", "MWHEREIS": "search", "MREPLACE": "replace",
           "MREPLACEWITH": "replacewith", "MYESNO": "yesno", "MGOTOLINE": "gotoline",
           "MWRITEFILE": "writeout", "MINSERTFILE": "insert", "MEXECUTE": "execute",
           "MHELP": "help", "MSPELL": "spell", "MLINTER": "linter", "MBROWSER": "browser",
           "MWHEREISFILE": "whereisfile", "MGOTODIR": "gotodir", "MFINDINHELP": ""}

PROFILES = ["default-utf8", "default-C", "default-modern", "default-modern-vt220",
            "default-preserve", "default-restricted", "default-rnano", "default-view",
            "default-saveonexit", "tiny-utf8", "tiny-C", "tiny-modern", "tiny-restricted"]

# Functions that changes_something() refuses in view mode (nano.c:1396-1421).
VIEW_BLOCKED = {"do_savefile", "do_writeout", "do_enter", "do_tab", "do_delete",
                "do_backspace", "cut_text", "paste_text", "chop_previous_word",
                "chop_next_word", "zap_text", "cut_till_eof", "do_execute",
                "do_indent", "do_unindent", "do_justify", "do_full_justify",
                "do_comment", "do_spell", "do_formatter", "complete_a_word",
                "do_replace", "do_verbatim_input"}
# Functions that call in_restricted_mode() and refuse to act (nano.c:205-213).
RESTRICTED_REFUSE = {"do_insertfile", "do_execute", "do_spell", "do_linter",
                     "do_formatter", "do_suspend"}


def rel(path):
    return os.path.relpath(path, SRC)


def src_lines(name):
    with open(os.path.join(SRC, name), encoding="utf-8", errors="replace") as fh:
        return fh.read().split("\n")


def c_string(lit):
    """Decode a C string literal body (without quotes) to Python str (latin-1 bytes)."""
    out = bytearray()
    i = 0
    while i < len(lit):
        c = lit[i]
        if c == "\\":
            n = lit[i + 1]
            if n == "x":
                m = re.match(r"[0-9a-fA-F]{1,2}", lit[i + 2:])
                out.append(int(m.group(0), 16))
                i += 2 + len(m.group(0))
                continue
            out.append({"n": 10, "t": 9, "\\": 92, '"': 34, "'": 39, "e": 27}.get(n, ord(n)))
            i += 2
            continue
        out += c.encode("utf-8")
        i += 1
    return out.decode("utf-8", errors="replace")


# ----------------------------------------------------------------- strtosc

def parse_strtosc():
    """Return list of dicts: rc name -> C function (or toggle flag)."""
    lines = src_lines("src/rcfile.c")
    conds = conditions(os.path.join(SRC, "src/rcfile.c"))
    start = next(i for i, l in enumerate(lines) if l.startswith("keystruct *strtosc("))
    end = next(i for i in range(start, len(lines)) if lines[i].startswith("}"))
    pending = []
    entries = []
    for i in range(start, end):
        l = lines[i]
        for name in re.findall(r'!strcmp\(input, "([^"]+)"\)', l):
            pending.append((name, i + 1))
        m = re.search(r"s->func = (\w+);", l)
        if m and pending and "do_toggle" != m.group(1):
            for name, ln in pending:
                entries.append({"rc_name": name, "func": m.group(1), "toggle": "",
                                "line": ln, "cond": conds[ln]})
            pending = []
        m = re.search(r"s->toggle = (\w+);", l)
        if m and pending:
            for name, ln in pending:
                entries.append({"rc_name": name, "func": "do_toggle", "toggle": m.group(1),
                                "line": ln, "cond": conds[ln]})
            pending = []
    return entries


# ----------------------------------------------------------------- sclist registrations

REG_SC = re.compile(r"add_to_sclist\((.+?),\s*(\"(?:[^\"\\]|\\.)*\"|help_key|SLASH_OR_DASH|ISSET\(MODERN_BINDINGS\) \? \"\^E\" : \"\^T\"),\s*([^,]+),\s*(\w+)\);")
REG_TOGGLE = re.compile(r'add_toggle\("([^"]+)", (\w+)\);')


def runtime_condition(lineno):
    """Hand-maintained runtime guards around registrations in global.c (verified by reading)."""
    guards = []
    table = [
        (1259, 1278, "MODERN_BINDINGS"), (1280, 1297, "!MODERN_BINDINGS"),
        (1282, 1283, "!PRESERVE (at shortcut_init time)"), (1286, 1287, "!PRESERVE (at shortcut_init time)"),
        (1319, 1320, "!PRESERVE (at shortcut_init time)"),
        (1389, 1399, "using_utf8"), (1395, 1398, "!on_a_vt"),
        (1403, 1411, "!using_utf8"), (1408, 1411, "!on_a_vt"),
        (1419, 1423, "using_utf8"), (1427, 1430, "!using_utf8"),
        (1442, 1444, "using_utf8"), (1448, 1449, "!using_utf8"),
        (1528, 1530, "using_utf8"), (1534, 1535, "!using_utf8"),
        (1558, 1559, "!PRESERVE (at shortcut_init time)"),
        (1564, 1569, "!RESTRICTED && !VIEW_MODE (at shortcut_init time)"),
        (1573, 1578, "!RESTRICTED && !VIEW_MODE (at shortcut_init time)"),
        (1583, 1584, "!RESTRICTED (at shortcut_init time)"),
    ]
    for a, b, g in table:
        if a <= lineno <= b:
            guards.append(g)
    return " && ".join(guards)


def parse_registrations():
    lines = src_lines("src/global.c")
    conds = conditions(os.path.join(SRC, "src/global.c"))
    regs = []
    for i, l in enumerate(lines, 1):
        m = REG_SC.search(l)
        if m and "void add_to_sclist" not in l:
            ks = m.group(2)
            if ks.startswith('"'):
                ks_vals = [c_string(ks[1:-1])]
            elif ks == "help_key":
                ks_vals = ["^H", "^N"]
            elif ks == "SLASH_OR_DASH":
                ks_vals = ["^/", "^-"]
            else:
                ks_vals = ["^E", "^T"]
            regs.append({"line": i, "menus_expr": m.group(1).strip(), "keystr_expr": ks,
                         "keystr_vals": ks_vals, "keycode_expr": m.group(3).strip(),
                         "func": m.group(4), "toggle": "", "cond": conds[i],
                         "runtime": runtime_condition(i)})
        m = REG_TOGGLE.search(l)
        if m and "void add_toggle" not in l:
            regs.append({"line": i, "menus_expr": "MMAIN (ALMOST_ALL for NO_HELP)",
                         "keystr_expr": '"%s"' % m.group(1), "keystr_vals": [m.group(1)],
                         "keycode_expr": "0", "func": "do_toggle", "toggle": m.group(2),
                         "cond": conds[i], "runtime": ""})
    return regs


FLAG_NAMES = None


def flag_names():
    global FLAG_NAMES
    if FLAG_NAMES is None:
        text = "\n".join(src_lines("src/definitions.h"))
        body = text[text.index("DONTUSE = 0"):]
        body = body[:body.index("};")]
        names = re.findall(r"^\s*([A-Z_]+),?", body, re.M)
        FLAG_NAMES = {i: n for i, n in enumerate(names)}
    return FLAG_NAMES


def load_dumps():
    dumps = {}
    for p in PROFILES:
        path = os.path.join(TABLES, p + ".json")
        if os.path.exists(path):
            dumps[p] = json.load(open(path))
    return dumps


def keycode_symbol(code):
    names = {0x0d: "CR", 0x09: "TAB", 0x08: "BS", 0x0a: "LF", 0x20: "SPACE",
             343: "KEY_ENTER", 263: "KEY_BACKSPACE", 330: "KEY_DC", 331: "KEY_IC",
             338: "KEY_NPAGE", 339: "KEY_PPAGE", 258: "KEY_DOWN", 259: "KEY_UP",
             260: "KEY_LEFT", 261: "KEY_RIGHT", 262: "KEY_HOME", 360: "KEY_END",
             355: "KEY_CANCEL", 397: "KEY_SIC",
             0x401: "CONTROL_LEFT", 0x402: "CONTROL_RIGHT", 0x403: "CONTROL_UP",
             0x404: "CONTROL_DOWN", 0x405: "CONTROL_HOME", 0x406: "CONTROL_END",
             0x40D: "CONTROL_DELETE", 0x41D: "CONTROL_SHIFT_DELETE",
             0x421: "ALT_LEFT", 0x422: "ALT_RIGHT", 0x423: "ALT_UP", 0x424: "ALT_DOWN",
             0x425: "ALT_HOME", 0x426: "ALT_END", 0x427: "ALT_PAGEUP", 0x428: "ALT_PAGEDOWN",
             0x42C: "ALT_INSERT", 0x42D: "ALT_DELETE", 0x45D: "SHIFT_DELETE",
             0x45F: "SHIFT_TAB", 0x4B5: "START_OF_PASTE", 0x4BE: "END_OF_PASTE",
             0x4F0: "KEY_CENTER", 0x4FE: "KEY_FRESH"}
    if 265 <= code <= 265 + 63:
        return "KEY_F(%d)" % (code - 264)
    if code in names:
        return names[code]
    if code < 0x20:
        return "CTRL-%s" % chr(code + 0x40)
    if 0x20 < code < 0x7f:
        return "'%s'" % chr(code)
    return ""


def consistent(reg, prof):
    """Is a registration's build/runtime condition compatible with a dumped profile?"""
    tiny = prof.startswith("tiny")
    cond, rt = reg["cond"], reg["runtime"]
    if re.search(r"(^|[^!])NANO_TINY", cond) and not tiny:
        return False
    if "!NANO_TINY" in cond and tiny:
        return False
    modern = "modern" in prof
    if re.search(r"(^|[^!])MODERN_BINDINGS", rt) and not modern:
        return False
    if "!MODERN_BINDINGS" in rt and modern:
        return False
    if "!PRESERVE" in rt and "preserve" in prof:
        return False
    utf8 = not prof.endswith("-C")
    if re.search(r"(^|[^!])using_utf8", rt) and not utf8:
        return False
    if "!using_utf8" in rt and utf8:
        return False
    if "!RESTRICTED" in rt and ("restricted" in prof or "rnano" in prof):
        return False
    if "!VIEW_MODE" in rt and "view" in prof:
        return False
    return True


def build_keybindings(dumps, rcmap, funcs_by_profile):
    regs = parse_registrations()
    rows = []
    unmatched = []
    seen = {}
    for prof, d in dumps.items():
        for k in d["keys"]:
            ks = k["keystr"] or ""
            cands = [r for r in regs if r["func"] == k["func"] and
                     (k.get("toggle", 0) == 0 or flag_names().get(k["toggle"]) == r["toggle"]) and
                     (ks in r["keystr_vals"] or (ks == "" and r["keystr_expr"] == '""'))]
            if len(cands) > 1:
                cands = [r for r in cands if consistent(r, prof)] or cands
            if len(cands) > 1:
                # disambiguate by menus
                c2 = [r for r in cands if all(m in r["menus_expr"] or "MMOST" in r["menus_expr"]
                      or "ALMOST" in r["menus_expr"] for m in k["menus"][:1])]
                cands = c2 or cands
            if not cands:
                unmatched.append((prof, k))
                continue
            reg = cands[0]
            key = (reg["line"], ks, tuple(k["menus"]), k["keycode"])
            seen.setdefault(key, {"reg": reg, "k": k, "profiles": set()})["profiles"].add(prof)
    for (line, ks, menus, code), v in sorted(seen.items(), key=lambda x: (x[0][0], x[0][1])):
        reg, k = v["reg"], v["k"]
        toggle = flag_names().get(k.get("toggle", 0), "") if k.get("toggle") else ""
        for menu in menus:
            rcnames = sorted({e["rc_name"] for e in rcmap
                              if e["func"] == k["func"] and (e["toggle"] == toggle or not toggle)})
            # help-line tag and phrase for this function in this menu (default profile)
            tag = phrase = ""
            for prof in ("default-utf8", "tiny-utf8"):
                for f in funcs_by_profile.get(prof, []):
                    if f["func"] == k["func"] and menu in f["menus"]:
                        tag, phrase = f["tag"] or "", f.get("phrase") or ""
                        break
                if tag:
                    break
            rows.append({
                "binding_id": "KB-%d-%s" % (line, menu),
                "context": menu,
                "rc_menu": RC_MENU[menu],
                "key_display": ks,
                "key_display_utf8_hex": ks.encode("utf-8").hex() if any(ord(c) > 127 for c in ks) else "",
                "keycode": k["keycode"],
                "keycode_symbol": keycode_symbol(k["keycode"]),
                "meta": "yes" if ks.startswith("M-") or ks.startswith("Sh-M-") else "no",
                "function_c": k["func"],
                "toggle_flag": toggle,
                "rc_function_names": " ".join(rcnames),
                "help_tag": tag,
                "help_phrase": phrase,
                "view_mode": ("blocked" if k["func"] in VIEW_BLOCKED else "allowed"),
                "restricted_mode": ("refused-with-message" if k["func"] in RESTRICTED_REFUSE else "allowed"),
                "profiles": " ".join(p for p in PROFILES if p in v["profiles"]),
                "build_condition": reg["cond"],
                "runtime_condition": reg["runtime"],
                "source": "src/global.c:%d" % line,
                "evidence": "runtime-observed (gdb table dump); source-confirmed",
                "spec_section": "02-keybindings.md",
                "req_ids": "",
                "test_ids": "",
            })
    return rows, unmatched


def build_functions(dumps, rcmap):
    rows = []
    seen = {}
    for prof, d in dumps.items():
        for f in d["funcs"]:
            key = (f["func"], f["tag"], tuple(f["menus"]))
            seen.setdefault(key, {"f": f, "profiles": set(), "order": {}})
            seen[key]["profiles"].add(prof)
            seen[key]["order"][prof] = f["order"]
    lines = src_lines("src/global.c")
    conds = conditions(os.path.join(SRC, "src/global.c"))
    for (func, tag, menus), v in seen.items():
        # find registration line: add_to_funcs(func, ... tag ...)
        ln = ""
        for i, l in enumerate(lines, 1):
            if re.search(r"add_to_funcs\(%s," % re.escape(func), l):
                window = " ".join(lines[i - 1:i + 3])
                if tag and ('"%s"' % tag) in window or (tag == "Exit" and "exit_tag" in window) \
                        or (tag == "Close" and "close_tag" in window):
                    ln = i
                    break
        rows.append({
            "function_c": func, "help_tag": tag, "contexts": " ".join(menus),
            "help_phrase": v["f"].get("phrase") or "",
            "blank_after": v["f"].get("blank_after", ""),
            "rc_function_names": " ".join(sorted({e["rc_name"] for e in rcmap if e["func"] == func})),
            "profiles": " ".join(p for p in PROFILES if p in v["profiles"]),
            "order_default_utf8": v["order"].get("default-utf8", ""),
            "order_tiny_utf8": v["order"].get("tiny-utf8", ""),
            "source": "src/global.c:%s" % ln if ln else "",
            "build_condition": conds[ln] if ln else "",
            "view_mode": "blocked" if func in VIEW_BLOCKED else "allowed",
            "restricted_mode": "refused-with-message" if func in RESTRICTED_REFUSE else "allowed",
            "spec_section": "02-keybindings.md",
        })
    rows.sort(key=lambda r: (r["order_default_utf8"] if r["order_default_utf8"] != "" else 999,
                             r["order_tiny_utf8"] if r["order_tiny_utf8"] != "" else 999))
    return rows


def build_bindable(rcmap):
    rows = []
    groups = {}
    for e in rcmap:
        groups.setdefault((e["func"], e["toggle"]), []).append(e)
    for (func, toggle), es in groups.items():
        for e in es:
            rows.append({
                "rc_name": e["rc_name"],
                "function_c": func,
                "toggle_flag": toggle,
                "aliases": " ".join(x["rc_name"] for x in es if x["rc_name"] != e["rc_name"]),
                "build_condition": e["cond"],
                "source": "src/rcfile.c:%d" % e["line"],
                "menu_restriction": menu_restriction(func, toggle),
                "spec_section": "02-keybindings.md#bindable-functions",
            })
    return rows


def menu_restriction(func, toggle):
    universal = {"do_left", "do_right", "do_home", "do_end", "to_prev_word", "to_next_word",
                 "do_delete", "do_backspace", "cut_text", "paste_text", "do_tab", "do_enter",
                 "do_verbatim_input"}
    if func in universal:
        return "MMOST|MBROWSER (universal)"
    if func == "do_toggle" and toggle == "NO_HELP":
        return "(MMOST|MBROWSER|MYESNO) & ~MFINDINHELP"
    if func == "do_toggle":
        return "MMAIN"
    if func == "full_refresh":
        return "MMOST|MBROWSER|MHELP|MYESNO"
    return "menus where the function is registered in the function list (allfuncs)"


# ----------------------------------------------------------------- help lines

def helplines(dumps, cols=80):
    """Simulate bottombars()/shown_entries_for() for each profile and menu (winio.c:2438-2491)."""
    rows = []
    for prof, d in dumps.items():
        keys, funcs = d["keys"], d["funcs"]

        def first_sc_for(menu, func):
            for k in keys:
                if menu in k["menus"] and k["func"] == func and k["keystr"]:
                    return k
            return None
        for menu in MENUS:
            if menu in ("MYESNO",):
                continue
            maximum = ((cols + 40) // 20) * 2
            count = 0
            idx = 0
            while count < maximum and idx < len(funcs):
                if menu in funcs[idx]["menus"]:
                    count += 1
                idx += 1
            if menu == "MWRITEFILE" and idx >= len(funcs) and first_sc_for(menu, "discard_buffer") is None:
                count -= 1
            number = count
            if number == 0:
                continue
            itemwidth = cols // ((number + 1) // 2)
            index = 0
            for f in funcs:
                if index >= number:
                    break
                if menu not in f["menus"]:
                    continue
                s = first_sc_for(menu, f["func"])
                if s is None:
                    continue
                width = itemwidth
                if number % 2 == 1 and index + 2 == number:
                    width += itemwidth
                if index + 2 >= number:
                    width += cols % itemwidth
                rows.append({"profile": prof, "context": menu, "slot": index,
                             "row": 1 + index % 2, "column": (index // 2) * itemwidth,
                             "width": width, "key_display": s["keystr"], "help_tag": f["tag"],
                             "function_c": f["func"], "cols": cols})
                index += 1
    return rows


# ----------------------------------------------------------------- write

def write_csv(name, rows, fields=None):
    path = os.path.join(DATA, name)
    fields = fields or (list(rows[0].keys()) if rows else [])
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("wrote %-32s %5d rows" % (name, len(rows)))


def main():
    os.makedirs(DATA, exist_ok=True)
    dumps = load_dumps()
    rcmap = parse_strtosc()
    funcs_by_profile = {p: d["funcs"] for p, d in dumps.items()}
    kb, unmatched = build_keybindings(dumps, rcmap, funcs_by_profile)
    write_csv("keybindings.csv", kb)
    if unmatched:
        print("UNMATCHED dump entries:", len(unmatched))
        for p, k in unmatched[:20]:
            print("  ", p, k["keystr"], k["func"], k["menus"])
    write_csv("functions.csv", build_functions(dumps, rcmap))
    write_csv("bindable-functions.csv", build_bindable(rcmap))
    write_csv("helplines-80cols.csv", helplines(dumps))
    for mod in ("inv_cli", "inv_rc", "inv_messages", "inv_features", "inv_misc"):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), mod + ".py")
        if os.path.exists(path):
            m = __import__(mod)
            m.build(write_csv)


if __name__ == "__main__":
    main()
