# Run

## Concurrent Runs Model

Multiple analyses can run at the same time (different targets, different sessions, or a re-analysis while an older one is still in flight). Every analysis is an isolated **run**:

```
.codebase-xray/
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
2. **Isolation.** A run writes ONLY inside `.codebase-xray/runs/<run-id>/` while in progress. Concurrent runs never share files.
3. **Registry.** `runs.json` holds `{"schema": 2, "active": [{run_id, target, mode, started_at}], "latest_completed": "<run-id>"}`. Commands register their run at start and update the registry at completion. Read-modify-write it; never blindly overwrite entries you did not create.
4. **Publish step.** On successful completion, the orchestrating command copies the run's `01..0N.md` files and `state.json` to the `.codebase-xray/` root and sets `latest_completed`. The root mirror is the **downstream contract**: consumers (`/senior-review:team-review`, `/senior-review:code-review`, `/project-knowledge:guide`, `/project-knowledge:instructions --create`) keep reading `.codebase-xray/01-structure.md` etc. unchanged. If two runs finish concurrently, the last one to publish owns the root mirror; both remain intact under `runs/`.
5. **Resume.** On invocation, the command reads `runs.json`: active runs are offered for resume; completed runs can be archived or re-published. A root `state.json` containing `current_phase` with no `runs.json` present is a pre-runs legacy layout: offer to migrate it into `runs/legacy-<date>/` before starting.
6. **Mirror is for latest-state consumers only.** `.codebase-xray/` is a mutable convenience mirror of the latest published run. It MUST NOT be used by an orchestrated workflow to consume the output of a specific X-ray invocation: rule 4 makes the root mirror owned by whichever run published last, so a concurrent run can replace it between production and consumption. A workflow that started a run and then consumes it MUST retain and propagate the immutable run directory `.codebase-xray/runs/<run-id>/`. The general form: a specific invocation implies the immutable run directory, a latest-state consumer implies the mirror. One-shot commands asking for the most recent published analysis are correct on the mirror.
7. **Lineage.** Every run writes `snapshot/manifest.json`, the structural record of the tree it analyzed, which makes it a possible parent for a later run. An incremental run records its parent in `state.json -> parent_run` and in its `runs.json` entry. The chain of those values is the analysis history, and no other structure holds it. A mirror consumer never needs any of this: `snapshot/`, `changes.json` and `changes.md` stay in the run directory and are never published to the root.

## Perimeter

The X-ray never analyzes three things below its target: what Git ignores, any directory whose name starts with a dot, and dependency or build output (`node_modules/`, `dist/`, `build/`, `target/`, `vendor/`, `venv/`, `__pycache__/`). `scripts/tree_scope.py` owns the rule, and every script that walks a tree applies it: the snapshot, the cascade scan, the usage search, the comment scan and the documentation review. Reading by hand follows it too. A path the snapshot left out is not opened, globbed or cited in a phase file.

The target itself is analyzed as given. Naming a dot directory, or a directory Git ignores, as the target is how its content gets an X-ray of its own. A dot file beside analyzed source (`.eslintrc.json`) is not a directory and stays, subject to the forbidden list in `evidence.md`. A file Git tracks is never ignored, whatever pattern it matches, because Git does not ignore what it tracks.

The rule exists because tools write beside the code they work on: run records under `.daodan/`, a review under `.team-review/`, editor settings, caches. Counted as project files they enter every later change set, and an incremental update of an untouched project asks for a full analysis. A parent run recorded before this rule holds paths the perimeter now leaves out. Its first update reports them as removed and retires the claims that cite them: they left the inventory, whether or not they left the disk.

What the rule leaves out is declared, never silent. `snapshot.py scope <target>` prints it before a run starts, and the manifest's `scope` block keeps it: `git_ignore` is `applied`, or `unavailable` when the target is in no work tree or git did not answer, in which case no ignore rule was applied; `skipped.dot_directories` names the dot directories the walk pruned; `skipped.git_ignored` counts the ignored paths it met. The scope confirmation and the final report repeat those figures. `.github/` holds a project's CI: a reader who needs it analyzed must be able to see that it was not, and can name it as a target.

## Team Mode Integration

The classic `/codebase-xray:analyze` command runs every phase inline in one context on a single target. For monorepos, multi-language repos, or any target where one context would have to hold too much, switch to the team variant:

```
/codebase-xray:team-analyze <target>
```

The team command:
1. Auto-detects partitions (workspaces, top-level dirs, or language clusters) and shows the concrete scope before dispatch. A fresh run proceeds on the invocation's authorization, without requiring `--yes`; an unresolved choice or an explicit request for approval gets an answerable question, through a permitted input tool or ordinary chat.
2. Spawns three workers per partition in two waves (Wave 1 = Structure; Wave 2 = Behavior + Quality). Wave 2 workers read every partition's Wave 1 output, so cross-partition contracts and flows can be cited directly.
3. Synthesizes a backward-compatible `01..07.md` set inside the run directory; the publish step mirrors it to the `.codebase-xray/` root, so any downstream consumer (`/senior-review:team-review`, `/project-knowledge:guide`, `/project-knowledge:instructions --create`) picks it up without changes.
4. Adds `08-interconnect-map.md` produced by `codebase-xray:semantic-interconnect-mapper` on top of the consolidated set, giving a global Call Graph, Contracts, Invariants, and Integration Hot-Spots view.

### Choosing between classic and team

| Repo profile                                        | Use classic | Use team |
|-----------------------------------------------------|-------------|----------|
| Single package, < 200 files, one language           | ✓           |          |
| Monorepo (pnpm/npm/yarn/lerna/nx/turbo workspaces)  |             | ✓        |
| Multi-language (Python + TS, etc.) at top level     |             | ✓        |
| You want a global interconnection map produced in the same run |  | ✓        |
| You want `--phase N` or `--docs-only` control       | ✓           |          |
