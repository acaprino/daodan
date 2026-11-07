# Map consumption

Consume evidence read-only inside analyze or other composed workflows and ordinary
work, with or without commands. This unit grants no run creation, snapshot refresh,
card deepening or publication. Standalone consumers never perform them; composed
workflows require their method's authorization.

1. **Locate evidence.** Call `codebase_map_runs`, then `codebase_map_status` on
   a completed run. Without MCP inspect `.codebase-map/runs.json`, published
   `state.json` and root mirror. Latest-state questions may use mirrors;
   invocation-bound work keeps its exact run directory. Exclude partial runs.
2. **Navigate before scanning.** Use `reading.md`'s `Task views`; follow
   `locate.md`: `codebase_map_search` request names, then `codebase_map_outline`
   and `codebase_map_graph` hits. Use `codebase_map_meta_query` and
   `codebase_map_artifact` as pertinent, or search run Markdown and project.
   Locate symbols, contracts, flows and documentation leads before broad source
   reading.
3. **Verify before editing.** Call `codebase_map_edit_impact` on affected symbols
   when available. Authorized consumers read exact target and neighbor source via
   `codebase_map_read` or file tools; artifact-only consumers stay within their
   declared inputs. Maps supply leads, not verdicts: verify material behavior and
   business rules against current source. Static evidence proves no runtime behavior.
4. **Recover.** `codebase_map_diff` compares bound snapshot with current source;
   newer snapshots never refresh older reports or cards. A read-only consumer
   discloses absent, incomplete, inaccessible or drifting evidence and continues
   with ordinary repository exploration, never starting analysis, update or
   deepening implicitly. A composed producer instead follows its authorized refresh,
   re-derivation or blocking procedure; these obligations remain.
