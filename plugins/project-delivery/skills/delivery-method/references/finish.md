# Finish a task (phase 7)

Closes the current branch's task: the whole candidate reviewed, merged with
the user's authorization, the record verified, the knowledge realigned, the
workspace closed and the agenda row released.

1. **The task.** Resolve the branch's task from the agenda
   (`run_state.py agenda --branch`) with this session's id; a task another
   session holds is taken over only after the user confirms that session is
   closed. A branch without a task finishes plainly, without the
   record. Every wave must be `sealed`; an open one returns to
   `references/waves.md`. Ask open questions first.
2. **Stage D.** Run `references/verify.md` on the whole candidate. A
   blocking result after its remediation waves stops here with the finding
   and the options. Report the last receipt's residual obligations.
3. **Merge.** Confirm stage D against the current project (`validate --current`);
   a changed candidate returns to stage D. Ask merge authorization with base,
   commits and verdict. Merge
   the task branch into the base with a merge commit, or fast-forward when
   the user asks for it. A base that moved meanwhile is merged into the task
   branch first, and stage D reviews the delta. Without authorization, record
   the command and stop. Record `integration.merged_sha` and branch review
   receipt in `integration.candidate_review`.
4. **Realign.** Follow `references/realign.md` with `merged_sha`.
5. **Close.** After recording `merged_sha`, complete the run before removing
   the worktree, releasing the agenda while its binding exists. Then remove the
   worktree and branch; records remain in the main checkout. Pushing needs
   separate authorization. `references/retention.md` disposes of output on request.

A process-backed record also requires its bound graph to reach
`VERIFIED_SUCCESS`, with admitted worker artifact bytes matching the native
reports. Include the unchanged `process` binding in the result envelope.
Graph success does not waive any stage D, candidate, delivery or merge gate.
