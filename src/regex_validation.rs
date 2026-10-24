//! Fixture-only regex corpus entry point; enabled by NARO_REGEX_PROBE.
use crate::native::Regex;
use std::io::{self, BufRead};
fn unescape(s: &[u8]) -> Vec<u8> {
    let mut out = Vec::new();
    let mut i = 0;
    while i < s.len() {
        if s[i] == b'\\' && i + 1 < s.len() {
            match s[i + 1] {
                b't' => {
                    out.push(9);
                    i += 2;
                }
                b'n' => {
                    out.push(10);
                    i += 2;
                }
                b'\\' => {
                    out.push(92);
                    i += 2;
                }
                b'x' if i + 3 < s.len() => {
                    out.push(
                        u8::from_str_radix(&String::from_utf8_lossy(&s[i + 2..i + 4]), 16)
                            .unwrap_or(0),
                    );
                    i += 4;
                }
                _ => {
                    out.push(92);
                    i += 1;
                }
            }
        } else {
            out.push(s[i]);
            i += 1;
        }
    }
    out
}
fn json(s: &[u8]) -> String {
    let mut out = String::from("\"");
    for b in s {
        match *b {
            b'"' => out.push_str("\\\""),
            b'\\' => out.push_str("\\\\"),
            32..=126 => out.push(*b as char),
            _ => out.push_str(&format!("\\u{b:04x}")),
        }
    }
    out.push('"');
    out
}
pub fn run() {
    for line in io::stdin().lock().lines().map_while(Result::ok) {
        if line.starts_with('#') || line.is_empty() {
            continue;
        }
        let fields: Vec<_> = line.split('\t').collect();
        if fields.len() < 2 {
            continue;
        }
        let flags = fields[0];
        let pattern = unescape(fields[1].as_bytes());
        let subject = unescape(fields.get(2).unwrap_or(&"").as_bytes());
        let start = fields.get(3).and_then(|s| s.parse().ok());
        let mut out = format!(
            "{{\"flags\":{},\"pattern\":{},\"subject\":{}",
            json(flags.as_bytes()),
            json(&pattern),
            json(&subject)
        );
        if let Some(start) = start {
            out.push_str(&format!(",\"start\":{start}"));
        }
        let bits = i32::from(flags.contains('E'))
            | if flags.contains('I') { 2 } else { 0 }
            | if flags.contains('N') { 4 } else { 0 };
        match Regex::flags(&pattern, bits) {
            Err(error) => {
                out.push_str(&format!(
                    ",\"compile\":1,\"error\":{}",
                    json(error.as_bytes())
                ));
            }
            Ok(re) => {
                out.push_str(",\"compile\":0");
                if let Some(groups) = re.find(
                    &subject,
                    if flags.contains('S') {
                        start.unwrap_or(0)
                    } else {
                        0
                    },
                    flags.contains('B'),
                ) {
                    out.push_str(",\"exec\":0");
                    if !flags.contains('N') {
                        out.push_str(",\"match\":[");
                        for (i, (a, b)) in groups.iter().enumerate() {
                            if i > 0 {
                                out.push(',');
                            }
                            out.push_str(&format!(
                                "[{},{}]",
                                if *a == usize::MAX { -1 } else { *a as i64 },
                                if *b == usize::MAX { -1 } else { *b as i64 }
                            ));
                        }
                        out.push_str(&format!("],\"nsub\":{}", re.groups));
                    }
                } else {
                    out.push_str(",\"exec\":1");
                }
            }
        }
        out.push('}');
        println!("{out}");
    }
}
