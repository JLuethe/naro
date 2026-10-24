//! Terminal cell composition. ANSI output is delegated to ncursesw.
use crate::bytes;
use crate::{
    buffer::{Buffer, Pos},
    bytes::{Encoding, Glyph},
    config::{Config, Style},
    editor::*,
    generated::*,
    native,
};
#[derive(Clone, Debug)]
pub struct Cell {
    pub text: String,
    pub style: Style,
    pub width: usize,
}
#[derive(Clone)]
pub struct Canvas {
    pub cols: usize,
    pub rows: usize,
    pub cells: Vec<Cell>,
}
impl Canvas {
    pub fn new(cols: usize, rows: usize) -> Self {
        Self {
            cols,
            rows,
            cells: vec![
                Cell {
                    text: " ".into(),
                    style: Style::NORMAL,
                    width: 1
                };
                cols * rows
            ],
        }
    }
    pub fn put(&mut self, row: usize, col: usize, text: &str, style: Style, width: usize) {
        if row >= self.rows || col >= self.cols || col + width > self.cols {
            return;
        }
        self.cells[row * self.cols + col] = Cell {
            text: text.into(),
            style,
            width,
        };
        for i in 1..width {
            self.cells[row * self.cols + col + i] = Cell {
                text: String::new(),
                style,
                width: 0,
            };
        }
    }
    pub fn fill(&mut self, row: usize, start: usize, end: usize, style: Style) {
        for c in start..end.min(self.cols) {
            self.put(row, c, " ", style, 1);
        }
    }
    pub fn text(&mut self, row: usize, col: usize, text: &str, style: Style, span: usize) {
        let e = Encoding { utf8: true, tab: 8 };
        let mut x = 0;
        for g in e.display(text.as_bytes(), false, false) {
            if x + g.width > span {
                break;
            }
            self.put(row, col + x, &g.text, style, g.width);
            x += g.width;
        }
    }
    pub fn flush(&self, cursor: (usize, usize, bool)) {
        unsafe {
            native::nr_erase();
        }
        for y in 0..self.rows {
            for x in 0..self.cols {
                let cell = &self.cells[y * self.cols + x];
                if cell.width == 0 {
                    continue;
                }
                let chars: Vec<u32> = cell.text.chars().map(u32::from).collect();
                unsafe {
                    native::nr_put(
                        y as i32,
                        x as i32,
                        chars.as_ptr(),
                        chars.len() as i32,
                        cell.style.bits,
                        cell.style.fg,
                        cell.style.bg,
                    );
                }
            }
        }
        unsafe {
            native::nr_refresh(
                cursor.1.min(self.rows - 1) as i32,
                cursor.0.min(self.cols - 1) as i32,
                cursor.2 as i32,
            );
        }
    }
}
#[derive(Clone, Copy, Debug)]
pub struct Layout {
    pub cols: usize,
    pub rows: usize,
    pub top: usize,
    pub edit_rows: usize,
    pub status: usize,
    pub help: bool,
    pub margin: usize,
    pub sidebar: usize,
    pub width: usize,
}
pub fn layout(ed: &Editor) -> Layout {
    let c = &ed.conf;
    let cols = unsafe { native::nr_cols() }.max(1) as usize;
    let rows = unsafe { native::nr_rows() }.max(1) as usize;
    let zero = c.on(ZERO) && !matches!(ed.mode, Mode::Help(_));
    let mini = c.on(MINIBAR) && !zero;
    let min = if zero {
        3
    } else if mini {
        4
    } else {
        5
    };
    let help = !c.on(NO_HELP) && rows >= min;
    let bottom = if help { 3 } else { 1 };
    let top = if rows < 3 || mini || zero {
        0
    } else {
        1 + usize::from(c.on(EMPTY_LINE) && rows > min)
    };
    let edit_rows = if rows < 3 {
        if zero { rows } else { 1 }
    } else {
        rows.saturating_sub(top + bottom) + usize::from(zero)
    };
    let status = rows - bottom.min(rows);
    let mut margin = if c.on(LINE_NUMBERS) && !matches!(ed.mode, Mode::Help(_) | Mode::Browser(_)) {
        ed.b().state.lines.len().to_string().len().max(2) + 1
    } else {
        0
    };
    if margin + 4 > cols {
        margin = 0;
    }
    let sidebar = usize::from(
        c.on(INDICATOR)
            && rows > 5
            && cols > 9
            && !matches!(ed.mode, Mode::Help(_) | Mode::Browser(_)),
    );
    let width = cols.saturating_sub(margin + sidebar).max(1);
    Layout {
        cols,
        rows,
        top,
        edit_rows: edit_rows.max(1),
        status,
        help,
        margin,
        sidebar,
        width,
    }
}
#[derive(Clone, Debug)]
pub struct VisualRow {
    pub line: usize,
    pub from: usize,
    pub to: usize,
}
pub fn visual_rows(b: &Buffer, c: &Config, width: usize) -> Vec<VisualRow> {
    let mut rows = Vec::new();
    let e = c.enc();
    for (line, s) in b.state.lines.iter().enumerate() {
        let total = e.breadth(s);
        if !c.on(SOFTWRAP) || total == 0 {
            rows.push(VisualRow {
                line,
                from: 0,
                to: total,
            });
            continue;
        }
        let glyphs = e.display(s, false, true);
        let mut from = 0;
        while from < total {
            let mut end = (from + width).min(total);
            let mut at = 0;
            let mut blank = None;
            for g in &glyphs {
                if at < end && at + g.width > end && g.width == 2 {
                    end = at;
                }
                if at > from && at < end && s.get(g.byte).is_some_and(|b| *b == 32 || *b == 9) {
                    blank = Some((at + g.width).min(end));
                }
                at += g.width;
            }
            if c.on(AT_BLANKS)
                && end < total
                && let Some(blank) = blank
            {
                end = blank;
            }
            if end <= from {
                end = (from + width).min(total);
            }
            rows.push(VisualRow {
                line,
                from,
                to: end,
            });
            from = end;
        }
        if total.is_multiple_of(width) {
            rows.push(VisualRow {
                line,
                from: total,
                to: total,
            });
        }
    }
    rows
}
pub fn visual_cursor(b: &Buffer, c: &Config, rows: &[VisualRow]) -> usize {
    let col = c.enc().column(b.line(), b.pos().x);
    rows.iter()
        .enumerate()
        .filter(|(_, r)| r.line == b.pos().line && r.from <= col)
        .map(|(i, _)| i)
        .next_back()
        .unwrap_or(0)
}
pub fn help_items(ed: &Editor, menu: u32, cols: usize) -> (usize, Vec<(String, String, i32)>) {
    let max = ((cols + 40) / 20) * 2;
    let available = ed.conf.funcs.iter().filter(|f| f.menus & menu != 0).count();
    let mut count = available.min(max);
    if menu == WRITE
        && available <= max
        && !ed
            .conf
            .keys
            .iter()
            .any(|k| k.menus & menu != 0 && k.func == "discard_buffer")
    {
        count = count.saturating_sub(1);
    }
    let mut items = Vec::new();
    for f in ed.conf.funcs.iter().filter(|f| f.menus & menu != 0) {
        if let Some(k) = ed
            .conf
            .keys
            .iter()
            .find(|k| k.menus & menu != 0 && k.func == f.func && !k.tag.is_empty())
        {
            let tag = if menu == MAIN && f.func == "do_exit" && ed.buffers.len() > 1 {
                "Close"
            } else {
                &f.tag
            };
            let tag = native::tr(tag);
            let tag = if ed.conf.utf8 {
                tag
            } else {
                tag.replace('…', "...")
            };
            items.push((k.tag.clone(), tag, k.key));
            if items.len() >= count {
                break;
            }
        }
    }
    (count, items)
}
fn helplines(ed: &Editor, canvas: &mut Canvas, l: Layout) {
    if !l.help {
        return;
    }
    let (n, items) = help_items(ed, ed.menu(), l.cols);
    if n == 0 {
        return;
    }
    let width = l.cols / n.div_ceil(2);
    if width == 0 {
        return;
    }
    for (i, (key, tag, _)) in items.iter().enumerate() {
        let row = l.rows - 2 + i % 2;
        let col = i / 2 * width;
        let span = width
            + if n % 2 == 1 && i + 2 == n { width } else { 0 }
            + if i + 2 >= n { l.cols % width } else { 0 };
        let keyw = Encoding { utf8: true, tab: 8 }.breadth(key.as_bytes());
        canvas.text(row, col, key, ed.conf.style("keycolor"), span);
        if keyw + 2 <= span {
            canvas.text(
                row,
                col + keyw + 1,
                tag,
                ed.conf.style("functioncolor"),
                span - keyw - 1,
            );
        }
    }
}
fn title(ed: &Editor, canvas: &mut Canvas, l: Layout) {
    if l.top == 0 {
        return;
    }
    let style = ed.conf.style("titlecolor");
    canvas.fill(0, 0, l.cols, style);
    let e = Encoding {
        utf8: true,
        tab: ed.conf.tab,
    };
    let mut prefix = String::new();
    let mut state = String::new();
    let mut plug = 0;
    let mut upper = String::new();
    let path = match &ed.mode {
        Mode::Prompt(p) if matches!(p.kind, PromptKind::HelpSearch) => ed
            .help_saved
            .as_ref()
            .map(|h| h.title.clone())
            .unwrap_or_default(),
        Mode::Prompt(p)
            if matches!(p.kind, PromptKind::BrowserSearch | PromptKind::BrowserGoto) =>
        {
            prefix = native::tr("DIR:");
            ed.browser_saved
                .as_ref()
                .map(|b| directory_title(&b.dir))
                .unwrap_or_default()
        }
        Mode::Help(h) => h.title.clone(),
        Mode::Browser(b) => {
            prefix = native::tr("DIR:");
            directory_title(&b.dir)
        }
        Mode::Lint(_) => {
            prefix = native::tr("Linting --");
            bytes::text(&ed.b().name)
        }
        _ => {
            upper = if ed.multiple {
                format!("[{}/{}]", ed.current + 1, ed.buffers.len())
            } else {
                "GNU nano 9.3".into()
            };
            state = if ed.conf.on(VIEW_MODE) {
                native::tr("View")
            } else if ed.conf.on(STATEFLAGS) {
                "+.xxxxx".into()
            } else if ed.b().modified {
                native::tr("Modified")
            } else if ed.conf.on(RESTRICTED) {
                native::tr("Restricted")
            } else {
                plug = e.breadth(native::tr("Modified").as_bytes()) + 1;
                String::new()
            };
            if ed.b().name.is_empty() {
                native::tr("New Buffer")
            } else {
                bytes::text(&ed.b().name)
            }
        }
    };
    let path_bytes = path.as_bytes();
    let mut verlen = e.breadth(upper.as_bytes()) + 3;
    let prefixlen = if prefix.is_empty() {
        0
    } else {
        e.breadth(prefix.as_bytes()) + 1
    };
    let pathlen = e.breadth(path_bytes) + usize::from(!state.is_empty());
    let mut statelen = e.breadth(state.as_bytes()) + 2;
    if verlen + prefixlen + pathlen + plug + statelen <= l.cols {
        canvas.text(0, 2, &upper, style, l.cols.saturating_sub(2));
    } else {
        verlen = 2;
        if verlen + prefixlen + pathlen + plug + statelen > l.cols {
            plug = 0;
        }
        if verlen + prefixlen + pathlen + plug + statelen > l.cols {
            verlen = 0;
            statelen = statelen.saturating_sub(2);
        }
    }
    let mut offset = if verlen > 0 {
        verlen
            + (l.cols
                .saturating_sub(verlen + plug + statelen + prefixlen + pathlen))
                / 2
    } else {
        0
    };
    if verlen + prefixlen + pathlen + plug + statelen <= l.cols && !prefix.is_empty() {
        canvas.text(0, offset, &prefix, style, l.cols.saturating_sub(offset));
        offset += prefixlen;
    }
    if pathlen + plug + statelen <= l.cols {
        let glyphs = ed
            .conf
            .enc()
            .display(path_bytes, ed.conf.on(WHITESPACE_DISPLAY), false);
        paint_glyphs(canvas, 0, offset, &glyphs, 0, pathlen, style, false);
    } else if 5 + statelen <= l.cols {
        canvas.text(0, offset, "...", style, 3);
        let from = (3 + pathlen + statelen).saturating_sub(l.cols);
        let glyphs = ed
            .conf
            .enc()
            .display(path_bytes, ed.conf.on(WHITESPACE_DISPLAY), false);
        paint_glyphs(
            canvas,
            0,
            offset + 3,
            &glyphs,
            from,
            l.cols.saturating_sub(statelen + 3),
            style,
            false,
        );
    }
    if ed.conf.on(STATEFLAGS)
        && !ed.conf.on(VIEW_MODE)
        && !matches!(ed.mode, Mode::Help(_) | Mode::Browser(_))
    {
        if ed.b().modified && l.cols > 1 {
            canvas.text(0, offset + e.breadth(path_bytes), " *", style, 2);
        }
        if statelen < l.cols {
            canvas.text(0, l.cols + 2 - statelen, &states(ed), style, 5);
        }
    } else {
        canvas.text(0, l.cols.saturating_sub(statelen), &state, style, l.cols);
    }
}
fn states(ed: &Editor) -> String {
    [
        if ed.conf.on(AUTOINDENT) { 'I' } else { ' ' },
        if ed.b().state.mark.is_some() {
            'M'
        } else {
            ' '
        },
        if ed.conf.on(BREAK_LONG_LINES) {
            'L'
        } else {
            ' '
        },
        if ed.recording { 'R' } else { ' ' },
        if ed.conf.on(SOFTWRAP) { 'S' } else { ' ' },
    ]
    .iter()
    .collect()
}
#[allow(clippy::too_many_arguments)] // Explicit byte-to-cell clipping geometry.
fn paint_glyphs(
    canvas: &mut Canvas,
    row: usize,
    col: usize,
    glyphs: &[Glyph],
    from: usize,
    span: usize,
    style: Style,
    markers: bool,
) {
    let mut at = 0;
    let mut more = false;
    for g in glyphs {
        let end = at + g.width;
        if end <= from {
            at = end;
            continue;
        }
        if at >= from + span {
            more = true;
            break;
        }
        let start = at.saturating_sub(from);
        if at < from {
            canvas.put(row, col, "]", style, 1);
        } else if start + g.width <= span {
            canvas.put(row, col + start, &g.text, style, g.width);
        } else {
            canvas.put(row, col + start, "[", style, 1);
            more = true;
        }
        at = end;
    }
    if markers && span > 0 {
        if from > 0 && at > from {
            canvas.put(row, col, "<", style, 1);
        }
        if more {
            canvas.put(row, col + span - 1, ">", style, 1);
        }
    }
}
fn syntax_spans(ed: &Editor) -> Vec<Vec<(usize, usize, Style)>> {
    let mut spans = vec![Vec::new(); ed.b().state.lines.len()];
    if ed.conf.on(NO_SYNTAX) {
        return spans;
    }
    let Some(syn) = ed.syntax() else {
        return spans;
    };
    let e = ed.conf.enc();
    for rule in &syn.rules {
        let mut open = false;
        for (line, s) in ed.b().state.lines.iter().enumerate() {
            let mut from = 0;
            loop {
                if open {
                    let end = rule.end.as_ref().and_then(|r| r.find(s, from, from > 0));
                    if let Some(m) = end {
                        spans[line].push((from, m[0].1, rule.style));
                        from = m[0].1;
                        open = false;
                        if from == s.len() {
                            break;
                        }
                    } else {
                        spans[line].push((from, s.len(), rule.style));
                        break;
                    }
                } else {
                    if from > s.len() || from > 2000 {
                        break;
                    }
                    let Some(m) = rule.start.find(s, from, from > 0) else {
                        break;
                    };
                    let (a, b) = m[0];
                    if a > 2000 {
                        break;
                    }
                    if let Some(end) = &rule.end {
                        if let Some(m) = end.find(s, b, b > 0) {
                            let z = m[0].1;
                            if z > a {
                                spans[line].push((a, z, rule.style));
                            }
                            if z == a {
                                if z == s.len() {
                                    break;
                                }
                                from = e.right(s, z);
                            } else {
                                from = z;
                            }
                        } else {
                            spans[line].push((a, s.len(), rule.style));
                            open = true;
                            break;
                        }
                    } else {
                        if b > a {
                            spans[line].push((a, b, rule.style));
                            from = b;
                        } else {
                            if a == s.len() {
                                break;
                            }
                            from = e.right(s, a);
                        }
                    }
                }
            }
        }
    }
    spans
}
fn edit(ed: &mut Editor, canvas: &mut Canvas, l: Layout) -> (usize, usize, bool) {
    let c = &ed.conf;
    let e = c.enc();
    let rows = visual_rows(ed.b(), c, l.width);
    let cursor = visual_cursor(ed.b(), c, &rows);
    let mut top = ed.b().top.min(rows.len() - 1);
    if cursor < top {
        top = if c.on(JUMPY_SCROLLING) {
            cursor.saturating_sub(l.edit_rows / 2)
        } else {
            cursor
        };
    }
    if cursor >= top + l.edit_rows {
        top = if c.on(JUMPY_SCROLLING) {
            cursor.saturating_sub(l.edit_rows / 2)
        } else {
            cursor + 1 - l.edit_rows
        };
    }
    let col = e.column(ed.b().line(), ed.b().pos().x);
    let mut brink = ed.b().brink;
    if !c.on(SOFTWRAP) {
        if c.on(SOLO_SIDESCROLL) || l.width <= 8 {
            brink = if col == 0 || col + 2 < l.width {
                0
            } else if l.width > 8 {
                col - 6 - (col - 6) % (l.width - 8)
            } else {
                col.saturating_sub(l.width.saturating_sub(2))
            };
        } else if col < 3 {
            brink = 0;
        } else if col < brink + 3 {
            brink = if c.on(JUMPY_SCROLLING) {
                col.saturating_sub(l.width / 2)
            } else {
                col - 3
            };
        } else if col > brink + l.width - 4 {
            brink = col.saturating_sub(l.width)
                + if c.on(JUMPY_SCROLLING) {
                    l.width / 2
                } else {
                    3
                }
                + 1;
        }
    }
    let spans = syntax_spans(ed);
    let region = ed.b().region();
    for row in 0..l.edit_rows {
        if let Some(v) = rows.get(top + row) {
            let s = &ed.b().state.lines[v.line];
            if l.margin > 0 && v.from == 0 {
                let number = format!("{:>width$}", v.line + 1, width = l.margin - 1);
                canvas.text(
                    l.top + row,
                    0,
                    &number,
                    c.style("numbercolor"),
                    l.margin - 1,
                );
                if ed.b().state.anchors[v.line] {
                    canvas.text(
                        l.top + row,
                        l.margin - 1,
                        if c.utf8 { "†" } else { "+" },
                        Style::NORMAL,
                        1,
                    );
                }
            }
            let from = if c.on(SOFTWRAP) {
                v.from
            } else if c.on(SOLO_SIDESCROLL) && v.line != ed.b().pos().line {
                0
            } else {
                brink
            };
            let glyphs = e.display(s, c.on(WHITESPACE_DISPLAY), true);
            let mut at = 0;
            let span = if c.on(SOFTWRAP) {
                v.to.saturating_sub(v.from).min(l.width)
            } else {
                l.width
            };
            for g in &glyphs {
                let end = at + g.width;
                if end > from && at < from + span {
                    let mut style = Style::NORMAL;
                    for (a, b, paint) in &spans[v.line] {
                        if g.byte >= *a && g.byte < *b {
                            style = *paint;
                        }
                    }
                    if c.guide > 0 && at < c.guide && end > c.guide - 1 {
                        style = c.style("stripecolor");
                    }
                    if let Some((a, b)) = region
                        && (Pos {
                            line: v.line,
                            x: g.byte,
                        }) >= a
                        && (Pos {
                            line: v.line,
                            x: g.byte,
                        }) < b
                    {
                        style = c.style("selectedcolor");
                    }
                    if let Some((line, a, b)) = ed.spotlight
                        && line == v.line
                        && g.byte >= a
                        && g.byte < b
                    {
                        style = c.style("spotlightcolor");
                    }
                    let x = at.saturating_sub(from);
                    if at < from {
                        canvas.put(l.top + row, l.margin, "]", style, 1);
                    } else if x + g.width <= l.width {
                        canvas.put(l.top + row, l.margin + x, &g.text, style, g.width);
                    } else if x < l.width {
                        canvas.put(l.top + row, l.margin + x, "[", style, 1);
                    }
                }
                at = end;
            }
            if !c.on(SOFTWRAP) && !s.is_empty() {
                if from > 0 && at > from {
                    canvas.put(
                        l.top + row,
                        l.margin,
                        "<",
                        if c.on(BOLD_TEXT) {
                            Style {
                                bits: 1,
                                ..Style::NORMAL
                            }
                        } else {
                            Style::reverse()
                        },
                        1,
                    );
                }
                if at > from + l.width {
                    canvas.put(
                        l.top + row,
                        l.margin + l.width - 1,
                        ">",
                        if c.on(BOLD_TEXT) {
                            Style {
                                bits: 1,
                                ..Style::NORMAL
                            }
                        } else {
                            Style::reverse()
                        },
                        1,
                    );
                }
            }
            if c.guide > 0 && c.guide > from && c.guide - 1 < from + l.width {
                let x = l.margin + c.guide - 1 - from;
                let i = (l.top + row) * canvas.cols + x;
                if canvas.cells[i].text == " " {
                    canvas.cells[i].style = c.style("stripecolor");
                }
            }
            if let Some((line, a, b)) = ed.spotlight
                && line == v.line
                && a == b
            {
                let column = e.column(s, a);
                if column >= from && column < from + l.width {
                    canvas.put(
                        l.top + row,
                        l.margin + column - from,
                        " ",
                        c.style("spotlightcolor"),
                        1,
                    );
                }
            }
        }
    }
    if l.sidebar > 0 {
        let lowest = top * l.edit_rows / rows.len();
        let highest = if rows.len() < l.edit_rows {
            l.edit_rows
        } else {
            lowest + l.edit_rows * l.edit_rows / rows.len()
        };
        for r in 0..l.edit_rows {
            let mut style = c.style("scrollercolor");
            if r >= lowest && r <= highest {
                style.bits ^= 4;
            }
            canvas.put(l.top + r, l.cols - 1, " ", style, 1);
        }
    }
    let from = if c.on(SOFTWRAP) {
        rows[cursor].from
    } else {
        brink
    };
    let result = (
        l.margin + col.saturating_sub(from),
        l.top + cursor - top,
        ed.spotlight.is_none() || c.on(SHOW_CURSOR),
    );
    ed.bm().top = top;
    ed.bm().brink = brink;
    result
}
fn message(ed: &Editor, canvas: &mut Canvas, l: Layout) {
    if let Some(m) = &ed.message {
        let style = ed.conf.style(if m.level >= 5 {
            "errorcolor"
        } else if m.level == 4 {
            "selectedcolor"
        } else {
            "statuscolor"
        });
        let text = &m.text;
        let e = Encoding { utf8: true, tab: 8 };
        let width = e.breadth(text.as_bytes()).min(l.cols);
        let start = (l.cols - width) / 2;
        if start > 1 {
            canvas.text(
                l.status,
                start - 2,
                &format!("[ {text} ]"),
                style,
                l.cols - start + 2,
            );
            if m.ellipsis {
                canvas.text(l.status, start + width + 3, "...", style, 3);
            }
        } else {
            canvas.text(l.status, start, text, style, l.cols - start);
        }
    }
}
fn minibar(ed: &Editor, canvas: &mut Canvas, l: Layout) {
    let c = &ed.conf;
    let style = c.style("minicolor");
    canvas.fill(l.status, 0, l.cols, style);
    let name = if ed.b().name.is_empty() {
        "(nameless)".into()
    } else {
        bytes::text(&ed.b().name)
    };
    let e = Encoding { utf8: true, tab: 8 };
    let padding = if e.breadth(name.as_bytes()) + 19 > l.cols {
        0
    } else {
        2
    };
    canvas.text(
        l.status,
        padding,
        &format!("{name}{}", if ed.b().modified { " *" } else { "  " }),
        style,
        l.cols.saturating_sub(padding),
    );
    if ed.b().report_size && l.cols > 35 {
        let n = ed.b().line_count();
        let count = native::plural(" (%zu line)", " (%zu lines)", n).replace("%zu", &n.to_string());
        let offset = padding + e.breadth(name.as_bytes()) + 2;
        if e.breadth(name.as_bytes()) + e.breadth(count.as_bytes()) + 11 < l.cols {
            canvas.text(
                l.status,
                offset,
                &count,
                style,
                l.cols.saturating_sub(offset),
            );
        }
    }
    if l.cols > 35 && c.on(CONSTANT_SHOW) {
        let pos = format!(
            "{},{}",
            ed.b().pos().line + 1,
            c.enc().column(ed.b().line(), ed.b().pos().x) + 1
        );
        canvas.text(
            l.status,
            l.cols.saturating_sub(27 + pos.len()),
            &pos,
            style,
            pos.len(),
        );
        let code = if ed.b().pos() == ed.b().end() {
            "  ----".into()
        } else if ed.b().pos().x == ed.b().line().len() {
            "U+000A".into()
        } else {
            match c.enc().code(ed.b().line(), ed.b().pos().x) {
                Some(10) => "  0x00".into(),
                Some(code) => format!("U+{code:04X}"),
                None => format!("  0x{:02X}", ed.b().line()[ed.b().pos().x]),
            }
        };
        canvas.text(l.status, l.cols - 23, &code, style, 6);
    }
    if c.on(STATEFLAGS) && l.cols >= 16 {
        canvas.text(l.status, l.cols - 11 - padding, &states(ed), style, 5);
    }
    if l.cols > 8 {
        canvas.text(
            l.status,
            l.cols - 4 - padding,
            &format!(
                "{:3}%",
                (ed.b().pos().line + 1) * 100 / ed.b().state.lines.len()
            ),
            style,
            4,
        );
    }
}
fn prompt(ed: &Editor, p: &Prompt, canvas: &mut Canvas, l: Layout) -> (usize, usize, bool) {
    let style = ed.conf.style("promptcolor");
    canvas.fill(l.status, 0, l.cols, style);
    let e = Encoding {
        utf8: true,
        tab: ed.conf.tab,
    };
    let label = ed.prompt_label(p);
    let n = e.actual(label.as_bytes(), l.cols.saturating_sub(5));
    let label = &label[..n];
    let base = e.breadth(label.as_bytes()) + 2;
    let column = base + ed.conf.enc().column(&p.answer, p.x);
    let page = if column == base || column < l.cols - 1 {
        0
    } else if l.cols > base + 2 {
        column - base - 1 - (column - base - 1) % (l.cols - base - 2)
    } else {
        column.saturating_sub(2)
    };
    canvas.text(
        l.status,
        0,
        &format!("{label}:{}", if page > 0 { '<' } else { ' ' }),
        style,
        l.cols,
    );
    let glyphs = ed.conf.enc().display(&p.answer, false, false);
    paint_glyphs(
        canvas,
        l.status,
        base,
        &glyphs,
        page,
        l.cols.saturating_sub(base),
        style,
        false,
    );
    if ed.conf.enc().breadth(&p.answer) > page + l.cols.saturating_sub(base) {
        canvas.put(l.status, l.cols - 1, ">", style, 1);
    }
    if !ed.completion.is_empty() {
        for row in l.top..l.top + l.edit_rows {
            canvas.fill(row, 0, l.cols, Style::NORMAL);
        }
        let e = ed.conf.enc();
        let max = ed
            .completion
            .iter()
            .map(|s| e.breadth(s))
            .max()
            .unwrap_or(0)
            .min(l.cols - 1);
        let width = max + 2;
        let piles = ((l.cols + 1) / width).max(1);
        let height = ed.completion.len().div_ceil(piles);
        let first = l.top + l.edit_rows.saturating_sub(height + 1);
        for (i, name) in ed.completion.iter().enumerate() {
            let row = first + i / piles;
            if row >= l.top + l.edit_rows {
                break;
            }
            if height >= l.edit_rows && row == l.top + l.edit_rows - 1 && i % piles == piles - 1 {
                canvas.text(row, i % piles * width, "(more)", Style::NORMAL, max);
                break;
            }
            canvas.text(
                row,
                i % piles * width,
                &bytes::text(name),
                Style::NORMAL,
                max,
            );
        }
    }

    (column.saturating_sub(page), l.status, true)
}
pub fn draw(ed: &mut Editor) {
    let l = layout(ed);
    let paused = ed
        .pause_screen
        .as_ref()
        .filter(|s| s.cols == l.cols && s.rows == l.rows)
        .cloned();
    let mut canvas = paused
        .clone()
        .unwrap_or_else(|| Canvas::new(l.cols, l.rows));
    let startup_lock = matches!(
        &ed.mode,
        Mode::Question(Question {
            kind: QuestionKind::Lock(_),
            ..
        })
    );
    let mut cursor = if startup_lock {
        (0, l.top, true)
    } else if paused.is_some() {
        title(ed, &mut canvas, l);
        (0, l.top, true)
    } else {
        title(ed, &mut canvas, l);
        edit(ed, &mut canvas, l)
    };
    if (!ed.conf.on(ZERO) && l.rows > 1) || ed.message.is_some() {
        canvas.fill(l.status, 0, l.cols, Style::NORMAL);
    }
    if ed.conf.on(MINIBAR) && !ed.conf.on(ZERO) && ed.message.is_none() {
        minibar(ed, &mut canvas, l);
    }
    if let Mode::Prompt(p) = &ed.mode {
        if matches!(p.kind, PromptKind::HelpSearch)
            && let Some(h) = &ed.help_saved
        {
            paint_help(ed, &mut canvas, l, h);
        }
        if matches!(p.kind, PromptKind::BrowserSearch | PromptKind::BrowserGoto)
            && let Some(b) = &ed.browser_saved
        {
            paint_browser(ed, &mut canvas, l, b);
        }
    }
    message(ed, &mut canvas, l);
    if paused.is_none() {
        helplines(ed, &mut canvas, l);
    }
    match &ed.mode {
        Mode::Prompt(p) => cursor = prompt(ed, p, &mut canvas, l),
        Mode::Question(q) => {
            let style = ed.conf.style("promptcolor");
            canvas.fill(l.status, 0, l.cols, style);
            canvas.text(
                l.status,
                0,
                &native::tr(&q.text),
                style,
                l.cols.saturating_sub(1),
            );
            if l.help {
                canvas.fill(l.rows - 2, 0, l.cols, Style::NORMAL);
                canvas.fill(l.rows - 1, 0, l.cols, Style::NORMAL);
                let width = if l.cols < 32 { l.cols / 2 } else { 16 };
                for (row, col, key, label) in [
                    (
                        l.rows - 2,
                        0,
                        format!(" {}", native::tr("Yy").chars().next().unwrap_or('Y')),
                        native::tr("Yes"),
                    ),
                    (
                        l.rows - 1,
                        0,
                        format!(" {}", native::tr("Nn").chars().next().unwrap_or('N')),
                        native::tr("No"),
                    ),
                    (l.rows - 1, width, "^C".into(), native::tr("Cancel")),
                ] {
                    canvas.text(row, col, &key, ed.conf.style("keycolor"), width);
                    canvas.text(
                        row,
                        col + key.len() + 1,
                        &label,
                        ed.conf.style("functioncolor"),
                        width.saturating_sub(key.len() + 1),
                    );
                }
                if q.all {
                    let key = format!(" {}", native::tr("Aa").chars().next().unwrap_or('A'));
                    canvas.text(l.rows - 2, width, &key, ed.conf.style("keycolor"), 2);
                    canvas.text(
                        l.rows - 2,
                        width + 3,
                        &native::tr("All"),
                        Style::NORMAL,
                        width.saturating_sub(3),
                    );
                }
            }
            let width = Encoding { utf8: true, tab: 8 }
                .breadth(native::tr(&q.text).as_bytes())
                .min(l.cols - 1);
            cursor = (width, l.status, !q.all);
        }
        Mode::Help(h) => cursor = paint_help(ed, &mut canvas, l, h),
        Mode::Browser(b) => cursor = paint_browser(ed, &mut canvas, l, b),
        Mode::Lint(_) => {}
        Mode::Edit => {}
    }
    if ed.pause_until.is_some() {
        if l.help && paused.is_none() {
            canvas.fill(l.rows - 2, 0, l.cols, Style::NORMAL);
            canvas.fill(l.rows - 1, 0, l.cols, Style::NORMAL);
        }
        if l.help
            && ed.pause_next.as_ref().is_some_and(|m| {
                matches!(
                    m.as_ref(),
                    Mode::Prompt(Prompt {
                        kind: PromptKind::Spell,
                        ..
                    })
                )
            })
        {
            canvas.fill(l.rows - 1, 0, l.cols, Style::NORMAL);
            let width = if l.cols < 32 { l.cols / 2 } else { 16 };
            let no = format!(" {}", native::tr("Nn").chars().next().unwrap_or('N'));
            canvas.text(l.rows - 1, 0, &no, ed.conf.style("keycolor"), width);
            canvas.text(
                l.rows - 1,
                3,
                &native::tr("No"),
                ed.conf.style("functioncolor"),
                width.saturating_sub(3),
            );
            canvas.text(l.rows - 1, width, "^C", ed.conf.style("keycolor"), width);
            canvas.text(
                l.rows - 1,
                width + 3,
                &native::tr("Cancel"),
                ed.conf.style("functioncolor"),
                width.saturating_sub(3),
            );
        }
        let width = ed
            .message
            .as_ref()
            .map(|m| Encoding { utf8: true, tab: 8 }.breadth(m.text.as_bytes()))
            .unwrap_or(0);
        cursor = ((l.cols + width) / 2 + 2, l.status, false);
    }
    if l.rows == 1 && ed.message.as_ref().is_some_and(|m| m.level > 1) {
        cursor.2 = false;
    }
    canvas.flush(cursor);
    ed.last_screen = Some(canvas);
}

fn directory_title(p: &std::path::Path) -> String {
    let mut s = p.to_string_lossy().into_owned();
    if !s.ends_with('/') {
        s.push('/');
    }
    s
}
fn paint_browser(
    ed: &Editor,
    canvas: &mut Canvas,
    l: Layout,
    b: &BrowserState,
) -> (usize, usize, bool) {
    for row in 0..l.edit_rows {
        canvas.fill(l.top + row, 0, l.cols, Style::NORMAL);
    }
    let page = b.selected / (l.edit_rows * b.piles).max(1) * (l.edit_rows * b.piles);
    for (i, p) in b
        .entries
        .iter()
        .enumerate()
        .skip(page)
        .take(l.edit_rows * b.piles)
    {
        let n = i - page;
        let row = l.top + n / b.piles;
        let col = n % b.piles * (b.gauge + 2);
        let style = if i == b.selected {
            ed.conf.style("selectedcolor")
        } else {
            Style::NORMAL
        };
        canvas.fill(row, col, col + b.gauge, style);
        let name = p
            .file_name()
            .map(|s| s.to_string_lossy().into_owned())
            .unwrap_or_else(|| "..".into());
        let meta = std::fs::metadata(p).ok();
        let info = if name == ".." {
            "(parent dir)".into()
        } else if p.is_dir() {
            "(dir)".into()
        } else if p.is_symlink() {
            "--".into()
        } else if let Some(meta) = meta {
            let size = meta.len();
            if size < 1024 {
                format!("{size:4}  B")
            } else if size < 1048576 {
                format!("{:4} KB", size / 1024)
            } else if size < 1073741824 {
                format!("{:4} MB", size / 1048576)
            } else {
                format!("{:4} GB", size / 1073741824)
            }
        } else {
            "--".into()
        };
        let name = if name.chars().count() >= b.gauge.saturating_sub(7) && l.cols >= 15 {
            let tail: String = name
                .chars()
                .rev()
                .take(b.gauge.saturating_sub(10))
                .collect::<String>()
                .chars()
                .rev()
                .collect();
            format!("...{tail}")
        } else {
            name
        };
        canvas.text(row, col, &name, style, b.gauge);
        let infow = info.len().min(b.gauge);
        canvas.text(row, col + b.gauge - infow, &info, style, infow);
    }
    let count = b
        .entries
        .len()
        .saturating_sub(page)
        .min(l.edit_rows * b.piles);
    let row = l.top + count.saturating_sub(1) / b.piles;
    let column = canvas.cells[row * l.cols..(row + 1) * l.cols]
        .iter()
        .enumerate()
        .filter(|(_, c)| c.text != " " && !c.text.is_empty())
        .map(|(i, c)| i + c.width)
        .next_back()
        .unwrap_or(0)
        .min(l.cols - 1);
    if (ed.message.is_some() || b.footer_cursor) && l.help {
        let y = l.rows - 1;
        let x = canvas.cells[y * l.cols..(y + 1) * l.cols]
            .iter()
            .enumerate()
            .filter(|(_, c)| c.text != " " && !c.text.is_empty())
            .map(|(i, c)| i + c.width)
            .next_back()
            .unwrap_or(0)
            .min(l.cols - 1);
        (x, y, ed.conf.on(SHOW_CURSOR))
    } else {
        (column, row, ed.conf.on(SHOW_CURSOR))
    }
}
fn paint_help(ed: &Editor, canvas: &mut Canvas, l: Layout, h: &HelpState) -> (usize, usize, bool) {
    let e = Encoding { utf8: true, tab: 8 };
    for row in 0..l.edit_rows {
        canvas.fill(l.top + row, 0, l.cols, Style::NORMAL);
        if let Some(line) = h.lines.get(h.top + row) {
            let mut x = 0;
            for g in e.display(line, false, true) {
                if x + g.width > l.cols {
                    break;
                }
                let style = if h
                    .highlight
                    .is_some_and(|(i, a, b)| i == h.top + row && g.byte >= a && g.byte < b)
                {
                    ed.conf.style("spotlightcolor")
                } else {
                    Style::NORMAL
                };
                canvas.put(l.top + row, x, &g.text, style, g.width);
                x += g.width;
            }
        }
    }
    if let Some((line, x, _)) = h.highlight {
        (
            e.column(&h.lines[line], x),
            l.top + line.saturating_sub(h.top),
            ed.conf.on(SHOW_CURSOR),
        )
    } else {
        (
            0,
            l.top + if h.cursor_bottom { l.edit_rows - 1 } else { 0 },
            false,
        )
    }
}
