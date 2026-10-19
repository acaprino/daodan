---
name: lifecycle-method
description: >
  Coordinate complete AI development work across code, tests, project knowledge and artifacts.
  TRIGGER WHEN: running project-lifecycle assess, repair, change, verify or consolidate, or explicitly taking responsibility for project coherence.
  DO NOT TRIGGER WHEN: an isolated specialist audit suffices (use senior-review, codebase-map or testing directly).
---

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

# Project lifecycle

Own the requested outcome and its consequences, in proportion to risk, scope
and authorization. Load `project-protocol:project-protocol` first: it owns run
records, snapshots, verification and recovery. This skill owns decisions and
dispatch, never detection prompts.

## Load map

Read one unit per step, in this skill, when the step starts.

| Operation or step | Read |
|---|---|
| assess, including `--init` | `references/assess.md` |
| change, phase 1 | `references/preflight.md` |
| change, phases 2 and 3 | `references/interview.md` |
| change, phases 4 and 5 | `references/waves.md`, then `references/worker-brief.md` before each dispatch |
| change, overview of all seven phases | `references/change.md` |
| repair | `references/repair.md`, then preflight and waves as it directs |
| verify | `references/verify.md` |
| consolidate | `references/consolidate.md` |
| converting a native report | `references/native-reports.md` |
| a requested HTML view | `references/human-view.md` |

## Run record

Inputs: operation, project root, objective and its source; optional target,
focus, depth, run and plan identities, output root, prior evidence. Initialize
through the protocol helper with operation, objective, scope, authorizations,
budget, phases, plan, deliveries and required gates; the loop sections
(`workspace`, `preflight`, `adr`, `waves`, `rulings`) are added as the phases
produce them, and a draft plan passes `plan-check` before it enters the run.
Resume only an exact run with current authorizations; the latest report of
another session is never a resume target. Preview is the default; `--fix`
authorizes in-scope edits, `--commit` adds commits, neither authorizes a push
or a permanent deletion.

## Canonical methods

Load only what the step needs, by name, never by path into another plugin.

| Need | Load or dispatch |
|---|---|
| Static context, impact packets, exact run binding | `codebase-map:map-method`; dispatch `codebase-map:map-analyst` in an isolated context for an analysis |
| Decisions governing a scope, a proposed record, promotion at merge | `project-knowledge:adr-method` |
| Candidate review at any stage, any target kind, budget `delta` or `full` | `senior-review:review-method`, through `senior-review:review-preparation` |
| Application subtraction | `senior-review:application-cleanup-method` |
| Suite preparation and remediation | `testing:test-preparation`, `testing:test-remediation-method` |
| Test authoring | dispatch `testing:test-writer` |
| Writing Python or TypeScript in a wave | dispatch `python-development:python-engineer` or `typescript-development:typescript-engineer`; other stacks use the isolated worker with the knowledge `skill-catalog:skill-catalog` selects |
| Readability with behavior preserved | `clean-code:readability-method` |
| Structural diagnosis | `abstraction-architect:abstraction-architect` and its auditor |
| Durable instructions, guides, README | `project-knowledge:instructions-method`, `project-knowledge:project-knowledge`, `project-knowledge:readme-craft` |
| Workspace detection and reversible operations | `repo-hygiene:repo-hygiene` |
| Challenge of a proposed record or plan by another model, on request | dispatch `peer-review:packet-builder` and `peer-review:respondent` through `peer-review:cross-model-peer-review` |
| Second opinion on a decision, on request | load the `moe:multi-model-deliberation` skill |

For a Codebase Map, execute the analyze entry's preflight, checkpoints,
delivery check and publication decision here and dispatch the analyst for the
phases; loading a role as a skill runs nothing. Never launch a lifecycle
workflow from inside a lifecycle operation.

## Delivery and closure

Keep every specialist's native report, hashes, scope, status, evidence and
declared gaps. A missing delivery stays missing; a failed worker is not an
empty result. Deduplicate findings by behavior or concept, keep contradictions,
and treat two reviewers with one inherited premise as one observation.

For a requested HTML view, or a final report that benefits from navigation
or comparison, the coordinator reads `references/human-view.md` before
closing the run; workers keep their native deliveries.

`result.json` follows the protocol's envelope and references each native
report. Validate it with the helper before claiming completion; a validated
record is not read evidence. Reports state inventory, read and runtime
coverage separately, the exact candidate of every check, decisions, changes,
remaining limits and next actions. Never claim runtime coverage from source
inspection, correctness from self-generated tests, or disk recovery from a
quarantine move.
