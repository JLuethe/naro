// SPDX-License-Identifier: GPL-3.0-or-later
mod buffer;
mod bytes;
mod config;
mod editor;
mod features;
mod files;
#[rustfmt::skip]
mod generated;
mod help_data;
mod input;
mod native;
mod prompts;
mod regex_validation;
mod render;
mod search;
use std::os::unix::ffi::OsStrExt;
fn main() {
    if std::env::var_os("TERM").is_none() {
        unsafe {
            std::env::set_var("TERM", "vt220");
        }
    }
    let locale_dir = std::env::var_os("NARO_LOCALEDIR")
        .map(std::path::PathBuf::from)
        .unwrap_or_else(|| {
            std::path::PathBuf::from(concat!(env!("CARGO_MANIFEST_DIR"), "/assets/locale"))
        });
    let loc = native::cstr(locale_dir.as_os_str().as_bytes());
    let utf8 = unsafe { native::nr_locale(loc.as_ptr()) } != 0;
    if std::env::var_os("NARO_REGEX_PROBE").is_some() {
        regex_validation::run();
        return;
    }
    let mut conf = config::Config::new(utf8);
    match conf.parse_cli() {
        Ok(Some(status)) => std::process::exit(status),
        Ok(None) => {}
        Err(msg) => {
            eprintln!("{msg}");
            std::process::exit(1);
        }
    }
    if unsafe { native::nr_tty(1) } == 0 {
        unsafe {
            native::nr_done();
        }
        eprintln!("Standard output is not a terminal");
        std::process::exit(1);
    }
    let terminal = match native::Terminal::new(
        conf.on(generated::PRESERVE),
        conf.on(generated::RAW_SEQUENCES),
    ) {
        Ok(t) => t,
        Err(msg) => {
            eprintln!("{msg}");
            std::process::exit(1);
        }
    };
    if let Err(msg) = conf.finish_startup() {
        drop(terminal);
        eprintln!("{msg}");
        std::process::exit(1);
    }
    unsafe {
        native::nr_configure(
            conf.on(generated::PRESERVE) as i32,
            conf.on(generated::RAW_SEQUENCES) as i32,
        );
    }
    let mut editor = editor::Editor::new(conf);
    std::panic::set_hook(Box::new(|_| {}));
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| editor.run()));
    let status = match result {
        Ok(code) => {
            if let Some(message) = editor.fatal.clone() {
                editor.fatal_save(&message);
            }
            code
        }
        Err(_) => {
            editor.fatal_save("Sorry! Nano crashed!  Code: 6.  Please report a bug.\n");
            1
        }
    };
    drop(terminal);
    if editor.fatal.is_none() {
        for error in &editor.conf.errors {
            eprintln!("{error}");
        }
    }
    std::process::exit(status);
}
