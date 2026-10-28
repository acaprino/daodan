---
description: 'Scaffold a new plugin for any Claude Code plugin marketplace. TRIGGER WHEN: the user asks to create a new plugin, bootstrap plugin structure, or add a new entry to marketplace.json. DO NOT TRIGGER WHEN: adding a skill or agent to an existing plugin (use skills-creator).'
---

<daodan_host_binding host="pi">
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

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi has no network tool: network fetch and network search run as shell
commands, and a user question is asked in the reply while the run waits for the
answer.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

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

# marketplace-scaffold-plugin

<!-- Generated by the Daodan compiler for pi. Edit the kernel, never this file. -->

## Execution harness

Selected topology: **parallel-subagents**, with role delivery by **inline-prompt**, and declared
isolation **required**. Dispatch one worker per entry in the plan below with the `subagent`
tool supplied by the `pi-subagents` package, each in its own context. Role delivery here is
`inline-prompt`: paste that role's Markdown body into the dispatch prompt verbatim, because the
worker must receive the whole role rather than a summary of it.

Pi's core ships no subagent tool. Apply the availability check when the selected task
requires a dispatched worker. If the method explicitly permits a worker-free path
(for example, read-only inspection or a narrow edit), record why no worker is needed
and continue that path without this companion. Do not waive a required worker.
If a worker is needed and no subagent tool is available, the declared isolation
above decides what happens, and the two cases are not interchangeable:

- **`required`**: stop the dependent dispatch, and tell the user to run `pi install npm:pi-subagents`. Running the phases
  serially in this one context is the loss of isolation rather than a lesser form of it, so a
  report produced that way would claim a contract it did not meet.
- **`shared`**: run the phases in order in this context, and say in the report that no worker was
  isolated.

Coordinator completion ownership: keep the method's owned run and delivery ledger,
including each expected worker, attempt, report path and required check evidence.
Validate report artifacts before recording delivered. An empty final message or
worker stop remains missing delivery: inspect or resume when permitted, otherwise
record failed with the uncovered scope. Follow the declared join and phase gates;
a recorded failure is accounted for, never converted into a successful delivery.
Continue authorized work and recovery until the requested result and its checks
exist or a concrete blocker is recorded. Preserve the exclusive final report owner
and the ledger schema; a tool exit or a promise cannot satisfy completion.

Harness obligations, none of them optional:

- Every dispatched worker runs in its own context and reads only coordinator-declared inputs.
  Independent reviewers never read peer results before their own delivery.
- Follow the dispatch plan below in phase order. A phase starts only after every phase it needs has
  closed, and a phase closes only when every worker it dispatched is recorded `delivered` or
  `failed`. A worker reports delivered or failed in its final message; there is no shared task
  list, so the coordinator keeps that record itself.
- Dispatch only roles from this set, as the phase graph or loaded method requires: `marketplace-manager`
- A worker writes only what the coordinator assigned to it: its intermediate report and, when its
  task authorizes edits, its assigned files. It never reverts preexisting or foreign changes.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `scope`: runs in the orchestrating context; produces `artifact:scope`.
2. `review`: one `marketplace-manager` in an isolated context; needs `scope`; consumes `artifact:scope`; produces `artifact:marketplace-scaffold-plugin-report`.

Role body bindings (load the complete body only for the selected worker):

- `marketplace-manager`: read `skills/marketplace-ops-marketplace-manager/SKILL.md` inside this package and pass its complete body verbatim.

The phase graph and record-schema references are in `contracts/marketplace-scaffold-plugin.workflow.toml`.

## Method

## Source profile preflight

Load marketplace-ops:kernel-marketplace before this procedure. Detect the target's
source model from its manifests and instructions. For daodan/v1 neutral kernels,
follow that skill's operation-specific procedure and finish there. Generated
exports and catalog entries are inspected as output, never authored as source.
The procedure below applies only to a legacy Claude marketplace with hand-authored
agents/ and commands/. It must not be applied to a neutral kernel checkout.



# Scaffold New Plugin

Create a new plugin following the standard Claude Code plugin conventions (works against any marketplace with a `.claude-plugin/marketplace.json` registry).

## Procedure

### 1. Parse arguments

- `plugin-name`: required, kebab-case
- `--with-agent`: create an agent `.md` starter
- `--with-skill`: create a skill directory with `SKILL.md` starter
- `--with-command`: create a command `.md` starter
- `--category`: plugin category; if omitted, read existing `marketplace.json` to list current categories and ask the user to pick or propose a new one
- `--author`: plugin author; if omitted, read the first plugin's author from `marketplace.json` and use it (or ask the user if the marketplace is empty)
- If no `--with-*` flags are provided, ask the user what components they want

### 2. Create directory structure

```
plugins/<plugin-name>/
  agents/          (if --with-agent)
  skills/          (if --with-skill)
  commands/        (if --with-command)
```

Do NOT create empty subdirectories.

### 3. Create starter files

Starters are minimal and use real content. They show the required frontmatter shape and leave clearly labelled `{{PLACEHOLDER}}` fields for the user to fill. They are NOT registered until the user confirms the content.

**Agent starter** (`agents/<plugin-name>.md`):
```markdown
---
name: <plugin-name>
description: >
  {{ONE_SENTENCE_ROLE}}
  TRIGGER WHEN: {{concrete triggers, comma-separated}}
  DO NOT TRIGGER WHEN: {{sibling-conflict exclusions}}
model: inherit
color: {{red | blue | green | yellow | purple | orange | pink | cyan}}
---

# ROLE
{{Agent purpose in 1-3 sentences}}

# CAPABILITIES
{{Bulleted list of what this agent does}}

# CONVENTIONS
{{Any non-obvious conventions the agent must follow}}

# OUTPUT FORMAT
{{How findings/results should be structured}}
```

**Skill starter** (`skills/<skill-name>/SKILL.md`):
```markdown
---
name: <skill-name>
description: >
  {{ONE_SENTENCE_ROLE}}
  TRIGGER WHEN: {{concrete triggers}}
  DO NOT TRIGGER WHEN: {{sibling-conflict exclusions}}
---

# {{Skill Title}}

{{Skill instructions -- teach what Claude does not already know}}
```

**Command starter** (`commands/<command-name>.md`):
```markdown
---
description: >
  {{ONE_SENTENCE_ROLE}}
  TRIGGER WHEN: {{concrete triggers}}
  DO NOT TRIGGER WHEN: {{sibling-conflict exclusions}}
argument-hint: "{{expected arguments}}"
---

# {{Command Title}}

{{Command procedure}}
```

### 4. Register in marketplace.json

Add entry to `plugins[]` array:
```json
{
  "name": "<plugin-name>",
  "source": "./plugins/<plugin-name>",
  "description": "{{one-sentence description}}",
  "version": "1.0.0",
  "author": { "name": "<author-from-step-1>" },
  "license": "{{license from existing plugins, often MIT}}",
  "keywords": ["<plugin-name>"],
  "category": "<category-from-step-1>",
  "strict": false,
  "agents": [],
  "skills": [],
  "commands": []
}
```

Populate `agents` / `skills` / `commands` arrays with the relative paths of files just created. Omit empty arrays.

### 5. Bump metadata.version

Increment the marketplace `metadata.version` (typically minor for a new plugin).

### 6. Report

Show:
- Created files with paths
- Updated marketplace.json entry
- Next actions: fill placeholders in the starter files, add real keywords, then run `/marketplace-ops:marketplace-health` to validate

## Notes

- Marketplace-agnostic: respects whatever author, license, and category conventions already exist in the target marketplace.
- Never hardcodes an author -- reads from existing plugins or asks the user.
- Never hardcodes a license -- reads from existing plugins or asks.
