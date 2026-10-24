"""Miscellaneous inventories.

Reference revision: 6ed285c3ec7a1d228def4d4e7021c6ba269f620c

  data/menus.csv             menu contexts (definitions.h, rcfile.c menunames)
  data/escape-sequences.csv  sequences decoded by nano itself (winio.c 443-920)
  data/toggles.csv           toggles (global.c add_toggle, epithet_of_flag)
  data/syntaxes.csv          bundled syntax definitions (syntax/*.nanorc)
  data/undo-types.csv        undo record kinds (definitions.h, text.c)
"""

import glob
import os
import re

from ifdefs import conditions

SRC = os.path.expanduser("~/src/nano-ref")

MENU_ROWS = [
    ("MMAIN", 0, "main", "edit window", "yes"),
    ("MWHEREIS", 1, "search", "Search prompt (^W / ^F / ^B)", "yes"),
    ("MREPLACE", 2, "replace", "Search (to replace) prompt", "yes"),
    ("MREPLACEWITH", 3, "replacewith", "Replace with prompt", "yes"),
    ("MGOTOLINE", 4, "gotoline", "Go To Line prompt", "yes"),
    ("MWRITEFILE", 5, "writeout", "Write to File prompt", "yes"),
    ("MINSERTFILE", 6, "insert", "File to insert prompt", "yes"),
    ("MEXECUTE", 7, "execute", "Command to execute prompt", "yes"),
    ("MHELP", 8, "help", "help viewer", "yes"),
    ("MSPELL", 9, "spell", "Edit a replacement prompt (spell checker)", "yes"),
    ("MBROWSER", 10, "browser", "file browser", "yes"),
    ("MWHEREISFILE", 11, "whereisfile", "Search prompt in file browser", "yes"),
    ("MGOTODIR", 12, "gotodir", "Go To Directory prompt in file browser", "yes"),
    ("MYESNO", 13, "yesno", "Yes/No/All questions", "yes"),
    ("MLINTER", 14, "linter", "linter message navigation", "yes"),
    ("MFINDINHELP", 15, "", "Search prompt inside the help viewer", "no rc name (only via 'all')"),
]


def build(write_csv):
    write_csv("menus.csv", [{"context": c, "bit": b, "mask": hex(1 << b), "rc_menu_name": n,
                             "where": w, "rc_addressable": a, "source": "src/definitions.h:254-269; src/rcfile.c:496-506",
                             "spec_section": "02-keybindings.md#contexts"}
                            for c, b, n, w, a in MENU_ROWS])

    path = os.path.join(SRC, "src/winio.c")
    lines = open(path, encoding="utf-8").read().split("\n")
    conds = conditions(path)
    rows = []
    for i in range(442, 920):
        for m in re.finditer(r"Esc (O|\[) ([^=]+?) == ([^*]+?)(?:\*/|$)", lines[i]):
            seq = "ESC %s %s" % (m.group(1), m.group(2).strip())
            meaning = m.group(3).strip().rstrip(".")
            # find the nearest following 'return' within 12 lines
            ret = ""
            for k in range(i, min(i + 14, len(lines))):
                r = re.search(r"return ([^;]+);", lines[k])
                if r:
                    ret = r.group(1)
                    break
            rows.append({"sequence": seq, "documented_meaning": meaning, "result_c": ret,
                         "decoder": "convert_SS3_sequence" if i < 583 else "convert_CSI_sequence",
                         "source": "src/winio.c:%d" % (i + 1), "build_condition": conds[i + 1],
                         "applies_when": "only when ncurses did not translate the sequence (unknown to terminfo) or with --rawsequences",
                         "spec_section": "03-terminal-input.md"})
    write_csv("escape-sequences.csv", rows)

    gl = open(os.path.join(SRC, "src/global.c"), encoding="utf-8").read().split("\n")
    gconds = conditions(os.path.join(SRC, "src/global.c"))
    ep = {}
    for i in range(1630, 1666):
        m = re.search(r"case (\w+):", gl[i])
        if m:
            d = re.search(r'N_\("([^"]+)"\)', gl[i + 1] + gl[i + 2] + gl[i + 3])
            ep[m.group(1)] = d.group(1) if d else ""
    rc = open(os.path.join(SRC, "src/rcfile.c"), encoding="utf-8").read()
    trows = []
    for i, l in enumerate(gl, 1):
        m = re.search(r'add_toggle\("([^"]+)", (\w+)\);', l)
        if m:
            rcname = re.findall(r'!strcmp\(input, "(\w+)"\)\)\s*\n\s*s->toggle = %s;' % m.group(2), rc)
            trows.append({"key": m.group(1), "flag": m.group(2), "description": ep.get(m.group(2), ""),
                          "rc_function": " ".join(rcname),
                          "contexts": "ALMOST_ALL ((MMOST|MBROWSER|MYESNO) & ~MFINDINHELP)" if m.group(2) == "NO_HELP" else "MMAIN",
                          "legacy": "yes" if "Legacy" in l else "",
                          "build_condition": gconds[i], "source": "src/global.c:%d" % i,
                          "spec_section": "05-buffer-and-editing.md#toggles; 12-features.md"})
    write_csv("toggles.csv", trows)

    srows = []
    for f in sorted(glob.glob(os.path.join(SRC, "syntax", "*.nanorc")) + glob.glob(os.path.join(SRC, "syntax", "extra", "*.nanorc"))):
        text = open(f, encoding="utf-8", errors="replace").read().split("\n")
        for ln, l in enumerate(text, 1):
            m = re.match(r'syntax\s+("?)([^"\s]+)\1\s*(.*)$', l)
            if m:
                name, rest = m.group(2), m.group(3)
                body = text[ln:]
                stop = next((k for k, x in enumerate(body) if x.startswith("syntax ")), len(body))
                body = body[:stop]
                get = lambda kw: " ".join(x[len(kw) + 1:] for x in body if x.startswith(kw + " "))
                srows.append({
                    "file": os.path.relpath(f, SRC), "line": ln, "syntax": name,
                    "extensions": rest, "header": get("header"), "magic": get("magic"),
                    "comment": get("comment"), "linter": get("linter"),
                    "formatter": get("formatter"), "tabgives": get("tabgives"),
                    "color_rules": sum(1 for x in body if re.match(r"i?color ", x)),
                    "multiline_rules": sum(1 for x in body if re.match(r"i?color .*start=", x)),
                    "installed": "no (extra/)" if "/extra/" in f else "yes",
                    "license_line": next((x for x in text[:8] if "icense" in x), "").strip("# "),
                    "spec_section": "11-syntax-highlighting.md#bundled"})
    write_csv("syntaxes.csv", srows)

    utypes = [
        ("ADD", "typed or injected text", "inject() nano.c:1488-1491; do_wrap", "Undid/Redid addition", ""),
        ("ENTER", "line break", "do_enter() text.c:900", "line break", ""),
        ("BACK", "Backspace deletion (becomes JOIN at line start)", "expunge(BACK)", "deletion / line join", "WAS_BACKSPACE_AT_EOF"),
        ("DEL", "Delete deletion (becomes JOIN at line end)", "expunge(DEL)", "deletion / line join", ""),
        ("JOIN", "joining of two lines", "add_undo BACK/DEL morph", "line join", "WAS_BACKSPACE_AT_EOF"),
        ("REPLACE", "one replacement of a search match", "do_replace_loop search.c:624", "replacement", ""),
        ("SPLIT_BEGIN", "start of automatic hard wrap (inserted below the triggering item)", "do_wrap text.c:1276", "addition", "ENABLE_WRAPPING"),
        ("SPLIT_END", "end of automatic hard wrap", "do_wrap text.c:1385", "addition", "ENABLE_WRAPPING"),
        ("INDENT", "indent of line(s)", "do_indent text.c:145", "indent", ""),
        ("UNINDENT", "unindent of line(s)", "do_unindent text.c:250", "unindent", ""),
        ("COMMENT", "comment line(s)", "do_comment text.c:405", "comment", "ENABLE_COMMENT"),
        ("UNCOMMENT", "uncomment line(s)", "do_comment text.c:405", "uncomment", "ENABLE_COMMENT"),
        ("PREFLIGHT", "(internal action code, never stored)", "comment_line", "", "ENABLE_COMMENT"),
        ("ZAP", "zap (erase without cutbuffer)", "zap_text cut.c:593", "erasure", ""),
        ("CUT", "cut (line, region, chopped word, justify extraction, tool replacement)", "cut_text cut.c:548 and others", "cut", ""),
        ("CUT_TO_EOF", "cut till end of file", "cut_till_eof cut.c:575; replace_buffer", "cut", ""),
        ("COPY", "(last_action marker only; not stored as an undo item)", "copy_text cut.c:721", "", ""),
        ("PASTE", "paste of cutbuffer, or re-insertion of justified text", "paste_text cut.c:745", "paste", ""),
        ("INSERT", "inserted file or command output", "read_file files.c:677", "insertion", ""),
        ("COUPLE_BEGIN", "start of compound operation (justification, filtering, spelling correction, formatting)", "text.c:1782 etc.", "<operation name>", ""),
        ("COUPLE_END", "end of compound operation", "text.c:2002 etc.", "<operation name>", ""),
        ("OTHER", "(last_action marker only)", "", "", ""),
    ]
    write_csv("undo-types.csv", [{"type": t, "meaning": m, "created_by": c, "message_noun": n,
                                  "flags_or_condition": f, "source": "src/definitions.h:297-308; src/text.c:495-1230",
                                  "spec_section": "06-undo-redo.md"} for t, m, c, n, f in utypes])
