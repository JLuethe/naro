# Step 9 — community distribution review

Completed: see the [steps 8–9 results](NARO_STEP8_9_RESULTS_2026-10-30.md) for refreshed
archive identities, validation, backup and the outstanding step 10 CI gate.

Date: October 30, 2026. Candidate: NARO 0.1.0, default Linux x86_64 GNU/glibc.

The public documentation and reporting text are approved for adoption. The
refreshed archive inventory and rebuild checks are recorded in the subsequent
step 8/9 completion receipt. Publication remains a separate step 10 decision.

## Attribution and licensing inventory

| Material | Review and distribution treatment |
| --- | --- |
| NARO Rust editor and native bridge | Cargo metadata and bridge identify GPL-3.0-or-later; full LICENSE accompanies binary and source. Native bridge source and build scripts are in corresponding source. |
| Upstream reference, generated binding/help data | NOTICE and CREDITS identify GNU nano, the Free Software Foundation, contributors and pinned reference revision 6ed285c3ec7a1d228def4d4e7021c6ba269f620c. Generated help retains its origin/license header. |
| Syntax definitions | Original files and headers are preserved. Haskell states GPL version 3; Go states CC0. These exceptions remain in NOTICE and the reference inventory; no blanket relicensing of assets is claimed. |
| Translations | All 41 compiled catalogs and original PO sources are included. PO copyright, translator credits and nano-package license notices remain intact. |
| Native system dependencies | ncursesw/tinfo, libc/POSIX, libmagic and transitive runtime dependencies are recorded in build/runtime metadata. External shared libraries are not copied into the archive. No Cargo package dependencies are declared. |
| Project acknowledgment | README names John Luethe and thanks OpenAI for their generous support. GNU nano remains independently credited; the wording does not claim upstream affiliation. |

[NOTICE](NOTICE), [CREDITS](CREDITS.md), [LICENSE](LICENSE) and
[the reference inventory](spec/00-reference-environment.md#12-license-for-implementation-review)
remain authoritative repository entry points. No production attribution file was
changed, so the qualified source fingerprint is preserved.

The selected distribution method pairs the binary and matching source archive
in the same release download set, without an extra charge for source. This is
the method described by [GPLv3 section 6(d)](https://www.gnu.org/licenses/gpl.en.html).
The source archive includes editable production inputs, assets and build scripts;
the fresh offline rebuild checks its production fingerprint and feature profile.
The review checks concrete notices and source availability; it does not establish
exhaustive third-party rights clearance or constitute a security audit.

## Reporting route

GitHub's repository API was checked on October 30: JLuethe/naro is public,
unarchived, and has issues enabled. John explicitly selected **public GitHub
issues** for security reports, superseding the original plan's private-reporting
configuration task. No private advisory service is promised or enabled here.

[SECURITY.md](SECURITY.md) directs reporters to a `Security:` issue and explains
that credentials/private data must be omitted; John can arrange a private
follow-up if needed. [The bug template](.github/ISSUE_TEMPLATE/bug_report.md)
requests build identity, OS, terminal, locale, synthetic reproduction and
expected/actual results. No test issue or message was sent.

## Publication contents

The reviewed public set is exactly these seven files, with final hashes in the
completion receipt and `SHA256SUMS`:

- `naro-0.1.0-x86_64-unknown-linux-gnu.tar.gz`
- `naro-0.1.0-source.tar.gz`
- `build.json`
- `BUILD-ENVIRONMENT.json`
- `RUNTIME-REQUIREMENTS.md`
- `QUALIFICATION.json`
- `SHA256SUMS`

The source archive uses a clean committed file inventory. The local review
workspace, unrelated agent/session exports, `.git`, ignored build products and
private test fixtures are excluded. Full raw evidence stays in the separate
backup; it is not a proposed release asset. Source revision and compiled revision
are recorded separately because documentation and packaging changed after the
production freeze.

Use [release notes](RELEASE_NOTES.md) for the release description. The optional
community announcement below remains a draft until publication is authorized.

## Community announcement draft

I'm John Luethe, and I've been working on NARO, an independent Rust port of GNU
nano 9.3. NARO 0.1.0 is an experimental terminal editor for Linux x86_64 using
GNU/glibc, with familiar nano bindings, undo/redo, search and replacement,
multiple buffers, syntax highlighting and translations.

The candidate has completed host, Ubuntu and guest Linux VT qualification,
including the documented compatibility differences. It still uses a small C
bridge and native libraries. This first release does not promise complete nano
parity or support for every Linux distribution. Please read the installation
instructions, release notes and known limitations before trying it.

Thank you to GNU nano's contributors and the Free Software Foundation for the
reference behavior and reused data/assets, and to OpenAI for their generous
support. Feedback and synthetic reproductions are welcome through
https://github.com/JLuethe/naro/issues. Follow SECURITY.md for security bugs.

Before posting: add the approved release URL after publication and verify that
the final binary, matching source and checksums are available there.
