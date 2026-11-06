//! Ordinary, fixture-owned authorization checks. No entry-swapping/race harness.
use super::*;
use crate::{buffer::Buffer, files, generated::*};
use std::{
    os::unix::{
        ffi::OsStrExt,
        fs::{MetadataExt, symlink},
    },
    sync::atomic::{AtomicU64, Ordering},
};
static SERIAL: AtomicU64 = AtomicU64::new(0);
struct Fixture {
    base: PathBuf,
    root: PathBuf,
    conf: Config,
}
impl Fixture {
    fn new() -> Self {
        let base = std::env::current_dir()
            .unwrap()
            .join("target/issue-12-fixtures")
            .join(format!(
                "{}-{}",
                std::process::id(),
                SERIAL.fetch_add(1, Ordering::Relaxed)
            ));
        let root = base.join("root");
        fs::create_dir_all(root.join("nested")).unwrap();
        fs::create_dir_all(base.join("other")).unwrap();
        let mut conf = Config::new(false);
        conf.strings
            .insert("operatingdir".into(), root.as_os_str().as_bytes().to_vec());
        conf.operating_root = Some(File::open(&root).unwrap());
        Self { base, root, conf }
    }
    fn buffer(&self, name: &str) -> Buffer {
        let mut b = Buffer::new(
            self.root.join(name).as_os_str().as_bytes().to_vec(),
            vec![b"new data".to_vec(), vec![]],
        );
        b.modified = true;
        b
    }
    fn save(&self, b: &mut Buffer, name: &Path, mode: i32) -> Result<usize, String> {
        files::write(
            &self.conf,
            b,
            name.as_os_str().as_bytes(),
            mode,
            false,
            false,
            |_| {},
        )
        .map_err(String::from)
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        fs::remove_dir_all(&self.base).unwrap();
    }
}

#[test]
fn confinement_reads_and_metadata_use_opened_file() {
    let f = Fixture::new();
    let path = f.root.join("nested/input");
    fs::write(&path, b"content\n").unwrap();
    symlink("nested/input", f.root.join("relative-link")).unwrap();
    let (raw, meta) = read(&f.conf, &f.root.join("relative-link")).unwrap();
    assert_eq!(raw, b"content\n");
    assert_eq!(meta.ino(), fs::metadata(&path).unwrap().ino());
    let (buffer, _, _) = files::open(
        &f.conf,
        f.root.join("relative-link").as_os_str().as_bytes(),
        false,
    )
    .unwrap();
    assert_eq!(buffer.raw(), b"content\n");
    assert_eq!(buffer.stat.unwrap().ino(), meta.ino());
    assert_eq!(files::read(&f.conf, &path).unwrap(), b"content\n");
}
#[test]
fn confinement_rejects_unresolved_or_uninitialized_authority() {
    let mut f = Fixture::new();
    assert!(!check(&f.conf, &f.root.join("missing/child")));
    assert!(Parent::open(&f.conf, &f.root.join("missing/child")).is_err());
    assert!(check(&f.conf, &f.root.join("new-file")));
    f.conf.operating_root = None;
    assert!(!check(&f.conf, &f.root.join("new-file")));
    assert!(Parent::open(&f.conf, &f.root.join("new-file")).is_err());
}
#[test]
fn confinement_rejects_paths_outside_root_and_absolute_links() {
    let f = Fixture::new();
    let other = f.base.join("other/input");
    fs::write(&other, b"other fixture\n").unwrap();
    assert!(!check(&f.conf, &other));
    assert!(read(&f.conf, &other).is_err());
    assert!(Parent::open(&f.conf, &other).is_err());
    assert!(f.save(&mut f.buffer("unused"), &other, 0).is_err());
    // Absolute symlinks are rejected even when their ordinary target is inside.
    let inside = f.root.join("input");
    fs::write(&inside, b"inside\n").unwrap();
    symlink(&inside, f.root.join("absolute-link")).unwrap();
    assert!(read(&f.conf, &f.root.join("absolute-link")).is_err());
    assert_eq!(fs::read(&other).unwrap(), b"other fixture\n");
}
#[test]
fn confinement_new_overwrite_append_prepend_and_symlink_policy() {
    let f = Fixture::new();
    for mode in 0..=2 {
        let path = f.root.join(format!("nested/mode-{mode}"));
        fs::write(&path, b"old\n").unwrap();
        let mut b = f.buffer("unused");
        f.save(&mut b, &path, mode).unwrap();
        let expected: &[u8] = match mode {
            0 => b"new data\n",
            1 => b"old\nnew data\n",
            _ => b"new data\nold\n",
        };
        assert_eq!(fs::read(&path).unwrap(), expected);
    }
    let path = f.root.join("nested/new");
    let mut b = f.buffer("unused");
    f.save(&mut b, &path, 0).unwrap();
    assert_eq!(fs::read(&path).unwrap(), b"new data\n");
    symlink("nested/new", f.root.join("save-link")).unwrap();
    let error = f.save(&mut b, &f.root.join("save-link"), 0).unwrap_err();
    assert!(error.contains("symbolic link"), "{error}");
    assert_eq!(fs::read(&path).unwrap(), b"new data\n");
    symlink("nested", f.root.join("directory-link")).unwrap();
    f.save(&mut b, &f.root.join("directory-link/new-via-parent"), 0)
        .unwrap();
    assert_eq!(
        fs::read(f.root.join("nested/new-via-parent")).unwrap(),
        b"new data\n"
    );
}
#[test]
#[cfg(not(feature = "tiny"))]
fn confinement_backups_stay_with_authorized_parents() {
    let mut f = Fixture::new();
    f.conf.flags |= 1 << MAKE_BACKUP;
    let path = f.root.join("input");
    fs::write(&path, b"original\n").unwrap();
    let mut b = f.buffer("input");
    f.save(&mut b, &path, 0).unwrap();
    assert_eq!(fs::read(f.root.join("input~")).unwrap(), b"original\n");
    f.conf.strings.insert(
        "backupdir".into(),
        f.root.join("nested").as_os_str().as_bytes().to_vec(),
    );
    f.save(&mut b, &path, 0).unwrap();
    let configured_backups: Vec<_> = fs::read_dir(f.root.join("nested")).unwrap().collect();
    assert_eq!(configured_backups.len(), 1);
    assert_eq!(
        fs::read(configured_backups[0].as_ref().unwrap().path()).unwrap(),
        b"new data\n"
    );
    f.conf.strings.insert(
        "backupdir".into(),
        f.base.join("other").as_os_str().as_bytes().to_vec(),
    );
    let error = f.save(&mut b, &path, 0).unwrap_err();
    assert!(error.contains("Error writing"), "{error}");
    assert_eq!(fs::read(&path).unwrap(), b"new data\n");
    assert_eq!(fs::read_dir(f.base.join("other")).unwrap().count(), 0);
}
#[test]
fn confinement_recovery_and_locks_use_authorized_parent() {
    let f = Fixture::new();
    let mut b = f.buffer("nested/input");
    files::lock(&f.conf, &mut b).unwrap();
    assert!(files::lock_conflict(&f.conf, &b.name).is_some());
    assert!(f.root.join("nested/.input.swp").exists());
    files::remove_lock(&mut b);
    assert!(!f.root.join("nested/.input.swp").exists());
    let recovery = files::emergency(&f.conf, &b).unwrap().unwrap();
    assert_eq!(fs::read(&recovery).unwrap(), b"new data\n");
    let recovery2 = files::emergency(&f.conf, &b).unwrap().unwrap();
    assert_ne!(recovery, recovery2);
    b.name = f.base.join("other/input").as_os_str().as_bytes().to_vec();
    assert!(files::lock(&f.conf, &mut b).is_err());
    assert!(files::emergency(&f.conf, &b).is_err());
    assert_eq!(fs::read_dir(f.base.join("other")).unwrap().count(), 0);
}

#[test]
fn confinement_directory_listing_is_authorized() {
    let f = Fixture::new();
    fs::write(f.root.join("nested/first"), b"one").unwrap();
    fs::write(f.root.join("nested/second"), b"two").unwrap();
    let mut entries = directory_entries(&f.conf, &f.root.join("nested")).unwrap();
    entries.sort();
    assert_eq!(
        entries,
        vec![f.root.join("nested/first"), f.root.join("nested/second")]
    );
    assert!(directory_entries(&f.conf, &f.base.join("other")).is_err());
    assert!(directory_entries(&f.conf, &f.root.join("missing")).is_err());
    assert!(is_directory(&f.conf, &f.root.join("nested")));
    assert!(!is_directory(&f.conf, &f.base.join("other")));
}

#[test]
fn confinement_startup_pins_and_enters_root() {
    if let Some(root) = std::env::var_os("NARO_CONFINEMENT_INIT_FIXTURE") {
        let root = PathBuf::from(root);
        let opened = initialize(&root).unwrap();
        assert_eq!(std::env::current_dir().unwrap(), root);
        assert_eq!(
            opened.metadata().unwrap().ino(),
            fs::metadata(".").unwrap().ino()
        );
        return;
    }
    // Changing cwd is process-global, so initialization runs in its own process.
    let f = Fixture::new();
    let output = std::process::Command::new(std::env::current_exe().unwrap())
        .args([
            "--exact",
            "confinement::tests::confinement_startup_pins_and_enters_root",
        ])
        .env("NARO_CONFINEMENT_INIT_FIXTURE", &f.root)
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}{}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
fn confinement_rejects_fifo_before_data_open() {
    unsafe extern "C" {
        fn mkfifo(path: *const std::ffi::c_char, mode: u32) -> i32;
    }
    let f = Fixture::new();
    let path = f.root.join("fifo");
    let name = cpath(&path).unwrap();
    assert_eq!(unsafe { mkfifo(name.as_ptr(), 0o600) }, 0);
    assert_eq!(read(&f.conf, &path).unwrap_err().raw_os_error(), Some(22));
    assert_eq!(
        Parent::open(&f.conf, &path)
            .unwrap()
            .read()
            .unwrap_err()
            .raw_os_error(),
        Some(22)
    );
}
