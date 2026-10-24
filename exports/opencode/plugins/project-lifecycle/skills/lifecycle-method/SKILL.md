---
name: lifecycle-method
description: >
  Coordinate complete AI development work across code, tests, project knowledge and artifacts.
  TRIGGER WHEN: the user wants to brainstorm or explore an idea before building, initialize or set up a project, diagnose project health or technical debt, build a feature, fix a bug, refactor code, check task status, continue an open task, finish and merge a task, sync upstream, or run a daodan lifecycle command.
  DO NOT TRIGGER WHEN: the user requests code explanation without investigation or changes, wants an isolated specialist audit (use senior-review, codebase-map or testing directly), or only needs a problem investigated without fixing it (use senior-review:investigation-method).
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

# Project lifecycle

Load the `project-protocol:project-protocol` skill for records, snapshots, verification and
recovery. Coordinate authorized outcomes and dispatch within scope; reuse detection
owners.

## Load map

Read each step's units at its start.

| Operation or step | Read |
|---|---|
| initialization | `references/init.md` |
| assess, the diagnosis | `references/assess.md` |
| change, phase 1 | `references/preflight.md`, `references/context-cycle.md` |
| change, phases 2 and 3 | `references/interview.md` |
| change, phases 4 and 5 | `references/waves.md`, then `references/worker-brief.md` before each dispatch |
| change, overview | `references/change.md` |
| repair, refactor | `references/repair.md`, `references/refactor.md`, then the change phases they name |
| continue a task | `references/continue.md` |
| status | `references/status.md` |
| verify | `references/verify.md` |
| brainstorm | `references/brainstorm.md` |
| finish, phase 7 | `references/finish.md`, then `references/realign.md` |
| sync | `references/sync.md`, then `references/realign.md` |
| consolidate | `references/realign.md`; a run's output, `references/retention.md` |
| converting a native report | `references/native-reports.md` |
| a requested HTML view | `references/human-view.md` |

## Run record

Inputs: operation, project root, objective and its source; optional target,
run identity and prior evidence. Initialize
through the protocol helper with operation, objective, scope, authorizations,
budget, phases, plan, deliveries and required gates; the loop sections are
added as the phases produce them, and a draft plan passes `plan-check` before
it enters the run. Resume the branch's task from the agenda with current
authorizations and this session's id; a task another session holds is taken
over only after the user confirms it is closed. Preview is the default; an
authorization is asked when a step needs it and recorded in the run: `fix` for
in-scope edits, `commit` for commits, neither a push or a permanent deletion.

## Canonical methods

Load owners by name, never by path.

| Need | Load or dispatch |
|---|---|
| Static context, impact packets, exact run binding | `codebase-map:map-method`; dispatch `codebase-map:map-analyst` in an isolated context for an analysis |
| Decisions governing a scope, a proposed record, promotion at merge | `project-knowledge:adr-method` |
| Review at any stage and of any kind, shape `light` or `branch` | `senior-review:review-method`; shape `branch` through `senior-review:review-preparation` |
| Application subtraction | `senior-review:application-cleanup-method` |
| Suite preparation and remediation | `testing:test-preparation`, `testing:test-remediation-method` |
| Test authoring | dispatch `testing:test-writer` |
| Readability with behavior preserved | `clean-code:readability-method` |
| Structural diagnosis | `abstraction-architect:abstraction-architect` and its auditor |
| Durable instructions, guides, README | `project-knowledge:instructions-method`, `project-knowledge:project-knowledge`, `project-knowledge:readme-craft` |
| Workspace detection and reversible operations | `repo-hygiene:repo-hygiene` |
| Another model's challenge of a record or plan, on request | `peer-review:cross-model-peer-review`, dispatching `peer-review:packet-builder` and `peer-review:respondent`; a question goes to `moe:multi-model-deliberation` |

For a Codebase Map, execute the analyze entry's preflight, checkpoints,
delivery check and publication decision here and dispatch the analyst for the
phases; loading a role as a skill runs nothing. Never start a command from
inside another.

## Delivery and closure

Keep every specialist's native report, hashes, scope, status, evidence and
declared gaps. A missing delivery stays missing; a failed worker is not an
empty result. Deduplicate findings by behavior or concept, keep contradictions,
and treat two reviewers with one inherited premise as one observation.

For an HTML view, requested or useful for navigation, the coordinator reads
`references/human-view.md` before closing; workers keep native deliveries.

Use the protocol envelope for `result.json`, referencing each native report.
Validate before claiming completion; validation alone is no reading evidence.
Report inventory, reading and runtime coverage separately, each check's exact
candidate, decisions, changes, limits and next actions. Source inspection proves
no runtime coverage; self-generated tests prove no correctness; quarantine moves
prove no recovered disk space.
