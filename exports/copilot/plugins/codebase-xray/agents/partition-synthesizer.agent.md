---
name: partition-synthesizer
description: 'Consolidates per-partition Codebase Map outputs into 01..07.md in the run directory with cross-partition sections and a team-mode final report. TRIGGER WHEN: spawned by /codebase-map:team-analyze in its consolidation phase. DO NOT TRIGGER WHEN: outside that team pipeline. Classic /codebase-map:analyze dispatches isolated codebase-map:map-analyst.'
tools: ['search', 'edit']
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

<!-- Generated by the Daodan compiler for copilot. Edit the kernel, never this file. -->

<!-- Codebase Map shared instruction wrapper. -->

## Compatibility entry

`codebase-xray:partition-synthesizer` is the retained role identity for Codebase Map.

Load `codebase-map:map-method` through the active host's advertised skill
identity and verify its provider. Resolve the references named below relative to
that loaded skill's own installed location. Every installed-root marker, nested
Method load and helper path in those references belongs to `codebase-map`, never
to this compatibility package. Follow the provider's host binding when its native
skill identity differs from its logical identity.

## Method loads

| Resource | Sections | When |
|---|---|---|
| `codebase-map:map-method` | all | always |
| `references/role-partition-synthesizer.md` inside the loaded `codebase-map:map-method` skill | all | always |

Before executing the shared worker, require the coordinator to have completed
root migration. For supplied analysis-root bindings (run, partition, output or
`xray_path`), use the loaded provider's `migrate_root.py resolve` command from
`references/migration.md` and pass the resolved paths to the shared worker.
Preserve each run ID, suffix and ownership. If resolution still selects
`.codebase-xray`, stop for coordinator migration. This worker performs no root
migration and never writes the legacy store. Forward other inputs unchanged.

Read the complete shared instruction resource and its nested Method loads, then
execute it in this same worker context. Preserve flags, run identity and current manifest; translate only the
analysis-root path bindings as required above. Preserve authorization, tool permissions, ownership and delivery accounting.
This wrapper owns registration metadata; the shared resource contains behavior only.
Loading it does not start another context. Do not dispatch another worker to execute this shared resource. Never load
a registered role as a skill. The canonical method is the skill being loaded.
