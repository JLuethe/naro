# Attempts and retries

1. Freeze verification — passed.
2. First host harness invocation under default sandbox — failed to create tmux session because access to the tmux socket returned `Operation not permitted`. This was infrastructure failure; no editor verdict.
3. Host rerun with scoped escalation — 13/13 pass. A later repeat used a private `NANOSPEC_WORK` root and again passed 13/13.
4. Ubuntu `run` — startup failed because the output subdirectory already existed from the partial attempt; preserved.
5. Ubuntu `run2` — harness launched but case assertions failed and execution did not produce a complete report; environment did not match qualification setup; preserved, not candidate verdict.
6. Ubuntu `run3` — only en_US locale configured; German case timed out. Preserved, not candidate verdict.
7. Ubuntu `run4` — locale setup allowed four cases to pass, but run was incomplete when the remaining environment setup was insufficient; preserved.
8. Ubuntu `run5` — 12/13 comparison acceptance; German case ran candidate from `/frozen/naro`, so its runtime locale asset lookup did not resolve. The candidate displayed English while reference displayed German. Diagnosed by comparing paths and output; preserved and not treated as candidate mismatch.
9. Ubuntu `run6` — corrected qualification startup, with private source tree, candidate at `/work/naro/target/release/naro`, pinned installed nano at `/work/reference`, all locale definitions and private locpath adjustment. 13/13 pass.
10. Old binary negative control — first path guess was wrong and failed before execution; corrected path run in `old-control2` completed: old NARO failed all 13 while nano checks passed.
11. Intentionally wrong assertion — scratch nanoharness first showed the failed row assertion. Scratch check_follow_up returned harness statuses 1; strict collector then rejected it for failed statuses and expectations. Both attempts and logs retained under `wrong-assertion/`.

12. Whole-release `collect_closure.py` run at 2026-10-31 06:25:33–06:25:42 UTC against all mapped inputs. Exit 0; 99 checks passed, none failed. Command and output are preserved in `whole-release-collector/COMMAND.log`; output directory was newly created.
