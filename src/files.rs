//! File bytes, metadata, atomic saving, backups and nano-compatible locks.
use crate::{
    buffer::Buffer,
    bytes,
    config::{self, Config, io_error},
    confinement::{self, Parent},
    generated::*,
    native,
};
#[cfg(not(feature = "tiny"))]
use std::{fs::OpenOptions, os::unix::fs::OpenOptionsExt};
use std::{
    fs::{self, File},
    io::{Read, Write},
    os::unix::{
        ffi::OsStrExt,
        fs::{MetadataExt, PermissionsExt},
    },
    path::{Path, PathBuf},
};
pub fn inside(c: &Config, p: &Path) -> bool {
    confinement::check(c, p)
}
pub fn read(c: &Config, p: &Path) -> std::io::Result<Vec<u8>> {
    confinement::read(c, p).map(|(bytes, _)| bytes)
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
    let stat = confinement::metadata(c, &p).ok();
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
        match confinement::read(c, &p) {
            Ok((raw, metadata)) => {
                b.stat = Some(metadata);
                let (lines, dos, n) = parse(&raw, !c.on(NO_CONVERT));
                b.state.lines = lines;
                // Loading replaces the one-line constructor state. Establish
                // all line metadata before magic() can append a journaled LF.
                b.state.anchors.resize(b.state.lines.len(), false);
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
}
impl From<String> for WriteError {
    fn from(message: String) -> Self {
        Self {
            message,
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
            confirm_backup: false,
        }
    }
}
pub enum WriteProgress<'a> {
    Status(&'a str),
    Warning(&'a str),
}
pub fn write(
    c: &Config,
    b: &mut Buffer,
    name: &[u8],
    mode: i32,
    selection: bool,
    skip_backup: bool,
    mut progress: impl FnMut(WriteProgress<'_>),
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
    let parent = Parent::open(c, &p).map_err(|e| WriteError::writing(&display, e))?;
    let meta = match parent.metadata() {
        Ok(meta) => Some(meta),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => None,
        Err(e) => return Err(WriteError::writing(&display, e)),
    };
    if meta.as_ref().is_some_and(|m| m.file_type().is_symlink()) {
        return Err(format!(
            "Refusing to save through symbolic link {display}; save its target path explicitly"
        )
        .into());
    }
    if mode == 2
        && meta
            .as_ref()
            .is_some_and(|m| m.mode() & 0o170000 == 0o010000)
    {
        return Err(format!("Error writing {display}: FIFO").into());
    }
    if c.on(MAKE_BACKUP)
        && !skip_backup
        && !c.on(RESTRICTED)
        && let Some(meta) = meta.as_ref()
        && meta.is_file()
    {
        progress(WriteProgress::Status("Making backup..."));
        make_backup_from(c, &p, &parent, meta, |text| {
            progress(WriteProgress::Warning(text))
        })?;
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
        progress(WriteProgress::Status("Writing to FIFO..."));
    }
    if fifo && confinement::enabled(c) {
        return Err(
            "FIFO writes are unavailable with operating-directory confinement"
                .to_string()
                .into(),
        );
    }
    if fifo {
        let mut f = native::open_write(&p, mode == 1).map_err(|error| {
            if error.kind() == std::io::ErrorKind::Interrupted {
                "Interrupted".to_string().into()
            } else {
                WriteError::writing(&display, error)
            }
        })?;
        progress(WriteProgress::Status("Writing..."));
        write_bytes(&mut f, &data)
            .and_then(|()| native::close_checked(f))
            .map_err(|error| {
                let mut failure = WriteError::writing(&display, error);
                failure.message.push_str(" (FIFO output may be incomplete)");
                failure
            })?;
    } else {
        progress(WriteProgress::Status("Writing..."));
        native::safe_save(&parent, &data, mode).map_err(|(error, committed)| {
            if committed {
                format!(
                    "File replaced, but durability is uncertain for {display}: {}",
                    io_error(&error)
                )
                .into()
            } else {
                let mut failure = WriteError::writing(&display, error);
                failure.message.push_str(" (original file unchanged)");
                failure
            }
        })?;
    }
    if !selection && mode == 0 {
        if b.name != name {
            remove_lock(b);
            b.name = name.to_vec();
            b.syntax = c.select_syntax(name, &b.state.lines[0]);
            if c.on(LOCKING)
                && let Err(message) = lock(c, b)
            {
                progress(WriteProgress::Warning(&message));
            }
        }
        b.stat = parent.metadata().ok();
        b.saved();
        b.report_size = true;
    }
    Ok(n)
}
pub fn changed(c: &Config, b: &Buffer, name: &[u8]) -> bool {
    if b.name != name {
        return false;
    }
    match (&b.stat, confinement::metadata(c, &config::expand(name))) {
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
pub fn lock_conflict(c: &Config, name: &[u8]) -> Option<Result<String, String>> {
    let p = lock_path(name);
    let mut raw = Vec::new();
    Parent::open(c, &p)
        .ok()?
        .read()
        .ok()?
        .read_to_end(&mut raw)
        .ok()?;
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
/// Keep the created file open so its identity cannot be recycled while this
/// buffer owns the lock. The remembered pathname alone is not ownership: a
/// successful save-as can replace that entry with the saved document.
#[derive(Debug)]
pub struct OwnedLock {
    parent: Parent,
    file: File,
}
impl OwnedLock {
    fn remove(&self) -> std::io::Result<()> {
        let current = match self.parent.metadata() {
            Ok(metadata) => metadata,
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(()),
            Err(error) => return Err(error),
        };
        let owned = self.file.metadata()?;
        if current.dev() != owned.dev() || current.ino() != owned.ino() {
            return Err(std::io::Error::other("lock file was replaced"));
        }
        self.parent.remove()
    }
}
pub fn lock(c: &Config, b: &mut Buffer) -> Result<(), String> {
    write_lock(c, b, false)
}
/// Called only after the user accepts replacing another editor's lock.
pub fn take_over_lock(c: &Config, b: &mut Buffer) -> Result<(), String> {
    write_lock(c, b, true)
}
fn write_lock(c: &Config, b: &mut Buffer, takeover: bool) -> Result<(), String> {
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
    let parent = Parent::open(c, &p).map_err(|e| {
        format!(
            "Cannot authorize lock file {}: {}",
            p.display(),
            io_error(&e)
        )
    })?;
    // Refresh may remove only our owned entry. A new lock must be created
    // exclusively unless the user explicitly accepted a conflict takeover.
    let removed = if let Some(owned) = b.lock.take() {
        owned.remove()
    } else if takeover {
        parent.remove()
    } else {
        Ok(())
    };
    match removed {
        Ok(()) => (),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => (),
        Err(e) => {
            return Err(format!(
                "Error deleting lock file {}: {}",
                p.display(),
                io_error(&e)
            ));
        }
    }
    let file = parent
        .create(0o666)
        .map_err(|e| format!("Error writing lock file {}: {}", p.display(), io_error(&e)))?;
    let mut owned = OwnedLock { parent, file };
    if let Err(error) = owned.file.write_all(&raw) {
        let _ = owned.remove();
        return Err(io_error(&error));
    }
    b.lock = Some(owned);
    b.lock_modified = b.modified;
    Ok(())
}
pub fn remove_lock(b: &mut Buffer) {
    if let Some(owned) = b.lock.take() {
        let _ = owned.remove();
    }
}
pub fn emergency(c: &Config, b: &Buffer) -> Result<Option<PathBuf>, String> {
    if !b.modified || c.on(RESTRICTED) {
        return Ok(None);
    }
    let name = if b.name.is_empty() {
        format!("nano.{}", std::process::id()).into_bytes()
    } else {
        b.name.clone()
    };
    let mut name = name;
    name.extend(b".save");
    let base = config::expand(&name);
    let parent = Parent::open(c, &base).map_err(|e| {
        format!(
            "Cannot authorize recovery file {}: {}",
            base.display(),
            io_error(&e)
        )
    })?;
    let (p, parent, mut f) = create_recovery(&base, parent).map_err(|e| {
        format!(
            "Emergency save failed for {} (create): {}; recovery file may be incomplete or not durable",
            base.display(),
            io_error(&e)
        )
    })?;
    let failure = |stage: &str, error: std::io::Error| {
        format!(
            "Emergency save failed for {} ({stage}): {}; recovery file may be incomplete or not durable",
            p.display(),
            io_error(&error)
        )
    };
    // Preserve even a partial recovery file on error: it may contain the only
    // surviving copy of edits. Never describe it as successfully written.
    f.write_all(&output(b, None, c.on(NO_NEWLINES)))
        .map_err(|e| failure("write", e))?;
    f.sync_all().map_err(|e| failure("file sync", e))?;
    native::close_checked(f).map_err(|e| failure("file close", e))?;
    parent
        .directory
        .sync_all()
        .map_err(|e| failure("directory sync", e))?;
    native::close_checked(parent.directory).map_err(|e| failure("directory close", e))?;
    Ok(Some(p))
}
fn create_recovery(base: &Path, parent: Parent) -> std::io::Result<(PathBuf, Parent, File)> {
    for i in 0..=99999 {
        let path = if i == 0 {
            base.to_path_buf()
        } else {
            config::path(&[base.as_os_str().as_bytes(), format!(".{i}").as_bytes()].concat())
        };
        let candidate = parent.sibling(PathBuf::from(
            path.file_name().ok_or(std::io::ErrorKind::InvalidInput)?,
        ))?;
        match candidate.create(0o600) {
            Ok(file) => return Ok((path, candidate, file)),
            Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => (),
            Err(e) => return Err(e),
        }
    }
    Err(std::io::ErrorKind::AlreadyExists.into())
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

// A backup output is always an exclusively created inode. Keep its identity
// through close so errors can clean up only the entry this operation created.
struct BackupOutput {
    stage_entry: Parent,
    content: Parent,
    target: Parent,
    file: Option<File>,
    identity: fs::Metadata,
    stage_identity: fs::Metadata,
}
impl BackupOutput {
    fn create(stage_entry: Parent, target: Parent) -> std::io::Result<Self> {
        native::private_entry_parent(&stage_entry.directory)?;
        let content = stage_entry.private_child()?;
        let stage_identity = content.directory.metadata()?;
        let file = match content.create(0o600) {
            Ok(file) => file,
            Err(error) => {
                if stage_entry.metadata().is_ok_and(|m| {
                    (m.dev(), m.ino()) == (stage_identity.dev(), stage_identity.ino())
                }) {
                    let _ = stage_entry.remove_directory();
                }
                return Err(error);
            }
        };
        let identity = match file.metadata() {
            Ok(identity) => identity,
            Err(error) => {
                drop(file);
                let _ = content.remove();
                if stage_entry.metadata().is_ok_and(|m| {
                    (m.dev(), m.ino()) == (stage_identity.dev(), stage_identity.ino())
                }) {
                    let _ = stage_entry.remove_directory();
                }
                return Err(error);
            }
        };
        Ok(Self {
            stage_entry,
            content,
            target,
            file: Some(file),
            identity,
            stage_identity,
        })
    }
    fn owns_stage(&self) -> bool {
        self.stage_entry.metadata().is_ok_and(|m| {
            (m.dev(), m.ino()) == (self.stage_identity.dev(), self.stage_identity.ino())
        })
    }
    fn owns_entry(&self) -> bool {
        self.content
            .metadata()
            .is_ok_and(|m| (m.dev(), m.ino()) == (self.identity.dev(), self.identity.ino()))
    }
    fn finish(mut self, replace: bool) -> std::io::Result<()> {
        native::close_checked(self.file.take().unwrap())?;
        if !self.owns_stage() || !self.owns_entry() {
            return Err(std::io::Error::other("Backup temporary entry changed"));
        }
        self.content.publish_to(&self.target, replace)?;
        if !replace {
            // linkat gives the home fallback its original exclusive-create
            // semantics, then removes the private source name.
            if !self.owns_entry() {
                return Err(std::io::Error::other("Backup temporary entry changed"));
            }
            self.content.remove()?;
        }
        self.content.directory.sync_all()?;
        self.target.directory.sync_all()?;
        if !self.owns_stage() {
            return Err(std::io::Error::other("Backup staging entry changed"));
        }
        self.stage_entry.remove_directory()?;
        self.target.directory.sync_all()
    }
}
impl Drop for BackupOutput {
    fn drop(&mut self) {
        if self.owns_entry() {
            let _ = self.content.remove();
        }
        if self.owns_stage() {
            let _ = self.stage_entry.remove_directory();
        }
    }
}

#[cfg(test)]
fn make_backup(
    c: &Config,
    path: &Path,
    meta: &fs::Metadata,
    warning: impl FnMut(&str),
) -> Result<(), WriteError> {
    let parent =
        Parent::open(c, path).map_err(|e| WriteError::writing(&path.display().to_string(), e))?;
    make_backup_from(c, path, &parent, meta, warning)
}
fn make_backup_from(
    c: &Config,
    path: &Path,
    parent: &Parent,
    _meta: &fs::Metadata,
    mut warning: impl FnMut(&str),
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
    let read_failed = std::cell::Cell::new(false);
    let write = |output: &mut BackupOutput, warning: &mut dyn FnMut(&str)| -> std::io::Result<()> {
        read_failed.set(false);
        // Source-open failures belong to the backup failure/confirmation flow,
        // just like read failures. Keep the read anchored to the opened parent.
        let source = parent.read().inspect_err(|_| read_failed.set(true))?;
        let meta = source.metadata()?;
        let file = output.file.as_mut().unwrap();
        let mut bytes = Vec::new();
        use std::os::unix::fs::FileExt;
        let mut offset = 0;
        let mut chunk = [0u8; 65536];
        loop {
            let n = source
                .read_at(&mut chunk, offset)
                .inspect_err(|_| read_failed.set(true))?;
            if n == 0 {
                break;
            }
            bytes.extend_from_slice(&chunk[..n]);
            offset += n as u64;
        }
        write_bytes(file, &bytes)?;
        // chown and content writes can clear set-ID bits. Apply the final mode
        // after both operations, then restore times and sync all metadata.
        if let Err(error) = native::file_chown(file, meta.uid(), meta.gid()) {
            if error.kind() == std::io::ErrorKind::PermissionDenied {
                let actual = file.metadata()?;
                if (actual.uid(), actual.gid()) != (meta.uid(), meta.gid()) {
                    warning("Cannot preserve backup ownership: Permission denied");
                }
            } else {
                return Err(error);
            }
        }
        file.set_permissions(fs::Permissions::from_mode(meta.mode() & 0o7777))?;
        file.set_times(
            std::fs::FileTimes::new()
                .set_accessed(meta.accessed()?)
                .set_modified(meta.modified()?),
        )?;
        file.sync_all()?;
        Ok(())
    };
    let target = if directory.is_empty() {
        let mut name = parent.name.as_os_str().as_bytes().to_vec();
        name.push(b'~');
        parent.sibling(config::path(&name))
    } else {
        Parent::open(c, &name)
    };
    let target = match target {
        Err(error) if confinement::enabled(c) => {
            return Err(WriteError::writing(&name.display().to_string(), error));
        }
        result => result,
    };
    static SERIAL: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
    let first = (|| {
        let target = target?;
        let source_dir = parent.directory.metadata()?;
        let target_dir = target.directory.metadata()?;
        if parent.name == target.name
            && (source_dir.dev(), source_dir.ino()) == (target_dir.dev(), target_dir.ino())
        {
            return Err(std::io::ErrorKind::InvalidInput.into());
        }
        // Even allow_insecure_backup must not truncate an existing object:
        // that object may be another name for the save destination.
        for _ in 0..1000 {
            let serial = SERIAL.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
            let leaf = PathBuf::from(format!(".naro-backup-{}-{serial}", std::process::id()));
            if leaf == parent.name || leaf == target.name {
                continue;
            }
            match BackupOutput::create(target.sibling(leaf)?, target.sibling(target.name.clone())?)
            {
                Ok(mut output) => {
                    write(&mut output, &mut warning)?;
                    return output.finish(true);
                }
                Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => continue,
                Err(e) => return Err(e),
            }
        }
        Err(std::io::ErrorKind::AlreadyExists.into())
    })();
    if first.is_ok() {
        return Ok(());
    }
    let mut last = first.unwrap_err();
    if !read_failed.get()
        && !confinement::enabled(c)
        && let Some(home) = config::home_dir()
    {
        warning("Cannot make regular backup");
        warning("Trying again in your home directory");
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
            let attempt = Parent::open(c, &home.join(config::path(&name))).and_then(|target| {
                let serial = SERIAL.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                let leaf = PathBuf::from(format!(".naro-backup-{}-{serial}", std::process::id()));
                BackupOutput::create(target.sibling(leaf)?, target)
            });
            match attempt {
                Ok(mut output) => {
                    let result =
                        write(&mut output, &mut warning).and_then(|()| output.finish(false));
                    match result {
                        Ok(()) => return Ok(()),
                        Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => continue,
                        Err(e) => {
                            last = e;
                            break;
                        }
                    }
                }
                Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => continue,
                Err(e) => {
                    last = e;
                    break;
                }
            }
        }
    }
    warning(if read_failed.get() {
        "Cannot read original file"
    } else {
        "Cannot make backup"
    });
    warning(&io_error(&last));
    Err(WriteError {
        message: format!("Cannot make backup: {}", io_error(&last)),
        confirm_backup: last.raw_os_error() != Some(28),
    })
}

#[cfg(test)]
#[path = "lock_tests.rs"]
mod lock_tests;

#[cfg(test)]
#[path = "safe_save_tests.rs"]
mod safe_save_tests;

#[cfg(test)]
#[path = "backup_tests.rs"]
mod backup_tests;

#[cfg(test)]
mod load_tests {
    use super::*;
    #[test]
    fn multiline_without_final_lf_loads_with_aligned_metadata() {
        let root = std::env::current_dir()
            .unwrap()
            .join("target/load-no-final-lf")
            .join(std::process::id().to_string());
        fs::create_dir_all(&root).unwrap();
        let path = root.join("ordinary.txt");
        fs::write(&path, b"first\nsecond").unwrap();
        let newline_modes: &[bool] = if cfg!(feature = "tiny") {
            &[false]
        } else {
            &[false, true]
        };
        for &nonew in newline_modes {
            let mut config = Config::new(false);
            config.set(NO_NEWLINES, nonew);
            let (buffer, _, _) = open(&config, path.as_os_str().as_bytes(), false).unwrap();
            assert_eq!(
                buffer.raw(),
                if nonew {
                    b"first\nsecond".as_slice()
                } else {
                    b"first\nsecond\n".as_slice()
                }
            );
            assert_eq!(buffer.state.lines.len(), buffer.state.anchors.len());
            assert_eq!(buffer.state.lines.len(), buffer.state.generations.len());
            assert!(!buffer.modified);
            assert_eq!(buffer.hist, 0);
        }
        fs::remove_dir_all(root).unwrap();
    }
}
