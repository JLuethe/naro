//! Typed substitution for the original position-report catalog key.
//!
//! The legacy printf spellings are identifiers only. Accept the exact nine
//! conversions used by the shipped catalogs, in order, plus escaped percent
//! signs. The catalog cannot choose types, widths, indexes or argument counts.
//! Unsupported or incomplete templates fall back to the English message.

pub const MSGID: &str = "line %*zd/%zd (%2d%%), col %2zu/%2zu (%3d%%), char %*zu/%zu (%2d%%)";
const TOKENS: [&[u8]; 9] = [
    b"%*zd", b"%zd", b"%2d", b"%2zu", b"%2zu", b"%3d", b"%*zu", b"%zu", b"%2d",
];
// Shipped templates are much smaller. Bound both scanning and output growth
// for user-selected catalogs, independently of any embedded width spelling.
const MAX_TEMPLATE: usize = 4096;

pub fn format(template: &[u8], values: [usize; 9]) -> Vec<u8> {
    let [
        line,
        lines,
        line_pct,
        col,
        cols,
        col_pct,
        count,
        total,
        char_pct,
    ] = values;
    let line_width = lines.to_string().len().max(2);
    let char_width = total.to_string().len().max(2);
    let numbers = [
        format!("{line:>line_width$}"),
        lines.to_string(),
        format!("{line_pct:>2}"),
        format!("{col:>2}"),
        format!("{cols:>2}"),
        format!("{col_pct:>3}"),
        format!("{count:>char_width$}"),
        total.to_string(),
        format!("{char_pct:>2}"),
    ];
    substitute(template, &numbers)
        .unwrap_or_else(|| substitute(MSGID.as_bytes(), &numbers).expect("fixed position template"))
}

fn substitute(template: &[u8], numbers: &[String; 9]) -> Option<Vec<u8>> {
    if template.len() > MAX_TEMPLATE || template.contains(&0) {
        return None;
    }
    let mut result = Vec::with_capacity(template.len());
    let mut rest = template;
    let mut index = 0;
    while let Some(percent) = rest.iter().position(|&b| b == b'%') {
        result.extend_from_slice(&rest[..percent]);
        rest = &rest[percent..];
        if let Some(tail) = rest.strip_prefix(b"%%") {
            result.push(b'%');
            rest = tail;
        } else {
            rest = rest.strip_prefix(*TOKENS.get(index)?)?;
            result.extend_from_slice(numbers[index].as_bytes());
            index += 1;
        }
    }
    result.extend_from_slice(rest);
    (index == numbers.len()).then_some(result)
}

#[cfg(test)]
mod tests {
    use super::*;

    const VALUES: [usize; 9] = [1, 3, 33, 2, 6, 33, 1, 11, 9];

    #[test]
    fn english_widths_and_large_unsigned_values() {
        assert_eq!(
            format(MSGID.as_bytes(), VALUES),
            b"line  1/3 (33%), col  2/ 6 ( 33%), char  1/11 ( 9%)"
        );
        let max = usize::MAX;
        assert_eq!(
            format(MSGID.as_bytes(), [max, max, 100, 1, 1, 100, max, max, 100]),
            format!("line {max}/{max} (100%), col  1/ 1 (100%), char {max}/{max} (100%)")
                .as_bytes()
        );
    }

    #[test]
    fn catalog_bytes_and_percent_spacing_are_preserved() {
        let template = b"l\xedna %*zd/%zd (%2d %%), col %2zu/%2zu (%3d %%), char %*zu/%zu (%2d %%)";
        assert_eq!(
            format(template, VALUES),
            b"l\xedna  1/3 (33 %), col  2/ 6 ( 33 %), char  1/11 ( 9 %)"
        );
    }

    #[test]
    fn malformed_templates_use_english_without_interpreting_arguments() {
        let expected = format(MSGID.as_bytes(), VALUES);
        // Only the safe Rust formatter receives these incomplete/unsupported
        // templates. They are never passed to a legacy native formatter.
        for template in [
            b"translated position".as_slice(),
            b"translated position %",
            b"translated position %q",
            &MSGID.as_bytes()[..MSGID.len() - 7],
            &[MSGID.as_bytes(), b" extra %2d"].concat(),
            &[MSGID.as_bytes(), b"\0"].concat(),
            &vec![b'x'; MAX_TEMPLATE + 1],
        ] {
            assert_eq!(format(template, VALUES), expected);
        }
    }
}
