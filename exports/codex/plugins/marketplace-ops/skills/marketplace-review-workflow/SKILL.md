---
name: marketplace-review-workflow
description: 'Quality review of the content of any Claude Code plugin marketplace. TRIGGER WHEN: the user asks to review plugin, agent or skill quality, audit descriptions or trigger keywords, or evaluate activation accuracy and cross-plugin coherence. DO NOT TRIGGER WHEN: just validating marketplace.json structure (use /marketplace-ops:marketplace-health) or authoring new components (use /marketplace-ops:marketplace-scaffold-plugin).'
---

> Arguments: `[plugin-name] [--all] [--fix]`. Wherever `<arguments>` appears below, substitute the text the user typed after the skill name.

<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
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

# marketplace-review

<!-- Generated by the Daodan compiler for codex. Edit the kernel, never this file. -->

## Execution harness

Selected topology: **parallel-subagents**, with role delivery by **inline-prompt**. Start one isolated
runtime subagent per dispatched worker. When role delivery is `inline-prompt`, paste that role's
Markdown body into the dispatch prompt verbatim: the worker must receive the whole role, not a
summary of it.
Declared worker isolation: **required**.

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

- Every dispatched worker runs in its own subagent context and reads only coordinator-declared inputs.
  Independent reviewers never read peer results before their own delivery.
- Follow the dispatch plan below in phase order. A phase starts only after every phase it needs has
  closed, and a phase closes only when every worker it dispatched is recorded `delivered` or
  `failed`. A worker reports delivered or failed in its final message; there is no shared task
  list, so the coordinator keeps that record itself.
- Dispatch only roles from this set, as the phase graph or loaded method requires: `marketplace-manager`
- Workers may write only intermediate reports explicitly assigned by the coordinator.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `scope`: runs in the orchestrating context; produces `artifact:scope`.
2. `review`: one `marketplace-manager` in an isolated context; needs `scope`; consumes `artifact:scope`; produces `artifact:marketplace-review-report`.

Role body bindings (load the complete body only for the selected worker):

- `marketplace-manager`: read `roles/marketplace-manager.md` inside this package and pass its complete body verbatim.

The phase graph and record-schema references ship under `contracts/marketplace-review.workflow.toml`.

## Method

## Source profile preflight

Load marketplace-ops:kernel-marketplace before this procedure. Detect the target's
source model from its manifests and instructions. For daodan/v1 neutral kernels,
follow that skill's operation-specific procedure and finish there. Generated
exports and catalog entries are inspected as output, never authored as source.
The procedure below applies only to a legacy Claude marketplace with hand-authored
agents/ and commands/. It must not be applied to a neutral kernel checkout.



# Marketplace AI Review

Perform an AI-driven quality evaluation of plugin content across any Claude Code plugin marketplace.

## What this evaluates

This review goes beyond structural validation (which `/marketplace-health` handles) and analyzes the **semantic quality** of every plugin component using AI judgment.

## Procedure

### Step 1: Load marketplace data

Read `.claude-plugin/marketplace.json` at the project root to get the full plugin registry.

### Step 2: For each plugin (or the specified one), evaluate these dimensions

#### A. Plugin Description Quality (marketplace.json)

Evaluate the `description` field:
- **Clarity**: Is it immediately clear what the plugin does?
- **Trigger coverage**: Does it mention enough trigger scenarios for Claude to auto-invoke?
- **Specificity**: Does it name concrete actions, not just abstract categories?
- **Length**: Under 1024 chars, ideally under 300 for auto-load discoverability
- **Keyword coverage**: Keywords array contains the concrete domain terms users will search for

#### B. Agent Quality (for each agent in the plugin)

Read the agent `.md` file:
- **Description directive voice**: Uses "ALWAYS invoke", "You MUST", "Use PROACTIVELY" or similar (vs passive "Helps with", "Can be used for")
- **TRIGGER WHEN clause**: present, specific, uses concrete verbs / domain terms
- **DO NOT TRIGGER WHEN clause**: present only where a confusable sibling exists, and naming it (which other agent should handle this case instead). A clause that names none is context cost with no routing value: flag it for deletion
- **Body structure**: clear sections (ROLE, CAPABILITIES, CONVENTIONS, OUTPUT FORMAT or similar)
- **Body size**: 60-200 lines for simple agents, up to ~560 lines for complex; flag over 700 lines
- **Tool restrictions**: minimal but sufficient (e.g., a read-only reviewer should NOT have Write/Edit)
- **Model choice**: justified if not `opus`
- **Color consistency**: matches siblings in the same plugin where appropriate

#### C. Skill Quality (for each skill in the plugin)

Read the skill `SKILL.md`:
- **Description**: same directive voice + TRIGGER WHEN / DO NOT TRIGGER WHEN checks as agents
- **Body size**: under 500 lines; larger content should go in `references/`
- **Progressive disclosure**: uses `references/` for deep content, keeps SKILL.md scannable
- **Action-oriented**: teaches what Claude doesn't already know; avoids restating general best practices
- **Examples**: 3-5 `<example>` tags for high-activation skills

#### D. Command Quality (for each command in the plugin)

Read the command `.md` file:
- **Frontmatter shape**: `description` and `argument-hint` as separate YAML keys (not a single concatenated string)
- **Argument hint**: accurate, shows the expected arguments
- **Body**: actionable procedure, not just marketing copy
- **Integration**: references the agent or skill that does the real work

### Step 3: Cross-plugin coherence

- Detect overlapping triggers between plugins (two agents competing for the same activation)
- Detect orphan references (agent X references skill Y that doesn't exist)
- Identify missing sibling-conflict DO NOT TRIGGER clauses when two plugins cover adjacent domains

### Step 4: Report

Write `.marketplace-review/REPORT.md` with:

```markdown
# Marketplace AI Review -- <marketplace-name> -- <date>

## Summary
- Plugins evaluated: N
- Critical issues: K
- Recommendations: M

## Per-plugin findings
### <plugin-name>
- Description score: X/5 -- <reasoning>
- Agents: ...
- Skills: ...
- Commands: ...
- Recommended fixes:
  - [CRITICAL] ...
  - [WARNING] ...

## Cross-plugin observations
- ...
```

### With --fix flag

For each recommendation, offer to apply the fix with user confirmation. Stage changes via Edit, do not auto-commit.

## Notes

- Marketplace-agnostic: works on any project with a standard Claude Code plugin layout.
- Complements (does not replace) the deterministic audit run by `/marketplace-ops:marketplace-health` and the detailed lint in `/marketplace-ops:skills-validate`.
