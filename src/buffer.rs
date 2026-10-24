//! Byte-line buffer and transactional undo. No filesystem or terminal effects.
use crate::bytes::{self, Encoding};
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq, Ord, PartialOrd)]
pub struct Pos {
    pub line: usize,
    pub x: usize,
}
#[derive(Clone, Debug, PartialEq)]
pub struct State {
    pub lines: Vec<Vec<u8>>,
    pub pos: Pos,
    pub mark: Option<Pos>,
    pub anchors: Vec<bool>,
}
#[derive(Clone, Debug)]
pub struct Undo {
    pub before: State,
    pub after: State,
    pub kind: String,
}
#[derive(Debug)]
pub struct Buffer {
    pub state: State,
    pub name: Vec<u8>,
    pub modified: bool,
    pub dos: bool,
    pub preferred: usize,
    pub top: usize,
    pub firstcol: usize,
    pub brink: usize,
    pub softmark: bool,
    pub history: Vec<Undo>,
    pub hist: usize,
    pub saved: Option<usize>,
    pub last_kind: String,
    pub stat: Option<std::fs::Metadata>,
    pub lock: Option<std::path::PathBuf>,
    pub lock_modified: bool,
    pub deferred: Option<String>,
    pub report_size: bool,
    pub syntax: Option<usize>,
}
impl Default for Buffer {
    fn default() -> Self {
        Self::new(Vec::new(), vec![Vec::new()])
    }
}
impl Buffer {
    pub fn new(name: Vec<u8>, lines: Vec<Vec<u8>>) -> Self {
        let n = lines.len();
        Self {
            state: State {
                lines,
                pos: Pos::default(),
                mark: None,
                anchors: vec![false; n],
            },
            name,
            modified: false,
            dos: false,
            preferred: 0,
            top: 0,
            firstcol: 0,
            brink: 0,
            softmark: false,
            history: Vec::new(),
            hist: 0,
            saved: Some(0),
            last_kind: String::new(),
            stat: None,
            lock: None,
            lock_modified: false,
            deferred: None,
            report_size: false,
            syntax: None,
        }
    }
    pub fn pos(&self) -> Pos {
        self.state.pos
    }
    pub fn set_pos(&mut self, p: Pos) {
        let line = p.line.min(self.state.lines.len() - 1);
        self.state.pos = Pos {
            line,
            x: p.x.min(self.state.lines[line].len()),
        };
    }
    pub fn line(&self) -> &[u8] {
        &self.state.lines[self.pos().line]
    }
    pub fn raw(&self) -> Vec<u8> {
        self.raw_region(Pos::default(), self.end())
    }
    pub fn end(&self) -> Pos {
        let line = self.state.lines.len() - 1;
        Pos {
            line,
            x: self.state.lines[line].len(),
        }
    }
    pub fn line_count(&self) -> usize {
        self.state.lines.len() - usize::from(self.state.lines.last().is_some_and(|l| l.is_empty()))
    }
    pub fn tally(&self, e: Encoding) -> usize {
        self.state.lines.iter().map(|l| e.count(l)).sum::<usize>() + self.state.lines.len() - 1
    }
    pub fn offset(&self, p: Pos) -> usize {
        self.state.lines[..p.line]
            .iter()
            .map(|l| l.len() + 1)
            .sum::<usize>()
            + p.x
    }
    pub fn position_at_offset(&self, mut off: usize) -> Pos {
        for (line, s) in self.state.lines.iter().enumerate() {
            if off <= s.len() {
                return Pos { line, x: off };
            }
            off -= s.len() + 1;
        }
        self.end()
    }
    pub fn raw_region(&self, a: Pos, b: Pos) -> Vec<u8> {
        let mut v = Vec::new();
        for l in a.line..=b.line {
            if l > a.line {
                v.push(b'\n');
            }
            let s = &self.state.lines[l];
            v.extend(bytes::decode_nuls(
                &s[if l == a.line { a.x } else { 0 }..if l == b.line { b.x } else { s.len() }],
            ));
        }
        v
    }
    pub fn region(&self) -> Option<(Pos, Pos)> {
        self.state.mark.map(|m| {
            if m < self.pos() {
                (m, self.pos())
            } else {
                (self.pos(), m)
            }
        })
    }
    pub fn range_lines(&self) -> std::ops::RangeInclusive<usize> {
        let (a, b) = self.region().unwrap_or((self.pos(), self.pos()));
        let end = if b.line > a.line && b.x == 0 {
            b.line - 1
        } else {
            b.line
        };
        a.line..=end
    }
    pub fn magic(&mut self, nonew: bool) {
        if self.state.lines.is_empty() {
            self.state.lines.push(Vec::new());
        }
        if !nonew && self.state.lines.last().is_some_and(|l| !l.is_empty()) {
            self.state.lines.push(Vec::new());
        }
        self.state.anchors.resize(self.state.lines.len(), false);
    }
    pub fn begin(&self) -> State {
        self.state.clone()
    }
    pub fn finish(&mut self, before: State, kind: &str, group: bool, nonew: bool) {
        self.magic(nonew);
        self.history.truncate(self.hist);
        if self.saved.is_some_and(|s| s > self.hist) {
            self.saved = None;
        }
        let join = group
            && self.last_kind == kind
            && self.hist > 0
            && self.saved != Some(self.hist)
            && self.history[self.hist - 1].after.pos == before.pos;
        let after = self.state.clone();
        if join {
            self.history[self.hist - 1].after = after;
        } else {
            self.history.push(Undo {
                before,
                after,
                kind: kind.into(),
            });
            self.hist += 1;
        }
        self.last_kind = kind.into();
        self.modified = true;
    }
    pub fn saved(&mut self) {
        self.saved = Some(self.hist);
        self.modified = false;
        self.last_kind.clear();
    }
    pub fn undo(&mut self, redo: bool) -> Option<String> {
        let (index, state) = if redo {
            if self.hist >= self.history.len() {
                return None;
            }
            let i = self.hist;
            self.hist += 1;
            (i, self.history[i].after.clone())
        } else {
            if self.hist == 0 {
                return None;
            }
            self.hist -= 1;
            (self.hist, self.history[self.hist].before.clone())
        };
        self.state = state;
        self.state.mark = None;
        self.softmark = false;
        self.modified = self.saved != Some(self.hist);
        self.last_kind.clear();
        Some(self.history[index].kind.clone())
    }
    /// Replace an ordered region with external bytes (LF separators, NUL payload).
    pub fn replace(&mut self, a: Pos, b: Pos, raw: &[u8]) {
        let start = self.offset(a);
        let end = self.offset(b);
        let mark = self.state.mark.map(|m| self.offset(m));
        let prefix = self.state.lines[a.line][..a.x].to_vec();
        let suffix = self.state.lines[b.line][b.x..].to_vec();
        let mut lines: Vec<Vec<u8>> = raw.split(|b| *b == 10).map(bytes::encode_nuls).collect();
        let count = lines.len();
        let lastlen = lines.last().unwrap().len();
        lines[0].splice(0..0, prefix);
        lines.last_mut().unwrap().extend(suffix);
        let anchor = self.state.anchors[a.line..=b.line].iter().any(|b| *b);
        self.state.lines.splice(a.line..=b.line, lines);
        self.state.anchors.splice(
            a.line..=b.line,
            std::iter::once(anchor).chain(std::iter::repeat_n(false, count - 1)),
        );
        self.state.pos = Pos {
            line: a.line + count - 1,
            x: if count == 1 { a.x + lastlen } else { lastlen },
        };
        if let Some(m) = mark {
            let m = if m > end {
                m - end + start + raw.len()
            } else if m > start {
                start
            } else {
                m
            };
            self.state.mark = Some(self.position_at_offset(m));
        }
    }
    pub fn insert(&mut self, raw: &[u8], kind: &str, group: bool, nonew: bool) {
        if raw.is_empty() {
            return;
        }
        let before = self.begin();
        let p = self.pos();
        self.replace(p, p, raw);
        self.finish(before, kind, group, nonew);
    }
    pub fn enter(&mut self, e: Encoding, auto: bool, nonew: bool) {
        let before = self.begin();
        let p = self.pos();
        let n = if auto {
            e.indent(self.line()).min(p.x)
        } else {
            0
        };
        let indent = bytes::decode_nuls(&self.line()[..n]);
        if auto && n == p.x && e.indent(self.line()) == p.x {
            self.replace(Pos { line: p.line, x: 0 }, p, b"");
        }
        let p = self.pos();
        let mut raw = vec![b'\n'];
        raw.extend(indent);
        self.replace(p, p, &raw);
        self.finish(before, "line break", false, nonew);
    }
    pub fn delete(&mut self, e: Encoding, back: bool, nonew: bool, zap: bool) -> bool {
        if zap
            && let Some((a, b)) = self.region()
            && a != b
        {
            let before = self.begin();
            self.replace(a, b, b"");
            self.state.mark = None;
            self.finish(before, "erasure", false, nonew);
            return true;
        }
        let before = self.begin();
        let p = self.pos();
        let (a, b, kind) = if back {
            if p.x > 0 {
                (
                    Pos {
                        line: p.line,
                        x: e.left(self.line(), p.x),
                    },
                    p,
                    "deletion",
                )
            } else if p.line > 0 {
                (
                    Pos {
                        line: p.line - 1,
                        x: self.state.lines[p.line - 1].len(),
                    },
                    p,
                    "line join",
                )
            } else {
                return false;
            }
        } else if p.x < self.line().len() {
            (
                p,
                Pos {
                    line: p.line,
                    x: e.move_right(self.line(), p.x),
                },
                "deletion",
            )
        } else if p.line + 1 < self.state.lines.len() {
            (
                p,
                Pos {
                    line: p.line + 1,
                    x: 0,
                },
                "line join",
            )
        } else {
            return false;
        };
        if !nonew
            && b.line == self.state.lines.len() - 1
            && self.state.lines[b.line].is_empty()
            && a.x > 0
            && a.line != b.line
        {
            if back {
                self.state.pos = a;
                self.finish(before, kind, false, nonew);
                self.modified = self.saved != Some(self.hist - 1);
                return true;
            }
            return false;
        }
        self.replace(a, b, b"");
        let deletion_key = if back { "backspace" } else { "delete" };
        let same_kind = self.last_kind == deletion_key;
        self.last_kind = if same_kind {
            "deletion".into()
        } else {
            String::new()
        };
        self.finish(
            before,
            kind,
            kind == "deletion" && self.pos().line == p.line,
            nonew,
        );
        self.last_kind = if kind == "deletion" {
            deletion_key.into()
        } else {
            kind.into()
        };
        true
    }
    pub fn cut(&mut self, a: Pos, b: Pos, kind: &str, group: bool, nonew: bool) -> Vec<u8> {
        let raw = self.raw_region(a, b);
        if a == b {
            return raw;
        }
        let before = self.begin();
        self.replace(a, b, b"");
        self.state.mark = None;
        self.softmark = false;
        self.finish(before, kind, group, nonew);
        raw
    }
    pub fn move_h(&mut self, e: Encoding, right: bool) {
        let p = self.pos();
        let target = if right {
            if p.x < self.line().len() {
                Pos {
                    line: p.line,
                    x: e.move_right(self.line(), p.x),
                }
            } else if p.line + 1 < self.state.lines.len() {
                Pos {
                    line: p.line + 1,
                    x: 0,
                }
            } else {
                p
            }
        } else if p.x > 0 {
            Pos {
                line: p.line,
                x: e.move_left(self.line(), p.x),
            }
        } else if p.line > 0 {
            Pos {
                line: p.line - 1,
                x: self.state.lines[p.line - 1].len(),
            }
        } else {
            p
        };
        self.state.pos = target;
        self.preferred = e.column(self.line(), target.x);
    }
    pub fn move_v(&mut self, e: Encoding, delta: isize) {
        let line = self
            .pos()
            .line
            .saturating_add_signed(delta)
            .min(self.state.lines.len() - 1);
        self.state.pos = Pos {
            line,
            x: e.actual(&self.state.lines[line], self.preferred),
        };
    }
    pub fn word_target(
        &self,
        e: Encoding,
        right: bool,
        after: bool,
        punct: bool,
        extra: &[u8],
    ) -> Pos {
        let mut p = self.pos();
        let mut seen = false;
        let mut wasword = e.word(&self.state.lines[p.line], p.x, punct, extra);
        if right {
            loop {
                let s = &self.state.lines[p.line];
                if p.x < s.len() {
                    p.x = e.move_right(s, p.x);
                } else if p.line + 1 < self.state.lines.len() {
                    p.line += 1;
                    p.x = 0;
                    wasword = false;
                } else {
                    return p;
                }
                let w = e.word(&self.state.lines[p.line], p.x, punct, extra);
                if after {
                    if wasword && !w {
                        return p;
                    }
                } else if !wasword && w {
                    return p;
                }
                wasword = w;
            }
        } else {
            loop {
                if p.x > 0 {
                    p.x = e.move_left(&self.state.lines[p.line], p.x);
                } else if p.line > 0 {
                    if seen {
                        return p;
                    }
                    p.line -= 1;
                    p.x = self.state.lines[p.line].len();
                } else {
                    return p;
                }
                let w = e.word(&self.state.lines[p.line], p.x, punct, extra);
                if seen && !w {
                    p.x = e.move_right(&self.state.lines[p.line], p.x);
                    return p;
                }
                seen |= w;
                if p.x == 0 && w {
                    return p;
                }
            }
        }
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn byte_edits_saved_and_redo() {
        let mut b = Buffer::default();
        b.insert(b"a\0b", "addition", true, false);
        assert_eq!(b.raw(), b"a\0b\n");
        b.saved();
        b.insert(b"!", "addition", true, false);
        assert_eq!(b.history.len(), 2);
        b.undo(false);
        assert!(!b.modified);
        assert_eq!(b.raw(), b"a\0b\n");
        b.undo(false);
        assert_eq!(b.raw(), b"");
        assert!(b.modified);
        b.undo(true);
        assert!(!b.modified);
        b.insert(b"x", "addition", true, false);
        assert!(b.undo(true).is_none());
    }
    #[test]
    fn backspace_and_delete_are_distinct_undo_groups() {
        let e = Encoding { utf8: true, tab: 8 };
        let mut b = Buffer::new(vec![], vec![b"abcdef".to_vec(), vec![]]);
        b.state.pos.x = 3;
        b.delete(e, true, false, false);
        b.delete(e, true, false, false);
        b.delete(e, false, false, false);
        assert_eq!(b.raw(), b"aef\n");
        b.undo(false);
        assert_eq!(b.raw(), b"adef\n");
        b.undo(false);
        assert_eq!(b.raw(), b"abcdef\n");
    }
    #[test]
    fn region_splice() {
        let mut b = Buffer::new(vec![], vec![b"abc".to_vec(), b"def".to_vec(), vec![]]);
        b.replace(Pos { line: 0, x: 1 }, Pos { line: 1, x: 2 }, b"X\nY");
        assert_eq!(b.raw(), b"aX\nYf\n");
        assert_eq!(b.pos(), Pos { line: 1, x: 1 });
    }
}
