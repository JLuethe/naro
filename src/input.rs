//! ncurses input plus nano's escape/meta layer.
use crate::{config::Config, generated::*, native};
use std::collections::VecDeque;
#[derive(Clone, Debug)]
pub enum Event {
    Key(Key),
    Signal(i32),
    Idle,
}
#[derive(Clone, Debug)]
pub struct Key {
    pub code: i32,
    pub meta: bool,
    pub shift: bool,
    pub command: Option<String>,
}
impl Key {
    pub fn plain(code: i32) -> Self {
        Self {
            code,
            meta: false,
            shift: false,
            command: None,
        }
    }
}
#[derive(Default)]
pub struct Input {
    pub queue: VecDeque<i32>,
    pub replay: VecDeque<Key>,
    esc: usize,
    first_alone: bool,
    last_alone: bool,
    digits: Vec<u8>,
}
impl Input {
    pub fn next(&mut self, c: &Config) -> Event {
        if let Some(k) = self.replay.pop_front() {
            return Event::Key(k);
        }
        loop {
            let sig = unsafe { native::nr_signal() };
            if sig != 0 {
                return Event::Signal(sig);
            }
            let code = if let Some(k) = self.queue.pop_front() {
                k
            } else {
                let k = unsafe { native::nr_get(100) };
                if k < 0 {
                    return Event::Idle;
                }
                if k == 27 && c.on(RAW_SEQUENCES) {
                    std::thread::sleep(std::time::Duration::from_millis(20));
                }
                loop {
                    let v = unsafe { native::nr_get(0) };
                    if v < 0 {
                        break;
                    }
                    self.queue.push_back(v);
                }
                k
            };
            if code == 410 {
                return Event::Signal(28);
            }
            if code == 27 {
                self.first_alone = self.last_alone;
                self.last_alone = self.queue.is_empty();
                if !self.digits.is_empty() {
                    self.digits.clear();
                    self.esc = 1;
                } else {
                    self.esc += 1;
                    if self.esc == 3 {
                        self.esc = if self.last_alone { 0 } else { 1 };
                    }
                }
                continue;
            }
            let mut key = Key::plain(code);
            match self.esc {
                1 => {
                    self.esc = 0;
                    if code == 9 {
                        key.code = 0x45f;
                    } else if matches!(code, 8 | 127 | 263) {
                        key.code = 0x41d;
                    } else if !(32..=126).contains(&code) {
                        if code < 32 && !self.last_alone {
                            key.meta = true;
                        }
                    } else if matches!(code, 79 | 91)
                        && !self.queue.is_empty()
                        && self.queue.front() != Some(&27)
                    {
                        key = self.sequence(code);
                    } else {
                        key.meta = true;
                        if !c.shifted && (65..=90).contains(&code) {
                            key.code = code + 32;
                        }
                    }
                }
                2 => {
                    self.esc = 0;
                    if code == 91
                        && self
                            .queue
                            .front()
                            .is_some_and(|c| matches!(c,65..=68|97..=100))
                    {
                        let c = self.queue.pop_front().unwrap();
                        key.code = match c {
                            65 | 99 => 262,
                            66 | 100 => 360,
                            67 => 0x402,
                            68 => 0x401,
                            97 => 339,
                            98 => 338,
                            _ => 0x4fc,
                        };
                        key.shift = c >= 97;
                    } else if matches!(code, 79 | 91) && !self.queue.is_empty() {
                        key = self.sequence(code);
                        key.meta = true;
                    } else if (48..=50).contains(&code)
                        || !self.digits.is_empty() && (48..=57).contains(&code)
                    {
                        self.digits.push(code as u8);
                        let value = std::str::from_utf8(&self.digits)
                            .unwrap_or("")
                            .parse::<u32>()
                            .unwrap_or(999);
                        if value > 255 {
                            self.digits.clear();
                            key.code = code;
                        } else if self.digits.len() < 3 {
                            self.esc = 2;
                            continue;
                        } else {
                            self.digits.clear();
                            if value > 127 && c.utf8 {
                                let bytes = char::from_u32(value).unwrap().to_string().into_bytes();
                                self.queue.extend(bytes[1..].iter().map(|b| *b as i32));
                                key.code = bytes[0] as i32;
                            } else {
                                key.code = value as i32;
                            }
                        }
                    } else if self.first_alone && !self.last_alone {
                        key.meta = true;
                        if !c.shifted && (65..=90).contains(&code) {
                            key.code = code + 32;
                        }
                    } else {
                        key.code = match code {
                            64..=95 => code - 64,
                            96..=126 => code - 96,
                            51..=55 => code - 24,
                            63 | 56 => 127,
                            32 | 50 => 0,
                            47 => 31,
                            _ => code,
                        };
                    }
                }
                _ => {}
            }
            key.code = unsafe { native::nr_map(key.code) };
            if (0x411..=0x416).contains(&key.code) {
                key.code -= 16;
                key.shift = true;
            }
            match key.code {
                0x451 => {
                    key.code = 260;
                    key.shift = true;
                }
                0x452 => {
                    key.code = 261;
                    key.shift = true;
                }
                0x453 => {
                    key.code = 259;
                    key.shift = true;
                }
                0x454 => {
                    key.code = 258;
                    key.shift = true;
                }
                0x455 => {
                    key.code = 262;
                    key.shift = true;
                }
                0x456 => {
                    key.code = 360;
                    key.shift = true;
                }
                0x457 => {
                    key.code = 339;
                    key.shift = true;
                }
                0x458 => {
                    key.code = 338;
                    key.shift = true;
                }
                0x431 => {
                    key.code = 262;
                    key.shift = true;
                }
                0x432 => {
                    key.code = 360;
                    key.shift = true;
                }
                0x433 => {
                    key.code = 339;
                    key.shift = true;
                }
                0x434 => {
                    key.code = 338;
                    key.shift = true;
                }
                127 | 263 => key.code = if c.on(REBIND_DELETE) { 330 } else { 263 },
                330 if c.on(REBIND_DELETE) => key.code = 263,
                _ => {}
            }
            if matches!(key.code, 354 | 378 | 350 | 410 | 0x4fe) {
                continue;
            }
            return Event::Key(key);
        }
    }
    fn sequence(&mut self, prefix: i32) -> Key {
        let mut seq = Vec::new();
        while let Some(&b) = self.queue.front() {
            if !(0..256).contains(&b) {
                break;
            }
            self.queue.pop_front();
            seq.push(b as u8);
            if (b'@'..=b'~').contains(&(b as u8)) {
                break;
            }
        }
        let s = String::from_utf8_lossy(&seq);
        let mut key = Key::plain(0x4fc);
        if prefix == 79 && seq.len() == 1 {
            key.code = match seq[0] {
                b'A' => 259,
                b'B' => 258,
                b'C' => 261,
                b'D' => 260,
                b'H' => 262,
                b'F' => 360,
                b'M' => 343,
                b'P'..=b'S' => 265 + (seq[0] - b'P') as i32,
                b'j' => 42,
                b'k' => 43,
                b'l' => 44,
                b'm' => 45,
                b'o' => 47,
                b'n' => 330,
                b'p' => 331,
                b'q' => 360,
                b'r' => 258,
                b's' => 338,
                b't' => 260,
                b'v' => 261,
                b'w' => 262,
                b'x' => 259,
                b'y' => 339,
                _ => 0x4fc,
            };
            return key;
        }
        if s == "200~" {
            key.code = 0x4b5;
            return key;
        }
        if s == "201~" {
            key.code = 0x4be;
            return key;
        }
        if s == "Z" {
            key.code = 0x45f;
            return key;
        }
        let Some(&end) = seq.last() else {
            return key;
        };
        let numbers = String::from_utf8_lossy(&seq[..seq.len() - 1]);
        let nums: Vec<i32> = numbers.split(';').map(|n| n.parse().unwrap_or(1)).collect();
        let modifier = if nums.len() > 1 { nums[1] } else { 1 };
        let base = match end {
            b'A' | b'a' => 259,
            b'B' | b'b' => 258,
            b'C' | b'c' => 261,
            b'D' | b'd' => 260,
            b'H' => 262,
            b'F' => 360,
            b'P'..=b'S' => 265 + (end - b'P') as i32,
            b'~' => match nums[0] {
                1 | 7 => 262,
                4 | 8 => 360,
                2 => 331,
                3 => 330,
                5 => 339,
                6 => 338,
                11 => 265,
                12 => 266,
                13 => 267,
                14 => 268,
                15 => 269,
                17 => 270,
                18 => 271,
                19 => 272,
                20 => 273,
                21 => 274,
                23 => 275,
                24 => 276,
                _ => 0x4fc,
            },
            _ => 0x4fc,
        };
        key.code = base;
        if end.is_ascii_lowercase() {
            key.shift = true;
        }
        if modifier == 2 {
            key.shift = true;
            if base == 330 {
                key.code = 0x45d;
            }
        } else if modifier == 5 || modifier == 6 {
            key.shift = modifier == 6;
            key.code = match base {
                260 => 0x401,
                261 => 0x402,
                259 => 0x403,
                258 => 0x404,
                262 => 0x405,
                360 => 0x406,
                330 => {
                    if modifier == 6 {
                        0x41d
                    } else {
                        0x40d
                    }
                }
                _ => 0x4fc,
            };
        } else if modifier == 3 {
            key.code = match base {
                260 => 0x421,
                261 => 0x422,
                259 => 0x423,
                258 => 0x424,
                262 => 0x425,
                360 => 0x426,
                339 => 0x427,
                338 => 0x428,
                331 => 0x42c,
                330 => 0x42d,
                _ => 0x4fc,
            };
        } else if modifier == 4 {
            key.shift = true;
            key.code = match base {
                260 => 262,
                261 => 360,
                259 => 339,
                258 => 338,
                _ => 0x4fc,
            };
        } else if modifier > 6 {
            key.code = 0x4fc;
        }
        if key.code == 0x4fc && seq.first() == Some(&b'2') {
            self.queue.clear();
        }
        key
    }
    pub fn paste(&mut self) -> (Vec<u8>, bool) {
        let mut bytes = Vec::new();
        loop {
            let k = if let Some(k) = self.queue.pop_front() {
                k
            } else {
                unsafe { native::nr_get(100) }
            };
            if k < 0 {
                if unsafe { native::nr_signal() } != 0 {
                    return (bytes, false);
                }
                continue;
            }
            if k == 0x4be {
                return (bytes, true);
            }
            if k == 27 && self.queue.front() == Some(&91) {
                self.queue.pop_front();
                let key = self.sequence(91);
                if key.code == 0x4be {
                    return (bytes, true);
                }
                return (bytes, false);
            }
            if k == 10 || k == 13 {
                bytes.push(10);
            } else if k == 9 || (32..=255).contains(&k) && k != 127 {
                bytes.push(k as u8);
            } else {
                return (bytes, false);
            }
        }
    }
    pub fn verbatim(&mut self, utf8: bool) -> Result<Vec<u8>, ()> {
        unsafe {
            native::nr_keypad(0);
            native::nr_paste(0);
        }
        let first = if let Some(k) = self.queue.pop_front() {
            k
        } else {
            unsafe { native::nr_get(-1) }
        };
        let result = if utf8 && (first as u8).is_ascii_hexdigit() && first < 128 {
            let mut digits = vec![first as u8];
            loop {
                let k = if let Some(k) = self.queue.pop_front() {
                    k
                } else {
                    unsafe { native::nr_get(-1) }
                };
                if k == 32 || k == 13 {
                    break;
                }
                if !(0..128).contains(&k) || !(k as u8).is_ascii_hexdigit() {
                    digits.clear();
                    break;
                }
                digits.push(k as u8);
                if digits.len() == 6 {
                    break;
                }
            }
            if let Ok(value) = u32::from_str_radix(&String::from_utf8_lossy(&digits), 16)
                && let Some(ch) = char::from_u32(value)
            {
                Ok(ch.to_string().into_bytes())
            } else {
                Err(())
            }
        } else if first == 27 {
            std::thread::sleep(std::time::Duration::from_millis(20));
            let k = if let Some(k) = self.queue.pop_front() {
                k
            } else {
                unsafe { native::nr_get(0) }
            };
            if (0..256).contains(&k) {
                Ok(vec![27, k as u8])
            } else {
                Ok(vec![27])
            }
        } else if (0..256).contains(&first) {
            Ok(vec![first as u8])
        } else {
            Err(())
        };
        unsafe {
            native::nr_keypad(1);
            native::nr_paste(1);
        }
        result
    }
}
