# Continue a task

Load `worktree-manager:worktree-method`; reconcile run, Git identity, catalog and
holder at the original project path.

1. **Find.** `run_state.py agenda --project <root> --branch <branch>`.
   Detached: replace `--branch` with `--worktree <original-checkout>`; add
   `--run-id <task>` when known. Match run/project/holder. Check the original
   agenda before offering `Daodan-Task:` trailer/branch-record adoption.
   One open task per branch.
2. **Take.** `resume` with session/current authorizations. Commit recovery requires
   matching parent, bytes, owned paths and trailer. Integration recovery requires
   delivered branch review, unchanged raw snapshot/identity, exact verified
   detached result and preserved source branch. Refresh candidate; preserve
   receipts/gates; verify stale final gates. Refuse other changes. Take over only
   after the user confirms the previous session closed.
3. **Answer.** Record command text against pending questions first, source
   `continue`; ask remaining questions one per turn.
4. **Continue.** Restart the first open wave/review/merge; verify and review
   changed bytes before the next wave.

Retry failed setup/cleanup, never verified integration. Completed records remain
immutable; cleanup receipts stay outside.

For `process`, follow `work-controller:work-record`'s `references/process-runtime.md`:
validate identity and reconcile attempts/host handles before redispatch.
Legacy records retain their method.
