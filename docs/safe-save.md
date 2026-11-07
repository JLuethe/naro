# Safe saves (issue #3)

NARO saves regular files by replacement. This is an intentional safety
change from nano's in-place writing and from NARO 0.1.1. There is no opt-in
in-place mode for regular files: preserving inode identity is not sufficient
justification for exposing the old contents to truncation on an I/O failure.

The save creates a unique private mode-0700 staging directory directly under
the opened destination directory, then exclusively creates its temporary file
inside that child. This keeps the temporary entry inaccessible to a different
user in an authorized destination directory. The child and
destination are on the same filesystem, so publication by `renameat` remains
atomic. The save writes the complete result, applies metadata, syncs and closes
the file, replaces the named destination from the held staging-directory
descriptor, syncs the staging directory and destination directory, removes the
empty staging directory, and syncs the destination directory again. A successful
save requires all these operations to succeed. The rename is the commit point. Failures before
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

Before staging, NARO requires an opened destination parent owned by the editor
or root. If the parent has group or other write permission, it must also have
the sticky bit. These checks use the opened directory's mode; its group mode
bits include the effective POSIX ACL mask, so a named ACL writer is treated
conservatively. An ordinary mode-0777 directory without sticky protection is
refused even when the editor owns it. An editor-owned private directory and a
trusted-owner sticky directory can still be saved in. This restriction prevents
a different UID from replacing the newly created staging directory with an
unrelated editor-owned directory before NARO opens it. It is a compatibility
restriction for shared writable directories; choose a private directory or a
sticky directory owned by the editor or root.

## Compatibility policy

- Existing regular files retain numeric owner/group and permission bits.
  Linux extended attributes, including POSIX ACLs, must be copied successfully;
  failures abort replacement. This may refuse a save that nano would permit.
  Existing-file metadata preservation currently supports Linux; other native
  platforms reject replacement rather than silently discard metadata.
- New files use creation permissions subject to the process umask and default
  ACL inherited by the private staging directory from the destination parent.
  The private directory is narrowed to mode 0700, and its file receives the
  same parent default ACL and resulting mode as a direct child would on Linux.
  Existing-file modification time changes on successful save;
  inode change time and creation identity are those of the new inode. NARO does
  not promise to restore old access/modification timestamps.
- A symbolic link observed in the final pathname component during validation
  is rejected, whether its target exists or not. Open the actual target
  pathname to save it. Saves never follow a final symlink. A symlink inserted
  after final validation can itself be replaced by publication, but its
  referent is not written. Final-entry publication is not a compare-and-swap
  transaction; the bounded issue #12 tests document this limit.
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
- Lock cleanup and refresh retain the created lock's opened descriptor and
  check its device/inode against the current directory entry before unlinking.
  Saving under the buffer's old lock pathname therefore preserves the committed
  document, records its metadata and marks the buffer saved. A replaced lock
  entry is preserved; a failed refresh continues without owning a lock. A new
  sidecar is created exclusively. An existing sidecar at a save-as destination
  is preserved and reported as a warning; the document save still succeeds.
  Replacing an unowned lock requires explicitly accepting the lock-conflict
  question when opening a buffer.
- FIFOs remain a streaming compatibility exception: they cannot be replaced
  safely with regular files. A stream error reports potentially incomplete
  output. Prepending to a FIFO remains rejected. No filesystem durability is
  promised for data delivered to a FIFO reader.

## Backup safety

Backup output is written to a newly and exclusively created file, with the
existing owner/group, permission and timestamp handling. The normal backup is
published from a sibling temporary file only after its contents and metadata
are synced and its close succeeds, then the backup directory is synced. An
opened backup parent must pass the same owner/sticky permission check as the
document save parent before temporary creation. Its owner must be the editor
or root; group or other write permission requires a sticky bit. The group mode
bits include the POSIX ACL mask. This applies to configured backup directories
and to the home-directory fallback. It prevents a different UID from moving
the temporary entry after its identity check and substituting a backup that
would be published by rename. A private child is unnecessary in an authorized
parent: the temporary file is mode 0600, and a different UID cannot move its
entry. A nonsticky shared configured backup directory triggers the existing
home fallback when allowed; confined saves and failed fallbacks use the backup
confirmation flow. Use an editor-owned private directory or a trusted-owner
sticky directory. An existing backup entry is replaced by rename; its inode is
never opened for writing, even with `allow_insecure_backup`. Hard links and symbolic links at
the backup name therefore cannot redirect output into the save destination or
another existing file. The option remains accepted for configuration
compatibility, but does not enable truncating existing backup objects.

A failed unpublished attempt retains any previous backup. Error cleanup checks
the created entry's identity before removing it, and leaves colliding or
substituted entries alone. The existing home-directory fallback uses exclusive
creation and the same checked write, metadata, sync and close handling. Backup
failures retain the existing confirmation flow. A published backup, including
one whose directory sync failed, may remain after a failed save or fallback;
that side effect never permits changing the destination before the save's own
rename commit point.

## Failure and interruption limits

Positive short writes are completed and interrupted I/O is handled explicitly.
Write, metadata, file-sync, close and rename failures abort before replacement.
Directory-sync errors cannot roll back a committed rename safely, so they are
reported as uncertain durability rather than success or original preservation.
Errors closing the directory after sync receive the same conservative report.

Ordinary error cleanup removes only the transaction's own temporary entry and
staging directory, after checking their identities. A replaced staging entry
is left alone. Uncatchable termination or power loss can leave a private
staging directory, with a `content` file before publication or empty after it.
NARO does not scan for and delete names belonging to unrelated processes.
Before rename, the original remains intact. After rename, readers see the
complete replacement. The file-then-directory fsync sequence is the intended
Linux durability contract; successful calls are required before reporting
success. These tests do not establish persistence after an actual power cut on
any particular filesystem, controller, or device.

Historical nano comparisons that require truncation, inode preservation or
hard-link propagation are evidence of the old compatibility behavior, not
proof of the new safety contract. New semantic assertions must check the
chosen policy without weakening the shared comparison or normalization rules.
