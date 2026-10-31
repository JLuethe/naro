//! Movement, cutting and position reporting shared by both profiles.
use crate::{buffer::Pos, bytes, editor::*, generated::*, native, render};
impl Editor {
    pub fn cursor_row(&self) -> usize {
        let l = render::layout(self);
        let rows = render::visual_rows(self.b(), &self.conf, l.width);
        render::visual_cursor(self.b(), &self.conf, &rows)
    }
    pub fn center(&mut self) {
        let l = render::layout(self);
        let row = self.cursor_row();
        self.bm().top = row.saturating_sub(l.edit_rows / 2);
    }
    pub fn move_vertical(&mut self, delta: isize) {
        let e = self.conf.enc();
        if !self.conf.on(SOFTWRAP) {
            self.bm().move_v(e, delta);
            return;
        }
        let l = render::layout(self);
        let rows = render::visual_rows(self.b(), &self.conf, l.width);
        let row = render::visual_cursor(self.b(), &self.conf, &rows);
        let target = row.saturating_add_signed(delta).min(rows.len() - 1);
        if target == row {
            return;
        }
        // Preserve the desired column within a chunk, then rebase it onto
        // the destination chunk. A short final chunk permits its end-of-line.
        let col = (self.b().preferred % l.width + l.width - rows[row].from % l.width) % l.width;
        let line = rows[target].line;
        let text = &self.b().state.lines[line];
        let proper_x = |index: usize| {
            let v = &rows[index];
            let last = index + 1 == rows.len() || rows[index + 1].line != line;
            let column = (v.from + col).min(v.to.saturating_sub(usize::from(!last)));
            let mut x = e.actual(text, column);
            // A tab spanning a chunk boundary can otherwise send the cursor
            // back a row when moving down, or skip a row when moving up.
            let shifted = text.get(x) == Some(&b'\t')
                && if delta > 0 {
                    e.column(text, x) < v.from
                } else {
                    v.from > 0
                        && column / e.tab == (v.from - 1) / e.tab
                        && column / e.tab < (v.from + l.width - 1) / e.tab
                };
            if shifted {
                x += 1;
            }
            let actual_col = e.column(text, x);
            let actual_row = rows
                .iter()
                .rposition(|r| r.line == line && r.from <= actual_col)
                .unwrap_or(index);
            (x, actual_row, shifted)
        };
        let (mut x, mut actual_row, shifted) = proper_x(target);
        if shifted || rows[actual_row].from < rows[target].from {
            (x, actual_row, _) = proper_x(actual_row);
        }
        self.bm().state.pos = Pos { line, x };
        self.bm().preferred = rows[actual_row].from + col;
    }
    pub fn page(&mut self, down: bool) {
        let l = render::layout(self);
        let rows = render::visual_rows(self.b(), &self.conf, l.width);
        let row = self.cursor_row();
        let step = l.edit_rows.saturating_sub(2).max(1);
        if self.conf.on(SOFTWRAP) {
            let screen_row = row.saturating_sub(self.b().top);
            if down && row + step >= rows.len() {
                self.bm().state.pos = self.b().end();
                self.preferred();
                self.bm().top = rows.len().saturating_sub(l.edit_rows);
            } else if !down && row < step {
                self.bm().state.pos = Pos::default();
                self.preferred();
                self.bm().top = 0;
            } else {
                // Page by visual chunks using the same chunk-relative desired
                // column and spanning-tab adjustment as Up/Down. Then keep the
                // cursor on its previous screen row, as STATIONARY does in nano.
                self.move_vertical(if down {
                    step as isize
                } else {
                    -(step as isize)
                });
                self.bm().top = self.cursor_row().saturating_sub(screen_row);
            }
            return;
        }
        if down && row + step >= rows.len() {
            self.bm().state.pos = self.b().end();
            self.bm().top = rows.len().saturating_sub(l.edit_rows);
        } else if !down && row < step {
            self.bm().state.pos = Pos::default();
            self.bm().top = 0;
        } else {
            let target = if down { row + step } else { row - step };
            let r = &rows[target];
            let x = self
                .conf
                .enc()
                .actual(&self.b().state.lines[r.line], self.b().preferred);
            self.bm().state.pos = Pos { line: r.line, x };
            self.bm().top = if down {
                self.b().top + step
            } else {
                self.b().top.saturating_sub(step)
            };
        }
    }
    pub fn scroll(&mut self, down: bool, amount: usize) {
        let l = render::layout(self);
        let rows = render::visual_rows(self.b(), &self.conf, l.width);
        let top = if down {
            (self.b().top + amount).min(rows.len() - 1)
        } else {
            self.b().top.saturating_sub(amount)
        };
        let row = self.cursor_row();
        self.bm().top = top;
        if row < top {
            self.move_vertical((top - row) as isize);
        } else if row >= top + l.edit_rows {
            self.move_vertical(-((row - top - l.edit_rows + 1) as isize));
        }
    }
    pub fn block(&mut self, down: bool) {
        let mut line = self.b().pos().line;
        let e = self.conf.enc();
        let blank = |i: usize| {
            self.b().state.lines[i].iter().all(|b| *b == 13)
                || e.indent(&self.b().state.lines[i]) == self.b().state.lines[i].len()
        };
        if down {
            let mut saw = false;
            while line + 1 < self.b().state.lines.len() {
                line += 1;
                if blank(line) {
                    saw = true;
                } else if saw {
                    break;
                }
            }
        } else {
            while line > 0 && blank(line) {
                line -= 1;
            }
            while line > 0 && !blank(line - 1) {
                line -= 1;
            }
            if line == self.b().pos().line && line > 0 {
                line -= 1;
                while line > 0 && blank(line) {
                    line -= 1;
                }
                while line > 0 && !blank(line - 1) {
                    line -= 1;
                }
            }
        }
        self.bm().state.pos = Pos { line, x: 0 };
        self.preferred();
        self.center();
    }
    pub fn cut(&mut self, fun: &str) {
        let no = self.conf.on(NO_NEWLINES);
        let p = self.b().pos();
        let region = self.b().region();
        let copy = fun == "copy_text";
        let zap = fun == "zap_text";
        let rest = fun == "cut_till_eof";
        let from = self.conf.on(CUT_FROM_CURSOR);
        let (a, b) = if rest {
            (p, self.b().end())
        } else if let Some(r) = region {
            r
        } else if from {
            if p.x < self.b().line().len() {
                (
                    p,
                    Pos {
                        line: p.line,
                        x: self.b().line().len(),
                    },
                )
            } else if p.line + 1 < self.b().state.lines.len() {
                (
                    p,
                    Pos {
                        line: p.line + 1,
                        x: 0,
                    },
                )
            } else {
                (p, p)
            }
        } else {
            (
                Pos { line: p.line, x: 0 },
                if p.line + 1 < self.b().state.lines.len() {
                    Pos {
                        line: p.line + 1,
                        x: 0,
                    }
                } else {
                    self.b().end()
                },
            )
        };
        if a == b
            || a.x > 0
                && a.line + 1 == self.b().state.lines.len() - 1
                && b == self.b().end()
                && self.b().state.lines[b.line].is_empty()
                && from
        {
            self.bm().state.mark = None;
            self.msg(
                if copy {
                    "Copied nothing"
                } else {
                    "Nothing was cut"
                },
                1,
            );
            return;
        }
        let chain = self.last_command == fun && region.is_none() && !rest;
        let raw = if copy {
            self.b().raw_region(a, b)
        } else {
            self.bm()
                .cut(a, b, if zap { "erasure" } else { "cut" }, chain, no)
        };
        if !zap {
            if chain {
                self.cutbuffer.extend(&raw);
            } else {
                self.cutbuffer = raw;
            }
        }
        if copy {
            self.bm().state.mark = None;
            if region.is_none() {
                self.bm().state.pos = b;
            }
        } else {
            self.bm().state.pos = a;
        }
        self.preferred();
        self.clear();
    }
    pub fn report_position(&mut self) {
        let b = self.b();
        let e = self.conf.enc();
        let lines = b.state.lines.len();
        let current = b.pos().line + 1;
        let col = e.column(b.line(), b.pos().x) + 1;
        let cols = e.breadth(b.line()) + 1;
        let total = b.tally(e);
        let count = b.state.lines[..b.pos().line]
            .iter()
            .map(|s| e.count(s) + 1)
            .sum::<usize>()
            + e.count(&b.line()[..b.pos().x]);
        let raw = unsafe {
            native::from_c(native::nr_position(
                lines.to_string().len().max(2) as i32,
                current,
                lines,
                (current * 100 / lines) as i32,
                col,
                cols,
                (col * 100 / cols) as i32,
                total.to_string().len().max(2) as i32,
                count,
                total,
                ((count * 100).checked_div(total).unwrap_or(0)) as i32,
            ))
        };
        let text = bytes::text(&raw);
        self.msg(text, 3);
    }
}
