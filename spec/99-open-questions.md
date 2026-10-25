Reference commit: `6ed285c3ec7a1d228def4d4e7021c6ba269f620c`

# 99 — Decisions, defects and open questions

The reference behavior is fixed by the commit. Decisions here describe the Rust
target; a recorded deviation must never be hidden by comparison normalization.
“Resolved” means a specification decision, not proof of implementation.

| ID | Evidence / issue | Decision or remaining work |
|---|---|---|
| Q-DEF-001 | CLI-033, TEST-CLI-057: `+r/(` proceeds after failed regcomp and crashes | Resolved: validate compilation, show `Bad regex "(": Unmatched ( or \(`, skip search and keep editor alive. Deliberate safety deviation. |
| Q-DOC-001 | nano.1 says `nano.save`; SIG-EMERG / TEST-SIG-002 writes `nano.<pid>.save` | Resolved: observed source behavior wins; normalize only PID. |
| Q-DOC-002 | nanorc.5 default space marker `⋅` differs from code `·` | Resolved: U+00B7; tab marker U+00BB in UTF-8. |
| Q-PROMPT-001 | I18N-YESNO, TEST-PROMPT-NUL-001: NUL answers Yes by empty substring match | Resolved: reject NUL as an unrecognized answer. Deliberate deviation; do not update golden evidence. |
| Q-EDIT-001 | TEST-BYTE-004 confirms sign-extended Latin-1 letters are not word characters in byte mode | Resolved: reproduce. Earlier “probably” in 05 is superseded by doc 18. |
| Q-REGEX-001 | 81-case corpus × 2 locales, REGEX-002 | Resolved: libc POSIX regex via an opaque native bridge. No Rust regex engine substitution. |
| Q-I18N-001 | German ISO-8859-1 catalog output, TEST-I18N-003 | Resolved target: gettext with original catalogs and native charset conversion. Implementation completion must be checked separately. |
| Q-ENV-001 | No separately installed nano | Remains an environmental limitation L-3; pinned default/tiny builds suffice. No system install needed. |
| Q-ENV-002 | Reference built from export, empty revision.h | Resolved: target reference `GNU nano 9.3` branding for compatibility. Product README identifies Naro. |
| Q-IN-001 | Terminfo/keypad timing | Resolved architecture: ncursesw; Rust decoder handles nano's additional sequences. |
| Q-IN-002 / Q-KEY-003 | Linux VT modifier/ioctl paths | Implemented and qualified on a genuine guest Linux VT with emulated PS/2 input: 19 exact cases on both optimized builds, plus separate ioctl models. See ../validation/console-vm/README.md. Physical keyboard/operator scope remains deferred under L-2. |
| Q-IN-003 | Malformed CSI 2 consumes burst | Resolved: reproduce deterministic behavior. |
| Q-KEY-001 | Arbitrary `{function}` in string binds can crash source | Resolved: inapplicable functions do nothing safely; broader combinations not exhaustively inventoried. |
| Q-KEY-002 | Rc `preserve` leaves bindings present | Resolved: reproduce command-line/rc distinction. |
| Q-CLI-001 | glibc getopt diagnostics and locale | Resolved architecture: use native GNU option semantics/wording or reproduce exactly; translated libc-domain diagnostics require verification. |
| Q-CLI-002 | `-z` drops rc errors | Resolved: reproduce immediate exit behavior. |
| Q-REND-001 | Invisible blank-cell attributes | Resolved: N-ATTR-BLANK in doc 16; visible attributes remain significant. |
| Q-REND-002 | Width-table differences across libcs | Resolved envelope: host glibc widths; other platforms explicitly unverified. |
| Q-EDIT-002 | Hard wrap only on single-line cutbuffer paste | Resolved: reproduce; reference to this ID in EDIT-060 was a typo (fixed). |
| Q-UNDO-001 | Redo magic-line backspace marks modified | Resolved: reproduce UNDO-007. |
| Q-UNDO-002 | Hard-wrap undo in all chunk combinations | Open runtime gap; source specification stands. |
| Q-SRCH-001 | Zero-length spotlight hides current character | Resolved: reproduce. |
| Q-SRCH-002 | Leftmost-longest and empty matches | Resolved by Q-REGEX-001; corpus and TEST-SRCH-015 are acceptance evidence. |
| Q-FILE-001 | Mixed endings drop CR after LF first line | Resolved: reproduce. |
| Q-FILE-002 | Rewriting in place can truncate on interruption | Resolved: preserve metadata/link semantics; no unsolicited atomic-write change. Disk-full testing must be isolated. |
| Q-FILE-003 | Lock filename field is name as given | Resolved: reproduce. |
| Q-FILE-004 | Bad lock disables locking for buffer | Resolved: reproduce. |
| Q-BROWSE-001 | Sorting uses locale libc case conversion | Resolved architecture: native locale semantics. |
| Q-RC-001 | Boolean set ignores extra words | Resolved: reproduce. |
| Q-RC-002 | Syntax closes at set/bind/include etc. | Resolved: reproduce including lazy-load boundaries. |
| Q-SYN-001 | Libmagic path not probed | Open runtime gap; database version part of envelope. |
| Q-FEAT-001 | Internal speller uses external pipeline | Resolved target: same hunspell/spell → sort -f → uniq behavior, fixture stubs in tests. |
| Q-FEAT-002 | Justify keeps trailing blank without trimblanks | Resolved: reproduce. |
| Q-FEAT-003 | GNU scrolling credits Easter egg | Optional, excluded from default compatibility acceptance; static Naro attribution and the separate runtime proposal are in doc 19. |
| Q-CRED-001 | Naro credits proposal | Static CREDITS.md is documentation. The default-off `credits` feature implements plain-text `--credits`; exact stdout/status and default rejection are verified in `../validation/follow-up/host-extensions.json`. No default CLI change. |
| Q-TOOL-001 | TEST-NEXT-TOOL-003-SIGTERM/SIGHUP: the reference leaves a tool temp file after handled termination | Target removes the file and reaps its child under NEXT-TOOL-005 ownership. This intentional resource-cleanup difference is reported explicitly; no ordinary bytes, modes or exit assertions are masked. |
| Q-ROOT-NOHOME-001 | HOME unset, no passwd entry, opening ~/other | Source utils.c:copy_of(NULL)/strlen crashes with Code 11. Target preserves the literal pathname and remains usable. Dedicated source/candidate assertions retain all differences and require unchanged files and namespace identity; see `../validation/root-console/safety-no-home.json`. |
| Q-ENV-ROOT-001 | Root home-directory precedence | Resolved by doc 20: target shares cached effective-home resolution across rc, tilde, state and backup consumers. Genuine namespace uid 0/1000 and private NSS cases pass; see `../validation/root-console/root.json`. Host-root privilege behavior beyond these cases is not certified. |
| Q-TINY-001 | Naro tiny profile | Deferred optional work; match pinned tiny feature/binding tables and measure actual size/dependencies before advertising it. |
| Q-SIG-001 | Emergency paths relative to cwd | Clarification: normally cwd stays fixed, but `-o` changes it at startup; use filename as given relative to resulting cwd. |
| Q-SIG-002 | Rust panic recovery equivalent | Resolved architecture in 15 §5; verify restoration and emergency bytes with injected panic tests. |
| Q-PROMPT-002 | Username completion depends on passwd | Resolved test policy: do not assert host-specific username listings. |
| Q-BYTE-001 | Non-UTF-8 bytes under UTF-8 tmux | Resolved test policy: byte/internal-report assertions, not reliable screen goldens. |

Any later change to these decisions should include an ID, reason, reference
scenario and candidate evidence. Complete spec coverage is not the same as a
complete runtime corpus or complete implementation.
