# Local service and MCP

## Startup and binding

The declared `codebase-map` server runs over stdio:

```text
uv run --no-config --no-project --script <installed-plugin-root>/skills/map/scripts/mcp_server.py --project <project-root>
```

`--no-config --no-project` keep `uv` from reading the analyzed project's
`uv.toml`, `pyproject.toml` or `.python-version`: a repository under analysis
never chooses the package index or interpreter of its own analyzer. Keep both
flags in any custom registration. `uv` provisions the official MCP Python SDK
2.x; the server requires Python 3.12 or later (`requires-python` header plus a
startup check). Parser dependencies stay optional with the CLI's diagnostics
and fallbacks; `mcp_service.py` and the build stay standard-library-only.

Build the map with the runtime that serves it: `codebase_map_create_run` on
this server, or `snapshot.py write` under the same `uv` environment. The lexical
index records the SQLite version and parser fingerprint that built it, so a map
written by another Python reads as `stale` (`codebase_map_index` rebuilds the
index; a different parser set needs a new run). Run creation also derives the
module graph beside the snapshot; a failed derivation records `modules_failed`
and `codebase_map_modules(refresh=true)` repairs it.

The project is fixed at startup: `--project`, or the working directory when
omitted, so a consumer that controls the launch passes it explicitly. `scope`
and `status` (hence `runs`) return the bound `project_root`; verify it before
creating a run. Every target is relative to the project; every run ID selects
exactly `.daodan/map/runs/<run-id>/` (or `<store>/runs/<run-id>/`). Foreign
paths, traversal, symlinks and Windows junctions are rejected; clients supply no
executable, output root or manifest path. Helper subprocesses run from the helper
directory and resolve `git` from absolute `PATH` entries only.

### Custom analysis store

`--store <project-relative-path>` (or `MapService(project_root, store)`), fixed
for the server's lifetime, moves the whole store: runs, registry, locks and the
published mirror. The path is exact POSIX, starts with a dot directory so every
perimeter already excludes it, and may not be `.daodan/map`, reuse `.git` or a
device name; a target inside it is refused. The first write creates the marker
`.daodan-map-store.json`, `{"schema": "daodan/codebase-map-store/v1",
"store": "<path>"}`, which binds the store to its project: `snapshot.py`
commands accept a run directory in such a store and derive the project from
it. A non-empty directory without the marker is refused, a marker naming another
path invalidates every run in the store, and a lost marker is recovered by
rewriting that exact marker. Shell workflows and worker roles name
`.daodan/map/`, so they use a custom store only when the host hands them the
exact run directory; the canonical mirror and its consumers do not see such
runs. The host registers the server. Verify its connection before calling these
tools; a shell workflow uses its existing commands and needs no MCP connection.

## Tools

Every tool returns structured JSON and reports errors as MCP tool failures.

| Tool | Inputs and behavior |
|---|---|
| `codebase_map_scope` | `target="."`: inventory counts, languages and declared exclusions; starts no analysis |
| `codebase_map_create_run` | `target`, exact `run_id`, optional `depth="full"` or `"lite"`, `critical`, `comments`, `docs_only`, `phase`, `stop_after`, `format="sqlite"` (or explicit `"json"`), `engine=true`: snapshot and prepared classic run, and the call-resolution engine pass started in the background beside the snapshot (`engine_started`, or `engine_unavailable` with its install line); `engine=false` skips it for this run, and its repairs too |
| `codebase_map_runs` | canonical runs and active registry in this project; an unreadable run is listed with `readable: false` and its `error` |
| `codebase_map_status` | `run_id`: current `state` and canonical delivery `check`; missing-source diagnostics keep history observable; `engine`: the engine store state (`running`, `fresh`, `sampled`, `stale`, `failed`, `unavailable`, `stopped`, `off`), the same per language in `languages` (`answered` of `population` while a stage publishes; an `unavailable` language carries its `install` line), and `resolution`, resolved over resolvable calls with `by_language` |
| `codebase_map_outline` | `run_id`, optional `path`, `pattern` (literal case-insensitive substrings separated by `\|`, never a regular expression), `limit=100`: bound symbol metadata |
| `codebase_map_graph` | `run_id`, optional `paths`, `hops=2`, `limit=100`: verified static graph and diagnostics |
| `codebase_map_read` | `run_id`, `requests`: verified source blocks; a result above 4,000,000 characters is refused, so split the request |
| `codebase_map_modules` | `run_id`, optional `query`, `refresh=false`, `brief=false`, `limit=10`, `proposals`, `replace_proposals=false`: the module graph beside the bound snapshot (`references/modules.md`). Without arguments: graph state, every module with provenance (`build`, `declared`, `proposed`), kind, location, status, paths and members, the edges (`declares`, `contains`, `imports`, `calls`, `uses`) and gaps. `query`: candidates for a name, alias or path with paths, files, members, `relations`, `read_scope`, evidence and gaps, and a `status` (`resolved`, `needs_clarification`, `incomplete`, `unknown`) that never promotes an inferred module. `brief`: what a model needs before proposing. `proposals`: records `{name, kind, location, responsibility, members, evidence}` beside the snapshot, verifies every member and rebuilds; `replace_proposals` drops earlier ones. `refresh` rebuilds a missing or stale graph. Writes `modules.json`, `modules.md` and `proposals.json`, so it is not annotated read-only |
| `codebase_map_search` | `run_id`, `query`, optional `anchors` (at most 100, each `entity_id`, `path` with `line`, or `symbol`), `limit=20` (1 to 100): the run's lexical index ranked for the query, exact symbol and traceback matches first, then FTS5 subtoken matches; records carry `entity_id`, `kind`, `path`, `start_line`, `end_line`, `signatures`, `provenance` and `score`, never source. Read-only; the binding of the index is checked but the tree is not reread, so read hits with `codebase_map_read`. A `missing`, `stale` or `corrupt` index returns no results and a `gaps` entry naming `codebase_map_index`; see `locate.md` for the loop |
| `codebase_map_index` | `run_id`, optional `check=false`, `break_lock=false`, `environment` (`auto` by default: the project's Python environment or one Daodan builds once from the declared packages; a path; `none`): state of the lexical index beside the snapshot (`fresh`, `missing`, `stale`, `corrupt`, `failed`) and, unless `check`, its repair; `break_lock` removes the lock and temporaries a crashed build left, since a bare lock has no owner; writes only `retrieval.sqlite`, its lock and its temporaries beside the manifest. A run whose index failed at creation stays usable: the event journal carries `index_failed` and searches report the gap. `engine` reports the call-resolution store and, unless `check`, restarts its pass when it is not fresh, running or stopped |
| `codebase_map_flows` | `run_id`, optional `rules` (the project's link rules, recorded beside the snapshot as `flow-rules.json`), `start` (`file::symbol`, `store:name/key` or `module:name`), `direction="from"` (`to`, `through`), `level="fisico"` (`logico`, `dati`, `ux`), `limit=100`: without recorded rules, `status: needs_rules` with the rule format; without `start`, entry points, stores with writer and reader counts, linked routes and declared gaps; with `start`, one flow, its links marked `diretto`, `dedotto` or `dichiarato`, incomplete when a boundary, the budget or a gap stops it; optional `card` `{name, type, text}` records the model's card of that flow, refused unless every line cites a `file:line` that is a step of the flow, and returned with `fresh: false` once a file of the flow changed |
| `codebase_map_edit_impact` | `run_id`, `targets` (symbol ids `path::Name` or file paths), `neighbors=20`, `history=5`, `include_source=true`, `hops=1`, `include_neighbor_source=false`, `include_slices=false`, `budget_chars=120000`: for each target its digests, signature records and card, L1 callers/callees with exact reference sites, optional L2 signatures, optional verified L1 neighbour source, optional lazy Python slices, L4 related tests and obligations, unresolved references, recent changes and verified target source. Budget omissions and DO NOT TOUCH unavailability are explicit. Evidence and leads, never a verdict; an unreadable or stale source is reported in `source.error` and the metadata stays usable |
| `codebase_map_symbols_at` | `run_id`, optional `requests` (each with `path` and line `ranges`), or `base_run_id` with a unified `diff`: symbols overlapping explicit ranges in the candidate run, or removed lines in the base run and added lines in the candidate. Stable entity keys are kept separate from revision anchors; unplaced files and ranges are declared gaps |
| `codebase_map_stale_callers` | `run_id`, `base_run_id`, `limit=100`: compare two runs and classify candidate callers of changed symbols into RED `edit_impact`, GREEN `validation_impact` and `do_not_touch`, with changed symbols, digest-version incompatibilities and impacted SCCs in callees-before-callers order |
| `codebase_map_context` | `run_id`, `request`, `recipient`, optional `out="context"`, `cursor`, `base_run_id`, `embedding_result`: bounded evidence packet and resumable cursor for a bound run; see "Preparing and calling the context tool". It writes artifacts, so it is not annotated read-only, and it refreshes no index: the lexical index is built with the snapshot and repaired by `codebase_map_index` |
| `codebase_map_meta_query` | `run_id`, optional `paths`, `symbol`, `freshness`, `include_history=true`, `limit=100`: Meta-Code symbols with their digests and signature records, card freshness and the bounded changeset history. Cards come from the analysis root's `cards.sqlite`, judged against this run's snapshot; read-only, and cards are written with `snapshot.py meta-upsert` |
| `codebase_map_diff` | `run_id`: read-only source and parser comparison; preserves the snapshot |
| `codebase_map_artifact` | `run_id`, `name`: one declared artifact's content, `bytes` and digest of the whole file; content stops at 2,000,000 bytes with `truncated: true` |
| `codebase_map_checkpoint` | `run_id`, `phase`, `event`, optional `message`: persist a host phase hook |
| `codebase_map_events` | `run_id`, optional `after=0`, `limit=100`: persistent events and replay cursor |
| `codebase_map_ui` | no arguments: starts once the explorer of this project on 127.0.0.1 and returns its `url`; the page lists the runs, draws a run's envelope and polls its events |
| `codebase_map_ui_requests` | optional `take=true`: what the person asked in the explorer (`kind` map or review, `scope` global, changeset, feature or prompt, `text`); `take` moves the pending ones to `taken`. The host runs each with its own method: the server starts no model |
| `codebase_map_ui_done` | `request_id`, optional `results`, `message`: close a taken request; `results` are project-relative JSON files with a `findings` or `retained_findings` list, which the explorer shows |
| `codebase_map_resume` | `run_id`, optional `phase`: prepare continuation of the unchanged exact run |
| `codebase_map_stop` | `run_id`, `reason`: record partial state and unregister after workers have stopped |
| `codebase_map_publish` | `run_id`: canonical freshness, delivery and whole-mirror publication; only an `in_progress` run publishes, so resume a stopped run first |

Source requests use the source reader's selection shape; `full_file: true`
requests the entire inventoried file, and identity checks and whole-file
fallbacks are those of `references/evidence.md`. Emitted bytes are not a
model's deep-reading ledger, and runtime coverage stays none unless the user
supplied it.

```json
{
  "run_id": "src-analysis",
  "requests": [
    {"path": "src/service.py", "symbols": ["Service.validate"]},
    {"path": "src/config.py", "ranges": [{"start": 1, "end": 30}]}
  ]
}
```

Creation defaults to SQLite, separately from analysis flags; state declares
`snapshot.format`, `snapshot.path` and `snapshot.storage_version`, existing and
parent runs keep their binding, runs without it are JSON only, ambiguous
or mismatched files fail, and readers close after each operation. Creation
covers classic full, lite, docs-only and single-phase runs with their stop
limits, always with a full new snapshot: `diff` detects change, and the CLI
`update`/`carry` owns incremental re-derivation. Reading covers classic and team
runs; team partitioning belongs to the host and the team workflow.

### Preparing and calling the context tool

The tool reads derived inputs and creates none; each belongs to one manifest,
so after a refresh rebuild them or they are refused with `retrieval index
belongs to a different candidate`:

1. Retrieval index (required): `<manifest directory>/retrieval.sqlite`, built
   with the snapshot by `codebase_map_create_run` and `snapshot.py write`,
   repaired by `codebase_map_index` or `snapshot.py index MANIFEST`
   (`--check` reports without writing). Missing, it stays a bound missing input.
2. Engine call edges: `engine-edges.sqlite`, written beside the manifest by the
   pass that run creation starts, one entry per language as each engine's stage
   ends; while a language's stage runs, or when its engine is unavailable, its
   callers come from the lexical edges alone and the edge view says so.
3. Cards (optional): the project card store; only fresh cards enter a packet.

```json
{
  "run_id": "src-analysis",
  "request": {
    "schema": "daodan/context-request/v1", "task_id": "t1", "intent": "bug",
    "query": "set_cookie accepts names with spaces",
    "read_boundary": ["."], "write_boundary": [],
    "anchors": [{"entity_id": "src/responses.py::Response.set_cookie"}],
    "base": null, "candidate": null, "diff": [], "proposed_edits": [],
    "mandatory_requirements": [], "required_gates": [],
    "budget": {"max_candidates": 100, "max_edges": 1000, "max_rounds": 100,
               "max_seconds": 120, "max_input_tokens": 100000, "max_output_tokens": 100000},
    "policy_version": "scope-v1"
  },
  "recipient": {"id": "host", "available_tokens": 30000, "reserve_tokens": 2000,
                "max_chars": 24000, "max_evaluations": 2000}
}
```

The result carries `status` (`ready`, `incomplete`, `needs_split`),
`status_reason`, the packet path, digests, counts, gaps and cost. Retrieval
hits are leads: they fill the budget and never block the packet. A request
with only a `query` stays `incomplete` (`not_localized`) with leads; a `ready`
packet needs an accepted target (`anchors`, `diff`, `proposed_edits`) or a
requirement. `needs_split` names why (`core_too_large`, `missing_support` and
the others in `references/context.md`): split the task or raise the recipient
limit, then call again. Pass the returned `cursor` only to continue the same
request. Costs are characters unless the dispatch owner counts tokens. Planning
and packing a 669-entity Python package took about 8 seconds.

## Host execution and phase hooks

After run preparation the host resolves scope, dispatches the declared isolated
workers with the exact run and manifest, and follows the canonical method. The
service starts no LLM, selects no model and owns no scheduler; creating a run or
finishing a call completes no analysis.

- `status` includes `source_available`. A deleted or renamed target keeps
  history, events and stopping available, with `check` null and
  `check_unavailable` explaining; `diff` reports the recorded files and symbols
  as removed; verified reads, resume and publication need the source. Absolute
  target metadata is accepted only inside the bound project; client targets stay
  relative.
- The host calls `checkpoint` with `phase_started`, `phase_completed` or
  `blocked`. A completed checkpoint requires the phase's real declared artifacts
  and their delivery checks, not their semantic conclusions; canonical state
  remains the completion authority, and the host verifies requested human views
  before publication because the structural gate cannot.
- To interrupt, stop the host's workers first, then call `stop`: it records a
  recoverable partial run and signals no agent. Resume checks source and parser
  freshness and prepares the next work while the host restarts workers; it
  counts phases whose artifacts it binds as inherited proof. A published
  (`complete`) run is never resumed: create a new run.
- `checkpoint` never moves `current_phase` backwards. Service state writes
  re-read `state.json` and change only the keys they own, so concurrent worker
  fields survive. Cancelling an MCP request cancels no analysis: an in-flight
  synchronous mutation may finish and remain visible through `status` and
  `events`.

## Progress and durable events

Request-scoped progress uses the standard MCP `progressToken`: operation start
and successful completion with increasing values, no invented percentage, only
for the active request, ignorable.

Run history persists in `mcp-events.json` inside the run. `events` returns
`events`, `next_cursor` and `has_more`; each event has `cursor`, `timestamp`,
`run_id`, `event` and phase or message details. A UI stores the last cursor,
requests `after` it and drains while `has_more`. Restarting the server
preserves history. A journal holds at most 10,000 events; past that,
transitions still apply but the event is refused with an error and canonical
state stays authoritative. Events record service-controlled transitions and
explicit host hooks, never direct CLI or worker writes; `status` reads the
canonical files on every request, so clients reconcile external changes. There
is no filesystem watcher, callback URL, notification scheduler or MCP Tasks
requirement: the host owns polling and display, and after an interruption
reconciles against state and delivery checks, never the last notification.

## Native consumers

`MapService(project_root, store=None)` exposes the tool suffixes as methods and
imports no SDK, so a native backend calls it directly while its agents use MCP
over the same run store and checks. Mutations serialize through the project
lock; registry and publication keep their own canonical OS lock, released by a
crashed holder. Run creation builds its snapshot before taking the project lock
and removes its own run directory if preparation fails. A concurrent call may
receive the bounded project-lock retry error while another operation owns the
project. Other agent tools stay subject to their host's permissions.

The host owns its UI, worker lifetime, models, routing and permissions. It may
bind a custom store inside the project; that changes only where the run store
lives, never the analysis, gates or commands.
