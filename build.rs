use std::{env, path::PathBuf, process::Command};
fn main() {
    let out = PathBuf::from(env::var_os("OUT_DIR").unwrap());
    let status = Command::new(env::var("CC").unwrap_or("cc".into()))
        .args([
            "-std=c11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-D_DEFAULT_SOURCE",
            "-D_XOPEN_SOURCE=700",
            "-c",
            "native/bridge.c",
            "-o",
        ])
        .arg(out.join("bridge.o"))
        .status()
        .expect("a C compiler is required for ncurses/regex ABI glue");
    assert!(status.success(), "native bridge compilation failed");
    assert!(
        Command::new("ar")
            .arg("crs")
            .arg(out.join("libnaro_native.a"))
            .arg(out.join("bridge.o"))
            .status()
            .unwrap()
            .success()
    );
    println!("cargo:rustc-link-search=native={}", out.display());
    println!("cargo:rustc-link-lib=static=naro_native");
    println!("cargo:rustc-link-lib=ncursesw");
    println!("cargo:rustc-link-lib=magic");
    println!("cargo:rerun-if-changed=native/bridge.c");
    println!("cargo:rerun-if-changed=native/options.inc");
}
