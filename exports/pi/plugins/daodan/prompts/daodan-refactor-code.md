---
description: 'Restructure code without changing its behavior: characterization tests first, waves with structural oracles, a review of equivalence. Covers readability too. TRIGGER WHEN: the user wants code restructured, simplified, deduplicated, renamed or made more readable with the same behavior. DO NOT TRIGGER WHEN: behavior should change (use new-feature or fix-bug).'
---

<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
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

# refactor-code

<!-- Generated by the Daodan compiler for pi. Edit the kernel, never this file. -->

## Execution harness

Selected topology: **parallel-subagents**, with role delivery by **inline-prompt**, and declared
isolation **required**. Dispatch one worker per entry in the plan below with the `subagent`
tool supplied by the `pi-subagents` package, each in its own context. Role delivery here is
`inline-prompt`: paste that role's Markdown body into the dispatch prompt verbatim, because the
worker must receive the whole role rather than a summary of it.

Pi's core ships no subagent tool. If none is available in this session, the declared isolation
above decides what happens, and the two cases are not interchangeable:

- **`required`**: stop, and tell the user to run `pi install npm:pi-subagents`. Running the phases
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
- Dispatch only roles from this set, as the phase graph or loaded method requires: `abstraction-architect:abstraction-architect-agent`, `clean-code:clean-code-agent`, `codebase-map:map-analyst`, `codebase-map:semantic-interconnect-mapper`, `peer-review:brief-builder`, `peer-review:packet-builder`, `peer-review:respondent`, `platform-engineering:platform-reviewer`, `project-knowledge:codebase-explorer`, `project-knowledge:doc-humanizer`, `project-knowledge:documentation-engineer`, `project-knowledge:flow-writer`, `project-knowledge:guide-reviewer`, `project-knowledge:instructions-auditor`, `project-knowledge:onboarding-writer`, `project-knowledge:ops-writer`, `project-knowledge:overview-writer`, `project-knowledge:tech-writer`, `project-protocol:isolated-worker`, `python-development:python-engineer`, `python-development:python-refactor-agent`, `react-development:react-performance-optimizer`, `repo-hygiene:workspace-auditor`, `senior-review:api-contract-auditor`, `senior-review:chicken-egg-detector`, `senior-review:cleanup-auditor`, `senior-review:code-auditor`, `senior-review:data-integrity-auditor`, `senior-review:distributed-flow-auditor`, `senior-review:logic-integrity-auditor`, `senior-review:premise-auditor`, `senior-review:resource-lifecycle-auditor`, `senior-review:security-auditor`, `senior-review:temporal-resilience-auditor`, `senior-review:ui-race-auditor`, `testing:test-suite-auditor`, `testing:test-writer`, `text-humanizer:text-humanizer`, `typescript-development:type-safety-auditor`, `typescript-development:typescript-engineer`
- A worker writes only what the coordinator assigned to it: its intermediate report and, when its
  task authorizes edits, its assigned files. It never reverts preexisting or foreign changes.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `prepare`: runs in the orchestrating context; produces `artifact:work`.
2. `execute`: runs in the orchestrating context; needs `prepare`; consumes `artifact:work`; produces `artifact:result`.

Role body bindings (load the complete body only for the selected worker):

- `abstraction-architect:abstraction-architect-agent`: read `contracts/dispatch/abstraction-architect/abstraction-architect-agent.md` inside this package and pass its complete role body verbatim.
- `clean-code:clean-code-agent`: read `contracts/dispatch/clean-code/clean-code-agent.md` inside this package and pass its complete role body verbatim.
- `codebase-map:map-analyst`: read `contracts/dispatch/codebase-map/map-analyst.md` inside this package and pass its complete role body verbatim.
- `codebase-map:semantic-interconnect-mapper`: read `contracts/dispatch/codebase-map/semantic-interconnect-mapper.md` inside this package and pass its complete role body verbatim.
- `peer-review:brief-builder`: read `contracts/dispatch/peer-review/brief-builder.md` inside this package and pass its complete role body verbatim.
- `peer-review:packet-builder`: read `contracts/dispatch/peer-review/packet-builder.md` inside this package and pass its complete role body verbatim.
- `peer-review:respondent`: read `contracts/dispatch/peer-review/respondent.md` inside this package and pass its complete role body verbatim.
- `platform-engineering:platform-reviewer`: read `contracts/dispatch/platform-engineering/platform-reviewer.md` inside this package and pass its complete role body verbatim.
- `project-knowledge:codebase-explorer`: read `contracts/dispatch/project-knowledge/codebase-explorer.md` inside this package and pass its complete role body verbatim.
- `project-knowledge:doc-humanizer`: read `contracts/dispatch/project-knowledge/doc-humanizer.md` inside this package and pass its complete role body verbatim.
- `project-knowledge:documentation-engineer`: read `contracts/dispatch/project-knowledge/documentation-engineer.md` inside this package and pass its complete role body verbatim.
- `project-knowledge:flow-writer`: read `contracts/dispatch/project-knowledge/flow-writer.md` inside this package and pass its complete role body verbatim.
- `project-knowledge:guide-reviewer`: read `contracts/dispatch/project-knowledge/guide-reviewer.md` inside this package and pass its complete role body verbatim.
- `project-knowledge:instructions-auditor`: read `contracts/dispatch/project-knowledge/instructions-auditor.md` inside this package and pass its complete role body verbatim.
- `project-knowledge:onboarding-writer`: read `contracts/dispatch/project-knowledge/onboarding-writer.md` inside this package and pass its complete role body verbatim.
- `project-knowledge:ops-writer`: read `contracts/dispatch/project-knowledge/ops-writer.md` inside this package and pass its complete role body verbatim.
- `project-knowledge:overview-writer`: read `contracts/dispatch/project-knowledge/overview-writer.md` inside this package and pass its complete role body verbatim.
- `project-knowledge:tech-writer`: read `contracts/dispatch/project-knowledge/tech-writer.md` inside this package and pass its complete role body verbatim.
- `project-protocol:isolated-worker`: read `contracts/dispatch/project-protocol/isolated-worker.md` inside this package and pass its complete role body verbatim.
- `python-development:python-engineer`: read `contracts/dispatch/python-development/python-engineer.md` inside this package and pass its complete role body verbatim.
- `python-development:python-refactor-agent`: read `contracts/dispatch/python-development/python-refactor-agent.md` inside this package and pass its complete role body verbatim.
- `react-development:react-performance-optimizer`: read `contracts/dispatch/react-development/react-performance-optimizer.md` inside this package and pass its complete role body verbatim.
- `repo-hygiene:workspace-auditor`: read `contracts/dispatch/repo-hygiene/workspace-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:api-contract-auditor`: read `contracts/dispatch/senior-review/api-contract-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:chicken-egg-detector`: read `contracts/dispatch/senior-review/chicken-egg-detector.md` inside this package and pass its complete role body verbatim.
- `senior-review:cleanup-auditor`: read `contracts/dispatch/senior-review/cleanup-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:code-auditor`: read `contracts/dispatch/senior-review/code-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:data-integrity-auditor`: read `contracts/dispatch/senior-review/data-integrity-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:distributed-flow-auditor`: read `contracts/dispatch/senior-review/distributed-flow-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:logic-integrity-auditor`: read `contracts/dispatch/senior-review/logic-integrity-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:premise-auditor`: read `contracts/dispatch/senior-review/premise-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:resource-lifecycle-auditor`: read `contracts/dispatch/senior-review/resource-lifecycle-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:security-auditor`: read `contracts/dispatch/senior-review/security-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:temporal-resilience-auditor`: read `contracts/dispatch/senior-review/temporal-resilience-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:ui-race-auditor`: read `contracts/dispatch/senior-review/ui-race-auditor.md` inside this package and pass its complete role body verbatim.
- `testing:test-suite-auditor`: read `contracts/dispatch/testing/test-suite-auditor.md` inside this package and pass its complete role body verbatim.
- `testing:test-writer`: read `contracts/dispatch/testing/test-writer.md` inside this package and pass its complete role body verbatim.
- `text-humanizer:text-humanizer`: read `contracts/dispatch/text-humanizer/text-humanizer.md` inside this package and pass its complete role body verbatim.
- `typescript-development:type-safety-auditor`: read `contracts/dispatch/typescript-development/type-safety-auditor.md` inside this package and pass its complete role body verbatim.
- `typescript-development:typescript-engineer`: read `contracts/dispatch/typescript-development/typescript-engineer.md` inside this package and pass its complete role body verbatim.
- Method-owned inline workers use only `project-protocol:isolated-worker`. Give each the full task, owned scope, authorization and budget, plus its expected report path. This permission exposes no other registry role.

The phase graph and record-schema references are in `contracts/refactor-code.workflow.toml`.

## Method

# Refactor code

$ARGUMENTS

Load the skills `project-lifecycle:lifecycle-method` and
`project-protocol:project-protocol`. Run operation `change` for the request above as the
lifecycle method's `references/refactor.md` directs: characterization tests before any
refactoring wave, structural oracles, behavior unchanged at every step. Stop only for
the user's answers, the plan approval and the merge authorization; ask each with the
host's question tool, or record it in the run and close the turn listing it. At the end,
propose `/daodan:finish-task`.
