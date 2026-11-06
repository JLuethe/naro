//! Ordinary lock/save fixtures: each test owns its disposable directory.
use super::*;
use std::sync::atomic::{AtomicU64, Ordering};

struct Fixture {
    root: PathBuf,
    config: Config,
}

impl Fixture {
    fn new(confined: bool) -> Self {
        static SERIAL: AtomicU64 = AtomicU64::new(0);
        let root = std::env::temp_dir().join(format!(
            "naro-lock-{}-{}",
            std::process::id(),
            SERIAL.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&root).unwrap();
        let mut config = Config::new(false);
        config.set(LOCKING, true);
        if confined {
            config
                .strings
                .insert("operatingdir".into(), root.as_os_str().as_bytes().to_vec());
            config.operating_root = Some(File::open(&root).unwrap());
        }
        Self { root, config }
    }

    fn buffer(&self) -> Buffer {
        let source = self.root.join("document");
        fs::write(&source, b"original\n").unwrap();
        let (mut buffer, _, _) = open(&self.config, source.as_os_str().as_bytes(), false).unwrap();
        lock(&self.config, &mut buffer).unwrap();
        buffer
    }
}

impl Drop for Fixture {
    fn drop(&mut self) {
        fs::remove_dir_all(&self.root).unwrap();
    }
}

fn identity(metadata: &fs::Metadata) -> (u64, u64) {
    (metadata.dev(), metadata.ino())
}

#[test]
fn save_as_to_owned_lock_keeps_document_and_saved_state() {
    for confined in [false, true] {
        let fixture = Fixture::new(confined);
        let mut buffer = fixture.buffer();
        let source = config::path(&buffer.name);
        let destination = lock_path(&buffer.name);
        buffer.insert(b"edited ", "addition", false, false);
        assert!(buffer.modified);
        let saved_bytes = buffer.raw();
        let n = write(
            &fixture.config,
            &mut buffer,
            destination.as_os_str().as_bytes(),
            0,
            false,
            true,
            |_| {},
        )
        .map_err(|e| e.message)
        .unwrap();
        assert_eq!(n, 1);
        assert_eq!(fs::read(&destination).unwrap(), saved_bytes);
        assert_eq!(fs::read(source).unwrap(), b"original\n");
        assert_eq!(buffer.name, destination.as_os_str().as_bytes());
        assert!(!buffer.modified);
        assert_eq!(buffer.saved, Some(buffer.hist));
        assert_eq!(
            identity(buffer.stat.as_ref().expect("saved document has metadata")),
            identity(&fs::metadata(&destination).unwrap())
        );
        assert!(!changed(&fixture.config, &buffer, &buffer.name));
        let new_lock = lock_path(&buffer.name);
        if !cfg!(feature = "tiny") {
            assert_eq!(fs::read(&new_lock).unwrap().len(), 1024);
        }
        remove_lock(&mut buffer);
        assert!(!new_lock.exists());
        assert_eq!(fs::read(&destination).unwrap(), saved_bytes);
        if !cfg!(feature = "tiny") {
            buffer.undo(false).unwrap();
            assert!(buffer.modified);
            buffer.undo(true).unwrap();
            assert!(!buffer.modified);
        }
    }
}

#[test]
fn cleanup_preserves_substituted_lock_entry() {
    for confined in [false, true] {
        let fixture = Fixture::new(confined);
        let mut buffer = fixture.buffer();
        let path = lock_path(&buffer.name);
        fs::rename(&path, fixture.root.join("previous-lock")).unwrap();
        fs::write(&path, b"unrelated document\n").unwrap();
        remove_lock(&mut buffer);
        assert!(buffer.lock.is_none());
        assert_eq!(fs::read(path).unwrap(), b"unrelated document\n");
    }
}

#[test]
fn refresh_preserves_substituted_lock_entry() {
    for confined in [false, true] {
        let fixture = Fixture::new(confined);
        let mut buffer = fixture.buffer();
        let path = lock_path(&buffer.name);
        fs::rename(&path, fixture.root.join("previous-lock")).unwrap();
        fs::write(&path, b"unrelated document\n").unwrap();
        buffer.insert(b"edited ", "addition", false, false);
        assert!(lock(&fixture.config, &mut buffer).is_err());
        assert!(buffer.lock.is_none());
        assert!(buffer.modified);
        assert_eq!(fs::read(&path).unwrap(), b"unrelated document\n");
        remove_lock(&mut buffer);
        assert_eq!(fs::read(path).unwrap(), b"unrelated document\n");
    }
}

#[test]
fn owned_lock_refresh_and_cleanup_keep_normal_semantics() {
    for confined in [false, true] {
        let fixture = Fixture::new(confined);
        let mut buffer = fixture.buffer();
        let path = lock_path(&buffer.name);
        let first = fs::read(&path).unwrap();
        assert_eq!(first.len(), 1024);
        assert_eq!(&first[..10], b"b0nano 9.3");
        assert_eq!(first[1007], 0);
        buffer.insert(b"edited ", "addition", false, false);
        lock(&fixture.config, &mut buffer).unwrap();
        let refreshed = fs::read(&path).unwrap();
        assert_eq!(refreshed.len(), 1024);
        assert_eq!(&refreshed[..1007], &first[..1007]);
        assert_eq!(refreshed[1007], 0x55);
        assert!(buffer.lock_modified);
        remove_lock(&mut buffer);
        assert!(!path.exists());
        assert!(buffer.lock.is_none());
        remove_lock(&mut buffer);
    }
}

#[test]
fn missing_owned_lock_can_be_refreshed_and_removed() {
    let fixture = Fixture::new(false);
    let mut buffer = fixture.buffer();
    let path = lock_path(&buffer.name);
    fs::remove_file(&path).unwrap();
    buffer.insert(b"edited ", "addition", false, false);
    lock(&fixture.config, &mut buffer).unwrap();
    assert_eq!(fs::read(&path).unwrap()[1007], 0x55);
    fs::remove_file(&path).unwrap();
    remove_lock(&mut buffer);
    assert!(buffer.lock.is_none());
}

#[test]
fn save_as_preserves_an_unowned_new_sidecar() {
    for confined in [false, true] {
        let fixture = Fixture::new(confined);
        let mut buffer = fixture.buffer();
        let old_lock = lock_path(&buffer.name);
        let destination = fixture.root.join("saved-document");
        let new_lock = lock_path(destination.as_os_str().as_bytes());
        fs::write(&new_lock, b"unrelated sidecar document\n").unwrap();
        let before = fs::metadata(&new_lock).unwrap();
        buffer.insert(b"edited ", "addition", false, false);
        let mut warnings = Vec::new();
        write(
            &fixture.config,
            &mut buffer,
            destination.as_os_str().as_bytes(),
            0,
            false,
            true,
            |event| {
                if let WriteProgress::Warning(message) = event {
                    warnings.push(message.to_owned());
                }
            },
        )
        .map_err(|e| e.message)
        .unwrap();
        assert_eq!(fs::read(&destination).unwrap(), buffer.raw());
        assert!(!old_lock.exists());
        assert_eq!(
            fs::read(&new_lock).unwrap(),
            b"unrelated sidecar document\n"
        );
        assert_eq!(
            identity(&fs::metadata(&new_lock).unwrap()),
            identity(&before)
        );
        assert!(buffer.lock.is_none());
        assert!(!buffer.modified);
        assert_eq!(buffer.saved, Some(buffer.hist));
        assert_eq!(
            identity(buffer.stat.as_ref().unwrap()),
            identity(&fs::metadata(destination).unwrap())
        );
        assert_eq!(warnings.len(), usize::from(!cfg!(feature = "tiny")));
        remove_lock(&mut buffer);
        assert_eq!(fs::read(new_lock).unwrap(), b"unrelated sidecar document\n");
    }
}

#[test]
fn only_explicit_takeover_replaces_an_unowned_lock() {
    let fixture = Fixture::new(false);
    let name = fixture.root.join("document");
    let path = lock_path(name.as_os_str().as_bytes());
    fs::write(&path, b"existing lock\n").unwrap();
    let mut buffer = Buffer::new(name.as_os_str().as_bytes().to_vec(), vec![vec![]]);
    assert!(lock(&fixture.config, &mut buffer).is_err());
    assert_eq!(fs::read(&path).unwrap(), b"existing lock\n");
    assert!(buffer.lock.is_none());
    take_over_lock(&fixture.config, &mut buffer).unwrap();
    assert_eq!(fs::read(&path).unwrap().len(), 1024);
    remove_lock(&mut buffer);
    assert!(!path.exists());
}
