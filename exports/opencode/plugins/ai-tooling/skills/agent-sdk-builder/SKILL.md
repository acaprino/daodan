---
name: agent-sdk-builder
description: >
  Run the Claude Agent SDK (formerly Claude Code SDK) loop inside your own program, not the `anthropic` client SDK for chat completions.
  TRIGGER WHEN: code references claude-agent-sdk, user says "agent sdk", "build an agent", "programmatic claude", "claude code sdk", "sidecar", "run claude programmatically"; or asks about tool integration, subagent orchestration, prompt caching or model migration inside that loop.
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/`, `agents/` and `commands/`. The loader substitutes it in every body it registers; in any other file, resolve it once from where that file was loaded.

<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
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

# Claude Agent SDK

Build applications that run the Claude Code agent loop programmatically: agents that read files,
write code, run commands, search the web, and delegate to subagents from inside your own program.

**Key distinction**: the Agent SDK (`claude-agent-sdk`) runs the full agent loop with built-in
tools. The Anthropic Client SDK (`anthropic`) makes raw API calls. Use the Agent SDK when you want
an autonomous tool-using agent, not a chat completion.

| | TypeScript | Python |
|---|---|---|
| **Package** | `@anthropic-ai/claude-agent-sdk` | `claude-agent-sdk` |
| **Install** | `npm install @anthropic-ai/claude-agent-sdk` | `pip install claude-agent-sdk` |
| **Auth** | `ANTHROPIC_API_KEY` env var | `ANTHROPIC_API_KEY` env var |
| **Entry point** | `query()` | `query()` |
| **Source** | `anthropics/claude-agent-sdk-typescript` | `anthropics/claude-agent-sdk-python` |

The CLI package `@anthropic-ai/claude-code` ships inside the SDK. No separate install.

---

## Source of truth

This SDK changes faster than any bundled document. Option shapes, tool names, defaults, and whole
features move between releases: `fork_session` changed type, `plugins` changed from paths to config
objects, and the TypeScript V2 preview was removed outright. Treat this skill's knowledge as
orientation, never as the authority.

Three tiers. Stop at the first one that answers the question:

1. **The project's installed SDK.** TypeScript: the type definitions under
   `node_modules/@anthropic-ai/claude-agent-sdk/` and the version in its `package.json`. Python:
   the installed package under `site-packages/claude_agent_sdk/`, or `inspect.signature()` on the
   symbol. This tier wins over everything else, because it is what the user's code will run
   against.
2. **Current official documentation**, https://code.claude.com/docs/en/agent-sdk/. Use it when
   nothing is installed yet, or when the question is about behavior rather than a signature.
3. **The references in this skill.** Worked examples and orientation. Never the last word on a
   signature, an option shape, a default, or whether a feature still exists.

Classify a claim before you rely on it:

| Class | Example | Resolve with |
|---|---|---|
| STABLE | "Restrict `allowedTools` to what the task needs." | This skill |
| API-SENSITIVE | "`forkSession` is a boolean used with `resume`." | Tier 1, then tier 2 |
| MODEL-SENSITIVE | "This model id and effort level exist." | Tier 2 |

Never emit API-sensitive code from memory when tier 1 or tier 2 can settle it. Items marked
*(verify)* in the references are the ones that failed tier-2 resolution at the last refresh: they
are unconfirmed rather than confirmed-absent, and checking them is cheap.

---

## Step 1: Detect the environment

Do this before writing a line of code, and state what you found.

- **Language.** A `package.json` naming `@anthropic-ai/claude-agent-sdk` means TypeScript. A
  `pyproject.toml`, `requirements.txt`, or `uv.lock` naming `claude-agent-sdk` means Python.
- **Installed version.** `npm ls @anthropic-ai/claude-agent-sdk` or `pip show claude-agent-sdk`.
  Record it: every API-sensitive answer you give is relative to that version.
- **Nothing installed.** Say so, install the current release, and resolve signatures from tier 2.
- **Version pinned below current.** Honor the pin. Resolve against the installed types, and if the
  user asks for a feature that release does not have, say which version added it instead of
  emitting code that cannot run.

## Step 2: Pick the shape

| Need | Shape | Reference |
|---|---|---|
| One task, run to completion | `query()` | `references/sdk-api.md` |
| Multi-turn with retained context | `ClaudeSDKClient` (Python), or `query()` with `resume` | `references/sessions-subagents.md` |
| Branch a conversation without mutating it | `resume` plus `forkSession` | `references/sessions-subagents.md` |
| Delegate specialized work | `agents` plus the `Agent` tool | `references/sessions-subagents.md` |
| Give the agent your own functions | in-process MCP server | `references/mcp-plugins-skills.md` |
| Reuse existing Claude Code plugins | `plugins` and `settingSources` | `references/mcp-plugins-skills.md` |
| A machine-readable result | `outputFormat` with a JSON schema | `references/sdk-api.md` |
| Coarse "what may it use at all" | `allowedTools` / `disallowedTools` / `permissionMode` | `references/permissions-hooks-security.md` |
| A rule that must hold on every call | `PreToolUse` hook | `references/permissions-hooks-security.md` |
| Decide unresolved requests in code | `canUseTool` | `references/permissions-hooks-security.md` |
| Run untrusted work | sandbox and container isolation | `references/deployment.md` |
| Ship it somewhere | ephemeral or long-running hosting | `references/deployment.md` |

Load only the reference the chosen row names. Loading all five defeats the point.

## Step 3: Security model

Three mechanisms, three jobs. Substituting one for another is the most common way an SDK
application ends up with security that does not run:

| Mechanism | Job |
|---|---|
| `allowedTools` / `disallowedTools` / `permissionMode` | Coarse policy: what the agent may use at all |
| `PreToolUse` hook | Always-on enforcement: runs for every matching call, before permission resolution |
| `canUseTool` | Interactive fallback: runs only for calls no rule, mode, or hook already resolved |

**A validation rule that must always hold belongs in a `PreToolUse` hook.** Anything you allow-list
never reaches `canUseTool`, so a check placed there stops running the moment the tool is approved,
silently. `disallowedTools` is the only hard block and outranks even `bypassPermissions`. Details
and worked examples: `references/permissions-hooks-security.md`.

Also standing: set `maxTurns` and `maxBudgetUsd` on anything autonomous, keep secrets out of
prompts (use `env` or an MCP tool instead), and isolate untrusted work in a container.

## Step 4: Build and validate

1. Write the smallest program that does the job. Resist adding options you have not verified.
2. Resolve every API-sensitive detail against tier 1, then tier 2.
3. Type-check where the project supports it (`tsc --noEmit`, or the project's type checker).
4. Run it once on a cheap prompt with `maxTurns` and `maxBudgetUsd` set low, before running it for
   real.
5. Report which facts came from the installed SDK, which from the documentation, and name anything
   you could not verify. A named gap is useful; a confident guess is not.

---

## References

| File | Holds |
|---|---|
| `references/sdk-api.md` | Install, `query()`, full options table, built-in tools, streaming, structured output, cost tracking, migration from `claude-code-sdk` |
| `references/sessions-subagents.md` | Sessions, resume, fork, session metadata, introspection, subagent definitions, Python client methods |
| `references/permissions-hooks-security.md` | Permission modes and evaluation order, `canUseTool`, hook events and matchers, security practices |
| `references/mcp-plugins-skills.md` | Custom tools as in-process MCP servers, external MCP servers, loading plugins and settings |
| `references/deployment.md` | Hosting shapes, sandbox isolation, CI/CD review agent, research pipeline, chat loop |

Reasoning patterns belong to the `prompt-engineer` agent, not to the SDK. That reference lives in
the prompt-engineering skill: `<plugin-root>/skills/prompt-engineering/references/reasoning-patterns.md`.

## Official documentation

- [Overview](https://code.claude.com/docs/en/agent-sdk/overview)
- [TypeScript reference](https://code.claude.com/docs/en/agent-sdk/typescript)
- [Python reference](https://code.claude.com/docs/en/agent-sdk/python)
- [Permissions](https://code.claude.com/docs/en/agent-sdk/permissions)
- [Hooks](https://code.claude.com/docs/en/agent-sdk/hooks)
- [Sessions](https://code.claude.com/docs/en/agent-sdk/sessions)
- [Subagents](https://code.claude.com/docs/en/agent-sdk/subagents)
- [Custom tools and MCP](https://code.claude.com/docs/en/agent-sdk/custom-tools)
- [Hosting](https://code.claude.com/docs/en/agent-sdk/hosting)
- [Secure deployment](https://code.claude.com/docs/en/agent-sdk/secure-deployment)
- [Migration guide](https://code.claude.com/docs/en/agent-sdk/migration-guide)
- [Demo apps](https://github.com/anthropics/claude-agent-sdk-demos)
