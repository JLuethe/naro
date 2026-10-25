//! Narrow safe wrappers around the opaque native ABI.
use std::{
    ffi::{CStr, CString, c_char, c_int, c_void},
    ptr::NonNull,
};
unsafe extern "C" {
    pub fn nr_position(
        lw: c_int,
        line: usize,
        lines: usize,
        lp: c_int,
        col: usize,
        cols: usize,
        cp: c_int,
        cw: c_int,
        count: usize,
        total: usize,
        hp: c_int,
    ) -> *const c_char;
    pub fn nr_signal() -> c_int;
    pub fn nr_locale(path: *const c_char) -> c_int;
    fn nr_tr(s: *const c_char) -> *const c_char;
    fn nr_plural(a: *const c_char, b: *const c_char, n: usize) -> *const c_char;
    pub fn nr_width(ch: u32) -> c_int;
    pub fn nr_class(ch: u32, kind: c_int) -> c_int;
    pub fn nr_lower(ch: u32) -> u32;
    pub fn nr_byte_lower(b: i32) -> i32;
    pub fn nr_tty(fd: c_int) -> c_int;
    pub fn nr_reconnect() -> c_int;
    fn nr_host() -> *const c_char;
    fn nr_user() -> *const c_char;
    fn nr_current_home() -> *const c_char;
    fn nr_home(name: *const c_char) -> *const c_char;
    pub fn nr_option(argc: c_int, argv: *mut *mut c_char) -> c_int;
    pub fn nr_optarg() -> *const c_char;
    pub fn nr_optind() -> c_int;
    pub fn nr_setup_signals();
    pub fn nr_configure(preserve: c_int, rawseq: c_int);
    pub fn nr_init(preserve: c_int, rawseq: c_int) -> c_int;
    pub fn nr_done();
    pub fn nr_resume(preserve: c_int);
    pub fn nr_resize();
    pub fn nr_rows() -> c_int;
    pub fn nr_cols() -> c_int;
    pub fn nr_colors() -> c_int;
    pub fn nr_collate(a: *const c_char, b: *const c_char) -> c_int;
    pub fn nr_print_byte(b: c_int) -> c_int;
    #[cfg(not(feature = "tiny"))]
    pub fn nr_child_signals();
    pub fn nr_erase();
    pub fn nr_finish(start: c_int);
    pub fn nr_refresh(row: c_int, col: c_int, visible: c_int);
    pub fn nr_beep();
    pub fn nr_get(ms: c_int) -> c_int;
    pub fn nr_keypad(yes: c_int);
    pub fn nr_paste(yes: c_int);
    pub fn nr_mouse(yes: c_int);
    #[cfg(not(feature = "tiny"))]
    pub fn nr_mouse_event(x: *mut c_int, y: *mut c_int) -> c_int;
    pub fn nr_put(
        y: c_int,
        x: c_int,
        chars: *const u32,
        count: c_int,
        style: c_int,
        fg: c_int,
        bg: c_int,
    );
    pub fn nr_on_vt() -> c_int;
    pub fn nr_vt_key(key: c_int, meta: c_int, shift: *mut c_int) -> c_int;
    pub fn nr_map(key: c_int) -> c_int;
    fn nr_regex(
        pattern: *const c_char,
        flags: c_int,
        error: *mut c_char,
        cap: usize,
    ) -> *mut c_void;
    fn nr_match(
        re: *mut c_void,
        text: *const c_char,
        len: usize,
        start: usize,
        notbol: c_int,
        pairs: *mut c_int,
        count: c_int,
    ) -> c_int;
    fn nr_nsub(re: *mut c_void) -> c_int;
    fn nr_regex_free(re: *mut c_void);
    fn nr_magic(path: *const c_char) -> *const c_char;
    pub fn nr_stop();
}
pub fn cstr(s: &[u8]) -> CString {
    CString::new(s).unwrap_or_default()
}
pub unsafe fn from_c(p: *const c_char) -> Vec<u8> {
    if p.is_null() {
        Vec::new()
    } else {
        unsafe { CStr::from_ptr(p) }.to_bytes().to_vec()
    }
}
pub fn tr(s: &str) -> String {
    let s = cstr(s.as_bytes());
    String::from_utf8_lossy(&unsafe { from_c(nr_tr(s.as_ptr())) }).into_owned()
}
pub fn plural(a: &str, b: &str, n: usize) -> String {
    let a = cstr(a.as_bytes());
    let b = cstr(b.as_bytes());
    String::from_utf8_lossy(&unsafe { from_c(nr_plural(a.as_ptr(), b.as_ptr(), n)) }).into_owned()
}
pub fn host() -> Vec<u8> {
    unsafe { from_c(nr_host()) }
}
pub fn user() -> Vec<u8> {
    unsafe { from_c(nr_user()) }
}
pub fn home(name: &[u8]) -> Vec<u8> {
    let s = cstr(name);
    unsafe { from_c(nr_home(s.as_ptr())) }
}
pub fn current_home() -> Option<Vec<u8>> {
    let home = unsafe { nr_current_home() };
    if home.is_null() {
        None
    } else {
        Some(unsafe { from_c(home) })
    }
}
pub fn magic(path: &[u8]) -> Vec<u8> {
    let s = cstr(path);
    unsafe { from_c(nr_magic(s.as_ptr())) }
}
pub struct Regex {
    ptr: NonNull<c_void>,
    pub groups: usize,
}
impl std::fmt::Debug for Regex {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Regex")
            .field("groups", &self.groups)
            .finish()
    }
}
impl Regex {
    pub fn new(pattern: &[u8], icase: bool) -> Result<Self, String> {
        Self::flags(pattern, 1 | if icase { 2 } else { 0 })
    }
    pub fn flags(pattern: &[u8], flags: i32) -> Result<Self, String> {
        let p = CString::new(pattern).map_err(|_| "NUL in regex".to_string())?;
        let mut error = [0i8; 512];
        let raw = unsafe { nr_regex(p.as_ptr(), flags, error.as_mut_ptr(), error.len()) };
        let ptr = NonNull::new(raw).ok_or_else(|| {
            String::from_utf8_lossy(&unsafe { from_c(error.as_ptr()) }).into_owned()
        })?;
        Ok(Self {
            ptr,
            groups: unsafe { nr_nsub(raw) }.max(0) as usize,
        })
    }
    pub fn find(&self, text: &[u8], start: usize, notbol: bool) -> Option<Vec<(usize, usize)>> {
        if start > text.len() {
            return None;
        }
        let mut t = text.to_vec();
        t.push(0);
        let mut pairs = [-1i32; 20];
        let count = (self.groups + 1).min(10);
        let ret = unsafe {
            nr_match(
                self.ptr.as_ptr(),
                t.as_ptr() as *const c_char,
                text.len(),
                start,
                notbol as i32,
                pairs.as_mut_ptr(),
                count as i32,
            )
        };
        if ret != 0 {
            return None;
        }
        Some(
            pairs[..count * 2]
                .as_chunks::<2>()
                .0
                .iter()
                .map(|p| {
                    if p[0] < 0 {
                        (usize::MAX, usize::MAX)
                    } else {
                        (p[0] as usize, p[1] as usize)
                    }
                })
                .collect(),
        )
    }
}
impl Drop for Regex {
    fn drop(&mut self) {
        unsafe { nr_regex_free(self.ptr.as_ptr()) }
    }
}
pub struct Terminal;
impl Terminal {
    pub fn new(preserve: bool, rawseq: bool) -> Result<Self, String> {
        if unsafe { nr_init(preserve as i32, rawseq as i32) } == 0 {
            Err("Cannot initialize terminal".into())
        } else {
            Ok(Self)
        }
    }
}
impl Drop for Terminal {
    fn drop(&mut self) {
        unsafe { nr_done() }
    }
}
