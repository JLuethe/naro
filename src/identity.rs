//! Runtime product identity. Reference assets and gettext keys remain unchanged.

pub const TITLE: &str = concat!("NARO ", env!("CARGO_PKG_VERSION"));

pub fn version() -> String {
    format!(
        " NARO, version {}\n Independent Rust port of GNU nano; reference version 9.3\n License: GPL-3.0-or-later\n Compiled profile: {}; UTF-8 enabled\n",
        env!("CARGO_PKG_VERSION"),
        if cfg!(feature = "tiny") {
            "tiny"
        } else {
            "default"
        }
    )
}

pub fn cli_help(reference: &str) -> String {
    reference
        .replace("Usage: nano ", "Usage: naro ")
        .replace(", nano reads data", ", naro reads data")
}

/// Brand explicit UI text only, after gettext has used its original nano key.
/// Whole words prevent changes to compatible terms such as nanorc.
pub fn brand_program_name(text: &str) -> String {
    // These Japanese particles attach directly to the Latin product name in
    // the bundled help translations. Do not broaden this to arbitrary words.
    let text = text
        .replace("nanoの", "NAROの")
        .replace("nanoは", "NAROは")
        .replace("nanoが", "NAROが");
    text.split_inclusive(|c: char| !c.is_alphanumeric() && c != '_')
        .map(|part| {
            let end = part
                .find(|c: char| !c.is_alphanumeric() && c != '_')
                .unwrap_or(part.len());
            // Observed product aliases in the bundled ar/fi/ko/sr catalogs.
            // Preserve inflection suffixes; nanorc and its transliterations
            // are compatible configuration terms and are not product labels.
            let branded = match &part[..end] {
                "nano" | "Nano" | "NANO" | "نانو" | "나노" | "нано" => Some("NARO"),
                "nanon" | "Nanon" => Some("NAROn"),
                "nanoon" => Some("NAROon"),
                "Nanossa" => Some("NAROssa"),
                "나노에" => Some("NARO에"),
                "наноа" => Some("NAROа"),
                "нанова" => Some("NAROва"),
                _ => None,
            };
            if let Some(name) = branded {
                format!("{name}{}", &part[end..])
            } else {
                part.to_owned()
            }
        })
        .collect()
}

#[cfg(not(feature = "tiny"))]
pub fn main_help_title(translated_title: &str) -> String {
    if translated_title.contains("NARO") {
        translated_title.to_owned()
    } else {
        format!("NARO — {translated_title}")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn version_identifies_product_and_reference_separately() {
        let output = version();
        assert!(output.starts_with(concat!(" NARO, version ", env!("CARGO_PKG_VERSION"), "\n")));
        assert!(output.contains("Independent Rust port of GNU nano; reference version 9.3\n"));
        assert!(output.contains("License: GPL-3.0-or-later\n"));
        assert!(output.ends_with(if cfg!(feature = "tiny") {
            "Compiled profile: tiny; UTF-8 enabled\n"
        } else {
            "Compiled profile: default; UTF-8 enabled\n"
        }));
    }

    #[test]
    fn all_cli_help_profiles_identify_the_executable() {
        for source in [
            include_str!("../assets/help.txt"),
            include_str!("../assets/help-restricted.txt"),
            include_str!("../assets/help-tiny.txt"),
        ] {
            let output = cli_help(source);
            assert!(output.starts_with("Usage: naro [OPTIONS]"));
            assert!(!output.contains("Usage: nano "));
            assert!(!output.contains(", nano reads data"));
            assert_eq!(output.lines().count(), source.lines().count());
        }
    }

    #[test]
    fn translated_program_names_preserve_other_words() {
        assert_eq!(
            brand_program_name("Main nano help text; Nano, NANO. nanorc nano_data nanometer"),
            "Main NARO help text; NARO, NARO. nanorc nano_data nanometer"
        );
        assert_eq!(
            brand_program_name("Aide de nano : édition"),
            "Aide de NARO : édition"
        );
    }

    #[test]
    fn observed_catalog_aliases_preserve_inflections_and_config_terms() {
        for (original, expected) in [
            ("نانو", "NARO"),
            ("nanon Nanon nanoon Nanossa", "NAROn NAROn NAROon NAROssa"),
            (
                "nanoのヘルプ nanoは もしnanoが",
                "NAROのヘルプ NAROは もしNAROが",
            ),
            ("나노 나노에", "NARO NARO에"),
            ("нано наноа нанова", "NARO NAROа NAROва"),
            (
                "nanorc нанорц nanometer nano_data",
                "nanorc нанорц nanometer nano_data",
            ),
        ] {
            assert_eq!(brand_program_name(original), expected);
        }
    }

    #[cfg(not(feature = "tiny"))]
    #[test]
    fn main_help_heading_always_names_naro_without_double_prefix() {
        assert_eq!(
            main_help_title("===  Kratke upute  ==="),
            "NARO — ===  Kratke upute  ==="
        );
        assert_eq!(
            main_help_title("Main NARO help text"),
            "Main NARO help text"
        );
        assert_eq!(
            main_help_title("NARO 주요 도움말 내용"),
            "NARO 주요 도움말 내용"
        );
    }
}
