# NARO next steps — Codex development ownership

Current state: the Pi-review marked-wrap, filter and evidence-validator defects
are fixed for the recorded inputs. See [review](NARO_PI_TEST_REVIEW.md) and
[verification/commits](NARO_DEVELOPMENT_PROGRESS.md). The prior local plan was
read and preserved before replacement; its confirmed fixes are incorporated.
The historical 39-case checkpoint is not complete parity certification.

Codex is the sole implementation, permanent-test, specification and GitHub
owner. Pi/DeepSeek, OpenCode/MiniMax and GLM are independent testing agents only.
The binding next assignment is [NARO_TEST_AGENT_HANDOFF.md](NARO_TEST_AGENT_HANDOFF.md)
and its [start prompt](NARO_TEST_AGENT_START_PROMPT.md). Testing agents must
report defects to Codex rather than change implementation or expectations.

1. **Close combined terminal/history gaps.** Review independent evidence for
   hard+soft wrap (`-b -S`), scrolled viewports, resize mid-history, preferred
   column, view mode, `-L`, magic-EOF Backspace and a subsequent fill-accepted
   wrap. Pi's earlier similarly named cases did not reach every claimed branch.
   Fix measured mismatches only; do not redesign history speculatively.
2. **Validate structural callers.** Extend decisive wrap-lifetime checks through
   file/command insertion, search replacement, justification, formatter/speller
   and failed tools. Keep each surviving/detached node policy aligned with nano.
   Cover marked-filter reverse/empty/whole-buffer, empty/multiline/NUL output,
   saved points and divergence. The six current filter cases are finite coverage.
3. **Extend position/encoding evidence.** Marks before/at/after splits and
   removed prefixes; Unicode quote leads/blanks, literal tabs, CJK/combining
   characters, malformed UTF-8 and NUL; exact bursts versus individual keys;
   successive cuts, paste and undo/redo. Preserve the reference's byte/display
   width distinctions and quote-prepend quirk until contrary oracle evidence.
4. **Broaden memory and console qualification.** The critical five-case ASan
   run covers instrumented Rust/native bridge only. Extend to structural and
   stress cases, then refresh genuine VT/portable release qualification for a
   release candidate. Miri's unsupported FFI and unavailable Valgrind are not
   safety findings. Physical-keyboard and other-platform scope stays open.
5. **Maintain honest evidence.** Keep exact scenario membership and independent
   recomputation in the report gate; never substitute report booleans for
   artifacts or treat hashes as signed authenticity. Keep the nine unresolved
   audit citations listed as gaps until real scenarios/evidence exist. Add
   appropriate oracle scenarios, not invented coverage records.

Do not weaken assertions, normalize real differences or invent deviations.
Q-UNDO-002 remains partial. Default, tiny and all-features are different test
configurations. A release requires refreshed packaging and portable/console
checks; this development push does not publish or replace a system editor.
