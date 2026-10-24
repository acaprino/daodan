# Finish a task (phase 7)

Closes the current branch's task: the whole candidate reviewed, merged with
the user's authorization, the record promoted, the knowledge realigned, the
workspace closed and the agenda row released.

1. **The task.** Resolve the branch's task from the agenda
   (`run_state.py agenda --branch`) with this session's id; a task another
   session holds is taken over only after the user confirms that session is
   closed. A branch without a task finishes plainly, without the
   record. Every wave must be `sealed`; an open one returns to
   `references/waves.md`.
2. **Stage D.** Run `references/verify.md` on the whole candidate. A
   blocking result after its remediation waves stops here with the finding
   and the options. Report the last receipt's residual obligations.
3. **Merge.** Confirm that the stage D result validates against the current
   project (`validate --current`); a changed candidate returns to stage D.
   Ask once for merge authorization, showing base, commits and verdict. Merge
   the task branch into the base with a merge commit, or fast-forward when
   the user asks for it. A base that moved meanwhile is merged into the task
   branch first, and stage D reviews the delta. Without authorization, record
   the exact merge command and stop. Record `merged_sha`.
4. **Realign.** Follow `references/realign.md` with `merged_sha`.
5. **Close.** Only after the merge is recorded, remove the preflight worktree
   and its branch, then complete the run, which releases its
   agenda row. Pushing is a separate authorization. The run's own output is
   disposed of only through `references/retention.md`, on request.
