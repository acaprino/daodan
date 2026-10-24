---
description: 'Close the current branchs task: complete review of the branch, merge with your authorization, decision record promoted, map and documentation realigned, worktree removed. TRIGGER WHEN: the user wants a task completed, merged or closed. DO NOT TRIGGER WHEN: the task still has open waves (use continue-task).'
---

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

# finish-task

<!-- Generated by the Daodan compiler for opencode. Edit the kernel, never this file. -->

## Execution harness

Selected topology: **parallel-subagents**, with role delivery by **named-agent**, and declared
isolation **required**.

Dispatch one worker per entry in the plan below with the `subagent` tool. Name the role as the
agent, using the qualified identity in the bindings below, and give it a short `description` and the full
task as `prompt`. Each agent runs in a fresh child session, so isolation is native here.
For a local role the qualified form is `agent: "daodan:<role>"`; external roles
use their owner's prefix from the bindings, never the coordinator's prefix.

Under `parallel-subagents`, dispatch every worker of one phase with `background: true`, then wait
for every completion notice before the phase closes; do not poll. Under `serial-isolated`, dispatch
them one at a time in the foreground.

Every role below is registered as an agent by this package. A `subagent` call that answers with an
unknown agent means the install is broken: stop and report it, never continue with a shorter
report.

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
- Dispatch only roles from this set, as the phase graph or loaded method requires: `abstraction-architect:abstraction-architect-agent`, `abstraction-architect:abstraction-fit-auditor`, `abstraction-architect:concept-ownership-auditor`, `clean-code:clean-code-agent`, `codebase-map:map-analyst`, `codebase-map:semantic-interconnect-mapper`, `peer-review:brief-builder`, `peer-review:packet-builder`, `peer-review:respondent`, `platform-engineering:app-distribution-auditor`, `platform-engineering:browser-compatibility-auditor`, `platform-engineering:desktop-bridge-auditor`, `platform-engineering:native-lifecycle-auditor`, `platform-engineering:offline-lifecycle-auditor`, `platform-engineering:platform-reviewer`, `project-knowledge:codebase-explorer`, `project-knowledge:doc-humanizer`, `project-knowledge:documentation-engineer`, `project-knowledge:flow-writer`, `project-knowledge:guide-reviewer`, `project-knowledge:instructions-auditor`, `project-knowledge:onboarding-writer`, `project-knowledge:ops-writer`, `project-knowledge:overview-writer`, `project-knowledge:tech-writer`, `project-protocol:isolated-worker`, `python-development:python-engineer`, `python-development:python-refactor-agent`, `python-development:python-semantics-auditor`, `react-development:react-bundle-auditor`, `react-development:react-dataflow-auditor`, `react-development:react-effects-auditor`, `react-development:react-performance-optimizer`, `react-development:react-render-cost-auditor`, `repo-hygiene:workspace-auditor`, `senior-review:accessibility-auditor`, `senior-review:accessible-navigation-auditor`, `senior-review:accessible-perception-auditor`, `senior-review:ai-boundary-auditor`, `senior-review:algorithmic-cost-auditor`, `senior-review:api-contract-auditor`, `senior-review:application-reachability-auditor`, `senior-review:artifact-lifecycle-auditor`, `senior-review:asset-delivery-auditor`, `senior-review:audit-trail-auditor`, `senior-review:authorization-auditor`, `senior-review:browser-security-auditor`, `senior-review:cache-consistency-auditor`, `senior-review:callback-authenticity-auditor`, `senior-review:capacity-quota-auditor`, `senior-review:chicken-egg-detector`, `senior-review:cleanup-auditor`, `senior-review:code-auditor`, `senior-review:data-integrity-auditor`, `senior-review:data-representation-auditor`, `senior-review:data-retention-auditor`, `senior-review:dependency-usage-auditor`, `senior-review:distributed-flow-auditor`, `senior-review:environment-binding-auditor`, `senior-review:feature-flag-auditor`, `senior-review:input-validation-auditor`, `senior-review:local-concurrency-auditor`, `senior-review:local-correctness-auditor`, `senior-review:logic-integrity-auditor`, `senior-review:message-delivery-auditor`, `senior-review:observability-auditor`, `senior-review:operability-auditor`, `senior-review:performance-auditor`, `senior-review:premise-auditor`, `senior-review:recovery-auditor`, `senior-review:release-compatibility-auditor`, `senior-review:remote-effect-auditor`, `senior-review:resource-lifecycle-auditor`, `senior-review:runtime-cost-auditor`, `senior-review:schema-coherence-auditor`, `senior-review:secret-exposure-auditor`, `senior-review:security-auditor`, `senior-review:service-health-auditor`, `senior-review:service-resilience-auditor`, `senior-review:session-delegation-auditor`, `senior-review:sql-efficiency-auditor`, `senior-review:temporal-resilience-auditor`, `senior-review:transaction-integrity-auditor`, `senior-review:ui-race-auditor`, `senior-review:untrusted-resource-auditor`, `testing:ai-evaluation-auditor`, `testing:capacity-test-auditor`, `testing:contract-test-auditor`, `testing:journey-protection-auditor`, `testing:test-oracle-auditor`, `testing:test-reliability-auditor`, `testing:test-suite-auditor`, `testing:test-suite-structure-auditor`, `testing:test-writer`, `text-humanizer:text-humanizer`, `typescript-development:type-safety-auditor`, `typescript-development:type-soundness-auditor`, `typescript-development:typed-boundary-auditor`, `typescript-development:typescript-engineer`
- A worker writes only what the coordinator assigned to it: its intermediate report and, when its
  task authorizes edits, its assigned files. It never reverts preexisting or foreign changes.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `prepare`: runs in the orchestrating context; produces `artifact:work`.
2. `execute`: runs in the orchestrating context; needs `prepare`; consumes `artifact:work`; produces `artifact:result`.

Role bindings:

- `abstraction-architect:abstraction-architect-agent`: dispatch the installed `abstraction-architect:abstraction-architect-agent` agent by its qualified identity.
- `abstraction-architect:abstraction-fit-auditor`: dispatch the installed `abstraction-architect:abstraction-fit-auditor` agent by its qualified identity.
- `abstraction-architect:concept-ownership-auditor`: dispatch the installed `abstraction-architect:concept-ownership-auditor` agent by its qualified identity.
- `clean-code:clean-code-agent`: dispatch the installed `clean-code:clean-code-agent` agent by its qualified identity.
- `codebase-map:map-analyst`: dispatch the installed `codebase-map:map-analyst` agent by its qualified identity.
- `codebase-map:semantic-interconnect-mapper`: dispatch the installed `codebase-map:semantic-interconnect-mapper` agent by its qualified identity.
- `peer-review:brief-builder`: dispatch the installed `peer-review:brief-builder` agent by its qualified identity.
- `peer-review:packet-builder`: dispatch the installed `peer-review:packet-builder` agent by its qualified identity.
- `peer-review:respondent`: dispatch the installed `peer-review:respondent` agent by its qualified identity.
- `platform-engineering:app-distribution-auditor`: dispatch the installed `platform-engineering:app-distribution-auditor` agent by its qualified identity.
- `platform-engineering:browser-compatibility-auditor`: dispatch the installed `platform-engineering:browser-compatibility-auditor` agent by its qualified identity.
- `platform-engineering:desktop-bridge-auditor`: dispatch the installed `platform-engineering:desktop-bridge-auditor` agent by its qualified identity.
- `platform-engineering:native-lifecycle-auditor`: dispatch the installed `platform-engineering:native-lifecycle-auditor` agent by its qualified identity.
- `platform-engineering:offline-lifecycle-auditor`: dispatch the installed `platform-engineering:offline-lifecycle-auditor` agent by its qualified identity.
- `platform-engineering:platform-reviewer`: dispatch the installed `platform-engineering:platform-reviewer` agent by its qualified identity.
- `project-knowledge:codebase-explorer`: dispatch the installed `project-knowledge:codebase-explorer` agent by its qualified identity.
- `project-knowledge:doc-humanizer`: dispatch the installed `project-knowledge:doc-humanizer` agent by its qualified identity.
- `project-knowledge:documentation-engineer`: dispatch the installed `project-knowledge:documentation-engineer` agent by its qualified identity.
- `project-knowledge:flow-writer`: dispatch the installed `project-knowledge:flow-writer` agent by its qualified identity.
- `project-knowledge:guide-reviewer`: dispatch the installed `project-knowledge:guide-reviewer` agent by its qualified identity.
- `project-knowledge:instructions-auditor`: dispatch the installed `project-knowledge:instructions-auditor` agent by its qualified identity.
- `project-knowledge:onboarding-writer`: dispatch the installed `project-knowledge:onboarding-writer` agent by its qualified identity.
- `project-knowledge:ops-writer`: dispatch the installed `project-knowledge:ops-writer` agent by its qualified identity.
- `project-knowledge:overview-writer`: dispatch the installed `project-knowledge:overview-writer` agent by its qualified identity.
- `project-knowledge:tech-writer`: dispatch the installed `project-knowledge:tech-writer` agent by its qualified identity.
- `project-protocol:isolated-worker`: dispatch the installed `project-protocol:isolated-worker` agent by its qualified identity.
- `python-development:python-engineer`: dispatch the installed `python-development:python-engineer` agent by its qualified identity.
- `python-development:python-refactor-agent`: dispatch the installed `python-development:python-refactor-agent` agent by its qualified identity.
- `python-development:python-semantics-auditor`: dispatch the installed `python-development:python-semantics-auditor` agent by its qualified identity.
- `react-development:react-bundle-auditor`: dispatch the installed `react-development:react-bundle-auditor` agent by its qualified identity.
- `react-development:react-dataflow-auditor`: dispatch the installed `react-development:react-dataflow-auditor` agent by its qualified identity.
- `react-development:react-effects-auditor`: dispatch the installed `react-development:react-effects-auditor` agent by its qualified identity.
- `react-development:react-performance-optimizer`: dispatch the installed `react-development:react-performance-optimizer` agent by its qualified identity.
- `react-development:react-render-cost-auditor`: dispatch the installed `react-development:react-render-cost-auditor` agent by its qualified identity.
- `repo-hygiene:workspace-auditor`: dispatch the installed `repo-hygiene:workspace-auditor` agent by its qualified identity.
- `senior-review:accessibility-auditor`: dispatch the installed `senior-review:accessibility-auditor` agent by its qualified identity.
- `senior-review:accessible-navigation-auditor`: dispatch the installed `senior-review:accessible-navigation-auditor` agent by its qualified identity.
- `senior-review:accessible-perception-auditor`: dispatch the installed `senior-review:accessible-perception-auditor` agent by its qualified identity.
- `senior-review:ai-boundary-auditor`: dispatch the installed `senior-review:ai-boundary-auditor` agent by its qualified identity.
- `senior-review:algorithmic-cost-auditor`: dispatch the installed `senior-review:algorithmic-cost-auditor` agent by its qualified identity.
- `senior-review:api-contract-auditor`: dispatch the installed `senior-review:api-contract-auditor` agent by its qualified identity.
- `senior-review:application-reachability-auditor`: dispatch the installed `senior-review:application-reachability-auditor` agent by its qualified identity.
- `senior-review:artifact-lifecycle-auditor`: dispatch the installed `senior-review:artifact-lifecycle-auditor` agent by its qualified identity.
- `senior-review:asset-delivery-auditor`: dispatch the installed `senior-review:asset-delivery-auditor` agent by its qualified identity.
- `senior-review:audit-trail-auditor`: dispatch the installed `senior-review:audit-trail-auditor` agent by its qualified identity.
- `senior-review:authorization-auditor`: dispatch the installed `senior-review:authorization-auditor` agent by its qualified identity.
- `senior-review:browser-security-auditor`: dispatch the installed `senior-review:browser-security-auditor` agent by its qualified identity.
- `senior-review:cache-consistency-auditor`: dispatch the installed `senior-review:cache-consistency-auditor` agent by its qualified identity.
- `senior-review:callback-authenticity-auditor`: dispatch the installed `senior-review:callback-authenticity-auditor` agent by its qualified identity.
- `senior-review:capacity-quota-auditor`: dispatch the installed `senior-review:capacity-quota-auditor` agent by its qualified identity.
- `senior-review:chicken-egg-detector`: dispatch the installed `senior-review:chicken-egg-detector` agent by its qualified identity.
- `senior-review:cleanup-auditor`: dispatch the installed `senior-review:cleanup-auditor` agent by its qualified identity.
- `senior-review:code-auditor`: dispatch the installed `senior-review:code-auditor` agent by its qualified identity.
- `senior-review:data-integrity-auditor`: dispatch the installed `senior-review:data-integrity-auditor` agent by its qualified identity.
- `senior-review:data-representation-auditor`: dispatch the installed `senior-review:data-representation-auditor` agent by its qualified identity.
- `senior-review:data-retention-auditor`: dispatch the installed `senior-review:data-retention-auditor` agent by its qualified identity.
- `senior-review:dependency-usage-auditor`: dispatch the installed `senior-review:dependency-usage-auditor` agent by its qualified identity.
- `senior-review:distributed-flow-auditor`: dispatch the installed `senior-review:distributed-flow-auditor` agent by its qualified identity.
- `senior-review:environment-binding-auditor`: dispatch the installed `senior-review:environment-binding-auditor` agent by its qualified identity.
- `senior-review:feature-flag-auditor`: dispatch the installed `senior-review:feature-flag-auditor` agent by its qualified identity.
- `senior-review:input-validation-auditor`: dispatch the installed `senior-review:input-validation-auditor` agent by its qualified identity.
- `senior-review:local-concurrency-auditor`: dispatch the installed `senior-review:local-concurrency-auditor` agent by its qualified identity.
- `senior-review:local-correctness-auditor`: dispatch the installed `senior-review:local-correctness-auditor` agent by its qualified identity.
- `senior-review:logic-integrity-auditor`: dispatch the installed `senior-review:logic-integrity-auditor` agent by its qualified identity.
- `senior-review:message-delivery-auditor`: dispatch the installed `senior-review:message-delivery-auditor` agent by its qualified identity.
- `senior-review:observability-auditor`: dispatch the installed `senior-review:observability-auditor` agent by its qualified identity.
- `senior-review:operability-auditor`: dispatch the installed `senior-review:operability-auditor` agent by its qualified identity.
- `senior-review:performance-auditor`: dispatch the installed `senior-review:performance-auditor` agent by its qualified identity.
- `senior-review:premise-auditor`: dispatch the installed `senior-review:premise-auditor` agent by its qualified identity.
- `senior-review:recovery-auditor`: dispatch the installed `senior-review:recovery-auditor` agent by its qualified identity.
- `senior-review:release-compatibility-auditor`: dispatch the installed `senior-review:release-compatibility-auditor` agent by its qualified identity.
- `senior-review:remote-effect-auditor`: dispatch the installed `senior-review:remote-effect-auditor` agent by its qualified identity.
- `senior-review:resource-lifecycle-auditor`: dispatch the installed `senior-review:resource-lifecycle-auditor` agent by its qualified identity.
- `senior-review:runtime-cost-auditor`: dispatch the installed `senior-review:runtime-cost-auditor` agent by its qualified identity.
- `senior-review:schema-coherence-auditor`: dispatch the installed `senior-review:schema-coherence-auditor` agent by its qualified identity.
- `senior-review:secret-exposure-auditor`: dispatch the installed `senior-review:secret-exposure-auditor` agent by its qualified identity.
- `senior-review:security-auditor`: dispatch the installed `senior-review:security-auditor` agent by its qualified identity.
- `senior-review:service-health-auditor`: dispatch the installed `senior-review:service-health-auditor` agent by its qualified identity.
- `senior-review:service-resilience-auditor`: dispatch the installed `senior-review:service-resilience-auditor` agent by its qualified identity.
- `senior-review:session-delegation-auditor`: dispatch the installed `senior-review:session-delegation-auditor` agent by its qualified identity.
- `senior-review:sql-efficiency-auditor`: dispatch the installed `senior-review:sql-efficiency-auditor` agent by its qualified identity.
- `senior-review:temporal-resilience-auditor`: dispatch the installed `senior-review:temporal-resilience-auditor` agent by its qualified identity.
- `senior-review:transaction-integrity-auditor`: dispatch the installed `senior-review:transaction-integrity-auditor` agent by its qualified identity.
- `senior-review:ui-race-auditor`: dispatch the installed `senior-review:ui-race-auditor` agent by its qualified identity.
- `senior-review:untrusted-resource-auditor`: dispatch the installed `senior-review:untrusted-resource-auditor` agent by its qualified identity.
- `testing:ai-evaluation-auditor`: dispatch the installed `testing:ai-evaluation-auditor` agent by its qualified identity.
- `testing:capacity-test-auditor`: dispatch the installed `testing:capacity-test-auditor` agent by its qualified identity.
- `testing:contract-test-auditor`: dispatch the installed `testing:contract-test-auditor` agent by its qualified identity.
- `testing:journey-protection-auditor`: dispatch the installed `testing:journey-protection-auditor` agent by its qualified identity.
- `testing:test-oracle-auditor`: dispatch the installed `testing:test-oracle-auditor` agent by its qualified identity.
- `testing:test-reliability-auditor`: dispatch the installed `testing:test-reliability-auditor` agent by its qualified identity.
- `testing:test-suite-auditor`: dispatch the installed `testing:test-suite-auditor` agent by its qualified identity.
- `testing:test-suite-structure-auditor`: dispatch the installed `testing:test-suite-structure-auditor` agent by its qualified identity.
- `testing:test-writer`: dispatch the installed `testing:test-writer` agent by its qualified identity.
- `text-humanizer:text-humanizer`: dispatch the installed `text-humanizer:text-humanizer` agent by its qualified identity.
- `typescript-development:type-safety-auditor`: dispatch the installed `typescript-development:type-safety-auditor` agent by its qualified identity.
- `typescript-development:type-soundness-auditor`: dispatch the installed `typescript-development:type-soundness-auditor` agent by its qualified identity.
- `typescript-development:typed-boundary-auditor`: dispatch the installed `typescript-development:typed-boundary-auditor` agent by its qualified identity.
- `typescript-development:typescript-engineer`: dispatch the installed `typescript-development:typescript-engineer` agent by its qualified identity.
- Method-owned inline workers use only `project-protocol:isolated-worker`. Give each the full task, owned scope, authorization and budget, plus its expected report path. This permission exposes no other registry role.

The phase graph and the record schemas are in `contracts/finish-task.workflow.toml`.

## Method

# Finish the task

Load the skills `project-lifecycle:lifecycle-method` and
`project-protocol:project-protocol` and follow the lifecycle method's
`references/finish.md` for the current branch's task. The merge happens only with the
user's authorization, asked once with base, commits and verdict in view. Pushing is a
separate authorization.
