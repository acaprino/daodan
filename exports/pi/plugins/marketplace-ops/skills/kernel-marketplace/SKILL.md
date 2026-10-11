---
name: kernel-marketplace
description: >
  Maintain neutral multi-host plugin kernels through their compiler instead of editing generated host packages.
  TRIGGER WHEN: marketplace operations target daodan/v1 kernels or compiler-managed exports.
  DO NOT TRIGGER WHEN: the target is a legacy Claude marketplace with hand-authored native packages.
---

<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

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

# Kernel marketplace operations

Identify the source profile first. Read the target's durable instructions,
plugins/*/plugin.toml and adapter declarations. A daodan/v1 manifest establishes
the neutral profile even though generated catalogs also resemble native packages.

## Source boundary

Hand-authored plugin source: plugin.toml, roles/, workflows/ with MD and TOML
sidecars, skills/, contracts/ and policies/. Adapter mechanisms live in adapters/.
A root references/, scripts/ or mcp/ is not a shipped runtime resource; put helpers
under skills/<name>/ and declare an MCP server in plugin.toml when needed.

Generated exports and root marketplace manifests are output. Never register a
kernel by editing catalog arrays, author a native commands/ copy, or hand-fix
one host's export. Markdown is behavior, TOML declarative metadata.
No name repeats across role, skill and workflow kinds within a kernel.

## Health and review

Use the target compiler's read-only validation/drift command, dependency,
registration, bundled-path, fact-anchor and vocabulary gates. On Daodan the
authoritative command is python scripts/daodan_build.py --check --support, followed
by the required scripts and tests listed in its durable instructions.

A native-package audit can check generated package integrity, but its registration
fixes must be translated back into kernel declarations. Report source defects,
compiler defects and generated drift separately. Review the whole consequence set,
including documentation, evals and unchanged consumers.

## Scaffold and content authoring

1. Choose a kebab-case plugin and distinct role/skill/workflow names.
2. Create plugin.toml with schema daodan/v1, version 1.0.0, identity, closed
   capability requirements, hard dependency declarations and components.
3. Write meaningful behavior under the corresponding source directories. A
   workflow needs an entry body and sidecar with phases, contract and deliverables.
4. Add only needed contracts/policies. Runtime helper files live under a skill.
5. Validate declared components and dependencies, then compile every host.
6. Review the resulting source and package behavior before publishing.

Do not put host tool primitives in neutral behavior. Each adapter supplies its
binding and coordination strategy. Declared roles/schemas must actually resolve.
Do not preserve unused or optional local dependencies to make a compiler pass.

## Version, sync and publication

Bump each changed kernel version and the marketplace version according to the
target's rules. Rebuild all hosts and stage source plus generated results together,
using explicit paths. A rebuild alone is not a plugin source change.

Follow the target's upstream/licensing workflow before import or synchronization.
Verify gates before an authorized push. Read-only review, source changes, commits
and publication are separate scopes; preserve already granted human authorization.
