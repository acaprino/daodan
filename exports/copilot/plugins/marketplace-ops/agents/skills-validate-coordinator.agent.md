---
name: skills-validate-coordinator
description: 'Validate skill and agent quality: deterministic activation checks plus AI body review. TRIGGER WHEN: the user asks to validate skill/agent quality, enforce trigger patterns, check description token budgets, or run pre-commit marketplace checks. DO NOT TRIGGER WHEN: checking structural JSON references only (use /marketplace-ops:marketplace-health) or doing an AI-only content review (use /marketplace-ops:marketplace-review).'
tools: ['agent', 'edit', 'fetch', 'runCommands', 'search']
agents: ['marketplace-manager']
---

> Arguments: `[plugin-name] [--all] [--skip-ai]`. Wherever `<arguments>` appears below, substitute the text the user typed after the prompt name.

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

# skills-validate

<!-- Generated by the Daodan compiler for copilot. Edit the kernel, never this file. -->

## Execution harness

Selected topology: **parallel-subagents**. Dispatch the workers listed in this agent's `agents` allowlist and
nothing else. Request them in parallel where the plan allows it; serializing them is permitted and
changes no part of the contract.
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

- Every dispatched worker runs in its own context and reads only coordinator-declared inputs.
  Independent reviewers never read peer results before their own delivery.
- Follow the dispatch plan below in phase order. A phase starts only after every phase it needs has
  closed, and a phase closes only when every worker it dispatched is recorded `delivered` or
  `failed`. A worker reports delivered or failed in its final message; there is no shared task
  list, so this coordinator keeps that record itself.
- Dispatch only roles from this set, as the phase graph or loaded method requires: `marketplace-manager`
- A worker writes only what the coordinator assigned to it: its intermediate report and, when its
  task authorizes edits, its assigned files. It never reverts preexisting or foreign changes.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `scope`: runs in the orchestrating context; produces `artifact:scope`.
2. `review`: one `marketplace-manager` in an isolated context; needs `scope`; consumes `artifact:scope`; produces `artifact:skills-validate-report`.

Role bindings:

- `marketplace-manager`: dispatch the installed `marketplace-ops:marketplace-manager` agent by its qualified identity.

The phase graph and record schemas ship with this package in
`contracts/skills-validate.workflow.toml`.

## Method

## Source profile preflight

Load marketplace-ops:kernel-marketplace before this procedure. Detect the target's
source model from its manifests and instructions. For daodan/v1 neutral kernels,
follow that skill's operation-specific procedure and finish there. Generated
exports and catalog entries are inspected as output, never authored as source.
The procedure below applies only to a legacy Claude marketplace with hand-authored
agents/ and commands/. It must not be applied to a neutral kernel checkout.



# Skills Validation

Deterministic activation-quality checks plus AI-powered body review for all skills and agents.

## What this validates

### Deterministic checks (script)

1. **Trigger calibration**: description states purpose and `TRIGGER WHEN:` (or explicit coordinator caller for internal method skills/worker roles) without emphasis escalation (`CRITICAL: ALWAYS invoke`)
2. **TRIGGER WHEN clause**: explicit activation boundary present on user-triggered components
3. **DO NOT TRIGGER WHEN clause**: when present, must name the sibling to route to; absence is fine when no confusable sibling exists
4. **Passive pattern detection**: flags vague openings ("Helps with", "Can be used for", "Useful for")
5. **Description length**: hard limit 1024 chars, recommended under 300
6. **Token budget**: total description chars across all components vs 35,000 char budget
7. **SKILL.md body size**: warn over 300 lines without `references/`, flag over 500 lines
8. **Agent body size**: flag over 700 lines
9. **Dash-aside detection**: flags em dash (`—`) outside pattern-catalog documentation
10. **Token estimate**: SKILL.md body chars/4, target under 5,000 tokens
11. **context: fork**: reports if skill uses isolated subagent context
12. **disable-model-invocation**: reports if auto-triggering is disabled
13. **!command preprocessor**: detects shell command injection in skill body

### AI review dimensions (Step 5)

- **Structure** -- section organization, logical flow, no wall-of-text
- **Clarity** -- actionable instructions, no vague directives, teaches only what Claude lacks
- **Redundancy** -- no repetition, no filler, every sentence adds unique value
- **Progressive disclosure** -- large content split into references/ appropriately
- **Tool restrictions** -- agents have appropriate tools for their role
- **Isolation needs** -- destructive skills should use context: fork

## Procedure

### Step 1: Run the validation script

```bash
# Validate all plugins
python plugins/marketplace-ops/skills/skills-creator/scripts/validate_skills.py --all

# Validate a specific plugin
python plugins/marketplace-ops/skills/skills-creator/scripts/validate_skills.py <plugin-name>
```

### Step 2: Review the report

The script outputs:
- Token budget usage (current chars / 15,000 budget)
- Estimated total body tokens across all skills
- Per-component issues grouped by plugin
- Activation score summary table (1-5 per component)
- Components scoring below 3/5 flagged for attention

### Step 3: Fix low-scoring descriptions

For each component scoring below 3/5, rewrite the description following the high-activation template:

```yaml
description: >
  "<Domain summary>" argument-hint: "<usage hint>".
  TRIGGER WHEN: <specific triggers>.
  DO NOT TRIGGER WHEN: <exclusions>.
```

### Step 4: Re-validate deterministic checks

Run the script again to confirm all scores improved.

### Step 5: AI body quality review

Skip this step if the user passed `--skip-ai`.

Read the SKILL.md body and agent body of each component that scored below 4/5 OR was flagged for token/line/body issues. For each, evaluate these dimensions:

#### 5A. Structure (score 1-5)

- **5/5**: Clear headers (## Purpose, ## Procedure, ## Constraints, ## Output), logical flow
- **3/5**: Some structure but sections bleed into each other or headers are vague
- **1/5**: Wall-of-text, no headers, instructions mixed with examples

#### 5B. Clarity (score 1-5)

- **5/5**: Every instruction is specific, imperative, teaches only what Claude doesn't already know
- **3/5**: Mostly clear but has vague directives ("handle appropriately", "use best judgment")
- **1/5**: Instructions repeat common knowledge, contradict each other, or are ambiguous

#### 5C. Redundancy (score 1-5)

- **5/5**: Every sentence adds unique value, no repetition
- **3/5**: Some duplication between description and body, or preambles before actionable content
- **1/5**: Same instruction stated multiple ways, "You are an expert in..." throat-clearing, verbose filler

#### 5D. Progressive disclosure (score 1-5)

- Skip if body <150 lines
- **5/5**: Body under 300 lines OR large body with well-used references/ directory
- **3/5**: Body >300 lines with references/ but wrong content split
- **1/5**: Body >300 lines with no references/ directory

#### 5E. Tool restrictions (score 1-5, agents only)

- **5/5**: Tools list matches agent's actual needs precisely
- **3/5**: Slightly over-permissive but not dangerous
- **1/5**: All tools allowed when agent only needs Read/Grep, or missing tools it clearly needs

#### 5F. Isolation needs (score 1-5)

- **5/5**: Pure knowledge/conventions skill (no isolation needed) OR destructive skill with context: fork
- **3/5**: Runs shell commands but low risk
- **1/5**: Performs destructive operations, generates huge output, or calls external APIs without context: fork

#### Output format

For each reviewed component:

```
### <plugin>/<component> -- Body Quality

| Dimension   | Score | Issue |
|-------------|-------|-------|
| Structure   | X/5   | ...   |
| Clarity     | X/5   | ...   |
| Redundancy  | X/5   | ...   |
| Disclosure  | X/5   | ...   |
| Tool restr. | X/5   | ...   |
| Isolation   | X/5   | ...   |

**Top fix:** <single most impactful improvement>
```

### Step 6: Final re-validate

Run the script one more time to confirm all deterministic fixes landed cleanly.
