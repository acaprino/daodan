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

# README layout techniques

Choose only sections that serve the planned readers and project. Preserve the
author's intentional voice. Structure is a reader decision, not a line quota or
adoption-funnel requirement.

## Entry and purpose

Name the project, explain the concrete problem and who uses it. A plain text
introduction is sufficient. Use an existing logo or screenshot only if it helps
show verified behavior; do not create placeholder visuals. Dark/light `<picture>`
variants are useful when existing assets need them.

Link to relevant project documentation rather than duplicate a long reference.
Clarify scope and limitations before making unsupported claims of maturity,
speed, compatibility or popularity.

## Getting started

Use the project's actual installation and distribution mechanism. A CLI, library,
private application and source-only tool need different instructions. Preserve
prerequisites, environment setup, expected outcomes and safety-relevant steps.
Do not shorten a real setup to satisfy an invented time limit.

Provide complete commands that follow the configured scripts and package manager.
Say when the commands have not been exercised. Code blocks contain usable input,
without shell prompt prefixes or ellipses that hide required steps.

## Features and reference

Explain user-visible capabilities with examples, and use tables for command/API
mappings or comparisons. Put advanced configuration in linked documents or
collapsible sections when the project's renderer and readers support them.
Preserve useful detail rather than impose a fixed README length.

Architecture diagrams are optional. When useful, use actual modules and flows,
with source evidence and the repository's supported diagram format. A diagram
does not imply runtime coverage.

## Metadata and community

License, author, package name and repository links come from verified project
metadata. Badges are optional; their URLs must name the real repository/package
and their metric must mean what the prose claims. Do not invent download counts,
test coverage, stars, endorsements or user quotations.

Link existing CONTRIBUTING, issue tracker, community or sponsor pages only when
relevant and supported by the supplied project information. Optional missing
assets or links can be omitted without another questionnaire.

## Delivery

For an existing README, apply accepted findings to the authorized scope. Full
restructure is a distinct scope from fact maintenance. Preserve content and
intentional voice, validate relative links and report unexercised examples or
external URLs. Operational status belongs in the owned run, not in README.
