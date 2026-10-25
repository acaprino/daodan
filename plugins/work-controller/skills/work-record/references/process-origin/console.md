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
