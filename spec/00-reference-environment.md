# 00 — Reference environment

Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

This document records the source, builds, dependencies, runtime environments,
comparison binaries, reproducible commands, and limitations that every other
specification file depends on. Anything called "the reference" in this
specification means the **unmodified** build described in §3, the
`default` profile, run in the baseline environment of §5 unless a section says
otherwise.

## 1. Upstream source

| Item | Value |
|---|---|
| Repository | `https://git.savannah.gnu.org/git/nano.git` (redirects to `https://https.git.savannah.gnu.org/git/nano.git/`) |
| Requested revision | `6ed285c` |
| Resolved full hash | `6ed285c3ec7a1d228def4d4e7021c6ba269f620c` (unambiguous; `git rev-parse 6ed285c^{commit}`) |
| Subject | `build: when enabled, properly include Linter and friends in tiny version` |
| Author | Benno Schulenberg, author date 2026-10-23T16:00:56+02:00 |
| Commit date | 2026-10-23 16:14:12 +0200 |
| `git describe --tags` | `v9.3-7-g6ed285c3` (7 commits after tag `v9.3`) |
| Tags containing the commit | none (no release includes it) |
| Branch position at clone time | identical to `master` HEAD on 2026-10-23 |
| `AC_INIT` version | `9.3` |

Commits between `v9.3` and the reference (all "build"/"tweaks" commits):

```
6ed285c3 build: when enabled, properly include Linter and friends in tiny version
a79849a3 tweaks: rename a variable, and condense a fragment of code
ed153007 tweaks: reshuffle the Speller help text, into a more logical order
21b649eb tweaks: reshuffle four braces, to make all those 'else' branches the same
948ef13f tweaks: adjust the whitespace after the previous change
a8c1a1e5 tweaks: add a few 'const' markers, to avoid a bunch of warnings
33835004 build: raise the required version of gettext to 0.21, to avoid a warning
```

### 1.1 Paths

| Path | Purpose | State |
|---|---|---|
| `~/src/nano` | Clone of upstream (`master`) | Fresh clone made for this work; HEAD = reference commit |
| `~/src/nano-ref` | `git worktree add --detach` at the reference commit | Clean (`git status --porcelain` empty). **All source citations in this specification refer to this tree.** |
| `~/src/nano-bootstrap` | `git archive` export of the reference commit, plus gnulib import and `autoreconf` output | Generated build inputs only; tracked sources identical to the commit |
| `~/src/nano-build/{default,tiny}` | Out-of-tree object directories | Build artifacts |
| `~/src/nano-install/{default,tiny}` | `make install` prefixes | Reference executables |
| `~/src/nano-locales` | Private locales compiled with `localedef` (used through `LOCPATH`) | Test support |
| `~/src/nano-rs/spec` | This specification | — |

The pinned worktree was never used for building, so it holds no generated
files. No tracked source file was modified anywhere.

### 1.2 License (for implementation review)

| Material | License as stated in the pinned tree |
|---|---|
| C sources `src/*.c`, `src/*.h` (18 files) | GPL "version 3 of the License, or (at your option) any later version" (header of every file); full text in `COPYING` (GPLv3, 29 June 2007) |
| `doc/nano.1`, `doc/rnano.1`, `doc/nanorc.5`, `doc/nano.texi` | Dual: GPLv3-or-later **or** GFDL 1.2-or-later (no invariant sections); `COPYING.DOC` holds GFDL 1.2 |
| `syntax/*.nanorc`, `syntax/extra/*.nanorc` | Mixed per-file headers: 17 "GPL version 3 or newer", `rust.nanorc` "Licensed under GPL version 3 or newer", `haskell.nanorc` "GPL version 3" (no "or later"), `go.nanorc` "CC0 (public domain)", 24 files carry no license line (they fall under the package license) |
| `po/*.po` | "distributed under the same license as the nano package" |
| gnulib modules (build time only) | Imported from gnulib `d89ea630c1318a1a595aa3aff169586f4e626274`; LGPL/GPL per module |

A GPLv3-licensed Rust reimplementation that consults this source is compatible
with these terms. Reusing the bundled syntax files verbatim needs a per-file check
(`haskell.nanorc` is GPLv3-only, which is compatible with GPLv3).

## 2. Build procedure

`autogen.sh` clones gnulib from `git://git.sv.gnu.org/gnulib.git`. The Savannah
HTTPS endpoint returned `HTTP 500` during this work, so gnulib was cloned from
the GitHub mirror `https://github.com/coreutils/gnulib.git`. The exact pinned
gnulib commit `d89ea630c1318a1a595aa3aff169586f4e626274` (2026-10-06) was
checked out and verified by hash, so the result matches `autogen.sh`.

```sh
# 1. pristine export (keeps the pinned worktree free of generated files)
mkdir -p ~/src/nano-bootstrap
git -C ~/src/nano archive 6ed285c3ec7a1d228def4d4e7021c6ba269f620c | tar -x -C ~/src/nano-bootstrap
cd ~/src/nano-bootstrap
git clone --filter=blob:none https://github.com/coreutils/gnulib.git gnulib
git -C gnulib checkout --force d89ea630c1318a1a595aa3aff169586f4e626274
# 2. the two steps of autogen.sh, with its module list
modules=$(sed -n '/^modules="/,/^"/p' autogen.sh | grep -v '"')
./gnulib/gnulib-tool --import $modules
autoreconf --install --symlink --force
# 3. builds (out of tree)
for p in default tiny; do
  mkdir -p ~/src/nano-build/$p && cd ~/src/nano-build/$p
  extra=; [ $p = tiny ] && extra=--enable-tiny
  ~/src/nano-bootstrap/configure --prefix=$HOME/src/nano-install/$p $extra
  make -j"$(nproc)" && make install
done
```

Configure arguments: `--prefix=$HOME/src/nano-install/default` (default profile);
`--prefix=$HOME/src/nano-install/tiny --enable-tiny` (tiny profile). No other
options were given. `CFLAGS = -g -O2 -Wall`, `CPPFLAGS = -D_DEFAULT_SOURCE -D_XOPEN_SOURCE=600`.

Because the build tree is not a git checkout, `src/revision.h` is generated
**empty** (`src/Makefile.am:17-21` writes `REVISION` only when `git describe`
succeeds). As a result:

* `--version` prints ` GNU nano, version 9.3` and not ` GNU nano from git, v9.3-7-g6ed285c3`;
* the title bar shows `GNU nano 9.3` (`BRANDING` = `PACKAGE_STRING`, `src/winio.c:34-38`).

A build run inside a git checkout would show the `from git` strings instead. The
specification treats the tarball-style branding as the reference and the git
branding as build-variant `BV-REVISION` (see `99-open-questions.md` Q-ENV-002).

## 3. Reference executables

| Profile | Executable | SHA-256 | Size |
|---|---|---|---|
| `default` | `~/src/nano-install/default/bin/nano` (`rnano` → symlink to `nano`) | `b4fe2cb30a931c3d058ee68d9d60acec6db1ff87f6a50baaa0972affb629a3b2` | 986264 |
| `tiny` | `~/src/nano-install/tiny/bin/nano` (`rnano` → `nano`) | `0e6343fe60e7c55f16cef7ecd99c7087885706d7065023cf12e7641728ea6439` | 396144 |

`--version` output:

```
default:
 GNU nano, version 9.3
 (C) 2026 the Free Software Foundation and various contributors
 Compiled options: --enable-utf8

tiny:
 GNU nano, version 9.3
 Compiled options: --enable-tiny --enable-utf8
```

### 3.1 Feature macros (from each `config.h`)

| Macro | default | tiny | Notes |
|---|---|---|---|
| `ENABLE_BROWSER` | 1 | – | |
| `ENABLE_COLOR` | 1 | – | |
| `ENABLE_COMMENT` | 1 | – | cannot be enabled with tiny |
| `ENABLE_EXTRA` | 1 | – | Easter egg (credits crawl) |
| `ENABLE_FORMATTER` | 1 | – | |
| `ENABLE_HELP` | 1 | – | |
| `ENABLE_HISTORIES` | 1 | – | |
| `ENABLE_JUSTIFY` | 1 | – | |
| `ENABLE_LINENUMBERS` | 1 | – | |
| `ENABLE_LINTER` | 1 | – | |
| `ENABLE_MOUSE` | 1 | – | requires `NCURSES_MOUSE_VERSION` |
| `ENABLE_MULTIBUFFER` | 1 | – | |
| `ENABLE_NANORC` | 1 | – | |
| `ENABLE_OPERATINGDIR` | 1 | – | |
| `ENABLE_SPELLER` | 1 | – | |
| `ENABLE_TABCOMP` | 1 | – | |
| `ENABLE_WORDCOMPLETION` | 1 | – | cannot be enabled with tiny |
| `ENABLE_WRAPPING` | 1 | – | |
| `ENABLE_UTF8` | 1 | 1 | |
| `ENABLE_NLS` | 1 | 1 | gettext 1.0 (glibc libintl) |
| `NANO_TINY` | – | 1 | |
| `HAVE_LIBMAGIC` | 1 | – | `-lmagic -lz` |
| `HAVE_USE_DEFAULT_COLORS`, `HAVE_SET_ESCDELAY`, `HAVE_KEY_DEFINED`, `HAVE_DEFINE_KEY` | 1 | 1 | ncursesw 6.6 |
| `NANO_REG_EXTENDED` | `REG_EXTENDED` | `REG_EXTENDED` | no `REG_ENHANCED` on glibc |
| regex implementation | glibc `regcomp`/`regexec` | same | gnulib's replacement regex was **not** compiled in (no `lib/regex.o`) |
| `wcwidth` | glibc | glibc | gnulib's `wcwidth` replacement was not compiled in |
| `NDEBUG` | 1 | 1 | `--enable-debug` not used |
| `RCFILE_NAME` | default (`.nanorc` / `nanorc`) | n/a | |
| `PKGDATADIR` | `…/install/default/share/nano` | `…/install/tiny/share/nano` | |
| `SYSCONFDIR` | `…/install/default/etc` | n/a | **no `nanorc` is installed there**, so the system rcfile is absent |

Linked libraries (default): `libmagic.so.1 libz.so.1 libncursesw.so.6 libc.so.6`
(plus libmagic's `libzstd liblzma libbz2`). Tiny: `libncursesw.so.6 libc.so.6`.

## 4. Host and dependencies

| Item | Version |
|---|---|
| OS | Omarchy (Arch-based), Linux 7.2.8-9-omarchy x86_64 |
| C library | glibc 2.44 (`2.44+r50+g1848099f063e-1`) |
| Compiler | gcc 16.2.1 20260810 |
| Terminal library | ncursesw 6.6 (`ncurses 6.6.20251230`, package `6.6-2`) |
| libmagic | file 5.48 |
| zlib | 1.3.2 |
| gettext | 1.0 |
| autotools | autoconf / automake / autopoint present; `makeinfo` present |
| tmux (terminal emulator for tests) | 3.8 |
| gdb (table dumps) | 18.1 |
| Python (harness) | 3.14.8, standard library only |

External programs that nano may run, as present on this host:

| Program | Present | Use in nano |
|---|---|---|
| `spell` | **no** | default external speller command (`spell`) |
| `aspell` | **no** | — |
| `hunspell` | yes (`/usr/bin/hunspell`) | possible `--speller` value |
| `sh` | yes | execute command, linter, formatter |
| `file` | yes 5.48 | not run by nano (libmagic is used in-process) |

External-tool tests use **stub programs** placed in a fixture `bin/` directory at
the front of `PATH` (see `16-test-plan.md` §6). Results do not depend on the
host's spellers.

## 5. Runtime environments (compatibility envelope)

### 5.1 Baseline environment `ENV-BASE`

All runtime observations are taken in this environment unless the observation
names another one.

| Aspect | Value |
|---|---|
| Executable | `default` profile, §3 |
| Terminal emulator | tmux 3.8, private server (`tmux -L <socket> -f /dev/null`), status line off, `window-size manual` |
| `TERM` | `tmux-256color` (terminfo from ncurses 6.6; `kbs=^?`, `kcuu1=\EOA`, `smkx=\E[?1h\E=`, `smcup=\E[?1049h`, `cnorm=\E[34h\E[?25h`, `civis=\E[?25l`) |
| Size | 80 columns × 24 rows |
| Colors | tmux-256color reports 256 colors |
| Locale | `LANG=en_US.UTF-8`, no `LC_*` overrides, `LC_ALL` unset → all categories `en_US.UTF-8`; `nl_langinfo(CODESET)` = `UTF-8` |
| Environment | built with `env -i`: `HOME=<fixture>/home`, `PATH=<fixture>/bin:/usr/bin:/bin`, `TERM`, `LANG`, `SHELL=/bin/sh`, `TZ=UTC`; nothing else (no `XDG_*`, no `SPELL`, no `NO_COLOR`, no `NANO_NOCATCH`) |
| Working directory | `<fixture>/work` |
| umask | `022` |
| Configuration | No system nanorc (absent at `SYSCONFDIR`). User rcfile only when a scenario provides `<fixture>/home/.nanorc`; many scenarios also pass `-I`. |
| History/state files | `$HOME/.local/share/nano/` inside the fixture (`XDG_DATA_HOME` unset) |
| Linux console | No (`on_a_vt` is false under tmux) |

### 5.2 Additional profiles (inventoried; partly verified)

| ID | Difference from ENV-BASE | Status |
|---|---|---|
| `ENV-TINY` | `tiny` executable | key tables dumped (runtime); other behavior is source-specified |
| `ENV-C` | `LANG=C` (non-UTF-8, ASCII) | key tables dumped; TEST-BYTE-005 verifies byte-mode stepping/counting |
| `ENV-LATIN1` | `LANG=en_US.ISO-8859-1` with `LOCPATH=~/src/nano-locales` | see 97 for recorded probes and remaining gaps |
| `ENV-DE` | `LANG=de_DE.UTF-8` with `LOCPATH` (translated messages) | TEST-I18N-001/-002/-007 and CLI probes recorded |
| `ENV-JA` | `LANG=ja_JP.UTF-8` (wide characters in translations) | see 97 for recorded probes and remaining gaps |
| `ENV-VT220` | `TERM=vt220` (`kbs=^H`, which changes the modern-bindings Help key) | key tables dumped |
| `ENV-XTERM` | `TERM=xterm-256color` inside tmux (terminfo mismatch with the emulator) | see 97 for recorded probes and remaining gaps |
| `ENV-SMALL` | small sizes, e.g. 20×5, 10×3, 80×1 | see 97 for recorded probes and remaining gaps |
| `ENV-LINUXVT` | real Linux console (`on_a_vt` true) | **not available** in this environment; source-specified only |
| `ENV-SLANG`, non-glibc, macOS, BSD | other terminal/C libraries | out of envelope; source notes only |

## 6. Comparison binaries

The task statement names an installed `nano` as a secondary comparison target.
**There is no `nano` on this host's `PATH`** (`which nano` fails, and there is no
package). No secondary comparison was possible. This is recorded as limitation
L-3 and open question Q-ENV-001. The pinned builds remain the comparison targets; no system binary is needed.

## 7. Tooling written for this specification

| Tool | Purpose |
|---|---|
| `spec/tools/dump_tables.py` | gdb script: dumps the effective shortcut list (`sclist`) and function list (`allfuncs`) of the unmodified executable at `prepare_for_display()`, after command-line and rcfile processing |
| `spec/tools/dump_all_tables.sh` | runs the dump for 13 profiles → `spec/evidence/tables/*.json` |
| `spec/tools/nanoharness.py` | tmux-based scenario runner (screen cells, attributes, cursor, modes, raw trace, fixture manifest, exit status) |

Running a scenario:

```sh
cd ~/src/nano-rs/spec
python3 tools/nanoharness.py evidence/scenarios/<file>.json            # default profile
python3 tools/nanoharness.py --profile tiny evidence/scenarios/<file>.json
python3 tools/nanoharness.py --binary /path/to/rust/nano evidence/scenarios/<file>.json
```

## 8. Limitations

| ID | Limitation | Effect |
|---|---|---|
| L-1 | Runtime verification uses one terminal emulator (tmux 3.8). tmux re-encodes output, so snapshots show what tmux shows, not the exact byte stream. | Screen-state comparisons are emulator-mediated; raw traces are kept for diagnosis. |
| L-2 | No real Linux virtual console. | `on_a_vt` paths (`^-` label, `TIOCLINUX` modifier probing, zero-width skipping, `M-Left/Right` buffer switching disabled) are source-specified only. |
| L-3 | No installed `nano` binary. | No secondary comparison. |
| L-4 | Savannah git over HTTPS returned HTTP 500 for gnulib. | gnulib came from the GitHub mirror at the verified pinned hash; no effect on content. |
| L-5 | Only two build profiles were built (`default`, `tiny`). Single-feature `--disable-X` builds were not. | Per-feature conditional behavior is specified from source (`12-features.md`, `data/build-features.csv`). |
| L-6 | `spell`/`aspell` are absent. | The default speller's failure path can be observed; success paths use stubs. |
| L-7 | tmux reports a dead pane's cursor as invisible. | The harness derives the final cursor, alternate-screen, keypad and bracketed-paste state from the raw trace (`trace_final_modes`). |
