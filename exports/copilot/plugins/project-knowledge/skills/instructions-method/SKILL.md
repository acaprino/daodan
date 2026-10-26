---
name: instructions-method
description: >
  Create, audit and maintain durable project instructions in AGENTS.md, CLAUDE.md or the target host's instruction file.
  TRIGGER WHEN: auditing, creating or updating AGENTS.md, CLAUDE.md or durable project instruction files.
---

> `${PLUGIN_ROOT}` is this plugin's install directory, the one that holds its `plugin.json`. If the host has not expanded it, resolve it from where this file was loaded.

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

# Durable instructions method

Load the skill `work-controller:work-record` for run records and gates.
Receive project root, worktree/snapshot, scope, requested instruction destinations,
mode, existing files, evidence paths and authorizations. Reuse the caller's run.

## Destination and authority

Read `references/instruction-loading.md` during preparation. Bind the actual
host/version, configured discovery and applicable root/nested scopes; a file's
presence does not prove it is loaded or enforceable. Record evidence and unknowns
in the owned run rather than assuming every host reads the same files.

Use explicit user destinations first, then the project's existing authoritative
instruction file and documented synchronization rule. For a new project, use the
mechanism confirmed for the active host/configuration (for example AGENTS.md for
Codex, CLAUDE.md for Claude, or configured rules). If the binding is unknown, present concrete
destinations before writing; do not invent a universal filename. Multiple hosts
may use generated or thin-pointer copies only under an explicit project rule.
Never maintain two independent contradictory instruction sets. Honor nested
scopes and do not rewrite a generated instruction copy directly.

## Preparation

Read manifests, source structure, entry points, configured commands and CI before
checking claims. Map evergreen categories and ownership rather than every file.
Read approved requirements/decisions separately from implementation. A supplied
Codebase Map is consumed through `codebase-map:map-method`, bound to its exact run and
snapshot, preserving unknown/disputed claims and inherited premise provenance.
For test guidance, derive the policy from this project's configured commands,
services, conventions and approved behavior. Check its completeness with
`references/test-suite-rules.md`; do not turn a template into project authority.

## Audit and create

Dispatch `instructions-auditor` with explicit audit-only or create mode and the
inputs above. Audit-only returns findings to the owned run, without editing any
durable file. Use its claim/reference/duplication checks; do not add another
detector prompt to the caller. Creation uses a planned destination and verified
facts, not invented project policy.

Read `references/working-principles.md` when a new project needs working guidance
and `references/test-suite-rules.md` when tests exist or are planned. Existing
equivalent rules remain valid; missing canonical wording alone is not a defect.
Read `references/output-economy.md` when creating or maintaining context/output
guidance or instructions for projects that author agent components or tools.
Keep the always-loaded rule short and preserve required reading,
independent verification and domain report contracts.
`references/instruction-example.md` illustrates structure, not current package
versions or requirements for the target project.

## Apply and verify

Audit is the default. With authorized fix/commit, reuse the same claim report and
read `${PLUGIN_ROOT}/skills/project-knowledge/references/apply-method.md`.
Preserve unverified claims without inventing
support; distinguish them from disproved claims. Resolve uncertain intent before
changing an obligation. Extract repeated detail to existing docs with a working
pointer when authorized; keep the primary entry point coherent. Recheck paths,
commands, instruction scope and generated-copy parity before recording completion.
Apply the project's synchronization rule from its canonical owner. Distinguish
verified generated parity from instruction activation: use a supported reload or
new session when required, or record the unperformed loading check and its effect
on the active run. Never claim a textual obligation is mechanically enforced
without evidence of the actual guard in the relevant environment.
Run status, task lists, temporary paths and one-run results stay in the operational
record, never in durable instructions.

## Loop block

A project driven by the lifecycle loop carries one bounded block in its
authoritative instruction file, between `<!-- LOOP-HARNESS:BEGIN -->` and
`<!-- LOOP-HARNESS:END -->`. The block holds only what every task needs at
its start: the verified test, lint, type and build commands with their
prerequisites; on a project that keeps decision records, the active ones per
domain, by identity and title, supplied by the caller as resolved active decision inputs; the
workspace convention (worktree root, branch naming); and the sentence that the
loop's run records live under `.daodan/runs/`. Reasons stay in the records,
procedures stay in the loaded methods, and run state never enters the block.

Create the block at project initialization when creation is authorized;
otherwise report it as a planned change. At the close of a task, regenerate
the block from the run record and, when the project keeps decision records, the
record index, and touch nothing outside
the markers. A missing marker pair in an existing file is a finding, not a
reason to append a second block. Generated copies follow the project's
synchronization rule as for any other instruction change.

## Coordinator delivery

For requested HTML or useful comparison/navigation, the coordinator reads
`${PLUGIN_ROOT}/skills/project-knowledge/references/human-view.md` before
closing the run. Instructions-auditor deliveries stay native.
