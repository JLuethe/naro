# Post-fix Daybreak command record

The outer Daybreak invocation is in [README.md](README.md). The following are
the 39 qualification commands recorded inside the run. Exit 0 means passed.
Nonzero attempts are retained and classified; every one was superseded as noted.

1. `git clone --no-local --no-checkout . target/daybreak-blue-postfix-20261106T094550Z/clone` — exit 0.
2. `python3 /home/john/Code/naro/target/daybreak-blue-postfix-20261106T094550Z/preflight.py` — exit 2; wrong relative creation path, superseded by 3.
3. Same absolute preflight command after creating the script at the correct path — exit 0.
4. `python3 tools/test_package_docs.py` — exit 0; 8/8.
5. `python3 tools/test_package_provenance.py` — exit 0; 8/8.
6. `python3 tools/test_installer_transactions.py --report target/daybreak-blue-postfix-20261106T094550Z/installer-transactions.json` — exit 0; 16/16.
7. `cargo fmt --check` — exit 0.
8. `cargo clippy --locked --offline --all-targets --all-features --target-dir target/daybreak-blue-postfix-20261106T094550Z/cargo-target -- -D warnings` — exit 0.
9. `cargo clippy --locked --offline --all-targets --no-default-features --features tiny --target-dir target/daybreak-blue-postfix-20261106T094550Z/cargo-target -- -D warnings` — exit 0.
10. `cargo test --locked --offline --target-dir target/daybreak-blue-postfix-20261106T094550Z/cargo-target` — exit 101; sandbox supplementary-GID prerequisite, superseded by 14.
11. `cargo test --locked --offline --no-default-features --features tiny --target-dir target/daybreak-blue-postfix-20261106T094550Z/cargo-target` — exit 101; same prerequisite, superseded by 15.
12. `cargo test --locked --offline --all-features --target-dir target/daybreak-blue-postfix-20261106T094550Z/cargo-target` — exit 101; same prerequisite, superseded by 16.
13. `python3 -m unittest discover -s spec/tools -p 'test_*.py'` — exit 0; 66/66.
14. Host-permission rerun of command 10 — exit 0; 72/72, ten ignored.
15. Host-permission rerun of command 11 — exit 0; 39/39, ten ignored.
16. Host-permission rerun of command 12 — exit 0; 39/39, ten ignored.
17. `python3 tools/package.py --binary target/independent-retest-2026-11-06T085948Z/frozen/naro-default --out target/daybreak-blue-postfix-20261106T094550Z/package-default` — exit 0.
18. `python3 tools/package.py --binary target/independent-retest-2026-11-06T085948Z/frozen/naro-tiny --features tiny --out target/daybreak-blue-postfix-20261106T094550Z/package-tiny` — exit 0.
19. `python3 -m unittest discover -s tools -p 'test_*.py'` — exit 0; 132/132.
20. `git diff --check` — exit 0.
21. `python3 tools/check_package.py --archive target/daybreak-blue-postfix-20261106T094550Z/package-default/naro-0.1.2-x86_64-unknown-linux-gnu.tar.gz --source-archive target/daybreak-blue-postfix-20261106T094550Z/package-default/naro-0.1.2-source.tar.gz --out target/daybreak-blue-postfix-20261106T094550Z/check-default` — exit 0; 17/17 plus 44/44 assets.
22. The equivalent command for `package-tiny` and `check-tiny` — exit 0; 17/17 plus 44/44 assets.
23. `python3 tests/safe-save/run.py --binary <default-rust-test-executable> --out target/daybreak-blue-postfix-20261106T094550Z/safe-save-default` — exit 0; 448/448.
24. The equivalent command with the tiny Rust-test executable — exit 0; 448/448.
25. `python3 tests/backup/run_safe_save.py --binary <default-rust-test-executable> --out target/daybreak-blue-postfix-20261106T094550Z/backup-default` — exit 0; 1200/1200.
26. `python3 tests/recovery/run.py --binary target/independent-retest-2026-11-06T085948Z/frozen/naro-hooks --out target/daybreak-blue-postfix-20261106T094550Z/recovery-default` — exit 0; 41/41.
27. The equivalent recovery command with `--tiny` and `naro-hooks-tiny` — exit 0; 41/41.
28. `python3 target/daybreak-blue-postfix-20261106T094550Z/archive_audit.py` — exit 0.
29. `python3 tests/remediation/safe_save_semantics.py --binary target/independent-retest-2026-11-06T085948Z/frozen/naro-default --out target/daybreak-blue-postfix-20261106T094550Z/save-semantics` — exit 0; 22/22 plus 10/10.
30. `python3 spec/tools/nanoharness.py tests/safe-save/locking.json target/issue-3-lock-validation/historical-locking.json --binary target/independent-retest-2026-11-06T085948Z/frozen/naro-default --out target/daybreak-blue-postfix-20261106T094550Z/lock-terminal-six --keep` — exit 0; six scenarios and 35/35 assertions.
31. Default Rust-test executable with `--exact files::backup_tests::insecure_backup_replaces_a_hard_link_without_truncating_source --nocapture` — exit 0.
32. Default Rust-test executable with `--exact files::lock_tests::save_as_to_owned_lock_keeps_document_and_saved_state --nocapture` — exit 0.
33. `python3 target/daybreak-blue-postfix-20261106T094550Z/evidence_audit.py` — exit 0.
34. `python3 target/daybreak-blue-postfix-20261106T094550Z/guard_audit.py` — exit 0.
35. `python3 target/daybreak-blue-postfix-20261106T094550Z/final_state.py` — exit 1; inconsistent untracked-status format, superseded by 37.
36. Corrected-format retry of command 35 — exit 1; still inconsistent, superseded by 37.
37. Consistent `-uall` retry of command 35 — exit 0.
38. `git diff --check 2888560a9a2709469334a417d1ad9ac3a91c30ba 9d7cd10530501cf7f352b043d25e80756ff7d939` — exit 0.
39. `python3 target/daybreak-blue-postfix-20261106T094550Z/runner.py rust-default-host cargo test --locked --offline --target-dir target/daybreak-blue-postfix-20261106T094550Z/cargo-target` — exit 2 before entering the runner; wrong relative runner path, superseded by 14. Exact timestamps were not captured and were not invented.
