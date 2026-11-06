//! Opened-directory authorization for operating-directory file operations.
use crate::config::{self, Config};
use std::{
    ffi::{CStr, CString, c_void},
    fs::{self, File},
    io::{self, Read},
    os::{
        fd::{AsRawFd, FromRawFd},
        unix::ffi::{OsStrExt, OsStringExt},
    },
    path::{Path, PathBuf},
};
unsafe extern "C" {
    fn nr_confined_open(root: i32, path: *const std::ffi::c_char, directory: i32) -> i32;
    fn nr_at_open(dir: i32, name: *const std::ffi::c_char, operation: i32, mode: u32) -> i32;
    fn nr_at_unlink(dir: i32, name: *const std::ffi::c_char) -> i32;
    fn nr_directory_chdir(dir: i32) -> i32;
    fn nr_directory_stream(dir: i32) -> *mut c_void;
    fn nr_directory_next(stream: *mut c_void, error: *mut i32) -> *const std::ffi::c_char;
    fn nr_directory_close(stream: *mut c_void);
}
fn cpath(path: &Path) -> io::Result<CString> {
    CString::new(path.as_os_str().as_bytes()).map_err(|_| io::ErrorKind::InvalidInput.into())
}
fn descriptor(fd: i32) -> io::Result<File> {
    if fd < 0 {
        Err(io::Error::last_os_error())
    } else {
        Ok(unsafe { File::from_raw_fd(fd) })
    }
}
fn relative(c: &Config, path: &Path) -> io::Result<PathBuf> {
    let root = config::path(&c.value("operatingdir"));
    let absolute = if path.is_absolute() {
        path.to_path_buf()
    } else {
        std::env::current_dir()?.join(path)
    };
    absolute
        .strip_prefix(root)
        .map(Path::to_path_buf)
        .map_err(|_| io::ErrorKind::PermissionDenied.into())
}
fn beneath(c: &Config, path: &Path, directory: i32) -> io::Result<File> {
    let root = c
        .operating_root
        .as_ref()
        .ok_or(io::ErrorKind::PermissionDenied)?;
    let relative = relative(c, path)?;
    let relative = if relative.as_os_str().is_empty() {
        Path::new(".")
    } else {
        &relative
    };
    let path = cpath(relative)?;
    descriptor(unsafe { nr_confined_open(root.as_raw_fd(), path.as_ptr(), directory) })
}
pub fn enabled(c: &Config) -> bool {
    !c.value("operatingdir").is_empty()
}
pub fn initialize(root: &Path) -> io::Result<File> {
    let root = File::open(root)?;
    if !root.metadata()?.is_dir() {
        return Err(io::ErrorKind::NotADirectory.into());
    }
    let dot = CString::new(".").unwrap();
    let check = descriptor(unsafe { nr_confined_open(root.as_raw_fd(), dot.as_ptr(), 1) })?;
    if unsafe { nr_directory_chdir(check.as_raw_fd()) } < 0 {
        return Err(io::Error::last_os_error());
    }
    Ok(root)
}
pub fn read(c: &Config, path: &Path) -> io::Result<(Vec<u8>, fs::Metadata)> {
    let mut file = if enabled(c) {
        beneath(c, path, 0)?
    } else {
        File::open(path)?
    };
    let metadata = file.metadata()?;
    let mut bytes = Vec::new();
    file.read_to_end(&mut bytes)?;
    Ok((bytes, metadata))
}
/// Enumerate an authorized opened directory. Returned paths are display names;
/// every subsequent operation must independently acquire its own authority.
pub fn directory_entries(c: &Config, path: &Path) -> io::Result<Vec<PathBuf>> {
    if !enabled(c) {
        return fs::read_dir(path)?
            .map(|entry| entry.map(|e| e.path()))
            .collect();
    }
    let directory = beneath(c, path, 1)?;
    struct Stream(*mut c_void);
    impl Drop for Stream {
        fn drop(&mut self) {
            unsafe {
                nr_directory_close(self.0);
            }
        }
    }
    let raw = unsafe { nr_directory_stream(directory.as_raw_fd()) };
    if raw.is_null() {
        return Err(io::Error::last_os_error());
    }
    let stream = Stream(raw);
    let mut names = Vec::new();
    loop {
        let mut error = 0;
        let entry = unsafe { nr_directory_next(stream.0, &mut error) };
        if entry.is_null() {
            if error != 0 {
                return Err(io::Error::from_raw_os_error(error));
            }
            return Ok(names);
        }
        // readdir owns this NUL-terminated name until the next call; copy now.
        let name = unsafe { CStr::from_ptr(entry) }.to_bytes();
        if name != b"." && name != b".." {
            names.push(path.join(std::ffi::OsString::from_vec(name.to_vec())));
        }
    }
}
pub fn is_directory(c: &Config, path: &Path) -> bool {
    metadata(c, path).is_ok_and(|m| m.is_dir())
}
pub fn metadata(c: &Config, path: &Path) -> io::Result<fs::Metadata> {
    if enabled(c) {
        beneath(c, path, -1)?.metadata()
    } else {
        fs::metadata(path)
    }
}
pub fn check(c: &Config, path: &Path) -> bool {
    if !enabled(c) {
        return true;
    }
    match metadata(c, path) {
        Ok(_) => true,
        Err(e) if e.kind() == io::ErrorKind::NotFound => Parent::open(c, path).is_ok(),
        Err(_) => false,
    }
}
/// The parent actually used by each create/read/unlink/save operation.
#[derive(Debug)]
pub struct Parent {
    pub directory: File,
    pub name: PathBuf,
    confined: bool,
}
impl Parent {
    pub fn open(c: &Config, path: &Path) -> io::Result<Self> {
        let name = path.file_name().ok_or(io::ErrorKind::InvalidInput)?;
        let parent = path
            .parent()
            .filter(|p| !p.as_os_str().is_empty())
            .unwrap_or(Path::new("."));
        let directory = if enabled(c) {
            beneath(c, parent, 1)?
        } else {
            File::open(parent)?
        };
        if !directory.metadata()?.is_dir() {
            return Err(io::ErrorKind::NotADirectory.into());
        }
        Ok(Self {
            directory,
            name: PathBuf::from(name),
            confined: enabled(c),
        })
    }
    fn open_leaf(&self, operation: i32, mode: u32) -> io::Result<File> {
        let name = cpath(&self.name)?;
        descriptor(unsafe {
            nr_at_open(self.directory.as_raw_fd(), name.as_ptr(), operation, mode)
        })
    }
    pub fn read(&self) -> io::Result<File> {
        self.open_leaf(if self.confined { 3 } else { 0 }, 0)
    }
    pub fn create(&self, mode: u32) -> io::Result<File> {
        self.open_leaf(1, mode)
    }
    pub fn remove(&self) -> io::Result<()> {
        let name = cpath(&self.name)?;
        if unsafe { nr_at_unlink(self.directory.as_raw_fd(), name.as_ptr()) } < 0 {
            Err(io::Error::last_os_error())
        } else {
            Ok(())
        }
    }
    pub fn metadata(&self) -> io::Result<fs::Metadata> {
        self.open_leaf(2, 0)?.metadata()
    }
    pub fn sibling(&self, name: PathBuf) -> io::Result<Self> {
        if name.components().count() != 1 || name.file_name().is_none() {
            return Err(io::ErrorKind::InvalidInput.into());
        }
        Ok(Self {
            directory: self.directory.try_clone()?,
            name,
            confined: self.confined,
        })
    }
}

#[cfg(all(test, not(feature = "tiny")))]
#[path = "confinement_tests.rs"]
mod tests;

#[cfg(test)]
mod shared_tests {
    use super::*;
    #[test]
    fn confinement_parent_supports_unconfined_file_operations() {
        let path = std::env::current_dir()
            .unwrap()
            .join("target/issue-12-shared")
            .join(std::process::id().to_string());
        fs::create_dir_all(&path).unwrap();
        let destination = path.join("new");
        let parent = Parent::open(&Config::new(false), &destination).unwrap();
        crate::native::safe_save(&parent, b"first\n", 0).unwrap();
        crate::native::safe_save(&parent, b"second\n", 1).unwrap();
        assert_eq!(fs::read(&destination).unwrap(), b"first\nsecond\n");
        assert!(parent.metadata().unwrap().is_file());
        parent.remove().unwrap();
        assert!(!destination.exists());
        fs::remove_dir(&path).unwrap();
    }
}
