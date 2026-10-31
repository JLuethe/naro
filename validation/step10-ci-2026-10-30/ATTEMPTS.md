# Step 10 attempts

- First host diagnostic attempt could not open the private tmux socket under
  the sandbox. No editor launched. Original error log and summary retained.
  Retried as attempt02 with permission for private tmux use and distinct roots.
- Two editing preflight scripts aborted on formatting assertions before writing
  anything. The first full host/Ubuntu runs consequently used original scenarios;
  they are retained as unmodified controls and both passed 40/40. They are not
  relabeled as synchronized-scenario runs.
- The narrow edit was then applied and verified structurally. New full-suite
  directories contain the synchronized case: host 40/40, Ubuntu 40/40, each with
  both harness statuses zero and complete evidence validation.
- Across four executables (host/Ubuntu NARO and their own nano references), all
  four zero-delay original controls passed, eight delayed original cases failed
  only their saved cursor, and all twelve synchronized cases passed. These eight
  failures are expected diagnostic reproductions, not accepted qualification.
- The intentionally short save-wait deadline failed steps_ok and the cursor as
  required. This is an expected negative control, not a passing editor scenario.
- No original evidence, source freeze, executable, comparator or expectation was
  changed. No CI rerun was used to erase an earlier failure.
