<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. fetch
retrieves a known URL and does not search: network search needs a search tool
registered in this session. A user question is asked in the reply, and the run
waits for the answer. Custom
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

# Agent SDK: custom tools, MCP servers, plugins and skills

Defining your own tools as in-process MCP servers, connecting external MCP servers over stdio and
HTTP, the `mcp__<server>__<tool>` naming convention, and loading Claude Code plugins and
filesystem settings into an SDK run.

---

## 1. Custom Tools via MCP


Create custom tools using the SDK's MCP server helpers. Tools are defined with schemas and handlers, then exposed as in-process MCP servers.

### TypeScript

```typescript
import { tool, createSdkMcpServer, query } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

// Define tools
const getWeather = tool(
  "get_weather",
  "Get current weather for a city",
  { city: z.string(), units: z.enum(["celsius", "fahrenheit"]).default("celsius") },
  async ({ city, units }) => ({
    content: [{ type: "text", text: JSON.stringify({ city, temp: 22, units }) }],
  })
);

const searchDatabase = tool(
  "search_db",
  "Search the application database",
  { query: z.string(), limit: z.number().default(10) },
  async ({ query: q, limit }) => {
    const results = await db.search(q, limit);
    return { content: [{ type: "text", text: JSON.stringify(results) }] };
  }
);

// Create MCP server
const server = createSdkMcpServer({
  name: "app-tools",
  tools: [getWeather, searchDatabase],
});

// Use in query
for await (const msg of query({
  prompt: "What's the weather in Rome and find related travel posts?",
  options: {
    mcpServers: { app: server },
    allowedTools: ["mcp__app__get_weather", "mcp__app__search_db"],
  },
})) {
  // Custom tools are called automatically by the agent
}
```

### Python

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, query, ClaudeAgentOptions

@tool("get_weather", "Get current weather for a city", {"city": str, "units": str})
async def get_weather(args):
    return {"content": [{"type": "text", "text": f"Weather in {args['city']}: 22C"}]}

@tool("search_db", "Search the database", {"query": str, "limit": int})
async def search_db(args):
    results = await db.search(args["query"], args["limit"])
    return {"content": [{"type": "text", "text": str(results)}]}

server = create_sdk_mcp_server(name="app-tools", tools=[get_weather, search_db])

options = ClaudeAgentOptions(
    mcp_servers={"app": server},
    allowed_tools=["mcp__app__get_weather", "mcp__app__search_db"],
)

async for msg in query(prompt="Weather in Rome?", options=options):
    pass
```

### MCP Tool Naming Convention

Custom tools follow the pattern: `mcp__<server-name>__<tool-name>`

Example: server named `"mytools"` with tool `"search"` becomes `mcp__mytools__search`

### External MCP Servers

Connect to external MCP servers via stdio or HTTP:

```typescript
options: {
  mcpServers: {
    // stdio transport (local process)
    localServer: {
      command: "node",
      args: ["./mcp-server.js"],
    },
    // HTTP/SSE transport (remote)
    remoteServer: {
      url: "https://mcp.example.com/sse",
      headers: { Authorization: "Bearer token" },
    },
  },
}
```

---

## 2. Plugins and Skills


Load local plugins to give the agent access to custom skills, agents, and commands:

```typescript
for await (const msg of query({
  prompt: "Review the frontend code",
  options: {
    plugins: [{ type: "local", path: "/path/to/my-plugin" }],
    allowedTools: ["Read", "Glob", "Grep", "Skill"],
  },
})) { /* agent can now invoke skills from the plugin */ }
```

Load filesystem settings (CLAUDE.md, .claude/ configs):

```typescript
options: {
  settingSources: ["user", "project", "local"],
}
```
