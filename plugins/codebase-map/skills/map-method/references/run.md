# Run

Coordinators: before root lookup, run `python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/migrate_root.py" --project <project-root>`.
Require exit 0. Workers only resolve bindings; legacy roots/bindings activate migration load.

## Concurrent Runs Model

Every analysis is an isolated run; targets, sessions and re-analyses may overlap.

Within `.codebase-map/`:
- `runs.json`: active-run registry and latest completed run.
- `runs/<run-id>/`: isolated analysis directory containing:
  - `state.json`: phase tracking, flags and lineage.
  - `snapshot/manifest.json`: analyzed files, symbols and hashes.
  - `changes.json`, `changes.md`: incremental change set and claim consequences.
  - `knowledge/navigation.md`, `knowledge/documentation-leads.md`: Phase 0.
  - `01-structure.md` through `07-final-report.md`.
  - `partitions/<name>/...`, `08-interconnect-map.md`: team only.
- `state.json`, `01-structure.md` through `08-*.md`: latest published mirror.

1. **Identity.** `run-id` is the target-path slug + `-YYYYMMDD-HHMMSS`, or `--run-name <name>` normalized to `[a-z0-9-]`; append `-2`, `-3`, ... on collision.
2. **Isolation.** Write only inside `.codebase-map/runs/<run-id>/` while in progress. Concurrent runs never share files.
3. **Registry.** `runs.json` holds `{"schema": 2, "active": [{run_id, target, mode, started_at}], "latest_completed": "<run-id>"}`. Invoke `snapshot.py register $RUN_DIR` after state initialization or lineage changes; `snapshot.py unregister $RUN_DIR` on cancellation, partial delivery or failure. These commands and publication share one registry lock. Never write the registry directly or remove another run's entry.
4. **Publish.** Only the entry publishes after `snapshot.py check` reports `complete` and `may_publish` and every requested view is delivered. Its `publish` helper replaces the whole mirror of known phase files and `state.json`, then sets `latest_completed`, with locked rollback-protected replacement. Lite removes older `03`, `04`, `06`; classic removes an older team's `08-interconnect-map.md`. Partial, docs-only, single-phase and stopped runs never publish. Concurrent publishers preserve both archives; the last successful publisher owns the mirror.
5. **Resume.** `--resume-from [N] --run-name <exact-id>` selects the interrupted directory without collision suffixes. Keep mode and flags; a different mode requires a new run. The gate confirms earlier artifacts with same-run provenance, selects the first incomplete produced phase when N is omitted, and drops the invocation's stop. Interrupted/stopped runs retain recoverable state and never alter `latest_completed`. Root `state.json` with `current_phase` but no `runs.json` is pre-runs layout: offer migration into `runs/legacy-<date>/`.
6. **Consumers.** A workflow consuming a specific invocation must retain and propagate its immutable `.codebase-map/runs/<run-id>/`, never the mutable `.codebase-map/` mirror. The mirror serves latest-state consumers, including one-shot requests for the most recent published analysis.
7. **Lineage.** Every run writes `snapshot/manifest.json` of its analyzed tree, making it a possible parent. Incremental runs record the parent in `state.json -> parent_run` and their `runs.json` entry; this chain alone is the analysis history. `snapshot/`, `changes.json` and `changes.md` stay run-local and never publish to the root.

## Perimeter

Below its target, exclude what Git ignores, every directory whose name starts with a dot, and dependency/build output (`node_modules/`, `dist/`, `build/`, `target/`, `vendor/`, `venv/`, `__pycache__/`). `scripts/tree_scope.py` owns this general rule; every tree-walking script applies it: snapshot, cascade scan, usage search, comment scan and documentation review. Manual reading follows it too. A path the snapshot left out is not opened, globbed or cited in a phase file.

Analyze the target as given, including dot or Git-ignored directories. Dot files beside analyzed source (`.eslintrc.json`) remain, subject to the forbidden list in `evidence.md`. Git-tracked files are never ignored, regardless of patterns.

On the first update of a parent recorded before this rule, report newly excluded paths as removed and retire claims citing them, even if they remain on disk.

Declare exclusions: `snapshot.py scope <target>` prints them before a run; the manifest's `scope` keeps `git_ignore` as `applied` or `unavailable` (outside a work tree or Git did not answer; no ignore rule applied), `skipped.dot_directories` naming pruned dot directories and `skipped.git_ignored` counting ignored paths met. Scope confirmation and the final report repeat those figures. Name excluded `.github/` as the target to analyze CI.

## Team Mode Integration

Classic `/codebase-map:analyze` delegates declared phases to one isolated `codebase-map:map-analyst` context. Use the team variant for monorepos, multi-language repos or targets exceeding one context:

```
/codebase-map:team-analyze <target>
```

The team command:
1. Auto-detects partitions (workspaces, top-level dirs or language clusters) and shows concrete scope before dispatch. Fresh invocation authorization requires no `--yes`; unresolved choices or explicit approval requests get answerable questions through a permitted input tool or ordinary chat.
2. Spawns three workers per partition: Wave 1 Structure; Wave 2 Behavior + Quality. Wave 2 reads every partition's Wave 1 output to cite cross-partition contracts and flows directly.
3. Synthesizes a backward-compatible `01..07.md` set inside the run directory; the same all-mode gate and whole-mirror publication bind downstream consumers.
4. `codebase-map:semantic-interconnect-mapper` adds `08-interconnect-map.md` on the consolidated set: global Call Graph, Contracts, Invariants and Integration Hot-Spots.

### Choosing between classic and team

| Repo profile                                        | Use classic | Use team |
|-----------------------------------------------------|-------------|----------|
| Single package, < 200 files, one language           | ✓           |          |
| Monorepo (pnpm/npm/yarn/lerna/nx/turbo workspaces)  |             | ✓        |
| Multi-language (Python + TS, etc.) at top level     |             | ✓        |
| You want a global interconnection map produced in the same run |  | ✓        |
| You want `--phase N` or `--docs-only` control       | ✓           |          |
