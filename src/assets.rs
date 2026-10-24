//! Runtime assets follow the installed executable, with explicit overrides.
use std::path::PathBuf;

pub fn locale_dir() -> PathBuf {
    if let Some(path) = std::env::var_os("NARO_LOCALEDIR") {
        return PathBuf::from(path);
    }
    if let Ok(exe) = std::env::current_exe()
        && let Some(prefix) = exe.parent().and_then(|p| p.parent())
    {
        let installed = prefix.join("share/naro/locale");
        if installed.is_dir() {
            return installed;
        }
    }
    PathBuf::from(concat!(env!("CARGO_MANIFEST_DIR"), "/assets/locale"))
}
