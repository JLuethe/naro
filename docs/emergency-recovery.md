# Emergency recovery durability

For a modified buffer outside restricted mode, NARO creates a new mode-0600
recovery file using the existing `.save`, `.save.1`, … naming policy. It writes
the buffer, syncs the file, checks file close, syncs the containing directory,
and checks directory close before printing `Buffer written to …`.

Any failed step reports `Emergency save failed for <path> (<stage>): <reason>`
on stderr after terminal restoration. The diagnostic identifies create, write,
file sync, file close, directory open, directory sync or directory close and
warns that recovery may be incomplete or not durable. Failed recovery does not
print the success message. Other buffers still get their recovery attempt.

The created recovery file is retained on failure because even partial bytes may
be the only surviving copy of edits. A sync or close error can leave all bytes
visible while their persistence remains uncertain. The original file is never
overwritten by emergency recovery. Restricted and unmodified buffers remain
silent skips; abnormal exit retains status 1.

This intentionally improves on the pinned nano reference's invisible recovery
errors. It does not certify power-loss behavior on every filesystem or storage
device, address concurrent namespace changes, or change collision-name policy.
See the [regression driver](../tests/recovery/README.md) and
[issue #4 evidence](../validation/issue-4-recovery/README.md).
