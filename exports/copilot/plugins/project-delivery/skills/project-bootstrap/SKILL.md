---
name: project-bootstrap
description: >
  Draft missing ADR and FRD from verified project evidence without turning legacy behavior or stale documentation into approved requirements.
  TRIGGER WHEN: a project has no ADR or FRD, existing project knowledge must be bootstrapped from code, documentation or Codebase Map, or /daodan:init-project needs initial requirement records.
  DO NOT TRIGGER WHEN: recording one already understood decision (use adr-method), editing an existing FRD (use frd-method), or running the implementation cycle (use delivery-method).
---

<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

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

# Project knowledge bootstrap

Load `work-controller:work-record`, `project-delivery:adr-method` and
`project-delivery:frd-method`. Work in an owned run; generated records are drafts
and no project behavior changes.

## 1. Inventory and evidence

Detect `docs/adr/README.md` and the FRD index. Validate existing records before
using them; missing artifacts are a drafting request, not permission to invent.
Inventory documentation, source, tests and configuration. Use
`codebase-map:map-method` to validate or refresh a current completed map and
maximize structural discovery. If no current completed map exists, search and read
the source directly and record reduced structural coverage. A map is static
evidence, never a correctness verdict.

Classify each input claim as observed, documented or derived. Verify behavioral
documentation against current source and tests before using it. Contradictions
become explicit FRD conflicts or user questions. Unexercised runtime behavior is
a limitation, never a silent pass.

## 2. Draft and reconcile

Extract FRD requirements, entities, relations and exact evidence spans through
`frd-method`. Include only evidenced people, organizations, locations and
relations; uncertainty stays explicit. Draft architectural decisions only when
the evidence supports a real design choice and alternatives. Current behavior is
a candidate explanation, not an approved requirement.

Write Proposed artifacts through the helpers. Preserve source digests and manual
corrections on every later merge. Review contradictions with the user, then run
the relevant document/spec review. Only explicit approval promotes an artifact.
After implementation, reconciliation and verification use the same candidate and
merge gates as every other delivery.
