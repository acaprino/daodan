# Status

Shows where the project's work stands. It reads and never writes, and opens
no run.

1. **Agenda.** `run_state.py agenda` from the main checkout: for each task its
   kind and objective, branch, phase, sealed waves out of the total, record,
   last review, unanswered questions, and who holds it since when. A row
   whose holder has been idle for a day is flagged as possibly abandoned.
2. **Branches.** For each task branch, commits ahead of and behind the
   default branch; the default branch against its upstream after a fetch
   only when the user asked for it.
3. **Map.** The bound run, its head against `HEAD`, and the stale paths from
   `snapshot.py diff --verify`.
4. **Records.** `adr_tool.py validate` through `project-knowledge:adr-method`:
   active, proposed and superseded counts, and any record whose cited symbols
   changed since it was accepted.

One screen, newest task first, then the next step for each task.
