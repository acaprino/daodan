<daodan_host_binding host="opencode">
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

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network fetch uses webfetch, network search uses
websearch, and a user question uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

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

# Agent SDK: sessions and subagents

Multi-turn sessions, resuming, forking, session metadata, introspection, subagent definitions
and behavior, and the Python `ClaudeSDKClient` runtime methods.

Method names and option shapes here are API-sensitive: resolve them against the installed SDK or
the current documentation before use, per the source-of-truth policy in `SKILL.md`.

---

## 1. Subagents -- Multi-Agent Orchestration


Subagents let you define specialized agents that the main agent can spawn for parallel or delegated work.

### Defining Subagents

```typescript
for await (const msg of query({
  prompt: "Review the codebase for quality and security issues",
  options: {
    allowedTools: ["Read", "Grep", "Glob", "Agent"],  // Agent tool required
    agents: {
      "security-reviewer": {
        description: "Security expert. Use for vulnerability scanning, auth review, injection detection.",
        prompt: "You are a security auditor. Find vulnerabilities, auth issues, and injection vectors.",
        tools: ["Read", "Glob", "Grep"],
        model: "opus",
      },
      "code-quality": {
        description: "Code quality reviewer. Use for style, patterns, complexity, dead code.",
        prompt: "Review code quality: naming, complexity, patterns, duplication.",
        tools: ["Read", "Glob", "Grep"],
        model: "sonnet",
      },
      "test-runner": {
        description: "Runs tests and reports results.",
        prompt: "Execute test suites and analyze failures.",
        tools: ["Bash", "Read", "Grep"],
        model: "haiku",
      },
    },
  },
})) {
  // Claude automatically decides when to spawn subagents
  // based on their descriptions
}
```

### Subagent Properties

| Property | Type | Description |
|---|---|---|
| `description` | `string` | **Required.** When to use this agent (Claude decides based on this) |
| `prompt` | `string` | **Required.** System prompt for the subagent |
| `tools` | `string[]` | Restricted tool set |
| `model` | `string` | `"sonnet"`, `"opus"`, `"haiku"`, or `"inherit"` |
| `disallowedTools` | `string[]` | Tools to block |
| `mcpServers` | `object` | MCP servers available to subagent |
| `skills` | `string[]` | Skills the subagent can invoke |
| `memory` | `object` | Memory configuration for the subagent |
| `maxTurns` | `number` | Turn limit for this subagent |

Also documented: `initialPrompt`, `background`, `effort`, `permissionMode`.

### Subagent Behavior

- **Context isolation** -- each subagent gets a fresh conversation; only its final message returns to the parent
- **Parallel execution** -- multiple subagents run concurrently when spawned together
- **No nesting** -- subagents cannot spawn their own subagents
- **Resumable** -- subagents can be resumed by ID from tool results
- **Cost isolated** -- each subagent's token usage is tracked separately
- **Progress summaries** *(verify)* -- enable `agentProgressSummaries: true` to receive periodic AI-generated progress updates from running subagents

---

## 2. Session Management


Sessions persist conversation history to disk, enabling multi-turn workflows.

### Resume a Session (TypeScript)

```typescript
let sessionId: string | undefined;

// First query -- capture session ID
for await (const msg of query({
  prompt: "Read the authentication module",
  options: { allowedTools: ["Read", "Glob"] },
})) {
  if (msg.type === "system" && msg.subtype === "init") {
    sessionId = msg.session_id;
  }
}

// Second query -- resume with full context
for await (const msg of query({
  prompt: "Now refactor it to use JWT",
  options: { resume: sessionId },
})) {
  if ("result" in msg) console.log(msg.result);
}

// Branch instead of continuing: resume + forkSession leaves the original untouched
for await (const msg of query({
  prompt: "Try an alternative approach on a copy of this conversation",
  options: { resume: sessionId, forkSession: true },
})) { /* ... */ }
```

### Continue Most Recent Session

```typescript
// TypeScript
for await (const msg of query({
  prompt: "Continue where we left off",
  options: { continue: true },
})) { /* ... */ }
```

```python
# Python
options = ClaudeAgentOptions(continue_conversation=True)
async for msg in query(prompt="Continue where we left off", options=options):
    pass
```

### Session Client (Python)

Python provides `ClaudeSDKClient` for managed multi-turn conversations:

```python
from claude_agent_sdk import ClaudeSDKClient

async with ClaudeSDKClient() as client:
    # First turn
    await client.query("What's the project structure?")
    async for msg in client.receive_response():
        pass  # process

    # Second turn -- context retained automatically
    await client.query("Now find all API endpoints")
    async for msg in client.receive_response():
        pass  # process

    # Interrupt current generation
    await client.interrupt()
```

### List, Inspect, and Manage Sessions

```typescript
import {
  listSessions, getSessionInfo, getSessionMessages,
  tagSession, renameSession,
} from "@anthropic-ai/claude-agent-sdk";

// List sessions
const sessions = await listSessions({ dir: "/path/to/project", limit: 10 });
for (const session of sessions) {
  console.log(session.sessionId, session.createdAt, session.tag);
}

// Single-session metadata lookup
const info = await getSessionInfo(sessionId);
console.log(info.tag, info.createdAt);

// Read conversation history (includes parallel tool results)
const messages = await getSessionMessages(sessionId);

// Organize sessions with tags and renames
await tagSession(sessionId, "auth-refactor");
await renameSession(sessionId, "auth-refactor-v2");
```

```python
from claude_agent_sdk import (
    list_sessions, get_session_info, get_session_messages,
    tag_session, rename_session,
)

sessions = await list_sessions(dir="/path/to/project", limit=10)
for session in sessions:
    messages = await get_session_messages(session.session_id)

info = await get_session_info(session_id)
await tag_session(session_id, "auth-refactor")
await rename_session(session_id, "auth-refactor-v2")
```

### Session State Events

Session state change events are **opt-in** as of v0.2.83 *(verify)*. Enable with environment variable:

```bash
export CLAUDE_CODE_EMIT_SESSION_STATE_EVENTS=1
```

### Exit Reasons

The `ExitReason` type includes: `"end_turn"`, `"max_turns"`, `"budget"`, `"interrupt"`, `"resume"` *(verify)*.

---

## 3. Introspection Utilities


```typescript
import { supportedAgents } from "@anthropic-ai/claude-agent-sdk";

// Discover available subagents
const agents = await supportedAgents();
```

`getSettings()` *(verify)* appears in some SDK versions for inspecting runtime-resolved settings, but is not in the currently documented API.

---

## 4. ClaudeSDKClient Methods (Python)


The Python `ClaudeSDKClient` provides additional runtime control methods:

```python
async with ClaudeSDKClient() as client:
    # Core conversation
    await client.query("Analyze the codebase")
    async for msg in client.receive_response():
        pass

    # Runtime controls
    await client.set_permission_mode("acceptEdits")
    await client.set_model("claude-sonnet-5")

    # MCP server management
    status = await client.get_mcp_status()
    await client.toggle_mcp_server("my-server", enabled=False)

    # Interrupt current generation
    await client.interrupt()

    # Clean disconnect
    await client.disconnect()
```
