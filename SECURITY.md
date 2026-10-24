# Security reporting

Naro is an experimental terminal editor. A passing compatibility test suite is
not a security audit. Security fixes are developed against the current default
branch; no separate maintenance schedule is promised for older revisions.

Please report suspected vulnerabilities privately. GitHub private vulnerability
reporting is not currently enabled for this repository. If the repository's
[security page](https://github.com/JLuethe/naro/security) offers **Report a
vulnerability**, use that private reporting flow. Otherwise, open an
[issue](https://github.com/JLuethe/naro/issues/new) asking the maintainer to
arrange a private reporting channel. Include no exploit details, confidential
files, credentials or other sensitive information in that public request.

Once a private channel is available, include the Naro commit or binary version,
operating system, relevant locale and terminal, expected and observed behavior,
and a minimal reproduction using synthetic files. Describe the possible impact
and any workaround you have verified. Use private, disposable fixtures rather
than real user files for reproductions.

Ordinary bugs without sensitive security implications can be reported through
public issues. Reports concerning GNU nano or a native dependency should clearly
identify which project and revision are affected; Naro does not speak for those
upstream projects.
