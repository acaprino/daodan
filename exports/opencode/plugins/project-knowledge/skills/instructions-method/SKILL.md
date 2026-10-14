---
name: instructions-method
description: >
  Create, audit and maintain durable project instructions in AGENTS.md, CLAUDE.md or the target host's established instruction file. Provides an explicit audit-only method.
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/`, `agents/` and `commands/`. The loader substitutes it in every body it registers; in any other file, resolve it once from where that file was loaded.

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

# Durable instructions method

Load `project-protocol:project-protocol` for run records and gates.
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
guidance. Keep the always-loaded rule short and preserve required reading,
independent verification and domain report contracts.
`references/instruction-example.md` illustrates structure, not current package
versions or requirements for the target project.

## Apply and verify

Audit is the default. With authorized fix/commit, reuse the same claim report and
read `<plugin-root>/skills/project-knowledge/references/apply-method.md`.
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
