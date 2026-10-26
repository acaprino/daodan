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

# Claude Code Plugin Conventions Reference

This reference documents the standard conventions used across Claude Code plugin marketplaces. Individual marketplaces may extend or restrict these conventions in their own `CLAUDE.md` -- always read the target project's CLAUDE.md first.

## Agent Color Palette

Valid colors: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`

### Semantic Color Guidance

- **Warm** (red, orange, yellow, pink) -- creative, outward-facing, marketing, content
- **Cool** (blue, cyan, purple) -- analytical, development, code quality
- **Neutral** (green) -- tooling, infrastructure, utilities

All agents within a plugin should use the same color. Avoid reusing a color across more than 3 plugins.

## Plugin Categories

Plugin categories are marketplace-specific. Read the existing `marketplace.json` to learn the local taxonomy before choosing one; if proposing a new category, confirm with the user.

Common categories observed across marketplaces: `review`, `development`, `frontend`, `ai-ml`, `utilities`, `infrastructure`, `research`, `business`, `documentation`, `mobile`, `optimization`, `marketing`, `payments`, `workflow`, `productivity`, `testing`, `analysis`, `security`, `algotrading`.

## Agent Tools

Available tools for the `tools` frontmatter field (comma-separated):

`Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`, `WebFetch`, `WebSearch`, `Task`

Omit the `tools` field entirely to allow all tools.

## Marketplace.json Required Fields (per plugin)

```
name, source, description, version, author, license, keywords, category, strict
```

Plus arrays (include only non-empty): `agents`, `skills`, `commands`

Optional: `dependencies`, `optionalDependencies` (arrays of plugin names)

## Naming Rules

- Plugin directories: kebab-case
- Agent filenames: kebab-case `.md`, filename matches `name` frontmatter
- Skill directories: kebab-case, directory name matches `name` frontmatter
- Command filenames: kebab-case `.md`
- Avoid the dash-aside construct in any form (`—`, `--`, or ` - `); rewrite with colons, parentheses, or separate sentences

## Agent Body Structure

Terse keyword-list style, imperative tone. Standard sections:

```
# ROLE
[One-line purpose]

# CORE CAPABILITIES
## 1. [Capability]
- Key behavior
- Key behavior

# CONVENTIONS
- Convention list

# OUTPUT FORMAT
- Format instructions
```

Simple agents: 60-200 lines. Complex agents: up to 700 lines (move domain knowledge to a skill's `references/`).

## Description Format (Skills and Agents)

The description sits in context in every session and governs routing accuracy.

### Calibrated Trigger Template

```yaml
# Skill description
description: >
  <Concise third-person summary>.
  TRIGGER WHEN: <specific triggers, comma-separated>.
  DO NOT TRIGGER WHEN: <the confusable case> (use <sibling-component> instead).

# Agent description (multiline with >)
description: >
  <Concise third-person role summary>.
  TRIGGER WHEN: <triggers>.
  DO NOT TRIGGER WHEN: <the confusable case> (use <sibling-component> instead).
```

### Rules

- **Calibrated trigger phrasing**: state purpose and concrete `TRIGGER WHEN:` conditions; avoid emphasis escalation (`CRITICAL: ALWAYS invoke`) which causes overtriggering on frontier models
- **TRIGGER WHEN on user-triggered components**: carries the distinctive vocabulary that routes to this component (internal coordinator-loaded method skills and sub-roles may state their purpose and caller without `TRIGGER WHEN`)
- **DO NOT TRIGGER WHEN only when it names a sibling**: see the rule below
- **Third person**: "Processes X when Y", not "I process X"
- **Max 1024 characters** per description
- **Under 300 characters** recommended (token budget)
- **Specific trigger phrases**: list exact words/actions that should activate
- **No term in both the opening sentence and TRIGGER WHEN**: the trigger line keeps it, the opening sentence yields

### The DO NOT TRIGGER WHEN rule

A `DO NOT TRIGGER WHEN` clause earns its context cost only by naming the component that should handle the case instead. It is a routing instruction, not a disclaimer.

```yaml
# Useless: states the logical inverse of TRIGGER WHEN and discriminates nothing
DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.

# Useful: routes the confusable case to a named sibling
DO NOT TRIGGER WHEN: the target is a Python codebase (use python-dead-code instead).
```

When no confusable sibling exists, omit the clause. Adding one anyway costs every session context and buys no routing accuracy.

### Low-Activation and Overtriggering Anti-patterns

- "Helps with stuff": vague, no concrete triggers
- "CRITICAL: You MUST ALWAYS invoke this skill": emphasis escalation that causes false-positive triggers
- A `DO NOT TRIGGER WHEN` clause naming no sibling: pure context cost, delete it

## Token Budget

Descriptions are the only part of a component that sits in context in **every** session; the body loads only after invocation. Anything a description restates from its own body is pure cost.

- Each skill/agent costs ~100 tokens at idle (name + description in system prompt)
- All descriptions share a **15,000 character** budget by default
- When total exceeds limit, components may be silently dropped
- Do not enumerate in a description what the body already covers: list the trigger vocabulary, not the feature set

## Skill SKILL.md Structure

```yaml
---
name: skill-name
description: >
  "<What it does>" argument-hint: "<usage hint>".
  TRIGGER WHEN: <triggers>.
  DO NOT TRIGGER WHEN: <exclusions>.
---
```

Body: under 500 lines, imperative tone, only context Claude lacks.
Progressive disclosure: split into references/ when exceeding ~300 lines.

### Optional Frontmatter Fields

- `context: fork` -- runs skill in isolated subagent context
- `allowed-tools` -- restricts which tools the skill can use
- `disable-model-invocation: true` -- prevents auto-triggering (slash-command only)
