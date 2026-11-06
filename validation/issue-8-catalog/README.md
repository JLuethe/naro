# Issue #8 — typed catalog position formatting

The cursor-position report no longer has a C formatter or variadic FFI call.
`native::position` borrows gettext's bytes and passes them to a safe Rust
substitution function. The original msgid remains unchanged so the shipped
catalogs remain usable. Its `%zd` spellings are template identifiers only;
all values are formatted as Rust `usize` values before substitution.

The formatter accepts the nine existing conversion tokens in their original
order and `%%`. Catalog text cannot select types, widths, indexes or argument
counts. Unsupported, missing, additional, NUL-containing or oversized templates
fall back to the English message. The 4096-byte template limit bounds scanning
and output growth inside substitution. Original catalog bytes and percentage
spacing are preserved. Arbitrary third-party printf extensions/reordering are
not supported; they receive the English fallback.

Relevant requirements: [MSG-CATALOG and I18N-CATALOGS](../../spec/14-messages-and-i18n.md),
including numeric position layout in I18N-WIDTH. This is targeted issue evidence,
not release qualification or a claim about translation quality.

## Validation

- Default and tiny: three focused Rust tests pass for English padding, maximum
  unsigned values, raw non-UTF-8 template bytes, percent spacing and malformed
  template fallback.
- Default and tiny: each catalog runner checks all **41** shipped PO files with
  `msgfmt --check --check-format`; each executes **128** assertions through real
  gettext lookup and the fixed native Rust wrapper. These include 123 output
  comparisons (three numeric cases per catalog) against an independent Python
  printf oracle and five malformed/oversized private catalog cases. Each test
  first asserts the exact translated template returned by gettext, preventing
  missing catalogs or an unexpected English fallback from counting as a pass.
- GCC and Clang accept both default and tiny bridge builds with `-Wformat=2`,
  `-Werror=format`, and `-Werror=format-nonliteral`. These flags are also part of
  every Cargo native build.
- The literal-format source rule accepts the fixed bridge's one remaining
  printf call and rejects the pre-fix bridge's translated format. Its five
  parser regression tests pass. The old bridge is inspected/compiled only;
  no malformed catalog is executed against it.
- Rustfmt passes on the owned Rust files. Whole-tree formatting was attempted
  while the search agent was editing `src/search.rs`; its in-progress formatting
  differences are left for the integrated check rather than counted as a pass.
- Integrated all-features strict Clippy was attempted and failed on two warnings
  in concurrent search work (`first_spell_match` unused in tiny and
  `manual_is_multiple_of`). The search owner was notified; this attempt is not
  counted as a pass. `git diff --check` passes.

GCC's `gettext` `format_arg` annotation accepts the old expression even with
strict format warnings. The separate structural rule therefore requires actual
string-literal format arguments. Both checks run in the catalog CI step.

The initial runtime attempt correctly failed the template assertion because
`C.UTF-8` suppresses gettext on this host. The runner now requires an installed
non-C UTF-8 locale (`en_US.UTF-8` by default); CI explicitly generates that
locale. The failed attempt remains in the raw output directory.

## Reproduction and artifacts

Build each test executable with:

```sh
cargo test position_message --target-dir target/issue-8-catalog-build
cargo test position_message --features tiny --target-dir target/issue-8-catalog-build-tiny
```

Use the printed Cargo test-executable path for each profile:

```sh
python3 tests/catalog/run.py --binary TEST_EXECUTABLE --out NEW_PRIVATE_OUTPUT_DIRECTORY
```

The output directory must be fresh; the runner makes it mode 0700. A missing
compiler, `msgfmt`, locale, test entry point, catalog or actual executed assertion
fails the run. The fixture-dependent Rust test is ignored by ordinary Cargo
tests and explicitly executed by the runner in a separate process for each
case, avoiding process-global gettext/locale interference.

[receipt.json](receipt.json) records commands, outcomes, environment, source
hashes and both test-executable hashes. Full raw logs, generated catalogs and
failed attempts are retained locally in `target/issue-8-catalog/`, not added to
tracked validation. The shared tree was dirty with concurrent undo/search
remediation, so these hashes identify the tested binaries without asserting
that they represent the final integrated source tree.
