//! Editing operations, movement, browser/help, tools and persisted state.
use crate::{
    buffer::{Buffer, Pos, Splice},
    bytes,
    config::{self, io_error},
    editor::*,
    files,
    generated::*,
    input::Key,
    native, render,
};
use std::{
    fs,
    io::{Read, Write},
    os::unix::{
        ffi::OsStrExt,
        fs::{OpenOptionsExt, PermissionsExt},
    },
    path::PathBuf,
    process::{Command, Stdio},
};
impl Editor {
    pub fn scroll_horizontal(&mut self, right: bool) {
        if self.conf.on(SOFTWRAP) || self.conf.on(SOLO_SIDESCROLL) {
            self.msg(
                if self.conf.on(SOFTWRAP) {
                    "Not possible with '--softwrap'"
                } else {
                    "Not possible with '--solo'"
                },
                5,
            );
            return;
        }
        let l = render::layout(self);
        let step = self.conf.tab.max(2);
        let brink = if right {
            self.b().brink + step
        } else {
            self.b().brink.saturating_sub(step)
        };
        let e = self.conf.enc();
        let mut line = self.b().pos().line;
        if right && e.breadth(self.b().line()) < brink + 3 {
            let candidates = (0..line).rev().chain(line + 1..self.b().state.lines.len());
            if let Some(i) = candidates
                .into_iter()
                .find(|i| e.breadth(&self.b().state.lines[*i]) >= brink + 3)
            {
                line = i;
            } else {
                return;
            }
        }
        let col = e.column(
            &self.b().state.lines[line],
            self.b().pos().x.min(self.b().state.lines[line].len()),
        );
        let target = if right {
            col.max(brink + 3)
        } else {
            col.min(brink + l.width.saturating_sub(4))
        };
        let x = e.actual(&self.b().state.lines[line], target);
        self.bm().state.pos = Pos { line, x };
        self.bm().brink = brink;
        self.preferred();
    }
    pub fn paragraph_move(&mut self, down: bool) {
        let p = self.b().pos();
        let e = self.conf.enc();
        let blank = |i: usize| e.indent(&self.b().state.lines[i]) == self.b().state.lines[i].len();
        let mut line = p.line;
        if down {
            while line + 1 < self.b().state.lines.len() && blank(line) {
                line += 1;
            }
            while line + 1 < self.b().state.lines.len() && !blank(line) {
                line += 1;
            }
        } else {
            line = line.saturating_sub(1);
            while line > 0 && blank(line) {
                line -= 1;
            }
            while line > 0 && !blank(line - 1) {
                line -= 1;
            }
        }
        self.bm().state.pos = Pos { line, x: 0 };
        self.preferred();
        self.center();
    }
    pub fn chop(&mut self, right: bool) {
        let p = self.b().pos();
        let e = self.conf.enc();
        let mut target = self.b().word_target(
            e,
            right,
            self.conf.on(AFTER_ENDS),
            self.conf.on(WORD_BOUNDS),
            &self.conf.value("wordchars"),
        );
        if right && target.line > p.line && p.x < self.b().line().len() {
            target = Pos {
                line: p.line,
                x: self.b().line().len(),
            };
        }
        if !right && target.line < p.line {
            target = if p.x > 0 {
                Pos { line: p.line, x: 0 }
            } else {
                Pos {
                    line: p.line - 1,
                    x: self.b().state.lines[p.line - 1].len(),
                }
            };
        }
        let (a, b) = if target < p { (target, p) } else { (p, target) };
        if a == b {
            self.msg("Nothing was cut", 1);
            return;
        }
        let no = self.conf.on(NO_NEWLINES);
        self.bm().cut(a, b, "cut", false, no);
        self.bm().state.mark = None;
        self.preferred();
    }
    pub fn indent(&mut self, unindent: bool) {
        let range = self.b().range_lines();
        let e = self.conf.enc();
        let tab = self
            .syntax()
            .and_then(|s| s.tab.clone())
            .unwrap_or_else(|| {
                if self.conf.on(TABS_TO_SPACES) {
                    vec![32; self.conf.tab]
                } else {
                    vec![9]
                }
            });
        let before = self.b().begin();
        let mut any = false;
        for line in range {
            let s = self.b().state.lines[line].clone();
            if s.is_empty() {
                continue;
            }
            let n = if unindent {
                if s.starts_with(&tab) {
                    tab.len()
                } else {
                    let mut n = 0;
                    while n < s.len() && n < self.conf.tab {
                        if s[n] == 9 {
                            n += 1;
                            break;
                        }
                        if s[n] != 32 {
                            break;
                        }
                        n += 1;
                    }
                    n
                }
            } else {
                0
            };
            if unindent && n == 0 {
                continue;
            }
            any = true;
            let delta = if unindent {
                -(n as isize)
            } else {
                tab.len() as isize
            };
            if unindent {
                self.bm().state.lines[line].drain(..n);
            } else {
                self.bm().state.lines[line].splice(..0, tab.clone());
            }
            let b = self.bm();
            if b.pos().line == line && b.pos().x > 0 {
                b.state.pos.x = b.pos().x.saturating_add_signed(delta);
            }
            if let Some(m) = b.state.mark.as_mut()
                && m.line == line
                && m.x > 0
            {
                m.x = m.x.saturating_add_signed(delta);
            }
        }
        if any {
            let no = self.conf.on(NO_NEWLINES);
            self.bm().finish(
                before,
                if unindent { "unindent" } else { "indent" },
                false,
                no,
            );
        }
        let _ = e;
        self.preferred();
    }
    pub fn comment(&mut self) {
        let comment = self
            .syntax()
            .and_then(|s| s.comment.clone())
            .unwrap_or_else(|| b"#".to_vec());
        if comment.is_empty() {
            self.msg("Commenting is not supported for this file type", 5);
            return;
        }
        let parts: Vec<_> = comment.splitn(2, |b| *b == b'|').collect();
        let prefix = parts[0];
        let suffix = parts.get(1).copied().unwrap_or_default();
        let range = self.b().range_lines();
        let last = self.b().state.lines.len() - 1;
        if *range.start() == last && self.b().state.lines[last].is_empty() {
            self.msg("Cannot comment past end of file", 5);
            return;
        }
        let e = self.conf.enc();
        let uncomment = range
            .clone()
            .any(|l| e.indent(&self.b().state.lines[l]) < self.b().state.lines[l].len())
            && range.clone().all(|l| {
                let s = &self.b().state.lines[l];
                e.indent(s) == s.len() || s.starts_with(prefix) && s.ends_with(suffix)
            });
        let before = self.b().begin();
        for line in range {
            if line == last && self.b().state.lines[last].is_empty() {
                continue;
            }
            let s = &mut self.bm().state.lines[line];
            let delta = if uncomment {
                if !s.starts_with(prefix) || !s.ends_with(suffix) {
                    continue;
                }
                s.truncate(s.len() - suffix.len());
                s.drain(..prefix.len());
                -(prefix.len() as isize)
            } else {
                s.splice(..0, prefix.iter().copied());
                s.extend(suffix);
                prefix.len() as isize
            };
            let b = self.bm();
            if b.pos().line == line && b.pos().x > 0 {
                b.state.pos.x = b.pos().x.saturating_add_signed(delta);
            }
            if let Some(m) = b.state.mark.as_mut()
                && m.line == line
                && m.x > 0
            {
                m.x = m.x.saturating_add_signed(delta);
            }
        }
        let no = self.conf.on(NO_NEWLINES);
        self.bm().finish(
            before,
            if uncomment { "uncomment" } else { "comment" },
            false,
            no,
        );
        self.preferred();
    }
    pub fn complete_word(&mut self) {
        let e = self.conf.enc();
        let extra = self.conf.value("wordchars");
        let punct = self.conf.on(WORD_BOUNDS);
        if self.last_command != "complete_a_word" || self.completion_fragment.is_empty() {
            let p = self.b().pos();
            let mut start = p.x;
            while start > 0 {
                let prev = e.left(self.b().line(), start);
                if !e.word(self.b().line(), prev, punct, &extra) {
                    break;
                }
                start = prev;
            }
            if start == p.x {
                self.msg("No word fragment", 5);
                return;
            }
            self.completion_fragment = self.b().line()[start..p.x].to_vec();
            self.completion_start = p;
            self.completion_tried.clear();
        } else if self.b().pos().x > self.completion_start.x {
            let a = self.completion_start;
            let z = self.b().pos();
            self.bm().replace(a, z, b"", Splice::Plain);
            if self.b().hist > 0 {
                self.bm().undo(false);
            }
        }
        let mut found = None;
        for b in self
            .buffers
            .iter()
            .cycle()
            .skip(self.current)
            .take(self.buffers.len())
        {
            for s in &b.state.lines {
                let mut x = 0;
                while x < s.len() {
                    if s[x..].starts_with(&self.completion_fragment)
                        && (x == 0 || !e.word(s, e.left(s, x), punct, &extra))
                    {
                        let mut end = x + self.completion_fragment.len();
                        while end < s.len() && e.word(s, end, punct, &extra) {
                            end = e.right(s, end);
                        }
                        let word = s[x..end].to_vec();
                        if word.len() > self.completion_fragment.len()
                            && !self.completion_tried.contains(&word)
                        {
                            found = Some(word);
                            break;
                        }
                    }
                    x = e.right(s, x);
                }
                if found.is_some() {
                    break;
                }
            }
            if found.is_some() {
                break;
            }
        }
        if let Some(word) = found {
            let raw = word[self.completion_fragment.len()..].to_vec();
            self.completion_tried.push(word);
            let no = self.conf.on(NO_NEWLINES);
            self.bm().insert(&raw, "addition", false, no);
            self.preferred();
            self.clear();
        } else {
            self.msg(
                if self.completion_tried.is_empty() {
                    "No matches"
                } else {
                    "No further matches"
                },
                5,
            );
            self.last_command.clear();
            self.completion_fragment.clear();
        }
    }
    pub fn anchor(&mut self, next: bool) {
        let n = self.b().state.lines.len();
        let p = self.b().pos();
        for d in 1..=n {
            let line = if next {
                (p.line + d) % n
            } else {
                (p.line + n - d % n) % n
            };
            if self.b().state.anchors[line] {
                if line == p.line {
                    self.msg("This is the only anchor", 2);
                } else {
                    self.bm().state.pos = Pos { line, x: 0 };
                    self.preferred();
                    self.center();
                    if !self.conf.on(LINE_NUMBERS) {
                        self.msg("Jumped to anchor", 1);
                    }
                }
                return;
            }
        }
        self.msg("There are no anchors", 5);
    }
    pub fn word_count(&mut self) {
        let raw = if let Some((a, b)) = self.b().region() {
            self.b().raw_region(a, b)
        } else {
            self.b().raw()
        };
        let e = self.conf.enc();
        let lines = raw.iter().filter(|b| **b == 10).count()
            + usize::from(!raw.is_empty() && raw.last() != Some(&10));
        let chars = e.count(&raw);
        let mut words = 0;
        let mut inword = false;
        let mut x = 0;
        while x < raw.len() {
            let word = e.word(&raw, x, true, &[]);
            if word && !inword {
                words += 1;
            }
            inword = word;
            x = e.right(&raw, x);
        }
        let noun = |n, a, b| native::plural(a, b, n);
        self.msg(
            format!(
                "{}{lines} {},  {words} {},  {chars} {}",
                if self.b().state.mark.is_some() {
                    native::tr("In Selection:  ")
                } else {
                    String::new()
                },
                noun(lines, "line", "lines"),
                noun(words, "word", "words"),
                noun(chars, "character", "characters")
            ),
            3,
        );
    }
    /// Wrap the current line at the last blank that fits within the wrap
    /// column, following the reference's `do_wrap`.
    ///
    /// The reference's sequence is: find the wrap point, join the overflow
    /// line when the live spillage pointer names it, trim the blanks before
    /// the wrap point and finally split the line with `do_enter`. Every step
    /// has an effect on the explicit mark and on the identity of the lines,
    /// so the steps are reproduced here in the same order instead of
    /// replacing the two lines in one generic splice.
    pub fn hard_wrap(&mut self) {
        if !self.conf.on(BREAK_LONG_LINES) {
            return;
        }
        let layout = render::layout(self);
        // The reference wraps at the terminal width, not at the margin-reduced
        // edit width, when the fill is not positive (`wrap_at = COLS + fill`).
        let wrap = if self.conf.fill > 0 {
            self.conf.fill as usize
        } else {
            layout.cols.saturating_add_signed(self.conf.fill)
        };
        let e = self.conf.enc();
        let p = self.b().pos();
        let line0 = p.line;
        let s = self.b().state.lines[line0].clone();
        if e.breadth(&s) <= wrap {
            return;
        }
        // The reference's quote prefix and indentation (`quote_length` and
        // `indent_length` in `do_wrap`). The quote prefix belongs to the
        // line's lead and is copied to the continuation line.
        let (quot_len, lead) = self.para_lead(line0);
        // Find the wrap point: the last run of blanks that still fits within
        // the wrap column (the reference's `break_line`).
        let mut x = lead;
        let mut split = None;
        while x < s.len() {
            if e.blank(&s, x) {
                let mut end = e.right(&s, x);
                while end < s.len() && e.blank(&s, end) {
                    end = e.right(&s, end);
                }
                if e.column(&s, x) <= wrap || split.is_none() {
                    split = Some(end);
                }
                if e.column(&s, end) > wrap {
                    break;
                }
                x = end;
            } else {
                x = e.right(&s, x);
            }
        }
        let Some(split) = split else {
            return;
        };
        if split >= s.len() {
            return;
        }
        let rest_length = s.len() - split;
        let spillage = self.b().state.spillage;
        let next_breadth = if line0 + 1 < self.b().state.lines.len() {
            e.breadth(&self.b().state.lines[line0 + 1])
        } else {
            0
        };
        // The reference joins only when `spillage_line == line->next` (a node
        // pointer comparison). With generations, compare the live spillage
        // generation to the generation currently at the successor line.
        let join = spillage.is_some()
            && line0 + 1 < self.b().state.lines.len()
            && self.b().state.generations[line0 + 1] == spillage.unwrap()
            && rest_length + next_breadth <= wrap;
        // The cursor position in the original line, like the reference's
        // `cursor_x`.
        let cursor_x = p.x;
        // The joined line and the mark, following the reference's sequence:
        // an optional added space, the join with the overflow line, the
        // removal of the duplicated prefix and of the extra blanks.
        let mut merged = s.clone();
        let mut mark = self.b().state.mark;
        if join {
            let next = self.b().state.lines[line0 + 1].clone();
            let remainder = &s[split..];
            let ends_blank = e.blank(remainder, e.left(remainder, remainder.len()));
            if !ends_blank {
                // The remainder does not end in a blank: the reference adds a
                // space before joining the overflow line.
                merged.push(b' ');
            }
            // The position where the overflow line's content is joined.
            let join_x = merged.len();
            // Strip the duplicated leading part only when the overflow line
            // starts with the same prefix as the current line (the
            // reference's `strncmp`). The previous code started at `lead`
            // unconditionally, which panicked when the overflow line was
            // shorter than `lead` and silently deleted real text when the
            // prefixes differed.
            let mut ni = 0;
            if next.len() >= lead && next[..lead] == s[..lead] {
                ni = lead;
            }
            let strip = ni;
            while ni < next.len() && e.blank(&next, ni) {
                ni = e.right(&next, ni);
            }
            let blanks = ni - strip;
            // A mark on the eaten line moves onto the joined line; a mark
            // behind the join point shifts back over the removed prefix and
            // blanks (the reference's `expunge` rules).
            if let Some(mut m) = mark {
                if m.line == line0 + 1 {
                    m.line = line0;
                    m.x += join_x;
                }
                // Joining and deleting the duplicated lead are successive
                // operations. A mark from the eaten node must receive both;
                // a mark inside the deleted prefix stops at the join point.
                if m.line == line0 && m.x > join_x {
                    m.x = join_x + (m.x - join_x).saturating_sub(strip + blanks);
                }
                mark = Some(m);
            }
            merged.extend(&next[strip + blanks..]);
        }
        // Trim the blanks before the wrap point (the reference's
        // `TRIM_BLANKS`). The guard keeps the typed character: the trim
        // stops before the character just before the cursor unless the
        // cursor is at or after the wrap point.
        let mut cut = split;
        if self.conf.on(TRIM_BLANKS) {
            let typed_x = e.left(&merged, cursor_x);
            let mut rear_x = e.left(&merged, split);
            while (rear_x != typed_x || cursor_x >= split) && e.blank(&merged, rear_x) {
                let end = e.right(&merged, rear_x);
                merged.drain(rear_x..end);
                cut = rear_x;
                if let Some(m) = mark
                    && m.line == line0
                    && m.x > rear_x
                {
                    mark = Some(Pos {
                        line: line0,
                        x: m.x - (end - rear_x),
                    });
                }
                rear_x = e.left(&merged, rear_x);
            }
        }
        // The reference's `do_enter`: the continuation line's indentation. A
        // quoted line suspends automatic indentation and copies its quote
        // prefix (quote plus indentation) to the continuation instead.
        let mut extra = 0usize;
        let mut quote_prefix: Vec<u8> = Vec::new();
        let mut sample_indent: Vec<u8> = Vec::new();
        let mut allblanks = false;
        if quot_len > 0 {
            quote_prefix = merged[..lead].to_vec();
        } else if self.conf.on(AUTOINDENT) {
            // When the next line is in the same paragraph and is not a
            // paragraph start, its indentation is the model. After a
            // spillage join the overflow line is gone, so the model is the
            // line that follows it.
            let next_index = if join { line0 + 2 } else { line0 + 1 };
            let sample = if next_index < self.b().state.lines.len()
                && self.in_para(next_index)
                && !self.para_start(next_index, 0)
            {
                next_index
            } else {
                line0
            };
            let sample_data = if sample == line0 {
                merged.clone()
            } else {
                self.b().state.lines[sample].clone()
            };
            extra = e.indent(&sample_data);
            sample_indent = sample_data[..extra].to_vec();
            if extra > cut {
                extra = cut;
                sample_indent.truncate(extra);
            } else if extra == cut {
                allblanks = e.indent(&merged) == extra;
            }
        }
        // Shift pre-existing lower nodes before moving a mark from the
        // wrapping line onto its new continuation. Doing this afterward
        // would shift that newly moved mark a second time.
        if !join
            && let Some(m) = mark.as_mut()
            && m.line > line0
        {
            m.line += 1;
        }
        // A mark behind the wrap point moves to the continuation line.
        if let Some(m) = mark
            && m.line == line0
            && m.x > cut
        {
            mark = Some(Pos {
                line: line0 + 1,
                x: m.x - cut + extra,
            });
        }
        if allblanks {
            cut = 0;
            if let Some(m) = mark
                && m.line == line0
            {
                mark = Some(Pos { line: line0, x: 0 });
            }
        }
        let first = merged[..cut].to_vec();
        let mut second = Vec::new();
        second.extend_from_slice(&quote_prefix);
        second.extend_from_slice(&sample_indent);
        second.extend_from_slice(&merged[cut..]);
        // The reference keeps the cursor on the first line when it was
        // before the wrap point and moves it to the continuation otherwise.
        let pos = if cursor_x < split {
            Pos {
                line: line0,
                x: cursor_x,
            }
        } else {
            Pos {
                line: line0 + 1,
                x: extra + quote_prefix.len() + (cursor_x - split),
            }
        };
        self.bm().wrap_split(line0, first, second, join);
        self.bm().state.mark = mark;
        self.bm().state.pos = pos;
        let mut after = self.b().state.clone();
        // The reference clears `spillage_line` only in delete_node (when the
        // wrap-created line is freed) and does not restore it on redo: redo
        // re-applies the inner ENTER without setting the spillage pointer.
        // Record `None` in both the before- and after-state of a wrap item so
        // undo and redo of a wrap yield no spillage, matching the reference.
        // The live marker is set below for the next wrap's join decision.
        after.spillage = None;
        if let Some(last) = self.bm().history.last_mut() {
            last.after = after;
            last.before.spillage = None;
            last.is_wrap = true;
            if last.kind == "paste" {
                last.redo_kind = Some("addition".into());
            }
        }
        // A successful wrap creates the spillage line for the next wrap: the
        // new continuation line's generation (assigned by the split).
        self.bm().state.spillage = self.bm().state.generations.get(line0 + 1).copied();
        // A hard wrap ends the current addition group: nano's do_wrap closes
        // the wrap with a SPLIT_END item and resets last_action, so the next
        // typed character (even at the wrapped cursor) starts a new ADD item
        // instead of continuing the item that triggered the wrap. Without this
        // reset, a movement that returns to the wrap cursor (Home/End) would
        // let later typing undo together with the wrap+trigger, diverging from
        // the reference. See spec 06 UNDO-003 and Q-UNDO-002.
        self.bm().last_kind.clear();
        self.preferred();
    }
    fn para_lead(&self, line: usize) -> (usize, usize) {
        let s = &self.b().state.lines[line];
        let q = native::Regex::new(&self.conf.value("quotestr"), false)
            .ok()
            .and_then(|r| r.find(s, 0, false))
            .filter(|m| m[0].0 == 0)
            .map(|m| m[0].1)
            .unwrap_or(0);
        (q, q + self.conf.enc().indent(&s[q..]))
    }
    fn in_para(&self, line: usize) -> bool {
        self.para_lead(line).1 < self.b().state.lines[line].len()
    }
    fn para_start(&self, line: usize, depth: usize) -> bool {
        if depth > 222 || !self.in_para(line) {
            return false;
        }
        if line == 0 {
            return true;
        }
        let (q, lead) = self.para_lead(line);
        let (pq, plead) = self.para_lead(line - 1);
        let s = &self.b().state.lines[line];
        let previous = &self.b().state.lines[line - 1];
        if self.conf.on(BOOKSTYLE) && !self.conf.on(AUTOINDENT) && self.conf.enc().blank(s, 0)
            || q != pq
            || s[..q] != previous[..pq]
            || !self.in_para(line - 1)
        {
            return true;
        }
        self.conf.enc().breadth(&s[q..lead]) != self.conf.enc().breadth(&previous[pq..plead])
            && !self.para_start(line - 1, depth + 1)
    }
    pub fn justify(&mut self, full: bool) {
        let e = self.conf.enc();
        let start = self.b().pos().line;
        let last = self.b().state.lines.len();
        let mut line = if full { 0 } else { start };
        while line > 0 && !full && self.in_para(line) && !self.para_start(line, 0) {
            line -= 1;
        }
        let before = self.b().begin();
        let mut changed = false;
        let layout = render::layout(self);
        let width = if self.conf.fill > 0 {
            self.conf.fill as usize
        } else {
            layout.width.saturating_add_signed(self.conf.fill)
        };
        let quote = crate::native::Regex::new(&self.conf.value("quotestr"), false).ok();
        while line < self.b().state.lines.len() {
            while line < self.b().state.lines.len()
                && e.indent(&self.b().state.lines[line]) == self.b().state.lines[line].len()
            {
                line += 1;
            }
            if line >= self.b().state.lines.len() {
                break;
            }
            let first = line;
            let get_lead = |s: &[u8]| {
                let q = quote
                    .as_ref()
                    .and_then(|r| r.find(s, 0, false))
                    .filter(|m| m[0].0 == 0)
                    .map(|m| m[0].1)
                    .unwrap_or(0);
                q + e.indent(&s[q..])
            };
            let lead0 = get_lead(&self.b().state.lines[line]);
            let _quote0 = quote
                .as_ref()
                .and_then(|r| r.find(&self.b().state.lines[line], 0, false))
                .map(|m| m[0].1)
                .unwrap_or(0);
            let mut end = line + 1;
            while end < self.b().state.lines.len() && self.in_para(end) && !self.para_start(end, 0)
            {
                end += 1;
            }
            let firstlead = self.b().state.lines[first][..lead0].to_vec();
            let sample = if end > first + 1 {
                self.b().state.lines[first + 1][..get_lead(&self.b().state.lines[first + 1])]
                    .to_vec()
            } else {
                firstlead.clone()
            };
            let mut content = Vec::new();
            for i in first..end {
                let s = &self.b().state.lines[i];
                let lead = get_lead(s);
                if !content.is_empty() && !content.ends_with(b" ") {
                    content.push(32);
                }
                content.extend(&s[lead..]);
            }
            let mut squeezed = Vec::new();
            let mut i = 0;
            while i < content.len() {
                if content[i] == 32 || content[i] == 9 {
                    let begin = i;
                    while i < content.len() && (content[i] == 32 || content[i] == 9) {
                        i += 1;
                    }
                    if i < content.len() {
                        let double =
                            squeezed.last().is_some_and(|b| b"!.?".contains(b)) && i - begin > 1;
                        squeezed.push(32);
                        if double {
                            squeezed.push(32);
                        }
                    }
                } else {
                    squeezed.push(content[i]);
                    i += 1;
                }
            }
            let mut output = Vec::new();
            let mut lead = firstlead;
            let mut rest = squeezed;
            loop {
                let available = width.saturating_sub(e.breadth(&lead));
                if e.breadth(&rest) <= available {
                    let mut row = lead;
                    row.extend(rest);
                    output.push(row);
                    break;
                }
                let x = e.actual(&rest, available);
                let cut = rest[..(x + 1).min(rest.len())]
                    .iter()
                    .rposition(|b| *b == 32)
                    .or_else(|| rest.iter().position(|b| *b == 32));
                let Some(cut) = cut else {
                    let mut row = lead;
                    row.extend(rest);
                    output.push(row);
                    break;
                };
                let mut after = cut;
                while after < rest.len() && rest[after] == 32 {
                    after += 1;
                }
                let mut row = lead;
                row.extend(&rest[..cut]);
                if !self.conf.on(TRIM_BLANKS) {
                    row.push(32);
                }
                output.push(row);
                rest = rest[after..].to_vec();
                lead = sample.clone();
            }
            let count = output.len();
            self.bm().state.lines.splice(first..end, output);
            // The paragraph's old lines are all replaced by rewrapped output;
            // none survive, so a spillage marker in the range is cleared and a
            // marker below shifts (R1). `replace` is not used here, so maintain
            // the marker explicitly.
            self.bm().spillage_no_survivors(first, end, count);
            let n = self.b().state.lines.len();
            self.bm().state.anchors.resize(n, false);
            line = first + count;
            changed = true;
            if !full {
                break;
            }
        }
        if changed {
            let pos = if full {
                Pos {
                    line: start.min(self.b().state.lines.len() - 1),
                    x: 0,
                }
            } else {
                Pos {
                    line: line.min(self.b().state.lines.len() - 1),
                    x: 0,
                }
            };
            self.bm().set_pos(pos);
            let no = self.conf.on(NO_NEWLINES);
            self.bm().finish(before, "justification", false, no);
            self.msg(
                if full {
                    "Justified file"
                } else {
                    "Justified paragraph"
                },
                2,
            );
            self.preferred();
        } else {
            self.bm().state.pos = self.b().end();
        }
        let _ = last;
    }
    pub fn open_help(&mut self, previous: Mode) {
        let menu = match &previous {
            Mode::Prompt(p) => match p.kind {
                PromptKind::Search(false) => SEARCH,
                PromptKind::Search(true) => REPLACE,
                PromptKind::ReplaceWith => REPLACEWITH,
                PromptKind::Goto => GOTO,
                PromptKind::Write { .. } => WRITE,
                PromptKind::Insert => INSERT,
                PromptKind::Execute => EXEC,
                _ => MAIN,
            },
            Mode::Browser(_) => BROWSER,
            _ => MAIN,
        };
        let parts = crate::help_data::INTROS
            .iter()
            .find(|(m, _)| *m == menu)
            .or_else(|| crate::help_data::INTROS.iter().find(|(m, _)| *m == MAIN));
        let intro = parts
            .map(|(_, parts)| parts.iter().map(|s| native::tr(s)).collect::<String>())
            .unwrap_or_else(|| "Main nano help text\n\n".into());
        let mut paragraphs = intro.splitn(2, '\n');
        let title = paragraphs.next().unwrap_or("").to_string();
        let body = paragraphs
            .next()
            .unwrap_or("")
            .strip_prefix('\n')
            .unwrap_or("");
        let cols = unsafe { native::nr_cols() }.max(1) as usize;
        let mut lines = vec![b" ".to_vec()];
        let mut intro_lines = wrap_lines(body, cols.clamp(40, 74), " ");
        if intro_lines.last().is_some_and(Vec::is_empty) {
            intro_lines.pop();
        }
        lines.extend(intro_lines);
        for f in self.conf.funcs.iter().filter(|f| f.menus & menu != 0) {
            let keys: Vec<_> = self
                .conf
                .keys
                .iter()
                .filter(|k| k.func == f.func && k.menus & menu != 0 && !k.tag.is_empty())
                .take(2)
                .collect();
            let first = keys.first().map(|k| k.tag.as_str()).unwrap_or("");
            let second = keys
                .get(1)
                .map(|k| format!("({})", k.tag))
                .unwrap_or_default();
            let prefix = format!("{first:<7}{second:<10}");
            let wrapped = wrap_lines(&native::tr(&f.phrase), cols.saturating_sub(18).max(22), "");
            for (i, line) in wrapped.into_iter().enumerate() {
                let mut row = if i == 0 {
                    prefix.as_bytes().to_vec()
                } else {
                    vec![32; 17]
                };
                row.extend(line);
                lines.push(row);
            }
            if f.blank {
                lines.push(vec![]);
            }
        }
        if menu == MAIN {
            for flag in 1..=13 {
                if let Some((_, _, desc)) = TOGGLES.iter().find(|(_, f, _)| *f == flag)
                    && let Some(k) = self
                        .conf
                        .keys
                        .iter()
                        .find(|k| k.toggle == flag && k.menus & MAIN != 0)
                {
                    lines.push(
                        format!("{:<17}{} enable/disable", k.tag, native::tr(desc)).into_bytes(),
                    );
                    if matches!(flag, LINE_NUMBERS | SOFTWRAP | AUTOINDENT) {
                        lines.push(Vec::new());
                    }
                }
            }
        }
        let saved_flags = self.conf.flags;
        let saved_search = self.search.clone();
        let viewport = (self.b().top, self.b().brink);
        for f in [
            NO_HELP,
            LINE_NUMBERS,
            WHITESPACE_DISPLAY,
            ZERO,
            SOFTWRAP,
            USE_REGEXP,
            CASE_SENSITIVE,
            BACKWARDS_SEARCH,
        ] {
            self.conf.set(f, false);
        }
        self.clear();
        self.mode = Mode::Help(HelpState {
            previous: Box::new(previous),
            title,
            lines,
            top: 0,
            saved_flags,
            saved_search,
            viewport,
            highlight: None,
            cursor_bottom: false,
        });
    }
    pub fn help_key(&mut self, mut h: HelpState, key: Key, fun: &str) {
        let f = if fun.is_empty() && !key.meta {
            match key.code {
                101 | 113 | 120 => "do_exit",
                32 => "do_page_down",
                45 | 98 => "do_page_up",
                47 | 119 => "do_search_forward",
                110 => "do_findnext",
                78 => "do_findprevious",
                _ => fun,
            }
        } else {
            fun
        };
        let l = render::layout(self);
        if matches!(
            f,
            "to_first_line" | "to_last_line" | "do_up" | "do_down" | "do_page_up" | "do_page_down"
        ) {
            h.highlight = None;
        }
        match f {
            "do_exit" | "do_cancel" => {
                self.conf.flags = h.saved_flags;
                self.search = h.saved_search;
                self.bm().top = h.viewport.0;
                self.bm().brink = h.viewport.1;
                self.mode = *h.previous;
                if let Mode::Browser(b) = &mut self.mode {
                    b.footer_cursor = true;
                }
                self.clear();
                return;
            }
            "do_up" | "do_scroll_up" => h.top = h.top.saturating_sub(1),
            "do_down" | "do_scroll_down" => {
                h.top = (h.top + 1).min(h.lines.len().saturating_sub(l.edit_rows))
            }
            "do_page_up" => h.top = h.top.saturating_sub(l.edit_rows.saturating_sub(2)),
            "do_page_down" => {
                h.top = (h.top + l.edit_rows.saturating_sub(2))
                    .min(h.lines.len().saturating_sub(l.edit_rows))
            }
            "to_first_line" => {
                h.top = 0;
                h.cursor_bottom = false;
            }
            "to_last_line" => {
                h.top = h.lines.len().saturating_sub(l.edit_rows);
                h.cursor_bottom = true;
            }
            "do_search_forward" | "do_search_backward" => {
                self.help_saved = Some(h);
                self.prompt(PromptKind::HelpSearch, vec![]);
                return;
            }
            "do_findnext" | "do_findprevious" => {
                self.help_find(h, f == "do_findprevious");
                return;
            }
            "full_refresh" => {}
            _ => self.unbound(&key),
        }
        self.mode = Mode::Help(h);
    }
    pub fn help_find(&mut self, mut h: HelpState, back: bool) {
        if self.search.is_empty() {
            self.msg("No current search pattern", 5);
            self.mode = Mode::Help(h);
            return;
        }
        let from = h.highlight.map(|m| m.0).unwrap_or(h.top);
        let n = h.lines.len();
        let mut found = None;
        for step in 1..=n {
            let i = if back {
                (from + n - step % n) % n
            } else {
                (from + step) % n
            };
            if let Some((a, b)) =
                crate::search::literal(&self.conf, &h.lines[i], &self.search, 0, false)
            {
                found = Some((i, a, b));
                break;
            }
        }
        if let Some((i, a, b)) = found {
            let rows = render::layout(self).edit_rows;
            h.top = i.saturating_sub(rows / 2).min(n.saturating_sub(rows));
            h.highlight = Some((i, a, b));
            if i <= from && !back {
                self.msg("Search Wrapped", 1);
            } else {
                self.clear();
            }
        } else {
            self.msg(
                native::tr("\"%.*s%s\" not found").replacen(
                    "%.*s%s",
                    &bytes::text(&self.search),
                    1,
                ),
                5,
            );
        }
        self.mode = Mode::Help(h);
    }
    pub fn open_browser(&mut self, p: Prompt) {
        let raw = config::expand(&p.answer);
        let dir = if raw.is_dir() {
            raw
        } else {
            raw.parent()
                .filter(|s| !s.as_os_str().is_empty())
                .unwrap_or(std::path::Path::new("."))
                .to_path_buf()
        };
        let dir =
            fs::canonicalize(dir).unwrap_or_else(|_| std::env::current_dir().unwrap_or_default());
        self.mode = Mode::Browser(BrowserState {
            previous: p,
            dir,
            entries: Vec::new(),
            selected: 0,
            gauge: 15,
            piles: 1,
            footer_cursor: false,
        });
        self.refresh_browser();
    }
    pub fn refresh_browser(&mut self) {
        let mode = std::mem::take(&mut self.mode);
        let Mode::Browser(mut b) = mode else {
            self.mode = mode;
            return;
        };
        let current = b.entries.get(b.selected).cloned();
        let mut entries = vec![b.dir.join("..")];
        match fs::read_dir(&b.dir) {
            Ok(items) => {
                entries.extend(items.flatten().map(|e| e.path()));
                entries.sort_by(|a, b| {
                    b.is_dir()
                        .cmp(&a.is_dir())
                        .then_with(|| {
                            a.file_name()
                                .unwrap_or_default()
                                .as_bytes()
                                .to_ascii_lowercase()
                                .cmp(
                                    &b.file_name()
                                        .unwrap_or_default()
                                        .as_bytes()
                                        .to_ascii_lowercase(),
                                )
                        })
                        .then(a.cmp(b))
                });
            }
            Err(e) => {
                self.msg(format!("Cannot open directory: {}", io_error(&e)), 7);
                self.mode = Mode::Browser(b);
                return;
            }
        }
        let cols = unsafe { native::nr_cols() }.max(1) as usize;
        let longest = entries
            .iter()
            .map(|p| {
                self.conf
                    .enc()
                    .breadth(p.file_name().unwrap_or_default().as_bytes())
            })
            .max()
            .unwrap_or(0);
        b.gauge = (longest + 10).max(15).min(cols);
        b.piles = ((cols + 2) / (b.gauge + 2)).max(1);
        b.entries = entries;
        if let Some(p) = current
            && let Some(i) = b.entries.iter().position(|e| *e == p)
        {
            b.selected = i;
        }
        b.selected = b.selected.min(b.entries.len() - 1);
        self.mode = Mode::Browser(b);
    }
    pub fn browser_key(&mut self, mut b: BrowserState, key: Key, fun: &str) {
        let f = if fun.is_empty() && !key.meta {
            match key.code {
                101 | 113 | 120 => "do_exit",
                63 => "do_help",
                115 => "do_enter",
                103 => "goto_dir",
                47 | 119 => "do_search_forward",
                110 => "do_findnext",
                78 => "do_findprevious",
                32 => "do_page_down",
                45 | 98 => "do_page_up",
                _ => fun,
            }
        } else {
            fun
        };
        let n = b.entries.len();
        let original_selection = b.selected;
        b.footer_cursor = false;
        let l = render::layout(self);
        let p = b.piles;
        match f {
            "do_exit" | "do_cancel" => {
                self.mode = Mode::Prompt(b.previous);
                return;
            }
            "do_help" => {
                self.open_help(Mode::Browser(b));
                return;
            }
            "do_left" => b.selected = b.selected.saturating_sub(1),
            "do_right" => b.selected = (b.selected + 1).min(n - 1),
            "do_up" => b.selected = b.selected.saturating_sub(p),
            "do_down" => {
                if b.selected + p < n {
                    b.selected += p;
                }
            }
            "to_first_file" => b.selected = 0,
            "to_last_file" => b.selected = n - 1,
            "to_prev_word" => b.selected -= b.selected % p,
            "to_next_word" => b.selected = (b.selected + p - 1 - b.selected % p).min(n - 1),
            "to_prev_block" => b.selected %= l.edit_rows * p,
            "to_next_block" => {
                b.selected = (b.selected / (l.edit_rows * p) * (l.edit_rows * p)
                    + (l.edit_rows - 1) * p
                    + b.selected % p)
                    .min(n - 1)
            }
            "do_page_up" => b.selected = b.selected.saturating_sub(l.edit_rows * p),
            "do_page_down" => b.selected = (b.selected + l.edit_rows * p).min(n - 1),
            "do_search_forward" | "do_search_backward" => {
                self.browser_saved = Some(b);
                self.prompt(PromptKind::BrowserSearch, vec![]);
                return;
            }
            "do_findnext" | "do_findprevious" => {
                if self.search.is_empty() {
                    self.msg("No current search pattern", 5);
                } else {
                    self.browser_saved = Some(b);
                    let prompt = Prompt::new(PromptKind::BrowserSearch, vec![]);
                    self.submit(prompt);
                    return;
                }
            }
            "goto_dir" => {
                self.browser_saved = Some(b);
                self.prompt(PromptKind::BrowserGoto, vec![]);
                return;
            }
            "do_enter" => {
                let selected = b.entries[b.selected].clone();
                if selected.is_dir() {
                    if b.dir == std::path::Path::new("/") && selected.ends_with("..") {
                        self.msg("Can't move up a directory", 7);
                    } else if !files::inside(&self.conf, &selected) {
                        self.msg(
                            format!(
                                "Can't go outside of {}",
                                bytes::text(&self.conf.value("operatingdir"))
                            ),
                            7,
                        );
                    } else {
                        let old = b.dir.clone();
                        let parent = selected.ends_with("..");
                        b.dir = fs::canonicalize(&selected).unwrap_or(selected);
                        b.entries.clear();
                        b.selected = 0;
                        self.mode = Mode::Browser(b);
                        self.refresh_browser();
                        if parent
                            && let Mode::Browser(b) = &mut self.mode
                            && let Some(i) = b.entries.iter().position(|e| *e == old)
                        {
                            b.selected = i;
                        }
                        return;
                    }
                } else if selected.exists() {
                    let mut prompt = b.previous;
                    prompt.answer = selected.as_os_str().as_bytes().to_vec();
                    prompt.x = prompt.answer.len();
                    self.submit(prompt);
                    return;
                } else {
                    self.msg(
                        format!(
                            "Error reading {}: No such file or directory",
                            selected.display()
                        ),
                        7,
                    );
                }
            }
            "full_refresh" => {
                self.mode = Mode::Browser(b);
                self.refresh_browser();
                return;
            }
            _ => self.unbound(&key),
        }
        if b.selected == original_selection {
            b.footer_cursor = true;
        }
        self.mode = Mode::Browser(b);
    }
    pub fn mouse(&mut self) {
        let (mut x, mut y) = (0, 0);
        let button = unsafe { native::nr_mouse_event(&mut x, &mut y) };
        if button == 0 {
            return;
        }
        let l = render::layout(self);
        let (x, y) = (x.max(0) as usize, y.max(0) as usize);
        if button == 4 || button == 5 {
            if y >= l.top && y <= l.status {
                self.scroll(button == 5, 2);
            }
            return;
        }
        if y >= l.rows.saturating_sub(2) && l.help {
            if matches!(self.mode, Mode::Question(_)) {
                let Mode::Question(q) = std::mem::take(&mut self.mode) else {
                    unreachable!()
                };
                let key = if y == l.rows - 2 {
                    if x < 16 { b'y' } else { b'a' }
                } else if x < 16 {
                    b'n'
                } else {
                    3
                };
                self.mode = Mode::Question(q);
                self.key(Key::plain(key as i32));
                return;
            }
            let (n, items) = render::help_items(self, self.menu(), l.cols);
            let width = if n < 5 {
                l.cols / 2
            } else {
                l.cols / n.div_ceil(2)
            };
            if let Some(column) = x.checked_div(width) {
                let i = column * 2 + y - (l.rows - 2);
                if let Some((_, _, code)) = items.get(i) {
                    let mut key = Key::plain(*code);
                    key.meta = *code >= 32 && *code < 256;
                    self.key(key);
                }
            }
            return;
        }
        let prompt_base = if let Mode::Prompt(p) = &self.mode {
            self.prompt_label(p).len() + 2
        } else {
            0
        };
        match &mut self.mode {
            Mode::Prompt(p) if y == l.status => {
                let base = prompt_base;
                let target = x.saturating_sub(base);
                p.x = self.conf.enc().actual(&p.answer, target);
            }
            Mode::Browser(b) if y >= l.top && y < l.top + l.edit_rows => {
                let page = b.selected / (l.edit_rows * b.piles) * (l.edit_rows * b.piles);
                let i = (page + (y - l.top) * b.piles + (x / (b.gauge + 2)).min(b.piles - 1))
                    .min(b.entries.len() - 1);
                let choose = i == b.selected;
                b.selected = i;
                if choose {
                    self.key(Key::plain(13));
                }
            }
            Mode::Edit if y >= l.top && y < l.top + l.edit_rows => {
                let rows = render::visual_rows(self.b(), &self.conf, l.width);
                let row = (self.b().top + y - l.top).min(rows.len() - 1);
                let r = &rows[row];
                let p = Pos {
                    line: r.line,
                    x: self.conf.enc().actual(
                        &self.b().state.lines[r.line],
                        r.from + self.b().brink + x.saturating_sub(l.margin),
                    ),
                };
                if p == self.b().pos() {
                    self.bm().state.mark = if self.b().state.mark.is_some() {
                        None
                    } else {
                        Some(p)
                    };
                } else {
                    self.bm().state.pos = p;
                }
                self.preferred();
            }
            _ => {}
        }
    }
    pub fn load_history(&mut self) {
        if !self.conf.on(HISTORYLOG) && !self.conf.on(POSITIONLOG) {
            return;
        }
        let home = config::home_dir();
        let legacy = home
            .as_ref()
            .map(|p| p.join(".nano"))
            .filter(|p| p.is_dir());
        let dir = if let Some(legacy) = legacy {
            legacy
        } else if let Some(x) = std::env::var_os("XDG_DATA_HOME") {
            PathBuf::from(x).join("nano")
        } else {
            let Some(home) = home else {
                return;
            };
            home.join(".local/share/nano")
        };
        use std::os::unix::fs::DirBuilderExt;
        if let Err(e) = fs::DirBuilder::new()
            .recursive(true)
            .mode(0o700)
            .create(&dir)
        {
            self.conf.errors.push(format!(
                "Unable to create directory {}: {}",
                dir.display(),
                io_error(&e)
            ));
            return;
        }
        self.state_dir = Some(dir.clone());
        if self.conf.on(HISTORYLOG)
            && let Ok(data) = fs::read(dir.join("search_history"))
        {
            let mut list = 0;
            for line in data.split(|b| *b == 10) {
                if line.is_empty() {
                    list += 1;
                    if list >= 3 {
                        break;
                    }
                } else {
                    let value = bytes::encode_nuls(line);
                    self.histories[list].retain(|s| *s != value);
                    self.histories[list].push(value);
                }
            }
        }
        if self.conf.on(POSITIONLOG)
            && let Ok(data) = fs::read(dir.join("filepos_history"))
        {
            self.position_entries = data
                .split(|b| *b == 10)
                .filter(|s| !s.is_empty())
                .take(200)
                .map(Vec::from)
                .collect();
        }
        self.history_changed = false;
    }
    pub fn save_history(&mut self) {
        if !self.conf.on(HISTORYLOG) || !self.history_changed {
            return;
        }
        let Some(dir) = &self.state_dir else {
            return;
        };
        let mut data = Vec::new();
        for list in &self.histories {
            for value in list {
                data.extend(bytes::decode_nuls(value));
                data.push(10);
            }
            data.push(10);
        }
        let p = dir.join("search_history");
        if let Ok(mut f) = fs::OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(true)
            .mode(0o600)
            .open(&p)
        {
            let _ = f.set_permissions(fs::Permissions::from_mode(0o600));
            let _ = f.write_all(&data);
        }
    }
    pub fn restore_position(&mut self) {
        if !self.conf.on(POSITIONLOG) || self.b().name.is_empty() {
            return;
        }
        let Ok(path) = fs::canonicalize(config::expand(&self.b().name)) else {
            return;
        };
        let name = path.as_os_str().as_bytes();
        for entry in self.position_entries.clone() {
            if let Some(i) = entry.iter().position(|b| *b == b'/') {
                let fields: Vec<_> = entry.rsplitn(3, |b| *b == 32).collect();
                if fields.len() == 3 && fields[2].get(i..) == Some(name) {
                    let line = bytes::text(fields[1]).parse::<usize>().unwrap_or(1);
                    let col = bytes::text(fields[0]).parse::<usize>().unwrap_or(1);
                    self.goto(format!("{line},{col}").as_bytes(), true);
                    for anchor in entry[..i].split(|b| *b == 32) {
                        if let Ok(line) = bytes::text(anchor).parse::<usize>()
                            && line > 0
                            && line <= self.b().state.anchors.len()
                        {
                            self.bm().state.anchors[line - 1] = true;
                        }
                    }
                    break;
                }
            }
        }
    }
    pub fn record_position(&mut self) {
        if !self.conf.on(POSITIONLOG) || self.b().name.is_empty() {
            return;
        }
        let Some(dir) = self.state_dir.clone() else {
            return;
        };
        let Ok(path) = fs::canonicalize(config::expand(&self.b().name)) else {
            return;
        };
        let mut entry = Vec::new();
        for (i, anchor) in self.b().state.anchors.iter().enumerate() {
            if *anchor {
                entry.extend(format!("{} ", i + 1).as_bytes());
            }
        }
        entry.extend(path.as_os_str().as_bytes());
        entry.extend(
            format!(
                " {} {}",
                self.b().pos().line + 1,
                self.conf.enc().column(self.b().line(), self.b().pos().x) + 1
            )
            .as_bytes(),
        );
        let name = path.as_os_str().as_bytes();
        self.position_entries.retain(|e| {
            let fields: Vec<_> = e.rsplitn(3, |b| *b == 32).collect();
            !fields
                .get(2)
                .is_some_and(|p| p.windows(name.len()).any(|s| s == name))
        });
        self.position_entries.insert(0, entry);
        self.position_entries.truncate(200);
        let p = dir.join("filepos_history");
        if let Ok(mut f) = fs::OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(true)
            .mode(0o600)
            .open(p)
        {
            let _ = f.set_permissions(fs::Permissions::from_mode(0o600));
            for e in &self.position_entries {
                let _ = f.write_all(&bytes::decode_nuls(e));
                let _ = f.write_all(b"\n");
            }
        }
    }
    pub fn execute(&mut self, command: Vec<u8>) {
        if command.is_empty() {
            if self.conf.on(NEW_BUFFER) {
                self.new_buffer(Buffer::default());
            } else {
                self.cancelled();
            }
            return;
        }
        let filter = command.starts_with(b"|");
        let text = bytes::text(if filter { &command[1..] } else { &command });
        let input = if filter {
            Some(if let Some((a, b)) = self.b().region() {
                self.b().raw_region(a, b)
            } else {
                self.b().raw()
            })
        } else {
            None
        };
        self.mode = Mode::Edit;
        self.msg("Executing...", 1);
        render::draw(self);
        let shell = std::env::var_os("SHELL").unwrap_or_else(|| "/bin/sh".into());
        let result = capture(Command::new(shell).arg("-c").arg(&text), input);
        match result {
            Ok((0, raw)) => {
                let original = self.b().pos();
                let (lines, _, n) = files::parse(&raw, !self.conf.on(NO_CONVERT));
                let raw = Buffer::new(vec![], lines).raw();
                let new = self.conf.on(NEW_BUFFER);
                let before = self.b().begin();
                if new {
                    self.new_buffer(Buffer::default());
                }
                let no = self.conf.on(NO_NEWLINES);
                if filter && !new {
                    let marked = self.b().state.mark.is_some();
                    let (a, b) = self
                        .b()
                        .region()
                        .unwrap_or((Pos::default(), self.b().end()));
                    self.bm().state.mark = None;
                    // Nano cuts first (including restoring the magic line),
                    // then inserts the command output. A single replacement
                    // loses that intermediate newline and the cut's node
                    // survivor policy when the selection reaches EOF.
                    self.bm().replace(a, b, &[], Splice::Cut);
                    self.bm().magic(no);
                    let start = self.b().pos();
                    self.bm().replace(start, start, &raw, Splice::Plain);
                    if !marked {
                        self.bm().set_pos(Pos {
                            line: original.line,
                            x: 0,
                        });
                    }
                    self.bm().finish(before, "filtering", false, no);
                } else {
                    self.bm().insert(&raw, "insertion", false, no);
                }
                if new {
                    self.bm().state.pos = Pos::default();
                }
                self.add_history(2, command);
                self.preferred();
                self.msg(files::line_message("Read", n, false), 2);
            }
            Ok((status, raw)) => {
                if filter && !self.conf.on(NEW_BUFFER) {
                    // Nano undoes and discards the failed compound edit;
                    // undo clears the selection even though text is restored.
                    self.bm().state.mark = None;
                    self.bm().softmark = false;
                    self.bm().last_kind.clear();
                }
                let line = raw
                    .split(|b| *b == 10)
                    .rfind(|s| !s.is_empty())
                    .unwrap_or_default();
                let text = bytes::text(line);
                let error = text.split_once(": ").map(|(_, s)| s).unwrap_or("---");
                self.msg(
                    if status < 0 {
                        "Cancelled".into()
                    } else {
                        format!("Error: {error}")
                    },
                    7,
                );
            }
            Err(e) => self.msg(format!("Error: {}", io_error(&e)), 7),
        }
    }
    pub fn format_tool(&mut self) {
        let command = self
            .syntax()
            .and_then(|s| s.formatter.clone())
            .filter(|s| !s.is_empty());
        if let Some(cmd) = command {
            self.bm().state.mark = None;
            self.external_tool(&cmd, false);
        } else {
            self.msg("No formatter is defined for this type of file", 5);
        }
    }
    pub fn external_tool(&mut self, cmd: &str, spell: bool) {
        use std::os::unix::process::CommandExt;
        let mut args = cmd.split(' ').filter(|s| !s.is_empty());
        let Some(program) = args.next() else {
            return;
        };
        let region = if spell { self.b().region() } else { None };
        let empty = region
            .map(|(a, b)| a == b)
            .unwrap_or_else(|| self.b().raw().is_empty());
        if empty {
            self.msg(
                if region.is_some() {
                    "Selection is empty"
                } else {
                    "Buffer is empty"
                },
                5,
            );
            return;
        }
        let temp = match files::temp(&self.conf, self.b(), region.is_some()) {
            Ok(t) => t,
            Err(e) => {
                self.msg(format!("Error writing temp file: {e}"), 7);
                return;
            }
        };
        let old = fs::metadata(&temp.path).and_then(|s| s.modified()).ok();
        let before = self.b().begin();
        let pos = self.b().pos();
        let mark = self.b().state.mark;
        let at_eol = pos.x == self.b().line().len();
        let preferred = self.b().preferred;
        if spell {
            unsafe {
                native::nr_done();
            }
        } else {
            self.msg("Invoking formatter...", 1);
            render::draw(self);
        }
        let mut command = Command::new(program);
        command.args(args).arg(&temp.path);
        unsafe {
            command.pre_exec(|| {
                native::nr_child_signals();
                Ok(())
            });
        }
        let result = command.spawn().and_then(|mut child| {
            loop {
                if let Some(status) = child.try_wait()? {
                    return Ok(status);
                }
                let sig = unsafe { native::nr_signal() };
                if matches!(sig, 1 | 15) {
                    let _ = child.kill();
                    let _ = child.wait();
                    self.signal(sig);
                    return Err(std::io::Error::new(
                        std::io::ErrorKind::Interrupted,
                        "editor terminated",
                    ));
                }
                if sig == 28 {
                    self.signal(sig);
                }
                std::thread::sleep(std::time::Duration::from_millis(10));
            }
        });
        if spell {
            self.last_footer_layout = None;
            unsafe {
                native::nr_resume(self.conf.on(PRESERVE) as i32);
            }
        }
        if self.exit.is_some() {
            return;
        }
        let status = result.ok().and_then(|s| s.code()).unwrap_or(9);
        if status > 2 {
            self.msg(format!("Error invoking '{program}'"), 7);
            return;
        }
        if status != 0 {
            self.msg(format!("Program '{program}' complained"), 7);
        }
        if fs::metadata(&temp.path).and_then(|s| s.modified()).ok() == old {
            self.msg("Nothing changed", 2);
            return;
        }
        match fs::read(&temp.path) {
            Ok(raw) => {
                let (lines, _, _) = files::parse(&raw, !self.conf.on(NO_CONVERT));
                let corrected = Buffer::new(Vec::new(), lines).raw();
                let mut wanted = pos;
                if let Some((a, b)) = region {
                    self.bm().replace(a, b, &corrected, Splice::Plain);
                    let end = self.b().pos();
                    if mark.is_some_and(|m| m < pos) {
                        wanted.x = end.x;
                    }
                    if let Some(mut m) = mark {
                        if m >= pos {
                            m.x = end.x;
                        }
                        m.line = m.line.min(self.b().state.lines.len() - 1);
                        m.x = m.x.min(self.b().state.lines[m.line].len());
                        self.bm().state.mark = Some(m);
                    }
                } else {
                    let (lines, _, _) = files::parse(&raw, !self.conf.on(NO_CONVERT));
                    self.bm().state.lines = lines;
                    // Whole-buffer replacement frees every old line; the
                    // spillage marker cannot survive (R1).
                    self.bm().spillage_clear();
                }
                self.bm().set_pos(wanted);
                if at_eol {
                    self.bm().state.pos.x = self.b().line().len();
                }
                if let Some(first) = self.bm().state.anchors.first_mut() {
                    *first = false;
                }
                let no = self.conf.on(NO_NEWLINES);
                self.bm().finish(
                    before,
                    if spell {
                        "spelling correction"
                    } else {
                        "formatting"
                    },
                    false,
                    no,
                );
                self.bm().preferred = preferred;
                self.msg(
                    if spell {
                        "Finished checking spelling"
                    } else {
                        "Buffer has been processed"
                    },
                    2,
                );
            }
            Err(e) => self.msg(
                format!("Error reading {}: {}", temp.path.display(), io_error(&e)),
                7,
            ),
        }
    }
    pub fn spell(&mut self) {
        let command = self.conf.value("speller");
        if !command.is_empty() {
            self.external_tool(&bytes::text(&command), true);
            return;
        }
        let temp = match files::temp(&self.conf, self.b(), self.b().state.mark.is_some()) {
            Ok(t) => t,
            Err(e) => {
                self.msg(format!("Error writing temp file: {e}"), 7);
                return;
            }
        };
        // Both the native pipeline and its statuses are retained independently
        // of the interactive correction session.
        let output = spelling_pipeline(&temp.path);
        match output {
            Ok((data, failure)) => {
                let words = data
                    .split(|b| *b == 10 || *b == 13)
                    .filter(|s| !s.is_empty())
                    .map(Vec::from)
                    .collect();
                self.spelling = Some(Spelling {
                    _temp: temp,
                    region: self
                        .b()
                        .region()
                        .map(|(a, b)| (self.b().offset(a), self.b().offset(b))),
                    upright: self.b().state.mark.is_some_and(|m| m < self.b().pos()),
                    failure,
                    preferred: self.b().preferred,
                    brink: self.b().brink,
                    words,
                    search: self.search.clone(),
                    flags: self.conf.flags,
                    original: self.b().pos(),
                    top: self.b().top,
                    started: false,
                });
                self.next_spell();
            }
            Err(_) => self.msg("Error invoking 'spell'", 7),
        }
    }
    pub fn next_spell(&mut self) {
        let Some(session) = self.spelling.as_mut() else {
            return;
        };
        let started = session.started;
        session.started = true;
        if let Some(word) = session.words.pop_front() {
            self.search = word.clone();
            self.conf.set(CASE_SENSITIVE, true);
            self.conf.set(USE_REGEXP, false);
            self.conf.set(BACKWARDS_SEARCH, false);
            let region = self.spelling.as_ref().and_then(|s| s.region);
            let e = self.conf.enc();
            let wordchars = self.conf.value("wordchars");
            let found = self
                .all_matches(true)
                .unwrap_or_default()
                .into_iter()
                .find(|(a, b, _)| {
                    let text = &self.b().state.lines[a.line];
                    region.is_none_or(|(lo, hi)| {
                        self.b().offset(*a) >= lo && self.b().offset(*b) <= hi
                    }) && (a.x == 0 || !e.word(text, e.left(text, a.x), false, &wordchars))
                        && (b.x == text.len() || !e.word(text, b.x, false, &wordchars))
                });
            let Some((a, b, _)) = found else {
                self.msg(format!("Unfindable word: {}", bytes::text(&word)), 7);
                self.pause_duration = std::time::Duration::from_millis(2800);
                self.pause_until = Some(std::time::Instant::now() + self.pause_duration);
                self.pause_painted = false;
                // Continue the session after the alert; no recursion through
                // arbitrary tool output and no reference to an invalid match.
                self.pause_next =
                    Some(Box::new(Mode::Prompt(Prompt::new(PromptKind::Spell, word))));
                return;
            };
            self.bm().state.pos = a;
            self.bm().state.mark = None;
            self.preferred();
            self.center();
            self.spotlight = Some((a.line, a.x, b.x));
            self.spotlight_time = std::time::Instant::now();
            self.clear();
            let next = Mode::Prompt(Prompt::new(PromptKind::Spell, word));
            if started {
                self.pause_screen = self.last_screen.clone();
                self.pause_painted = false;
                self.pause_duration = std::time::Duration::from_millis(400);
                self.mode = Mode::Edit;
                self.msg("Next word...", 1);
                self.pause_until =
                    Some(std::time::Instant::now() + std::time::Duration::from_millis(400));
                self.pause_next = Some(Box::new(next));
            } else {
                self.mode = next;
            }
        } else {
            self.finish_spell();
        }
    }
    pub fn restore_spell_position(&mut self) {
        if let Some(s) = &self.spelling {
            let original = s.original;
            let region = s.region;
            let upright = s.upright;
            let top = s.top;
            if let Some((lo, hi)) = region {
                let (cur, mark) = if upright { (hi, lo) } else { (lo, hi) };
                self.bm().state.pos = self.b().position_at_offset(cur);
                self.bm().state.mark = Some(self.b().position_at_offset(mark));
            } else {
                self.bm().set_pos(original);
            }
            self.bm().top = top;
        }
    }
    pub fn finish_spell(&mut self) {
        if let Some(s) = self.spelling.take() {
            self.search = s.search;
            self.conf.flags = s.flags;
            if let Some((lo, hi)) = s.region {
                let (cur, mark) = if s.upright { (hi, lo) } else { (lo, hi) };
                self.bm().state.pos = self.b().position_at_offset(cur);
                self.bm().state.mark = Some(self.b().position_at_offset(mark));
            } else {
                self.bm().set_pos(s.original);
            }
            self.bm().top = s.top;
            self.bm().brink = s.brink;
            self.mode = Mode::Edit;
            self.spotlight = None;
            self.preferred();
            self.clear();
            self.bm().preferred = s.preferred;
            if let Some(program) = s.failure {
                self.msg(format!("Error invoking '{program}'"), 7);
            } else {
                self.msg("Finished checking spelling", 2);
            }
        }
    }
    pub fn lint(&mut self) {
        if self.syntax().and_then(|s| s.linter.as_ref()).is_none() {
            self.msg("No linter is defined for this type of file", 5);
            return;
        }
        if self.b().modified {
            self.question(
                "Save modified buffer before linting?",
                QuestionKind::LintSave,
                false,
            );
        } else {
            self.lint_run();
        }
    }
    pub fn lint_run(&mut self) {
        let Some(command) = self.syntax().and_then(|s| s.linter.clone()) else {
            return;
        };
        let mut words = command.split(' ').filter(|s| !s.is_empty());
        let Some(program) = words.next() else {
            return;
        };
        let output = capture(
            Command::new(program)
                .args(words)
                .arg(config::path(&self.b().name)),
            None,
        );
        match output {
            Ok((status, data)) if (0..=2).contains(&status) => {
                let mut entries = Vec::new();
                for line in data.split(|b| *b == 10 || *b == 13) {
                    let s = bytes::text(line);
                    let Some((location, msg)) = s.split_once(' ') else {
                        continue;
                    };
                    let fields: Vec<_> = location.trim_end_matches(':').split(':').collect();
                    if fields.len() < 2 {
                        continue;
                    }
                    let nums: Vec<_> = fields[1].split(',').collect();
                    let Ok(line) = nums[0].parse::<usize>() else {
                        continue;
                    };
                    if line == 0 {
                        continue;
                    }
                    let col = if nums.len() > 1 {
                        nums[1].parse().unwrap_or(1)
                    } else if fields.len() > 2 {
                        fields[2].parse().unwrap_or(1)
                    } else {
                        1
                    };
                    entries.push((fields[0].as_bytes().to_vec(), line, col, msg.to_string()));
                }
                if entries.is_empty() {
                    self.msg(format!("Zero messages from '{command}'"), 2);
                    return;
                }
                let hidden = self.conf.on(NO_HELP);
                self.conf.set(NO_HELP, false);
                self.show_lint(LintState {
                    entries,
                    index: 0,
                    original_nohelp: hidden,
                });
            }
            _ => self.msg(format!("Error invoking '{command}'"), 7),
        }
    }
    fn show_lint(&mut self, l: LintState) {
        let entry = &l.entries[l.index];
        let line = entry.1;
        let col = entry.2.max(1);
        let msg = entry.3.clone();
        self.goto(format!("{line},{col}").as_bytes(), false);
        self.msg(msg, 4);
        self.mode = Mode::Lint(l);
    }
    pub fn lint_key(&mut self, mut l: LintState, key: Key, fun: &str) {
        match fun {
            "do_cancel" | "do_enter" => {
                self.conf.set(NO_HELP, l.original_nohelp);
                self.mode = Mode::Edit;
                self.clear();
                return;
            }
            "do_page_down" | "to_next_block" => {
                if l.index + 1 < l.entries.len() {
                    l.index += 1;
                } else {
                    self.msg("At last message", 1);
                    self.mode = Mode::Lint(l);
                    return;
                }
            }
            "do_page_up" | "to_prev_block" => {
                if l.index > 0 {
                    l.index -= 1;
                } else {
                    self.msg("At first message", 1);
                    self.mode = Mode::Lint(l);
                    return;
                }
            }
            "do_help" => {
                self.open_help(Mode::Lint(l));
                return;
            }
            _ => {
                self.unbound(&key);
                self.mode = Mode::Lint(l);
                return;
            }
        }
        self.show_lint(l);
    }
}
fn wrap_lines(text: &str, width: usize, indent: &str) -> Vec<Vec<u8>> {
    let mut lines = Vec::new();
    for paragraph in text.split('\n') {
        if paragraph.is_empty() {
            lines.push(Vec::new());
            continue;
        }
        let mut rest = paragraph;
        while rest.chars().count() > width {
            let byte = rest
                .char_indices()
                .nth(width)
                .map(|(i, _)| i)
                .unwrap_or(rest.len());
            let cut = rest[..byte].rfind(' ').filter(|i| *i > 0).unwrap_or(byte);
            let mut line = if rest.as_ptr() == paragraph.as_ptr() {
                Vec::new()
            } else {
                indent.as_bytes().to_vec()
            };
            line.extend(&rest.as_bytes()[..cut]);
            lines.push(line);
            rest = rest[cut..].strip_prefix(' ').unwrap_or(&rest[cut..]);
        }
        let mut line = if rest.as_ptr() == paragraph.as_ptr() {
            Vec::new()
        } else {
            indent.as_bytes().to_vec()
        };
        line.extend(rest.as_bytes());
        lines.push(line);
    }
    lines
}
fn capture(cmd: &mut Command, input: Option<Vec<u8>>) -> std::io::Result<(i32, Vec<u8>)> {
    use std::os::{
        fd::OwnedFd,
        unix::{net::UnixStream, process::CommandExt},
    };
    let (mut reader, writer) = UnixStream::pair()?;
    reader.set_read_timeout(Some(std::time::Duration::from_millis(100)))?;
    cmd.stdout(Stdio::from(OwnedFd::from(writer.try_clone()?)))
        .stderr(Stdio::from(OwnedFd::from(writer)))
        .stdin(if input.is_some() {
            Stdio::piped()
        } else {
            Stdio::null()
        })
        .process_group(0);
    unsafe {
        cmd.pre_exec(|| {
            native::nr_child_signals();
            Ok(())
        });
    }
    let mut child = cmd.spawn()?;
    let sender = input.and_then(|raw| {
        child.stdin.take().map(|mut p| {
            std::thread::spawn(move || {
                let _ = p.write_all(&raw);
            })
        })
    });
    let mut output = Vec::new();
    let mut cancelled = false;
    let mut buf = [0u8; 8192];
    loop {
        match reader.read(&mut buf) {
            Ok(0) => break,
            Ok(n) => output.extend(&buf[..n]),
            Err(e)
                if matches!(
                    e.kind(),
                    std::io::ErrorKind::WouldBlock | std::io::ErrorKind::TimedOut
                ) =>
            {
                if unsafe { native::nr_get(0) } == 3 {
                    let _ = child.kill();
                    cancelled = true;
                }
                if child.try_wait()?.is_some() {
                    break;
                }
            }
            Err(e) => return Err(e),
        }
    }
    let status = child.wait()?;
    if let Some(thread) = sender {
        let _ = thread.join();
    }
    Ok((
        if cancelled {
            -1
        } else {
            status.code().unwrap_or(-1)
        },
        output,
    ))
}

fn spelling_pipeline(path: &std::path::Path) -> std::io::Result<(Vec<u8>, Option<&'static str>)> {
    use std::os::unix::process::CommandExt;
    fn prepare(cmd: &mut Command) {
        cmd.stdout(Stdio::piped()).stderr(Stdio::inherit());
        unsafe {
            cmd.pre_exec(|| {
                native::nr_child_signals();
                Ok(())
            });
        }
    }
    let mut first = Command::new("hunspell");
    first.arg("-l").stdin(fs::File::open(path)?);
    prepare(&mut first);
    let mut spell = first
        .spawn()
        .or_else(|_| {
            let mut fallback = Command::new("spell");
            fallback.stdin(fs::File::open(path)?);
            prepare(&mut fallback);
            fallback.spawn()
        })
        .ok();
    let mut second = Command::new("sort");
    second.arg("-f");
    prepare(&mut second);
    second.stdin(
        spell
            .as_mut()
            .and_then(|c| c.stdout.take())
            .map(Stdio::from)
            .unwrap_or(Stdio::null()),
    );
    let mut sort = second.spawn().ok();
    let mut third = Command::new("uniq");
    prepare(&mut third);
    third.stdin(
        sort.as_mut()
            .and_then(|c| c.stdout.take())
            .map(Stdio::from)
            .unwrap_or(Stdio::null()),
    );
    let mut uniq = third.spawn().ok();
    let mut data = Vec::new();
    if let Some(out) = uniq.as_mut().and_then(|c| c.stdout.take()) {
        out.take(u64::MAX).read_to_end(&mut data)?;
    }
    let a = uniq
        .as_mut()
        .and_then(|c| c.wait().ok())
        .is_some_and(|s| s.success());
    let b = sort
        .as_mut()
        .and_then(|c| c.wait().ok())
        .is_some_and(|s| s.success());
    let c = spell
        .as_mut()
        .and_then(|c| c.wait().ok())
        .is_some_and(|s| s.success());
    Ok((
        data,
        if !a {
            Some("uniq")
        } else if !b {
            Some("sort")
        } else if !c {
            Some("spell")
        } else {
            None
        },
    ))
}
