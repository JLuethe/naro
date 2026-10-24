use std::{
    env,
    io::Write,
    path::{Path, PathBuf},
    process::{Command, Stdio},
};
fn main() {
    let out = PathBuf::from(env::var_os("OUT_DIR").unwrap());
    let mut files = Vec::new();
    for dir in ["src", "native", "assets"] {
        collect(Path::new(dir), &mut files);
    }
    files.extend(["Cargo.toml", "Cargo.lock", "build.rs", "CREDITS.md"].map(PathBuf::from));
    files.sort();
    let sums = Command::new("sha256sum")
        .args(&files)
        .output()
        .expect("sha256sum is required");
    assert!(sums.status.success());
    let mut hash = Command::new("sha256sum")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();
    hash.stdin.take().unwrap().write_all(&sums.stdout).unwrap();
    let result = hash.wait_with_output().unwrap();
    let fingerprint = String::from_utf8(result.stdout).unwrap();
    println!(
        "cargo:rustc-env=NARO_SOURCE_SHA256={}",
        fingerprint.split_whitespace().next().unwrap()
    );
    // Rebuild provenance when the current commit changes, including worktrees.
    for name in ["HEAD", "packed-refs"] {
        git_watch(name);
    }
    if let Ok(head) = std::fs::read_to_string(".git/HEAD")
        && let Some(reference) = head.trim().strip_prefix("ref: ")
    {
        git_watch(reference);
    }
    let revision = Command::new("git")
        .args(["rev-parse", "HEAD"])
        .output()
        .ok()
        .filter(|o| o.status.success())
        .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_owned())
        .unwrap_or_else(|| "source-archive".into());
    println!("cargo:rustc-env=NARO_BUILD_REVISION={revision}");
    let version = Command::new(env::var_os("RUSTC").unwrap_or_else(|| "rustc".into()))
        .arg("--version")
        .output()
        .expect("compiler version");
    println!(
        "cargo:rustc-env=NARO_RUSTC_VERSION={}",
        String::from_utf8_lossy(&version.stdout).trim()
    );
    let features = ["credits", "test-hooks"]
        .into_iter()
        .filter(|name| {
            env::var_os(format!(
                "CARGO_FEATURE_{}",
                name.replace('-', "_").to_uppercase()
            ))
            .is_some()
        })
        .collect::<Vec<_>>()
        .join(",");
    println!("cargo:rustc-env=NARO_BUILD_FEATURES={features}");
    for name in ["src", "assets", "Cargo.toml", "Cargo.lock", "CREDITS.md"] {
        println!("cargo:rerun-if-changed={name}");
    }
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

fn collect(path: &Path, files: &mut Vec<PathBuf>) {
    for entry in std::fs::read_dir(path).unwrap() {
        let path = entry.unwrap().path();
        if path.is_dir() {
            collect(&path, files);
        } else if path.is_file() {
            files.push(path);
        }
    }
}

fn git_watch(name: &str) {
    if let Ok(output) = Command::new("git")
        .args(["rev-parse", "--git-path", name])
        .output()
        && output.status.success()
    {
        let path = String::from_utf8_lossy(&output.stdout);
        let path = path.trim();
        if Path::new(path).exists() {
            println!("cargo:rerun-if-changed={path}");
        }
    }
}
