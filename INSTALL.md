# Installing Naro

Naro currently targets Linux x86_64 with glibc, ncursesw and libmagic. Binary
compatibility is limited to the runtime versions measured in the artifact's
`manifest.json`; the build machine's binary may require a newer libc than yours.

Build from source with Rust, a C compiler, ncursesw development headers/library
and libmagic development headers/library:

```sh
cargo build --release
python3 tools/package.py --binary target/release/naro --out target/package
```

Use a new output directory for each package build. The output includes a binary
archive, source archive, checksums and build provenance. No package is published
automatically. Only artifacts whose required validation gates pass should be
called release candidates.

Install an archive with the standalone installer:

```sh
python3 tools/release/install.py install --archive target/package/naro-0.1.0-x86_64-unknown-linux-gnu.tar.gz --prefix "$HOME/.local"
```

Alternatively, unpack the trusted archive and run its `install.py install`.
The default prefix is `~/.local`; an explicit prefix can contain spaces.
No shell profiles or user configuration files are edited. Launch
`~/.local/bin/naro`, or add the prefix's bin directory to PATH yourself.

Translations and syntax files are installed below `share/naro`. The executable
finds translations relative to its resolved installed location. An explicit
`NARO_LOCALEDIR` overrides that location; missing catalogs fall back to English.
Enable syntax files explicitly with a nanorc include such as:

```text
include "/your/prefix/share/naro/syntax/*.nanorc"
```

The installed documentation includes a sample configuration, attribution and PO
sources. A source-checkout fallback supports development without installation.

Remove an installation with the same installer and prefix:

```sh
python3 tools/release/install.py uninstall --prefix "$HOME/.local"
```

Removal uses `.naro-install.json` and deletes only unchanged, owned files. Modified
files and unrelated files are preserved; conflicts are reported with a nonzero
exit status. Keep the manifest until conflicts are resolved. Archive symlinks,
path traversal, checksum mismatches and destination symlinks are rejected.

The optional `credits` Cargo feature enables `naro --credits`. Default builds
retain the existing nano-compatible CLI. The `test-hooks` feature is for isolated
recovery tests and must never be included in distributed artifacts.

For the reduced editor, build and package the same `tiny` feature:

```sh
cargo build --release --features tiny --target-dir target/tiny
python3 tools/package.py --binary target/tiny/release/naro --features tiny --out target/package-tiny
```

Tiny needs Rust, a C compiler and ncursesw headers/library; libmagic is omitted.
It installs translations and their sources but no syntax definitions or nanorc
example. Configuration files are ignored. Use separate output directories for
full and tiny packages; their archive names and installed executable name are
the same. The manifest identifies the compiled features. Package checking
rebuilds source with those exact features.
