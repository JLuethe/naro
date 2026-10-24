//! POSIX search, interactive replace and bracket matching.
use crate::native;
use crate::{buffer::Pos, bytes, config::Config, editor::*, generated::*, native::Regex};
pub fn literal(
    c: &Config,
    hay: &[u8],
    needle: &[u8],
    start: usize,
    case: bool,
) -> Option<(usize, usize)> {
    if needle.is_empty() {
        return Some((start, start));
    }
    let e = c.enc();
    let mut i = start;
    while i <= hay.len() {
        if case {
            if hay[i..].starts_with(needle) {
                return Some((i, i + needle.len()));
            }
        } else {
            let (mut x, mut n) = (i, 0);
            while x < hay.len() && n < needle.len() {
                let (a, b) = if c.utf8 {
                    (e.code(hay, x), e.code(needle, n))
                } else {
                    (
                        Some(unsafe { crate::native::nr_byte_lower(hay[x] as i32) } as u32),
                        Some(unsafe { crate::native::nr_byte_lower(needle[n] as i32) } as u32),
                    )
                };
                let same = match (a, b) {
                    (Some(a), Some(b)) => {
                        (unsafe { crate::native::nr_lower(a) })
                            == (unsafe { crate::native::nr_lower(b) })
                    }
                    (None, None) => hay[x] == needle[n],
                    _ => false,
                };
                if !same {
                    break;
                }
                x = e.right(hay, x);
                n = e.right(needle, n);
            }
            if n == needle.len() {
                return Some((i, x));
            }
        }
        if i == hay.len() {
            break;
        }
        i = e.right(hay, i);
    }
    None
}
impl Editor {
    pub fn validate_search(&mut self) -> bool {
        if self.conf.on(USE_REGEXP)
            && let Err(e) = Regex::new(&self.search, !self.conf.on(CASE_SENSITIVE))
        {
            self.mode = Mode::Edit;
            self.msg(
                format!("Bad regex \"{}\": {e}", bytes::text(&self.search)),
                5,
            );
            return false;
        }
        true
    }
    pub(crate) fn all_matches(&self, overlapping: bool) -> Result<Vec<Match>, String> {
        let re = if self.conf.on(USE_REGEXP) {
            Some(Regex::new(&self.search, !self.conf.on(CASE_SENSITIVE))?)
        } else {
            None
        };
        let mut all = Vec::new();
        let mut skipone = false;
        let e = self.conf.enc();
        for (line, s) in self.b().state.lines.iter().enumerate() {
            if line + 1 == self.b().state.lines.len() && s.is_empty() {
                continue;
            }
            let mut from = 0;
            while from <= s.len() {
                let m = if let Some(r) = &re {
                    r.find(s, from, false)
                } else {
                    literal(
                        &self.conf,
                        s,
                        &self.search,
                        from,
                        self.conf.on(CASE_SENSITIVE),
                    )
                    .map(|m| vec![m])
                };
                let Some(groups) = m else {
                    break;
                };
                let (a, b) = groups[0];
                if a > s.len() || b > s.len() || a > b {
                    break;
                }
                all.push((Pos { line, x: a }, Pos { line, x: b }, groups));
                if !overlapping && b > a {
                    if b >= s.len() {
                        break;
                    }
                    from = if skipone { e.right(s, b) } else { b };
                } else {
                    if a >= s.len() {
                        break;
                    }
                    from = e.right(s, a);
                    if !overlapping {
                        skipone = true;
                    }
                }
            }
        }
        Ok(all)
    }
    pub fn find(&mut self, startup: bool) {
        if self.search.is_empty() {
            if let Some(s) = self.histories[0].last() {
                self.search = s.clone();
            } else {
                self.msg("No current search pattern", 5);
                return;
            }
        }
        if !self.validate_search() {
            return;
        }
        let matches = match self.all_matches(true) {
            Ok(m) => m,
            Err(_) => return,
        };
        let p = self.b().pos();
        let back = self.conf.on(BACKWARDS_SEARCH);
        let picked = if back {
            matches
                .iter()
                .rev()
                .find(|(a, _, _)| if startup { *a <= p } else { *a < p })
        } else {
            matches
                .iter()
                .find(|(a, _, _)| if startup { *a >= p } else { *a > p })
        };
        let wrapped = picked.is_none();
        let picked = picked.or_else(|| {
            if back {
                matches.last()
            } else {
                matches.first()
            }
        });
        if let Some((a, b, _)) = picked {
            let (a, b) = (*a, *b);
            self.bm().state.pos = a;
            self.preferred();
            let l = crate::render::layout(self);
            let row = self.cursor_row();
            if startup || row < self.b().top || row >= self.b().top + l.edit_rows {
                self.center();
            }
            self.spotlight = Some((a.line, a.x, b.x));
            self.spotlight_time = std::time::Instant::now();
            self.spotlight_time = std::time::Instant::now();
            if !startup {
                if a == p {
                    self.msg("This is the only occurrence", 2);
                } else if wrapped {
                    self.msg("Search Wrapped", 2);
                } else {
                    self.clear();
                }
            } else if self.action_level < 5 {
                self.clear();
            }
        } else {
            let max = unsafe { crate::native::nr_cols() }.max(1) as usize / 2;
            let n = self.conf.enc().actual(&self.search, max);
            let needle = format!(
                "{}{}",
                bytes::text(&self.search[..n]),
                if n < self.search.len() { "..." } else { "" }
            );
            self.msg(
                native::tr("\"%.*s%s\" not found").replacen("%.*s%s", &needle, 1),
                5,
            );
        }
    }
    pub fn start_replace(&mut self, replacement: Vec<u8>) {
        let mut matches = match self.all_matches(false) {
            Ok(m) => m,
            Err(e) => {
                self.msg(e, 5);
                return;
            }
        };
        if self.spelling.is_some() {
            let e = self.conf.enc();
            matches.retain(|(a, b, _)| {
                let s = &self.b().state.lines[a.line];
                (a.x == 0 || !e.word(s, e.left(s, a.x), false, &[]))
                    && (b.x == s.len() || !e.word(s, b.x, false, &[]))
            });
        }
        let original = self.b().pos();
        let mark = self.b().state.mark;
        let top = self.b().top;
        if let Some((a, b)) = self.b().region() {
            matches.retain(|(x, y, _)| *x >= a && *y <= b);
        } else {
            let pivot = matches
                .iter()
                .position(|(a, _, _)| *a >= original)
                .unwrap_or(0);
            matches.rotate_left(pivot);
        }
        if self.conf.on(BACKWARDS_SEARCH) {
            matches.reverse();
        }
        if matches.is_empty() {
            self.find(false);
            return;
        }
        self.bm().state.mark = None;
        self.replacement = Some(Replacement {
            matches,
            next: 0,
            replacement,
            count: 0,
            original,
            top,
            mark,
        });
        self.show_replacement();
    }
    fn show_replacement(&mut self) {
        let Some(r) = &self.replacement else {
            return;
        };
        if r.next >= r.matches.len() {
            self.finish_replace();
            return;
        }
        let a = r.matches[r.next].0;
        let b = r.matches[r.next].1;
        self.bm().state.pos = a;
        self.preferred();
        let l = crate::render::layout(self);
        let row = self.cursor_row();
        if row < self.b().top || row >= self.b().top + l.edit_rows {
            self.center();
        }
        self.spotlight = Some((a.line, a.x, b.x));
        self.spotlight_time = std::time::Instant::now();
        self.question("Replace this instance?", QuestionKind::Replace, true);
    }
    pub fn replace_answer(&mut self, yes: bool, all: bool) {
        loop {
            let Some(mut r) = self.replacement.take() else {
                return;
            };
            if r.next >= r.matches.len() {
                self.replacement = Some(r);
                self.finish_replace();
                return;
            }
            let (a, b, groups) = r.matches[r.next].clone();
            if yes {
                let mut raw = Vec::new();
                let line = self.b().state.lines[a.line].clone();
                let mut i = 0;
                while i < r.replacement.len() {
                    if self.conf.on(USE_REGEXP)
                        && r.replacement[i] == b'\\'
                        && i + 1 < r.replacement.len()
                        && (b'1'..=b'9').contains(&r.replacement[i + 1])
                    {
                        let n = (r.replacement[i + 1] - b'0') as usize;
                        if n < groups.len() {
                            let (start, end) = groups[n];
                            if start != usize::MAX && end <= line.len() {
                                raw.extend(bytes::decode_nuls(&line[start..end]));
                            }
                            i += 2;
                            continue;
                        }
                    }
                    raw.push(r.replacement[i]);
                    i += 1;
                }
                let before = self.b().begin();
                self.bm().replace(a, b, &raw);
                let no = self.conf.on(NO_NEWLINES);
                self.bm().finish(before, "replacement", false, no);
                let delta = raw.len() as isize - (b.x - a.x) as isize;
                for (x, y, g) in r.matches.iter_mut().skip(r.next + 1) {
                    if x.line == a.line && x.x >= b.x {
                        x.x = x.x.saturating_add_signed(delta);
                        y.x = y.x.saturating_add_signed(delta);
                        for (start, end) in g {
                            if *start != usize::MAX {
                                *start = start.saturating_add_signed(delta);
                                *end = end.saturating_add_signed(delta);
                            }
                        }
                    }
                }
                if r.original.line == a.line && r.original.x > a.x && r.original.x >= b.x {
                    r.original.x = r.original.x.saturating_add_signed(delta);
                }
                r.count += 1;
            }
            r.next += 1;
            let done = r.next >= r.matches.len();
            self.replacement = Some(r);
            if done {
                self.finish_replace();
                return;
            }
            if !all {
                self.show_replacement();
                return;
            }
        }
    }
    pub fn finish_replace(&mut self) {
        let spelling = self.spelling.is_some();
        if let Some(r) = self.replacement.take() {
            self.bm().set_pos(r.original);
            self.bm().top = r.top;
            self.bm().state.mark = r.mark;
            self.preferred();
            self.mode = Mode::Edit;
            self.spotlight = None;
            self.msg(
                crate::native::plural(
                    "Replaced %zd occurrence",
                    "Replaced %zd occurrences",
                    r.count,
                )
                .replace("%zd", &r.count.to_string()),
                2,
            );
        }

        if spelling {
            self.next_spell();
        }
    }
    pub fn find_bracket(&mut self) {
        let e = self.conf.enc();
        let brackets = if self.conf.value("matchbrackets").is_empty() {
            b"(<[{)>]}".to_vec()
        } else {
            self.conf.value("matchbrackets")
        };
        let mut chars = Vec::new();
        let mut x = 0;
        while x < brackets.len() {
            let n = e.len(&brackets, x);
            chars.push(brackets[x..x + n].to_vec());
            x += n;
        }
        let p = self.b().pos();
        let n = e.len(self.b().line(), p.x);
        let Some(index) = chars
            .iter()
            .position(|s| self.b().line().get(p.x..p.x + n) == Some(s.as_slice()))
        else {
            self.msg("Not a bracket", 5);
            return;
        };
        let half = chars.len() / 2;
        let forward = index < half;
        let partner = if forward { index + half } else { index - half };
        let mut depth = 1;
        let mut positions = Vec::new();
        for (line, s) in self.b().state.lines.iter().enumerate() {
            let mut x = 0;
            while x < s.len() {
                positions.push(Pos { line, x });
                x = e.right(s, x);
            }
        }
        if !forward {
            positions.reverse();
        }
        for q in positions {
            if forward && q <= p || !forward && q >= p {
                continue;
            }
            let s = &self.b().state.lines[q.line];
            let n = e.len(s, q.x);
            let ch = &s[q.x..q.x + n];
            if ch == chars[index] {
                depth += 1;
            } else if ch == chars[partner] {
                depth -= 1;
                if depth == 0 {
                    self.bm().state.pos = q;
                    self.preferred();
                    self.center();
                    return;
                }
            }
        }
        self.msg("No matching bracket", 5);
    }
}
