---
description: 'Diagnose the projects debt without changing it: structure, duplicated concepts, dead code, tests, documentation and instructions, workspace, and each stacks own audit (Python, React, TypeScript, platform, dependencies). Produces a plan of actions with owners and gates. TRIGGER WHEN: the user asks how healthy a project is, what its technical debt is, or what to clean up first. DO NOT TRIGGER WHEN: one change is to be reviewed (use review-changes or review-branch).'
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

# check-health

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
- Dispatch only roles from this set, as the phase graph or loaded method requires: `abstraction-architect:abstraction-architect-agent`, `codebase-map:map-analyst`, `platform-engineering:platform-reviewer`, `project-knowledge:documentation-engineer`, `project-knowledge:guide-reviewer`, `project-knowledge:instructions-auditor`, `react-development:react-performance-optimizer`, `repo-hygiene:workspace-auditor`, `senior-review:cleanup-auditor`, `testing:test-suite-auditor`, `typescript-development:type-safety-auditor`, `work-controller:isolated-worker`
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
- `codebase-map:map-analyst`: read `contracts/dispatch/codebase-map/map-analyst.md` inside this package and pass its complete role body verbatim.
- `platform-engineering:platform-reviewer`: read `contracts/dispatch/platform-engineering/platform-reviewer.md` inside this package and pass its complete role body verbatim.
- `project-knowledge:documentation-engineer`: read `contracts/dispatch/project-knowledge/documentation-engineer.md` inside this package and pass its complete role body verbatim.
- `project-knowledge:guide-reviewer`: read `contracts/dispatch/project-knowledge/guide-reviewer.md` inside this package and pass its complete role body verbatim.
- `project-knowledge:instructions-auditor`: read `contracts/dispatch/project-knowledge/instructions-auditor.md` inside this package and pass its complete role body verbatim.
- `react-development:react-performance-optimizer`: read `contracts/dispatch/react-development/react-performance-optimizer.md` inside this package and pass its complete role body verbatim.
- `repo-hygiene:workspace-auditor`: read `contracts/dispatch/repo-hygiene/workspace-auditor.md` inside this package and pass its complete role body verbatim.
- `senior-review:cleanup-auditor`: read `contracts/dispatch/senior-review/cleanup-auditor.md` inside this package and pass its complete role body verbatim.
- `testing:test-suite-auditor`: read `contracts/dispatch/testing/test-suite-auditor.md` inside this package and pass its complete role body verbatim.
- `typescript-development:type-safety-auditor`: read `contracts/dispatch/typescript-development/type-safety-auditor.md` inside this package and pass its complete role body verbatim.
- `work-controller:isolated-worker`: read `contracts/dispatch/work-controller/isolated-worker.md` inside this package and pass its complete role body verbatim.
- Method-owned inline workers use only `work-controller:isolated-worker`. Give each the full task, owned scope, authorization and budget, plus its expected report path. This permission exposes no other registry role.

The phase graph and record-schema references are in `contracts/check-health.workflow.toml`.

## Method

# Check the project's health

$ARGUMENTS

Load the skills `project-lifecycle:assess-method` and
`work-controller:work-record`.
Before anything is written, run `run_state.py first-use --project ROOT`; on
`first_use: true`, load `project-delivery:delivery-method` and follow its
`references/first-use.md` first. Run the diagnosis in the assessment method's
`references/assess.md`, with focus `all` on the area named above or
the whole project: knowledge, structure, tests, artifacts and every stack the snapshot
shows. It is read-only. The result is the plan of actions with owner, scope, evidence,
cost and gate, and the command that carries out each one.
