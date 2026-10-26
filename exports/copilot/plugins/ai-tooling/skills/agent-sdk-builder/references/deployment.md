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

# Agent SDK: deployment and worked patterns

Ephemeral versus long-running session hosting, custom process spawning, sandbox isolation, and
three end-to-end patterns: a CI/CD review agent, a multi-agent research pipeline, and an
interactive chat loop.

---

## 1. Hosting & Deployment Patterns


### Ephemeral Sessions

New container per task, destroy on completion. Best for CI/CD, one-shot tasks.

```typescript
// In a serverless function or CI step
const result = [];
for await (const msg of query({
  prompt: taskDescription,
  options: {
    maxTurns: 15,
    maxBudgetUsd: 0.25,
    permissionMode: "bypassPermissions",
    cwd: "/workspace",
  },
})) {
  if ("result" in msg) result.push(msg);
}
```

### Long-Running Sessions

Persistent containers with multiple agent interactions. Best for interactive applications.

```typescript
// Resume across container restarts
const sessionId = await loadSessionId();
for await (const msg of query({
  prompt: userInput,
  options: { resume: sessionId },
})) { /* ... */ }
```

### Custom Process Spawning *(verify)*

Run agents in VMs, containers, or remote environments. `spawnClaudeCodeProcess` ships in some SDK versions but is not in the currently documented API; confirm before building on it:

```typescript
for await (const msg of query({
  prompt: "Analyze the repo",
  options: {
    spawnClaudeCodeProcess: async (options) => {
      // Spawn in a Docker container, VM, or remote server
      const container = await docker.createContainer({
        Image: "node:20",
        Cmd: ["npx", "@anthropic-ai/claude-code", ...options.args],
      });
      await container.start();
      return container.stream;
    },
  },
})) { /* ... */ }
```

### Sandbox Isolation

The `sandbox` option enables sandboxed execution for agent tool calls. Anthropic also publishes a standalone sandboxing runtime (`@anthropic-ai/sandbox-runtime`) for isolating the whole agent process; its API surface changes faster than this file, so take exact usage from that package's README rather than from memory.

---

## 2. Common Patterns


### CI/CD Code Review Agent

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

async function reviewPR(diff: string): Promise<string> {
  let review = "";
  for await (const msg of query({
    prompt: `Review this PR diff for bugs, security issues, and style:\n\n${diff}`,
    options: {
      allowedTools: ["Read", "Glob", "Grep"],
      maxTurns: 15,
      maxBudgetUsd: 0.50,
      outputFormat: {
        type: "json_schema",
        schema: {
          type: "object",
          properties: {
            issues: { type: "array", items: { type: "object", properties: {
              severity: { type: "string" }, file: { type: "string" },
              line: { type: "number" }, description: { type: "string" },
            }}},
            summary: { type: "string" },
            approved: { type: "boolean" },
          },
          required: ["issues", "summary", "approved"],
        },
      },
    },
  })) {
    if ("result" in msg) review = msg.result;
  }
  return review;
}
```

### Multi-Agent Research Pipeline

```typescript
for await (const msg of query({
  prompt: "Research best practices for rate limiting in Node.js APIs",
  options: {
    allowedTools: ["Read", "Grep", "Glob", "WebSearch", "WebFetch", "Agent"],
    agents: {
      "codebase-analyst": {
        description: "Analyzes the local codebase for existing patterns.",
        prompt: "Search the codebase for rate limiting implementations and patterns.",
        tools: ["Read", "Glob", "Grep"],
        model: "sonnet",
      },
      "web-researcher": {
        description: "Researches best practices and documentation online.",
        prompt: "Search for current best practices, libraries, and patterns.",
        tools: ["WebSearch", "WebFetch"],
        model: "sonnet",
      },
    },
  },
})) { /* ... */ }
```

### Interactive Chat Application

```python
from claude_agent_sdk import ClaudeSDKClient

async def chat_loop():
    async with ClaudeSDKClient() as client:
        while True:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                break
            await client.query(user_input)
            async for msg in client.receive_response():
                if hasattr(msg, "content"):
                    for block in msg.content:
                        if block.get("type") == "text":
                            print(f"Agent: {block['text']}")
```
