---
name: worktrees-workflow
description: 'List all project worktrees, add concise descriptions and tags, create or resume a task workspace, and check Worktrunk upstream compatibility. TRIGGER WHEN: the user asks to list, describe, tag or manage task worktrees, or update the Worktrunk engine. DO NOT TRIGGER WHEN: starting a feature or finishing a task; those entries compose the same workspace method within their existing delivery cycle.'
---

> Arguments: `[request]`. Wherever `<arguments>` appears below, substitute the text the user typed after the skill name.

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

# worktrees

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
- Dispatch only roles from this set, as the phase graph or loaded method requires: `abstraction-architect:abstraction-architect-agent`, `abstraction-architect:abstraction-fit-auditor`, `abstraction-architect:concept-ownership-auditor`, `clean-code:clean-code-agent`, `codebase-map:map-analyst`, `codebase-map:semantic-interconnect-mapper`, `peer-review:brief-builder`, `peer-review:packet-builder`, `peer-review:respondent`, `platform-engineering:app-distribution-auditor`, `platform-engineering:browser-compatibility-auditor`, `platform-engineering:desktop-bridge-auditor`, `platform-engineering:native-lifecycle-auditor`, `platform-engineering:offline-lifecycle-auditor`, `platform-engineering:platform-reviewer`, `project-knowledge:codebase-explorer`, `project-knowledge:doc-humanizer`, `project-knowledge:documentation-engineer`, `project-knowledge:flow-writer`, `project-knowledge:guide-reviewer`, `project-knowledge:instructions-auditor`, `project-knowledge:onboarding-writer`, `project-knowledge:ops-writer`, `project-knowledge:overview-writer`, `project-knowledge:tech-writer`, `python-development:python-engineer`, `python-development:python-refactor-agent`, `python-development:python-semantics-auditor`, `react-development:react-bundle-auditor`, `react-development:react-dataflow-auditor`, `react-development:react-effects-auditor`, `react-development:react-performance-optimizer`, `react-development:react-render-cost-auditor`, `repo-hygiene:workspace-auditor`, `senior-review:accessibility-auditor`, `senior-review:accessible-navigation-auditor`, `senior-review:accessible-perception-auditor`, `senior-review:ai-boundary-auditor`, `senior-review:algorithmic-cost-auditor`, `senior-review:api-contract-auditor`, `senior-review:application-reachability-auditor`, `senior-review:artifact-lifecycle-auditor`, `senior-review:asset-delivery-auditor`, `senior-review:audit-trail-auditor`, `senior-review:authorization-auditor`, `senior-review:browser-security-auditor`, `senior-review:cache-consistency-auditor`, `senior-review:callback-authenticity-auditor`, `senior-review:capacity-quota-auditor`, `senior-review:chicken-egg-detector`, `senior-review:cleanup-auditor`, `senior-review:code-auditor`, `senior-review:data-integrity-auditor`, `senior-review:data-representation-auditor`, `senior-review:data-retention-auditor`, `senior-review:dependency-usage-auditor`, `senior-review:distributed-flow-auditor`, `senior-review:environment-binding-auditor`, `senior-review:feature-flag-auditor`, `senior-review:input-validation-auditor`, `senior-review:local-concurrency-auditor`, `senior-review:local-correctness-auditor`, `senior-review:logic-integrity-auditor`, `senior-review:message-delivery-auditor`, `senior-review:observability-auditor`, `senior-review:operability-auditor`, `senior-review:performance-auditor`, `senior-review:premise-auditor`, `senior-review:recovery-auditor`, `senior-review:release-compatibility-auditor`, `senior-review:remote-effect-auditor`, `senior-review:resource-lifecycle-auditor`, `senior-review:runtime-cost-auditor`, `senior-review:schema-coherence-auditor`, `senior-review:secret-exposure-auditor`, `senior-review:security-auditor`, `senior-review:service-health-auditor`, `senior-review:service-resilience-auditor`, `senior-review:session-delegation-auditor`, `senior-review:sql-efficiency-auditor`, `senior-review:temporal-resilience-auditor`, `senior-review:transaction-integrity-auditor`, `senior-review:ui-race-auditor`, `senior-review:untrusted-resource-auditor`, `testing:ai-evaluation-auditor`, `testing:capacity-test-auditor`, `testing:contract-test-auditor`, `testing:journey-protection-auditor`, `testing:test-oracle-auditor`, `testing:test-reliability-auditor`, `testing:test-suite-auditor`, `testing:test-suite-structure-auditor`, `testing:test-writer`, `text-humanizer:text-humanizer`, `typescript-development:type-safety-auditor`, `typescript-development:type-soundness-auditor`, `typescript-development:typed-boundary-auditor`, `typescript-development:typescript-engineer`, `work-controller:isolated-worker`
- A worker writes only what the coordinator assigned to it: its intermediate report and, when its
  task authorizes edits, its assigned files. It never reverts preexisting or foreign changes.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `execute`: runs in the orchestrating context; produces `artifact:result`.

Role body bindings (load the complete body only for the selected worker):

- `abstraction-architect:abstraction-architect-agent`: read `contracts/dispatch/abstraction-architect/abstraction-architect-agent.md` inside this package and pass its complete role body verbatim.
- `abstraction-architect:abstraction-fit-auditor`: read `contracts/dispatch/abstraction-architect/abstraction-fit-auditor.md` inside this package and pass its complete role body verbatim.
- `abstraction-architect:concept-ownership-auditor`: read `contracts/dispatch/abstraction-architect/concept-ownership-auditor.md` inside this package and pass its complete role body verbatim.
- `clean-code:clean-code-agent`: read `contracts/dispatch/clean-code/clean-code-agent.md` inside this package and pass its complete role body verbatim.
- `codebase-map:map-analyst`: read `contracts/dispatch/codebase-map/map-analyst.md` inside this package and pass its complete role body verbatim.
- `codebase-map:semantic-interconnect-mapper`: read `contracts/dispatch/codebase-map/semantic-interconnect-mapper.md` inside this package and pass its complete role body verbatim.
- `peer-review:brief-builder`: read `contracts/dispatch/peer-review/brief-builder.md` inside this package and pass its complete role body verbatim.
- `peer-review:packet-builder`: read `contracts/dispatch/peer-review/packet-builder.md` inside this package and pass its complete role body verbatim.
- `peer-review:respondent`: read `contracts/dispatch/peer-review/respondent.md` inside this package and pass its complete role body verbatim.
- `platform-engineering:app-distribution-auditor`: read `contracts/dispatch/platform-engineering/app-distribution-auditor.md` inside this package and pass its complete role body verbatim.
- `platform-engineering:browser-compatibility-auditor`: read `contracts/dispatch/platform-engineering/browser-compatibility-auditor.md` inside this package and pass its complete role body verbatim.
- `platform-engineering:desktop-bridge-auditor`: read `contracts/dispatch/platform-engineering/desktop-bridge-auditor.md` inside this package and pass its complete role body verbatim.
- `platform-engineering:native-lifecycle-auditor`: read `contracts/dispatch/platform-engineering/native-lifecycle-auditor.md` inside this package and pass its complete role body verbatim.
- `platform-engineering:offline-lifecycle-auditor`: read `contracts/dispatch/platform-engineering/offline-lifecycle-auditor.md` inside this package and pass its complete role body verbatim.
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
- `python-development:python-engineer`: read `contracts/dispatch/python-development/python-engineer.md` inside this package and pass its complete role body verbatim.
- `python-development:python-refactor-agent`: read `contracts/dispatch/python-development/python-refactor-agent.md` inside this package and pass its complete role body verbatim.
- `python-development:python-semantics-auditor`: read `contracts/dispatch/python-development/python-semantics-auditor.md` inside this package and pass its complete role body verbatim.
- `react-development:react-bundle-auditor`: read `contracts/dispatch/react-development/react-bundle-auditor.md` inside this package and pass its complete role body verbatim.
- `react-development:react-dataflow-auditor`: read `contracts/dispatch/react-development/react-dataflow-auditor.md` inside this package and pass its complete role body verbatim.
- `react-development:react-effects-auditor`: read `contracts/dispatch/react-development/react-effects-auditor.md` inside this package and pass its complete role body verbatim.
- `react-development:react-performance-optimizer`: read `contracts/dispatch/react-development/react-performance-optimizer.md` inside this package and pass its complete role body verbatim.
- `react-development:react-render-cost-auditor`: read `contracts/dispatch/react-development/react-render-cost-auditor.md` inside this package and pass its complete role body verbatim.
- `repo-hygiene:workspace-auditor`: read `contracts/dispatch/repo-hygiene/workspace-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:accessibility-auditor`: read `contracts/dispatch/senior-review/accessibility-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:accessible-navigation-auditor`: read `contracts/dispatch/senior-review/accessible-navigation-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:accessible-perception-auditor`: read `contracts/dispatch/senior-review/accessible-perception-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:ai-boundary-auditor`: read `contracts/dispatch/senior-review/ai-boundary-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:algorithmic-cost-auditor`: read `contracts/dispatch/senior-review/algorithmic-cost-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:api-contract-auditor`: read `contracts/dispatch/senior-review/api-contract-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:application-reachability-auditor`: read `contracts/dispatch/senior-review/application-reachability-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:artifact-lifecycle-auditor`: read `contracts/dispatch/senior-review/artifact-lifecycle-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:asset-delivery-auditor`: read `contracts/dispatch/senior-review/asset-delivery-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:audit-trail-auditor`: read `contracts/dispatch/senior-review/audit-trail-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:authorization-auditor`: read `contracts/dispatch/senior-review/authorization-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:browser-security-auditor`: read `contracts/dispatch/senior-review/browser-security-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:cache-consistency-auditor`: read `contracts/dispatch/senior-review/cache-consistency-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:callback-authenticity-auditor`: read `contracts/dispatch/senior-review/callback-authenticity-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:capacity-quota-auditor`: read `contracts/dispatch/senior-review/capacity-quota-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:chicken-egg-detector`: read `contracts/dispatch/senior-review/chicken-egg-detector.md` inside this package and pass its complete role body verbatim.
- `senior-review:cleanup-auditor`: read `contracts/dispatch/senior-review/cleanup-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:code-auditor`: read `contracts/dispatch/senior-review/code-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:data-integrity-auditor`: read `contracts/dispatch/senior-review/data-integrity-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:data-representation-auditor`: read `contracts/dispatch/senior-review/data-representation-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:data-retention-auditor`: read `contracts/dispatch/senior-review/data-retention-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:dependency-usage-auditor`: read `contracts/dispatch/senior-review/dependency-usage-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:distributed-flow-auditor`: read `contracts/dispatch/senior-review/distributed-flow-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:environment-binding-auditor`: read `contracts/dispatch/senior-review/environment-binding-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:feature-flag-auditor`: read `contracts/dispatch/senior-review/feature-flag-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:input-validation-auditor`: read `contracts/dispatch/senior-review/input-validation-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:local-concurrency-auditor`: read `contracts/dispatch/senior-review/local-concurrency-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:local-correctness-auditor`: read `contracts/dispatch/senior-review/local-correctness-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:logic-integrity-auditor`: read `contracts/dispatch/senior-review/logic-integrity-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:message-delivery-auditor`: read `contracts/dispatch/senior-review/message-delivery-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:observability-auditor`: read `contracts/dispatch/senior-review/observability-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:operability-auditor`: read `contracts/dispatch/senior-review/operability-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:performance-auditor`: read `contracts/dispatch/senior-review/performance-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:premise-auditor`: read `contracts/dispatch/senior-review/premise-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:recovery-auditor`: read `contracts/dispatch/senior-review/recovery-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:release-compatibility-auditor`: read `contracts/dispatch/senior-review/release-compatibility-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:remote-effect-auditor`: read `contracts/dispatch/senior-review/remote-effect-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:resource-lifecycle-auditor`: read `contracts/dispatch/senior-review/resource-lifecycle-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:runtime-cost-auditor`: read `contracts/dispatch/senior-review/runtime-cost-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:schema-coherence-auditor`: read `contracts/dispatch/senior-review/schema-coherence-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:secret-exposure-auditor`: read `contracts/dispatch/senior-review/secret-exposure-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:security-auditor`: read `contracts/dispatch/senior-review/security-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:service-health-auditor`: read `contracts/dispatch/senior-review/service-health-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:service-resilience-auditor`: read `contracts/dispatch/senior-review/service-resilience-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:session-delegation-auditor`: read `contracts/dispatch/senior-review/session-delegation-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:sql-efficiency-auditor`: read `contracts/dispatch/senior-review/sql-efficiency-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:temporal-resilience-auditor`: read `contracts/dispatch/senior-review/temporal-resilience-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:transaction-integrity-auditor`: read `contracts/dispatch/senior-review/transaction-integrity-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:ui-race-auditor`: read `contracts/dispatch/senior-review/ui-race-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:untrusted-resource-auditor`: read `contracts/dispatch/senior-review/untrusted-resource-auditor.md` inside this package and pass its complete role body verbatim.
- `testing:ai-evaluation-auditor`: read `contracts/dispatch/testing/ai-evaluation-auditor.md` inside this package and pass its complete role body verbatim.
- `testing:capacity-test-auditor`: read `contracts/dispatch/testing/capacity-test-auditor.md` inside this package and pass its complete role body verbatim.
- `testing:contract-test-auditor`: read `contracts/dispatch/testing/contract-test-auditor.md` inside this package and pass its complete role body verbatim.
- `testing:journey-protection-auditor`: read `contracts/dispatch/testing/journey-protection-auditor.md` inside this package and pass its complete role body verbatim.
- `testing:test-oracle-auditor`: read `contracts/dispatch/testing/test-oracle-auditor.md` inside this package and pass its complete role body verbatim.
- `testing:test-reliability-auditor`: read `contracts/dispatch/testing/test-reliability-auditor.md` inside this package and pass its complete role body verbatim.
- `testing:test-suite-auditor`: read `contracts/dispatch/testing/test-suite-auditor.md` inside this package and pass its complete role body verbatim.
- `testing:test-suite-structure-auditor`: read `contracts/dispatch/testing/test-suite-structure-auditor.md` inside this package and pass its complete role body verbatim.
- `testing:test-writer`: read `contracts/dispatch/testing/test-writer.md` inside this package and pass its complete role body verbatim.
- `text-humanizer:text-humanizer`: read `contracts/dispatch/text-humanizer/text-humanizer.md` inside this package and pass its complete role body verbatim.
- `typescript-development:type-safety-auditor`: read `contracts/dispatch/typescript-development/type-safety-auditor.md` inside this package and pass its complete role body verbatim.
- `typescript-development:type-soundness-auditor`: read `contracts/dispatch/typescript-development/type-soundness-auditor.md` inside this package and pass its complete role body verbatim.
- `typescript-development:typed-boundary-auditor`: read `contracts/dispatch/typescript-development/typed-boundary-auditor.md` inside this package and pass its complete role body verbatim.
- `typescript-development:typescript-engineer`: read `contracts/dispatch/typescript-development/typescript-engineer.md` inside this package and pass its complete role body verbatim.
- `work-controller:isolated-worker`: read `contracts/dispatch/work-controller/isolated-worker.md` inside this package and pass its complete role body verbatim.
- Method-owned inline workers use only `work-controller:isolated-worker`. Give each the full task, owned scope, authorization and budget, plus its expected report path. This permission exposes no other registry role.

The phase graph and record-schema references ship under `contracts/worktrees.workflow.toml`.

## Method

# Manage worktrees

<arguments>

Load skills `worktree-manager:worktree-method` and `work-controller:work-record`.
Without a specific request, show the read-only inventory, including external and
detached checkouts. Apply requested descriptions and tags to the identified
workspace; ambiguity is resolved before changing an annotation. Creation uses
the task's existing identity, authorization and workspace policy. Final review,
merge and completion load skill `project-delivery:delivery-method`, following
its `references/finish.md`; this entry never bypasses those gates.
Dispatch only the workers that the selected method requires. Inventory and
annotation do not start review workers or a delivery cycle. An explicit finish
request uses this entry's declared isolated worker bindings and the existing
delivery owner, including its review and realignment barriers.
