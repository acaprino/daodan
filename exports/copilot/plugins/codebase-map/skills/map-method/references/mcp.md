<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
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

# Local service and MCP

- [Startup and binding](#startup-and-binding)
- [Local Code Mode (opt-in)](#local-code-mode-opt-in)
- [Tools](#tools)
- [Host execution and phase hooks](#host-execution-and-phase-hooks)
- [Progress and durable events](#progress-and-durable-events)
- [Native consumers](#native-consumers)

## Startup and binding

The declared `codebase-map` server runs over stdio:

```text
uv run --no-config --no-project --script <installed-plugin-root>/skills/map-method/scripts/mcp_server.py --project <project-root>
```

`--no-config --no-project` keep `uv` from reading the analyzed project's
`uv.toml`, `pyproject.toml` or `.python-version`: a repository under analysis
must never choose the package index or interpreter of its own analyzer. Keep
both flags in any custom registration.

`uv` provisions the official MCP Python SDK 2.x in its own runtime environment.
The server requires Python 3.12 or later, which its `requires-python` header makes
`uv` provision and its startup check enforces. Existing parser dependencies stay
optional, with the same parser diagnostics and fallback as the CLI. The build
and the reusable `mcp_service.py` module remain standard-library-only.

The project is fixed at startup. Omitting `--project` binds the startup working
directory; a consumer that controls subprocess launch should pass it explicitly.
`scope` and `status` (and so `runs`) return the bound `project_root`; verify it
before creating a run. Helper subprocesses run from the helper directory and
resolve `git` from absolute `PATH` entries only, never from the project.
Every target is relative to that project, and every run ID selects the exact
`.codebase-map/runs/<run-id>/` (or `<store>/runs/<run-id>/` when started with
`--store`). Foreign paths, traversal, symlinks and Windows
junctions are rejected. Clients cannot supply an executable, output root or
manifest path. Legacy stores follow the project-bound migration contract;
resolve a reported migration conflict before continuing.

### Custom analysis store

The process that starts the server may move the whole store with
`--store <project-relative-path>`, fixed for the server's lifetime like
`--project`; `MapService(project_root, store)` takes the same value. Omitting it
keeps `.codebase-map/`. The path is exact POSIX, starts with a dot directory so
every perimeter already leaves it out of the analyzed sources, and may not reuse
`.codebase-map`, `.codebase-xray`, `.git` or a device name. Run IDs then select
`<store>/runs/<run-id>/`, and the registry, locks and published mirror live in
that store. A target inside its top directory is refused like the canonical
output.

The first write creates the store and its marker `.codebase-map-store.json`,
`{"schema": "daodan/codebase-map-store/v1", "store": "<path>"}`. The marker binds
the store to its project: the `snapshot.py` commands accept a run directory in
such a store and derive the project from the marker. The shell entry workflows,
worker roles and `migrate_root.py resolve` still name `.codebase-map/`, so they
use a custom store only when the host hands them the exact run directory. An
existing non-empty directory without the matching marker is refused rather than
adopted, and a marker that names another path invalidates every run in the
store; recovering a store whose marker was lost means rewriting that exact
marker. A custom store has no
legacy predecessor, so the `.codebase-xray` migration does not apply to it; the
default store keeps that contract. The canonical `.codebase-map/` mirror and
its consumers do not see runs in a custom store: the starting host owns that
choice and points its own consumers at the store.

The compiler supplies automatic manifests or host-specific registration notes.
Verify the active host's connection before calling these tools. A shell workflow
uses its existing commands and needs no MCP connection.

## Local Code Mode (opt-in)

The same server can expose `search` and `execute` in place of its 19 native
tools. The model writes JavaScript to discover operations, compose calls, filter
intermediate values and return a selected JSON result. Schemas and dispatch come
from the existing MCP wrappers, so their argument validation, project binding,
source checks, locks and publication gates remain authoritative. Code Mode starts
no LLM, analysis worker or scheduler.

### Start and register

Install Deno separately, outside the bound project. The minimum is 2.4; use a
maintained, patched release. Deno is required only for Code Mode. Start with:

```text
uv run --no-config --no-project --script <installed-plugin-root>/skills/map-method/scripts/mcp_server.py --project <project-root> --code-mode --deno /absolute/path/to/deno
```

`--deno` must be an absolute executable path outside the project. If omitted,
the server searches absolute `PATH` entries and rejects an executable inside the
project. A missing or unsupported Deno fails startup. Project-local Deno
configuration and environment settings do not select or configure the runner.
`--project` and `--store` retain the binding described above.

Configure these arguments on the existing `codebase-map` server registration;
do not register a second copy of its native catalog. Verify that `tools/list`
returns exactly `search` and `execute`. A standard MCP client can call them
without supplying a JavaScript runtime itself. Automatic manifests and manual
registration retain the active host's existing mechanism. Native startup remains
the default and needs no Deno installation.

### Discover and compose

| Tool | Inputs | JavaScript capabilities |
|---|---|---|
| `search` | `code`: an async function | `catalog`, the permitted MCP tool descriptors; no operation calls |
| `execute` | `code`: an async function; `tools`: explicit list of operation names | `tools.<name>(arguments)`, limited to the listed permitted operations |

Discover only the descriptions and schemas needed for the task. For example,
call `search` with:

```json
{
  "code": "async () => catalog.filter(({name}) => /_(runs|outline)$/.test(name))"
}
```

Then call `execute` with `tools` set to
`["codebase_map_runs", "codebase_map_outline"]` and this `code` value:

```javascript
async () => {
  const listing = await tools.codebase_map_runs({});
  const eligible = listing.runs.filter(run => run.readable && run.source_available);
  const selected = eligible.slice(0, 3);
  const outlines = [];
  for (const run of selected) {
    const outline = await tools.codebase_map_outline({run_id: run.run_id, limit: 5});
    outlines.push({
      run_id: run.run_id,
      matched: outline.matched,
      truncated: outline.truncated,
      symbols: outline.items.map(({path, symbol, start, end}) => ({path, symbol, start, end}))
    });
  }
  return {
    outlines,
    omitted_eligible_runs: eligible.length - selected.length,
    unavailable_runs: listing.runs.filter(run => !run.readable || !run.source_available)
      .map(({run_id, error, check_unavailable}) => ({run_id, error, check_unavailable}))
  };
}
```

This selects up to three existing runs, reads their outlines in one execution and
returns bounded metadata with omissions. It creates no run. These symbol records
do not establish source-reading coverage. Each operation takes one JSON object. Await every operation before
returning, and return a JSON value explicitly. A tool omitted from the `tools`
list cannot be called, even when it appears in `search`. Each execution has fresh
JavaScript state; only the existing service's records persist.

### Mutations and approval

The default catalog contains only operations explicitly annotated read-only.
For a workflow that needs writes, the process owner grants each mutation at
startup with repeatable arguments, for example:

```text
--code-mode-allow-write codebase_map_create_run
--code-mode-allow-write codebase_map_checkpoint
```

These grant only those named mutations. Unknown names, wildcards and names of
read-only operations are rejected. Generated code and `execute.tools` cannot
expand the startup permissions. `codebase_map_context` writes an evidence packet
and therefore also needs its own grant. Granting publication does not bypass the
existing delivery and freshness checks.

The outer `execute` tool is annotated as mutating when any write is granted.
A host's approval of that outer call covers the selected program; there is no
separate host approval for each internal operation. Startup grants must represent
the host owner's intended authority. Review the program and its named tools
before authorizing a run with writes.

### Results, failures and receipts

A successful `search` or `execute` returns:

- `value`: the JSON value selected by the generated function.
- `calls`: broker-owned receipts for admitted operations, with `tool`, `ok`, and
  either `output_bytes` or an error. Search has no operation calls.
- `stats`: `tool_calls`, `intermediate_bytes`, `selected_value_bytes`,
  `receipt_bytes` and `elapsed_ms`.

Read `calls` even when `value` looks successful. Catching an operation error in
JavaScript does not remove its failed receipt. If execution fails, its MCP tool
error includes the receipts for admitted calls. A completed mutation can precede
a later error or exceeded limit; successful earlier calls are not rolled back.
Check canonical `status` and `events` before retrying a mutation.

The byte counts distinguish selected values from the additional call receipts.
The statistics measure serialized UTF-8 bytes and elapsed time, not billed model
tokens. The two-tool interface keeps unused schemas and intermediate results out
of the model context, while generated code, discovery results and selected output
still consume context. Compare complete tasks, including retries, before claiming
a saving; this feature has no universal token-reduction percentage.

### Execution limits and boundary

| Resource | Default bound |
|---|---|
| JavaScript source | 32 KiB UTF-8 |
| JavaScript lifetime | 30 seconds |
| Internal operation calls | 32 |
| Arguments for one operation | 64 KiB serialized JSON |
| Selected final JSON value | 64 KiB serialized JSON |
| One intermediate operation result | 8 MiB serialized JSON |
| Cumulative intermediate results | 32 MiB serialized JSON |
| V8 old-space heap | 128 MiB |
| Runner stderr | 16 KiB |

Oversized output fails explicitly. The final-value bound excludes the broker's
receipts and statistics. Keep selections small and preserve relevant gaps and
truncation flags. The existing operation-specific limits still apply.

Generated code runs in a separate Deno Worker through a fixed shipped runner,
with filesystem, network, environment, subprocess, FFI and system-information
permissions denied, and remote imports disabled. The runner uses a disposable
working directory and a clean environment. The permitted Python operations are the route to project data;
they retain their existing confinement. Scripts cannot choose a new project,
output root, executable or capability through tool arguments.

On cancellation, protocol failure or deadline, the broker stops admitting calls
and terminates the runner. An already admitted atomic map operation may finish;
its outcome remains accounted for. The 30-second JavaScript deadline is therefore
not a hard wall-clock deadline for such an operation. Deno permissions are a
runtime boundary, not a complete OS sandbox. The old-space limit is not a total
process-memory or disk quota. This feature is for bounded local composition and
makes no isolation claim for a multi-tenant hostile-code service.

## Tools

Native mode exposes these 19 tools. Code Mode discovers the permitted subset of
the same operations and calls their existing wrappers. Every tool returns
structured JSON and reports errors as MCP tool failures.

| Tool | Inputs and behavior |
|---|---|
| `codebase_map_scope` | `target="."`: inventory counts, languages and declared exclusions; starts no analysis |
| `codebase_map_create_run` | `target`, exact `run_id`, optional `depth="full"` or `"lite"`, `critical`, `comments`, `docs_only`, `phase`, `stop_after`, `format="sqlite"` (or explicit `"json"`): snapshot and prepared classic run |
| `codebase_map_runs` | canonical runs and active registry in this project; an unreadable run is listed with `readable: false` and its `error` |
| `codebase_map_status` | `run_id`: current `state` and canonical delivery `check`; missing-source diagnostics keep history observable |
| `codebase_map_outline` | `run_id`, optional `path`, `pattern` (literal case-insensitive substrings separated by `\|`, never a regular expression), `limit=100`: bound symbol metadata |
| `codebase_map_graph` | `run_id`, optional `paths`, `hops=2`, `limit=100`: verified static graph and diagnostics |
| `codebase_map_read` | `run_id`, `requests`: verified source blocks; a result above 4,000,000 characters is refused, so split the request |
| `codebase_map_edit_impact` | `run_id`, `targets` (symbol ids `path::Name` or file paths), `neighbors=20`, `history=5`, `include_source=true`, `hops=1`, `include_neighbor_source=false`, `include_slices=false`, `budget_chars=120000`: for each target its digests, signature records and card, L1 callers/callees with exact reference sites, optional L2 signatures, optional verified L1 neighbour source, optional lazy Python slices, L4 related tests and obligations, unresolved references, recent changes and verified target source. Budget omissions and DO NOT TOUCH unavailability are explicit. Evidence and leads, never a verdict; an unreadable or stale source is reported in `source.error` and the metadata stays usable |
| `codebase_map_symbols_at` | `run_id`, optional `requests` (each with `path` and line `ranges`), or `base_run_id` with a unified `diff`: symbols overlapping explicit ranges in the candidate run, or removed lines in the base run and added lines in the candidate. Stable entity keys are kept separate from revision anchors; unplaced files and ranges are declared gaps |
| `codebase_map_stale_callers` | `run_id`, `base_run_id`, `limit=100`: compare two runs and classify candidate callers of changed symbols into RED `edit_impact`, GREEN `validation_impact` and `do_not_touch`, with changed symbols, digest-version incompatibilities and impacted SCCs in callees-before-callers order |
| `codebase_map_context` | `run_id`, `request`, `recipient`, optional `out="context"`, `cursor`, `base_run_id`, `embedding_result`: bounded evidence packet and resumable cursor for a bound run; see "Preparing and calling the context tool". It writes artifacts, so it is not annotated read-only, and it refreshes no index |
| `codebase_map_meta_query` | `run_id`, optional `paths`, `symbol`, `freshness`, `include_history=true`, `limit=100`: Meta-Code symbols with their digests and signature records, card freshness and the bounded changeset history. Cards come from the analysis root's `cards.sqlite`, judged against this run's snapshot; read-only, and cards are written with `snapshot.py meta-upsert` |
| `codebase_map_diff` | `run_id`: read-only source and parser comparison; preserves the snapshot |
| `codebase_map_artifact` | `run_id`, `name`: one declared artifact's content, `bytes` and digest of the whole file; content stops at 2,000,000 bytes with `truncated: true` |
| `codebase_map_checkpoint` | `run_id`, `phase`, `event`, optional `message`: persist a host phase hook |
| `codebase_map_events` | `run_id`, optional `after=0`, `limit=100`: persistent events and replay cursor |
| `codebase_map_resume` | `run_id`, optional `phase`: prepare continuation of the unchanged exact run |
| `codebase_map_stop` | `run_id`, `reason`: record partial state and unregister after workers have stopped |
| `codebase_map_publish` | `run_id`: canonical freshness, delivery and whole-mirror publication; only an `in_progress` run publishes, so resume a stopped run first |

For example, source requests use the source reader's existing selection shape:

```json
{
  "run_id": "src-analysis",
  "requests": [
    {"path": "src/service.py", "symbols": ["Service.validate"]},
    {"path": "src/config.py", "ranges": [{"start": 1, "end": 30}]}
  ]
}
```

`full_file: true` requests the entire inventoried file. Source/parser identity
checks and whole-file fallbacks remain those in `references/evidence.md`.
Outline metadata and emitted source bytes are distinct from a model's actual
deep-reading ledger. Runtime coverage remains none unless supplied by the user.

Creation defaults to SQLite, separate from analysis flags. State declares
`snapshot.format`, `snapshot.path` and `snapshot.storage_version`. Existing and
parent runs retain that exact binding; legacy runs without it are JSON only.
Ambiguous/mismatched files fail. Readers close after each operation. JSON
compatibility remains in Daodan; integrations may restrict reads to SQLite.

Creation supports classic full, lite, docs-only and single-phase runs, with the
existing combinations and stop limits. It creates a full new snapshot rather
than carrying incremental claims. `diff` provides change detection; existing CLI
update/carry remains the owner of incremental re-derivation. Reading supports
existing classic and team runs. Native team partitioning still belongs to the
host and the team workflow.

### Preparing and calling the context tool

The tool reads derived inputs and creates none of them. Prepare each for the exact
manifest the run is bound to:

1. Retrieval index (required): `retrieval.refresh_index(<manifest>, <manifest
   directory>/retrieval.sqlite)` from `scripts/retrieval.py`. No command-line
   entry or MCP tool builds it; a missing index stays a bound missing input.
2. Python call edges (recommended): `resolve_edges.py <manifest> --environment
   <venv of the analyzed project> --compact` writes `engine-edges.sqlite` beside
   the manifest. Without it callers come from the lexical edges alone, which
   resolve fewer calls made through instances.
3. Cards (optional): the project card store; only fresh cards enter a packet.

Every index belongs to one manifest. After the map is refreshed into a new
manifest, rebuild its index and edges: the old ones are refused with
`retrieval index belongs to a different candidate`.

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

Reading the result: `status` is `ready`, `incomplete` or `needs_split`, with
`status_reason`, the packet path, digests, counts, gaps and cost. Retrieval hits
are leads: they fill the budget and never block the packet. A request with only a
`query` stays `incomplete` (`not_localized`) and delivers leads; supply an
accepted target (`anchors`, `diff`, `proposed_edits`) or a requirement for a
`ready` packet. `needs_split` names why (`core_too_large`, `missing_support` and
the others in `references/context.md`); split the task or raise the recipient
limit, then call again. Pass the returned `cursor` only to continue the remaining
evidence of the same request. Costs are characters, never tokens, unless the
dispatch owner counts them. Planning and packing a 669-entity Python package
took about 8 seconds.

## Host execution and phase hooks

After run preparation, the host resolves scope, dispatches the declared isolated
workers with the exact run and manifest, and follows the canonical method.
The service starts no LLM, does not select models and owns no scheduler.
Creating a run or finishing an MCP call does not complete an analysis.

`status` includes `source_available`. If a target was deleted or renamed, history,
events and stopping remain available, while `check` is null and
`check_unavailable` explains the missing-source condition. `diff` reports the
recorded files and symbols as removed. Verified reads, resume and publication
require the source target. Existing canonical absolute target metadata is
accepted only inside the bound project; client target arguments remain relative.

The host calls `checkpoint` with `phase_started`, `phase_completed` or `blocked`.
A completed checkpoint requires that phase's real declared artifacts and their
applicable delivery checks; it does not certify their semantic conclusions.
Canonical state remains the completion authority. The host verifies requested
human views before publication, because the structural gate cannot establish
that a requested UI artifact was delivered.

To interrupt, first stop the host's workers, then call `stop`. This records a
recoverable partial run; it sends no signal to agents. Resume checks source and
parser freshness and prepares the next work, while the host restarts workers.
A published (`complete`) run is never resumed; create a new run. Resume counts
phases whose artifacts it binds as inherited proof as completed. `checkpoint`
never moves `current_phase` backwards. Service state writes re-read
`state.json` and change only the keys they own, so concurrent worker fields
survive.
Cancelling an MCP request does not cancel an analysis; an in-flight synchronous
mutation may finish and remain visible through `status` and `events`.

## Progress and durable events

Request-scoped progress uses the standard MCP `progressToken` mechanism. Calls
report operation start and successful completion with increasing values and no
invented analysis percentage. These notifications exist only for the active
request, and a caller may ignore them.

Run history is persisted in `mcp-events.json` inside the run. `events` returns
`events`, `next_cursor` and `has_more`. Each event has `cursor`, `timestamp`,
`run_id` and `event`, with phase/message details when applicable. A native UI
stores the last cursor, requests `after` that value, and drains pages while
`has_more` is true. Restarting the server preserves history. A journal holds at
most 10,000 events; past that, transitions still apply but the event is refused
with an error, and canonical state stays authoritative.

Events record successful service-controlled transitions and explicit host hooks.
Direct CLI or worker writes do not automatically emit events. `status` reads the
canonical files on every request, so clients can reconcile external changes.
There is no filesystem watcher, arbitrary callback URL, notification scheduler
or MCP Tasks requirement. The native app owns polling/subscriptions and display.
Events are derived history; after an interruption, reconcile against state and
delivery checks rather than treating the last notification as proof of success.

## Native consumers

`codebase_map_context` writes a bounded evidence packet and resumable checkpoint
for a bound run. It returns compact paths and cost, with no implicit index refresh
or inference. See `context.md` for recipient units, base-run binding, path confinement
and the required dispatch check when the recipient tokenizer is unavailable.

`MapService(project_root, store=None)` exposes the same methods as the tool suffixes and
contains no SDK imports. A native backend can call it directly while its agents
use MCP; both share the same run store and checks. Service mutations serialize
through the existing project migration lock, and registry/publication retain
their own canonical lock, an OS lock that a crashed holder releases. Run
creation builds its snapshot before taking the project lock and removes its own
run directory if preparation fails. Concurrent calls may receive the existing bounded project-lock retry error
while another operation owns that project. Other agent tools remain subject to
their host's permissions and ownership rules.

Tri-Tech Code owns its UI, worker lifetime, Gateway models, routing and app
permissions. It may bind a custom store inside the project; that changes only
where the canonical run store lives, and the analysis, gates and commands stay
the same. The interface supplies no application-specific fork of the analysis.
