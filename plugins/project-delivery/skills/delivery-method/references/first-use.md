# First use

Before writing, ask whether to keep decision records and analyze
the project (ADR-0005). These choices authorize their outputs.

1. **Probe.** `run_state.py first-use --project ROOT` through
   `work-controller:work-record` reads only. `first_use: false` ends this
   step; the project keeps records exactly when `records` is true.
2. **Ask** both in one message through the host's question tool:
   - Decision records: each design decision kept under `docs/adr/` with its
     examples, rejected alternatives and invariants, so later tasks inherit
     it. No (the default), or yes, which also commits the new index alone.
   - Analysis now: no; lite (structure, interfaces and risks, fewer tokens);
     deep (every phase of the map, more tokens on a large project).

   An analysis command asks only the depth, and not a depth the user named;
   `/daodan:record-decision` asks only the analysis. For an unscaffolded project, record
   choices in the brainstorm run; defer index commit and analysis until the
   repository and source exist. Initialization consumes these saved choices.
   Without a question tool, open the command's run
   (operation `assess` for a command that keeps none) holding only these two
   questions, close the turn listing them, and continue at step 3 on resume.
3. **Records.** Yes, once the repository exists: load `project-delivery:adr-method`, run `init-index`,
   and commit `docs/adr/README.md` alone on the current branch, so a task
   worktree branches with it. No: nothing under `docs/adr/`.
4. **Analysis.** With source, lite or deep: the map as `references/init.md` step 1 runs it,
   at depth `lite` or `full`. No: no `.codebase-map/`; a later step that needs
   the map builds it at lite depth on its scope, without asking.

Once `.daodan/` or `.codebase-map/` exists the probe returns `first_use: false`,
so nobody asks again. A project without records never hears of them;
`/daodan:record-decision` turns them on later by creating the index.
