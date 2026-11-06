# Operating-directory file authorization

NARO's `--operatingdir` (`-o`) uses an opened directory as its root of file
selection authority. Startup pins that directory and changes directory through
its descriptor. Confined lookups require Linux `openat2` with `RESOLVE_BENEATH`
and `RESOLVE_NO_MAGICLINKS`. Data reads first identify a regular file using
`O_PATH`, then reopen that held descriptor through Linux `/proc/self/fd`; procfs
access is therefore also required. If the kernel, build headers, or process policy do
not support this operation, requesting an operating directory fails with an
error. There is no pathname-only fallback. Ordinary usage without an operating
directory remains supported. Tiny does not offer the operating-directory option.

Loads and insertion obtain data and metadata from the same authorized open file.
Regular saves retain an authorized parent and pass it to the atomic save path;
source checks, temporary creation, replacement, and directory sync are relative
to that parent. A missing final filename is allowed only after its existing
parent has been opened successfully. Other resolution errors deny access.
Backups read a pinned source descriptor and, when confined, create in an
authorized parent. Confined backups never fall back to the home directory and
always use exclusive creation, including with `allow_insecure_backup` enabled.
An explicitly configured backup directory must also be within the root.
Lock creation/removal and recovery creation/sync retain their parent descriptor.
Browser and completion enumeration use an authorized directory stream; displayed
names are reauthorized when selected. Browser metadata uses authorized opens.

The symlink policy is deliberate:

- Reads and directory traversal support relative symlinks whose whole resolution
  stays under the operating root. Absolute symlinks are refused, even if their
  target text names a location inside the root. Kernel magic links are refused.
- Final-component save symlinks remain refused; save the target's path explicitly.
  Atomic saves replace one directory entry, preserving other hard links as
  described in [the safe-save policy](safe-save.md).
- Confined file reads accept regular files only. FIFO and device data reads are
  refused before a data open, so a FIFO cannot hang authorization. Confined
  FIFO writes are also refused. Ordinary unconfined FIFO behavior is unchanged.

This is authorization at lookup/open time. An opened directory remains the
same authorized object if it is subsequently renamed; retained descriptors do
not enforce permanent namespace ancestry. Other processes can still change or
remove directory entries, and replacement is not a general compare-and-swap
transaction against concurrent writers. Hard links and mounts already present
inside the root are part of its accessible namespace.

This feature is not a process sandbox. Configuration files, history storage,
external commands and tools, their temporary files, and their own filesystem
access remain governed by their existing trust and permission policies. In
particular, invoking a formatter, speller or command grants that program the
editor process's ordinary operating-system authority.

The issue #12 review remains a source-supported hypothesis: this change supplies
defensive authorization and ordinary fixture coverage, not evidence that a
pathname race was exploited. No entry-swapping or adversarial race reproducer
was constructed or run. See [validation](../validation/issue-12-confinement/README.md).
