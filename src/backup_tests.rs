//! Fixture-owned backup metadata checks. No user files are touched.
use super::*;
use std::fs::OpenOptions;

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

#[test]
fn insecure_backup_replaces_a_hard_link_without_truncating_source() {
    let fixture = Fixture::new("hard-link");
    let source = fixture.0.join("source");
    let backup = fixture.0.join("source~");
    fs::write(&source, b"original backup bytes\n").unwrap();
    fs::hard_link(&source, &backup).unwrap();
    let before = fs::metadata(&source).unwrap();
    let mut config = Config::new(false);
    config.set(INSECURE_BACKUP, true);
    make_backup(&config, &source, &before, |_| {})
        .map_err(|e| e.message)
        .unwrap();
    assert_eq!(fs::read(&source).unwrap(), b"original backup bytes\n");
    assert_eq!(fs::metadata(&source).unwrap().ino(), before.ino());
    assert_eq!(fs::read(&backup).unwrap(), b"original backup bytes\n");
    assert_ne!(fs::metadata(&backup).unwrap().ino(), before.ino());
}

#[test]
fn backups_replace_regular_files_and_links_without_writing_through_them() {
    use std::os::unix::fs::symlink;
    for insecure in [false, true] {
        for kind in [
            "regular",
            "source-symlink",
            "other-symlink",
            "other-hardlink",
        ] {
            let fixture = Fixture::new(kind);
            let source = fixture.0.join("source");
            let backup = fixture.0.join("source~");
            let other = fixture.0.join("other");
            fs::write(&source, b"original backup bytes\n").unwrap();
            fs::write(&other, b"unrelated bytes\n").unwrap();
            match kind {
                "source-symlink" => symlink("source", &backup).unwrap(),
                "other-symlink" => symlink("other", &backup).unwrap(),
                "other-hardlink" => fs::hard_link(&other, &backup).unwrap(),
                _ => fs::write(&backup, b"previous backup\n").unwrap(),
            }
            let before = fs::metadata(&source).unwrap();
            let mut config = Config::new(false);
            config.set(INSECURE_BACKUP, insecure);
            make_backup(&config, &source, &before, |_| {})
                .map_err(|e| e.message)
                .unwrap();
            assert_eq!(fs::read(&source).unwrap(), b"original backup bytes\n");
            assert_eq!(fs::metadata(&source).unwrap().ino(), before.ino());
            assert_eq!(fs::read(&other).unwrap(), b"unrelated bytes\n");
            assert!(
                !fs::symlink_metadata(&backup)
                    .unwrap()
                    .file_type()
                    .is_symlink()
            );
            assert_eq!(fs::read(&backup).unwrap(), b"original backup bytes\n");
        }
    }
}

#[test]
fn backup_cleanup_keeps_collisions_and_replaced_entries() {
    let fixture = Fixture::new("cleanup");
    let name = fixture.0.join("temporary");
    let target = fixture.0.join("backup");
    let parent = Parent::open(&Config::new(false), &name).unwrap();
    fs::write(&name, b"collision").unwrap();
    assert!(
        matches!(BackupOutput::create(parent, Parent::open(&Config::new(false), &target).unwrap()), Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists)
    );
    assert_eq!(fs::read(&name).unwrap(), b"collision");
    fs::remove_file(&name).unwrap();
    let parent = Parent::open(&Config::new(false), &name).unwrap();
    let output =
        BackupOutput::create(parent, Parent::open(&Config::new(false), &target).unwrap()).unwrap();
    fs::rename(&name, fixture.0.join("held")).unwrap();
    fs::write(&name, b"replacement entry").unwrap();
    drop(output);
    assert_eq!(fs::read(&name).unwrap(), b"replacement entry");
    assert!(fixture.0.join("held").is_dir());
}

#[test]
fn backup_publish_rejects_replaced_temp_and_keeps_existing_backup() {
    let fixture = Fixture::new("publish-identity");
    let name = fixture.0.join("temporary");
    let backup = fixture.0.join("backup");
    fs::write(&backup, b"previous backup").unwrap();
    let output = BackupOutput::create(
        Parent::open(&Config::new(false), &name).unwrap(),
        Parent::open(&Config::new(false), &backup).unwrap(),
    )
    .unwrap();
    fs::rename(name.join("content"), name.join("held")).unwrap();
    fs::write(name.join("content"), b"replacement entry").unwrap();
    assert!(output.finish(true).is_err());
    assert_eq!(
        fs::read(name.join("content")).unwrap(),
        b"replacement entry"
    );
    assert_eq!(fs::read(&backup).unwrap(), b"previous backup");
}

#[test]
#[cfg(not(feature = "tiny"))]
fn backup_directory_keeps_numbered_previous_copies() {
    let fixture = Fixture::new("backup-directory");
    let source = fixture.0.join("source");
    let directory = fixture.0.join("backups");
    fs::create_dir(&directory).unwrap();
    let mut config = Config::new(false);
    config.strings.insert(
        "backupdir".into(),
        directory.as_os_str().as_bytes().to_vec(),
    );
    for content in [b"first\n".as_slice(), b"second\n".as_slice()] {
        fs::write(&source, content).unwrap();
        make_backup(&config, &source, &fs::metadata(&source).unwrap(), |_| {})
            .map_err(|e| e.message)
            .unwrap();
    }
    let mut names: Vec<_> = fs::read_dir(directory)
        .unwrap()
        .map(|e| e.unwrap().path())
        .collect();
    names.sort();
    assert_eq!(names.len(), 2);
    assert!(names[0].as_os_str().as_bytes().ends_with(b"source~"));
    assert!(names[1].as_os_str().as_bytes().ends_with(b"source~.1"));
    assert_eq!(fs::read(&names[0]).unwrap(), b"first\n");
    assert_eq!(fs::read(&names[1]).unwrap(), b"second\n");
}
