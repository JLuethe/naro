"""nanorc inventories: data/nanorc-options.csv, data/nanorc-commands.csv,
data/color-names.csv, data/interface-elements.csv.

Reference revision: 6ed285c3ec7a1d228def4d4e7021c6ba269f620c
Sources: src/rcfile.c rcopts[] (41-143), parse_rcfile() (1379-1689),
color tables (1017-1038), definitions.h element enum (311-325).
"""

import os
import re

from ifdefs import conditions

SRC = os.path.expanduser("~/src/nano-ref")

# Argument-taking options: validation as implemented in parse_rcfile().
STRING_OPTS = {
    "brackets": ("string", 'copy_of("\\"\')>]}")', "must contain no blank characters", "Non-blank characters required"),
    "fill": ("integer", "-8 (COLUMNS_FROM_EOL); i.e. window width minus 8", "parse_num(); on failure fill=-8", "Requested fill size \"%s\" is invalid"),
    "operatingdir": ("path", "none", "none at parse time; init_operating_dir() dies if unusable", "Invalid operating directory: %s"),
    "punct": ("string", 'copy_of("!.?")', "must contain no blank characters", "Non-blank characters required"),
    "quotestr": ("regex", "^([ \\t]*([!#%:;>|}]|/{2}))+", "compiled at startup; nano dies when invalid", "Bad quoting regex \"%s\": %s"),
    "speller": ("command", "none (then $SPELL, then internal hunspell/spell)", "leading blanks stripped", ""),
    "backupdir": ("path", "none", "init_backup_dir() dies if not an existing directory", "Invalid backup directory: %s"),
    "guidestripe": ("integer > 0", "0 (off)", "parse_num() and > 0; on failure 0", "Guide column \"%s\" is invalid"),
    "matchbrackets": ("string, even char count, no blanks", '"(<[{)>]}"', "no blanks; even number of characters", "Non-blank characters required / Even number of characters required"),
    "tabsize": ("integer > 0", "8", "parse_num() and > 0; on failure -1 (=> 8)", "Requested tab size \"%s\" is invalid"),
    "whitespace": ("two single-column characters", "UTF-8: U+00BB U+00B7; else \">.\"", "exactly 2 characters each 1 column wide", "Two single-column characters required"),
    "wordchars": ("string", "none", "none", ""),
}
COLOR_OPTS = {"titlecolor": "TITLE_BAR", "numbercolor": "LINE_NUMBER", "stripecolor": "GUIDE_STRIPE",
              "scrollercolor": "SCROLL_BAR", "selectedcolor": "SELECTED_TEXT",
              "spotlightcolor": "SPOTLIGHTED", "minicolor": "MINI_INFOBAR",
              "promptcolor": "PROMPT_BAR", "statuscolor": "STATUS_BAR",
              "errorcolor": "ERROR_MESSAGE", "keycolor": "KEY_COMBO", "functioncolor": "FUNCTION_TAG"}

# Equivalent command-line option for each rc option (from nano.c switch and doc).
CLI_EQUIV = {
    "boldtext": "-D", "brackets": "", "breaklonglines": "-b", "casesensitive": "(+c modifier only)",
    "constantshow": "-c", "fill": "-r", "historylog": "-H", "linenumbers": "-l", "magic": "-!",
    "mouse": "-m", "multibuffer": "-F", "newbuffer": "-F", "nohelp": "-x", "nonewlines": "-L",
    "nowrap": "-w", "operatingdir": "-o", "positionlog": "-P", "preserve": "-p", "punct": "",
    "quotestr": "-Q", "quickblank": "-U", "rawsequences": "-K", "rebinddelete": "-d",
    "regexp": "(+r modifier only)", "saveonexit": "-t", "speller": "-s", "afterends": "-y",
    "allow_insecure_backup": "", "atblanks": "-a", "autoindent": "-i", "backup": "-B",
    "backupdir": "-C", "bookstyle": "-O", "colonparsing": "-@", "cutfromcursor": "-k",
    "emptyline": "-e", "guidestripe": "-J", "indicator": "-q", "jumpyscrolling": "-j",
    "locking": "-G", "matchbrackets": "", "minibar": "-_", "noconvert": "-N",
    "showcursor": "-g", "smarthome": "-A", "softwrap": "-S", "solosidescroll": "-1",
    "stateflags": "-%", "tabsize": "-T", "tabstospaces": "-E", "trimblanks": "-M",
    "unix": "-u", "whitespace": "", "whitespacedisplay": "--whitespacedisplay",
    "wordbounds": "-W", "wordchars": "-X", "zap": "-Z", "zero": "-0",
}


def build(write_csv):
    path = os.path.join(SRC, "src/rcfile.c")
    lines = open(path, encoding="utf-8").read().split("\n")
    conds = conditions(path)
    rows = []
    for i in range(40, 143):
        m = re.search(r'\{"(\w+)", (\w+)\}', lines[i])
        if not m:
            continue
        name, flag = m.group(1), m.group(2)
        deprecated = "Deprecated" in lines[i]
        if flag != "0":
            typ, default, valid, msg = "boolean", "unset" if name != "nowrap" else "set (NO_WRAP is set by default)", "set/unset; extra words ignored", ""
        elif name in COLOR_OPTS:
            typ, default, valid, msg = "color combination", "built-in (see 10-nanorc.md)", "[bold,][italic,]fg[,bg]", 'Color "%s" not understood'
        else:
            typ, default, valid, msg = STRING_OPTS.get(name, ("?", "?", "?", ""))
        rows.append({
            "option": name, "type": typ, "flag": flag if flag != "0" else "",
            "interface_element": COLOR_OPTS.get(name, ""),
            "default": default, "validation": valid, "error_template": msg,
            "unsettable": "yes" if flag != "0" else "no (\"Cannot unset option\")",
            "cli_equivalent": CLI_EQUIV.get(name, ""),
            "deprecated": "yes" if deprecated else "",
            "build_condition": conds[i + 1],
            "source": "src/rcfile.c:%d" % (i + 1),
            "spec_section": "10-nanorc.md",
        })
    write_csv("nanorc-options.csv", rows)

    cmds = [
        ("set", "anywhere in nanorc; not in included files", "src/rcfile.c:1511", "ENABLE_NANORC"),
        ("unset", "anywhere in nanorc; not in included files", "src/rcfile.c:1513", "ENABLE_NANORC"),
        ("bind", "nanorc only", "src/rcfile.c:1515", "ENABLE_NANORC"),
        ("unbind", "nanorc only", "src/rcfile.c:1517", "ENABLE_NANORC"),
        ("include", "nanorc only (not inside an included file)", "src/rcfile.c:1507", "ENABLE_COLOR"),
        ("syntax", "nanorc or included file", "src/rcfile.c:1470", "ENABLE_COLOR"),
        ("header", "after syntax", "src/rcfile.c:1476", "ENABLE_COLOR"),
        ("magic", "after syntax; ignored without libmagic", "src/rcfile.c:1479", "ENABLE_COLOR"),
        ("color", "after syntax", "src/rcfile.c:1330", "ENABLE_COLOR"),
        ("icolor", "after syntax", "src/rcfile.c:1332", "ENABLE_COLOR"),
        ("comment", "after syntax; ignored without ENABLE_COMMENT", "src/rcfile.c:1334", "ENABLE_COLOR"),
        ("tabgives", "after syntax", "src/rcfile.c:1338", "ENABLE_COLOR"),
        ("linter", "after syntax", "src/rcfile.c:1340", "ENABLE_COLOR"),
        ("formatter", "after syntax", "src/rcfile.c:1343", "ENABLE_COLOR"),
        ("extendsyntax", "nanorc only", "src/rcfile.c:1420", "ENABLE_COLOR"),
    ]
    write_csv("nanorc-commands.csv", [{"command": c, "where_allowed": w, "source": s,
                                       "build_condition": b, "spec_section": "10-nanorc.md"}
                                      for c, w, s, b in cmds])

    names = re.findall(r'"(\w+)"', " ".join(lines[1018:1030]))
    idx_text = " ".join(lines[1031:1038])
    idx = [x.strip() for x in idx_text[idx_text.index("{") + 1:idx_text.index("}")].split(",")]
    crow = []
    for n, (name, ix) in enumerate(zip(names, idx)):
        crow.append({"name": name, "index_expr": ix, "position": n,
                     "accepts_light_prefix": "yes" if n <= 7 else ("n/a" if n == 8 else "no"),
                     "requires_256_colors": "yes (else default)" if n > 8 else "no",
                     "source": "src/rcfile.c:1019-1038", "spec_section": "10-nanorc.md"})
    write_csv("color-names.csv", crow)
