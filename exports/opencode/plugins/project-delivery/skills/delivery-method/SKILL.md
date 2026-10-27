---
name: delivery-method
description: >
  Coordinate analysis, debugging, features and complete documentation through grounded specifications, adversarial plans, verified commits and authorized merge.
  TRIGGER WHEN: the user wants to brainstorm or design a project, define specifications or implementation plans, investigate or debug, build or refactor code, produce project documentation, resume work, or finish a delivery. Route design conversations to the owned brainstorm without requiring an explicit command.
  DO NOT TRIGGER WHEN: diagnosing project health without implementing (use project-lifecycle:assess-method), requesting code explanation, or requesting one isolated specialist audit without delivery coordination.
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

Load `work-controller:work-record` for grants/snapshots/delivery/recovery.
Own design-to-delivery; compose methods, never competing workflows.

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
- Investigation: `references/investigate.md`.
- Documentation: `references/document.md`.
- Repair/refactor: `references/repair.md`, `references/refactor.md`.
- Resume/status: `references/continue.md`, `references/status.md`.
- Verification: `references/verify.md`.
- Integration: `references/finish.md`, `references/realign.md`.
- Sync: `references/sync.md`, `references/realign.md`.
- Consolidation: `references/realign.md`, `references/retention.md`.

## Run record

Initialize operation/root/objective/source/scope; resume with current grants/session,
preview by default. Specifications live in `docs/specs/`; `intent.md` binds approval.
ADRs stay separate.

New execution runs set `process_required: true`; use work-record's
`references/process-runtime.md` to admit approved YAML and bind workers before
dispatch. Preserve legacy unbound runs; require process/delivery/domain gates and
reviewed commits.

## Canonical methods

- Maps: `codebase-map:map-method`; dispatch isolated `codebase-map:map-analyst`.
  Own analyze preflight/checkpoints/delivery/publication; loading is not dispatch.
- Load skills: `project-delivery:adr-method`.
- Load skills: `research:science-based-approach` before substantive decisions;
  automatic checkpoint in caller run/grants.
- Load skills: `senior-review:investigation-method`.
- Load skills: `senior-review:review-method`; branches: `senior-review:review-preparation`.
- Load skills: `senior-review:application-cleanup-method`.
- Tests: `testing:test-preparation`, `testing:test-remediation-method`; dispatch `testing:test-writer`.
- Load skills: `clean-code:readability-method`.
- Load skills: `abstraction-architect:abstraction-architect` and its auditor.
- Load skills: `project-knowledge:instructions-method`, `project-knowledge:project-knowledge`, `project-knowledge:readme-craft`.
- Load skills: `repo-hygiene:repo-hygiene`.
- Task workspaces/catalog: load skill `worktree-manager:worktree-method`.
- Requested challenge: `peer-review:cross-model-peer-review`; dispatch `peer-review:packet-builder`,
  `peer-review:respondent`. Requested opinion: `moe:multi-model-deliberation`.
- HTML: the coordinator must load skill `report-rendering:report-renderer` and read `references/project-run-view.md` before closure when requested/useful.

Worktree method owns workspaces and catalog annotations; Work Controller owns
agenda/grants. Status and brainstorming create none. Missing Worktrunk blocks
dependent operations with its recovery path.

## Delivery and closure

Validate `result.json`, retaining reports, hashes, gaps and shared-premise
contradictions. Missing deliveries block completion. Separate inventory, reading
and runtime with exact candidates/limits. Static checks are not runtime,
self-checks not independent correctness, quarantine not recovered disk space.
