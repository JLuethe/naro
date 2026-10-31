# NARO 0.1.1 identity audit — 2026-10-31

Scope: runtime product identity and package version only. No editing, saving, wrapping, recovery, file-format, configuration-path, or terminal-input behavior was changed.

## Production changes reviewed

- `Cargo.toml` and `Cargo.lock`: package version 0.1.0 → 0.1.1.
- `src/identity.rs`: package-derived title, honest NARO version/reference/license/profile output, exact CLI help substitutions, and scoped whole-word runtime branding after gettext.
- `src/config.rs`: NARO version and executable help; recovery suggestion names the `naro` executable.
- `src/features.rs`: translated in-editor help title/introduction identifies NARO; original GNU msgids remain byte-identical.
- `src/editor.rs`: welcome and suspend text identify NARO; startup gettext lookup uses the original nano key.
- `src/main.rs`: identity module and NARO panic message.
- `src/render.rs`: editing header uses package-derived NARO identity. Rendering logic is otherwise unchanged; new tests bind title and filename positioning at widths 32–35, 40, 80, and 120, including modified state.

## Intentionally retained occurrences

GNU attribution, GPL license/credits, reference revision/source comments, the gettext domain and catalog keys, pinned nano evidence, and original help assets remain unchanged. The fixed-format lock header `nano 9.3`, nano-compatible config/history paths, nanorc terminology, and temporary/backup filename prefixes remain compatibility data. These are not claims that NARO is GNU nano.

Runtime branding applies only to supplied UI strings, replacing standalone `nano`, `Nano`, or `NANO`. It preserves longer words such as nanorc and nano_data. It does not rewrite transliterated names: for example, the existing Korean welcome uses `나노`. The NARO title and CLI identity are independent of that translated prose. No claim is made that all 41 translations have been retranslated.

## Verification

- Rust identity tests: 3/3 in default and all-feature configurations.
- Renderer identity/boundary tests: 2/2.
- Full Rust checks: default 14/14 and all-features 10/10; fmt and Clippy all-targets/all-features with warnings denied passed. Recorded commands, timestamps, exit statuses and output are in `../branding-0.1.1-2026-10-31/production-checks/`.
- Actual debug CLI: 5/5 exact checks for default and 5/5 for tiny. Tests cover both version flags, default help, restricted flag, and restricted argv[0]. Each report retains binary SHA-256 and exact expected/observed output.
- The previous frozen 0.1.0 candidate failed all five identity checks as intended.
- Terminal smoke probe: 5/5 assertions for NARO title, welcome, help title, help introduction, and normal exit. It used the development default build, not a frozen release candidate.
- The CLI checker rejects existing output directories before launching probes; a second invocation failed with FileExistsError and preserved the report hash.

The two debug executables were built before the final shared-TITLE refactor and boundary tests; displayed behavior is equivalent, but these are development checks only. A new frozen host/Ubuntu build and candidate-policy qualification remain the parent agent's responsibility. No reference baseline was edited, and nothing was committed, pushed, or published by this agent.
