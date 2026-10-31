# Security reporting

Report security bugs through [GitHub issues](https://github.com/JLuethe/naro/issues/new)
in the [NARO repository](https://github.com/JLuethe/naro). Start the issue title
with **Security:** so the report is easy to identify.

Include build identity, OS, terminal, locale, possible impact, a minimal
reproduction using synthetic files, expected and observed behavior, and any
verified workaround. `NARO_BUILD_INFO=1 /path/to/naro` prints the compiled
identity without opening the editor.

GitHub issues are public. Do not include passwords, credentials, private files
or other confidential information. If sensitive details are needed, describe
the issue at a high level and ask John Luethe to arrange a private follow-up.

NARO is an experimental terminal editor. Compatibility qualification is not a
security audit. Fixes are developed against the current default branch; no
separate maintenance schedule is promised for older revisions.

Clearly identify which project and revision are affected if the issue involves
GNU nano or a native dependency; NARO does not speak for those upstream projects.
