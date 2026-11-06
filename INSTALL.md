# Installing NARO

This source tree is the NARO 0.1.2 local development candidate; no 0.1.2 release
has been published or qualified yet. Download a published version and its matching
source/checksums from [GitHub Releases](https://github.com/JLuethe/naro/releases).
The previously qualified 0.1.1 binary uses the default Linux x86_64 GNU/glibc
profile. Tiny was source-build only for that release.

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

## Install a verified 0.1.1 binary archive

For the prior published version, the selected binary archive is
`naro-0.1.1-x86_64-unknown-linux-gnu.tar.gz`.
The matching source archive is `naro-0.1.1-source.tar.gz`. Keep the accompanying
`SHA256SUMS`, build records, runtime notes and qualification receipt.

From a directory containing the complete download set:

```sh
sha256sum -c SHA256SUMS
```

Use a new empty directory for unpacking. For example, after verifying the files:

```sh
mkdir naro-unpack
tar -xzf naro-0.1.1-x86_64-unknown-linux-gnu.tar.gz -C naro-unpack
python3 naro-unpack/naro-0.1.1-x86_64-unknown-linux-gnu/install.py install --archive naro-0.1.1-x86_64-unknown-linux-gnu.tar.gz --prefix "$HOME/.local"
"$HOME/.local/bin/naro" example.txt
```

The prefix can contain spaces. Installation does not change shell profiles,
select a default editor, or replace system `nano`. Add the prefix's `bin` to
your PATH yourself if desired. Existing unowned or modified files cause a
conflict rather than silent replacement.

## Recoverable installation in the 0.1.2 candidate

The installer in this source tree adds the following transaction guarantees.
They do not apply to the installer shipped in the historical 0.1.1 archive.
It stages and syncs the complete payload before publishing a pending
journal (`.naro-install.pending.json`). Each file replacement is atomic, but
the complete file set is not switched simultaneously: do not run NARO from a
prefix while installing or recovering it. A failed or interrupted transaction
retains its journal and staging files so the next install or uninstall can
finish it safely before proceeding. To finish it without the original archive:

```sh
python3 tools/release/install.py recover --prefix "$HOME/.local"
```

Recovery checks the staged payload, existing ownership and destination contents;
modified files or symlinks stop recovery without overwriting them. Preserve the
journal and the `.naro-install-stage-*` directory it names until recovery
succeeds. Failures before journal publication can leave unreferenced staging
directories, and abrupt termination can leave `.naro-tmp-*` files. These are
unused copies, not installed ownership state; remove them only after confirming
that no installer is running and no pending journal references the staging
directory. Concurrent installer operations on the same prefix are refused.
Durability requires Linux filesystem support for file and directory `fsync`
and atomic rename; sync errors are reported rather than treated as success.

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
python3 naro-unpack/naro-0.1.1-x86_64-unknown-linux-gnu/install.py uninstall --prefix "$HOME/.local"
```

Removal deletes only unchanged files owned by `.naro-install.json`. Modified
files and unrelated files are preserved. Conflicts produce a nonzero exit;
retain the manifest while resolving them. To change the installed file set,
remove the previous installation first. Archive traversal, archive symlinks,
checksum mismatches and destination symlinks are rejected.
If a pending transaction exists, removal first completes it using its staged
payload. If recovery reports a conflict, removal stops and retains the journal.
Both installation state and conflict-only removal state are written using a
synced temporary file, atomic replacement and a containing-directory sync.

## Build from corresponding source

For a published version, extract its matching source archive into a new
directory. For the 0.1.2 development candidate, use this Git checkout. Provide
Rust/Cargo, a C compiler, pkg-config, ncursesw development files and libmagic
development files. The prior 0.1.1 candidate was built with rustc 1.99.1; no
older compiler minimum is claimed here. The package has no Cargo dependencies.

```sh
cargo build --release --offline --locked
./target/release/naro example.txt
./target/release/naro --credits
```

An offline build still needs its toolchain and native development dependencies
installed beforehand. Qualification demonstrated source rebuilding with the
same production fingerprint and features, not byte-for-byte reproducibility.

Developers can create new archives from a Git checkout with `tools/package.py`:

```sh
python3 tools/package.py --binary target/release/naro --out target/package-new
```

That packaging command needs Git-tracked source; the standalone source archive
supports building but does not include `.git`. Release packaging requires a clean
tracked tree and index, and refuses untracked files in source, native, and asset
inputs. Unrelated untracked review files are excluded from the source archive.
`build.json` records the clean commit, hashes and modes for every source archive
file, and the source archive hash. Use a fresh output directory.
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
- Credits: `naro --credits` prints the same attribution as `CREDITS.md` in default
  and tiny 0.1.2 builds. The `credits` feature remains accepted by Cargo for
  older build commands and does not change availability.
- `test-hooks`: isolated recovery-testing instrumentation; never enable it in a
  distributed editor.

Default and tiny packaging currently use the same archive basename and installed
executable name. Keep their output directories separate; do not distribute both
under an ambiguous filename or install them as if they were separate products.
