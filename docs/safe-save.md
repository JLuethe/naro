# Safe saves (issue #3)

NARO saves regular files by replacement. This is an intentional safety
change from nano's in-place writing and from NARO 0.1.1. There is no opt-in
in-place mode for regular files: preserving inode identity is not sufficient
justification for exposing the old contents to truncation on an I/O failure.

The save creates a unique temporary file in the destination directory, writes
the complete result, applies metadata, syncs and closes the file, replaces the
named destination, then syncs the directory. A successful save requires all
these operations to succeed. The rename is the commit point. Failures before
that point leave the destination's bytes and pathname unchanged; errors after
rename explicitly report that replacement happened but durability is uncertain.
The buffer remains modified on failure, including directory-sync failure.
For regular files, `Writing...` is painted before entering the transaction,
including before opening the existing file and temporary file. This is earlier
than nano's progress message on an open failure; the cursor is hidden while
the transaction is in progress.

The directory must permit creating and replacing directory entries. A writable
file in a non-writable directory can no longer be saved through its existing
name. Filesystems that cannot support the required operations fail closed;
NARO does not silently revert to truncating the original.

## Compatibility policy

- Existing regular files retain numeric owner/group and permission bits.
  Linux extended attributes, including POSIX ACLs, must be copied successfully;
  failures abort replacement. This may refuse a save that nano would permit.
  Existing-file metadata preservation currently supports Linux; other native
  platforms reject replacement rather than silently discard metadata.
- New files use creation permissions subject to the process umask and directory
  inheritance. Existing-file modification time changes on successful save;
  inode change time and creation identity are those of the new inode. NARO does
  not promise to restore old access/modification timestamps.
- A symbolic link in the final pathname component is rejected, whether its
  target exists or not. Open the actual target pathname to save it. The link
  itself and its target are left intact. Ancestor directory symlinks are not
  a complete operating-directory confinement boundary; issue #12 is separate.
- Saving one name of a multiply linked file creates a new inode for that name.
  Other hard links retain the original contents and inode. Existing open file
  descriptors also continue to reference the old inode.
- Append builds old bytes followed by the buffer's output; prepend builds the
  buffer's output followed by old bytes. Both commit using the same replacement
  transaction. Append may create a missing file; prepend requires an existing,
  readable source. Append is no longer an atomic `O_APPEND` operation relative
  to concurrent appenders. Concurrent writers require external coordination.
  Both operations require read and write access to the existing source.
- Selection saves use the same transaction without marking the whole buffer
  saved. Formatting, backup selection and line counting retain their existing
  behavior. Backups are separate operations and may have changed on a failed
  save; the original-file preservation guarantee is about the destination.
- FIFOs remain a streaming compatibility exception: they cannot be replaced
  safely with regular files. A stream error reports potentially incomplete
  output. Prepending to a FIFO remains rejected. No filesystem durability is
  promised for data delivered to a FIFO reader.

## Failure and interruption limits

Positive short writes are completed and interrupted I/O is handled explicitly.
Write, metadata, file-sync, close and rename failures abort before replacement.
Directory-sync errors cannot roll back a committed rename safely, so they are
reported as uncertain durability rather than success or original preservation.
Errors closing the directory after sync receive the same conservative report.

Ordinary error cleanup removes only the transaction's own temporary entry.
Uncatchable termination or power loss can leave a temporary file; NARO does
not scan for and delete names belonging to unrelated processes. Before rename,
the original remains intact. After rename, readers see the complete replacement;
persistence across power loss is established only after directory sync succeeds.
Tests at deterministic boundaries do not simulate every filesystem, storage
controller or power-loss behavior.

Historical nano comparisons that require truncation, inode preservation or
hard-link propagation are evidence of the old compatibility behavior, not
proof of the new safety contract. New semantic assertions must check the
chosen policy without weakening the shared comparison or normalization rules.
