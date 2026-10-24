//! Byte-preserving text coordinates; spec 18.
use crate::native;
#[derive(Clone, Copy, Debug)]
pub struct Encoding {
    pub utf8: bool,
    pub tab: usize,
}
impl Encoding {
    pub fn len(self, s: &[u8], x: usize) -> usize {
        if x >= s.len() {
            return 0;
        }
        if !self.utf8 {
            return 1;
        }
        let b = s[x];
        let n = match b {
            0xc2..=0xdf => 2,
            0xe0..=0xef => 3,
            0xf0..=0xf4 => 4,
            _ => 1,
        };
        if x + n > s.len() || s[x + 1..x + n].iter().any(|c| !(0x80..=0xbf).contains(c)) {
            return 1;
        }
        if std::str::from_utf8(&s[x..x + n]).is_err() {
            1
        } else {
            n
        }
    }
    pub fn right(self, s: &[u8], x: usize) -> usize {
        (x + self.len(s, x)).min(s.len())
    }
    pub fn left(self, s: &[u8], x: usize) -> usize {
        if x == 0 {
            return 0;
        }
        if !self.utf8 {
            return x - 1;
        }
        let mut p = x.saturating_sub(4);
        while p < x && self.right(s, p) < x {
            p = self.right(s, p);
        }
        p
    }
    pub fn code(self, s: &[u8], x: usize) -> Option<u32> {
        if x >= s.len() {
            return None;
        }
        if !self.utf8 {
            return Some((s[x] as i8 as i32) as u32);
        }
        std::str::from_utf8(&s[x..x + self.len(s, x)])
            .ok()?
            .chars()
            .next()
            .map(u32::from)
    }
    pub fn zero(self, s: &[u8], x: usize) -> bool {
        self.utf8
            && self
                .code(s, x)
                .is_some_and(|c| c >= 0x300 && unsafe { native::nr_width(c) } == 0)
    }
    pub fn move_right(self, s: &[u8], x: usize) -> usize {
        let mut p = self.right(s, x);
        while p < s.len() && self.zero(s, p) {
            p = self.right(s, p);
        }
        p
    }
    pub fn move_left(self, s: &[u8], x: usize) -> usize {
        let mut p = self.left(s, x);
        while p > 0 && self.zero(s, p) {
            p = self.left(s, p);
        }
        p
    }
    pub fn width(self, s: &[u8], x: usize, col: usize) -> usize {
        if s[x] == b'\t' {
            return self.tab - col % self.tab;
        }
        let b = s[x];
        if b < 32 || b == 127 || (!self.utf8 && (0x80..0xa0).contains(&b)) {
            return 2;
        }
        if self.utf8
            && let Some(c) = self.code(s, x)
        {
            if (0x80..0xa0).contains(&c) {
                return 2;
            }
            let w = unsafe { native::nr_width(c) };
            return if w < 0 { 1 } else { w as usize };
        }
        1
    }
    pub fn column(self, s: &[u8], x: usize) -> usize {
        let mut p = 0;
        let mut col = 0;
        while p < x.min(s.len()) {
            col += self.width(s, p, col);
            p = self.right(s, p);
        }
        col
    }
    pub fn breadth(self, s: &[u8]) -> usize {
        self.column(s, s.len())
    }
    pub fn actual(self, s: &[u8], col: usize) -> usize {
        let mut p = 0;
        let mut c = 0;
        while p < s.len() {
            let w = self.width(s, p, c);
            if c + w > col {
                break;
            }
            c += w;
            p = self.right(s, p);
        }
        p
    }
    pub fn count(self, s: &[u8]) -> usize {
        let mut p = 0;
        let mut n = 0;
        while p < s.len() {
            p = self.right(s, p);
            n += 1;
        }
        n
    }
    pub fn blank(self, s: &[u8], x: usize) -> bool {
        if x >= s.len() {
            return false;
        }
        if s[x] == b' ' || s[x] == b'\t' {
            return true;
        }
        self.code(s, x)
            .is_some_and(|c| unsafe { native::nr_class(c, 2) } != 0)
    }
    pub fn word(self, s: &[u8], x: usize, punct: bool, extra: &[u8]) -> bool {
        if x >= s.len() {
            return false;
        }
        let n = self.len(s, x);
        let class=self.code(s,x).is_some_and(|c|unsafe{native::nr_class(c,0)}!=0 || punct&&unsafe{native::nr_class(c,1)}!=0);
        class || (!extra.is_empty() && extra.windows(n).any(|w| w == &s[x..x + n]))
    }
    pub fn indent(self, s: &[u8]) -> usize {
        let mut x = 0;
        while x < s.len() && self.blank(s, x) {
            x = self.right(s, x);
        }
        x
    }
    pub fn display(self, s: &[u8], whitespace: bool, data: bool) -> Vec<Glyph> {
        let mut out: Vec<Glyph> = Vec::new();
        let mut x = 0;
        let mut col = 0;
        while x < s.len() {
            let n = self.len(s, x);
            let width = self.width(s, x, col);
            let b = s[x];
            if b == b'\t' {
                for i in 0..width {
                    out.push(Glyph {
                        text: if whitespace && i == 0 {
                            if self.utf8 { "»".into() } else { ">".into() }
                        } else {
                            " ".into()
                        },
                        width: 1,
                        byte: x,
                    });
                }
            } else if b < 32
                || b == 127
                || (!self.utf8 && (0x80..0xa0).contains(&b))
                || self.code(s, x).is_some_and(|c| (0x80..0xa0).contains(&c))
            {
                let second = if b == 10 && data {
                    '@'
                } else if b == 127 {
                    '?'
                } else if b < 32 {
                    (b + 64) as char
                } else {
                    let c = if self.utf8 { s[x + 1] } else { b };
                    if c == 0x9f { '=' } else { (c - 0x20) as char }
                };
                out.push(Glyph {
                    text: "^".into(),
                    width: 1,
                    byte: x,
                });
                out.push(Glyph {
                    text: second.to_string(),
                    width: 1,
                    byte: x,
                });
            } else {
                let text = if self.utf8 {
                    std::str::from_utf8(&s[x..x + n]).unwrap_or("�").to_string()
                } else {
                    (b as char).to_string()
                };
                let text = if whitespace && b == b' ' {
                    if self.utf8 { "·".into() } else { ".".into() }
                } else {
                    text
                };
                if width == 0 {
                    if let Some(g) = out.last_mut() {
                        g.text.push_str(&text);
                    }
                } else {
                    out.push(Glyph {
                        text,
                        width: width.max(1),
                        byte: x,
                    });
                }
            }
            col += width;
            x += n;
        }
        out
    }
}
#[derive(Clone, Debug)]
pub struct Glyph {
    pub text: String,
    pub width: usize,
    pub byte: usize,
}
pub fn encode_nuls(s: &[u8]) -> Vec<u8> {
    s.iter().map(|b| if *b == 0 { 10 } else { *b }).collect()
}
pub fn decode_nuls(s: &[u8]) -> Vec<u8> {
    s.iter().map(|b| if *b == 10 { 0 } else { *b }).collect()
}
pub fn text(s: &[u8]) -> String {
    String::from_utf8_lossy(s).into_owned()
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_and_boundaries() {
        let e = Encoding { utf8: true, tab: 8 };
        let s = b"a\xf0\x9f\x98\x80\xed\xa0\x80\xc0\x80";
        let mut p = 0;
        let mut v = vec![0];
        while p < s.len() {
            let next = e.right(s, p);
            assert_eq!(e.left(s, next), p);
            p = next;
            v.push(p);
        }
        assert_eq!(v, vec![0, 1, 5, 6, 7, 8, 9, 10]);
    }
    #[test]
    fn nul_roundtrip() {
        assert_eq!(decode_nuls(&encode_nuls(b"a\0b")), b"a\0b");
    }
    #[test]
    fn columns_tabs() {
        let e = Encoding { utf8: true, tab: 4 };
        assert_eq!(e.column(b"a\tb", 2), 4);
        assert_eq!(e.actual(b"a\tb", 3), 1);
    }
}
