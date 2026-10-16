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

# Local service and MCP

## Startup and binding

The declared `codebase-map` server runs over stdio:

```text
uv run --script <installed-plugin-root>/skills/map-method/scripts/mcp_server.py --project <project-root>
```

`uv` provisions the official MCP Python SDK 2.x in its own runtime environment.
The server requires Python 3.11 or later. Existing parser dependencies stay
optional, with the same parser diagnostics and fallback as the CLI. The build
and the reusable `mcp_service.py` module remain standard-library-only.

The project is fixed at startup. Omitting `--project` binds the startup working
directory; a consumer that controls subprocess launch should pass it explicitly.
Every target is relative to that project, and every run ID selects the exact
`.codebase-map/runs/<run-id>/`. Foreign paths, traversal, symlinks and Windows
junctions are rejected. Clients cannot supply an executable, output root or
manifest path. Legacy stores follow the project-bound migration contract;
resolve a reported migration conflict before continuing.

The compiler supplies automatic manifests or host-specific registration notes.
Verify the active host's connection before calling these tools. A shell workflow
uses its existing commands and needs no MCP connection.

## Tools

Every tool returns structured JSON and reports errors as MCP tool failures.

| Tool | Inputs and behavior |
|---|---|
| `codebase_map_scope` | `target="."`: inventory counts, languages and declared exclusions; starts no analysis |
| `codebase_map_create_run` | `target`, exact `run_id`, optional `depth="full"` or `"lite"`, `critical`, `comments`, `docs_only`, `phase`, `stop_after`: snapshot and prepared classic run |
| `codebase_map_runs` | canonical runs and active registry in this project |
| `codebase_map_status` | `run_id`: current `state` and canonical delivery `check`; missing-source diagnostics keep history observable |
| `codebase_map_outline` | `run_id`, optional `path`, `pattern`, `limit=100`: bound symbol metadata |
| `codebase_map_graph` | `run_id`, optional `paths`, `hops=2`, `limit=100`: verified static graph and diagnostics |
| `codebase_map_read` | `run_id`, `requests`: verified source blocks |
| `codebase_map_diff` | `run_id`: read-only source and parser comparison; preserves the snapshot |
| `codebase_map_artifact` | `run_id`, `name`: one declared artifact's content and digest |
| `codebase_map_checkpoint` | `run_id`, `phase`, `event`, optional `message`: persist a host phase hook |
| `codebase_map_events` | `run_id`, optional `after=0`, `limit=100`: persistent events and replay cursor |
| `codebase_map_resume` | `run_id`, optional `phase`: prepare continuation of the unchanged exact run |
| `codebase_map_stop` | `run_id`, `reason`: record partial state and unregister after workers have stopped |
| `codebase_map_publish` | `run_id`: canonical freshness, delivery and whole-mirror publication |

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

Creation supports classic full, lite, docs-only and single-phase runs, with the
existing combinations and stop limits. It creates a full new snapshot rather
than carrying incremental claims. `diff` provides change detection; existing CLI
update/carry remains the owner of incremental re-derivation. Reading supports
existing classic and team runs. Native team partitioning still belongs to the
host and the team workflow.

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
`has_more` is true. Restarting the server preserves history.

Events record successful service-controlled transitions and explicit host hooks.
Direct CLI or worker writes do not automatically emit events. `status` reads the
canonical files on every request, so clients can reconcile external changes.
There is no filesystem watcher, arbitrary callback URL, notification scheduler
or MCP Tasks requirement. The native app owns polling/subscriptions and display.
Events are derived history; after an interruption, reconcile against state and
delivery checks rather than treating the last notification as proof of success.

## Native consumers

`MapService(project_root)` exposes the same methods as the tool suffixes and
contains no SDK imports. A native backend can call it directly while its agents
use MCP; both share the same run store and checks. Service mutations serialize
through the existing project migration lock, and registry/publication retain
their own canonical lock. Concurrent calls may receive the existing bounded project-lock retry error
while another operation owns that project. Other agent tools remain subject to
their host's permissions and ownership rules.

Tri-Tech Code owns its UI, worker lifetime, Gateway models, routing and app
permissions. This interface retains `.codebase-map/`; it grants no private app
storage binding and supplies no application-specific fork of the analysis.
