---
name: assess-workflow
description: 'Assess project coherence and produce a scoped evidence-based repair plan. TRIGGER WHEN: the user requests lifecycle assess or its complete project outcome. DO NOT TRIGGER WHEN: a narrower specialist task already covers the requested outcome.'
---

> Arguments: `[target] [--focus=all|knowledge|structure|tests|artifacts] [--depth=quick|standard|deep] [--run-id ID] [--out INTERNAL_ROOT] [--dry-run|--fix|--commit]`. Wherever `<arguments>` appears below, substitute the text the user typed after the skill name.

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

# assess

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
- Dispatch only roles from this set, as the phase graph or loaded method requires: `abstraction-architect:abstraction-architect-agent`, `project-knowledge:documentation-engineer`, `project-knowledge:guide-reviewer`, `project-knowledge:instructions-auditor`, `project-protocol:isolated-worker`, `repo-hygiene:workspace-auditor`, `senior-review:cleanup-auditor`, `testing:test-suite-auditor`
- A worker writes only what the coordinator assigned to it: its intermediate report and, when its
  task authorizes edits, its assigned files. It never reverts preexisting or foreign changes.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `prepare`: runs in the orchestrating context; produces `artifact:work`, `selection:cleanup`, `selection:tests`, `selection:structure`, `selection:instructions`, `selection:workspace`.
2. `audit-cleanup`: one `senior-review:cleanup-auditor` per item of `selection:cleanup`, each in its own isolated context, in parallel where the host allows; barrier `all-delivered`; needs `prepare`; consumes `artifact:work`; produces `artifact:cleanup-report`.
3. `audit-tests`: one `testing:test-suite-auditor` per item of `selection:tests`, each in its own isolated context, in parallel where the host allows; barrier `all-delivered`; needs `prepare`; consumes `artifact:work`; produces `artifact:tests-report`.
4. `audit-structure`: one `abstraction-architect:abstraction-architect-agent` per item of `selection:structure`, each in its own isolated context, in parallel where the host allows; barrier `all-delivered`; needs `prepare`; consumes `artifact:work`; produces `artifact:structure-report`.
5. `audit-instructions`: one `project-knowledge:instructions-auditor` per item of `selection:instructions`, each in its own isolated context, in parallel where the host allows; barrier `all-delivered`; needs `prepare`; consumes `artifact:work`; produces `artifact:instructions-report`.
6. `audit-workspace`: one `repo-hygiene:workspace-auditor` per item of `selection:workspace`, each in its own isolated context, in parallel where the host allows; barrier `all-delivered`; needs `prepare`; consumes `artifact:work`; produces `artifact:workspace-report`.
7. `plan`: runs in the orchestrating context; needs `audit-cleanup`, `audit-tests`, `audit-structure`, `audit-instructions`, `audit-workspace`; consumes `artifact:cleanup-report`, `artifact:tests-report`, `artifact:structure-report`, `artifact:instructions-report`, `artifact:workspace-report`; produces `artifact:plan`, `artifact:result`.

Role body bindings (load the complete body only for the selected worker):

- `abstraction-architect:abstraction-architect-agent`: read `contracts/dispatch/abstraction-architect/abstraction-architect-agent.md` inside this package and pass its complete role body verbatim.
- `project-knowledge:documentation-engineer`: read `contracts/dispatch/project-knowledge/documentation-engineer.md` inside this package and pass its complete role body verbatim.
- `project-knowledge:guide-reviewer`: read `contracts/dispatch/project-knowledge/guide-reviewer.md` inside this package and pass its complete role body verbatim.
- `project-knowledge:instructions-auditor`: read `contracts/dispatch/project-knowledge/instructions-auditor.md` inside this package and pass its complete role body verbatim.
- `project-protocol:isolated-worker`: read `contracts/dispatch/project-protocol/isolated-worker.md` inside this package and pass its complete role body verbatim.
- `repo-hygiene:workspace-auditor`: read `contracts/dispatch/repo-hygiene/workspace-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:cleanup-auditor`: read `contracts/dispatch/senior-review/cleanup-auditor.md` inside this package and pass its complete role body verbatim.
- `testing:test-suite-auditor`: read `contracts/dispatch/testing/test-suite-auditor.md` inside this package and pass its complete role body verbatim.
- Method-owned inline workers use only `project-protocol:isolated-worker`. Give each the full task, owned scope, authorization and budget, plus its expected report path. This permission exposes no other registry role.

The phase graph and record-schema references ship under `contracts/assess.workflow.toml`.

## Method

# Assess

<arguments>

Load the skills project-lifecycle:lifecycle-method and project-protocol:project-protocol.
Perform the assess reference in this coordinator context. Preserve exact run identity,
scope, input snapshots, existing authorization and native specialist boundaries.
Write the common result with coverage, deliveries, checks and unresolved limits.
