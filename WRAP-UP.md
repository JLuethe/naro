# Naro wrap up plan

Reviewed 2026-10-24. GNU nano reference commit:
`6ed285c3ec7a1d228def4d4e7021c6ba269f620c`.

Execution update: the initial snapshot below is historical. Its local changes
were pushed, spec 21 was added, the upload issue was fixed, and all 19 console
cases passed on both frozen optimized candidates. The final regression/package
gate now passes all 85 checks. Delivery/CI state is in `spec/98-progress.md` and
`validation/closure/README.md`. Resume from those checkpoints rather than
repeating the completed implementation or qualification work.

Finish the current console compatibility and Ubuntu packaging work, then deliver
one reproducible, tested preview with matching source, binary, evidence and GitHub
revision. The editor and behavioral specification already exist. This plan closes
the remaining validation and delivery work; it does not promise exhaustive GNU
nano equivalence, a tiny build, or physical hardware certification.

## Verified state

| Location | State at review |
| --- | --- |
| GitHub `JLuethe/naro`, branch `main` | `7d3e0b51c86858985ad7137add55acf3a0fac8c1`, identical to local HEAD. Latest Rust CI succeeded: [run 40128658257](https://github.com/JLuethe/naro/actions/runs/40128658257). No GitHub releases were listed. |
| Committed project | Behavioral spec, Rust editor and native bridge, regression harness, packaging and installation tools, root/home fixes, optional credits, GPL licensing and contribution/security documentation. |
| Local tracked changes | Six modified files: `native/bridge.c`, `src/{config,editor,input,native}.rs`, `.github/workflows/rust.yml`. These console fixes are not on GitHub. |
| Local untracked implementation files | `tests/console/`, `tests/follow-up/scenarios/vt-ioctl.json`, and `tools/{check_console_vm,console_vm,prepare_console_vm,run_console_vm}.py`. These also need review and inclusion. |
| Local ignored evidence | `spec/evidence/follow-up-runs/vt-*` and `target/ubuntu-root-refresh-v1/`. A clone does not contain these raw results or binaries. |
| Original reference | `~/src/nano-ref` remains clean at the full pinned commit. Do not modify it. |
| Active work | No QEMU test VM or named validation process was running at review. This plan is not a background job. |

GitHub CI certifies its committed revision and configured checks. It does not
certify the uncommitted console changes or replace the full local release gate.

## What is completed

The spec was built from the pinned source, documentation, generated inventories
and observed terminal behavior. The comparison harness checks screens, cursors,
visible attributes, files and exits with documented narrow normalization. It
preserves intentional differences instead of rewriting reference observations.

The committed root phase records 27 exact root/home comparisons and a separate
asserted recovery case for missing home information. Its ordinary corpus has
301/303 full matches and 302/303 file/exit matches, with the two original declared
safety differences. CLI checks pass 38/38 and regex checks 162/162. See
`validation/root-console/README.md` and its reports for exact binary attribution.

Earlier follow-up evidence covers external tools, recovery, assets, packaging,
installation and a second Linux userspace. Its 53 paired cases have 51 exact
matches and two explicitly asserted termination cleanup differences. Those
historical reports remain valid for their recorded binaries, not every later edit.

The new local console code addresses Linux VT modifiers, bindings/help labels,
combining-character display and macro replay. A disposable VM uses a genuine
guest Linux VT and emulated PS/2 keys. This exercises kernel console behavior
without taking over the host's active console. It is not a physical keyboard trial.

Local VM reports show 14/14 matches in `vt-after-v1`, two corrected macro matches
in `vt-macro-fixed`, and a buffer-switch match in `vt-horizontal-v2`. These runs
use different development snapshots and cannot be combined into a final release
pass. Early macro trials did not actually start recording; the corrected trials
add explicit recording and cursor assertions. The last ioctl-model report is
7/8; its macro input timing has since been corrected but not revalidated.

The Ubuntu root refresh completed and records 301/303 full matches, 302/303
file/exit matches, CLI 38/38 and regex 162/162. Its binary SHA-256 is
`720f806e3b2b42ac8ee4f01ecaefe329a1eebc84e788ddb9fafcd63453e04760`.
It predates the console fixes, so its package is not the final deliverable.

## Ordered completion steps

1. **Make the console harness reliable.** Review all local changes. Replace the
   oversized single-message VM binary upload with bounded chunks, size/hash
   verification and explicit completion. Clear abandoned partial messages on
   disconnect. Confirm reconnect behavior in the private VM fixture. The previous
   upload timed out and left an incomplete JSON message; this is an unfinished
   test transport issue, not evidence of an editor failure. Rerun the corrected
   eight ioctl cases and the three VM boundary tests. Add the boundary tests to
   CI. Exit criterion: all eight paired model cases and boundary checks pass;
   interrupted transfers cannot install an unverified binary.

2. **Freeze and qualify the console implementation.** Review the code against
   the pinned source, commit the implementation and test tools, and build an
   optimized candidate. Run all 19 VM cases together on that binary. Record
   source/candidate hashes, kernel, keymap, real VT identity, files, visible cells,
   cursor, and terminal/keyboard restoration. Preserve semantic macro assertions.
   Exit criterion: 19/19 matches with no unexplained differences. Keep physical
   keyboard/operator requirements deferred; do not relabel VM evidence as human
   hardware testing.

3. **Run the final regression on host and Ubuntu.** Use the frozen source for
   both builds. Run formatting, strict Clippy, Rust and harness tests, the 303-case
   corpus, CLI, regex, safety assertions, 53 follow-up cases, root/home cases,
   panic recovery, assets and large-file checks as applicable to each environment.
   Run root namespace cases on the host with the recorded root oracle; do not
   pretend an ordinary Ubuntu container proves root behavior. Preserve existing
   declared differences and exclusions. Reuse Ubuntu reference recordings only
   if source, environment and scenario hashes match; otherwise replay them.
   Run all 19 VM cases again using the final Ubuntu executable. Exit criterion:
   no new unexplained regressions, every required assertion passes, and every
   result identifies the tested executable. Any production change invalidates
   the affected release results and requires revalidation.

4. **Produce and verify the portable preview.** Package the tested Ubuntu
   executable and matching source archive, with checksums, build provenance,
   licensing, credits, assets and measured runtime requirements. Perform clean
   installation, all 41 catalog checks, syntax checks, offline source rebuild,
   archive validation and uninstall/conflict checks. Use a new output directory.
   Exit criterion: the packaged binary hash equals the tested Ubuntu hash, the
   source fingerprint matches the checkout, and package checks pass. Preserve
   previous artifacts as historical results.

5. **Close documentation and GitHub delivery.** Add compact tracked console and
   Ubuntu reports; retain raw logs locally and describe how to regenerate them.
   Update `IMPLEMENTATION.md`, README, spec coverage/progress/open questions and
   test matrices. Run the spec audit; retain the full reference hash at the top
   of spec documents. Mirror the finalized spec and relevant reports to
   `~/src/nano-rs` without deleting unrelated files. Commit and push the final
   evidence, verify remote HEAD and wait for its CI. Exit criterion: GitHub has
   all implementation and reproduction tools, local tracked state is clean, CI
   is green, and the completion report links the exact revision and artifacts.
   Creating a tag or publishing a GitHub Release remains a separate delivery
   decision; pushing source does not publish the ignored local archives.

## Scope remaining after this wrap up

Tiny mode stays optional and unimplemented. Physical keyboard/operator console
certification remains deferred. Other platforms, broader host-root behavior and
the source-specified runtime gaps in `spec/99-open-questions.md` remain outside
this preview's certification. List these explicitly in the completion report.
Do not describe spec completion as exhaustive runtime coverage.

## Durable checkpoints and interrupted threads

At the end of each numbered step, update `spec/98-progress.md` with the current
step, exact source commit, binary hashes, report paths, failures, active process
IDs if any, and the next command. Commit coherent completed changes and push
checkpoints under the existing authorization. Do not commit generated VM images
or large raw logs. Keep short reports and reproduction commands in GitHub.

Use fresh output directories, bounded subprocess lifetimes, and serial ownership
of a scenario ID. Do not edit a script while a running shell is consuming it.
All editor test input must remain in private fixtures. Never edit real user or
system files, alter the pinned reference, or seize the host console.

A replacement thread can start with:

> Continue Naro in `/home/john/Code/naro`. Read `WRAP-UP.md`, the latest section
> of `spec/98-progress.md`, and `git status` first. This is compatibility and
> packaging work for our text editor against the pinned GNU nano source. Use
> only private test fixtures and the disposable VM; preserve the reference and
> original evidence. Resume the first incomplete completion step, verify actual
> process and artifact state, and checkpoint results on disk after each step.

This is a continuity measure, not a way to bypass a safety restriction. If a
specific request is blocked, leave its status explicit and use the official
feedback/support route. Independent permitted work can proceed.

## Content cannot be shown message

OpenAI documents this as an additional automated safeguard. A notice does not
itself establish a policy violation, and I cannot determine which detail caused
the message in this session. For an allowed task, the official advice is to
retry with a narrower scope and the context necessary to explain the intended
outcome. Describe this project accurately as editor compatibility testing in
owned fixtures; do not conceal what a test does or change its purpose to avoid
a check. No wording guarantees that the message will disappear.

For repeated blocks of benign work, report the exact message, product/model,
date/time/time zone, request ID if available, workspace if applicable, and a
brief redacted task description. Do not include credentials. Daybreak is an
application route for authorized cybersecurity work, not a guaranteed fix or a
prerequisite established for this editor project; approval retains safeguards.
See [OpenAI's explanation and reporting instructions](https://help.openai.com/en/articles/20001326)
and [the application linked in the notice](https://openai.com/form/enterprise-trusted-access-for-cyber/).
