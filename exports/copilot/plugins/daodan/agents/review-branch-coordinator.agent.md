---
name: review-branch-coordinator
description: 'Complete review of a branch against its base, or of a pull request: every perspective the signals activate, the map, blind derivation of premises and the verification panel, chosen by a script from the diff and the map. TRIGGER WHEN: the user asks for a full or deep review of a branch, a pull request or a large change, or before a merge. DO NOT TRIGGER WHEN: only the current changes or one commit are to be reviewed (use review-changes).'
tools: ['agent', 'codebase-map/*', 'edit', 'moe/*', 'peer-review/*', 'runCommands', 'search']
agents: ['abstraction-architect:abstraction-architect-agent', 'codebase-map:map-analyst', 'codebase-map:semantic-interconnect-mapper', 'platform-engineering:platform-reviewer', 'project-protocol:isolated-worker', 'react-development:react-performance-optimizer', 'repo-hygiene:workspace-auditor', 'senior-review:api-contract-auditor', 'senior-review:chicken-egg-detector', 'senior-review:cleanup-auditor', 'senior-review:code-auditor', 'senior-review:data-integrity-auditor', 'senior-review:distributed-flow-auditor', 'senior-review:logic-integrity-auditor', 'senior-review:premise-auditor', 'senior-review:resource-lifecycle-auditor', 'senior-review:security-auditor', 'senior-review:temporal-resilience-auditor', 'senior-review:ui-race-auditor', 'testing:test-suite-auditor', 'typescript-development:type-safety-auditor']
---

> Arguments: `[branch or pull request]`. Wherever `<arguments>` appears below, substitute the text the user typed after the prompt name.

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

# review-branch

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
- Dispatch only roles from this set, as the phase graph or loaded method requires: `abstraction-architect:abstraction-architect-agent`, `codebase-map:map-analyst`, `codebase-map:semantic-interconnect-mapper`, `platform-engineering:platform-reviewer`, `project-protocol:isolated-worker`, `react-development:react-performance-optimizer`, `repo-hygiene:workspace-auditor`, `senior-review:api-contract-auditor`, `senior-review:chicken-egg-detector`, `senior-review:cleanup-auditor`, `senior-review:code-auditor`, `senior-review:data-integrity-auditor`, `senior-review:distributed-flow-auditor`, `senior-review:logic-integrity-auditor`, `senior-review:premise-auditor`, `senior-review:resource-lifecycle-auditor`, `senior-review:security-auditor`, `senior-review:temporal-resilience-auditor`, `senior-review:ui-race-auditor`, `testing:test-suite-auditor`, `typescript-development:type-safety-auditor`
- A worker writes only what the coordinator assigned to it: its intermediate report and, when its
  task authorizes edits, its assigned files. It never reverts preexisting or foreign changes.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `prepare`: runs in the orchestrating context; produces `artifact:work`.
2. `execute`: runs in the orchestrating context; needs `prepare`; consumes `artifact:work`; produces `artifact:result`.

Role bindings:

- `abstraction-architect:abstraction-architect-agent`: dispatch the installed `abstraction-architect:abstraction-architect-agent` agent by its qualified identity.
- `codebase-map:map-analyst`: dispatch the installed `codebase-map:map-analyst` agent by its qualified identity.
- `codebase-map:semantic-interconnect-mapper`: dispatch the installed `codebase-map:semantic-interconnect-mapper` agent by its qualified identity.
- `platform-engineering:platform-reviewer`: dispatch the installed `platform-engineering:platform-reviewer` agent by its qualified identity.
- `project-protocol:isolated-worker`: dispatch the installed `project-protocol:isolated-worker` agent by its qualified identity.
- `react-development:react-performance-optimizer`: dispatch the installed `react-development:react-performance-optimizer` agent by its qualified identity.
- `repo-hygiene:workspace-auditor`: dispatch the installed `repo-hygiene:workspace-auditor` agent by its qualified identity.
- `senior-review:api-contract-auditor`: dispatch the installed `senior-review:api-contract-auditor` agent by its qualified identity.
- `senior-review:chicken-egg-detector`: dispatch the installed `senior-review:chicken-egg-detector` agent by its qualified identity.
- `senior-review:cleanup-auditor`: dispatch the installed `senior-review:cleanup-auditor` agent by its qualified identity.
- `senior-review:code-auditor`: dispatch the installed `senior-review:code-auditor` agent by its qualified identity.
- `senior-review:data-integrity-auditor`: dispatch the installed `senior-review:data-integrity-auditor` agent by its qualified identity.
- `senior-review:distributed-flow-auditor`: dispatch the installed `senior-review:distributed-flow-auditor` agent by its qualified identity.
- `senior-review:logic-integrity-auditor`: dispatch the installed `senior-review:logic-integrity-auditor` agent by its qualified identity.
- `senior-review:premise-auditor`: dispatch the installed `senior-review:premise-auditor` agent by its qualified identity.
- `senior-review:resource-lifecycle-auditor`: dispatch the installed `senior-review:resource-lifecycle-auditor` agent by its qualified identity.
- `senior-review:security-auditor`: dispatch the installed `senior-review:security-auditor` agent by its qualified identity.
- `senior-review:temporal-resilience-auditor`: dispatch the installed `senior-review:temporal-resilience-auditor` agent by its qualified identity.
- `senior-review:ui-race-auditor`: dispatch the installed `senior-review:ui-race-auditor` agent by its qualified identity.
- `testing:test-suite-auditor`: dispatch the installed `testing:test-suite-auditor` agent by its qualified identity.
- `typescript-development:type-safety-auditor`: dispatch the installed `typescript-development:type-safety-auditor` agent by its qualified identity.
- Method-owned inline workers use only `project-protocol:isolated-worker`. Give each the full task, owned scope, authorization and budget, plus its expected report path. This permission exposes no other registry role.

The phase graph and record schemas ship with this package in
`contracts/review-branch.workflow.toml`.

## Method

# Review the branch

<arguments>

Load the skill `senior-review:review-method` with shape `branch` and run variant
`team-review` on the branch above against its base, or on the current branch; a pull
request runs variant `pr-review`. Preparation goes through
`senior-review:review-preparation`, which computes the roster; nothing is dispatched
outside it. The report is read-only; posting comments on a pull request is an
authorization asked when needed.
