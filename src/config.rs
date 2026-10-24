//! Startup, nanorc parsing, syntax definitions and key table ownership.
use crate::{
    bytes,
    generated::*,
    native::{self, Regex},
};
use std::{
    collections::HashMap,
    ffi::{CString, OsString},
    os::unix::ffi::{OsStrExt, OsStringExt},
    path::{Path, PathBuf},
};
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct Style {
    pub bits: i32,
    pub fg: i32,
    pub bg: i32,
}
impl Style {
    pub const NORMAL: Self = Self {
        bits: 0,
        fg: -1,
        bg: -1,
    };
    pub fn reverse() -> Self {
        Self {
            bits: 4,
            ..Self::NORMAL
        }
    }
}
#[derive(Debug)]
pub struct Rule {
    pub start: Regex,
    pub end: Option<Regex>,
    pub style: Style,
}
#[derive(Debug, Default)]
pub struct Syntax {
    pub source: Option<(PathBuf, usize)>,
    pub augmentations: Vec<(PathBuf, usize, String, String)>,
    pub seen_color: bool,
    pub loaded: bool,
    pub name: String,
    pub files: Vec<Regex>,
    pub headers: Vec<Regex>,
    pub magic: Vec<Regex>,
    pub rules: Vec<Rule>,
    pub comment: Option<Vec<u8>>,
    pub tab: Option<Vec<u8>>,
    pub linter: Option<String>,
    pub formatter: Option<String>,
}
#[derive(Debug)]
pub struct Config {
    pub flags: u64,
    pub cli_flags: u64,
    pub tab: usize,
    pub fill: isize,
    pub guide: usize,
    pub strings: HashMap<String, Vec<u8>>,
    pub colors: HashMap<String, Style>,
    pub keys: Vec<Binding>,
    pub funcs: Vec<Function>,
    pub syntaxes: Vec<Syntax>,
    pub errors: Vec<String>,
    pub error_file: Option<PathBuf>,
    pub ignore: bool,
    pub rc: Option<PathBuf>,
    pub operands: Vec<Vec<u8>>,
    pub utf8: bool,
    pub shifted: bool,
    pub hardwrap: Option<bool>,
    pub preserve_cli: bool,
    pub provided: u8,
}
impl Config {
    pub fn new(utf8: bool) -> Self {
        let (keys, funcs) = keymap(if utf8 { "default-utf8" } else { "default-C" });
        Self {
            flags: 1 << NO_WRAP,
            cli_flags: 0,
            tab: 8,
            fill: -8,
            guide: 0,
            strings: HashMap::new(),
            colors: HashMap::new(),
            keys,
            funcs,
            syntaxes: Vec::new(),
            errors: Vec::new(),
            error_file: None,
            ignore: false,
            rc: None,
            operands: Vec::new(),
            utf8,
            shifted: false,
            hardwrap: None,
            preserve_cli: false,
            provided: 0,
        }
    }
    pub fn on(&self, f: usize) -> bool {
        self.flags & (1u64 << f) != 0
    }
    pub fn set(&mut self, f: usize, b: bool) {
        if b {
            self.flags |= 1u64 << f;
        } else {
            self.flags &= !(1u64 << f);
        }
    }
    pub fn toggle(&mut self, f: usize) {
        self.flags ^= 1u64 << f;
    }
    pub fn enc(&self) -> bytes::Encoding {
        bytes::Encoding {
            utf8: self.utf8,
            tab: self.tab,
        }
    }
    pub fn value(&self, k: &str) -> Vec<u8> {
        self.strings.get(k).cloned().unwrap_or_default()
    }
    pub fn style(&self, k: &str) -> Style {
        if unsafe { native::nr_colors() } <= 0 {
            return match k {
                "functioncolor" | "scrollercolor" => Style::NORMAL,
                "stripecolor" => Style::reverse(),
                _ => {
                    if self.on(BOLD_TEXT) {
                        Style {
                            bits: 1,
                            ..Style::NORMAL
                        }
                    } else {
                        Style::reverse()
                    }
                }
            };
        }
        if let Some(s) = self.colors.get(k) {
            return *s;
        }
        let high = if self.on(BOLD_TEXT) {
            Style {
                bits: 1,
                ..Style::NORMAL
            }
        } else {
            Style::reverse()
        };
        match k {
            "functioncolor" | "scrollercolor" => Style::NORMAL,
            "stripecolor" => Style::reverse(),
            "spotlightcolor" => {
                if std::env::var_os("NO_COLOR").is_some() && self.colors.is_empty() {
                    Style::reverse()
                } else {
                    Style {
                        bits: 0,
                        fg: 0,
                        bg: 11,
                    }
                }
            }
            "errorcolor" => {
                if std::env::var_os("NO_COLOR").is_some() && self.colors.is_empty() {
                    Style::reverse()
                } else {
                    Style {
                        bits: 1,
                        fg: 7,
                        bg: 1,
                    }
                }
            }
            _ => high,
        }
    }
    pub fn parse_cli(&mut self) -> Result<Option<i32>, String> {
        let args: Vec<CString> = std::env::args_os()
            .map(|a| native::cstr(a.as_bytes()))
            .collect();
        let mut ptrs: Vec<*mut std::ffi::c_char> = args
            .iter()
            .map(|s| s.as_ptr() as *mut _)
            .chain(std::iter::once(std::ptr::null_mut()))
            .collect();
        let argv0 = args[0].as_bytes();
        if Path::new(std::ffi::OsStr::from_bytes(argv0))
            .file_name()
            .is_some_and(|n| n.as_bytes().starts_with(b"r"))
        {
            self.set(RESTRICTED, true);
        }
        loop {
            let c = unsafe { native::nr_option(args.len() as i32, ptrs.as_mut_ptr()) };
            if c < 0 {
                break;
            }
            let arg = unsafe { native::from_c(native::nr_optarg()) };
            let ch = if c == 0x700 {
                '\0'
            } else {
                char::from_u32(c as u32).unwrap_or('\0')
            };
            match ch {
                'h' => {
                    print!(
                        "{}",
                        if self.on(RESTRICTED) {
                            include_str!("../assets/help-restricted.txt")
                        } else {
                            include_str!("../assets/help.txt")
                        }
                    );
                    return Ok(Some(0));
                }
                'V' => {
                    println!(
                        " GNU nano, version 9.3\n (C) 2026 the Free Software Foundation and various contributors\n Compiled options: --enable-utf8"
                    );
                    return Ok(Some(0));
                }
                'z' => {
                    self.load_rc();
                    if !self.syntaxes.is_empty() {
                        println!("Available syntaxes:");
                        let mut width = 0;
                        for s in self.syntaxes.iter().rev() {
                            if width > 45 {
                                println!();
                                width = 0;
                            }
                            print!(" {}", s.name);
                            width += self.enc().breadth(s.name.as_bytes());
                        }
                        println!();
                    }
                    return Ok(Some(0));
                }
                '?' => {
                    println!(
                        "Type '{} -h' for a list of available options.",
                        bytes::text(argv0)
                    );
                    return Ok(Some(1));
                }
                'I' => self.ignore = true,
                'f' => self.rc = Some(path(&arg)),
                'T' | 'J' | 'r' => {
                    self.provided |= match ch {
                        'T' => 1,
                        'r' => 2,
                        _ => 4,
                    };
                    let val = std::str::from_utf8(&arg).ok().and_then(parse_num);
                    if val.is_none() || (ch != 'r' && val.unwrap() <= 0) {
                        return Err(format!(
                            "{} \"{}\" is invalid",
                            match ch {
                                'T' => "Requested tab size",
                                'J' => "Guide column",
                                _ => "Requested fill size",
                            },
                            bytes::text(&arg)
                        ));
                    }
                    let v = val.unwrap();
                    match ch {
                        'T' => self.tab = v as usize,
                        'J' => self.guide = v as usize,
                        _ => self.fill = v as isize,
                    };
                }
                'C' | 'Q' | 'X' | 'Y' | 'o' | 's' => {
                    self.strings.insert(
                        match ch {
                            'C' => "backupdir",
                            'Q' => "quotestr",
                            'X' => "wordchars",
                            'Y' => "syntax",
                            'o' => "operatingdir",
                            _ => "speller",
                        }
                        .into(),
                        arg,
                    );
                }
                'b' | 'w' => {
                    self.hardwrap = Some(ch == 'b');
                    self.set(BREAK_LONG_LINES, ch == 'b');
                }
                '\0' if c == 0x700 => self.set(WHITESPACE_DISPLAY, true),
                _ => {
                    let flag = match ch {
                        'A' => SMART_HOME,
                        'B' => MAKE_BACKUP,
                        'D' => BOLD_TEXT,
                        'E' => TABS_TO_SPACES,
                        'F' => NEW_BUFFER,
                        'G' => LOCKING,
                        'H' => HISTORYLOG,
                        'K' => RAW_SEQUENCES,
                        'L' => NO_NEWLINES,
                        'M' => TRIM_BLANKS,
                        'N' => NO_CONVERT,
                        'O' => BOOKSTYLE,
                        'P' => POSITIONLOG,
                        'R' => RESTRICTED,
                        'S' => SOFTWRAP,
                        'U' => QUICK_BLANK,
                        'W' => WORD_BOUNDS,
                        'Z' => LET_THEM_ZAP,
                        'a' => AT_BLANKS,
                        'c' => CONSTANT_SHOW,
                        'd' => REBIND_DELETE,
                        'e' => EMPTY_LINE,
                        'g' => SHOW_CURSOR,
                        'i' => AUTOINDENT,
                        'j' => JUMPY_SCROLLING,
                        'k' => CUT_FROM_CURSOR,
                        'l' => LINE_NUMBERS,
                        'm' => USE_MOUSE,
                        'n' => NOREAD_MODE,
                        'p' => PRESERVE,
                        'q' => INDICATOR,
                        't' => SAVE_ON_EXIT,
                        'u' => MAKE_IT_UNIX,
                        'v' => VIEW_MODE,
                        'x' => NO_HELP,
                        'y' => AFTER_ENDS,
                        '!' => USE_MAGIC,
                        '@' => COLON_PARSING,
                        '%' => STATEFLAGS,
                        '_' => MINIBAR,
                        '0' => ZERO,
                        '1' => SOLO_SIDESCROLL,
                        '/' => MODERN_BINDINGS,
                        _ => return Err("Invalid option".into()),
                    };
                    self.set(flag, true);
                }
            }
        }
        self.operands = ptrs[unsafe { native::nr_optind() } as usize..args.len()]
            .iter()
            .map(|p| unsafe { native::from_c(*p) })
            .collect();
        self.cli_flags = self.flags & !(1u64 << NO_WRAP);
        self.preserve_cli = self.on(PRESERVE);
        let profile = if self.on(MODERN_BINDINGS) {
            if std::env::var("TERM").unwrap_or_default() == "vt220" {
                "default-modern-vt220"
            } else {
                "default-modern"
            }
        } else if self.on(RESTRICTED) {
            "default-restricted"
        } else if self.on(VIEW_MODE) {
            "default-view"
        } else if self.on(PRESERVE) {
            "default-preserve"
        } else if self.on(SAVE_ON_EXIT) {
            "default-saveonexit"
        } else if self.utf8 {
            "default-utf8"
        } else {
            "default-C"
        };
        (self.keys, self.funcs) = keymap(profile);
        if self.on(MODERN_BINDINGS) && self.preserve_cli {
            self.keys
                .retain(|k| !(k.key == 19 && k.menus == EXEC || k.key == 17 && k.menus == WRITE));
        }
        Ok(None)
    }
    pub fn load_rc(&mut self) {
        if self.ignore {
            return;
        }
        if let Some(p) = self.rc.clone() {
            if !p.exists() {
                self.errors.push("Specified rcfile does not exist".into());
                return;
            }
            self.read_rc(&p, false);
            return;
        }
        let home = home_dir();
        let mut paths = Vec::new();
        if let Some(home) = &home {
            paths.push(home.join(".nanorc"));
        }
        if let Some(x) = std::env::var_os("XDG_CONFIG_HOME") {
            paths.push(PathBuf::from(x).join("nano/nanorc"));
        }
        if let Some(home) = &home {
            paths.push(home.join(".config/nano/nanorc"));
        }
        if home.is_none() && std::env::var_os("XDG_CONFIG_HOME").is_none() {
            self.errors
                .push("I can't find my home directory!  Wah!".into());
            self.error_file = Some(PathBuf::from("/etc/nanorc"));
        }
        for p in paths {
            if p.is_file() {
                self.read_rc(&p, false);
                break;
            }
        }
    }
    pub fn finish_startup(&mut self) -> Result<(), String> {
        let cli = self.cli_flags;
        let oldtab = self.tab;
        let oldfill = self.fill;
        let oldguide = self.guide;
        let strings = self.strings.clone();
        self.load_rc();
        if self
            .errors
            .iter()
            .any(|e| e == "Specified rcfile does not exist")
        {
            return Err("Specified rcfile does not exist".into());
        }
        self.flags |= cli;
        if self.provided & 1 != 0 {
            self.tab = oldtab;
        }
        if self.provided & 2 != 0 {
            self.fill = oldfill;
        }
        if self.provided & 4 != 0 {
            self.guide = oldguide;
        }
        let operating_cli = strings.contains_key("operatingdir");
        self.strings.extend(strings);
        if let Some(w) = self.hardwrap {
            self.set(BREAK_LONG_LINES, w);
        } else if !self.on(NO_WRAP) {
            self.set(BREAK_LONG_LINES, true);
        }
        if self.on(RESTRICTED) {
            self.set(MAKE_BACKUP, false);
            self.set(HISTORYLOG, false);
            self.set(POSITIONLOG, false);
            if !operating_cli {
                self.strings.remove("operatingdir");
            }
        }
        if self.on(RAW_SEQUENCES) {
            self.set(USE_MOUSE, false);
        }
        if self.on(MODERN_BINDINGS) {
            self.set(PRESERVE, false);
        }
        if self.on(ZERO) {
            self.set(NO_HELP, true);
        }
        if !self.on(RESTRICTED)
            && let Some(p) = self.strings.get("backupdir")
            && !path(p).is_dir()
        {
            return Err(format!("Invalid backup directory: {}", bytes::text(p)));
        }
        if let Some(p) = self.strings.get("operatingdir") {
            let p = expand(p);
            let full = std::fs::canonicalize(&p).map_err(|_| {
                format!(
                    "Invalid operating directory: {}",
                    bytes::text(self.strings.get("operatingdir").unwrap())
                )
            })?;
            std::env::set_current_dir(&full)
                .map_err(|_| format!("Invalid operating directory: {}", full.display()))?;
            self.strings
                .insert("operatingdir".into(), full.as_os_str().as_bytes().to_vec());
        }
        if !self.on(RESTRICTED)
            && !self.strings.contains_key("speller")
            && let Some(s) = std::env::var_os("SPELL")
        {
            self.strings.insert("speller".into(), s.as_bytes().to_vec());
        }
        if !self.strings.contains_key("quotestr") {
            self.strings
                .insert("quotestr".into(), br"^([ \t]*([!#%:;>|}]|/{2}))+".to_vec());
        }
        let quote = self.value("quotestr");
        Regex::new(&quote, false)
            .map_err(|e| format!("Bad quoting regex \"{}\": {e}", bytes::text(&quote)))?;
        for (fun, menu) in [
            ("do_exit", MAIN),
            ("do_exit", BROWSER),
            ("do_exit", HELP),
            ("do_cancel", YESNO),
        ] {
            if !self
                .keys
                .iter()
                .any(|k| k.func == fun && k.menus & menu != 0)
            {
                return Err(format!(
                    "No key is bound to function '{}' in menu '{}'.  Exiting.\n\nIf needed, use nano with the -I option to adjust your nanorc settings.",
                    if fun == "do_exit" { "Exit" } else { "Cancel" },
                    menu_name(menu)
                ));
            }
        }
        Ok(())
    }
    fn error(&mut self, p: &Path, line: usize, msg: String) {
        if self.error_file.is_none() {
            self.error_file = Some(p.to_path_buf());
        }
        self.errors.push(if line == 0 {
            msg
        } else {
            format!("Error in {} on line {line}: {msg}", p.display())
        });
    }
    pub fn read_rc(&mut self, p: &Path, included: bool) {
        let data = match std::fs::read(p) {
            Ok(d) => d,
            Err(e) => {
                self.error(
                    p,
                    0,
                    format!("Error reading {}: {}", p.display(), io_error(&e)),
                );
                return;
            }
        };
        let mut current: Option<usize> = None;
        let mut syntax_line = 0;
        for (index, line) in data.split(|b| *b == b'\n').enumerate() {
            let line = String::from_utf8_lossy(line);
            let line = line.trim_end_matches('\r').trim_start_matches([' ', '\t']);
            if line.is_empty() || line.starts_with('#') {
                continue;
            }
            let (cmd, args) = word(line);
            if included
                && matches!(
                    cmd,
                    "set" | "unset" | "bind" | "unbind" | "include" | "extendsyntax"
                )
            {
                self.error(
                    p,
                    index + 1,
                    format!("Command \"{cmd}\" not allowed in included file"),
                );
                continue;
            }
            if matches!(
                cmd,
                "syntax" | "set" | "unset" | "bind" | "unbind" | "include" | "extendsyntax"
            ) && let Some(i) = current.take()
                && !self.syntaxes[i].seen_color
            {
                self.error(
                    p,
                    syntax_line,
                    format!("Syntax \"{}\" has no color commands", self.syntaxes[i].name),
                );
            }
            let result: Result<(), String> = (|| {
                match cmd {
                    "set" | "unset" => {
                        let (name, args) = word(args);
                        let on = cmd == "set";
                        if name.is_empty() {
                            return Err("Missing option".into());
                        }
                        if let Some((_, flag)) = RC_OPTIONS.iter().find(|(n, _)| *n == name) {
                            self.set(*flag, on);
                            return Ok(());
                        }
                        if !on {
                            if is_value_option(name) {
                                return Err(format!("Cannot unset option \"{name}\""));
                            }
                            return Err(format!("Unknown option: {name}"));
                        }
                        if !is_value_option(name) {
                            return Err(format!("Unknown option: {name}"));
                        }
                        if args.is_empty() {
                            return Err(format!("Option \"{name}\" requires an argument"));
                        }
                        let value = quoted(args)?;
                        if matches!(name, "fill" | "tabsize" | "guidestripe") {
                            let n = parse_num(&value);
                            let good = n.is_some() && (name == "fill" || n.unwrap() > 0);
                            if !good {
                                match name {
                                    "fill" => self.fill = -8,
                                    "tabsize" => self.tab = 8,
                                    _ => self.guide = 0,
                                };
                                return Err(format!(
                                    "{} \"{}\" is invalid",
                                    match name {
                                        "fill" => "Requested fill size",
                                        "tabsize" => "Requested tab size",
                                        _ => "Guide column",
                                    },
                                    value
                                ));
                            }
                            match name {
                                "fill" => self.fill = n.unwrap() as isize,
                                "tabsize" => self.tab = n.unwrap() as usize,
                                _ => self.guide = n.unwrap() as usize,
                            };
                        } else if name.ends_with("color") {
                            self.colors.insert(name.into(), color(&value)?);
                        } else {
                            if matches!(name, "matchbrackets" | "punct" | "brackets")
                                && value.chars().any(char::is_whitespace)
                            {
                                return Err("Non-blank characters required".into());
                            }
                            if name == "matchbrackets" && value.chars().count() % 2 != 0 {
                                return Err("Even number of characters required".into());
                            }
                            if name == "whitespace"
                                && (value.chars().count() != 2
                                    || value
                                        .chars()
                                        .any(|c| unsafe { native::nr_width(c as u32) } != 1))
                            {
                                return Err("Two single-column characters required".into());
                            }
                            self.strings.insert(name.into(), value.into_bytes());
                        }
                    }
                    "bind" | "unbind" => {
                        let (key, rest) = word(args);
                        if key.is_empty() {
                            return Err("Missing key name".into());
                        }
                        let mut normalized = key.to_string();
                        let position = usize::from(key.starts_with('^'));
                        if let Some(ch) = normalized.as_bytes().get(position).copied() {
                            normalized.replace_range(
                                position..position + 1,
                                &(ch as char).to_ascii_uppercase().to_string(),
                            );
                        }
                        let key = normalized.as_str();
                        if cmd == "bind" && rest.is_empty() {
                            return Err("Must specify a function to bind the key to".into());
                        }
                        let code =
                            parse_key(key).ok_or_else(|| format!("Key name {key} is invalid"))?;
                        if code == 27 {
                            return Err(format!("Keystroke {key} may not be rebound"));
                        }
                        let (function, rest, exp) = if cmd == "bind" {
                            if rest.starts_with('"') {
                                let end = rest
                                    .rfind('"')
                                    .filter(|i| *i > 0)
                                    .ok_or("Unterminated string")?;
                                ("", rest[end + 1..].trim(), Some(rest[1..end].to_string()))
                            } else {
                                let (f, r) = word(rest);
                                (f, r, None)
                            }
                        } else {
                            ("", rest, None)
                        };
                        let (menu, _) = word(rest);
                        if menu.is_empty() {
                            return Err(
                                "Must specify a menu (or \"all\") in which to bind/unbind the key"
                                    .into(),
                            );
                        }
                        let menus =
                            parse_menu(menu).ok_or_else(|| format!("Unknown menu: {menu}"))?;
                        for k in &mut self.keys {
                            if k.key == code {
                                k.menus &= !menus;
                            }
                        }
                        if cmd == "bind" {
                            let toggle = TOGGLES
                                .iter()
                                .find(|(n, _, _)| *n == function)
                                .map(|(_, f, _)| *f)
                                .unwrap_or(0);
                            let fun = if exp.is_some() {
                                "string".to_string()
                            } else if toggle > 0 {
                                "do_toggle".to_string()
                            } else {
                                RC_FUNCTIONS
                                    .iter()
                                    .find(|(n, _)| *n == function)
                                    .map(|(_, f)| f.to_string())
                                    .or_else(|| alias_function(function).map(str::to_string))
                                    .ok_or_else(|| format!("Unknown function: {function}"))?
                            };
                            let allowed = if exp.is_some() {
                                0xffff
                            } else if toggle > 0 {
                                if toggle == NO_HELP { 32511 } else { MAIN }
                            } else if matches!(
                                function,
                                "left"
                                    | "right"
                                    | "home"
                                    | "end"
                                    | "prevword"
                                    | "nextword"
                                    | "delete"
                                    | "backspace"
                                    | "cut"
                                    | "paste"
                                    | "tab"
                                    | "enter"
                                    | "verbatim"
                            ) {
                                57087
                            } else {
                                self.funcs
                                    .iter()
                                    .filter(|f| f.func == fun)
                                    .fold(0, |m, f| m | f.menus)
                            };
                            if allowed & menus == 0 && !self.on(RESTRICTED) && !self.on(VIEW_MODE) {
                                return Err(format!(
                                    "Function '{function}' does not exist in menu '{menu}'"
                                ));
                            }
                            self.shifted |= key.to_ascii_lowercase().starts_with("sh-m-");
                            let tag = if key.starts_with("Sh-") {
                                format!("Sh-M-{}", key.chars().last().unwrap().to_ascii_uppercase())
                            } else if let Some(key) = key.strip_prefix("m-") {
                                format!("M-{key}")
                            } else {
                                key.to_string()
                            };
                            self.keys.insert(
                                0,
                                Binding {
                                    key: code,
                                    menus: menus & allowed,
                                    func: fun,
                                    tag,
                                    toggle,
                                    expansion: exp,
                                },
                            );
                        }
                    }
                    "include" => {
                        let pattern = quoted(args)?;
                        let expanded = expand(pattern.as_bytes());
                        if !expanded.exists() {
                            if pattern.contains(['*', '?', '['])
                                && !expanded.parent().unwrap_or(Path::new(".")).exists()
                            {
                                return Err(format!(
                                    "Error expanding {pattern}: No such file or directory"
                                ));
                            }
                            if !pattern.contains(['*', '?', '[']) {
                                return Err(format!(
                                    "Error reading {}: No such file or directory",
                                    expanded.display()
                                ));
                            }
                        }
                        for include in expand_glob(&expanded) {
                            self.read_rc(&include, true);
                        }
                    }
                    "syntax" => {
                        let (name, rest) = if let Some(rest) = args.strip_prefix('"') {
                            let end = rest.find('"').ok_or("Unpaired quote in syntax name")?;
                            (&rest[..end], rest[end + 1..].trim())
                        } else {
                            word(args)
                        };
                        if name.is_empty() {
                            return Err("Missing syntax name".into());
                        }
                        if name == "none" {
                            return Err("The \"none\" syntax is reserved".into());
                        }
                        if name == "default" && !rest.is_empty() {
                            return Err("The \"default\" syntax does not accept extensions".into());
                        }
                        let mut syntax = Syntax {
                            name: name.into(),
                            source: Some((p.to_path_buf(), index + 1)),
                            ..Default::default()
                        };
                        for pat in regex_strings(rest)? {
                            syntax.files.push(compile(&pat, false)?);
                        }
                        self.syntaxes.push(syntax);
                        current = Some(self.syntaxes.len() - 1);
                        syntax_line = index + 1;
                    }
                    "extendsyntax" => {
                        let (name, rest) = word(args);
                        let (command, rest) = word(rest);
                        let i = self
                            .syntaxes
                            .iter()
                            .rposition(|s| s.name == name)
                            .ok_or_else(|| format!("Could not find syntax \"{name}\" to extend"))?;
                        if matches!(command, "header" | "magic") {
                            self.syntax_command(i, command, rest)?;
                        } else {
                            self.syntaxes[i].augmentations.push((
                                p.to_path_buf(),
                                index + 1,
                                command.into(),
                                rest.into(),
                            ));
                        }
                    }
                    "header" | "magic" | "color" | "icolor" | "comment" | "tabgives" | "linter"
                    | "formatter" => {
                        let i = current.ok_or_else(|| {
                            format!("A '{cmd}' command requires a preceding 'syntax' command")
                        })?;
                        if matches!(cmd, "header" | "magic") {
                            self.syntax_command(i, cmd, args)?;
                        } else {
                            if matches!(cmd, "color" | "icolor") {
                                self.syntaxes[i].seen_color = true;
                            }
                        }
                    }
                    _ => return Err(format!("Command \"{cmd}\" not understood")),
                }
                Ok(())
            })();
            if let Err(msg) = result {
                self.error(p, index + 1, msg);
            }
        }
        if let Some(i) = current
            && !self.syntaxes[i].seen_color
        {
            self.error(
                p,
                syntax_line,
                format!("Syntax \"{}\" has no color commands", self.syntaxes[i].name),
            );
        }
    }
    pub fn activate_syntax(&mut self, index: usize) -> bool {
        if self.syntaxes[index].loaded {
            return false;
        }
        self.syntaxes[index].loaded = true;
        let count = self.errors.len();
        if let Some((path, start)) = self.syntaxes[index].source.clone() {
            match std::fs::read(&path) {
                Ok(data) => {
                    for (line, bytes) in data.split(|b| *b == 10).enumerate().skip(start) {
                        let text = String::from_utf8_lossy(bytes);
                        let text = text.trim();
                        if text.is_empty() || text.starts_with('#') {
                            continue;
                        }
                        let (cmd, args) = word(text);
                        if matches!(
                            cmd,
                            "syntax"
                                | "set"
                                | "unset"
                                | "bind"
                                | "unbind"
                                | "include"
                                | "extendsyntax"
                        ) {
                            break;
                        }
                        if matches!(cmd, "header" | "magic") {
                            continue;
                        }
                        if let Err(error) = self.syntax_command(index, cmd, args) {
                            self.error(&path, line + 1, error);
                        }
                    }
                }
                Err(error) => self.error(
                    &path,
                    0,
                    format!("Error reading {}: {}", path.display(), io_error(&error)),
                ),
            }
        }
        let extra = std::mem::take(&mut self.syntaxes[index].augmentations);
        for (path, line, cmd, args) in extra {
            if let Err(error) = self.syntax_command(index, &cmd, &args) {
                self.error(&path, line, error);
            }
        }
        self.errors.len() != count
    }
    fn syntax_command(&mut self, i: usize, cmd: &str, args: &str) -> Result<(), String> {
        if args.is_empty() {
            return Err(if cmd == "color" || cmd == "icolor" {
                "Missing color name".into()
            } else if cmd == "header" || cmd == "magic" {
                format!("Missing regex string after '{cmd}' command")
            } else {
                format!("Missing argument after '{cmd}'")
            });
        }
        match cmd {
            "header" | "magic" => {
                if self.syntaxes[i].name == "default" {
                    return Err(format!(
                        "The \"default\" syntax does not accept '{cmd}' regexes"
                    ));
                }
                for p in regex_strings(args)? {
                    let r = compile(&p, false)?;
                    if cmd == "header" {
                        self.syntaxes[i].headers.push(r);
                    } else {
                        self.syntaxes[i].magic.push(r);
                    }
                }
            }
            "comment" | "tabgives" | "linter" | "formatter" => {
                let a = if args.starts_with('"') {
                    quoted(args).map_err(|_| format!("Argument of '{cmd}' lacks closing \""))?
                } else {
                    args.to_string()
                };
                match cmd {
                    "comment" => self.syntaxes[i].comment = Some(a.into_bytes()),
                    "tabgives" => self.syntaxes[i].tab = Some(a.into_bytes()),
                    "linter" => self.syntaxes[i].linter = Some(a),
                    _ => self.syntaxes[i].formatter = Some(a),
                };
            }
            "color" | "icolor" => {
                let (spec, rest) = word(args);
                let style = color(spec)?;
                let mut rest = rest;
                while !rest.is_empty() {
                    if let Some(s) = rest.strip_prefix("start=") {
                        let (p, r) = take_regex(s)?;
                        let e = r
                            .strip_prefix("end=")
                            .ok_or("\"start=\" requires a corresponding \"end=\"")?;
                        let (end, r) = take_regex(e)?;
                        self.syntaxes[i].rules.push(Rule {
                            start: compile(&p, cmd == "icolor")?,
                            end: Some(compile(&end, cmd == "icolor")?),
                            style,
                        });
                        rest = r;
                    } else {
                        let (p, r) = take_regex(rest)?;
                        self.syntaxes[i].rules.push(Rule {
                            start: compile(&p, cmd == "icolor")?,
                            end: None,
                            style,
                        });
                        rest = r;
                    }
                }
            }
            _ => return Err(format!("Command \"{cmd}\" not understood")),
        }
        Ok(())
    }
    pub fn select_syntax(&self, name: &[u8], first: &[u8]) -> Option<usize> {
        if self.syntaxes.is_empty() || self.value("syntax") == b"none" {
            return None;
        }
        let forced = self.value("syntax");
        if !forced.is_empty()
            && let Some(i) = self
                .syntaxes
                .iter()
                .rposition(|s| s.name.as_bytes() == forced)
        {
            return Some(i);
        }
        let full = std::fs::canonicalize(path(name)).unwrap_or_else(|_| path(name));
        let name = full.as_os_str().as_bytes();
        for (i, s) in self.syntaxes.iter().enumerate().rev() {
            if s.files.iter().any(|r| r.find(name, 0, false).is_some()) {
                return Some(i);
            }
        }
        for (i, s) in self.syntaxes.iter().enumerate().rev() {
            if s.headers.iter().any(|r| r.find(first, 0, false).is_some()) {
                return Some(i);
            }
        }
        if self.on(USE_MAGIC) {
            let desc = native::magic(name);
            for (i, s) in self.syntaxes.iter().enumerate().rev() {
                if s.magic.iter().any(|r| r.find(&desc, 0, false).is_some()) {
                    return Some(i);
                }
            }
        }
        self.syntaxes.iter().rposition(|s| s.name == "default")
    }
}
pub fn path(bytes: &[u8]) -> PathBuf {
    PathBuf::from(OsString::from_vec(bytes.to_vec()))
}
pub fn home_dir() -> Option<PathBuf> {
    // nano caches a successfully resolved home, and retries unresolved lookups.
    static HOME: std::sync::OnceLock<PathBuf> = std::sync::OnceLock::new();
    if let Some(home) = HOME.get() {
        return Some(home.clone());
    }
    let home = native::current_home().map(|bytes| path(&bytes))?;
    let _ = HOME.set(home.clone());
    Some(home)
}
pub fn expand(name: &[u8]) -> PathBuf {
    if name.first() != Some(&b'~') || name.len() == 1 {
        return path(name);
    }
    let end = name.iter().position(|b| *b == b'/').unwrap_or(name.len());
    let home = if end == 1 {
        let Some(home) = home_dir() else {
            return path(name);
        };
        home
    } else {
        let h = native::home(&name[1..end]);
        if h.is_empty() {
            return path(name);
        }
        path(&h)
    };
    if end == name.len() {
        home
    } else {
        let mut expanded = home.as_os_str().as_bytes().to_vec();
        expanded.extend_from_slice(&name[end..]);
        path(&expanded)
    }
}
pub fn io_error(e: &std::io::Error) -> String {
    e.to_string()
        .split(" (os error ")
        .next()
        .unwrap_or("")
        .into()
}
pub fn parse_num(s: &str) -> Option<i64> {
    let s = s.trim_start_matches([' ', '\t', '\n', '\r', '\u{b}', '\u{c}']);
    if s.is_empty() || s.trim_end() != s {
        return None;
    }
    s.parse().ok()
}
pub fn word(s: &str) -> (&str, &str) {
    let s = s.trim_start_matches([' ', '\t']);
    let i = s.find([' ', '\t']).unwrap_or(s.len());
    (&s[..i], s[i..].trim_start_matches([' ', '\t']))
}
pub fn quoted(s: &str) -> Result<String, String> {
    if let Some(rest) = s.strip_prefix('"') {
        let end = rest
            .rfind('"')
            .ok_or_else(|| format!("Argument '{s}' has an unterminated \""))?;
        Ok(rest[..end].into())
    } else {
        Ok(word(s).0.into())
    }
}
fn take_regex(s: &str) -> Result<(Vec<u8>, &str), String> {
    let rest = s
        .strip_prefix('"')
        .ok_or("Regex strings must begin and end with a \" character")?;
    let end = rest
        .char_indices()
        .find(|(i, c)| {
            *c == '"' && (rest[*i + 1..].is_empty() || rest[*i + 1..].starts_with([' ', '\t']))
        })
        .map(|(i, _)| i)
        .ok_or("Regex strings must begin and end with a \" character")?;
    if end == 0 {
        return Err("Empty regex string".into());
    }
    Ok((
        rest.as_bytes()[..end].to_vec(),
        rest[end + 1..].trim_start_matches([' ', '\t']),
    ))
}
fn regex_strings(mut s: &str) -> Result<Vec<Vec<u8>>, String> {
    let mut out = Vec::new();
    while !s.is_empty() {
        let (p, r) = take_regex(s)?;
        out.push(p);
        s = r;
    }
    Ok(out)
}
fn compile(p: &[u8], case: bool) -> Result<Regex, String> {
    Regex::new(p, case).map_err(|e| format!("Bad regex \"{}\": {e}", bytes::text(p)))
}
fn is_value_option(s: &str) -> bool {
    matches!(
        s,
        "fill"
            | "tabsize"
            | "guidestripe"
            | "operatingdir"
            | "backupdir"
            | "quotestr"
            | "speller"
            | "wordchars"
            | "punct"
            | "brackets"
            | "matchbrackets"
            | "whitespace"
    ) || s.ends_with("color")
}
pub fn parse_menu(s: &str) -> Option<u32> {
    Some(match s {
        "main" => MAIN,
        "search" => SEARCH,
        "replace" => REPLACE,
        "replacewith" => REPLACEWITH,
        "gotoline" => GOTO,
        "writeout" => WRITE,
        "insert" => INSERT,
        "execute" => EXEC,
        "help" => HELP,
        "spell" => SPELL,
        "browser" => BROWSER,
        "whereisfile" => BSEARCH,
        "gotodir" => BGOTO,
        "yesno" => YESNO,
        "linter" => LINTER,
        "all" => 0xffff,
        _ => return None,
    })
}
pub fn menu_name(m: u32) -> &'static str {
    match m {
        MAIN => "main",
        BROWSER => "browser",
        HELP => "help",
        YESNO => "yesno",
        _ => "all",
    }
}
pub fn parse_key(s: &str) -> Option<i32> {
    let l = s.to_ascii_lowercase();
    if l == "^space" {
        return Some(0);
    }
    if l.starts_with("sh-m-") && s.len() == 6 {
        return Some(s.as_bytes()[5].to_ascii_uppercase() as i32);
    }
    if l.starts_with("m-") {
        let s = &s[2..];
        if s.len() == 1 {
            return Some(s.as_bytes()[0].to_ascii_lowercase() as i32);
        }
        return Some(match s.to_ascii_lowercase().as_str() {
            "space" => 32,
            "left" => 0x421,
            "right" => 0x422,
            "up" => 0x423,
            "down" => 0x424,
            "ins" => 0x42c,
            "del" => 0x42d,
            _ => return None,
        });
    }
    if l.starts_with('^') && s.len() == 2 {
        let c = s.as_bytes()[1].to_ascii_uppercase();
        return if matches!(c, b'/' | b'-') {
            Some(31)
        } else if (b'@'..=b'_').contains(&c) {
            Some((c - 64) as i32)
        } else if c == b'`' {
            Some(0)
        } else {
            None
        };
    }
    if let Some(n) = l.strip_prefix('f') {
        let digits: String = n.chars().take_while(char::is_ascii_digit).collect();
        if let Ok(n) = digits.parse::<i32>()
            && (1..=24).contains(&n)
        {
            return Some(264 + n);
        }
    }
    match l.as_str() {
        "ins" => Some(331),
        "del" => Some(330),
        _ => None,
    }
}
fn alias_function(s: &str) -> Option<&'static str> {
    Some(match s {
        "location" => "report_cursor_position",
        "discardbuffer" => "discard_buffer",
        "findnext" => "do_findnext",
        "findprevious" => "do_findprevious",
        "suspend" => "do_suspend",
        _ => return None,
    })
}
pub fn color(spec: &str) -> Result<Style, String> {
    let mut s = Style::NORMAL;
    let mut rest = spec;
    loop {
        if let Some(r) = rest.strip_prefix("bold,") {
            s.bits |= 1;
            rest = r;
        } else if let Some(r) = rest.strip_prefix("italic,") {
            s.bits |= 2;
            rest = r;
        } else {
            break;
        }
    }
    if rest == "bold" || rest == "italic" {
        return Err("An attribute requires a subsequent comma".into());
    }
    let mut parts = rest.split(',');
    s.fg = color_number(parts.next().unwrap_or(""), &mut s.bits, false)?;
    s.bg = color_number(parts.next().unwrap_or(""), &mut s.bits, true)?;
    Ok(s)
}
fn color_number(s: &str, bits: &mut i32, bg: bool) -> Result<i32, String> {
    let (base, light, bright) = if let Some(s) = s.strip_prefix("light") {
        (s, true, false)
    } else if let Some(s) = s.strip_prefix("bright") {
        (s, true, true)
    } else {
        (s, false, false)
    };
    let basic = match base {
        "black" => Some(0),
        "red" => Some(1),
        "green" => Some(2),
        "yellow" => Some(3),
        "blue" => Some(4),
        "magenta" => Some(5),
        "cyan" => Some(6),
        "white" => Some(7),
        _ => None,
    };
    if let Some(n) = basic {
        if bright && !bg {
            *bits |= 1;
        }
        return Ok(n + if light && (!bright || bg) { 8 } else { 0 });
    }
    if light {
        return Err(format!("Color '{base}' takes no prefix"));
    }
    if s.is_empty() || s == "normal" {
        return Ok(-1);
    }
    if s == "grey" || s == "gray" {
        return Ok(8);
    }
    let extra = [
        ("pink", 204),
        ("purple", 163),
        ("mauve", 134),
        ("lagoon", 38),
        ("mint", 48),
        ("lime", 148),
        ("peach", 215),
        ("orange", 208),
        ("latte", 137),
        ("rosy", 175),
        ("beet", 127),
        ("plum", 98),
        ("sea", 32),
        ("sky", 111),
        ("slate", 66),
        ("teal", 35),
        ("sage", 107),
        ("brown", 100),
        ("ocher", 142),
        ("sand", 186),
        ("tawny", 136),
        ("brick", 166),
        ("crimson", 161),
    ];
    if let Some((_, n)) = extra.iter().find(|(k, _)| *k == s) {
        return Ok(*n);
    }
    if s.len() == 4
        && s.starts_with('#')
        && let Ok(n) = u16::from_str_radix(&s[1..], 16)
    {
        let r = (n >> 8) as i32;
        let g = ((n >> 4) & 15) as i32;
        let b = (n & 15) as i32;
        if r == g && g == b && r > 0 && r < 15 {
            return Ok(232 + [1, 2, 3, 4, 5, 6, 7, 9, 11, 13, 15, 18, 21, 23][(r - 1) as usize]);
        }
        let level = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5];
        return Ok(16 + 36 * level[r as usize] + 6 * level[g as usize] + level[b as usize]);
    }
    Err(format!("Color \"{s}\" not understood"))
}
fn expand_glob(p: &Path) -> Vec<PathBuf> {
    let Some(name) = p.file_name().map(|s| s.to_string_lossy()) else {
        return vec![p.to_path_buf()];
    };
    if !name.contains(['*', '?', '[']) {
        return vec![p.to_path_buf()];
    }
    let parent = p.parent().unwrap_or(Path::new("."));
    let mut found: Vec<_> = std::fs::read_dir(parent)
        .into_iter()
        .flatten()
        .filter_map(Result::ok)
        .filter(|e| glob_match(&name, &e.file_name().to_string_lossy()))
        .map(|e| e.path())
        .collect();
    found.sort_by(|a, b| {
        let a = native::cstr(a.as_os_str().as_bytes());
        let b = native::cstr(b.as_os_str().as_bytes());
        unsafe { native::nr_collate(a.as_ptr(), b.as_ptr()) }.cmp(&0)
    });
    if found.is_empty() {
        found.push(p.to_path_buf());
    }
    found
}
fn glob_match(p: &str, s: &str) -> bool {
    let (p, s) = (p.as_bytes(), s.as_bytes());
    fn go(p: &[u8], s: &[u8]) -> bool {
        match p.first() {
            None => s.is_empty(),
            Some(b'*') => go(&p[1..], s) || !s.is_empty() && go(p, &s[1..]),
            Some(b'?') => !s.is_empty() && go(&p[1..], &s[1..]),
            Some(c) => s.first() == Some(c) && go(&p[1..], &s[1..]),
        }
    }
    go(p, s)
}
