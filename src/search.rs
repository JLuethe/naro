//! POSIX search, interactive replace and bracket matching.
use crate::native;
use crate::{
    buffer::{Pos, Splice},
    bytes,
    config::Config,
    editor::*,
    generated::*,
    native::Regex,
};
pub fn literal(
    c: &Config,
    hay: &[u8],
    needle: &[u8],
    start: usize,
    case: bool,
) -> Option<(usize, usize)> {
    literal_checked(c, hay, needle, start, case, &mut || Ok(()))
        .ok()
        .flatten()
}
fn literal_checked(
    c: &Config,
    hay: &[u8],
    needle: &[u8],
    start: usize,
    case: bool,
    check: &mut impl FnMut() -> Result<(), ()>,
) -> Result<Option<(usize, usize)>, ()> {
    if start > hay.len() {
        return Ok(None);
    }
    if needle.is_empty() {
        return Ok(Some((start, start)));
    }
    let e = c.enc();
    let mut i = start;
    while i <= hay.len() {
        check()?;
        if case {
            if hay[i..].starts_with(needle) {
                return Ok(Some((i, i + needle.len())));
            }
        } else {
            let (mut x, mut n) = (i, 0);
            while x < hay.len() && n < needle.len() {
                check()?;
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
                return Ok(Some((i, x)));
            }
        }
        if i == hay.len() {
            break;
        }
        i = e.right(hay, i);
    }
    Ok(None)
}
/// Preserve non-cancelled input; discard the pending burst after Cancel.
struct SearchPoll {
    steps: usize,
    checked: std::time::Instant,
    cancel_keys: Vec<i32>,
    decoded: Option<crate::input::Input>,
    observed_raw: usize,
}
impl SearchPoll {
    const BURST_LIMIT: usize = 16_384;

    fn discard_cancelled_input(input: &mut crate::input::Input) {
        // nano discards the rest of the pending input burst when a search is
        // cancelled.  The first key may already be in Input::queue; further
        // keys may still be waiting in ncurses' nonblocking input buffer.
        input.queue.clear();
        input.replay.clear();
        #[cfg(not(test))]
        while unsafe { native::nr_get(0) } >= 0 {}
    }

    fn new(conf: &Config) -> Self {
        // Use the first effective binding in the search menu, as normal key
        // dispatch does.  In particular, an rc unbind can remove ^C and a
        // later bind can make another control key Cancel.
        let mut first = std::collections::HashMap::new();
        for binding in &conf.keys {
            if binding.menus & SEARCH != 0 {
                first
                    .entry(binding.key)
                    .or_insert(binding.func == "do_cancel");
            }
        }
        Self {
            steps: 0,
            checked: std::time::Instant::now(),
            cancel_keys: first
                .into_iter()
                .filter_map(|(key, cancel)| cancel.then_some(key))
                .collect(),
            decoded: None,
            observed_raw: 0,
        }
    }
    fn buffered_cancel(&mut self, input: &crate::input::Input, conf: &Config) -> bool {
        let reset = self.decoded.is_none() || input.queue.len() < self.observed_raw;
        if reset {
            self.decoded = None;
        }
        let decoded = self.decoded.get_or_insert_with(|| input.clone());
        if !reset {
            decoded
                .queue
                .extend(input.queue.range(self.observed_raw..).copied());
        }
        self.observed_raw = input.queue.len();
        for _ in 0..Self::BURST_LIMIT {
            let key = match decoded.next_buffered(conf) {
                crate::input::Event::Key(key) => key,
                crate::input::Event::Signal(_) => continue,
                crate::input::Event::Idle => break,
            };
            if key.command.as_deref() == Some("do_cancel") {
                return true;
            }
            if (!key.meta && (32..=255).contains(&key.code)) || (key.meta && key.code < 32) {
                continue;
            }
            if self.cancel_keys.contains(&key.code) {
                return true;
            }
        }
        false
    }
    fn check(&mut self, input: &mut crate::input::Input, conf: &Config) -> Result<(), ()> {
        self.steps += 1;
        if self.steps != 1 && !self.steps.is_multiple_of(1024) {
            return Ok(());
        }
        if native::signal_pending() {
            return Err(());
        }
        if self.buffered_cancel(input, conf) {
            Self::discard_cancelled_input(input);
            return Err(());
        }
        if self.checked.elapsed() < std::time::Duration::from_millis(50) {
            return Ok(());
        }
        self.checked = std::time::Instant::now();
        #[cfg(not(test))]
        for _ in 0..Self::BURST_LIMIT {
            let key = unsafe { native::nr_get(0) };
            if key < 0 {
                break;
            }
            input.queue.push_back(key);
        }
        if self.buffered_cancel(input, conf) {
            Self::discard_cancelled_input(input);
            return Err(());
        }
        Ok(())
    }
}

#[cfg(test)]
#[test]
fn search_poll_preserves_non_cancelled_queued_input() {
    let conf = Config::new(false);
    let mut input = crate::input::Input::default();
    input.queue.extend([b'X' as i32, b'Y' as i32]);
    let mut poll = SearchPoll::new(&conf);
    assert!(poll.check(&mut input, &conf).is_ok());
    assert_eq!(
        input.queue.iter().copied().collect::<Vec<_>>(),
        vec![88, 89]
    );
}

#[cfg(test)]
#[test]
fn search_poll_discards_queued_remainder_after_cancel() {
    let conf = Config::new(false);
    let mut input = crate::input::Input::default();
    input.queue.extend([3, b'X' as i32]);
    let mut poll = SearchPoll::new(&conf);
    assert!(poll.check(&mut input, &conf).is_err());
    assert!(input.queue.is_empty());
}

#[cfg(test)]
#[test]
fn search_poll_obeys_rebound_cancel_and_unbound_control_c() {
    let mut conf = Config::new(false);
    for binding in &mut conf.keys {
        if binding.key == 3 {
            binding.menus &= !SEARCH;
        }
    }
    conf.keys.insert(
        0,
        Binding {
            key: 7,
            menus: SEARCH,
            func: "do_cancel".into(),
            tag: "^G".into(),
            toggle: 0,
            expansion: None,
        },
    );
    let mut poll = SearchPoll::new(&conf);
    let mut input = crate::input::Input::default();
    input.queue.extend([3, b'X' as i32]);
    assert!(poll.check(&mut input, &conf).is_ok());
    assert_eq!(input.queue.iter().copied().collect::<Vec<_>>(), vec![3, 88]);
    input.queue.clear();
    input.queue.extend([7, b'Y' as i32]);
    let mut poll = SearchPoll::new(&conf);
    assert!(poll.check(&mut input, &conf).is_err());
    assert!(input.queue.is_empty());
}

#[cfg(test)]
#[test]
fn search_poll_decodes_meta_binding_without_consuming_other_keys() {
    let mut conf = Config::new(false);
    conf.keys.insert(
        0,
        Binding {
            key: b'g' as i32,
            menus: SEARCH,
            func: "do_cancel".into(),
            tag: "M-G".into(),
            toggle: 0,
            expansion: None,
        },
    );
    let mut poll = SearchPoll::new(&conf);
    let mut input = crate::input::Input::default();
    input.queue.extend([b'g' as i32, b'X' as i32]);
    assert!(poll.check(&mut input, &conf).is_ok());
    assert_eq!(
        input.queue.iter().copied().collect::<Vec<_>>(),
        vec![103, 88]
    );
    input.queue.clear();
    input.queue.push_back(27);
    poll.steps = 0;
    assert!(poll.check(&mut input, &conf).is_ok());
    assert_eq!(input.queue.iter().copied().collect::<Vec<_>>(), vec![27]);
    input.queue.extend([b'g' as i32, b'X' as i32]);
    poll.steps = 0;
    assert!(poll.check(&mut input, &conf).is_err());
    assert!(input.queue.is_empty());
}

#[cfg(test)]
#[test]
fn search_poll_reaches_cancel_behind_large_retained_burst() {
    let conf = Config::new(false);
    let mut input = crate::input::Input::default();
    input.queue.extend(std::iter::repeat_n(b'g' as i32, 8192));
    let mut poll = SearchPoll::new(&conf);
    assert!(poll.check(&mut input, &conf).is_ok());
    assert_eq!(poll.observed_raw, 8192);
    assert!(poll.decoded.as_ref().unwrap().queue.is_empty());
    poll.steps = 0;
    assert!(poll.check(&mut input, &conf).is_ok());
    assert_eq!(input.queue.len(), 8192);
    input.queue.extend([3, b'X' as i32]);
    poll.steps = 0;
    assert!(poll.check(&mut input, &conf).is_err());
    assert!(input.queue.is_empty());
}
#[derive(Debug)]
struct Pattern {
    needle: Vec<u8>,
    regex: Option<Regex>,
}
impl Pattern {
    fn new(c: &Config, needle: &[u8]) -> Result<Self, String> {
        Ok(Self {
            needle: needle.to_vec(),
            regex: if c.on(USE_REGEXP) {
                Some(Regex::new(needle, !c.on(CASE_SENSITIVE))?)
            } else {
                None
            },
        })
    }
    fn find(
        &self,
        c: &Config,
        terminated: &[u8],
        from: usize,
        poll: &mut SearchPoll,
        input: &mut crate::input::Input,
    ) -> Result<Option<Vec<(usize, usize)>>, ()> {
        poll.check(input, c)?;
        let text = &terminated[..terminated.len() - 1];
        if from > text.len() {
            return Ok(None);
        }
        let found = if let Some(re) = &self.regex {
            re.find_terminated(terminated, from, false)
        } else {
            literal_checked(
                c,
                text,
                &self.needle,
                from,
                c.on(CASE_SENSITIVE),
                &mut || poll.check(input, c),
            )?
            .map(|m| vec![m])
        };
        poll.check(input, c)?;
        Ok(found)
    }
}

#[derive(Debug)]
struct LineGrowth(Vec<usize>);
impl LineGrowth {
    fn new(n: usize) -> Self {
        Self(vec![0; n + 1])
    }
    fn add(&mut self, mut index: usize, amount: usize) {
        index += 1;
        while index < self.0.len() {
            self.0[index] += amount;
            index += index.isolate_lowest_one();
        }
    }
    fn before(&self, mut index: usize) -> usize {
        let mut sum = 0;
        while index > 0 {
            sum += self.0[index];
            index &= index - 1;
        }
        sum
    }
    fn at(&self, index: usize) -> usize {
        self.before(index + 1) - self.before(index)
    }
}
struct LineGroup {
    raw: Vec<u8>,
    metadata: Vec<(bool, u64)>,
}
struct GroupBuilder {
    raw: Vec<u8>,
    metadata: Vec<(bool, u64)>,
    source_line: usize,
    x: usize,
}
impl GroupBuilder {
    fn new(source: &LineGroup) -> Self {
        Self {
            raw: Vec::with_capacity(source.raw.len()),
            metadata: vec![source.metadata[0]],
            source_line: 0,
            x: 0,
        }
    }
    fn source(&mut self, source: &LineGroup, start: usize, end: usize) {
        self.raw.extend_from_slice(&source.raw[start..end]);
        for byte in &source.raw[start..end] {
            if *byte == b'\n' {
                self.source_line += 1;
                self.metadata.push(source.metadata[self.source_line]);
                self.x = 0;
            } else {
                self.x += 1;
            }
        }
    }
    fn added(&mut self, raw: &[u8], generations: &[u64]) {
        self.raw.extend_from_slice(raw);
        let mut gens = generations.iter();
        for byte in raw {
            if *byte == b'\n' {
                self.metadata.push((false, *gens.next().unwrap()));
                self.x = 0;
            } else {
                self.x += 1;
            }
        }
    }
    fn finish(self) -> LineGroup {
        LineGroup {
            raw: self.raw,
            metadata: self.metadata,
        }
    }
}

/// Traverses an immutable input snapshot, never inserted text. Forward scans
/// retain one match; reverse scans retain only spans for their current line.
#[derive(Debug)]
pub struct Replacement {
    source: Vec<Vec<u8>>,
    pattern: Pattern,
    offsets: Vec<usize>,
    line_deltas: Vec<isize>,
    line_growth: LineGrowth,
    phase: usize,
    line: usize,
    from: usize,
    skipone: bool,
    back: bool,
    backward_spans: Vec<(usize, usize)>,
    backward_ready: bool,
    line_skipone: Vec<bool>,
    region: Option<(Pos, Pos)>,
    pivot: Pos,
    current: Option<Match>,
    current_delta: isize,
    group: Option<(usize, usize)>,
    whole_word: bool,
    pub replacement: Vec<u8>,
    pub count: usize,
    pub original: Pos,
    pub top: usize,
    pub mark: Option<Pos>,
}
impl Replacement {
    fn new(
        editor: &mut Editor,
        replacement: Vec<u8>,
        poll: &mut SearchPoll,
    ) -> Result<Self, String> {
        let pattern = Pattern::new(&editor.conf, &editor.search)?;
        let source: Vec<Vec<u8>> = editor
            .b()
            .state
            .lines
            .iter()
            .map(|s| {
                let mut line = s.clone();
                line.push(0);
                line
            })
            .collect();
        let mut offset = 0;
        let offsets = source
            .iter()
            .map(|s| {
                let start = offset;
                offset += s.len();
                start
            })
            .collect();
        let original = editor
            .spelling
            .as_ref()
            .map(|s| s.original)
            .unwrap_or(editor.b().pos());
        let region = if let Some((lo, hi)) = editor.spelling.as_ref().and_then(|s| s.region) {
            Some((
                editor.b().position_at_offset(lo),
                editor.b().position_at_offset(hi),
            ))
        } else {
            editor.b().region()
        };
        let n = source.len();
        let back = editor.conf.on(BACKWARDS_SEARCH);
        let mut r = Self {
            source,
            pattern,
            offsets,
            line_deltas: vec![0; n],
            line_growth: LineGrowth::new(n),
            phase: 0,
            line: if back { n - 1 } else { 0 },
            from: 0,
            skipone: false,
            back,
            backward_spans: Vec::new(),
            backward_ready: false,
            line_skipone: vec![false; n],
            region,
            pivot: original,
            current: None,
            current_delta: 0,
            group: None,
            whole_word: editor.spelling.is_some(),
            replacement,
            count: 0,
            original,
            top: editor.b().top,
            mark: editor.b().state.mark,
        };
        if back {
            let mut skip = false;
            for line in 0..n {
                r.line_skipone[line] = skip;
                let mut from = 0;
                while let Some(groups) = r
                    .pattern
                    .find(&editor.conf, &r.source[line], from, poll, &mut editor.input)
                    .map_err(|_| "Cancelled".to_owned())?
                {
                    let (a, b) = groups[0];
                    let Some(next) = replacement_next(
                        &editor.conf,
                        &r.source[line][..r.source[line].len() - 1],
                        a,
                        b,
                        &mut skip,
                    ) else {
                        break;
                    };
                    from = next;
                }
            }
        }
        Ok(r)
    }
    fn next_line(&mut self) {
        self.from = 0;
        self.backward_ready = false;
        if (!self.back && self.line + 1 == self.source.len()) || (self.back && self.line == 0) {
            self.phase += 1;
            self.line = if self.back { self.source.len() - 1 } else { 0 };
            self.skipone = false;
        } else if self.back {
            self.line -= 1;
        } else {
            self.line += 1;
        }
    }
    fn accepts(&self, a: Pos, b: Pos, c: &Config) -> bool {
        if let Some((lo, hi)) = self.region {
            if a < lo || b > hi {
                return false;
            }
        } else if (a >= self.pivot) != (self.phase == usize::from(self.back)) {
            return false;
        }
        if self.whole_word {
            let s = &self.source[a.line][..self.source[a.line].len() - 1];
            let e = c.enc();
            if (a.x > 0 && e.word(s, e.left(s, a.x), false, &[]))
                || (b.x < s.len() && e.word(s, b.x, false, &[]))
            {
                return false;
            }
        }
        true
    }
    fn advance(
        &mut self,
        c: &Config,
        input: &mut crate::input::Input,
        poll: &mut SearchPoll,
    ) -> Result<bool, ()> {
        self.current = None;
        while self.phase < if self.region.is_some() { 1 } else { 2 } {
            poll.check(input, c)?;
            let line = self.line;
            let len = self.source[line].len() - 1;
            if line + 1 == self.source.len() && len == 0 {
                self.next_line();
                continue;
            }
            let groups = if self.back {
                if !self.backward_ready {
                    self.backward_spans.clear();
                    let mut from = 0;
                    let mut skip = self.line_skipone[line];
                    while let Some(g) =
                        self.pattern
                            .find(c, &self.source[line], from, poll, input)?
                    {
                        let (a, b) = g[0];
                        self.backward_spans.push((a, b));
                        let Some(next) =
                            replacement_next(c, &self.source[line][..len], a, b, &mut skip)
                        else {
                            break;
                        };
                        from = next;
                    }
                    self.backward_ready = true;
                }
                let Some((a, _)) = self.backward_spans.pop() else {
                    self.next_line();
                    continue;
                };
                self.pattern
                    .find(c, &self.source[line], a, poll, input)?
                    .unwrap()
            } else {
                let Some(groups) =
                    self.pattern
                        .find(c, &self.source[line], self.from, poll, input)?
                else {
                    self.next_line();
                    continue;
                };
                let (a, b) = groups[0];
                self.from = replacement_next(c, &self.source[line][..len], a, b, &mut self.skipone)
                    .unwrap_or(len + 1);
                groups
            };
            let (x, y) = groups[0];
            let (a, b) = (Pos { line, x }, Pos { line, x: y });
            if !self.accepts(a, b, c) {
                continue;
            }
            let group = (self.phase, line);
            if self.group != Some(group) {
                self.current_delta = if self.back && self.phase == 1 {
                    self.line_deltas[line]
                } else {
                    0
                };
                self.group = Some(group);
            }
            self.current = Some((a, b, groups));
            return Ok(true);
        }
        Ok(false)
    }
    fn live_match(&self, buffer: &crate::buffer::Buffer) -> (Pos, Pos) {
        let (a, b, _) = self.current.as_ref().unwrap();
        if buffer.state.lines.len() == self.source.len() {
            return (
                Pos {
                    line: a.line,
                    x: a.x.saturating_add_signed(self.current_delta),
                },
                Pos {
                    line: b.line,
                    x: b.x.saturating_add_signed(self.current_delta),
                },
            );
        }
        let prefix: isize = self.line_deltas[..a.line].iter().sum();
        let start = (self.offsets[a.line] + a.x).saturating_add_signed(prefix + self.current_delta);
        let end = start + b.x - a.x;
        (
            buffer.position_at_offset(start),
            buffer.position_at_offset(end),
        )
    }
    fn raw(&self) -> Vec<u8> {
        let (a, _, groups) = self.current.as_ref().unwrap();
        expand_replacement(
            &self.replacement,
            self.pattern.regex.is_some(),
            groups,
            &self.source[a.line],
        )
    }
    fn changed(&mut self, a: Pos, b: Pos, raw: &[u8]) {
        let source_line = self.current.as_ref().unwrap().0.line;
        let delta = raw.len() as isize - (b.x - a.x) as isize;
        self.line_deltas[source_line] += delta;
        self.line_growth
            .add(source_line, raw.iter().filter(|b| **b == b'\n').count());
        if !self.back {
            self.current_delta += delta;
        }
        adjust_position(&mut self.original, a, b, raw, false);
        if let Some(mark) = &mut self.mark {
            adjust_position(mark, a, b, raw, true);
        }
        self.count += 1;
    }
}
fn replacement_next(c: &Config, s: &[u8], a: usize, b: usize, skipone: &mut bool) -> Option<usize> {
    if b > a {
        if b >= s.len() {
            return None;
        }
        Some(if *skipone { c.enc().right(s, b) } else { b })
    } else {
        if a >= s.len() {
            return None;
        }
        *skipone = true;
        Some(c.enc().right(s, a))
    }
}
fn expand_replacement(
    replacement: &[u8],
    regex: bool,
    groups: &[(usize, usize)],
    line: &[u8],
) -> Vec<u8> {
    let mut raw = Vec::new();
    let mut i = 0;
    while i < replacement.len() {
        if regex
            && replacement[i] == b'\\'
            && i + 1 < replacement.len()
            && (b'1'..=b'9').contains(&replacement[i + 1])
        {
            let n = (replacement[i + 1] - b'0') as usize;
            if n < groups.len() {
                let (a, b) = groups[n];
                if a != usize::MAX && b <= line.len() {
                    raw.extend(bytes::decode_nuls(&line[a..b]));
                }
                i += 2;
                continue;
            }
        }
        raw.push(replacement[i]);
        i += 1;
    }
    raw
}
fn adjust_position(p: &mut Pos, a: Pos, b: Pos, raw: &[u8], inclusive: bool) {
    let extra = raw.iter().filter(|c| **c == b'\n').count();
    if p.line > a.line {
        p.line += extra;
    } else if p.line == a.line && (p.x > a.x || inclusive && p.x == a.x) && p.x >= b.x {
        if extra == 0 {
            p.x =
                p.x.saturating_add_signed(raw.len() as isize - (b.x - a.x) as isize);
        } else {
            p.line += extra;
            p.x = p.x - b.x + raw.rsplit(|c| *c == b'\n').next().unwrap().len();
        }
    }
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
    /// Search one half of a circular traversal, retaining just one candidate.
    fn scan_find(
        &mut self,
        pattern: &Pattern,
        p: Pos,
        back: bool,
        startup: bool,
        wrapped: bool,
        poll: &mut SearchPoll,
    ) -> Result<Option<Match>, ()> {
        let n = self.b().state.lines.len();
        for index in 0..n {
            let line = if back { n - 1 - index } else { index };
            if !wrapped && ((!back && line < p.line) || (back && line > p.line)) {
                continue;
            }
            if wrapped && ((!back && line > p.line) || (back && line < p.line)) {
                continue;
            }
            poll.check(&mut self.input, &self.conf)?;
            let s = &self.b().state.lines[line];
            if line + 1 == n && s.is_empty() {
                continue;
            }
            let mut terminated = s.clone();
            terminated.push(0);
            let len = terminated.len() - 1;
            let mut from = if !back && !wrapped && line == p.line {
                if startup {
                    p.x
                } else if p.x < len {
                    self.conf.enc().right(&terminated[..len], p.x)
                } else {
                    len + 1
                }
            } else {
                0
            };
            let mut candidate = None;
            while let Some(groups) =
                pattern.find(&self.conf, &terminated, from, poll, &mut self.input)?
            {
                let (x, y) = groups[0];
                let a = Pos { line, x };
                let b = Pos { line, x: y };
                let accept = if wrapped {
                    if back { a >= p } else { a <= p }
                } else if back {
                    if startup { a <= p } else { a < p }
                } else if startup {
                    a >= p
                } else {
                    a > p
                };
                if accept {
                    if !back {
                        return Ok(Some((a, b, groups)));
                    }
                    candidate = Some((a, b, groups));
                } else if (!back && wrapped) || (back && !wrapped) {
                    break;
                }
                if x >= len {
                    break;
                }
                from = self.conf.enc().right(&terminated[..len], x);
            }
            if candidate.is_some() {
                return Ok(candidate);
            }
        }
        Ok(None)
    }
    #[cfg(not(feature = "tiny"))]
    pub(crate) fn first_spell_match(
        &mut self,
        region: Option<(usize, usize)>,
        wordchars: &[u8],
    ) -> Option<Match> {
        let pattern = Pattern::new(&self.conf, &self.search).ok()?;
        let mut poll = SearchPoll::new(&self.conf);
        let mut offset = 0;
        for line in 0..self.b().state.lines.len() {
            let mut text = self.b().state.lines[line].clone();
            let len = text.len();
            text.push(0);
            let mut from = 0;
            while let Some(groups) = pattern
                .find(&self.conf, &text, from, &mut poll, &mut self.input)
                .ok()?
            {
                let (a, b) = groups[0];
                let e = self.conf.enc();
                if region.is_none_or(|(lo, hi)| offset + a >= lo && offset + b <= hi)
                    && (a == 0 || !e.word(&text[..len], e.left(&text[..len], a), false, wordchars))
                    && (b == len || !e.word(&text[..len], b, false, wordchars))
                {
                    return Some((Pos { line, x: a }, Pos { line, x: b }, groups));
                }
                if a >= len {
                    break;
                }
                from = e.right(&text[..len], a);
            }
            offset += len + 1;
        }
        None
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
        let Ok(pattern) = Pattern::new(&self.conf, &self.search) else {
            return;
        };
        let p = self.b().pos();
        let back = self.conf.on(BACKWARDS_SEARCH);
        let mut poll = SearchPoll::new(&self.conf);
        let first = self.scan_find(&pattern, p, back, startup, false, &mut poll);
        let wrapped = matches!(first, Ok(None));
        let picked = match first {
            Ok(None) => self.scan_find(&pattern, p, back, startup, true, &mut poll),
            other => other,
        };
        let picked = match picked {
            Ok(m) => m,
            Err(()) => {
                self.cancelled();
                return;
            }
        };
        if let Some((a, b, _)) = picked {
            self.bm().state.pos = a;
            self.preferred();
            let l = crate::render::layout(self);
            let row = self.cursor_row();
            if startup || row < self.b().top || row >= self.b().top + l.edit_rows {
                self.center();
            }
            if !cfg!(feature = "tiny") {
                self.spotlight = Some((a.line, a.x, b.x));
                self.spotlight_time = std::time::Instant::now();
            }
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
            self.search_not_found();
        }
    }
    fn search_not_found(&mut self) {
        let max = unsafe { native::nr_cols() }.max(1) as usize / 2;
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
    pub fn start_replace(&mut self, replacement: Vec<u8>) {
        let mut poll = SearchPoll::new(&self.conf);
        let mut r = match Replacement::new(self, replacement, &mut poll) {
            Ok(r) => r,
            Err(e) => {
                self.msg(e, 5);
                return;
            }
        };
        match r.advance(&self.conf, &mut self.input, &mut poll) {
            Ok(true) => {}
            Ok(false) => {
                self.search_not_found();
                return;
            }
            Err(()) => {
                self.cancelled();
                return;
            }
        }
        self.bm().state.mark = None;
        self.replacement = Some(r);
        self.show_replacement();
    }
    fn show_replacement(&mut self) {
        let Some(r) = &self.replacement else {
            return;
        };
        if r.current.is_none() {
            self.finish_replace();
            return;
        }
        let (a, b) = r.live_match(self.b());
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
    fn replacement_changed(&mut self, r: &mut Replacement, a: Pos, b: Pos, raw: &[u8]) {
        if let Some(session) = self.spelling.as_mut()
            && let Some((_, ref mut end)) = session.region
        {
            *end = end.saturating_add_signed(raw.len() as isize - (b.x - a.x) as isize);
        }
        r.changed(a, b, raw);
        if let Some(session) = self.spelling.as_mut() {
            session.original = r.original;
        }
    }
    /// Build a line in traversal order; journal each occurrence without moving
    /// its untouched suffix. Reverse traversal reverses bytes twice, so UTF-8
    /// and invalid byte sequences are both preserved exactly.
    fn replace_line_all(&mut self, r: &mut Replacement, poll: &mut SearchPoll) -> Result<(), ()> {
        let group = r.group;
        let (first, _) = r.live_match(self.b());
        let source = self.b().state.lines[first.line].clone();
        let base = r.current_delta;
        let mut output = Vec::with_capacity(source.len());
        let mut copied = if r.back { source.len() } else { 0 };
        let mut result = Ok(());
        loop {
            let (a, b) = r.live_match(self.b());
            let raw = r.raw();
            // LF requires Buffer's multiline splice, handled by the caller.
            if raw.contains(&b'\n') {
                break;
            }
            let original = r.current.as_ref().unwrap();
            let x = original.0.x.saturating_add_signed(base);
            let y = original.1.x.saturating_add_signed(base);
            if r.back {
                output.extend(source[y..copied].iter().rev());
                output.extend(bytes::encode_nuls(&raw).into_iter().rev());
                copied = x;
            } else {
                output.extend_from_slice(&source[copied..x]);
                output.extend(bytes::encode_nuls(&raw));
                copied = y;
            }
            let removed = bytes::decode_nuls(&source[x..y]);
            self.bm().record_replacement(a, b, &removed, &raw);
            self.replacement_changed(r, a, b, &raw);
            match r.advance(&self.conf, &mut self.input, poll) {
                Ok(true) if r.group == group => {}
                Ok(_) => break,
                Err(()) => {
                    result = Err(());
                    break;
                }
            }
        }
        if r.back {
            output.extend(source[..copied].iter().rev());
            output.reverse();
        } else {
            output.extend_from_slice(&source[copied..]);
        }
        self.bm().state.lines[first.line] = output;
        result
    }
    /// Multiline All keeps output grouped by original source line until the
    /// traversal finishes, avoiding a line-table splice for each newline.
    fn replace_multiline_all(&mut self, r: &mut Replacement, poll: &mut SearchPoll) {
        let mut groups = Vec::with_capacity(r.source.len());
        let mut live = 0;
        for line in 0..r.source.len() {
            let n = 1 + r.line_growth.at(line);
            let mut raw = Vec::new();
            let mut metadata = Vec::with_capacity(n);
            for current in live..live + n {
                if current > live {
                    raw.push(b'\n');
                }
                raw.extend(bytes::decode_nuls(&self.b().state.lines[current]));
                metadata.push((
                    self.b().state.anchors[current],
                    self.b().state.generations[current],
                ));
            }
            groups.push(LineGroup { raw, metadata });
            live += n;
        }
        while r.current.is_some() {
            let group = r.group;
            let source_line = r.current.as_ref().unwrap().0.line;
            let source = &groups[source_line];
            let live_start = source_line + r.line_growth.before(source_line);
            let base = r.current_delta;
            let mut builder = GroupBuilder::new(source);
            let mut copied = 0;
            let mut reverse_edits = Vec::new();
            let mut line_starts = vec![0];
            if r.back {
                for (i, b) in source.raw.iter().enumerate() {
                    if *b == b'\n' {
                        line_starts.push(i + 1);
                    }
                }
            }
            loop {
                let original = r.current.as_ref().unwrap();
                let x = original.0.x.saturating_add_signed(base);
                let y = original.1.x.saturating_add_signed(base);
                let raw = r.raw();
                let (a, anchor) = if r.back {
                    let line = line_starts.partition_point(|start| *start <= x) - 1;
                    (
                        Pos {
                            line: live_start + line,
                            x: x - line_starts[line],
                        },
                        source.metadata[line].0,
                    )
                } else {
                    builder.source(source, copied, x);
                    (
                        Pos {
                            line: live_start + builder.metadata.len() - 1,
                            x: builder.x,
                        },
                        builder.metadata.last().unwrap().0,
                    )
                };
                let b = Pos {
                    line: a.line,
                    x: a.x + y - x,
                };
                self.bm()
                    .record_replacement_with_anchor(a, b, &source.raw[x..y], &raw, anchor);
                let generations: Vec<u64> = raw
                    .iter()
                    .filter(|byte| **byte == b'\n')
                    .map(|_| {
                        let g = self.b().next_gen;
                        self.bm().next_gen += 1;
                        g
                    })
                    .collect();
                self.replacement_changed(r, a, b, &raw);
                if r.back {
                    reverse_edits.push((x, y, raw, generations));
                } else {
                    builder.added(&raw, &generations);
                    copied = y;
                }
                match r.advance(&self.conf, &mut self.input, poll) {
                    Ok(true) if r.group == group => {}
                    _ => break,
                }
            }
            if r.back {
                for (x, y, raw, gens) in reverse_edits.into_iter().rev() {
                    builder.source(source, copied, x);
                    builder.added(&raw, &gens);
                    copied = y;
                }
            }
            builder.source(source, copied, source.raw.len());
            groups[source_line] = builder.finish();
        }
        let capacity = r.source.len() + r.line_growth.before(r.source.len());
        let mut lines = Vec::with_capacity(capacity);
        let mut anchors = Vec::with_capacity(capacity);
        let mut generations = Vec::with_capacity(capacity);
        for group in groups {
            lines.extend(group.raw.split(|b| *b == b'\n').map(bytes::encode_nuls));
            for (anchor, generation) in group.metadata {
                anchors.push(anchor);
                generations.push(generation);
            }
        }
        self.bm().state.lines = lines;
        self.bm().state.anchors = anchors;
        self.bm().state.generations = generations;
    }
    pub fn replace_answer(&mut self, yes: bool, all: bool) {
        let Some(mut r) = self.replacement.take() else {
            return;
        };
        let mut poll = SearchPoll::new(&self.conf);
        if yes
            && all
            && (r.replacement.contains(&b'\n') || self.b().state.lines.len() != r.source.len())
        {
            self.replace_multiline_all(&mut r, &mut poll);
            self.replacement = Some(r);
            self.finish_replace();
            return;
        }
        loop {
            if r.current.is_none() {
                break;
            }
            let raw = if yes { r.raw() } else { Vec::new() };
            if yes && all && !raw.contains(&b'\n') && self.b().state.lines.len() == r.source.len() {
                if self.replace_line_all(&mut r, &mut poll).is_err() {
                    break;
                }
            } else {
                if yes {
                    let (a, b) = r.live_match(self.b());
                    let mut before = self.bm().begin();
                    before.pos = a;
                    self.bm().replace(a, b, &raw, Splice::Plain);
                    let no = self.conf.on(NO_NEWLINES);
                    self.bm().finish(before, "replacement", false, no);
                    if !cfg!(feature = "tiny")
                        && let Some(item) = self.bm().history.back_mut()
                    {
                        item.after.pos = a;
                    }
                    self.replacement_changed(&mut r, a, b, &raw);
                }
                if r.advance(&self.conf, &mut self.input, &mut poll).is_err() {
                    break;
                }
            }
            if !all {
                self.replacement = Some(r);
                self.show_replacement();
                return;
            }
        }
        self.replacement = Some(r);
        self.finish_replace();
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
            self.restore_spell_position();
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

#[cfg(test)]
#[path = "../tests/search/regressions.rs"]
mod tests;
