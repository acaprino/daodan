---
name: delivery-method
description: >
  Coordinate analysis, debugging, features and complete documentation through grounded specifications, adversarial plans, verified commits and authorized merge.
  TRIGGER WHEN: the user wants to investigate or debug a problem, build or refactor code, produce complete project documentation, define specifications or implementation plans, resume work, or finish and merge a delivery.
  DO NOT TRIGGER WHEN: diagnosing project health without implementing (use project-lifecycle:assess-method), requesting code explanation, or requesting one isolated specialist audit without delivery coordination.
---

<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

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

# Project delivery

Load `work-controller:work-record` for records, snapshots, verification and recovery.
Coordinate authorized outcomes within scope; reuse detection owners.

## Load map

Read each step's units at its start.

| Operation or step | Read |
|---|---|
| first use | `references/first-use.md` |
| initialization or missing ADR/FRD | `references/init.md`; `project-delivery:project-bootstrap` |
| change, phase 1 | `references/preflight.md`, `references/context-cycle.md` |
| change, phases 2 and 3 | `references/interview.md` |
| change, phases 4 and 5 | `references/waves.md`, then `references/worker-brief.md` before each dispatch |
| change, overview | `references/change.md` |
| investigate, debug | `references/investigate.md` |
| complete documentation | `references/document.md` |
| repair, refactor | `references/repair.md`, `references/refactor.md`, then the change phases they name |
| continue a task | `references/continue.md` |
| status | `references/status.md` |
| verify | `references/verify.md` |
| brainstorm | `references/brainstorm.md` |
| finish, phase 7 | `references/finish.md`, then `references/realign.md` |
| sync | `references/sync.md`, then `references/realign.md` |
| consolidate | `references/realign.md`; a run's output, `references/retention.md` |
| a requested HTML view | the project-run view of `report-rendering:report-renderer` |

## Run record

Inputs: operation, root, objective and source; optional target, run and evidence.
Initialize through the protocol helper. Resume the agenda's branch task with
current authorizations and this session. Preview is the default; `fix` and
`commit` grants are recorded separately, never push or permanent deletion.
Without `docs/adr/README.md`, the run's `intent.md` replaces records.

New execution runs set `process_required: true`; read Work Controller's
`references/process-runtime.md` to admit approved YAML and bind worker outputs
before dispatch. Legacy runs retain their recorded method. Graph, native ledger
and domain reviews must succeed; commits remain in the reviewed workflow.

## Canonical methods

Load owners by name, never by path.

| Need | Load or dispatch |
|---|---|
| Static context, packets, run binding | `codebase-map:map-method`; dispatch isolated `codebase-map:map-analyst` for analysis |
| Scientific grounding before substantive decisions | Load `research:science-based-approach`, automatic checkpoint entry; reuse the caller run and grants |
| Decisions and record lifecycle | `project-delivery:adr-method` |
| Root-cause investigation | `senior-review:investigation-method` |
| Any review, `light` or `branch` | `senior-review:review-method`; `branch` through `senior-review:review-preparation` |
| Application subtraction | `senior-review:application-cleanup-method` |
| Suite preparation and remediation | `testing:test-preparation`, `testing:test-remediation-method` |
| Test authoring | dispatch `testing:test-writer` |
| Behavior-preserving readability | `clean-code:readability-method` |
| Structural diagnosis | `abstraction-architect:abstraction-architect` and its auditor |
| Durable instructions, guides, README | `project-knowledge:instructions-method`, `project-knowledge:project-knowledge`, `project-knowledge:readme-craft` |
| Workspace detection and reversible operations | `repo-hygiene:repo-hygiene` |
| Task workspaces and catalog | `worktree-manager:worktree-method` |
| Requested model challenge | `peer-review:cross-model-peer-review`, dispatching `peer-review:packet-builder` and `peer-review:respondent`; questions use `moe:multi-model-deliberation` |

For a Codebase Map, execute the analyze entry's preflight, checkpoints,
delivery check and publication decision here and dispatch the analyst for the
phases; loading a role as a skill runs nothing. Never start a command from
inside another.

The worktree method owns workspace creation/resumption and catalog annotations;
Work Controller owns agenda and grants. Status and brainstorming create no
worktree. Missing Worktrunk blocks dependent operations with its recovery path.

## Delivery and closure

Keep native reports, hashes, scope, status, evidence and gaps. Missing/failed
deliveries stay visible. Deduplicate by behavior, retain contradictions and
count shared-premise reviewers as one observation.

For an HTML view, requested or useful for navigation, the coordinator must
load skill `report-rendering:report-renderer` and read `references/project-run-view.md`
before closing; workers keep native deliveries.

Use the protocol envelope for `result.json`, referencing each native report.
Validate before claiming completion; validation alone is no reading evidence.
Report inventory, reading and runtime coverage separately, each check's exact
candidate, decisions, changes, limits and next actions. Source inspection proves
no runtime coverage; self-generated tests prove no correctness; quarantine moves
prove no recovered disk space.
