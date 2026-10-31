# Installing NARO

The technically qualified 0.1.0 candidate uses the default Linux x86_64
GNU/glibc profile. Publication is pending; these instructions do not imply
that a hosted release is available. Tiny is source-build only for this release.

## Requirements

The portable candidate was built and tested under Ubuntu 24.04 with glibc 2.39,
ncursesw/tinfo 6.4 and libmagic 5.45. Its build records identify exact package
versions. This is a tested environment, not a minimum-glibc promise or universal
Linux compatibility claim.

Dynamic dependencies include `libncursesw.so.6`, `libtinfo.so.6`, `libmagic.so.1`,
`libgcc_s.so.1`, `libc.so.6`, `liblzma.so.5`, `libbz2.so.1.0`, `libz.so.1` and
the x86_64 GNU loader. Provide terminal information and the locales you use.
The editor does not need Rust at runtime. The installer uses Python's
`hashlib.file_digest`, available in Python 3.11 and later; it was tested with
Python 3.12 in Ubuntu and Python 3.14 on the host.

`build.json`, `BUILD-ENVIRONMENT.json` and the archive's `manifest.json` retain
library/symbol requirements and build provenance. See [validation](validation/README.md)
for the qualified executable identity.

## Install a verified binary archive

The selected binary archive is `naro-0.1.0-x86_64-unknown-linux-gnu.tar.gz`.
The matching source archive is `naro-0.1.0-source.tar.gz`. Keep the accompanying
`SHA256SUMS`, build records, runtime notes and qualification receipt.

From a directory containing the complete download set:

```sh
sha256sum -c SHA256SUMS
```

Use a new empty directory for unpacking. For example, after verifying the files:

```sh
mkdir naro-unpack
tar -xzf naro-0.1.0-x86_64-unknown-linux-gnu.tar.gz -C naro-unpack
python3 naro-unpack/naro-0.1.0-x86_64-unknown-linux-gnu/install.py install --archive naro-0.1.0-x86_64-unknown-linux-gnu.tar.gz --prefix "$HOME/.local"
"$HOME/.local/bin/naro" example.txt
```

The prefix can contain spaces. Installation does not change shell profiles,
select a default editor, or replace system `nano`. Add the prefix's `bin` to
your PATH yourself if desired. Existing unowned or modified files cause a
conflict rather than silent replacement.

Show the installed build identity for a bug report:

```sh
NARO_BUILD_INFO=1 "$HOME/.local/bin/naro"
```

## Assets and configuration

Translations live below `share/naro/locale` and are found relative to the
resolved executable, including a symlink launcher. `NARO_LOCALEDIR` explicitly
overrides that directory; missing catalogs fall back to English. Development
builds also have a source-checkout fallback.

Syntax definitions are installed below `share/naro/syntax`. Include them
explicitly in your nanorc, replacing the prefix with the actual absolute path:

```text
include "/your/prefix/share/naro/syntax/*.nanorc"
```

The installed `share/doc/naro/examples/nanorc.example` supplies the same pattern.
The package also includes LICENSE, NOTICE, CREDITS, documentation and translation
PO sources. Configuration is user-managed; the installer does not edit it.

## Remove an installation

Keep the unpacked installer and use the same prefix:

```sh
python3 naro-unpack/naro-0.1.0-x86_64-unknown-linux-gnu/install.py uninstall --prefix "$HOME/.local"
```

Removal deletes only unchanged files owned by `.naro-install.json`. Modified
files and unrelated files are preserved. Conflicts produce a nonzero exit;
retain the manifest while resolving them. To change the installed file set,
remove the previous installation first. Archive traversal, archive symlinks,
checksum mismatches and destination symlinks are rejected.

## Build from corresponding source

Extract the matching source archive into a new directory. Provide Rust/Cargo,
a C compiler, pkg-config, ncursesw development files and libmagic development
files. The candidate was built with rustc 1.99.1; no older compiler minimum is
claimed here. The package has no Cargo package dependencies.

```sh
cd naro-0.1.0-source
cargo build --release --offline --locked
./target/release/naro example.txt
```

An offline build still needs its toolchain and native development dependencies
installed beforehand. Qualification demonstrated source rebuilding with the
same production fingerprint and features, not byte-for-byte reproducibility.

Developers can create new archives from a Git checkout with `tools/package.py`:

```sh
python3 tools/package.py --binary target/release/naro --out target/package-new
```

That packaging command needs Git-tracked source; the standalone source archive
supports building but does not include `.git`. Use a fresh output directory.
A locally rebuilt executable is a new artifact and does not inherit the frozen
candidate's qualification automatically.

## Optional tools and profiles

- Spelling: the default pipeline tries `hunspell -l`, then `spell` if spawning
  hunspell fails, and uses `sort -f` and `uniq`. Install the relevant dictionaries.
  A configured `speller` command supplies an alternative.
- Formatting and linting: install the selected program and configure a
  `formatter` or `linter` for the relevant syntax. No formatter/linter is bundled.
- Command execution/filtering: the requested command and its dependencies must
  exist in the runtime environment. Compatibility testing uses controlled fixtures;
  it does not certify every external tool or version.
- Tiny: build with `cargo build --release --features tiny --target-dir target/tiny`.
  This profile uses ncursesw and omits libmagic, nanorc/syntax and other features;
  see [implementation status](IMPLEMENTATION.md). No tiny download is selected.
- Credits: the optional `credits` feature enables `naro --credits`; it is not
  enabled in the primary default binary.
- `test-hooks`: isolated recovery-testing instrumentation; never enable it in a
  distributed editor.

Default and tiny packaging currently use the same archive basename and installed
executable name. Keep their output directories separate; do not distribute both
under an ambiguous filename or install them as if they were separate products.
