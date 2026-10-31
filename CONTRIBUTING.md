# Contributing to NARO

NARO is an independent Rust port of GNU nano 9.3, referencing upstream commit
`6ed285c3ec7a1d228def4d4e7021c6ba269f620c`. Start with the
[behavioral specification](spec/00-overview.md), [implementation status](IMPLEMENTATION.md)
and [current validation index](validation/README.md).

## Reports and changes

For ordinary bugs, use [GitHub issues](https://github.com/JLuethe/naro/issues).
Include `NARO_BUILD_INFO=1 /path/to/naro` output, OS, terminal, locale, exact
keys/commands, synthetic input, and expected versus observed results. Include
nano's version if comparing editors. Do not post private documents or sensitive
security details; follow [SECURITY.md](SECURITY.md) for suspected vulnerabilities.

Describe a proposed behavior change with its trigger, resulting behavior,
relevant requirements and validation. Distinguish intentional NARO differences
from compatibility defects. Fixes should include focused regressions that
actually execute the operation being tested; a no-op comparison is not coverage.

## Development checks

Provide Rust/Cargo, a C compiler, pkg-config, ncursesw and libmagic development
files. Run checks appropriate to the change, for example:

```sh
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test
cargo test --all-features
python3 spec/tools/test_compare_runs.py
python3 spec/tools/test_nanoharness.py
```

Terminal testing requires the recorded tmux/terminfo/locale setup, Python,
reference inputs and private fixtures; see [the test plan](spec/16-test-plan.md).
The dated release reports show exact environments and commands. CI is useful
coverage but does not replace the full host/Ubuntu/guest-VT release matrix.

Keep tests inside owned fixtures and use fresh output directories. Preserve
pinned upstream source, original reference recordings, failed attempts and
candidate hashes. Never test against real user/system files or weaken
normalization to conceal a new difference. [COVERAGE_REVIEW.md](COVERAGE_REVIEW.md)
explains unresolved citation mappings.

## Documentation and packaging

Documentation edits normally need link/content review rather than an editor
rebuild. However README, INSTALL, IMPLEMENTATION and other selected files ship
inside packages. Changing archived documentation changes archive hashes and
requires updated package/source receipts and relevant package verification.
Keep qualified executables unchanged when repackaging only documentation, and
record documentation revisions separately from compiled source identity.

Use [INSTALL.md](INSTALL.md) for source builds and packaging. Default and tiny
have different scope; the primary 0.1.0 binary is default only. Never distribute
test-hooks instrumentation. Testing, committing or packaging does not authorize
release publication or replacement of the system editor.

## Licensing and provenance

Contributions follow the project's GPL-3.0-or-later terms. Contribute only
material you have the right to submit under those terms. Reused upstream files
and dependencies retain their own terms and notices. Preserve attribution and
state the provenance of reused material in your change description. See
[LICENSE](LICENSE), [NOTICE](NOTICE), [CREDITS.md](CREDITS.md) and original headers.
