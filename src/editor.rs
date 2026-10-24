//! Editor state machine. Mutations are routed through Buffer transactions.
use crate::{
    buffer::{Buffer, Pos},
    bytes,
    config::{self, Config},
    files,
    generated::*,
    input::{Event, Input, Key},
    native, render,
};
use std::{path::PathBuf, time::Instant};
#[derive(Clone, Debug, PartialEq)]
pub enum PromptKind {
    Search(bool),
    ReplaceWith,
    Goto,
    Write { exit: bool, mode: i32 },
    Insert,
    Execute,
    BrowserSearch,
    BrowserGoto,
    HelpSearch,
    Spell,
}
#[derive(Clone, Debug)]
pub struct Prompt {
    pub kind: PromptKind,
    pub answer: Vec<u8>,
    pub x: usize,
    pub history: Option<usize>,
    pub remembered: Vec<u8>,
    pub fragment: Vec<u8>,
    pub initial_newbuffer: bool,
    pub other_answer: Vec<u8>,
}
impl Prompt {
    pub fn new(kind: PromptKind, answer: Vec<u8>) -> Self {
        let x = answer.len();
        Self {
            kind,
            answer,
            x,
            history: None,
            remembered: Vec::new(),
            fragment: Vec::new(),
            initial_newbuffer: false,
            other_answer: Vec::new(),
        }
    }
}
#[derive(Debug)]
pub enum QuestionKind {
    Exit,
    Different(Prompt),
    Overwrite(Prompt),
    Changed(Prompt),
    Replace,
    Lock(usize),
    LintSave,
}
#[derive(Debug)]
pub struct Question {
    pub text: String,
    pub kind: QuestionKind,
    pub all: bool,
}
#[derive(Debug)]
pub struct HelpState {
    pub previous: Box<Mode>,
    pub title: String,
    pub lines: Vec<Vec<u8>>,
    pub top: usize,
    pub saved_search: Vec<u8>,
    pub saved_flags: u64,
    pub viewport: (usize, usize),
    pub highlight: Option<(usize, usize, usize)>,
    pub cursor_bottom: bool,
}
#[derive(Debug)]
pub struct BrowserState {
    pub previous: Prompt,
    pub dir: PathBuf,
    pub entries: Vec<PathBuf>,
    pub selected: usize,
    pub gauge: usize,
    pub piles: usize,
    pub footer_cursor: bool,
}
#[derive(Debug)]
pub struct LintState {
    pub entries: Vec<(Vec<u8>, usize, usize, String)>,
    pub index: usize,
    pub original_nohelp: bool,
}
#[derive(Debug, Default)]
pub enum Mode {
    #[default]
    Edit,
    Prompt(Prompt),
    Question(Question),
    Help(HelpState),
    Browser(BrowserState),
    Lint(LintState),
}
#[derive(Clone, Debug)]
pub struct Message {
    pub text: String,
    pub level: i32,
    pub countdown: usize,
    pub ellipsis: bool,
    pub time: Instant,
}
pub struct Spelling {
    pub started: bool,
    pub words: std::collections::VecDeque<Vec<u8>>,
    pub search: Vec<u8>,
    pub flags: u64,
    pub original: Pos,
    pub top: usize,
}
pub type Match = (Pos, Pos, Vec<(usize, usize)>);
#[derive(Debug)]
pub struct Replacement {
    pub matches: Vec<Match>,
    pub next: usize,
    pub replacement: Vec<u8>,
    pub count: usize,
    pub original: Pos,
    pub top: usize,
    pub mark: Option<Pos>,
}
pub struct Editor {
    pub conf: Config,
    pub buffers: Vec<Buffer>,
    pub current: usize,
    pub multiple: bool,
    pub mode: Mode,
    pub input: Input,
    pub message: Option<Message>,
    pub action_level: i32,
    pub pause_until: Option<Instant>,
    pub pause_next: Option<Box<Mode>>,
    pub last_screen: Option<render::Canvas>,
    pub pause_screen: Option<render::Canvas>,
    pub pause_painted: bool,
    pub pause_duration: std::time::Duration,
    pub spotlight: Option<(usize, usize, usize)>,
    pub spotlight_time: Instant,
    pub cutbuffer: Vec<u8>,
    pub last_command: String,
    pub search: Vec<u8>,
    pub histories: [Vec<Vec<u8>>; 3],
    pub history_changed: bool,
    pub state_dir: Option<PathBuf>,
    pub replacement: Option<Replacement>,
    pub spelling: Option<Spelling>,
    pub completion: Vec<Vec<u8>>,
    pub recording: bool,
    pub macro_keys: Vec<Key>,
    pub previous_macro: Vec<Key>,
    pub exit: Option<i32>,
    pub fatal: Option<String>,
    pub cycle: usize,
    pub give_hint: bool,
    pub completion_fragment: Vec<u8>,
    pub completion_tried: Vec<Vec<u8>>,
    pub completion_start: Pos,
    pub browser_saved: Option<BrowserState>,
    pub help_saved: Option<HelpState>,
    pub tool_answer: Vec<u8>,
    pub position_entries: Vec<Vec<u8>>,
}
impl Editor {
    pub fn new(conf: Config) -> Self {
        Self {
            conf,
            buffers: Vec::new(),
            current: 0,
            multiple: false,
            mode: Mode::Edit,
            input: Input::default(),
            message: None,
            action_level: 0,
            pause_until: None,
            pause_next: None,
            last_screen: None,
            pause_screen: None,
            pause_painted: false,
            pause_duration: std::time::Duration::ZERO,
            spotlight: None,
            spotlight_time: Instant::now(),
            cutbuffer: Vec::new(),
            last_command: String::new(),
            search: Vec::new(),
            histories: Default::default(),
            history_changed: false,
            state_dir: None,
            replacement: None,
            spelling: None,
            completion: Vec::new(),
            recording: false,
            macro_keys: Vec::new(),
            previous_macro: Vec::new(),
            exit: None,
            fatal: None,
            cycle: 0,
            give_hint: true,
            completion_fragment: Vec::new(),
            completion_tried: Vec::new(),
            completion_start: Pos::default(),
            browser_saved: None,
            help_saved: None,
            tool_answer: Vec::new(),
            position_entries: Vec::new(),
        }
    }
    pub fn b(&self) -> &Buffer {
        &self.buffers[self.current]
    }
    pub fn bm(&mut self) -> &mut Buffer {
        &mut self.buffers[self.current]
    }
    pub fn msg(&mut self, text: impl Into<String>, level: i32) {
        let text = text.into();
        if self.action_level > 4 && level < self.action_level {
            return;
        }
        if let Some(m) = self.message.as_mut()
            && self.action_level == 7
            && level == 7
        {
            m.ellipsis = true;
            return;
        }
        if level >= 5 {
            self.input.queue.clear();
            self.input.replay.clear();
        }
        if level == 7 {
            unsafe {
                native::nr_beep();
            }
        }
        self.action_level = level;
        self.message = Some(Message {
            text: native::tr(&text),
            level,
            ellipsis: false,
            countdown: if self.conf.on(QUICK_BLANK) { 1 } else { 20 },
            time: Instant::now(),
        });
    }
    pub fn clear(&mut self) {
        self.action_level = 0;
        self.message = None;
    }
    pub fn cancelled(&mut self) {
        self.mode = Mode::Edit;
        self.completion.clear();
        self.msg("Cancelled", 1);
    }
    pub fn menu(&self) -> u32 {
        match &self.mode {
            Mode::Edit => MAIN,
            Mode::Prompt(p) => match p.kind {
                PromptKind::Search(false) => SEARCH,
                PromptKind::Search(true) => REPLACE,
                PromptKind::ReplaceWith => REPLACEWITH,
                PromptKind::Goto => GOTO,
                PromptKind::Write { .. } => WRITE,
                PromptKind::Insert => INSERT,
                PromptKind::Execute => EXEC,
                PromptKind::BrowserSearch => BSEARCH,
                PromptKind::BrowserGoto => BGOTO,
                PromptKind::Spell => SPELL,
                PromptKind::HelpSearch => HSEARCH,
            },
            Mode::Question(_) => YESNO,
            Mode::Help(_) => HELP,
            Mode::Browser(_) => BROWSER,
            Mode::Lint(_) => LINTER,
        }
    }
    pub fn prompt(&mut self, kind: PromptKind, answer: Vec<u8>) {
        self.clear();
        self.completion.clear();
        let mut p = Prompt::new(kind, answer);
        p.initial_newbuffer = self.conf.on(NEW_BUFFER);
        self.mode = Mode::Prompt(p);
    }
    pub fn question(&mut self, text: impl Into<String>, kind: QuestionKind, all: bool) {
        self.clear();
        self.mode = Mode::Question(Question {
            text: text.into(),
            kind,
            all,
        });
    }
    pub fn setup(&mut self) {
        self.load_history();
        let args = self.conf.operands.clone();
        let mut pending: Option<Vec<u8>> = None;
        let mut first_msg: Option<Option<Message>> = None;
        for (i, word) in args.iter().enumerate() {
            if word.starts_with(b"+") && i + 1 < args.len() {
                pending = Some(word[1..].to_vec());
                continue;
            }
            let mut name = word.clone();
            let mut position = pending.take();
            if self.conf.on(COLON_PARSING) && position.is_none() && !config::path(&name).exists() {
                for _ in 0..2 {
                    if let Some(i) = name.iter().rposition(|b| *b == b':')
                        && i > 0
                        && name[i + 1..].iter().all(u8::is_ascii_digit)
                        && i + 1 < name.len()
                    {
                        let suffix = name[i + 1..].to_vec();
                        name.truncate(i);
                        if config::path(&name).exists() {
                            let mut pos = suffix;
                            if let Some(old) = position.take() {
                                pos.push(b',');
                                pos.extend(old);
                            }
                            position = Some(pos);
                            break;
                        } else {
                            position = Some(suffix);
                        }
                    }
                }
                if !config::path(&name).exists() {
                    name = word.clone();
                    position = None;
                }
            }
            if name == b"-" {
                let mut data = Vec::new();
                use std::io::Read;
                let _ = std::io::stdin().read_to_end(&mut data);
                unsafe {
                    native::nr_reconnect();
                }
                let (lines, dos, n) = files::parse(&data, !self.conf.on(NO_CONVERT));
                let mut b = Buffer::new(Vec::new(), lines);
                b.magic(self.conf.on(NO_NEWLINES));
                b.dos = dos && !self.conf.on(MAKE_IT_UNIX);
                b.modified = !data.is_empty() && !self.conf.on(VIEW_MODE);
                b.state.pos = b.end();
                self.buffers.push(b);
                if first_msg.is_none() {
                    self.msg(files::line_message("Read", n, dos), 2);
                    first_msg = Some(self.message.clone());
                }
                continue;
            }
            match files::open(&self.conf, &name, self.conf.on(NOREAD_MODE)) {
                Ok((b, msg, level)) => {
                    self.buffers.push(b);
                    self.current = self.buffers.len() - 1;
                    self.msg(msg, level);
                    self.restore_position();
                    if let Some(pos) = position {
                        self.startup_position(&pos);
                    }
                    if first_msg.is_none() {
                        first_msg = Some(self.message.clone());
                    }
                }
                Err(msg) => {
                    if let Some(b) = self.buffers.last_mut() {
                        b.deferred = Some(msg.clone());
                    }
                    self.msg(msg, 7);
                    first_msg = Some(self.message.clone());
                }
            }
        }
        if self.buffers.is_empty() {
            self.buffers.push(Buffer::default());
            self.conf.set(VIEW_MODE, false);
        }
        self.current = 0;
        self.multiple = self.buffers.len() > 1;
        self.conf.set(NOREAD_MODE, false);
        if self.conf.on(VIEW_MODE) {
            self.conf.set(NEW_BUFFER, true);
        }
        if self.multiple
            && !first_msg
                .as_ref()
                .and_then(|m| m.as_ref())
                .is_some_and(|m| m.level >= 5)
        {
            self.clear();
            self.buffer_message();
        } else {
            self.message = first_msg.flatten();
        }
        if (self.conf.on(ZERO) || self.conf.on(MINIBAR))
            && self.message.as_ref().is_some_and(|m| m.level < 5)
        {
            self.message = None;
        }
        if self.b().name.is_empty()
            && self.b().raw().is_empty()
            && self.action_level < 5
            && unsafe { native::nr_rows() } > 1
            && !self.conf.on(NO_HELP)
            && self
                .conf
                .keys
                .iter()
                .find(|k| k.func == "do_help" && k.menus & MAIN != 0)
                .is_some_and(|k| k.key == 7)
        {
            self.msg("Welcome to nano.  For basic help, type Ctrl+G.", 1);
        }
        if let Some(p) = self.conf.error_file.clone() {
            self.clear();
            self.msg(format!("Mistakes in '{}'", p.display()), 7);
        }
        if self.conf.on(LOCKING) && !self.conf.on(VIEW_MODE) {
            for i in 0..self.buffers.len() {
                if let Some(conflict) = files::lock_conflict(&self.buffers[i].name) {
                    match conflict {
                        Ok(text) => {
                            self.current = i;
                            self.question(text, QuestionKind::Lock(i), false);
                            break;
                        }
                        Err(msg) => self.msg(msg, 7),
                    }
                } else if let Err(msg) = files::lock(&mut self.buffers[i]) {
                    self.msg(msg, 6);
                }
            }
        }
        unsafe {
            native::nr_setup_signals();
            native::nr_mouse(self.conf.on(USE_MOUSE) as i32);
        }
    }
    pub fn run(&mut self) -> i32 {
        self.setup();
        if unsafe { native::nr_tty(0) } == 0 {
            self.fatal = Some("Standard input is not a terminal\n".into());
            self.exit = Some(1);
        }
        while self.exit.is_none() {
            if let Some(until) = self.pause_until {
                if !self.pause_painted {
                    render::draw(self);
                    self.pause_until = Some(Instant::now() + self.pause_duration);
                    self.pause_painted = true;
                    continue;
                }
                if Instant::now() < until {
                    std::thread::sleep(std::time::Duration::from_millis(50));
                    continue;
                }
                self.pause_until = None;
                self.pause_screen = None;
                self.clear();
                if let Some(next) = self.pause_next.take() {
                    self.mode = *next;
                }
            }
            if self.b().modified && self.b().lock.is_some() && !self.b().lock_modified {
                let i = self.current;
                if let Err(msg) = files::lock(&mut self.buffers[i]) {
                    self.msg(msg, 6);
                }
            }
            if self.conf.on(CONSTANT_SHOW)
                && !self.conf.on(ZERO)
                && !self.conf.on(MINIBAR)
                && self.action_level == 0
                && self.input.queue.is_empty()
                && self.input.replay.is_empty()
                && matches!(self.mode, Mode::Edit)
            {
                self.report_position();
            }
            render::draw(self);
            match self.input.next(&self.conf) {
                Event::Idle => {
                    let timed = self.conf.on(ZERO)
                        || self.conf.on(MINIBAR)
                        || unsafe { native::nr_rows() } == 1;
                    if timed
                        && self.message.as_ref().is_some_and(|m| {
                            m.level != 3
                                && m.time.elapsed().as_millis()
                                    > if self.conf.on(QUICK_BLANK) { 800 } else { 1500 }
                        })
                    {
                        self.clear();
                    }
                    if self.spotlight.is_some()
                        && matches!(self.mode, Mode::Edit)
                        && self.spotlight_time.elapsed().as_millis()
                            > if self.conf.on(QUICK_BLANK) { 800 } else { 1500 }
                    {
                        self.spotlight = None;
                    }
                }
                Event::Signal(s) => self.signal(s),
                Event::Key(k) => self.key(k),
            }
        }
        if self.fatal.is_none() {
            let l = render::layout(self);
            unsafe {
                native::nr_finish(l.status as i32);
            }
        }
        self.save_history();
        for b in &mut self.buffers {
            files::remove_lock(b);
        }
        self.exit.unwrap_or(0)
    }
    fn signal(&mut self, s: i32) {
        match s {
            1 | 15 => {
                self.fatal = Some("Received SIGHUP or SIGTERM\n".into());
                self.exit = Some(1);
            }
            28 => {
                self.clear();
                unsafe {
                    native::nr_resize();
                }
                if matches!(self.mode, Mode::Browser(_)) {
                    self.refresh_browser();
                }
            }
            18 => unsafe {
                native::nr_resume(self.conf.on(PRESERVE) as i32);
                native::nr_resize();
            },
            20 => self.suspend(),
            _ => {}
        }
    }
    pub fn fatal_save(&mut self, message: &str) {
        unsafe {
            native::nr_done();
        }
        for e in &self.conf.errors {
            eprintln!("{e}");
        }
        eprint!("{message}");
        for i in 0..self.buffers.len() {
            let j = (self.current + i) % self.buffers.len();
            files::remove_lock(&mut self.buffers[j]);
            if let Some(p) = files::emergency(&self.conf, &self.buffers[j]) {
                eprintln!("\nBuffer written to {}", p.display());
            }
        }
    }
    pub fn suspend(&mut self) {
        if self.conf.on(RESTRICTED) {
            self.msg("This function is disabled in restricted mode", 5);
            return;
        }
        unsafe {
            native::nr_done();
        }
        print!("\n\nUse \"fg\" to return to nano.\n");
        use std::io::Write;
        let _ = std::io::stdout().flush();
        unsafe {
            native::nr_stop();
            native::nr_resume(self.conf.on(PRESERVE) as i32);
            native::nr_resize();
        }
        self.mode = Mode::Edit;
    }
    pub fn key(&mut self, key: Key) {
        self.bm().report_size = false;
        if self.conf.on(ZERO) || self.conf.on(MINIBAR) {
            self.clear();
        }
        self.action_level = 0;
        if let Some(m) = self.message.as_mut() {
            self.action_level = 0;
            m.countdown = m.countdown.saturating_sub(1);
            if m.countdown == 0 {
                self.message = None;
            }
        }
        let menu = self.menu();
        if key.code == 409 {
            self.mouse();
            return;
        }
        if key.code == 0x4b5 {
            let (raw, ok) = self.input.paste();
            match &mut self.mode {
                Mode::Edit => {
                    if self.can_change() {
                        let no = self.conf.on(NO_NEWLINES);
                        self.bm().insert(&raw, "paste", false, no);
                        if ok {
                            self.clear();
                        }
                        if !ok {
                            self.msg("Flawed paste", 7);
                        }
                        self.preferred();
                    }
                }
                Mode::Prompt(p) => {
                    let raw: Vec<u8> = raw.into_iter().filter(|b| *b >= 32 || *b == 9).collect();
                    p.answer.splice(p.x..p.x, bytes::encode_nuls(&raw));
                    p.x += raw.len();
                }
                Mode::Question(_) => {
                    if let Some(&b) = raw.first() {
                        self.key(Key::plain(b as i32));
                    }
                }
                _ => self.msg("Paste is ignored", 5),
            }
            return;
        }
        let binding = if let Some(command) = &key.command {
            Some(Binding {
                key: key.code,
                menus: menu,
                func: command.clone(),
                tag: String::new(),
                toggle: 0,
                expansion: None,
            })
        } else if !key.meta && (32..=255).contains(&key.code) || key.meta && key.code < 32 {
            None
        } else {
            self.conf
                .keys
                .iter()
                .find(|k| k.menus & menu != 0 && k.key == key.code)
                .cloned()
        };
        if self.recording
            && binding
                .as_ref()
                .is_none_or(|b| b.func != "record_macro" && b.func != "run_macro")
        {
            self.macro_keys.push(key.clone());
        }
        if let Some(b) = binding.as_ref()
            && let Some(exp) = &b.expansion
        {
            self.expand_binding(exp);
            return;
        }
        let function = binding.as_ref().map(|b| b.func.as_str()).unwrap_or("");
        if menu == MAIN
            && !matches!(
                function,
                "do_search_forward" | "do_search_backward" | "do_replace"
            )
        {
            self.spotlight = None;
        }
        let mode = std::mem::take(&mut self.mode);
        match mode {
            Mode::Edit => self.edit_key(
                key,
                function,
                binding.as_ref().map(|b| b.toggle).unwrap_or(0),
            ),
            Mode::Prompt(p) => self.prompt_key(
                p,
                key,
                function,
                binding.as_ref().map(|b| b.toggle).unwrap_or(0),
            ),
            Mode::Question(q) => self.question_key(q, key, function),
            Mode::Help(h) => self.help_key(h, key, function),
            Mode::Browser(b) => self.browser_key(b, key, function),
            Mode::Lint(l) => self.lint_key(l, key, function),
        }
    }
    pub fn lookup_function(&self, name: &str) -> Option<String> {
        if let Some((_, flag, _)) = TOGGLES.iter().find(|(n, _, _)| *n == name) {
            return Some(format!("toggle:{flag}"));
        }
        RC_FUNCTIONS
            .iter()
            .find(|(n, _)| *n == name)
            .map(|(_, f)| f.to_string())
    }
    fn expand_binding(&mut self, exp: &str) {
        let mut chars = exp.chars().peekable();
        let mut keys = Vec::new();
        while let Some(c) = chars.next() {
            if c == '{' {
                let mut name = String::new();
                let mut closed = false;
                for c in chars.by_ref() {
                    if c == '}' {
                        closed = true;
                        break;
                    }
                    name.push(c);
                }
                if !closed {
                    keys.push(Key {
                        command: Some("error:Missing }".into()),
                        ..Key::plain(0)
                    });
                    break;
                }
                if name == "{" || name == "}" {
                    keys.push(Key::plain(name.as_bytes()[0] as i32));
                } else if let Some(fun) = self.lookup_function(&name) {
                    keys.push(Key {
                        command: Some(fun),
                        ..Key::plain(0)
                    });
                } else {
                    keys.push(Key {
                        command: Some(format!("error:Unknown function: {name}")),
                        ..Key::plain(0)
                    });
                    break;
                }
            } else {
                let mut buf = [0; 4];
                for b in c.encode_utf8(&mut buf).bytes() {
                    keys.push(Key::plain(b as i32));
                }
            }
        }
        for k in keys.into_iter().rev() {
            self.input.replay.push_front(k);
        }
    }
    pub fn can_change(&mut self) -> bool {
        if self.conf.on(VIEW_MODE) {
            self.msg("Key is invalid in view mode", 5);
            false
        } else {
            true
        }
    }
    pub fn preferred(&mut self) {
        let e = self.conf.enc();
        let col = e.column(self.b().line(), self.b().pos().x);
        self.bm().preferred = col;
    }
    fn edit_key(&mut self, key: Key, fun: &str, toggle: usize) {
        if let Some(err) = fun.strip_prefix("error:") {
            self.msg(err, 5);
            return;
        }
        if let Some(flag) = fun.strip_prefix("toggle:") {
            if let Ok(f) = flag.parse() {
                self.toggle(f);
            }
            return;
        }
        if fun == "do_toggle" {
            self.toggle(toggle);
            return;
        }
        let movement = matches!(
            fun,
            "do_left"
                | "do_right"
                | "do_up"
                | "do_down"
                | "do_home"
                | "do_end"
                | "to_prev_word"
                | "to_next_word"
                | "to_prev_block"
                | "to_next_block"
                | "do_page_up"
                | "do_page_down"
                | "to_first_line"
                | "to_last_line"
                | "to_para_begin"
                | "to_para_end"
                | "to_top_row"
                | "to_bottom_row"
        );
        if movement {
            if key.shift && self.b().state.mark.is_none() {
                let p = self.b().pos();
                self.bm().state.mark = Some(p);
                self.bm().softmark = true;
            } else if !key.shift && self.b().softmark {
                self.bm().state.mark = None;
                self.bm().softmark = false;
            }
        }
        if key.code == 8
            && !key.meta
            && self.give_hint
            && self.b().pos() == Pos::default()
            && !self.conf.on(NO_HELP)
        {
            self.msg("^W = Ctrl+W    M-W = Alt+W", 1);
            self.give_hint = false;
        } else if key.meta && !fun.is_empty() {
            self.give_hint = false;
        }
        let change = matches!(
            fun,
            "do_savefile"
                | "do_writeout"
                | "do_enter"
                | "do_tab"
                | "do_delete"
                | "do_backspace"
                | "cut_text"
                | "paste_text"
                | "chop_previous_word"
                | "chop_next_word"
                | "zap_text"
                | "cut_till_eof"
                | "do_execute"
                | "do_indent"
                | "do_unindent"
                | "do_justify"
                | "do_full_justify"
                | "do_comment"
                | "do_spell"
                | "do_formatter"
                | "complete_a_word"
                | "do_replace"
                | "do_verbatim_input"
        );
        if change && !self.can_change() {
            return;
        }
        if self.conf.on(RESTRICTED)
            && matches!(
                fun,
                "do_insertfile"
                    | "do_execute"
                    | "do_spell"
                    | "do_linter"
                    | "do_formatter"
                    | "do_suspend"
            )
        {
            self.msg("This function is disabled in restricted mode", 5);
            return;
        }
        let e = self.conf.enc();
        let no = self.conf.on(NO_NEWLINES);
        match fun {
            "" => {
                if !key.meta && (32..=255).contains(&key.code) {
                    if !self.can_change() {
                        return;
                    }
                    if self.b().softmark {
                        self.bm().state.mark = None;
                        self.bm().softmark = false;
                    }
                    let mut typed = vec![key.code as u8];
                    if !self.input.replay.is_empty() {
                        while self.input.replay.front().is_some_and(|k| {
                            !k.meta
                                && !k.shift
                                && k.command.is_none()
                                && (32..=255).contains(&k.code)
                                && k.code != 127
                        }) {
                            typed.push(self.input.replay.pop_front().unwrap().code as u8);
                        }
                    } else {
                        while self
                            .input
                            .queue
                            .front()
                            .is_some_and(|k| (32..=255).contains(k) && *k != 127)
                        {
                            let code = self.input.queue.pop_front().unwrap();
                            if self.recording {
                                self.macro_keys.push(Key::plain(code));
                            }
                            typed.push(code as u8);
                        }
                    }
                    self.bm().insert(&typed, "addition", true, no);
                    self.hard_wrap();
                    self.preferred();
                } else {
                    self.unbound(&key);
                }
                self.last_command.clear();
                return;
            }
            "do_left" => self.bm().move_h(e, false),
            "do_right" => self.bm().move_h(e, true),
            "do_up" => self.move_vertical(-1),
            "do_down" => self.move_vertical(1),
            "do_home" => {
                let pos = self.b().pos();
                let indent = e.indent(self.b().line());
                let l = render::layout(self);
                let rows = render::visual_rows(self.b(), &self.conf, l.width);
                let row = render::visual_cursor(self.b(), &self.conf, &rows);
                let from = rows[row].from;
                let x = if self.conf.on(SMART_HOME)
                    && pos.x != indent
                    && indent < self.b().line().len()
                    && from == 0
                {
                    indent
                } else if self.conf.on(SOFTWRAP) && e.column(self.b().line(), pos.x) != from {
                    e.actual(self.b().line(), from)
                } else {
                    0
                };
                self.bm().state.pos.x = x;
                self.preferred();
            }
            "do_end" => {
                let l = render::layout(self);
                let rows = render::visual_rows(self.b(), &self.conf, l.width);
                let row = render::visual_cursor(self.b(), &self.conf, &rows);
                let v = &rows[row];
                let target = if self.conf.on(SOFTWRAP)
                    && row + 1 < rows.len()
                    && rows[row + 1].line == v.line
                {
                    e.actual(self.b().line(), v.to.saturating_sub(1))
                } else {
                    self.b().line().len()
                };
                self.bm().state.pos.x = if self.b().pos().x == target {
                    self.b().line().len()
                } else {
                    target
                };
                self.preferred();
            }
            "to_prev_word" | "to_next_word" => {
                let p = self.b().word_target(
                    e,
                    fun == "to_next_word",
                    self.conf.on(AFTER_ENDS),
                    self.conf.on(WORD_BOUNDS),
                    &self.conf.value("wordchars"),
                );
                self.bm().state.pos = p;
                self.preferred();
            }
            "to_first_line" => {
                self.bm().state.pos = Pos::default();
                self.bm().top = 0;
                self.preferred();
            }
            "to_last_line" => {
                self.bm().state.pos = self.b().end();
                let l = render::layout(self);
                let all = render::visual_rows(self.b(), &self.conf, l.width);
                self.bm().top = all.len().saturating_sub(l.edit_rows);
                self.preferred();
            }
            "do_page_up" | "do_page_down" => self.page(fun == "do_page_down"),
            "to_prev_block" | "to_next_block" => self.block(fun == "to_next_block"),
            "to_para_begin" | "to_para_end" => self.paragraph_move(fun == "to_para_end"),
            "to_top_row" | "to_bottom_row" => {
                let l = render::layout(self);
                let rows = render::visual_rows(self.b(), &self.conf, l.width);
                let row = (self.b().top
                    + if fun == "to_bottom_row" {
                        l.edit_rows - 1
                    } else {
                        0
                    })
                .min(rows.len() - 1);
                let r = &rows[row];
                let line = &self.b().state.lines[r.line];
                let p = Pos {
                    line: r.line,
                    x: e.actual(line, r.from + self.b().preferred),
                };
                self.bm().set_pos(p);
            }
            "do_scroll_up" | "do_scroll_down" => self.scroll(fun == "do_scroll_down", 1),
            "do_center" | "do_refresh" | "full_refresh" => self.center(),
            "do_cycle" => {
                let l = render::layout(self);
                let row = self.cursor_row();
                let offset = match self.cycle % 3 {
                    0 => l.edit_rows / 2,
                    1 => 0,
                    _ => l.edit_rows - 1,
                };
                self.bm().top = row.saturating_sub(offset);
                self.cycle += 1;
            }
            "do_scroll_left" | "do_scroll_right" => {
                self.scroll_horizontal(fun == "do_scroll_right")
            }
            "do_enter" => {
                let auto = self.conf.on(AUTOINDENT);
                self.bm().enter(e, auto, no);
                self.preferred();
            }
            "do_tab" => {
                if self
                    .b()
                    .state
                    .mark
                    .is_some_and(|m| m.line != self.b().pos().line)
                {
                    self.indent(false);
                } else {
                    let tab = self
                        .syntax()
                        .and_then(|s| s.tab.clone())
                        .unwrap_or_else(|| {
                            if self.conf.on(TABS_TO_SPACES) {
                                vec![
                                    32;
                                    e.tab - e.column(self.b().line(), self.b().pos().x) % e.tab
                                ]
                            } else {
                                vec![9]
                            }
                        });
                    self.bm().insert(&tab, "addition", true, no);
                    self.hard_wrap();
                    self.preferred();
                }
            }
            "do_delete" | "do_backspace" => {
                let zap = self.conf.on(LET_THEM_ZAP);
                let region = self.b().state.mark.is_some();
                self.bm().delete(e, fun == "do_backspace", no, zap);
                if zap && region {
                    self.clear();
                }
                self.preferred();
            }
            "cut_text" | "zap_text" | "copy_text" | "cut_till_eof" => self.cut(fun),
            "paste_text" => {
                if self.cutbuffer.is_empty() {
                    self.msg("Cutbuffer is empty", 5);
                } else {
                    let raw = self.cutbuffer.clone();
                    self.bm().insert(&raw, "paste", false, no);
                    if !raw.contains(&10) {
                        self.hard_wrap();
                    }
                    self.clear();
                    self.preferred();
                }
            }
            "chop_previous_word" | "chop_next_word" => self.chop(fun == "chop_next_word"),
            "do_mark" => {
                if self.b().state.mark.is_some() {
                    self.bm().state.mark = None;
                    self.bm().softmark = false;
                    self.msg("Mark Unset", 1);
                } else {
                    let p = self.b().pos();
                    self.bm().state.mark = Some(p);
                    self.msg("Mark Set", 1);
                }
            }
            "do_indent" => self.indent(false),
            "do_unindent" => self.indent(true),
            "do_comment" => self.comment(),
            "complete_a_word" => self.complete_word(),
            "do_undo" | "do_redo" => {
                let redo = fun == "do_redo";
                if let Some(noun) = self.bm().undo(redo) {
                    self.msg(
                        native::tr(if redo { "Redid %s" } else { "Undid %s" })
                            .replace("%s", &native::tr(&noun)),
                        1,
                    );
                } else {
                    self.msg(
                        if redo {
                            "Nothing to redo"
                        } else {
                            "Nothing to undo"
                        },
                        5,
                    );
                }
                self.preferred();
            }
            "do_search_forward" | "do_search_backward" | "do_replace" => {
                self.conf.set(BACKWARDS_SEARCH, fun == "do_search_backward");
                self.prompt(PromptKind::Search(fun == "do_replace"), Vec::new());
            }
            "do_findnext" | "do_findprevious" => {
                self.conf.set(BACKWARDS_SEARCH, fun == "do_findprevious");
                self.find(false);
            }
            "do_gotolinecolumn" => self.prompt(PromptKind::Goto, Vec::new()),
            "do_find_bracket" => self.find_bracket(),
            "do_writeout" => self.prompt_write(false),
            "do_savefile" => {
                if self.b().name.is_empty() {
                    self.prompt_write(false);
                } else {
                    let p = Prompt::new(
                        PromptKind::Write {
                            exit: false,
                            mode: 0,
                        },
                        self.b().name.clone(),
                    );
                    self.try_write(p, false, false);
                }
            }
            "do_exit" => self.request_exit(),
            "discard_buffer" => self.close(2),
            "do_insertfile" => self.prompt(PromptKind::Insert, Vec::new()),
            "do_execute" => self.prompt(PromptKind::Execute, self.tool_answer.clone()),
            "switch_to_prev_buffer" => self.switch(false),
            "switch_to_next_buffer" => self.switch(true),
            "report_cursor_position" => self.report_position(),
            "count_lines_words_and_characters" => self.word_count(),
            "do_help" => self.open_help(Mode::Edit),
            "do_verbatim_input" => {
                self.msg("Verbatim Input", 3);
                render::draw(self);
                match self.input.verbatim(self.conf.utf8) {
                    Ok(raw) if raw != b"\n" => {
                        self.bm().insert(&raw, "addition", true, no);
                        self.clear();
                        self.preferred();
                    }
                    _ => self.msg("Invalid code", 5),
                }
            }
            "record_macro" => {
                if self.recording {
                    self.recording = false;
                    if self.macro_keys.is_empty() {
                        self.macro_keys = std::mem::take(&mut self.previous_macro);
                        self.msg("Cancelled", 2);
                    } else {
                        self.msg("Stopped recording", 2);
                    }
                } else {
                    self.previous_macro = std::mem::take(&mut self.macro_keys);
                    self.recording = true;
                    self.msg("Recording a macro...", 2);
                }
            }
            "run_macro" => {
                if self.recording {
                    self.msg("Cannot run macro while recording", 5);
                } else if self.macro_keys.is_empty() {
                    self.msg("Macro is empty", 5);
                } else {
                    self.input.replay.extend(self.macro_keys.clone());
                }
            }
            "do_justify" => self.justify(false),
            "do_full_justify" => self.justify(true),
            "do_spell" => self.spell(),
            "do_formatter" => self.format_tool(),
            "do_linter" => self.lint(),
            "do_suspend" => self.suspend(),
            "suggest_ctrlT_ctrlZ" => self.msg("To suspend, type ^T^Z", 5),
            "put_or_lift_anchor" => {
                let p = self.b().pos();
                let a = &mut self.bm().state.anchors[p.line];
                *a = !*a;
                let placed = *a;
                if !self.conf.on(LINE_NUMBERS) && !self.conf.on(MINIBAR) {
                    self.msg(
                        if placed {
                            "Placed anchor"
                        } else {
                            "Removed anchor"
                        },
                        if placed { 2 } else { 1 },
                    );
                }
            }
            "to_prev_anchor" | "to_next_anchor" => self.anchor(fun == "to_next_anchor"),
            "do_nothing" => {}
            _ => {
                if key.command.is_none() {
                    self.unbound(&key);
                }
            }
        }
        if fun != "do_cycle" {
            self.cycle = 0;
        }
        self.last_command = fun.into();
    }
    pub fn unbound(&mut self, k: &Key) {
        let msg = if k.code == 0x4fc {
            "Unknown sequence".into()
        } else if (265..=288).contains(&k.code) {
            format!("Unbound key: F{}", k.code - 264)
        } else if k.meta && k.code < 32 {
            format!("Unbindable key: M-^{}", (k.code + 64) as u8 as char)
        } else if k.meta && (65..=90).contains(&k.code) {
            format!("Unbound key: Sh-M-{}", k.code as u8 as char)
        } else if k.meta && k.code <= 127 {
            format!(
                "Unbound key: M-{}",
                (k.code as u8 as char).to_ascii_uppercase()
            )
        } else if k.code == 27 {
            "Unbindable key: ^[".into()
        } else if k.code < 32 {
            format!("Unbound key: ^{}", (k.code + 64) as u8 as char)
        } else if !k.meta && (32..127).contains(&k.code) {
            format!("Unbound key: {}", k.code as u8 as char)
        } else {
            "Unbound key".into()
        };
        self.msg(msg, 5);
        if let Some(m) = self.message.as_mut() {
            m.countdown = 1;
        }
    }
    pub fn toggle(&mut self, f: usize) {
        if f == 0 {
            return;
        }
        if f == TABS_TO_SPACES && self.syntax().is_some_and(|s| s.tab.is_some()) {
            self.msg("Current syntax determines Tab", 5);
            return;
        }
        let min = if self.conf.on(ZERO) {
            3
        } else if self.conf.on(MINIBAR) {
            4
        } else {
            5
        };
        if f == NO_HELP && unsafe { native::nr_rows() } < min {
            self.msg("Too tiny", 5);
            return;
        }
        self.conf.toggle(f);
        if f == ZERO {
            self.conf.set(NO_HELP, self.conf.on(ZERO));
            self.clear();
            return;
        }
        if f == CONSTANT_SHOW {
            if self.conf.on(ZERO) {
                self.conf.set(ZERO, false);
                self.conf.set(CONSTANT_SHOW, true);
            }
            self.clear();
            return;
        }
        if f == USE_MOUSE {
            unsafe {
                native::nr_mouse(self.conf.on(USE_MOUSE) as i32);
            }
        }
        if f == SOFTWRAP {
            self.bm().firstcol = 0;
        }
        if let Some((_, _, desc)) = TOGGLES.iter().find(|(_, flag, _)| *flag == f) {
            let enabled = self.conf.on(f) ^ (f == NO_HELP || f == NO_SYNTAX);
            self.msg(
                native::tr(if enabled { "%s enabled" } else { "%s disabled" })
                    .replace("%s", &native::tr(desc)),
                2,
            );
        }
    }
    pub fn syntax(&self) -> Option<&config::Syntax> {
        self.b().syntax.and_then(|i| self.conf.syntaxes.get(i))
    }
    pub fn prompt_write(&mut self, exit: bool) {
        let selection = self.b().state.mark.is_some() && !exit && !self.conf.on(RESTRICTED);
        self.prompt(
            PromptKind::Write { exit, mode: 0 },
            if selection {
                Vec::new()
            } else {
                self.b().name.clone()
            },
        );
    }
    pub fn request_exit(&mut self) {
        if !self.b().modified || self.conf.on(VIEW_MODE) {
            self.close(0);
        } else if self.conf.on(SAVE_ON_EXIT) && !self.b().name.is_empty() {
            let p = Prompt::new(
                PromptKind::Write {
                    exit: true,
                    mode: 0,
                },
                self.b().name.clone(),
            );
            self.try_write(p, false, false);
        } else {
            self.question("Save modified buffer? ", QuestionKind::Exit, false);
        }
    }
    pub fn close(&mut self, status: i32) {
        self.record_position();
        files::remove_lock(self.bm());
        if self.buffers.len() == 1 {
            self.exit = Some(status);
            return;
        }
        self.buffers.remove(self.current);
        if self.current >= self.buffers.len() {
            self.current = 0;
        }
        self.mode = Mode::Edit;
        self.buffer_message();
    }
    pub fn switch(&mut self, next: bool) {
        if self.buffers.len() == 1 {
            self.msg("No more open file buffers", 5);
            return;
        }
        self.current = if next {
            (self.current + 1) % self.buffers.len()
        } else {
            (self.current + self.buffers.len() - 1) % self.buffers.len()
        };
        self.buffer_message();
    }
    pub fn buffer_message(&mut self) {
        if let Some(msg) = self.bm().deferred.take() {
            self.msg(msg, 7);
            return;
        }
        if self.conf.on(ZERO) {
            return;
        }
        let name = if self.b().name.is_empty() {
            native::tr("New Buffer")
        } else {
            bytes::text(&self.b().name)
        };
        let n = self.b().line_count();
        let text = native::plural("%s -- %zu line", "%s -- %zu lines", n)
            .replace("%s", &name)
            .replace("%zu", &n.to_string());
        self.msg(
            format!("{text}{}", if self.b().dos { " (DOS)" } else { "" }),
            1,
        );
    }
}
