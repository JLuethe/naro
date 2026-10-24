"""Message inventory: data/messages.csv (+ evidence/messages/*.pot).

Reference revision: 6ed285c3ec7a1d228def4d4e7021c6ba269f620c

1. Regenerates the gettext template from the pinned sources with nano's own
   xgettext options (po/Makevars: --keyword=_ --keyword=N_ --keyword=P_:1,2).
2. Classifies every source reference by the call that displays it
   (statusline importance, statusbar, prompt, stderr, ...).
3. Adds the user-visible strings that are NOT marked for translation
   (literal statusline()/die()/fprintf() texts), found by scanning calls.
"""

import os
import re
import subprocess

SRC = os.path.expanduser("~/src/nano-ref")
SPEC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POT = os.path.join(SPEC, "evidence", "messages", "nano-6ed285c.pot")

CHANNELS = [
    (r"statusline\(\s*(VACUUM|HUSH|REMARK|INFO|NOTICE|AHEM|MILD|ALERT)", "statusline:{0}"),
    (r"statusbar\(", "statusline:HUSH (statusbar)"),
    (r"warn_and_briefly_pause\(", "statusline:ALERT + 1.5s pause"),
    (r"jot_error\(", "stderr-after-exit (rcfile/history error list)"),
    (r"\bdie\(", "stderr + exit(1) (die)"),
    (r"fprintf\(stderr", "stderr"),
    (r"\bprintf\(", "stdout"),
    (r"print_opt\(", "stdout (--help option table)"),
    (r"do_prompt\(", "prompt"),
    (r"ask_user\(", "yes/no prompt"),
    (r"add_to_funcs\(", "help-line tag / help-viewer description"),
    (r"add_undo\(", "undo/redo noun"),
    (r"titlebar|prefix =|path = _|state = _", "title bar"),
]


def regenerate_pot():
    os.makedirs(os.path.dirname(POT), exist_ok=True)
    files = [l.strip() for l in open(os.path.join(SRC, "po/POTFILES.in"))
             if l.strip() and not l.startswith("#") and l.strip().startswith("src/")]
    subprocess.run(["xgettext", "--keyword=_", "--keyword=N_", "--keyword=P_:1,2",
                    "--add-comments=TRANSLATORS:", "--from-code=UTF-8", "--no-wrap",
                    "--package-name=nano", "--package-version=6ed285c3",
                    "-o", POT] + files, cwd=SRC, check=True)


def parse_pot():
    entries = []
    cur = {"comments": [], "refs": [], "flags": "", "msgctxt": None, "msgid": None,
           "msgid_plural": None}
    field = None

    def unq(s):
        s = s.strip()[1:-1]
        return bytes(s, "utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8")
    for line in open(POT, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("#."):
            cur["comments"].append(line[2:].strip())
        elif line.startswith("#:"):
            cur["refs"] += line[2:].split()
        elif line.startswith("#,"):
            cur["flags"] = line[2:].strip()
        elif line.startswith("msgctxt "):
            cur["msgctxt"] = unq(line[8:]); field = "msgctxt"
        elif line.startswith("msgid_plural "):
            cur["msgid_plural"] = unq(line[13:]); field = "msgid_plural"
        elif line.startswith("msgid "):
            cur["msgid"] = unq(line[6:]); field = "msgid"
        elif line.startswith("msgstr"):
            field = None
        elif line.startswith('"') and field:
            cur[field] += unq(line)
        elif line == "":
            if cur["msgid"]:
                entries.append(cur)
            cur = {"comments": [], "refs": [], "flags": "", "msgctxt": None, "msgid": None,
                   "msgid_plural": None}
    if cur["msgid"]:
        entries.append(cur)
    return entries


_cache = {}


def source(name):
    if name not in _cache:
        _cache[name] = open(os.path.join(SRC, name), encoding="utf-8").read().split("\n")
    return _cache[name]


SPECIAL = [  # (file, first line, last line, label) for indirectly displayed strings
    ("src/global.c", 585, 586, "help-line tag (Exit/Close)"),
    ("src/global.c", 590, 760, "help-viewer description (gist) and help-line tag"),
    ("src/global.c", 1629, 1666, "toggle description (status bar REMARK and help viewer)"),
    ("src/help.c", 40, 210, "help-viewer introduction text"),
    ("src/help.c", 211, 300, "help-viewer text"),
    ("src/winio.c", 3597, 3726, "credits crawl (Easter egg)"),
    ("src/text.c", 495, 900, "undo/redo noun (\"Undid %s\" / \"Redid %s\")"),
    ("src/prompt.c", 655, 712, "yes/no prompt answer letters and labels"),
    ("src/files.c", 1150, 1200, "prompt"),
    ("src/files.c", 2060, 2100, "prompt (Write Out) and prompt modifiers"),
    ("src/search.c", 95, 110, "prompt (Search) and prompt modifiers"),
    ("src/browser.c", 150, 230, "file browser size/type column"),
    ("src/winio.c", 2150, 2210, "minibar"),
    ("src/files.c", 295, 295, "yes/no prompt (lock file)"),
    ("src/files.c", 2207, 2207, "yes/no prompt (overwrite)"),
    ("src/files.c", 2609, 2609, "tab-completion list in edit window"),
    ("src/rcfile.c", 193, 197, "statusline:ALERT at startup (startup_problem)"),
    ("src/rcfile.c", 201, 201, "stderr-after-exit prefix of rcfile errors"),
    ("src/text.c", 2220, 2220, "undo/redo noun (\"Undid %s\" / \"Redid %s\")"),
    ("src/text.c", 2834, 2834, "yes/no prompt (linter)"),
]


def channel_for(ref):
    fname, ln = ref.rsplit(":", 1)
    ln = int(ln)
    for f, a, b, label in SPECIAL:
        if f == fname and a <= ln <= b:
            return label
    lines = source(fname)
    window = " ".join(lines[max(0, ln - 6):ln])
    best = None
    bestpos = -1
    for pat, label in CHANNELS:
        for m in re.finditer(pat, window):
            if m.start() > bestpos:
                bestpos = m.start()
                best = label.format(*m.groups()) if m.groups() else label
    return best or "other (see source)"


def literal_messages():
    """User-visible literal strings not marked for translation."""
    rows = []
    pat = re.compile(r'(statusline\(\s*(\w+),\s*|die\(|fprintf\(stderr,\s*|printf\(|statusbar\()"((?:[^"\\]|\\.)*)"')
    for fname in sorted(os.listdir(os.path.join(SRC, "src"))):
        if not fname.endswith(".c"):
            continue
        for ln, line in enumerate(source("src/" + fname), 1):
            for m in pat.finditer(line):
                text = m.group(3)
                if text in ("%s", "\\n", "\\n%s\\n", " %s", "%s\\n") or text.startswith("\\x1B"):
                    continue
                rows.append({"msgid": text, "kind": "literal (not translatable)",
                             "refs": "src/%s:%d" % (fname, ln),
                             "channel": ("statusline:%s" % m.group(2)) if m.group(2) else channel_for("src/%s:%d" % (fname, ln))})
    return rows


def build(write_csv):
    regenerate_pot()
    entries = parse_pot()
    rows = []
    n = 0
    for e in entries:
        n += 1
        channels = sorted({channel_for(r) for r in e["refs"]})
        args = re.findall(r"%[-0-9*.]*(?:z|l|h)?[sdiuxXcp%]", e["msgid"])
        rows.append({
            "msg_id": "MSG-%03d" % n,
            "msgid": e["msgid"],
            "msgid_plural": e["msgid_plural"] or "",
            "msgctxt": e["msgctxt"] or "",
            "format_flags": e["flags"],
            "substitutions": " ".join(a for a in args if a != "%%"),
            "sources": " ".join(e["refs"]),
            "display_channels": "; ".join(channels),
            "translator_comment": " ".join(e["comments"]),
            "translatable": "yes",
            "owner": "nano",
            "spec_section": "14-messages-and-i18n.md",
        })
    for r in literal_messages():
        n += 1
        rows.append({"msg_id": "MSG-%03d" % n, "msgid": r["msgid"], "msgid_plural": "",
                     "msgctxt": "", "format_flags": "", "substitutions":
                     " ".join(re.findall(r"%[-0-9*.]*(?:z|l)?[sdiuxXc]", r["msgid"])),
                     "sources": r["refs"], "display_channels": r["channel"],
                     "translator_comment": "", "translatable": "no", "owner": "nano",
                     "spec_section": "14-messages-and-i18n.md"})
    write_csv("messages.csv", rows)

    # translation catalogs
    cats = []
    for po in sorted(os.listdir(os.path.join(SRC, "po"))):
        if not po.endswith(".po"):
            continue
        res = subprocess.run(["msgfmt", "--statistics", "-o", "/dev/null", os.path.join(SRC, "po", po)],
                             stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        stat = res.stderr.strip()
        nums = {k: 0 for k in ("translated", "fuzzy", "untranslated")}
        for num, kind in re.findall(r"(\d+) (translated|fuzzy|untranslated)", stat):
            nums[kind] = int(num)
        header = open(os.path.join(SRC, "po", po), encoding="utf-8", errors="replace").read(4000)
        plural = re.search(r'Plural-Forms: ([^\\]+)', header)
        cats.append({"catalog": "po/" + po, "language": po[:-3], **nums,
                     "plural_forms": plural.group(1).strip() if plural else "",
                     "installed_mo": "share/locale/%s/LC_MESSAGES/nano.mo" % po[:-3]})
    write_csv("translation-catalogs.csv", cats)
