# Continue a task

Resume a branch task across sessions and machines.

1. **Find it.** `run_state.py agenda --branch <current branch>`. Without a row,
   `Daodan-Task:` trailers and the branch record show prior work; offer an
   adoption run with that record as objective. A branch holds one open task.
2. **Take it.** `resume` with this session and current authorizations. After a
   commit crash, resume reconciles only matching parent, bytes, owned paths and
   run trailer; otherwise it refuses changes. Refuse another session's task
   unless the user confirms it closed, then take over.
3. **Answer.** Record command text against pending questions, source `continue`,
   before anything else. Ask remaining questions one per turn.
4. **Go on.** Restart at the agenda phase's first open step: unsealed wave,
   undelivered review or unauthorized merge. Verify and review a changed
   candidate's delta before the next wave.
