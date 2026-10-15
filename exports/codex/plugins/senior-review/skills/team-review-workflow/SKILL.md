---
name: team-review-workflow
description: 'Six-phase pipeline. Builds Codebase Map and interconnect context first, then runs specialized dimensions in parallel so cross-component logic bugs surface, not just local ones. TRIGGER WHEN: the user wants a multi-reviewer review of a whole codebase or a large change, or asks for the deepest review available.'
---

> Arguments: `<target> [--reviewers auto|security,performance,react,typescript,platform,...] [--base-branch main] [--all] [--deep] [--no-context] [--fast] [--rigorous]`. Wherever `<arguments>` appears below, substitute the text the user typed after the skill name.

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

# team-review

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
- Dispatch only roles from this set, as the phase graph or loaded method requires: `abstraction-architect:abstraction-architect-agent`, `api-contract-auditor`, `chicken-egg-detector`, `cleanup-auditor`, `code-auditor`, `codebase-map:map-analyst`, `codebase-map:semantic-interconnect-mapper`, `data-integrity-auditor`, `distributed-flow-auditor`, `logic-integrity-auditor`, `platform-engineering:platform-reviewer`, `premise-auditor`, `project-protocol:isolated-worker`, `react-development:react-performance-optimizer`, `repo-hygiene:workspace-auditor`, `resource-lifecycle-auditor`, `security-auditor`, `temporal-resilience-auditor`, `testing:test-suite-auditor`, `typescript-development:type-safety-auditor`, `ui-race-auditor`
- A worker writes only what the coordinator assigned to it: its intermediate report and, when its
  task authorizes edits, its assigned files. It never reverts preexisting or foreign changes.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `scope`: runs in the orchestrating context; produces `artifact:review-brief`.
2. `context-building`: runs in the orchestrating context; needs `scope`; consumes `artifact:review-brief`; produces `artifact:context-map`.
3. `dimension-detection`: runs in the orchestrating context; needs `context-building`; consumes `artifact:context-map`; produces `selection:reviewers`.
4. `independent-review`: one worker per item of `selection:reviewers`, each bound to the role the selection names (any role this plugin declares), each in its own isolated context, in parallel where the host allows; barrier `all-delivered`; needs `dimension-detection`; consumes `artifact:review-brief`, `artifact:context-map`; produces `artifact:reviewer-result`.
5. `delivery-accounting`: runs in the orchestrating context; needs `independent-review`; consumes `artifact:reviewer-result`; produces `artifact:delivery-ledger`.
6. `initial-consolidation`: runs in the orchestrating context; needs `delivery-accounting`; consumes `artifact:reviewer-result`, `artifact:delivery-ledger`; produces `artifact:initial-findings`.
7. `cross-examination`: `logic-integrity-auditor` and `premise-auditor`, once each, each in its own isolated context, in parallel where the host allows; barrier `all-delivered`; needs `initial-consolidation`; consumes `artifact:initial-findings`; produces `artifact:cross-examination`.
8. `consolidation`: one `code-auditor` in an isolated context; needs `cross-examination`; consumes `artifact:initial-findings`, `artifact:cross-examination`, `artifact:delivery-ledger`; produces `artifact:final-report`.
9. `report-delivery`: runs in the orchestrating context; needs `consolidation`; consumes `artifact:final-report`.

Role body bindings (load the complete body only for the selected worker):

- `abstraction-architect:abstraction-architect-agent`: read `contracts/dispatch/abstraction-architect/abstraction-architect-agent.md` inside this package and pass its complete role body verbatim.
- `api-contract-auditor`: read `roles/api-contract-auditor.md` inside this package and pass its complete body verbatim.
- `chicken-egg-detector`: read `roles/chicken-egg-detector.md` inside this package and pass its complete body verbatim.
- `cleanup-auditor`: read `roles/cleanup-auditor.md` inside this package and pass its complete body verbatim.
- `code-auditor`: read `roles/code-auditor.md` inside this package and pass its complete body verbatim.
- `codebase-map:map-analyst`: read `contracts/dispatch/codebase-map/map-analyst.md` inside this package and pass its complete role body verbatim.
- `codebase-map:semantic-interconnect-mapper`: read `contracts/dispatch/codebase-map/semantic-interconnect-mapper.md` inside this package and pass its complete role body verbatim.
- `data-integrity-auditor`: read `roles/data-integrity-auditor.md` inside this package and pass its complete body verbatim.
- `distributed-flow-auditor`: read `roles/distributed-flow-auditor.md` inside this package and pass its complete body verbatim.
- `logic-integrity-auditor`: read `roles/logic-integrity-auditor.md` inside this package and pass its complete body verbatim.
- `platform-engineering:platform-reviewer`: read `contracts/dispatch/platform-engineering/platform-reviewer.md` inside this package and pass its complete role body verbatim.
- `premise-auditor`: read `roles/premise-auditor.md` inside this package and pass its complete body verbatim.
- `project-protocol:isolated-worker`: read `contracts/dispatch/project-protocol/isolated-worker.md` inside this package and pass its complete role body verbatim.
- `react-development:react-performance-optimizer`: read `contracts/dispatch/react-development/react-performance-optimizer.md` inside this package and pass its complete role body verbatim.
- `repo-hygiene:workspace-auditor`: read `contracts/dispatch/repo-hygiene/workspace-auditor.md` inside this package and pass its complete role body verbatim.
- `resource-lifecycle-auditor`: read `roles/resource-lifecycle-auditor.md` inside this package and pass its complete body verbatim.
- `security-auditor`: read `roles/security-auditor.md` inside this package and pass its complete body verbatim.
- `api-contract-auditor`: read `roles/api-contract-auditor.md` inside this package and pass its complete body verbatim.
- `chicken-egg-detector`: read `roles/chicken-egg-detector.md` inside this package and pass its complete body verbatim.
- `cleanup-auditor`: read `roles/cleanup-auditor.md` inside this package and pass its complete body verbatim.
- `code-auditor`: read `roles/code-auditor.md` inside this package and pass its complete body verbatim.
- `data-integrity-auditor`: read `roles/data-integrity-auditor.md` inside this package and pass its complete body verbatim.
- `distributed-flow-auditor`: read `roles/distributed-flow-auditor.md` inside this package and pass its complete body verbatim.
- `logic-integrity-auditor`: read `roles/logic-integrity-auditor.md` inside this package and pass its complete body verbatim.
- `premise-auditor`: read `roles/premise-auditor.md` inside this package and pass its complete body verbatim.
- `resource-lifecycle-auditor`: read `roles/resource-lifecycle-auditor.md` inside this package and pass its complete body verbatim.
- `security-auditor`: read `roles/security-auditor.md` inside this package and pass its complete body verbatim.
- `temporal-resilience-auditor`: read `roles/temporal-resilience-auditor.md` inside this package and pass its complete body verbatim.
- `ui-race-auditor`: read `roles/ui-race-auditor.md` inside this package and pass its complete body verbatim.
- `temporal-resilience-auditor`: read `roles/temporal-resilience-auditor.md` inside this package and pass its complete body verbatim.
- `testing:test-suite-auditor`: read `contracts/dispatch/testing/test-suite-auditor.md` inside this package and pass its complete role body verbatim.
- `typescript-development:type-safety-auditor`: read `contracts/dispatch/typescript-development/type-safety-auditor.md` inside this package and pass its complete role body verbatim.
- `ui-race-auditor`: read `roles/ui-race-auditor.md` inside this package and pass its complete body verbatim.
- Method-owned inline workers use only `project-protocol:isolated-worker`. Give each the full task, owned scope, authorization and budget, plus its expected report path. This permission exposes no other registry role.

The phase graph and record-schema references ship under `contracts/team-review.workflow.toml`.

## Method

# /senior-review:team-review

Load the `senior-review:review-method` skill and run variant `team-review` with `<arguments>`.
Resolve this entry's existing target and flags through `senior-review:review-preparation`.
The method owns dispatch, delivery accounting, consolidation and reporting. Keep the
seven native review contracts; operational records use `project-protocol` envelopes.

The same review selects React performance, TypeScript type safety and platform
integration when the target warrants them, alongside testing, structural entropy
and workspace hygiene. Record selected dimensions, skip reasons and coverage gaps
in one review plan and report.
