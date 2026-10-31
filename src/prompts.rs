//! Shared prompt editing and save/exit continuations (spec 17, 08).
use crate::{
    buffer::{Buffer, Pos},
    bytes,
    config::{self, parse_num},
    editor::*,
    files,
    generated::*,
    input::Key,
    native, render,
};
use std::{fs, os::unix::ffi::OsStrExt};
impl Editor {
    pub fn prompt_label(&self, p: &Prompt) -> String {
        match p.kind {
            PromptKind::Search(replace) => {
                let mut s = native::tr("Search");
                for (flag, text) in [
                    (CASE_SENSITIVE, " [Case sensitive]"),
                    (USE_REGEXP, " [Reg.exp.]"),
                    (BACKWARDS_SEARCH, " [Backwards]"),
                ] {
                    if self.conf.on(flag) {
                        s.push_str(&native::tr(text));
                    }
                }
                if replace {
                    s.push_str(&native::tr(if self.b().state.mark.is_some() {
                        " (to replace) in selection"
                    } else {
                        " (to replace)"
                    }));
                }
                if !self.search.is_empty() {
                    let e = self.conf.enc();
                    let max = unsafe { native::nr_cols() }.max(1) as usize / 3;
                    let n = e.actual(&self.search, max);
                    s.push_str(" [");
                    s.push_str(&bytes::text(&self.search[..n]));
                    if n < self.search.len() {
                        s.push_str("...");
                    }
                    s.push(']');
                }
                s
            }
            PromptKind::ReplaceWith => native::tr("Replace with"),
            PromptKind::Goto => native::tr("Enter line number, column number"),
            PromptKind::Write { exit, mode } => {
                let selection = self.b().state.mark.is_some() && !exit && !self.conf.on(RESTRICTED);
                let mut s = native::tr(match (mode, selection) {
                    (1, false) => "Append to File",
                    (2, false) => "Prepend to File",
                    (1, true) => "Append Selection to File",
                    (2, true) => "Prepend Selection to File",
                    (_, true) => "Write Selection to File",
                    _ => "Write to File",
                });
                if self.b().dos {
                    s.push_str(&native::tr(" [DOS Format]"));
                }
                if self.conf.on(MAKE_BACKUP) {
                    s.push_str(&native::tr(" [Backup]"));
                }
                s
            }
            PromptKind::Insert => {
                native::tr(match (self.conf.on(NEW_BUFFER), self.conf.on(NO_CONVERT)) {
                    (false, false) => "File to insert [from %s]",
                    (false, true) => "File to insert unconverted [from %s]",
                    (true, false) => "File to read into new buffer [from %s]",
                    _ => "File to read unconverted into new buffer [from %s]",
                })
                .replace(
                    "%s",
                    &if self.conf.value("operatingdir").is_empty() {
                        "./".into()
                    } else {
                        format!("{}/", bytes::text(&self.conf.value("operatingdir")))
                    },
                )
            }
            PromptKind::Execute => native::tr(if self.conf.on(NEW_BUFFER) {
                "Command to execute in new buffer"
            } else {
                "Command to execute"
            }),
            PromptKind::BrowserSearch | PromptKind::HelpSearch => {
                let mut label = native::tr("Search");
                if !self.search.is_empty() {
                    label.push_str(&format!(" [{}]", bytes::text(&self.search)));
                }
                label
            }
            PromptKind::BrowserGoto => native::tr("Go To Directory"),
            PromptKind::Spell => native::tr("Edit a replacement"),
        }
    }
    pub fn prompt_key(&mut self, mut p: Prompt, key: Key, fun: &str, toggle: usize) {
        let e = self.conf.enc();
        let frozen = self.conf.on(RESTRICTED)
            && matches!(p.kind, PromptKind::Write { .. })
            && !self.b().name.is_empty();
        // Without TABCOMP and the full prompt-edit handlers, upstream tiny
        // dispatches these shortcuts to the buffer and returns from the prompt.
        // Write/Insert then use the answer; Search/Goto simply finish.
        if cfg!(feature = "tiny")
            && matches!(
                fun,
                "do_tab" | "copy_text" | "paste_text" | "to_prev_word" | "to_next_word"
            )
            && !(frozen && fun == "paste_text")
        {
            if self.conf.on(VIEW_MODE) && matches!(fun, "do_tab" | "paste_text") {
                unsafe {
                    native::nr_beep();
                }
                self.mode = Mode::Prompt(p);
                return;
            }
            self.mode = Mode::Edit;
            self.key(Key {
                command: Some(fun.into()),
                ..key
            });
            if matches!(p.kind, PromptKind::Write { .. } | PromptKind::Insert) {
                self.submit(p);
            }
            return;
        }
        let hist = match p.kind {
            PromptKind::Search(_) | PromptKind::BrowserSearch => Some(0),
            PromptKind::ReplaceWith => Some(1),
            PromptKind::Execute => Some(2),
            _ => None,
        };
        match fun {
            "do_cancel" => {
                if matches!(p.kind, PromptKind::HelpSearch) {
                    if let Some(h) = self.help_saved.take() {
                        self.mode = Mode::Help(h);
                    }
                    self.msg("Cancelled", 1);
                    return;
                }
                if matches!(p.kind, PromptKind::Insert | PromptKind::Execute) {
                    self.conf.set(NEW_BUFFER, p.initial_newbuffer);
                }
                if matches!(p.kind, PromptKind::Spell) {
                    self.finish_spell();
                    return;
                }
                if matches!(p.kind, PromptKind::BrowserSearch | PromptKind::BrowserGoto)
                    && let Some(b) = self.browser_saved.take()
                {
                    self.mode = Mode::Browser(b);
                    self.msg("Cancelled", 1);
                    return;
                }
                self.cancelled();
                return;
            }
            "do_enter" => {
                self.submit(p);
                return;
            }
            "do_help" => {
                self.open_help(Mode::Prompt(p));
                return;
            }
            "do_toggle" if toggle == NO_HELP => {
                self.toggle(toggle);
            }
            "do_left" => p.x = e.move_left(&p.answer, p.x),
            "do_right" => p.x = e.move_right(&p.answer, p.x),
            "do_home" => p.x = 0,
            "do_end" => p.x = p.answer.len(),
            "to_prev_word" | "to_next_word" => {
                let mut b = Buffer::new(vec![], vec![p.answer.clone()]);
                b.state.pos.x = p.x;
                p.x = b
                    .word_target(
                        e,
                        fun == "to_next_word",
                        self.conf.on(AFTER_ENDS),
                        self.conf.on(WORD_BOUNDS),
                        &self.conf.value("wordchars"),
                    )
                    .x;
            }
            "do_backspace" if !frozen => {
                if p.x > 0 {
                    let x = e.left(&p.answer, p.x);
                    p.answer.drain(x..p.x);
                    p.x = x;
                }
            }
            "do_delete" if !frozen => {
                if p.x < p.answer.len() {
                    let end = e.move_right(&p.answer, p.x);
                    p.answer.drain(p.x..end);
                }
            }
            "cut_text" if !frozen => {
                if p.x == p.answer.len() {
                    p.answer.clear();
                    p.x = 0;
                } else {
                    p.answer.truncate(p.x);
                }
            }
            "copy_text" if !frozen => {
                if !p.answer.is_empty() {
                    self.cutbuffer = bytes::decode_nuls(&p.answer);
                    p.x = 0;
                }
            }
            "paste_text" if !frozen => {
                let raw = self
                    .cutbuffer
                    .split(|b| *b == 10)
                    .next()
                    .unwrap_or_default();
                let raw = bytes::encode_nuls(raw);
                p.answer.splice(p.x..p.x, raw.clone());
                p.x += raw.len();
            }
            "do_verbatim_input" if !frozen => {
                self.mode = Mode::Prompt(p.clone());
                render::draw(self);
                if let Ok(raw) = self.input.verbatim(self.conf.utf8)
                    && (raw != b"\0"
                        || !matches!(p.kind, PromptKind::Write { .. } | PromptKind::Insert))
                {
                    let raw = bytes::encode_nuls(&raw);
                    p.answer.splice(p.x..p.x, raw.clone());
                    p.x += raw.len();
                }
            }
            "get_older_item" | "get_newer_item" => {
                if let Some(h) = hist {
                    let n = self.histories[h].len();
                    if p.history.is_none() {
                        p.remembered = p.answer.clone();
                        p.history = Some(n);
                    }
                    let i = p.history.unwrap();
                    let i = if fun == "get_older_item" {
                        i.saturating_sub(1)
                    } else {
                        (i + 1).min(n)
                    };
                    p.history = Some(i);
                    p.answer = if i == n {
                        p.remembered.clone()
                    } else {
                        self.histories[h][i].clone()
                    };
                    p.x = p.answer.len();
                }
            }
            "do_tab" if !frozen => {
                if let Some(h) = hist {
                    if p.fragment.is_empty() {
                        p.fragment = p.answer.clone();
                    }
                    let n = self.histories[h].len();
                    let start = p.history.unwrap_or(n);
                    for offset in 1..=n {
                        let i = (start + n - offset) % n;
                        if self.histories[h][i].starts_with(&p.fragment)
                            && self.histories[h][i] != p.answer
                        {
                            p.history = Some(i);
                            p.answer = self.histories[h][i].clone();
                            p.x = p.answer.len();
                            break;
                        }
                    }
                } else if matches!(
                    p.kind,
                    PromptKind::Write { .. } | PromptKind::Insert | PromptKind::BrowserGoto
                ) && !self.conf.on(RESTRICTED)
                {
                    self.filename_complete(&mut p);
                }
            }
            "case_sens_void" => self.conf.toggle(CASE_SENSITIVE),
            "regexp_void" => self.conf.toggle(USE_REGEXP),
            "backwards_void" => self.conf.toggle(BACKWARDS_SEARCH),
            "flip_replace" => {
                if !self.conf.on(VIEW_MODE) {
                    p.kind = match p.kind {
                        PromptKind::Search(b) => PromptKind::Search(!b),
                        _ => p.kind,
                    };
                } else {
                    self.msg("Key is invalid in view mode", 5);
                }
            }
            "flip_goto" => {
                p.kind = if matches!(p.kind, PromptKind::Goto) {
                    PromptKind::Search(false)
                } else {
                    PromptKind::Goto
                }
            }
            "flip_newbuffer" => {
                if !self.conf.on(VIEW_MODE) {
                    self.conf.toggle(NEW_BUFFER);
                }
            }
            "flip_convert" => self.conf.toggle(NO_CONVERT),
            "flip_execute" => {
                let from_execute = matches!(p.kind, PromptKind::Execute);
                if from_execute {
                    self.tool_answer = p.answer.clone();
                }
                let next = if !from_execute && p.other_answer.is_empty() {
                    self.tool_answer.clone()
                } else {
                    std::mem::take(&mut p.other_answer)
                };
                p.other_answer = std::mem::replace(&mut p.answer, next);
                p.kind = if from_execute {
                    PromptKind::Insert
                } else {
                    PromptKind::Execute
                };
                p.x = p.answer.len();
            }
            "flip_pipe" => {
                p.answer.insert(0, b'|');
                p.x += 1;
            }
            "dos_format" => {
                self.bm().dos = !self.b().dos;
            }
            "back_it_up" => self.conf.toggle(MAKE_BACKUP),
            "append_it" | "prepend_it" => {
                if let PromptKind::Write { mode, .. } = &mut p.kind {
                    let m = if fun == "append_it" { 1 } else { 2 };
                    *mode = if *mode == m { 0 } else { m };
                    if p.answer == self.b().name {
                        p.answer.clear();
                        p.x = 0;
                    }
                }
            }
            "discard_buffer" => {
                self.close(2);
                return;
            }
            "to_files" => {
                self.open_browser(p);
                return;
            }
            "to_first_line" | "to_last_line" => {
                self.key(Key {
                    command: Some(fun.into()),
                    ..Key::plain(0)
                });
                return;
            }
            "do_full_justify" | "do_spell" | "do_linter" | "do_formatter" | "cut_till_eof"
            | "do_suspend" => {
                self.tool_answer = p.answer.clone();
                self.key(Key {
                    command: Some(fun.into()),
                    ..Key::plain(0)
                });
                return;
            }
            "full_refresh" | "do_refresh" | "do_nothing" => {}
            "" if !frozen && !key.meta && (32..=255).contains(&key.code) => {
                p.answer.insert(p.x, key.code as u8);
                p.x += 1;
            }
            _ => unsafe {
                native::nr_beep();
            },
        }
        if fun != "do_tab" {
            p.fragment.clear();
        }
        self.mode = Mode::Prompt(p);
    }
    pub fn submit(&mut self, p: Prompt) {
        self.completion.clear();
        match p.kind {
            PromptKind::Write { .. } => self.try_write(p, false, false),
            PromptKind::Search(replace) => {
                if !p.answer.is_empty() {
                    self.search = p.answer.clone();
                    self.add_history(0, p.answer);
                }
                if self.search.is_empty() {
                    self.cancelled();
                    return;
                }
                if !self.validate_search() {
                    return;
                }
                if replace {
                    self.prompt(PromptKind::ReplaceWith, Vec::new());
                } else {
                    self.mode = Mode::Edit;
                    self.find(false);
                }
            }
            PromptKind::ReplaceWith => {
                if !p.answer.is_empty() {
                    self.add_history(1, p.answer.clone());
                }
                self.start_replace(p.answer);
            }
            PromptKind::Goto => {
                if p.answer.is_empty() {
                    self.cancelled();
                } else {
                    self.goto(&p.answer, false);
                }
            }
            PromptKind::Insert => {
                self.insert_file(p.answer);
                self.conf.set(NEW_BUFFER, p.initial_newbuffer);
            }
            PromptKind::Execute => {
                self.execute(p.answer);
                self.conf.set(NEW_BUFFER, p.initial_newbuffer);
            }
            PromptKind::BrowserSearch => {
                if let Some(mut b) = self.browser_saved.take() {
                    if !p.answer.is_empty() {
                        self.search = p.answer.clone();
                        self.add_history(0, p.answer);
                    }
                    let pat = self.search.clone();
                    let n = b.entries.len();
                    let mut found = false;
                    for step in 1..=n {
                        let i = (b.selected + step) % n;
                        let name = b.entries[i].file_name().unwrap_or_default().as_bytes();
                        if crate::search::literal(&self.conf, name, &pat, 0, false).is_some() {
                            if i <= b.selected {
                                self.msg("Search Wrapped", 1);
                            }
                            if i == b.selected {
                                self.msg("This is the only occurrence", 1);
                            }
                            b.selected = i;
                            found = true;
                            break;
                        }
                    }
                    if !found {
                        self.msg(format!("\"{}\" not found", bytes::text(&pat)), 5);
                    }
                    self.mode = Mode::Browser(b);
                }
            }
            PromptKind::BrowserGoto => {
                if let Some(mut b) = self.browser_saved.take() {
                    let path = config::expand(&p.answer);
                    let target = if path.is_absolute() {
                        path
                    } else {
                        b.dir.join(path)
                    };
                    if !files::inside(&self.conf, &target) {
                        self.msg(
                            format!(
                                "Can't go outside of {}",
                                bytes::text(&self.conf.value("operatingdir"))
                            ),
                            7,
                        );
                    } else if let Ok(dir) = fs::canonicalize(&target) {
                        b.dir = dir;
                        b.selected = 0;
                    } else {
                        self.msg("Cannot open directory: No such file or directory", 7);
                    }
                    self.mode = Mode::Browser(b);
                    self.refresh_browser();
                }
            }
            PromptKind::HelpSearch => {
                if !p.answer.is_empty() {
                    self.search = p.answer;
                }
                if let Some(h) = self.help_saved.take() {
                    self.help_find(h, false);
                }
            }
            PromptKind::Spell => {
                if p.answer == self.search {
                    self.next_spell();
                } else {
                    self.start_replace(p.answer);
                }
            }
        }
    }
    pub fn question_key(&mut self, q: Question, key: Key, fun: &str) {
        if fun == "do_toggle" {
            self.toggle(NO_HELP);
            self.mode = Mode::Question(q);
            return;
        }
        if fun == "full_refresh" {
            self.mode = Mode::Question(q);
            return;
        }
        let ch = if key.meta {
            None
        } else {
            u8::try_from(key.code).ok()
        };
        let yes = ch.is_some_and(|c| {
            c == 25 || native::tr("Yy").as_bytes().contains(&c) || b"Yy".contains(&c)
        });
        let no = ch.is_some_and(|c| {
            c == 14 || native::tr("Nn").as_bytes().contains(&c) || b"Nn".contains(&c)
        });
        let all = q.all
            && ch.is_some_and(|c| {
                c == 1 || native::tr("Aa").as_bytes().contains(&c) || b"Aa".contains(&c)
            });
        let cancel = fun == "do_cancel" || ch == Some(3);
        let discard = ch
            == Some(if self.conf.on(MODERN_BINDINGS) {
                24
            } else {
                17
            });
        if !yes && !no && !all && !cancel && !discard {
            unsafe {
                native::nr_beep();
            }
            self.mode = Mode::Question(q);
            return;
        }
        match q.kind {
            QuestionKind::Exit => {
                if yes {
                    self.prompt_write(true);
                } else if no || discard {
                    self.close(if discard { 2 } else { 0 });
                } else {
                    self.cancelled();
                }
            }
            QuestionKind::Different(p) => {
                if yes {
                    self.try_write(p, true, false);
                } else {
                    self.mode = Mode::Prompt(p);
                }
            }
            QuestionKind::Overwrite(p) => {
                if yes {
                    self.try_write(p, true, true);
                } else {
                    self.mode = Mode::Prompt(p);
                }
            }
            QuestionKind::Backup(mut p, error) => {
                if yes {
                    p.skip_backup = true;
                    self.try_write(p, true, true);
                } else {
                    self.mode = Mode::Edit;
                    self.msg(error, 2);
                }
            }
            QuestionKind::Changed(p) => {
                if yes {
                    self.try_write(p, true, true);
                } else if cancel {
                    self.mode = Mode::Prompt(p);
                } else {
                    self.cancelled();
                }
            }
            QuestionKind::Replace => {
                if cancel || discard {
                    self.finish_replace();
                } else {
                    self.replace_answer(yes || all, all);
                }
            }
            QuestionKind::Lock(i) => {
                if yes {
                    if let Err(msg) = files::lock(&mut self.buffers[i]) {
                        self.msg(msg, 6);
                    }
                    self.mode = Mode::Edit;
                    self.msg(
                        files::line_message(
                            "Read",
                            self.buffers[i].line_count(),
                            self.buffers[i].dos,
                        ),
                        2,
                    );
                } else if cancel {
                    self.exit = Some(0);
                } else if self.buffers.len() == 1 {
                    self.buffers = vec![Buffer::default()];
                    self.current = 0;
                    self.mode = Mode::Edit;
                } else {
                    self.buffers.remove(i);
                    self.current = 0;
                    self.mode = Mode::Edit;
                }
            }
            QuestionKind::LintSave => {
                if yes {
                    let p = Prompt::new(
                        PromptKind::Write {
                            exit: false,
                            mode: 0,
                        },
                        self.b().name.clone(),
                    );
                    self.try_write(p, false, false);
                    self.lint();
                } else if no {
                    self.lint_run();
                } else {
                    self.cancelled();
                }
            }
        }
    }
    pub fn try_write(&mut self, p: Prompt, confirmed_name: bool, confirmed_disk: bool) {
        let PromptKind::Write { exit, mode } = p.kind else {
            return;
        };
        if p.answer.is_empty() {
            self.cancelled();
            return;
        }
        let selection = self.b().state.mark.is_some() && !exit && !self.conf.on(RESTRICTED);
        let target = config::expand(&p.answer);
        let same = target == config::expand(&self.b().name)
            || fs::canonicalize(&target)
                .ok()
                .zip(fs::canonicalize(config::expand(&self.b().name)).ok())
                .is_some_and(|(a, b)| a == b);
        if mode == 0 && !confirmed_name && !same && !self.b().name.is_empty() && !selection {
            if self.conf.on(RESTRICTED) {
                self.msg("File exists -- cannot overwrite", 7);
                self.mode = Mode::Prompt(p);
                return;
            }
            self.question(
                "Save file under DIFFERENT NAME? ",
                QuestionKind::Different(p),
                false,
            );
            return;
        }
        if mode == 0 && !confirmed_disk && target.exists() && !same {
            if self.conf.on(RESTRICTED) {
                self.msg("File exists -- cannot overwrite", 7);
                self.mode = Mode::Prompt(p);
                return;
            }
            self.question(
                format!("File \"{}\" exists; OVERWRITE? ", bytes::text(&p.answer)),
                QuestionKind::Overwrite(p),
                false,
            );
            return;
        }
        if mode == 0 && !confirmed_disk && files::changed(self.b(), &p.answer) {
            self.mode = Mode::Edit;
            self.msg("File on disk has changed", 7);
            self.pause_painted = false;
            self.pause_duration = std::time::Duration::from_millis(1500);
            self.pause_until =
                Some(std::time::Instant::now() + std::time::Duration::from_millis(1500));
            self.pause_next = Some(Box::new(Mode::Question(Question {
                text: "File was modified since you opened it; continue saving? ".into(),
                kind: QuestionKind::Changed(p),
                all: false,
            })));
            return;
        }
        let i = self.current;
        let layout = render::layout(self);
        let mut progress_screen = self
            .last_screen
            .clone()
            .unwrap_or_else(|| render::Canvas::new(layout.cols, layout.rows));
        let progress_style = self.conf.style("statuscolor");
        let progress_allowed = self.action_level <= 4;
        let mut progress_painted = false;
        // Accepting the filename ends prompt input, even if opening blocks or fails.
        unsafe { native::nr_hide_cursor() };
        let result = files::write(
            &self.conf,
            &mut self.buffers[i],
            &p.answer,
            mode,
            selection,
            p.skip_backup,
            |text| {
                if progress_allowed {
                    render::write_progress(&mut progress_screen, layout, progress_style, text);
                    progress_painted = true;
                }
            },
        );
        if progress_painted {
            self.last_screen = Some(progress_screen);
        }
        match result {
            Ok(n) => {
                self.mode = Mode::Edit;
                self.msg(files::line_message("Wrote", n, false), 2);
                if exit {
                    self.close(0);
                }
            }
            Err(error) => {
                if error.confirm_backup {
                    self.question(
                        "Cannot make backup; continue and save actual file? ",
                        QuestionKind::Backup(p, error.message),
                        false,
                    );
                    return;
                }
                self.mode = Mode::Edit;
                let no_space = error.errno == Some(28);
                self.msg(error.message, 7);
                if no_space {
                    self.pause_screen = self.last_screen.clone();
                    self.pause_painted = false;
                    self.pause_duration = std::time::Duration::from_millis(3200);
                    self.pause_until = Some(std::time::Instant::now() + self.pause_duration);
                    self.io_warnings.push_back((
                        "File on disk has been truncated!".into(),
                        self.pause_duration,
                    ));
                    self.io_warnings.push_back((
                        "Maybe ^T^Z, make room on disk, resume, then ^S^X".into(),
                        std::time::Duration::ZERO,
                    ));
                }
            }
        }
    }
    pub fn insert_file(&mut self, name: Vec<u8>) {
        let new = self.conf.on(NEW_BUFFER);
        if name.is_empty() {
            if new {
                self.new_buffer(Buffer::default());
            } else {
                self.cancelled();
            }
            return;
        }
        if new {
            match files::open(&self.conf, &name, false) {
                Ok((b, msg, level)) => {
                    self.new_buffer(b);
                    self.msg(msg, level);
                }
                Err(msg) => self.msg(msg, 7),
            }
            return;
        }
        let path = config::expand(&name);
        if !files::inside(&self.conf, &path) {
            self.msg(
                format!(
                    "Can't read file from outside of {}",
                    bytes::text(&self.conf.value("operatingdir"))
                ),
                7,
            );
            return;
        }
        match fs::read(&path) {
            Ok(raw) => {
                let (lines, dos, n) = files::parse(&raw, !self.conf.on(NO_CONVERT));
                let b = Buffer::new(vec![], lines);
                let raw = b.raw();
                let no = self.conf.on(NO_NEWLINES);
                self.bm().insert(&raw, "insertion", false, no);
                self.preferred();
                self.mode = Mode::Edit;
                self.msg(files::line_message("Read", n, dos), 2);
            }
            Err(_) => {
                self.mode = Mode::Edit;
                self.msg(
                    native::tr("File \"%s\" not found").replace("%s", &bytes::text(&name)),
                    7,
                );
            }
        }
    }
    pub fn new_buffer(&mut self, b: Buffer) {
        self.current += 1;
        self.buffers.insert(self.current, b);
        self.multiple = true;
        self.mode = Mode::Edit;
    }
    pub fn add_history(&mut self, h: usize, value: Vec<u8>) {
        if cfg!(feature = "tiny") {
            return;
        }
        if value.is_empty() {
            return;
        }
        self.histories[h].retain(|s| *s != value);
        self.histories[h].push(value);
        if self.histories[h].len() > 100 {
            self.histories[h].remove(0);
        }
        self.history_changed = true;
    }
    pub fn filename_complete(&mut self, p: &mut Prompt) {
        if cfg!(feature = "tiny") {
            return;
        }
        if p.x != p.answer.len() {
            unsafe {
                native::nr_beep();
            }
            return;
        }
        let base = if matches!(p.kind, PromptKind::BrowserGoto) {
            self.browser_saved.as_ref().map(|b| b.dir.clone())
        } else {
            None
        };
        let i = p
            .answer
            .iter()
            .rposition(|b| *b == b'/')
            .map(|i| i + 1)
            .unwrap_or(0);
        let dir = if i == 0 {
            base.unwrap_or_else(|| config::path(b"."))
        } else {
            let d = config::expand(&p.answer[..i]);
            if d.is_absolute() {
                d
            } else {
                base.unwrap_or_else(|| config::path(b".")).join(d)
            }
        };
        let prefix = &p.answer[i..];
        let mut candidates = Vec::new();
        if let Ok(entries) = fs::read_dir(&dir) {
            for entry in entries.flatten() {
                let name = entry.file_name().as_bytes().to_vec();
                if name.starts_with(prefix)
                    && files::inside(&self.conf, &entry.path())
                    && (!matches!(p.kind, PromptKind::BrowserGoto) || entry.path().is_dir())
                {
                    candidates.push((name, entry.path().is_dir()));
                }
            }
        }
        candidates.sort_by(|a, b| {
            b.1.cmp(&a.1)
                .then(a.0.to_ascii_lowercase().cmp(&b.0.to_ascii_lowercase()))
                .then(a.0.cmp(&b.0))
        });
        if candidates.is_empty() {
            unsafe {
                native::nr_beep();
            }
            return;
        }
        let mut common = candidates[0].0.clone();
        for (name, _) in &candidates[1..] {
            let n = common.iter().zip(name).take_while(|(a, b)| a == b).count();
            common.truncate(n);
        }
        while std::str::from_utf8(&common).is_err() && !common.is_empty() {
            common.pop();
        }
        if candidates.len() == 1 && candidates[0].1 {
            common.push(b'/');
        }
        p.answer.truncate(i);
        p.answer.extend(common);
        p.x = p.answer.len();
        if candidates.len() > 1 {
            self.completion = candidates.into_iter().map(|(n, _)| n).collect();
            unsafe {
                native::nr_beep();
            }
        } else {
            self.completion.clear();
        }
    }
    pub fn startup_position(&mut self, pos: &[u8]) {
        if cfg!(feature = "tiny") {
            self.goto(pos, true);
            return;
        }
        if pos.first().is_some_and(u8::is_ascii_alphabetic)
            || pos.starts_with(b"/")
            || pos.starts_with(b"?")
        {
            let mut i = 0;
            while i < pos.len() && pos[i].is_ascii_alphabetic() {
                match pos[i] {
                    b'c' => self.conf.set(CASE_SENSITIVE, true),
                    b'C' => self.conf.set(CASE_SENSITIVE, false),
                    b'r' => self.conf.set(USE_REGEXP, true),
                    b'R' => self.conf.set(USE_REGEXP, false),
                    c => self.msg(format!("Invalid search modifier '{}'", c as char), 7),
                }
                i += 1;
            }
            if i < pos.len() && matches!(pos[i], b'/' | b'?') {
                self.conf.set(BACKWARDS_SEARCH, pos[i] == b'?');
                self.search = pos[i + 1..].to_vec();
                if self.search.is_empty() {
                    self.msg("Empty search string", 7);
                } else {
                    self.find(true);
                }
                return;
            }
        }
        self.goto(pos, true);
    }
    pub fn goto(&mut self, raw: &[u8], startup: bool) {
        let text = bytes::text(raw);
        let current = self.b().pos();
        let mut valid = true;
        let mut line = if raw.is_empty() {
            self.b().state.lines.len() as i64
        } else {
            current.line as i64 + 1
        };
        let mut column = self.b().preferred as i64 + 1;
        let parts: Vec<&str> = text.splitn(2, [',', '.', ':']).collect();
        let rel = parts[0].starts_with("++") || parts[0].starts_with("--");
        let num = if rel { &parts[0][1..] } else { parts[0] };
        if !num.is_empty() {
            if let Some(n) = parse_num(num) {
                line = if rel {
                    (current.line as i64 + 1 + n).max(1)
                } else if n < 0 {
                    self.b().state.lines.len() as i64 + n + 1
                } else if n == 0 {
                    current.line as i64 + 1
                } else {
                    n
                };
            } else {
                valid = false;
            }
        }
        if parts.len() > 1 {
            if let Some(n) = parse_num(parts[1]) {
                column = n;
            } else {
                valid = false;
            }
        }
        let l = (line.max(1) as usize - 1).min(self.b().state.lines.len() - 1);
        let e = self.conf.enc();
        if column < 0 {
            column = e.breadth(&self.b().state.lines[l]) as i64 + column + 2;
        }
        if column == 0 {
            column = self.b().preferred as i64 + 1;
        }
        let col = column.max(1) as usize - 1;
        let p = Pos {
            line: l,
            x: e.actual(&self.b().state.lines[l], col),
        };
        self.bm().state.pos = p;
        self.bm().preferred = col;
        self.mode = Mode::Edit;
        self.center();
        if startup {
            let layout = render::layout(self);
            let rows = render::visual_rows(self.b(), &self.conf, layout.width);
            if self.cursor_row() + layout.edit_rows / 2 >= rows.len() {
                self.bm().top = rows.len().saturating_sub(layout.edit_rows);
            }
        }
        if !valid {
            self.msg("Invalid line or column number", if startup { 7 } else { 5 });
        } else if !startup {
            self.clear();
        }
    }
}
