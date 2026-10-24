---
description: 'Explain an unfamiliar project to whoever takes it over: purpose, modules, critical flows, setup and tests, evidenced risks, active decisions, real unknowns and a first scoped work plan. Changes nothing in the project. TRIGGER WHEN: the user is new to a project, takes one over, or asks to be walked through it. DO NOT TRIGGER WHEN: the user wants a durable guide written into the repository (use write-docs).'
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

# onboard-project

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
- Dispatch only roles from this set, as the phase graph or loaded method requires: `codebase-map:semantic-interconnect-mapper`, `project-knowledge:codebase-explorer`, `project-knowledge:guide-reviewer`, `project-knowledge:onboarding-writer`
- A worker writes only what the coordinator assigned to it: its intermediate report and, when its
  task authorizes edits, its assigned files. It never reverts preexisting or foreign changes.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `prepare`: runs in the orchestrating context; produces `artifact:handover-request`, `artifact:file-audience-plan`.
2. `explore`: one `project-knowledge:codebase-explorer` in an isolated context; needs `prepare`; consumes `artifact:handover-request`, `artifact:file-audience-plan`; produces `artifact:context-brief`, `selection:contracts`.
3. `map-contracts`: one `codebase-map:semantic-interconnect-mapper` per item of `selection:contracts`, each in its own isolated context, in parallel where the host allows; barrier `all-delivered`; needs `explore`; consumes `artifact:context-brief`; produces `artifact:interconnect-report`.
4. `local-checks`: runs in the orchestrating context; needs `explore`; consumes `artifact:handover-request`, `artifact:context-brief`; produces `artifact:checks-report`.
5. `prepare-dossier`: runs in the orchestrating context; needs `map-contracts`, `local-checks`; consumes `artifact:context-brief`, `artifact:checks-report`; produces `artifact:handover-evidence`.
6. `write-dossier`: one `project-knowledge:onboarding-writer` in an isolated context; needs `prepare-dossier`; consumes `artifact:file-audience-plan`, `artifact:handover-evidence`; produces `artifact:handover-dossier`.
7. `review-dossier`: one `project-knowledge:guide-reviewer` in an isolated context; needs `write-dossier`; consumes `artifact:handover-dossier`, `artifact:context-brief`, `artifact:checks-report`; produces `artifact:guide-review`.
8. `close`: runs in the orchestrating context; needs `review-dossier`; consumes `artifact:handover-dossier`, `artifact:guide-review`, `artifact:checks-report`; produces `artifact:result`.

Role bindings:

- `codebase-map:semantic-interconnect-mapper`: dispatch the installed `codebase-map:semantic-interconnect-mapper` agent by its qualified identity.
- `project-knowledge:codebase-explorer`: dispatch the installed `project-knowledge:codebase-explorer` agent by its qualified identity.
- `project-knowledge:guide-reviewer`: dispatch the installed `project-knowledge:guide-reviewer` agent by its qualified identity.
- `project-knowledge:onboarding-writer`: dispatch the installed `project-knowledge:onboarding-writer` agent by its qualified identity.

The phase graph and the record schemas are in `contracts/onboard-project.workflow.toml`.

## Method

# Onboard onto the project

$ARGUMENTS

Load the skills `project-lifecycle:handover-method` and
`work-controller:work-record` and prepare the consultant dossier of the project or
area named above, or of this project. Depth is standard and no local check runs unless
the user asks for one. Before anything is written, run `run_state.py first-use --project ROOT`; on
`first_use: true`, load `project-lifecycle:lifecycle-method` and follow its
`references/first-use.md` first. What the user's first-use answers create comes before this command and
is not its write. Every write stays in the run; maintenance is never started from
here, the dossier names the next step for the user.
