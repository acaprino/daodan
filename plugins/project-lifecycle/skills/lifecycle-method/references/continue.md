# Continue a task

Resumes the current branch's task, in this session or another, on this
machine or another.

1. **Find it.** `run_state.py agenda --branch <current branch>`. No row on
   this branch: the commits carrying `Daodan-Task:` trailers and the
   branch's record say what was done; offer to open a run
   that adopts them, with the record as its objective. Several rows cannot
   occur: a branch holds one open task.
2. **Take it.** `resume` with this session's id and current authorizations.
   A task another session holds is refused: say which session and since
   when, and take it over only after the user confirms that session is
   closed.
3. **Answer.** Text given with the command answers the pending questions in
   order: record each with `answer`, source `continue`, before anything else.
   A question still unanswered is asked again, one per turn.
4. **Go on.** Restart at the phase the agenda names, from its first open
   step: the first unsealed wave, the review not yet delivered, the merge not
   yet authorized. A changed candidate (new commits, edits since the last
   record) is verified first and its delta reviewed before the next wave.
