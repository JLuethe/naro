# Locale identity completion — 2026-10-31

This follow-up supersedes the transliterated-name limitation in AUDIT.md. The first audit and its evidence are retained as the earlier development state.

All 41 bundled PO catalogs were enumerated for the welcome message and both help introductions whose English GNU msgids contain the product name. Catalog bytes and msgids remain unchanged. Empty translations use their existing English fallback.

The runtime helper now applies these observed aliases only to explicitly selected UI text:

| Observed text | Runtime identity |
| --- | --- |
| nano, Nano, NANO | NARO |
| Arabic نانو | NARO |
| Finnish nanon, Nanon | NAROn |
| Finnish nanoon | NAROon |
| Finnish Nanossa | NAROssa |
| Japanese nanoの, nanoは, nanoが | NAROの, NAROは, NAROが |
| Korean 나노, 나노에 | NARO, NARO에 |
| Serbian нано, наноа, нанова | NARO, NAROа, NAROва |

Inflection suffixes remain intact. The Japanese replacements are limited to three observed product/particle combinations; no general substring replacement was introduced. Configuration names nanorc and нанорц, and unrelated words nanometer and nano_data, remain unchanged. The runtime helper is never applied to arbitrary buffer text, user filenames, or all status messages.

MAIN help headings which omit a product name (Esperanto, Croatian and Dutch) receive the prefix `NARO — `. Existing branded headings retain their localized wording with no double prefix. Other help menu headings are unchanged.

Verification:

- Five focused Rust identity tests passed, including every alias/inflection, preserved terms, and main-heading behavior.
- A standalone driver compiled the actual production identity.rs helper and applied it to all 123 selected catalog strings (41 catalogs × 3 messages). All returned success; no observed old product alias remained, and every main-help heading contained NARO. `catalog-runtime-checks.json` retains exact input msgids, translation presence, argv, return code and output. This validates source catalog strings through the production helper; it does not claim 41 independent live terminal/locale runs.
- Full post-change fmt, default Rust tests (16/16), all-feature Rust tests (11/11), and Clippy all-targets/all-features with warnings denied passed. Exact commands, timestamps, output and exit statuses: `../branding-0.1.1-2026-10-31/production-checks-attempt02/`.
- CLI output and C/German identity expectations are unchanged by this follow-up. Previously passing CLI checks were not repeated unnecessarily.

No editor behavior beyond explicit product identity text changed. The config unbound-key diagnostic retains its existing English behavior and uses the lowercase executable name `naro`; no new diagnostic localization was introduced.
