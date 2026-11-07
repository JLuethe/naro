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
source checks, staging-directory creation, replacement, and directory sync are relative
to that parent. The temporary file is created within a unique mode-0700 child
of the opened parent. Saves refuse a parent owned by an untrusted UID, or one
with group/other write permission and no sticky bit, before creating that child.
The held child descriptor remains the publication source after a same-UID
entry change in an otherwise authorized parent.
A missing final filename is allowed only after its existing
parent has been opened successfully. Other resolution errors deny access.
Backups read a pinned source descriptor and create a private staging child in
an authorized opened parent. Publication uses the held child descriptor.
Confined backups never fall back to the home directory and
always use exclusive creation, including with `allow_insecure_backup` enabled.
An explicitly configured backup directory must also be within the root.
Backup publication additionally refuses a parent whose owner/sticky permission
policy would allow another UID to substitute the temporary entry before rename;
the same rule applies without confinement.
Lock creation/removal and recovery creation/sync retain their parent descriptor.
Browser and completion enumeration use an authorized directory stream; displayed
names are reauthorized when selected. Browser metadata uses authorized opens.
Syntax filename regexes use the canonical absolute name obtained from an
authorized descriptor's `/proc/self/fd` link, including the resolved target of
a supported relative symlink. If that name cannot be obtained (including for a
new file), they use the supplied filename, as nano does after failed canonical
resolution. The resolved string is used only for matching; internal libmagic
reads acquire their own authorized descriptor through the original filename.

The symlink policy is deliberate:

- Reads and directory traversal support relative symlinks whose whole resolution
  stays under the operating root. Absolute symlinks are refused, even if their
  target text names a location inside the root. Kernel magic links are refused.
- Final-component save symlinks observed during validation are refused; save the
  target's path explicitly. Saves never follow a final symlink. A symlink inserted
  after the final validation can itself be replaced by publication, just like any
  concurrent final-entry replacement; this is not a compare-and-swap guarantee.
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

The private staging child protects its contents from an actor with a distinct
UID. A non-sticky parent writable by that actor is refused because it could
replace the child entry before NARO opens it. An editor-owned or root-owned
sticky parent protects the editor-owned child entry; a foreign unprivileged
owner could move entries despite sticky protection and is refused. POSIX ACL
named-user and group write grants are reflected in the group mode mask and
trigger the same conservative rule. A process with the editor's UID can access
the private directory and remains outside this filesystem permission boundary.
The staging child remains on the destination filesystem; ordinary cleanup
checks entry identities and does not remove substitutions it observes.

This feature is not a process sandbox. Configuration files, history storage,
external commands and tools, their temporary files, and their own filesystem
access remain governed by their existing trust and permission policies. In
particular, invoking a formatter, speller or command grants that program the
editor process's ordinary operating-system authority.

The bounded issue #12 fixtures exercise controlled parent, staging, and final-entry swaps
at source open, temporary creation, final publication, and confined read reopen.
They support the opened-object policy for those interleavings and demonstrate
the final-entry compare-and-swap limit; they do not establish exhaustive race
safety or an exploited vulnerability. See
[validation](../validation/issue-12-confinement/README.md).
