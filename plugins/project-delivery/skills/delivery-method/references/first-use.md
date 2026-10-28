# First use

Before writing, ask whether to analyze the project; the answer authorizes its
output (ADR-0008). Decision records are not asked here:
`project-delivery:adr-method` asks at the first settled decision.

1. **Probe.** `run_state.py first-use --project ROOT` through
   `work-controller:work-record` reads only. `first_use: false` ends this
   step.
2. **Ask** through the host's question tool whether to analyze now: no; lite
   (structure, interfaces and risks, fewer tokens); deep (every phase of the
   map, more tokens on a large project).

   Never ask a depth the user named. For an unscaffolded project, record the
   choice in the brainstorm run and defer analysis until source exists.
   Initialization consumes this saved choice. Without a question tool, open
   the command's run (operation `assess` for a command that keeps none) holding
   only this question, close the turn naming it, and continue at step 3 on
   resume.
3. **Analysis.** With source, lite or deep: the map as `references/init.md` step 1 runs it,
   at depth `lite` or `full`. No: no `.codebase-map/`; a later step that needs
   the map builds it at lite depth on its scope, without asking.

Once `.daodan/runs/` or `.codebase-map/` exists the probe returns
`first_use: false`, so nobody asks again.
