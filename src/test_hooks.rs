//! Compiled exclusively into test-hook executables.
use std::path::PathBuf;
use std::sync::OnceLock;

pub fn issue14_snapshot(conf: &crate::config::Config) -> String {
    use std::fmt::Write;
    let mut output = format!(
        "flags {}\ntab {}\nfill {}\nguide {}\n",
        conf.flags, conf.tab, conf.fill, conf.guide
    );
    let mut names: Vec<_> = conf.strings.keys().collect();
    names.sort();
    for name in names {
        let value = &conf.strings[name];
        writeln!(&mut output, "string {name} {}", hex(value)).unwrap();
    }
    for (index, key) in conf.keys.iter().enumerate() {
        writeln!(
            &mut output,
            "key {index} {} {} {} {} {}",
            key.key,
            key.menus,
            key.func,
            hex(key.tag.as_bytes()),
            key.toggle
        )
        .unwrap();
    }
    output
}

fn hex(data: &[u8]) -> String {
    data.iter().map(|byte| format!("{byte:02x}")).collect()
}

pub fn poll(modified: bool) {
    static DIRECTORY: OnceLock<Option<PathBuf>> = OnceLock::new();
    if modified
        && let Some(dir) =
            DIRECTORY.get_or_init(|| std::env::var_os("NARO_TEST_PANIC_DIR").map(PathBuf::from))
    {
        if !dir.join("ready").exists() {
            std::fs::write(dir.join("ready"), b"modified\n").expect("test fixture acknowledgment");
        }
        assert!(
            !dir.join("trigger").exists(),
            "requested recovery-test panic"
        );
    }
}
