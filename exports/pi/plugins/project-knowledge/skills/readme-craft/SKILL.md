---
name: readme-craft
description: >
  Create or audit README.md from verified project facts, retaining author voice and proportional information architecture.
  TRIGGER WHEN: creating, auditing or updating README.md.
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/` and `prompts/`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

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

# README method

Load `work-controller:work-record` and the project-knowledge method for
run ownership, input preparation and authorized application. Receive the scope,
snapshot, existing README, reader, mode, output path and authorizations.

## Audit-only

Read the README, manifests, license, configured scripts, pertinent entry points,
public interfaces, assets and CI. Apply `references/audit-checklist.md` to every
claim, count, link, badge and command in scope. Compare implemented features with
approved intent rather than making the current code the product requirement.
Report evidence locators, status, preserved voice, wrong claims, structural
recommendations, uncovered surfaces and unavailable checks. Write only the owned
run report. Audit-only does not update README, badges, links, docs or ignore rules.

## Create or maintain

Prefer the existing README and its intentional style. Read
`references/layout-techniques.md` only for relevant structure patterns: a project
may need a plain introduction, install instructions and one working example,
without promotional claims, images, badges or community links. Never invent user
quotes, performance claims, download counts, package names or missing metadata.
Ask for a missing material choice only when needed; optional decoration can be
omitted. Follow the planned file and scope; full restructure requires an authorized
scope that permits it, rather than a new automatic approval ritual.

Use the project's verified scripts and install conventions. Distinguish a copied
command from one actually exercised. Correct accepted findings through the
project-knowledge apply-method, preserving facts, author voice and inbound links.
For a requested prose pass, load `text-humanizer:anti-ai-writing-patterns` and
dispatch `text-humanizer:text-humanizer` in the docs register. Record new or
retained gaps and checks in the same run; do not reproduce a session log in README.

## Coordinator delivery

For requested HTML or useful comparison/navigation, the coordinator reads
`<plugin-root>/skills/project-knowledge/references/human-view.md` before
closing the run.
