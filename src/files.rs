//! File bytes, metadata, in-place saving, backups and nano-compatible locks.
use crate::{
    buffer::Buffer,
    bytes,
    config::{self, Config, io_error},
    generated::*,
    native,
};
use std::{
    fs::{self, File, OpenOptions},
    io::Write,
    os::unix::{
        ffi::OsStrExt,
        fs::{MetadataExt, OpenOptionsExt, PermissionsExt},
    },
    path::{Path, PathBuf},
};
pub fn inside(c: &Config, p: &Path) -> bool {
    let dir = c.value("operatingdir");
    if dir.is_empty() {
        return true;
    }
    let full = fs::canonicalize(p).or_else(|_| {
        p.parent()
            .and_then(|p| fs::canonicalize(p).ok())
            .map(|parent| parent.join(p.file_name().unwrap_or_default()))
            .ok_or(std::io::Error::from(std::io::ErrorKind::NotFound))
    });
    full.map(|p| p.starts_with(config::path(&dir)))
        .unwrap_or(true)
}
pub fn parse(raw: &[u8], convert: bool) -> (Vec<Vec<u8>>, bool, usize) {
    let convert = convert && !cfg!(feature = "tiny");
    let mut lines = Vec::new();
    let mut dos = false;
    let mut n = 0;
    let lf_count = raw.iter().filter(|b| **b == 10).count();
    for (i, l) in raw.split(|b| *b == 10).enumerate() {
        let has_lf = lf_count > i;
        let mut s = bytes::encode_nuls(l);
        if convert && has_lf && s.last() == Some(&13) {
            s.pop();
            if i == 0 {
                dos = true;
            }
        }
        lines.push(s);
        if has_lf || !l.is_empty() {
            n += 1;
        }
    }
    (lines, dos, n)
}
pub fn line_message(verb: &str, n: usize, dos: bool) -> String {
    let a = if verb == "Read" {
        if dos {
            "Read %zu line (converted from DOS format)"
        } else {
            "Read %zu line"
        }
    } else {
        "Wrote %zu line"
    };
    let b = if verb == "Read" {
        if dos {
            "Read %zu lines (converted from DOS format)"
        } else {
            "Read %zu lines"
        }
    } else {
        "Wrote %zu lines"
    };
    native::plural(a, b, n).replace("%zu", &n.to_string())
}
pub fn open(c: &Config, name: &[u8], noread: bool) -> Result<(Buffer, String, i32), String> {
    let p = config::expand(name);
    let name = p.as_os_str().as_bytes();
    let display = bytes::text(name);
    if !inside(c, &p) {
        return Err(format!(
            "Can't read file from outside of {}",
            bytes::text(&c.value("operatingdir"))
        ));
    }
    let stat = fs::metadata(&p).ok();
    if stat.as_ref().is_some_and(|s| s.is_dir()) {
        return Err(format!("'{display}' is a directory"));
    }
    if stat
        .as_ref()
        .is_some_and(|s| s.mode() & 0o170000 == 0o020000 || s.mode() & 0o170000 == 0o060000)
    {
        return Err(format!("'{display}' is a device file"));
    }
    if stat.is_none() && name.ends_with(b"/") {
        return Err(format!("'{display}' is an invalid filename"));
    }
    if cfg!(feature = "tiny")
        && stat
            .as_ref()
            .is_some_and(|s| s.mode() & 0o170000 == 0o010000)
    {
        return Err(format!("'{display}' is a FIFO"));
    }
    let mut b = Buffer::new(name.to_vec(), vec![Vec::new()]);
    b.stat = stat;
    b.report_size = true;
    let (mut msg, mut level) = ("New File".to_string(), 2);
    if !noread {
        match fs::read(&p) {
            Ok(raw) => {
                let (lines, dos, n) = parse(&raw, !c.on(NO_CONVERT));
                b.state.lines = lines;
                let nl = b.state.lines.len() as u64;
                b.state.generations = (b.next_gen..b.next_gen + nl).collect();
                b.next_gen += nl;
                b.dos = dos && !c.on(MAKE_IT_UNIX);
                msg = line_message("Read", n, dos);
                if b.stat.as_ref().is_some_and(|s| s.mode() & 0o222 == 0) {
                    msg = format!("File '{display}' is unwritable");
                    level = 7;
                }
            }
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => {
                let parent = p
                    .parent()
                    .filter(|p| !p.as_os_str().is_empty())
                    .unwrap_or(Path::new("."));
                if !parent.exists() {
                    msg = format!("Directory '{}' does not exist", parent.display());
                    level = 7;
                }
            }
            Err(e) => {
                msg = format!("Error reading {display}: {}", io_error(&e));
                level = 7;
            }
        }
    }
    b.magic(c.on(NO_NEWLINES));
    b.syntax = c.select_syntax(name, &b.state.lines[0]);
    Ok((b, msg, level))
}
pub fn output(b: &Buffer, raw: Option<Vec<u8>>, nonew: bool) -> Vec<u8> {
    let mut data = raw.unwrap_or_else(|| b.raw());
    if !nonew && !data.is_empty() && data.last() != Some(&10) {
        data.push(10);
    }
    if b.dos {
        let mut dos = Vec::with_capacity(data.len() * 2);
        for x in data {
            if x == 10 {
                dos.push(13);
            }
            dos.push(x);
        }
        dos
    } else {
        data
    }
}
pub struct WriteError {
    pub confirm_backup: bool,
    pub message: String,
    pub errno: Option<i32>,
}
impl From<String> for WriteError {
    fn from(message: String) -> Self {
        Self {
            message,
            errno: None,
            confirm_backup: false,
        }
    }
}
impl From<WriteError> for String {
    fn from(error: WriteError) -> String {
        error.message
    }
}
impl WriteError {
    fn writing(name: &str, error: std::io::Error) -> Self {
        Self {
            message: format!("Error writing {name}: {}", io_error(&error)),
            errno: error.raw_os_error(),
            confirm_backup: false,
        }
    }
}
pub fn write(
    c: &Config,
    b: &mut Buffer,
    name: &[u8],
    mode: i32,
    selection: bool,
    skip_backup: bool,
    mut progress: impl FnMut(&str),
) -> Result<usize, WriteError> {
    let p = config::expand(name);
    if !inside(c, &p) {
        return Err(format!(
            "Can't write outside of {}",
            bytes::text(&c.value("operatingdir"))
        )
        .into());
    }
    let display = bytes::text(name);
    let meta = fs::metadata(&p).ok();
    if mode == 2
        && meta
            .as_ref()
            .is_some_and(|m| m.mode() & 0o170000 == 0o010000)
    {
        return Err(format!("Error writing {display}: FIFO").into());
    }
    let old = if meta.as_ref().is_some_and(|m| m.is_file()) {
        fs::read(&p).ok()
    } else {
        None
    };
    if c.on(MAKE_BACKUP)
        && !skip_backup
        && !c.on(RESTRICTED)
        && let (Some(old), Some(meta)) = (old.as_ref(), meta.as_ref())
        && meta.is_file()
    {
        make_backup(c, &p, old, meta)?;
    }
    let region = if selection {
        b.region().map(|(a, z)| b.raw_region(a, z))
    } else {
        None
    };
    let data = output(b, region, c.on(NO_NEWLINES));
    let n = data.iter().filter(|b| **b == 10).count()
        + usize::from(!data.is_empty() && data.last() != Some(&10));
    let fifo = meta
        .as_ref()
        .is_some_and(|m| m.mode() & 0o170000 == 0o010000);
    if fifo && !cfg!(feature = "tiny") {
        progress("Writing to FIFO...");
    }
    let mut f = OpenOptions::new()
        .write(true)
        .create(true)
        .truncate(mode != 1)
        .append(mode == 1)
        .mode(0o666)
        .open(&p)
        .map_err(|e| WriteError::writing(&display, e))?;
    progress("Writing...");
    write_bytes(&mut f, &data).map_err(|e| WriteError::writing(&display, e))?;
    if mode == 2
        && let Some(old) = old
    {
        write_bytes(&mut f, &old).map_err(|e| WriteError::writing(&display, e))?;
    }
    if !fifo {
        f.sync_all().map_err(|e| WriteError::writing(&display, e))?;
    }
    if !selection && mode == 0 {
        if b.name != name {
            remove_lock(b);
            b.name = name.to_vec();
            b.syntax = c.select_syntax(name, &b.state.lines[0]);
            if c.on(LOCKING) {
                let _ = lock(b);
            }
        }
        b.stat = fs::metadata(&p).ok();
        b.saved();
        b.report_size = true;
    }
    Ok(n)
}
pub fn changed(b: &Buffer, name: &[u8]) -> bool {
    if b.name != name {
        return false;
    }
    match (&b.stat, fs::metadata(config::expand(name))) {
        (Some(old), Ok(new)) => {
            new.dev() != old.dev()
                || new.ino() != old.ino()
                || new.mtime() > old.mtime()
                || new.mtime() == old.mtime() && new.mtime_nsec() > old.mtime_nsec()
        }
        _ => false,
    }
}
pub fn lock_path(name: &[u8]) -> PathBuf {
    let p = config::expand(name);
    let mut file = vec![b'.'];
    file.extend(p.file_name().unwrap_or_default().as_bytes());
    file.extend(b".swp");
    p.parent()
        .filter(|p| !p.as_os_str().is_empty())
        .unwrap_or(Path::new("."))
        .join(config::path(&file))
}
pub fn lock_conflict(name: &[u8]) -> Option<Result<String, String>> {
    let p = lock_path(name);
    let raw = fs::read(&p).ok()?;
    if raw.len() < 68 || !raw.starts_with(b"b0") {
        return Some(Err(format!("Bad lock file is ignored: {}", p.display())));
    }
    let end = |a: usize, b: usize| {
        let x = &raw[a..b];
        bytes::text(&x[..x.iter().position(|b| *b == 0).unwrap_or(x.len())])
    };
    let pid = u32::from_le_bytes(raw[24..28].try_into().unwrap());
    Some(Ok(format!(
        "File {} is being edited by {} (with {}, PID {pid}); open anyway?",
        bytes::text(name),
        end(28, 44),
        end(2, 12)
    )))
}
pub fn lock(b: &mut Buffer) -> Result<(), String> {
    if b.name.is_empty() {
        return Ok(());
    }
    let p = lock_path(&b.name);
    let mut raw = vec![0u8; 1024];
    raw[..2].copy_from_slice(b"b0");
    raw[2..10].copy_from_slice(b"nano 9.3");
    raw[24..28].copy_from_slice(&std::process::id().to_le_bytes());
    let user = native::user();
    let n = user.len().min(16);
    raw[28..28 + n].copy_from_slice(&user[..n]);
    let host = native::host();
    let n = host.len().min(31);
    raw[68..68 + n].copy_from_slice(&host[..n]);
    let n = b.name.len().min(768);
    raw[108..108 + n].copy_from_slice(&b.name[..n]);
    if b.modified {
        raw[1007] = 0x55;
    }
    if p.exists() {
        fs::remove_file(&p)
            .map_err(|e| format!("Error deleting lock file {}: {}", p.display(), io_error(&e)))?;
    }
    let mut f = OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o666)
        .open(&p)
        .map_err(|e| format!("Error writing lock file {}: {}", p.display(), io_error(&e)))?;
    f.write_all(&raw).map_err(|e| io_error(&e))?;
    b.lock = Some(p);
    b.lock_modified = b.modified;
    Ok(())
}
pub fn remove_lock(b: &mut Buffer) {
    if let Some(p) = b.lock.take() {
        let _ = fs::remove_file(p);
    }
}
pub fn emergency(c: &Config, b: &Buffer) -> Option<PathBuf> {
    if !b.modified || c.on(RESTRICTED) {
        return None;
    }
    let name = if b.name.is_empty() {
        format!("nano.{}", std::process::id()).into_bytes()
    } else {
        b.name.clone()
    };
    let mut name = name;
    name.extend(b".save");
    let p = collision(&config::path(&name));
    let mut f = OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .open(&p)
        .ok()?;
    f.write_all(&output(b, None, c.on(NO_NEWLINES))).ok()?;
    let _ = f.sync_all();
    Some(p)
}
pub fn collision(base: &Path) -> PathBuf {
    if !base.exists() {
        return base.to_path_buf();
    }
    for i in 1..=99999 {
        let mut n = base.as_os_str().as_bytes().to_vec();
        n.extend(format!(".{i}").as_bytes());
        let p = config::path(&n);
        if !p.exists() {
            return p;
        }
    }
    base.to_path_buf()
}
pub struct ToolFile {
    pub path: PathBuf,
}
impl Drop for ToolFile {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.path);
    }
}
#[cfg(not(feature = "tiny"))]
pub fn temp(c: &Config, b: &Buffer, selection: bool) -> Result<ToolFile, String> {
    let dir = std::env::var_os("TMPDIR")
        .map(PathBuf::from)
        .filter(|d| d.is_dir())
        .unwrap_or_else(|| PathBuf::from("/tmp"));
    let ext = config::path(&b.name)
        .extension()
        .map(|e| {
            let mut b = vec![b'.'];
            b.extend(e.as_bytes());
            b
        })
        .unwrap_or_default();
    for n in 0..1000 {
        let tick = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .subsec_nanos() as u64
            + std::process::id() as u64
            + n;
        let alphabet = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        let mut val = tick;
        let mut name = b"nano.".to_vec();
        for _ in 0..6 {
            name.push(alphabet[(val % 62) as usize]);
            val /= 62;
        }
        name.extend(&ext);
        let p = dir.join(config::path(&name));
        if let Ok(mut f) = OpenOptions::new()
            .write(true)
            .read(true)
            .create_new(true)
            .mode(0o600)
            .open(&p)
        {
            let temp = ToolFile { path: p };
            let region = if selection {
                b.region().map(|(a, z)| b.raw_region(a, z))
            } else {
                None
            };
            let data = output(b, region, selection || c.on(NO_NEWLINES));
            f.write_all(&data).map_err(|e| io_error(&e))?;
            f.sync_all().map_err(|e| io_error(&e))?;
            return Ok(temp);
        }
    }
    Err("Could not create temporary file".into())
}

// Match C stdio's error handling: retry positive short writes, but expose EINTR
// rather than silently retrying it as Write::write_all does.
fn write_bytes(file: &mut File, mut bytes: &[u8]) -> std::io::Result<()> {
    while !bytes.is_empty() {
        let count = file.write(bytes)?;
        if count == 0 {
            return Err(std::io::Error::from_raw_os_error(5));
        }
        bytes = &bytes[count..];
    }
    Ok(())
}

fn make_backup(
    c: &Config,
    path: &Path,
    bytes: &[u8],
    meta: &fs::Metadata,
) -> Result<(), WriteError> {
    let directory = c.value("backupdir");
    let name = if directory.is_empty() {
        let mut name = path.as_os_str().as_bytes().to_vec();
        name.push(b'~');
        config::path(&name)
    } else {
        let full = fs::canonicalize(path).unwrap_or_else(|_| path.to_path_buf());
        let mut name = full.as_os_str().as_bytes().to_vec();
        for c in &mut name {
            if *c == b'/' {
                *c = b'!';
            }
        }
        name.push(b'~');
        collision(&config::path(&directory).join(config::path(&name)))
    };
    let write = |file: &mut File| -> std::io::Result<()> {
        write_bytes(file, bytes)?;
        if let Err(error) = file.set_permissions(fs::Permissions::from_mode(meta.mode() & 0o7777))
            && error.raw_os_error() != Some(1)
        {
            return Err(error);
        }
        file.sync_all()?;
        let _ = file.set_times(
            std::fs::FileTimes::new()
                .set_accessed(meta.accessed()?)
                .set_modified(meta.modified()?),
        );
        Ok(())
    };
    let first = (|| {
        if !c.on(INSECURE_BACKUP) {
            match fs::remove_file(&name) {
                Ok(()) => (),
                Err(e) if e.kind() == std::io::ErrorKind::NotFound => (),
                Err(e) => return Err(e),
            }
        }
        let mut file = OpenOptions::new()
            .write(true)
            .create(true)
            .create_new(!c.on(INSECURE_BACKUP))
            .truncate(c.on(INSECURE_BACKUP))
            .mode(0o600)
            .open(&name)?;
        write(&mut file)
    })();
    if first.is_ok() {
        return Ok(());
    }
    let _ = fs::remove_file(&name);
    let mut last = first.unwrap_err();
    if let Some(home) = config::home_dir() {
        crate::render::flash_warning(c, "Cannot make regular backup");
        crate::render::flash_warning(c, "Trying again in your home directory");
        for i in 0..1000u64 {
            let value = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default()
                .as_nanos() as u64
                + i;
            let mut name = path.file_name().unwrap_or_default().as_bytes().to_vec();
            name.push(b'~');
            let alphabet = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
            let mut n = value;
            for _ in 0..6 {
                name.push(alphabet[(n % 62) as usize]);
                n /= 62;
            }
            match OpenOptions::new()
                .write(true)
                .create_new(true)
                .mode(0o600)
                .open(home.join(config::path(&name)))
            {
                Ok(mut file) => match write(&mut file) {
                    Ok(()) => return Ok(()),
                    Err(e) => {
                        last = e;
                        break;
                    }
                },
                Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => continue,
                Err(e) => {
                    last = e;
                    break;
                }
            }
        }
    }
    crate::render::flash_warning(c, "Cannot make backup");
    crate::render::flash_warning(c, &io_error(&last));
    Err(WriteError {
        message: format!("Cannot make backup: {}", io_error(&last)),
        errno: last.raw_os_error(),
        confirm_backup: last.raw_os_error() != Some(28),
    })
}
