# Save-progress repair and renewed qualification

The production fix is commit `16f6398968adc1f815055a4413cf0465aed28126`.
This record supersedes the earlier candidates. Full host/Ubuntu matrices and
the complete 99/99 technical gate pass. Independent review is tracked in the
final qualification sidecar and release review packet.
No release is published or authorized for publication.

The deterministic development comparison is 13/13 exact with all assertions;
the old frozen candidate fails all 13. Cases cover regular saves, FIFO open and
write, narrow/minibar/zero screens, German/color, direct save, append/prepend,
selection and open/sync failures. Expectations were observed on pinned nano.
Private syscall gates hold the operation until the snapshot, avoiding settled
screen timing. Both references and candidates receive identical scenarios.

Both newly frozen candidates passed 19/19 genuine guest-VT comparisons, and
transport passed 6/6. Raw recordings and controller logs remain in
`target/save-progress-qualification-2026-10-30/console/`. The disposable owned
VM exited zero. These are not physical-keyboard trials.

Full candidate inputs: `target/release-freeze-save-progress-2026-10-30/`.
Full matrix outputs: `target/save-progress-qualification-2026-10-30/`.
Development attempts: `target/save-progress-2026-10-30/ATTEMPTS.md`.
The freeze and full matrix evidence have verified backups outside target; see
[freeze backup](freeze-backup.json) and [qualification backup](qualification-backup.json).
These are same-disk copies. Final packaging receipts are recorded separately.

Fresh complete qualification retains the historical corpus and declared
exceptions. All five additional suites pass exactly in each environment:
wrap-undo 58, filter 6, release-fixes 15, step3-gaps 40, save-progress 13.
The [collector](closure/gate.json) passes 99/99 checks. CLI 38, regex 162,
recovery, signals, large files and package/source checks all pass. The frozen
production commit has [successful CI](production-ci.json). New archive contents
must receive fresh package verification; the initial matrix packages are retained
as evidence and are not the selected final downloads.
