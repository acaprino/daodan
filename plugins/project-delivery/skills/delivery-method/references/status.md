# Status

Shows where the project's work stands. It reads and never writes, and opens
no run.

1. **Agenda.** `run_state.py agenda` from the main checkout: for each task its
   kind and objective, branch, phase, sealed waves out of the total, record,
   last review, unanswered questions, and who holds it since when. A row
   whose holder has been idle for a day is flagged as possibly abandoned.
2. **Worktrees.** Load `worktree-manager:worktree-method`: join all Git worktrees
   and catalog descriptions/tags to the agenda. Include branch distance. Fetch
   only when requested; unavailable PR/CI information remains unknown.
3. **Map.** The bound run, its head against `HEAD`, and the stale paths from
   `snapshot.py diff --verify`.
4. **Records.** `adr_tool.py validate --sha HEAD_SHA` through
   `project-delivery:adr-method`: the count in each state, and each `drifted`
   record with its changed files, or never verified.

One screen, newest task first, then the next step for each task.
