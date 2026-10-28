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

# Skills vs Agents Decision Framework

## Core Concepts

**Skills = "La ricetta" (the recipe)** -- knowledge that shapes what the agent knows
- SKILL.md + references/ directories loaded into the active agent's context
- Composable: Claude auto-selects the right skill for the task
- Teach expertise, conventions, patterns, domain knowledge
- Do NOT change who is doing the work or what tools are available

**Agents = "Il collega specializzato" (the specialist colleague)** -- isolated worker with own context
- Agent .md files with frontmatter (name, description, model, tools, color) + system prompt
- Own context window, tool permissions, execution isolation
- Return results to parent; protect main context from noise
- Change WHO is doing the work and what they can access

## Decision Table

| Signal | Use Skill | Use Agent |
|--------|-----------|-----------|
| Adds domain knowledge / conventions | Yes | No |
| Needs tool permission isolation | No | Yes |
| Should be available to ANY agent | Yes | No |
| Runs independently, returns results | No | Yes |
| Multiple alternatives for same domain | Separate skills | No |
| Protects main context from large output | No | Yes |
| Reusable recipes / checklists | Yes | No |
| Parallel execution needed | No | Yes |
| Builds something new from scratch | No | Yes |
| Reference docs / API guides | Yes (references/) | No |

## Rule of Thumb

Start with a composable Skill. Escalate to an Agent when you need:
1. **Isolation** -- own context window to avoid polluting the parent
2. **Tool restrictions** -- specific tool subset (e.g., read-only agent)
3. **Parallel work** -- independent tasks that run concurrently
4. **Specialist persona** -- distinct role with its own system prompt

If none of these apply, a skill is the right choice.

## Patterns from Real Restructures

### tauri-development (3 skills -> 1 skill + 3 agents)
- **Before:** 3 separate skills (tauri2-desktop, tauri2-mobile, rust-development) each trying to be both knowledge AND worker
- **After:** 1 unified skill (tauri2-mobile - knowledge/recipes) + 3 agents (rust-engineer, tauri-optimizer, tauri2-mobile - specialist workers)
- **Why:** The skills were being invoked as isolated workers needing specific tools. Skills don't have tool restrictions or context isolation -- agents do.

### python-development (1 mega-skill -> 9 skills + 3 agents)
- **Before:** one broad skill trying to hold TDD discipline, refactoring recipes, async patterns, and packaging at once
- **After:** Focused Python techniques (pytest-patterns, python-refactor-method, async-python-patterns, uv-package-manager, pydantic-v2) and implementation/refactor roles. Universal test work belongs to testing:test-writer; the language plugin contributes techniques instead of another test owner.
- **Why:** recipes and conventions are skill territory, and they load only when the task matches. Work that needs tool restrictions and its own context window becomes an agent.

## Anti-patterns

| Anti-pattern | Why it's wrong | Fix |
|--------------|----------------|-----|
| Merging alternative libraries into one skill | Bloats context, forces irrelevant knowledge | One skill per library, never one skill covering all of them |
| Splitting layers of same domain into separate skills | Fragments knowledge that belongs together | One unified skill with references/ for depth |
| Skill that needs specific tool permissions | Skills inherit parent's tools, can't restrict | Make it an agent with explicit `tools` field |
| Agent that's just a knowledge dump with no isolation need | Wastes a context window, adds latency | Convert to a skill |
| One mega-agent covering an entire domain | Too broad, poor at any specific task | Split into focused agents + shared skill for knowledge |

## Combination Pattern

The most common healthy architecture is: **1 skill (knowledge) + N agents (specialists)**

```
plugins/<domain>/
  skills/
    <domain>/          # unified knowledge base
      SKILL.md         # recipes, conventions, patterns
      references/      # deep reference material
    <alt-1>/           # alternative library/framework skill
    <alt-2>/           # another alternative
  agents/
    <specialist-1>.md  # focused worker agent
    <specialist-2>.md  # another focused worker
```

The skill teaches; the agents do.
