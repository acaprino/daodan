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

# Console and MCP

The web console and MCP server use the same bounded read models in `process_controller.views`. They do not create claims, complete attempts, change tickets or execute commits.

## Local web console

```powershell
uv run process-controller --workspace . --home .process-controller console --host 127.0.0.1 --port 8765
```

Open the URL printed by the command. The initial URL contains a random token in its fragment. The console stores it in `sessionStorage`, which is isolated by origin, and immediately removes it from the address bar. API calls use `X-Process-Controller-Token`; SSE uses the same token in its own origin's query. No authentication cookie is created and tokens are not shared across ports. Static assets contain no run data. Only loopback hosts are accepted. There are no remote bindings, CORS allowances or write endpoints.

The console shows run progress, job and attempt states, artifact metadata, recent events, decision tickets and bounded command logs. Server-Sent Events refresh the active run without reloading the whole record. Pause and manual refresh remain available.

The console reads through the existing run/workspace binding. The overview lists only runs admitted in the selected workspace; run status, details, events and logs enforce the same binding. Decision maps are scoped to the shared home. Artifact bodies are not included in overview responses. Log output is limited to the selected attempt and stream, with a maximum of 64 KiB.

## Demo without a model

From the repository root:

```powershell
New-Item -ItemType Directory -Force .demo\workspace
uv run process-controller --workspace .demo\workspace --home .demo\home start examples\console-demo.yaml --grant shell --run-id console-demo
uv run process-controller --workspace .demo\workspace --home .demo\home drive console-demo --holder local-coordinator
uv run process-controller --workspace .demo\workspace --home .demo\home console --port 8765
```

The command job finishes with a real artifact and log. The review job waits for an agent, so the console shows both completed and pending work without making a model call.

## MCP over stdio

```powershell
uv run process-controller --workspace . --home .process-controller mcp
```

Register that command as a stdio MCP server in the host. Standard output is reserved for newline-delimited JSON-RPC messages; optional method debugging goes to stderr only when `PROCESS_CONTROLLER_MCP_DEBUG=1`.

The server supports the legacy `2025-11-25` initialization lifecycle and the modern `2026-07-28` discovery and per-request metadata model. Protocol behavior is bounded and read-only. It exposes:

- `process_runs`, `process_run_status`, `process_run_detail` and `process_frontier`;
- `process_events` with cursor and page limit;
- `process_map_status` for decision maps and ticket dependencies;
- `process_supervise` for bounded, non-authoritative observations.

Every tool result includes compact JSON text and `structuredContent`. Tool input is closed and validated. MCP does not return log bodies, artifact bodies or the full process YAML. Rate limiting is per server process; clients should also apply request timeouts.

## Security and evidence boundaries

The web token protects local read access but is not an enterprise authentication system. The console and MCP inherit the user's filesystem permissions. Do not expose them to a shared network without a separately reviewed deployment.

Protocol tests exercise discovery, initialization, tool schemas, calls, errors and transport. Interactive verification with a specific installed MCP client or browser version is separate evidence and is not inferred from unit tests.

Protocol references: [2026-07-28 transports](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports), [discovery](https://modelcontextprotocol.io/specification/2026-07-28/server/discover), [2025-11-25 lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle) and [tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools).
