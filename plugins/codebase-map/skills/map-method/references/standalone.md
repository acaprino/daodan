# Map consumption

Use this path for read-only evidence consumption during ordinary project work
and inside analyze or other composed workflows, with or without a Daodan command.
This unit grants no run creation, snapshot refresh, card
deepening or publication. Standalone consumption never performs them; a composed
workflow performs only operations already authorized by its own method.

1. **Locate existing evidence.** With MCP, call `codebase_map_runs`, then
   `codebase_map_status` for the selected completed run. Without MCP, inspect
   `.codebase-map/runs.json`, the published `state.json` and the root mirror.
   Latest-state questions may use the mirror; work bound to an invocation keeps
   that exact run directory. Do not select a partial run as a completed analysis.
2. **Navigate before scanning.** Use the task table in `reading.md`, section
   `Task views`. Query `codebase_map_outline`, `codebase_map_graph`,
   `codebase_map_meta_query` and `codebase_map_artifact` as pertinent, or search
   the run's Markdown and the project with ordinary tools. Locate symbols,
   contracts, flows and documentation leads before broadly reading source.
3. **Verify and bound the work.** Before editing, call
   `codebase_map_edit_impact` on affected symbols when available. Read exact
   target and neighbor source with `codebase_map_read` or ordinary file tools
   only when the consumer may read source; artifact-only consumers stay within
   their declared inputs. The map supplies leads, not verdicts; verify material
   behavior and business rules against current source. Static evidence
   establishes no runtime behavior.
4. **Recover by consumer role.** `codebase_map_diff` compares a bound snapshot
   with current source. A newer snapshot does not refresh an older report or
   card. A read-only consumer discloses absent, incomplete, inaccessible or
   drifting evidence and continues with ordinary repository exploration, never
   starting analysis, update or deepening implicitly. A composed producer
   instead follows its authorized refresh, re-derivation or blocking procedure;
   this unit never replaces those obligations.
