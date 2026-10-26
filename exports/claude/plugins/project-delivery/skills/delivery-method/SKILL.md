---
name: delivery-method
description: >
  Coordinate analysis, debugging, features and complete documentation through grounded specifications, adversarial plans, verified commits and authorized merge.
  TRIGGER WHEN: the user wants to brainstorm or design a project, define specifications or implementation plans, investigate or debug, build or refactor code, produce project documentation, resume work, or finish a delivery. Route design conversations to the owned brainstorm without requiring an explicit command.
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

Load `work-controller:work-record`; follow its grants, snapshots, delivery and
recovery contracts. Own design-to-delivery; compose methods, never competing workflows.

## Load map

Load by step:

- First use: `references/first-use.md`.
- Initialization/ADR/FRD bootstrap: `references/init.md`; `project-delivery:project-bootstrap`.
- Change overview: `references/change.md`.
- Preflight: `references/preflight.md`, `references/context-cycle.md`.
- Interview/specification: `references/interview.md`.
- Plan/execution: `references/waves.md`; dispatch: `references/worker-brief.md`.
- Specifications/approval/handoff: `references/specification.md`.
- Brainstorm: `references/brainstorm.md`.
- Load skills: `references/investigate.md`.
- Documentation: `references/document.md`.
- Repair/refactor: `references/repair.md`, `references/refactor.md`.
- Resume/status: `references/continue.md`, `references/status.md`.
- Verification: `references/verify.md`.
- Integration: `references/finish.md`, `references/realign.md`.
- Sync: `references/sync.md`, `references/realign.md`.
- Consolidation: `references/realign.md`, `references/retention.md`.

## Run record

Initialize operation, root, objective, source and scope.
Resume with current grants and session; preview is default. Specifications live
in `docs/specs/`; `intent.md` binds approval. ADRs retain separate technical decisions.

New execution runs set `process_required: true`; follow work-record's
`references/process-runtime.md` to admit approved YAML and bind workers before
dispatch. Preserve legacy unbound runs. Process, delivery and domain gates all
apply; commits stay in the reviewed domain workflow.

## Canonical methods

Load owners by name:

- Maps: `codebase-map:map-method`; dispatch isolated `codebase-map:map-analyst`.
  Own analyze preflight, checkpoints, delivery and publication; loading is not dispatch.
- Load skills: `project-delivery:adr-method`.
- Load skills: `senior-review:investigation-method`.
- Load skills: `senior-review:review-method`; branches: `senior-review:review-preparation`.
- Load skills: `senior-review:application-cleanup-method`.
- Tests: `testing:test-preparation`, `testing:test-remediation-method`; dispatch `testing:test-writer`.
- Load skills: `clean-code:readability-method`.
- Load skills: `abstraction-architect:abstraction-architect` and its auditor.
- Load skills: `project-knowledge:instructions-method`, `project-knowledge:project-knowledge`, `project-knowledge:readme-craft`.
- Load skills: `repo-hygiene:repo-hygiene`.
- Requested challenge: `peer-review:cross-model-peer-review`; dispatch `peer-review:packet-builder`,
  `peer-review:respondent`. Requested opinion: `moe:multi-model-deliberation`.
- Load skills: `report-rendering:report-renderer`, then `references/project-run-view.md`.

## Delivery and closure

Validate the protocol's `result.json`, retaining native reports, hashes, gaps
and contradictory/shared-premise findings. Missing deliveries block completion.
Report inventory, reading and runtime separately, exact candidates and limits.
Static checks prove no runtime execution; self-checks no independent correctness;
quarantine moves no recovered disk space.
