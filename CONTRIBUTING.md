# Contributing to Naro

Naro is an independent Rust port of GNU nano, based on GNU nano 9.3 at reference
commit `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`. Read the
[behavioral specification](spec/00-overview.md) and
[implementation status](IMPLEMENTATION.md) before changing editor behavior.

Report ordinary bugs or propose changes through
[GitHub issues](https://github.com/JLuethe/naro/issues). Include the Naro commit,
operating system, terminal, locale, exact reproduction steps and expected result.
Use synthetic input and avoid posting private files. Follow [SECURITY.md](SECURITY.md)
for suspected vulnerabilities.

Contributions are licensed under GPL-3.0-or-later, consistent with the project's
[license](LICENSE) and Cargo metadata. Contribute only material you have the right
to submit under those terms. Reused upstream material and dependencies retain
their original terms; preserve copyright, license and attribution notices.
Describe provenance and any additional licensing requirements in your pull
request. See [NOTICE](NOTICE) and [CREDITS.md](CREDITS.md).

Build with Rust, a C compiler, ncursesw development headers and libmagic
development headers. For ordinary code changes, run the relevant checks:

```sh
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all-features
python3 spec/tools/test_compare_runs.py
python3 spec/tools/test_nanoharness.py
```

For behavior changes, add or update fixture-based scenarios and run the relevant
comparison checks described in the [test plan](spec/16-test-plan.md) and
[README](README.md). Terminal validation needs tmux, terminfo, Python 3.11 or
newer, and the reference corpus. Keep all editor tests inside harness-owned
fixtures. Never test against real user or system files, modify the pinned GNU
nano source checkout, or overwrite the original reference recordings. Use a
fresh output directory and retain binary hashes and comparison results.

In a pull request, describe the trigger, resulting behavior, relevant spec
requirements, checks performed and remaining limitations. Distinguish intended
Naro differences from GNU nano compatibility defects. Documentation-only changes
need link and content review; they do not require rebuilding the editor.

Packaging and installation instructions are in [INSTALL.md](INSTALL.md).
Distributed artifacts must not enable the `test-hooks` feature. Building or
testing does not authorize publishing a release or replacing a system editor.
