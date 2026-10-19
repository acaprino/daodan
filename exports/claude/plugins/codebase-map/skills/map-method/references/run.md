<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when a required one is off.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

# Run

Coordinators: before root lookup, run `python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/migrate_root.py" --project <project-root>`.
Require exit 0. Workers only resolve bindings; legacy roots/bindings activate migration load.

## Concurrent Runs Model

Runs are isolated; targets and sessions may overlap.

Within `.codebase-map/`:
- `runs.json`: active-run registry and latest completed run.
- `runs/<run-id>/`: isolated analysis directory containing:
  - `state.json`: phase tracking, flags and lineage.
  - `snapshot/manifest.sqlite`: default inventory; JSON: `snapshot/manifest.json`. `snapshot.py resolve` selects the state's format/path.
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
7. **Lineage.** Each run's declared snapshot makes it a possible parent. Incremental runs record the parent in `state.json -> parent_run` and their `runs.json` entry; this chain alone is the analysis history. `snapshot/`, `changes.json` and `changes.md` stay run-local and never publish to the root.

## Perimeter

Below its target, exclude what Git ignores, every directory whose name starts with a dot, and dependency/build output (`node_modules/`, `dist/`, `build/`, `target/`, `vendor/`, `venv/`, `__pycache__/`). `scripts/tree_scope.py` owns this rule; every tree-walking script applies it: snapshot, cascade scan, usage search, comment scan and documentation review. Manual reading follows it. A path the snapshot left out is not opened, globbed or cited in a phase file.

Analyze the target as given, including dot directories; a Git-ignored target is its own root. Dot files beside analyzed source (`.eslintrc.json`) remain, subject to the forbidden list in `evidence.md`. Git-tracked files are never ignored, regardless of patterns.

On the first update of a parent recorded before this rule, report newly excluded paths as removed and retire claims citing them, even if they remain on disk.

Declare exclusions: `snapshot.py scope <target>` prints them before a run; the manifest's `scope` keeps `git_ignore` as `applied` or `unavailable` (outside a work tree or Git did not answer; no ignore rule applied), `skipped.dot_directories` naming pruned dot directories and `skipped.git_ignored` counting ignored paths met. Scope confirmation and the final report repeat those figures. Name excluded `.github/` as the target to analyze CI.

## Team Mode Integration

Classic `references/entry-analyze.md` delegates declared phases to one isolated `codebase-map:map-analyst` context. Use the team variant for monorepos, multi-language repos or targets exceeding one context:

```
/daodan:map-code <target>
```

The team entry:
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
