//! Byte-line buffer and transactional undo. No filesystem or terminal effects.
use crate::bytes::{self, Encoding};
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq, Ord, PartialOrd)]
pub struct Pos {
    pub line: usize,
    pub x: usize,
}
/// How a splice affects the identity (generation) of the lines it replaces.
///
/// The reference tracks line identity with node pointers: a node that
/// survives an edit keeps its identity, a freed node's identity disappears,
/// and a node that is recreated (by a split, by history or by a paste) gets a
/// fresh one. The Rust buffer models this with the parallel `generations`
/// vector, so every splice has to state which endpoint node survives. The
/// endpoint coordinates alone are not enough: a whole-line cut, a line join
/// over an empty predecessor and a partial multiline cut all end at column
/// zero of the lower line but free different nodes.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Splice {
    /// A plain replacement (an insertion, an in-place edit, a search and
    /// replace). The top node survives; inserted lines are new nodes.
    Plain,
    /// A line join, like the reference's `expunge` at a line break: the top
    /// node survives and absorbs the bottom node's text, and the bottom node
    /// is freed. This is also the reference's spillage join.
    Join,
    /// A cut of a region, like the reference's `extract_segment`: a cut of
    /// whole lines (top x == 0 and bottom x == 0) keeps the bottom node and
    /// detaches the top nodes; any other cut keeps the top node, copies the
    /// bottom suffix into it and detaches the bottom node.
    Cut,
    /// A wholesale replacement of a region (filter output). Every node in
    /// the replaced span is freed and every resulting line is a new node,
    /// like the reference's cut-then-insert pair.
    Replace,
}
#[derive(Clone, Debug, PartialEq)]
pub struct State {
    pub lines: Vec<Vec<u8>>,
    pub pos: Pos,
    pub mark: Option<Pos>,
    pub anchors: Vec<bool>,
    /// Stable identity (generation) for each line, parallel to `lines`.
    /// Models GNU nano's node identity: a line that survives an edit keeps
    /// its generation; a freed line's generation is discarded; a recreated
    /// line (including one recreated by undo/redo) gets a new generation.
    pub generations: Vec<u64>,
    /// The generation of the line created by the previous automatic hard wrap
    /// (nano's `spillage_line`, a live node pointer). A subsequent wrap of the
    /// predecessor joins onto this line only when the line currently at the
    /// successor position carries this exact generation. Storing a generation
    /// instead of a numeric index means that deleting the target (the
    /// generation leaves the buffer) or recreating its text (the new line gets
    /// a fresh generation) invalidates the marker, matching the reference's
    /// `delete_node`/`do_wrap` node-lifetime semantics. See Q-UNDO-002 (R2).
    pub spillage: Option<u64>,
}
#[derive(Clone, Debug)]
pub struct Undo {
    pub before: State,
    pub after: State,
    pub kind: String,
    pub redo_kind: Option<String>,
    /// True for an undo item whose chunks were produced by `hard_wrap`
    /// (SPLIT_BEGIN/SPLIT_END in the reference). The reference clears
    /// `spillage_line` when undoing the wrap (the overflow node is freed) and
    /// does not restore it on redo (redo ENTER creates a new node without
    /// assigning the pointer). `hard_wrap` sets this flag and also records
    /// `None` in both snapshots so that undo/redo of a wrap yield no spillage,
    /// matching the reference's node-lifetime behavior.
    pub is_wrap: bool,
}
#[derive(Debug)]
pub struct Buffer {
    pub state: State,
    pub name: Vec<u8>,
    pub modified: bool,
    pub dos: bool,
    pub preferred: usize,
    pub top: usize,
    /// Width used to interpret the visual-row index in `top` at the last draw.
    pub viewport_width: usize,
    pub firstcol: usize,
    pub brink: usize,
    pub softmark: bool,
    pub history: Vec<Undo>,
    pub hist: usize,
    pub saved: Option<usize>,
    pub last_kind: String,
    pub next_gen: u64,
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
        let next_gen = n as u64 + 1;
        Self {
            state: State {
                lines,
                pos: Pos::default(),
                mark: None,
                anchors: vec![false; n],
                generations: (0..n as u64).collect(),
                spillage: None,
            },
            name,
            modified: false,
            dos: false,
            preferred: 0,
            top: 0,
            viewport_width: 0,
            firstcol: 0,
            brink: 0,
            softmark: false,
            history: Vec::new(),
            hist: 0,
            saved: Some(0),
            last_kind: String::new(),
            next_gen,
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
    #[cfg(not(feature = "tiny"))]
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
            self.state.generations.push(self.next_gen);
            self.next_gen += 1;
        }
        if !nonew && self.state.lines.last().is_some_and(|l| !l.is_empty()) {
            self.state.lines.push(Vec::new());
            self.state.generations.push(self.next_gen);
            self.next_gen += 1;
        }
        self.state.anchors.resize(self.state.lines.len(), false);
        self.state.generations.resize(self.state.lines.len(), {
            let g = self.next_gen;
            self.next_gen += 1;
            g
        });
    }
    pub fn begin(&self) -> State {
        if cfg!(feature = "tiny") {
            return State {
                lines: Vec::new(),
                pos: self.pos(),
                mark: None,
                anchors: Vec::new(),
                generations: Vec::new(),
                spillage: None,
            };
        }
        self.state.clone()
    }
    pub fn finish(&mut self, before: State, kind: &str, group: bool, nonew: bool) {
        self.magic(nonew);
        if cfg!(feature = "tiny") {
            self.modified = true;
            return;
        }
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
                redo_kind: None,
                is_wrap: false,
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
        if cfg!(feature = "tiny") {
            return None;
        }
        let (index, mut state) = if redo {
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
        // The reference's `spillage_line` is a live node pointer set only by
        // `do_wrap` and cleared only in `delete_node` (when that exact node is
        // freed); ordinary undo/redo never assign it. Undoing a JOIN or ENTER
        // recreates text in a *new* node (`intruder`), so it must not inherit
        // the pointer; redo of a wrap re-applies the inner ENTER without
        // assigning the pointer.
        //
        // Model this by keeping `spillage` as a *live* generation (never
        // restored from the snapshot) and giving fresh generations to any line
        // in the restored state whose snapshot generation is no longer live
        // (i.e. the line was freed and is now being recreated). A wrap item
        // forces `None` (undo frees the overflow; redo does not reassign it).
        let live_spillage = self.state.spillage;
        let item_is_wrap = self.history[index].is_wrap;
        let live_gens: std::collections::HashSet<u64> =
            self.state.generations.iter().copied().collect();
        for g in state.generations.iter_mut() {
            if !live_gens.contains(g) {
                *g = self.next_gen;
                self.next_gen += 1;
            }
        }
        self.state = state;
        self.state.spillage = if item_is_wrap { None } else { live_spillage };
        // Drop the marker if its target generation left the buffer (the line
        // was freed by this undo/redo transition).
        if let Some(sg) = self.state.spillage
            && !self.state.generations.contains(&sg)
        {
            self.state.spillage = None;
        }
        self.state.mark = None;
        self.softmark = false;
        self.modified = self.saved != Some(self.hist);
        self.last_kind.clear();
        Some(if redo {
            self.history[index]
                .redo_kind
                .as_ref()
                .unwrap_or(&self.history[index].kind)
                .clone()
        } else {
            self.history[index].kind.clone()
        })
    }
    /// Replace an ordered region with external bytes (LF separators, NUL payload).
    ///
    /// `splice` states which endpoint node survives the replacement; see
    /// [`Splice`]. The coordinates alone cannot decide this: a join over an
    /// empty predecessor, a whole-line cut and a partial multiline cut all
    /// end at column zero of the lower line but free different nodes.
    pub fn replace(&mut self, a: Pos, b: Pos, raw: &[u8], splice: Splice) {
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
        // Capture the endpoint generations before the splice so we can assign
        // the survivor's identity to the resulting line.
        let gen_a = self.state.generations[a.line];
        let gen_b = if b.line > a.line {
            self.state.generations[b.line]
        } else {
            gen_a
        };
        // The node that survives the splice. The reference frees the other
        // endpoint node: a join frees the lower node, a whole-line cut frees
        // the upper nodes and a partial cut frees the lower node.
        let survivor = match splice {
            Splice::Plain | Splice::Join => gen_a,
            Splice::Cut => {
                if a.line == b.line {
                    gen_a
                } else if a.x == 0 && b.x == 0 {
                    // A whole-line cut detaches the top lines and keeps the
                    // bottom node.
                    gen_b
                } else {
                    // A partial cut keeps the top node; the bottom suffix is
                    // copied into it and the bottom node is detached.
                    gen_a
                }
            }
            // Every node in the replaced span is freed by a wholesale
            // replacement, so no endpoint survives.
            Splice::Replace => gen_a,
        };
        self.state.lines.splice(a.line..=b.line, lines);
        // Determine the survivor identity for the resulting lines. The first
        // resulting line keeps the survivor's generation; interior and
        // split-bottom lines are brand-new nodes.
        let mut new_gens: Vec<u64> = Vec::with_capacity(count);
        if splice == Splice::Replace {
            // A wholesale replacement frees every node in the span, so the
            // first resulting line is a new node as well.
            new_gens.push(self.next_gen);
            self.next_gen += 1;
        } else {
            new_gens.push(survivor);
        }
        for _ in 1..count.saturating_sub(1) {
            new_gens.push(self.next_gen);
            self.next_gen += 1;
        }
        if count > 1 {
            match splice {
                // A wholesale replacement frees every node in the span.
                Splice::Replace => {
                    new_gens.push(self.next_gen);
                    self.next_gen += 1;
                }
                // A join never produces more than one line, but a join that
                // is modelled as a plain splice must not resurrect the freed
                // bottom node.
                Splice::Join => {
                    new_gens.push(self.next_gen);
                    self.next_gen += 1;
                }
                Splice::Plain | Splice::Cut => {
                    if b.line > a.line {
                        new_gens.push(gen_b);
                    } else {
                        // a.line == b.line: a split, the bottom part is a new node.
                        new_gens.push(self.next_gen);
                        self.next_gen += 1;
                    }
                }
            }
        }
        self.state.anchors.splice(
            a.line..=b.line,
            std::iter::once(anchor).chain(std::iter::repeat_n(false, count - 1)),
        );
        self.state.generations.splice(a.line..=b.line, new_gens);
        // The spillage marker is a generation. If the line it identified was
        // freed or detached by this splice (its generation is no longer in the
        // buffer), drop the marker; otherwise it survives unchanged (a
        // surviving target that merely shifted index is found by generation).
        if let Some(sg) = self.state.spillage
            && !self.state.generations.contains(&sg)
        {
            self.state.spillage = None;
        }
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
    /// Apply the reference's hard-wrap split of the line at `line` into the
    /// two lines `first` and `second`.
    ///
    /// The reference's `do_enter` keeps the top node and creates a fresh node
    /// for the continuation. When the split follows a spillage join, the
    /// joined bottom node was freed by that join, so the continuation is a
    /// fresh node in its place; otherwise the following lines keep their
    /// identity and shift down by one.
    #[cfg(not(feature = "tiny"))]
    pub fn wrap_split(&mut self, line: usize, first: Vec<u8>, second: Vec<u8>, joined: bool) {
        self.state.lines[line] = first;
        if joined {
            // The join freed the old bottom node: the continuation is a
            // fresh node in its place. The anchor of the freed node moves to
            // the surviving top node, like the reference's `expunge`.
            self.state.anchors[line] |= self.state.anchors[line + 1];
            self.state.anchors[line + 1] = false;
            self.state.lines[line + 1] = second;
            self.state.generations[line + 1] = self.next_gen;
            self.next_gen += 1;
        } else {
            self.state.lines.insert(line + 1, second);
            self.state.generations.insert(line + 1, self.next_gen);
            self.next_gen += 1;
            self.state.anchors.insert(line + 1, false);
        }
        // The spillage marker names a generation. If that node was freed by
        // the join it can no longer be joined onto.
        if let Some(sg) = self.state.spillage
            && !self.state.generations.contains(&sg)
        {
            self.state.spillage = None;
        }
    }
    /// Clear/shift the spillage marker for a splice that replaces the lines in
    /// `[first, end)` with `count` new lines and keeps none of the old lines
    /// (no survivors). Used by `justify` (a rewrap) and the whole-buffer
    /// formatter/speller replacement. Unlike `replace`, the old lines are all
    /// freed, so a marker anywhere in the range is cleared, not retained at an
    /// endpoint. The `count` new lines get fresh generations.
    #[cfg(not(feature = "tiny"))]
    pub fn spillage_no_survivors(&mut self, first: usize, end: usize, count: usize) {
        let mut new_gens: Vec<u64> = Vec::with_capacity(count);
        for _ in 0..count {
            new_gens.push(self.next_gen);
            self.next_gen += 1;
        }
        self.state.generations.splice(first..end, new_gens);
        if let Some(sg) = self.state.spillage
            && !self.state.generations.contains(&sg)
        {
            self.state.spillage = None;
        }
    }
    /// Drop the spillage marker entirely (whole-buffer line replacement) and
    /// assign fresh generations to every current line.
    #[cfg(not(feature = "tiny"))]
    pub fn spillage_clear(&mut self) {
        let n = self.state.lines.len();
        self.state.generations.clear();
        for _ in 0..n {
            self.state.generations.push(self.next_gen);
            self.next_gen += 1;
        }
        self.state.spillage = None;
    }
    pub fn insert(&mut self, raw: &[u8], kind: &str, group: bool, nonew: bool) {
        if raw.is_empty() {
            return;
        }
        let before = self.begin();
        let p = self.pos();
        self.replace(p, p, raw, Splice::Plain);
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
            self.replace(Pos { line: p.line, x: 0 }, p, b"", Splice::Plain);
        }
        let p = self.pos();
        let mut raw = vec![b'\n'];
        raw.extend(indent);
        self.replace(p, p, &raw, Splice::Plain);
        self.finish(before, "line break", false, nonew);
    }
    pub fn delete(&mut self, e: Encoding, back: bool, nonew: bool, zap: bool) -> bool {
        if zap
            && let Some((a, b)) = self.region()
            && a != b
        {
            let before = self.begin();
            self.replace(a, b, b"", Splice::Cut);
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
                let modified = self.modified;
                self.finish(before, kind, false, nonew);
                self.modified = if cfg!(feature = "tiny") {
                    modified
                } else {
                    self.saved != Some(self.hist - 1)
                };
                return true;
            }
            return false;
        }
        // A deletion inside a line keeps the node; a deletion of a line break
        // joins the two lines and frees the lower node, like the reference's
        // `expunge`.
        let splice = if a.line == b.line {
            Splice::Plain
        } else {
            Splice::Join
        };
        self.replace(a, b, b"", splice);
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
        self.replace(a, b, b"", Splice::Cut);
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
    #[cfg(not(feature = "tiny"))]
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
    #[cfg(not(feature = "tiny"))]
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
    #[cfg(feature = "tiny")]
    fn tiny_edits_do_not_retain_buffer_snapshots() {
        let mut b = Buffer::new(vec![], vec![vec![b'x'; 1 << 20], vec![]]);
        for _ in 0..128 {
            b.insert(b"a", "addition", false, false);
        }
        assert!(b.modified);
        assert_eq!(b.raw().len(), (1 << 20) + 129);
        assert!(b.history.is_empty());
        assert_eq!(b.history.capacity(), 0);
        assert!(b.begin().lines.is_empty());
        b.saved();
        assert!(!b.modified);
        b.insert(b"z", "addition", false, false);
        assert!(b.modified);
        assert!(b.undo(false).is_none());
    }
    #[test]
    fn region_splice() {
        let mut b = Buffer::new(vec![], vec![b"abc".to_vec(), b"def".to_vec(), vec![]]);
        b.replace(
            Pos { line: 0, x: 1 },
            Pos { line: 1, x: 2 },
            b"X\nY",
            Splice::Plain,
        );
        assert_eq!(b.raw(), b"aX\nYf\n");
        assert_eq!(b.pos(), Pos { line: 1, x: 1 });
    }
    /// A spillage join builds the joined line from internally encoded line
    /// bytes (where byte 10 stands for a payload NUL) and must hand
    /// `Buffer::replace` *external* bytes (LF separators, NUL payload). The
    /// join path in `hard_wrap` converts the internal vector back to
    /// external bytes with `decode_nuls` before calling `replace`; this test
    /// exercises that round trip so a payload NUL is not reinterpreted as a
    /// line separator (F2).
    #[test]
    #[cfg(not(feature = "tiny"))]
    fn spillage_join_preserves_embedded_nul() {
        let mut b = Buffer::new(
            vec![],
            vec![
                b"aaaa bbbb cccc".to_vec(),
                vec![0x0a, b'd', b'd', b'd', b'd'],
                vec![],
            ],
        );
        b.state.spillage = Some(b.state.generations[1]);
        // Simulate the spillage join: the current line plus a space plus the
        // next line (which carries a payload NUL as internal byte 0x0a).
        let joined: Vec<u8> = [
            b.state.lines[0].as_slice(),
            b" ",
            b.state.lines[1].as_slice(),
        ]
        .concat();
        // The fix feeds `decode_nuls(&joined)` (external bytes: NUL 0x0a ->
        // 0x00) to `replace`, which splits on LF only and then re-encodes
        // NULs. Without `decode_nuls` the 0x0a payload NUL would be read as a
        // line separator and the buffer would gain a spurious extra line.
        let external = bytes::decode_nuls(&joined);
        b.replace(
            Pos { line: 0, x: 0 },
            Pos { line: 1, x: 5 },
            &external,
            Splice::Join,
        );
        assert_eq!(b.state.lines.len(), 2);
        assert_eq!(b.state.lines[0], b"aaaa bbbb cccc \x0adddd");
        assert_eq!(b.state.lines[1], b"");
    }
    /// The identity invariants that the hard-wrap spillage marker depends on.
    ///
    /// The reference frees a node when it is eaten by a join or detached by a
    /// cut, and keeps the identity of a node that survives. The endpoints of
    /// a splice are not enough to decide this: a join over an empty
    /// predecessor, a whole-line cut and a partial multiline cut all end at
    /// column zero of the lower line but free different nodes.
    #[test]
    #[cfg(not(feature = "tiny"))]
    fn splice_identity_follows_the_operation() {
        let e = Encoding { utf8: true, tab: 8 };
        // A join over an empty predecessor keeps the top node and frees the
        // bottom node, so a spillage marker on the bottom node is dropped.
        let mut b = Buffer::new(vec![], vec![Vec::new(), b"ddd".to_vec(), b"TAIL".to_vec()]);
        let top = b.state.generations[0];
        let bottom = b.state.generations[1];
        b.state.spillage = Some(bottom);
        b.state.pos = Pos { line: 0, x: 0 };
        b.delete(e, false, false, false);
        assert_eq!(b.raw(), b"ddd\nTAIL\n");
        assert_eq!(b.state.generations[0], top);
        assert!(!b.state.generations.contains(&bottom));
        assert_eq!(b.state.spillage, None);

        // A whole-line cut keeps the bottom node and detaches the top node.
        let mut b = Buffer::new(vec![], vec![b"top".to_vec(), b"bottom".to_vec()]);
        let top = b.state.generations[0];
        let bottom = b.state.generations[1];
        let raw = b.cut(
            Pos { line: 0, x: 0 },
            Pos { line: 1, x: 0 },
            "cut",
            false,
            false,
        );
        assert_eq!(raw, b"top\n");
        assert_eq!(b.raw(), b"bottom\n");
        assert_eq!(b.state.generations[0], bottom);
        assert!(!b.state.generations.contains(&top));

        // A partial multiline cut keeps the top node and detaches the bottom
        // node, even though the cut starts at column zero.
        let mut b = Buffer::new(vec![], vec![b"top".to_vec(), b"bottom".to_vec()]);
        let top = b.state.generations[0];
        let bottom = b.state.generations[1];
        b.cut(
            Pos { line: 0, x: 0 },
            Pos { line: 1, x: 3 },
            "cut",
            false,
            false,
        );
        assert_eq!(b.raw(), b"tom\n");
        assert_eq!(b.state.generations[0], top);
        assert!(!b.state.generations.contains(&bottom));

        // A split keeps the top node and creates a fresh node below it.
        let mut b = Buffer::new(vec![], vec![b"abcd".to_vec()]);
        let top = b.state.generations[0];
        b.state.pos = Pos { line: 0, x: 2 };
        b.enter(e, false, false);
        assert_eq!(b.raw(), b"ab\ncd\n");
        assert_eq!(b.state.generations[0], top);
        assert_ne!(b.state.generations[1], top);
    }
    /// Every line keeps a distinct identity and the identity vector stays
    /// parallel to the line vector through the editing operations.
    #[test]
    #[cfg(not(feature = "tiny"))]
    fn generations_stay_parallel_and_unique() {
        let e = Encoding { utf8: true, tab: 8 };
        let mut b = Buffer::new(
            vec![],
            vec![b"one".to_vec(), b"two".to_vec(), b"three".to_vec()],
        );
        let check = |b: &Buffer| {
            assert_eq!(b.state.lines.len(), b.state.generations.len());
            assert_eq!(b.state.lines.len(), b.state.anchors.len());
            let mut seen = std::collections::HashSet::new();
            for g in &b.state.generations {
                assert!(seen.insert(*g), "duplicate generation {g}");
            }
        };
        check(&b);
        b.state.pos = Pos { line: 0, x: 3 };
        b.delete(e, false, false, false);
        check(&b);
        b.state.pos = Pos { line: 0, x: 0 };
        b.delete(e, false, false, false);
        check(&b);
        b.state.pos = Pos { line: 0, x: 1 };
        b.enter(e, false, false);
        check(&b);
        b.cut(
            Pos { line: 0, x: 0 },
            Pos { line: 1, x: 0 },
            "cut",
            false,
            false,
        );
        check(&b);
        b.insert(b"x\ny\n", "addition", false, false);
        check(&b);
    }
}
