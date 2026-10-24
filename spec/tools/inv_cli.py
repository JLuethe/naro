"""CLI option inventory (data/cli-options.csv).

Reference revision: 6ed285c3ec7a1d228def4d4e7021c6ba269f620c
Sources: src/nano.c long_options[] (1744-1841), the getopt optstring
(1881-1882), the option switch (1883-2153) and usage() (490-648).
"""

import os
import re

from ifdefs import conditions

SRC = os.path.expanduser("~/src/nano-ref")


def build(write_csv):
    path = os.path.join(SRC, "src/nano.c")
    lines = open(path, encoding="utf-8").read().split("\n")
    conds = conditions(path)
    longs = {}
    for i in range(1743, 1841):
        m = re.search(r'\{"(\w+)", (\d), NULL, (\'.\'|0x[0-9A-F]+)\}', lines[i])
        if m:
            ch = m.group(3)
            ch = chr(int(ch, 16)) if ch.startswith("0x") else ch[1]
            longs.setdefault(ch, []).append((m.group(1), int(m.group(2)), i + 1, conds[i + 1]))
    optstring = "ABC:DEFGHIJ:KLMNOPQ:RST:UVWX:Y:Zabcdef:ghijklmno:pqr:s:tuvwxyz!@%_01/"
    shorts = {}
    j = 0
    while j < len(optstring):
        c = optstring[j]
        takes = j + 1 < len(optstring) and optstring[j + 1] == ":"
        shorts[c] = takes
        j += 2 if takes else 1
    # handler lines in the switch
    handlers = {}
    current = None
    for i in range(1882, 2153):
        m = re.match(r"\s*case '(.)':|\s*case (0xCC):", lines[i])
        if m:
            current = m.group(1) or "\xcc"
            handlers[current] = {"line": i + 1, "cond": conds[i + 1], "body": []}
            continue
        if lines[i].strip().startswith("default:"):
            current = None
        if current and lines[i].strip() not in ("break;",) and not lines[i].lstrip().startswith("#"):
            handlers[current]["body"].append(lines[i].strip())
    # usage lines
    usage = {}
    for i in range(489, 648):
        m = re.search(r'print_opt\((_\()?"([^"]+)"\)?, (_\()?"([^"]+)"\)?,', lines[i])
        if m:
            desc = re.search(r'N_\("([^"]+)"\)', lines[i] + lines[i + 1] + lines[i + 2] + lines[i + 3])
            short = m.group(2).split()[0]
            restr = ""
            for k in range(i - 1, max(i - 3, 489), -1):
                if "!ISSET(RESTRICTED)" in lines[k]:
                    restr = "hidden from --help when restricted"
            usage[short] = {"short_disp": m.group(2), "long_disp": m.group(4),
                            "desc": desc.group(1) if desc else "", "line": i + 1,
                            "cond": conds[i + 1], "restricted": restr}
    rows = []
    allchars = sorted(set(shorts) | set(longs), key=lambda c: optstring.find(c) if c in optstring else 999)
    for c in allchars:
        lg = longs.get(c, [])
        h = handlers.get(c, {})
        u = usage.get("-" + c, usage.get("-%s" % c, {}))
        effect = " ".join(h.get("body", []))
        effect = re.sub(r"\s+", " ", effect)
        rows.append({
            "short": ("-" + c) if c in shorts else "",
            "short_accepted_by_getopt": "yes" if c in shorts else "no (long only)",
            "long": " ".join("--" + n for n, _, _, _ in lg),
            "deprecated_aliases": " ".join("--" + n for n, _, ln, _ in lg
                                           if "Deprecated" in lines[ln - 1]),
            "argument": "required" if shorts.get(c) or any(a for _, a, _, _ in lg) else "none",
            "build_condition_long": " | ".join(sorted({cd for _, _, _, cd in lg})),
            "build_condition_handler": h.get("cond", ""),
            "handler_source": "src/nano.c:%s" % h["line"] if h else "",
            "long_source": " ".join("src/nano.c:%d" % ln for _, _, ln, _ in lg),
            "effect_c": effect,
            "help_text": u.get("desc", ""),
            "help_source": "src/nano.c:%s" % u["line"] if u else "",
            "help_condition": u.get("cond", ""),
            "help_restricted": u.get("restricted", ""),
            "spec_section": "01-cli.md",
        })
    write_csv("cli-options.csv", rows)
