//! Compiled exclusively into the recovery-test executable.
use std::path::PathBuf;
use std::sync::OnceLock;

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
