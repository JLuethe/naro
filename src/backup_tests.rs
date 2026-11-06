//! Fixture-owned backup metadata checks. No user files are touched.
use super::*;

struct Fixture(PathBuf);

impl Fixture {
    fn new(label: &str) -> Self {
        let stamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let path = PathBuf::from("target/issue-9-backup-fixtures")
            .join(format!("{label}-{}-{stamp}", std::process::id()));
        fs::create_dir_all(&path).unwrap();
        Self(path)
    }
}

impl Drop for Fixture {
    fn drop(&mut self) {
        fs::remove_dir_all(&self.0).unwrap();
    }
}

fn backup_with_metadata(source: &Path, uid: u32, gid: u32, mode: u32) {
    let source_file = OpenOptions::new().write(true).open(source).unwrap();
    native::file_chown(&source_file, uid, gid).unwrap();
    source_file
        .set_permissions(fs::Permissions::from_mode(mode))
        .unwrap();
    let times = fs::FileTimes::new()
        .set_accessed(std::time::UNIX_EPOCH + std::time::Duration::from_secs(1_600_000_001))
        .set_modified(std::time::UNIX_EPOCH + std::time::Duration::from_secs(1_600_000_002));
    source_file.set_times(times).unwrap();
    drop(source_file);

    let before = fs::metadata(source).unwrap();
    assert_eq!((before.uid(), before.gid()), (uid, gid));
    assert_eq!(before.mode() & 0o7777, mode);
    let mut warnings = Vec::new();
    make_backup(&Config::new(false), source, &before, |s| {
        warnings.push(s.to_owned())
    })
    .map_err(|e| e.message)
    .unwrap();
    assert!(warnings.is_empty(), "{warnings:?}");

    let backup = config::path(&[source.as_os_str().as_bytes(), b"~"].concat());
    let after = fs::metadata(&backup).unwrap();
    assert_eq!((after.uid(), after.gid()), (uid, gid));
    assert_eq!(after.mode() & 0o7777, mode);
    assert_eq!(
        (after.atime(), after.atime_nsec()),
        (before.atime(), before.atime_nsec())
    );
    assert_eq!(
        (after.mtime(), after.mtime_nsec()),
        (before.mtime(), before.mtime_nsec())
    );
    assert_eq!(fs::read(&backup).unwrap(), b"original backup bytes\n");
}

#[test]
fn backup_preserves_mode_and_times_for_current_owner() {
    let fixture = Fixture::new("current-owner");
    let source = fixture.0.join("source");
    fs::write(&source, b"original backup bytes\n").unwrap();
    let metadata = fs::metadata(&source).unwrap();
    backup_with_metadata(&source, metadata.uid(), metadata.gid(), 0o4750);
}

#[test]
fn backup_preserves_supplementary_group_setid_and_times() {
    let fixture = Fixture::new("supplementary");
    let source = fixture.0.join("source");
    fs::write(&source, b"original backup bytes\n").unwrap();
    let metadata = fs::metadata(&source).unwrap();
    let groups = std::process::Command::new("id").arg("-G").output().unwrap();
    assert!(groups.status.success());
    let groups = String::from_utf8(groups.stdout).unwrap();
    let group = groups
        .split_whitespace()
        .map(|g| g.parse::<u32>().unwrap())
        .find(|g| *g != metadata.gid())
        .expect("supplementary-group fixture required for this test");
    backup_with_metadata(&source, metadata.uid(), group, 0o6750);
}

#[test]
#[ignore = "requires uid 0 inside a private user namespace"]
fn backup_preserves_foreign_owner_in_private_root_namespace() {
    assert_eq!(
        std::env::var("NARO_BACKUP_ROOT_NAMESPACE").as_deref(),
        Ok("1")
    );
    let fixture = Fixture::new("root-namespace");
    let source = fixture.0.join("source");
    fs::write(&source, b"original backup bytes\n").unwrap();
    backup_with_metadata(&source, 1234, 1235, 0o6750);
}

#[test]
#[ignore = "requires a prepared foreign-owned fixture in a private user namespace"]
fn backup_warns_when_foreign_ownership_is_denied() {
    let source = PathBuf::from(std::env::var_os("NARO_BACKUP_DENIED_SOURCE").unwrap());
    let before = fs::metadata(&source).unwrap();
    assert_ne!(before.uid(), fs::metadata(".").unwrap().uid());
    let mut warnings = Vec::new();
    make_backup(&Config::new(false), &source, &before, |s| {
        warnings.push(s.to_owned())
    })
    .map_err(|e| e.message)
    .unwrap();
    assert_eq!(
        warnings,
        ["Cannot preserve backup ownership: Permission denied"]
    );
    let backup = config::path(&[source.as_os_str().as_bytes(), b"~"].concat());
    let after = fs::metadata(&backup).unwrap();
    assert_ne!((after.uid(), after.gid()), (before.uid(), before.gid()));
    assert_eq!(after.mode() & 0o7777, before.mode() & 0o7777);
    assert_eq!(fs::read(&backup).unwrap(), fs::read(&source).unwrap());
    fs::remove_file(backup).unwrap();
}
