# Finish a task (phase 7)

Review, authorize merge, verify the record, realign knowledge, close the workspace
and release its agenda row.

1. **Task.** Resolve the branch task through `run_state.py agenda --branch`
   with this session's id. Take over only after user confirmation the holder
   closed. Without a task, finish plainly without a record. Require every wave
   `sealed`; otherwise return to `references/waves.md`. Ask open questions first.
2. **Stage D.** Run `references/verify.md` on the whole candidate. A blocking
   result after remediation waves stops with findings/options. Report the last
   receipt's residual obligations.
3. **Merge.** Confirm stage D against the current project with `validate --current`;
   changed candidates return to stage D. Ask merge authorization, showing base,
   commits and verdict. Merge the task branch into base with a merge commit;
   fast-forward only on user request. Merge a moved base into the task first;
   stage D reviews the delta. Without authorization, record the command and stop.
   Record `integration.merged_sha` and branch review receipt in
   `integration.candidate_review`.
4. **Realign.** Follow `references/realign.md` with `merged_sha`.
5. **Close.** Record `merged_sha`, then complete the run, releasing its agenda
   while the worktree binding exists. Remove worktree/branch afterward; records
   remain in the main checkout. Push requires separate authorization.
   Use `references/retention.md` for requested output disposition.

Process-backed records additionally require bound-graph `VERIFIED_SUCCESS` and
admitted artifact bytes matching native reports. Include the unchanged `process`
binding in the result envelope. Graph success waives no stage D, candidate,
delivery or merge gate.
