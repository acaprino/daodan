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

Multiple analyses can run at the same time (different targets, different sessions, or a re-analysis while an older one is still in flight). Every analysis is an isolated **run**:

```
.codebase-map/
├── runs.json                          # registry: active runs + latest completed
├── runs/
│   └── <run-id>/                      # one directory per analysis run
│       ├── state.json                 # per-run phase tracking, flags, lineage
│       ├── snapshot/manifest.json     # the tree this run analyzed: files, symbols, hashes
│       ├── changes.json               # incremental runs: the change set since the parent
│       ├── changes.md                 # incremental runs: what changed and what it did to the claims
│       ├── knowledge/                   # Phase 0: navigation.md, documentation-leads.md
│       ├── 01-structure.md .. 07-final-report.md
│       ├── partitions/<name>/...      # team mode only
│       └── 08-interconnect-map.md     # team mode only
├── state.json                         # mirror of the latest published run
└── 01-structure.md .. 08-*.md         # mirror of the latest published run
```

Rules:

1. **Run identity.** `run-id` = slug of the target path + `-YYYYMMDD-HHMMSS`, or the value of `--run-name <name>` (normalized to `[a-z0-9-]`; on collision append `-2`, `-3`, ...).
2. **Isolation.** A run writes ONLY inside `.codebase-map/runs/<run-id>/` while in progress. Concurrent runs never share files.
3. **Registry.** `runs.json` holds `{"schema": 2, "active": [{run_id, target, mode, started_at}], "latest_completed": "<run-id>"}`. After state initialization or lineage changes, invoke `snapshot.py register $RUN_DIR`. On cancellation, partial delivery or failure invoke `snapshot.py unregister $RUN_DIR`. These commands and publication share one registry lock. Never write the registry directly or remove another run's entry.
4. **Publish step.** Only the entry publishes after `snapshot.py check` reports `complete` and `may_publish`, and every requested view is delivered. Its `publish` helper replaces the whole mirror of known phase files and `state.json`, then sets `latest_completed`, with locked rollback-protected replacement. A lite run removes older `03`, `04` and `06`; a classic run removes an older team's `08-interconnect-map.md`. Partial, docs-only, single-phase and stopped runs never publish. The mirror is the downstream latest-state contract; invocation-specific consumers retain the run directory. Concurrent publishing preserves both archives; the last successful publisher owns the mirror.
5. **Resume.** `--resume-from [N] --run-name <exact-id>` selects the interrupted directory without collision suffixes. Keep its mode and flags; a different mode is a new run. The gate confirms earlier artifacts with same-run provenance, selects the first incomplete produced phase when N is omitted, and drops an invocation's stop. Interrupted or stopped runs retain recoverable state; neither alters `latest_completed`. A root `state.json` with `current_phase` but no `runs.json` is a pre-runs layout: offer migration into `runs/legacy-<date>/`.
6. **Mirror is for latest-state consumers only.** `.codebase-map/` is a mutable convenience mirror of the latest published run. It MUST NOT be used by an orchestrated workflow to consume the output of a specific Codebase Map invocation: rule 4 makes the root mirror owned by whichever run published last, so a concurrent run can replace it between production and consumption. A workflow that started a run and then consumes it MUST retain and propagate the immutable run directory `.codebase-map/runs/<run-id>/`. The general form: a specific invocation implies the immutable run directory, a latest-state consumer implies the mirror. One-shot commands asking for the most recent published analysis are correct on the mirror.
7. **Lineage.** Every run writes `snapshot/manifest.json`, the structural record of the tree it analyzed, which makes it a possible parent for a later run. An incremental run records its parent in `state.json -> parent_run` and in its `runs.json` entry. The chain of those values is the analysis history, and no other structure holds it. A mirror consumer never needs any of this: `snapshot/`, `changes.json` and `changes.md` stay in the run directory and are never published to the root.

## Perimeter

The Codebase Map never analyzes three things below its target: what Git ignores, any directory whose name starts with a dot, and dependency or build output (`node_modules/`, `dist/`, `build/`, `target/`, `vendor/`, `venv/`, `__pycache__/`). `scripts/tree_scope.py` owns the rule, and every script that walks a tree applies it: the snapshot, the cascade scan, the usage search, the comment scan and the documentation review. Reading by hand follows it too. A path the snapshot left out is not opened, globbed or cited in a phase file.

The target itself is analyzed as given. Naming a dot directory, or a directory Git ignores, as the target is how its content gets a Codebase Map of its own. A dot file beside analyzed source (`.eslintrc.json`) is not a directory and stays, subject to the forbidden list in `evidence.md`. A file Git tracks is never ignored, whatever pattern it matches, because Git does not ignore what it tracks.

The rule exists because tools write beside the code they work on: run records under `.daodan/`, a review under `.team-review/`, editor settings, caches. Counted as project files they enter every later change set, and an incremental update of an untouched project asks for a full analysis. A parent run recorded before this rule holds paths the perimeter now leaves out. Its first update reports them as removed and retires the claims that cite them: they left the inventory, whether or not they left the disk.

What the rule leaves out is declared, never silent. `snapshot.py scope <target>` prints it before a run starts, and the manifest's `scope` block keeps it: `git_ignore` is `applied`, or `unavailable` when the target is in no work tree or git did not answer, in which case no ignore rule was applied; `skipped.dot_directories` names the dot directories the walk pruned; `skipped.git_ignored` counts the ignored paths it met. The scope confirmation and the final report repeat those figures. `.github/` holds a project's CI: a reader who needs it analyzed must be able to see that it was not, and can name it as a target.

## Team Mode Integration

The classic `/codebase-map:analyze` entry delegates its declared phases to one isolated `codebase-map:map-analyst` context. For monorepos, multi-language repos, or any target where one context would have to hold too much, switch to the team variant:

```
/codebase-map:team-analyze <target>
```

The team command:
1. Auto-detects partitions (workspaces, top-level dirs, or language clusters) and shows the concrete scope before dispatch. A fresh run proceeds on the invocation's authorization, without requiring `--yes`; an unresolved choice or an explicit request for approval gets an answerable question, through a permitted input tool or ordinary chat.
2. Spawns three workers per partition in two waves (Wave 1 = Structure; Wave 2 = Behavior + Quality). Wave 2 workers read every partition's Wave 1 output, so cross-partition contracts and flows can be cited directly.
3. Synthesizes a backward-compatible `01..07.md` set inside the run directory; the same all-mode gate and whole-mirror publication bind it to downstream consumers.
4. Adds `08-interconnect-map.md` produced by `codebase-map:semantic-interconnect-mapper` on top of the consolidated set, giving a global Call Graph, Contracts, Invariants, and Integration Hot-Spots view.

### Choosing between classic and team

| Repo profile                                        | Use classic | Use team |
|-----------------------------------------------------|-------------|----------|
| Single package, < 200 files, one language           | ✓           |          |
| Monorepo (pnpm/npm/yarn/lerna/nx/turbo workspaces)  |             | ✓        |
| Multi-language (Python + TS, etc.) at top level     |             | ✓        |
| You want a global interconnection map produced in the same run |  | ✓        |
| You want `--phase N` or `--docs-only` control       | ✓           |          |
