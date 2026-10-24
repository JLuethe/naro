"""Compile-time feature inventory: data/build-features.csv.

Reference revision: 6ed285c3ec7a1d228def4d4e7021c6ba269f620c
Sources: configure.ac option blocks, src/definitions.h derived macros,
and #ifdef usage counts across src/*.c src/*.h.
"""

import glob
import os
import re

SRC = os.path.expanduser("~/src/nano-ref")

# feature: (configure switch, macro, tiny default, dependencies/conflicts, observable scope)
FEATURES = [
    ("browser", "--disable-browser", "ENABLE_BROWSER", "off", "",
     "file browser (^T at Read/Write prompts), MBROWSER/MWHEREISFILE/MGOTODIR menus"),
    ("color", "--disable-color", "ENABLE_COLOR", "off", "requires nanorc; --disable-nanorc disables color silently",
     "syntax highlighting, interface colors, syntax/include/extendsyntax/color/icolor/header/magic/comment/tabgives/linter/formatter commands, -Y, -z"),
    ("comment", "--disable-comment", "ENABLE_COMMENT", "cannot enable with tiny", "",
     "comment/uncomment (M-3), 'comment' syntax command effect, COMMENT/UNCOMMENT undo types"),
    ("extra", "--disable-extra", "ENABLE_EXTRA", "off", "",
     "credits Easter egg (^X Y 'zzy'), M-& ncurses version"),
    ("formatter", "--disable-formatter", "ENABLE_FORMATTER", "off", "requires color+nanorc",
     "formatter tool (^T^O in Execute), 'formatter' syntax command"),
    ("help", "--disable-help", "ENABLE_HELP", "off", "requires multibuffer",
     "help viewer (^G/F1), help-line descriptions; without it ^G says '^W = Ctrl+W    M-W = Alt+W'"),
    ("histories", "--disable-histories", "ENABLE_HISTORIES", "off", "",
     "search/replace/execute histories, Up/Down/^P/^N history in prompts, -H, -P, history files"),
    ("justify", "--disable-justify", "ENABLE_JUSTIFY", "off", "",
     "^J justify, M-J full justify, paragraph movement M-( M-) M-9 M-0, -Q, quotestr/punct/brackets options"),
    ("libmagic", "--disable-libmagic", "HAVE_LIBMAGIC", "off (unless --enable-libmagic)", "requires color+nanorc; needs libmagic+zlib",
     "-! / set magic, 'magic' syntax command effect"),
    ("linter", "--disable-linter", "ENABLE_LINTER", "off", "requires color+nanorc",
     "linter (^T^Y), MLINTER menu, 'linter' syntax command"),
    ("linenumbers", "--disable-linenumbers", "ENABLE_LINENUMBERS", "off", "",
     "-l, M-N toggle (in tiny M-N toggles numbers if enabled)"),
    ("mouse", "--disable-mouse", "ENABLE_MOUSE", "off", "requires ncurses mouse (NCURSES_MOUSE_VERSION)",
     "-m, M-M toggle, mouse clicks/wheel"),
    ("multibuffer", "--disable-multibuffer", "ENABLE_MULTIBUFFER", "off", "",
     "several files, M-< M-> M-, M-. M-Left/Right, -F, Read-into-new-buffer; without it only one file may be named"),
    ("nanorc", "--disable-nanorc", "ENABLE_NANORC", "off", "",
     "nanorc files, -I, -f, bind/unbind, string binds"),
    ("operatingdir", "--disable-operatingdir", "ENABLE_OPERATINGDIR", "off", "",
     "-o / set operatingdir confinement"),
    ("speller", "--disable-speller", "ENABLE_SPELLER", "off", "",
     "spell check (^T^T, F12), -s, $SPELL"),
    ("tabcomp", "--disable-tabcomp", "ENABLE_TABCOMP", "off", "",
     "Tab completion of filenames, history completion in search prompts"),
    ("wordcomp", "--disable-wordcomp", "ENABLE_WORDCOMPLETION", "cannot enable with tiny", "",
     "^] word completion"),
    ("wrapping", "--disable-wrapping", "ENABLE_WRAPPING", "off", "",
     "hard wrapping (-b, -w, M-L), SPLIT_BEGIN/SPLIT_END undo"),
    ("nls", "--disable-nls", "ENABLE_NLS", "on", "gettext",
     "translated messages; affects yes/no letters"),
    ("utf8", "--enable-utf8/--disable-utf8", "ENABLE_UTF8", "auto", "wide curses + iswalpha etc.",
     "multibyte handling; using_utf8 additionally requires a UTF-8 locale at run time"),
    ("debug", "--enable-debug", "DEBUG", "off", "",
     "debug output on stderr, asserts; disables crash handler"),
    ("tiny", "--enable-tiny", "NANO_TINY", "-", "",
     "removes undo, mark, toggles, softwrap, indent, many keys; see 12-features.md"),
    ("altrcname", "--enable-altrcname=NAME", "RCFILE_NAME", "-", "",
     "changes ~/.nanorc and XDG rc file names"),
]

DERIVED = [
    ("ENABLED_WRAPORJUSTIFY", "ENABLE_WRAPPING || ENABLE_JUSTIFY", "src/definitions.h:95-97",
     "--fill/-r, --trimblanks/-M, wrap_at computation"),
    ("NCURSES_MOUSE_VERSION", "ncurses provides mouse API", "src/definitions.h:91-93",
     "undefines ENABLE_MOUSE when absent"),
    ("HAVE_SET_ESCDELAY", "ncurses has set_escdelay", "src/nano.c:2511-2514", "ESC delay 50 ms"),
    ("HAVE_DEFINE_KEY", "ncurses has define_key", "src/nano.c:2492-2496", "bracketed paste sequences mapped to keycodes"),
    ("HAVE_KEY_DEFINED", "ncurses has key_defined", "src/nano.c:1241-1254", "modified-key codes taken from terminfo"),
    ("HAVE_USE_DEFAULT_COLORS", "ncurses has use_default_colors", "src/color.c:38-41", "'normal'/default colors"),
    ("HAVE_TERM_H", "term.h available", "src/global.c:761-767", "help key ^H vs ^N in modern bindings"),
    ("REVISION", "build in git checkout", "src/winio.c:34-38, src/nano.c:654-658", "version banner and title bar branding"),
]


def count_uses(macro):
    n = 0
    for f in glob.glob(os.path.join(SRC, "src", "*.[ch]")):
        n += len(re.findall(r"#\s*(?:if|ifdef|ifndef|elif).*\b%s\b" % macro, open(f, encoding="utf-8").read()))
    return n


def build(write_csv):
    import json
    ref_cfg = {}
    for prof in ("default", "tiny"):
        path = os.path.expanduser("~/src/nano-build/%s/config.h" % prof)
        ref_cfg[prof] = open(path).read() if os.path.exists(path) else ""
    rows = []
    for name, switch, macro, tiny, deps, scope in FEATURES:
        rows.append({
            "feature": name, "configure_switch": switch, "macro": macro,
            "default_build": "on" if re.search(r"#define %s\b" % macro, ref_cfg["default"]) else "off",
            "tiny_build": "on" if re.search(r"#define %s\b" % macro, ref_cfg["tiny"]) else "off",
            "tiny_default": tiny, "dependencies": deps, "observable_scope": scope,
            "conditional_blocks_in_src": count_uses(macro),
            "source": "configure.ac", "spec_section": "12-features.md#build-features",
        })
    for macro, meaning, src, scope in DERIVED:
        rows.append({"feature": "(derived) " + macro, "configure_switch": "", "macro": macro,
                     "default_build": "on" if re.search(r"#define %s\b" % macro, ref_cfg["default"]) or macro in ("ENABLED_WRAPORJUSTIFY", "NCURSES_MOUSE_VERSION") else "off",
                     "tiny_build": "on" if re.search(r"#define %s\b" % macro, ref_cfg["tiny"]) or macro == "NCURSES_MOUSE_VERSION" else "off",
                     "tiny_default": "", "dependencies": meaning, "observable_scope": scope,
                     "conditional_blocks_in_src": count_uses(macro), "source": src,
                     "spec_section": "12-features.md#build-features"})
    write_csv("build-features.csv", rows)
