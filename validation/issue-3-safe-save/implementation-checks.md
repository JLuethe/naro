# Issue #3 implementation agent checks

Date: 2026-11-05. Working directory: `/home/john/Code/naro`.
This records commands executed by the production implementation agent. Other
agents' broader validation is recorded separately. These checks do not constitute
final release qualification. No commit, push, installation, or publication was
performed by this agent.

## Implementation decisions

Production edits are in `src/files.rs`, `src/native.rs`, and `native/bridge.c`.
Regular-file overwrite, append, prepend, and selection saves use a same-directory
exclusive temporary file. The transaction writes the entire result, preserves
metadata, syncs and checks close of the temporary file, atomically renames it,
then syncs and checks close of the containing directory. Writes and file syncs
retry EINTR; close is not retried because Linux releases the descriptor even on
an interrupted close. No pre-rename operation truncates the destination.

Errors after rename explicitly report uncertain durability. Errors do not advance
the buffer's saved state. Final-component symlinks are deliberately rejected,
including dangling symlinks; hard-link saves replace only the named entry.
Linux owner/group, mode, extended attributes, and POSIX ACLs must be preserved
or replacement fails. Existing-file replacement on unsupported metadata
platforms fails closed. Append and prepend require read/write access to the
original; prepend rejects missing sources. FIFO streaming remains an exception,
with checked close and an incomplete-output warning on stream errors.

Temporary files use `.naro-save-<pid>-<serial>`. Exclusive creation avoids
collisions; a generated basename equal to the destination is skipped. Temporary
device/inode identity is checked before rename and error cleanup. The directory
descriptor anchors subsequent path operations. These checks do not claim a
complete adversarial namespace/confinement solution for separate issue #12.
Uncatchable termination may leave an unpublished temporary file.

Review corrections included nonzero storage capacity for second xattr queries,
so zero-length attributes/lists cannot produce uninitialized reads on concurrent
growth, and the temporary/destination basename collision guard.

## Commands executed

The commands below are the shell command text actually dispatched, in order.
Some inspection commands intentionally returned nonzero because optional paths
or search matches were absent. Calls aborted before dispatch are not commands
executed and are not included. Source changes and this record were written with
the `apply_patch` tool rather than shell commands.

1. Repository/document discovery; exit 0:

   ```sh
   pwd && rg --files -g 'AGENTS.md' -g 'CONTRIBUTING.md' -g '08-files.md'
   ```

2. Read contributor/spec requirements, look for agent instructions, inspect
   initial file-writing implementation; final command exit 0. `find` reported
   permission denials in three unrelated sibling QA fixture directories:

   ```sh
   cat CONTRIBUTING.md spec/08-files.md; find .. -name AGENTS.md -print; sed -n '1,280p' src/files.rs
   ```

3. Inspect remaining file code, native interfaces, and optional ancestor agent
   instructions; exit 1 from the final absent-file `cat`:

   ```sh
   sed -n '280,600p' src/files.rs; rg -n 'open_write|test_hook|write_bytes|close|xattr' src/native.rs native/bridge.c src/files.rs Cargo.toml; cat /home/john/AGENTS.md /home/john/Code/AGENTS.md /home/john/Code/naro/AGENTS.md 2>/dev/null
   ```

4. Inspect native bridge, wrappers, features, and potential test-hook files;
   exit 2 because the `native/test*` and `tests/*hook*` globs had no matching files:

   ```sh
   sed -n '1,200p' native/bridge.c; sed -n '1,140p' src/native.rs; cat Cargo.toml; rg -n 'SAVE|save|sync|close|write' native/test* tests/*hook* build.rs
   ```

5. Inspect build configuration and repository status; exit 0. Existing untracked
   user files were left untouched:

   ```sh
   cat build.rs; rg -n '\[cfg\(test\)\]|mod tests' src/files.rs; git status --short
   ```

6. Verify that an interrupted tool call had not applied the C patch; exit 1,
   no matches:

   ```sh
   rg -n 'save_write|stdatomic' native/bridge.c
   ```

7. Verify that an interrupted tool call had not applied the Rust wrapper;
   exit 1, no matches:

   ```sh
   rg -n nr_safe_save src/native.rs
   ```

8. Format and compile the focused test; exit 101. Formatting succeeded. Test
   compilation found the test agent's obsolete `error.errno` reference after
   production removed that unused field. The test agent corrected it:

   ```sh
   /home/john/.cargo/bin/cargo fmt && /home/john/.cargo/bin/cargo test safe_save -- --nocapture
   ```

9. Check production compilation and inspect policy/test integration; exit 0.
   `cargo check` passed:

   ```sh
   /home/john/.cargo/bin/cargo check; cat docs/safe-save.md; sed -n '1,90p' src/safe_save_tests.rs
   ```

10. Recompile/run the focused test entry; exit 0, one test passed. Without
    `NARO_SAVE_FIXTURE`, this entry returns immediately: this invocation proves
    compilation/integration, not a real filesystem save. Real saves follow below
    and in the separate fault-matrix report:

    ```sh
    /home/john/.cargo/bin/cargo test safe_save -- --nocapture
    ```

11. Inspect the integrated Rust changes and fault-matrix driver; exit 0:

    ```sh
    git diff -- src/files.rs src/native.rs; sed -n '1,180p' tests/safe-save/run.py
    ```

12. Recheck production compilation after the temporary/destination basename
    collision guard; exit 0:

    ```sh
    /home/john/.cargo/bin/cargo check
    ```

13. Execute actual overwrite, append, and prepend through `files::write` in
    disposable synthetic fixtures; exit 0. Each case checked exact contents,
    replacement inode, preserved mode, and removal of temporary entries.
    The already-built test executable predates the basename-collision-only
    correction; that edge is covered by the separate regression matrix.

    ```sh
    python3 - <<'PY'
    import os, pathlib, subprocess, tempfile
    binary=pathlib.Path('target/debug/deps/naro-f143b0d4013ffd62').resolve()
    for mode in range(3):
        with tempfile.TemporaryDirectory(prefix='naro-safe-save-check-') as root:
            target=pathlib.Path(root)/'data'/'target'
            target.parent.mkdir()
            target.write_bytes(b'old\n')
            target.chmod(0o640)
            old=target.stat()
            env=dict(os.environ, NARO_SAVE_FIXTURE=root, NARO_SAVE_MODE=str(mode))
            subprocess.run([binary,'--exact','files::safe_save_tests::fixture_save'],env=env,check=True,stdout=subprocess.DEVNULL)
            expected=[b'replacement\n',b'old\nreplacement\n',b'replacement\nold\n'][mode]
            assert target.read_bytes()==expected
            assert target.stat().st_ino!=old.st_ino
            assert target.stat().st_mode==old.st_mode
            assert list(target.parent.iterdir())==[target]
            print(mode, (pathlib.Path(root)/'result').read_text().strip())
    PY
    ```

    Observed output:

    ```text
    0 ok 1 modified=false
    1 ok 1 modified=true
    2 ok 1 modified=true
    ```

The independent reviewer separately reported clean formatting/diff checks and
warning-as-error C syntax checks for default and tiny builds, with no remaining
production correctness finding at that review point. Those commands were run
by the reviewer, not this agent. Fault injection, interruption-boundary checks,
broader feature/build tests, and terminal suites are owned by the other agents;
their results must be consulted before any final qualification claim.
