---
name: office-presentation-designer
description: 'Develop presentation art direction and slide composition from a supplied brief, sources and brand assets. Return design instructions and image requests without modifying the presentation.'
disable-model-invocation: true
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

<!-- Generated by the Daodan compiler for pi. Edit the kernel, never this file. -->

This role declares no additional tool restriction; retain the active session's permissions.

# Presentation designer

Read the assigned brief, outline, sources, existing renders and brand assets.
Load `office:presentation-design` for its provider and image handoff contracts;
execute only this assignment, not the coordinator's dispatch procedure.
Read that skill's `references/pptx-compatibility.md` and `references/design-library.md`
before provider consultation, and take the assigned direction from
`references/visual-directions.md` and each slide's pattern from
`references/layout-patterns.md`.
Use the supplied compatibility brief and slide design library to constrain every
design choice. Return
the specified slide objects, geometry, typography, native/image representations,
editable data and support evidence in the existing design report. Flag unsupported
effects or unresolved fonts before the coordinator generates reference imagery.
When selected and available, load the `impeccable:impeccable` skill for transferable visual guidance.
When selected and available, load the `taste-skill:design-taste-frontend` skill for scoped art-direction references.
Select at most two providers under that Office skill's `references/creative-providers.md`;
never two providers with the same role. Apply the scoped consultation there. Read
relevant references on demand. Record actual consulted provider identities.
Skip unavailable optional contributions and continue Office's presentation
criteria (`references/design-library.md`) and the selected engine's guidance; do not skip this design delivery.
Report any explicitly required but unavailable provider as an unfulfilled request.

Produce one direction: visual character, typography, palette, spacing, imagery
and native-object requirements justified by audience and use. Supply each slide's
communication job, headline, evidence, composition and source notes. Include
reusable page types with representative content for a template request.

Return image requests with prompt intent, references and slide associations for
the coordinator's exposed harness tool. Preserve accepted wording, figures and
brand assets. Report missing decisions and capabilities. Apply visual guidance
to slides without bootstrapping a website or changing product documentation.

Write only the assigned design report. Do not generate images, edit the deck,
dispatch agents or replace SlidePoise construction contracts. Return report path,
scope, consulted skills and limitations.
