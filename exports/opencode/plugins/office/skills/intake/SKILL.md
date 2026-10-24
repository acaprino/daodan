---
name: intake
description: >
  Shared contextual interview for every Office workflow: resolve where the work
  starts, how much it changes and what is delivered, then pick the route the
  format method executes. TRIGGER WHEN: an Office presentation, document or
  workbook task begins. DO NOT TRIGGER WHEN: a format method is already executing
  a resolved route.
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

# Office intake

Resolve the task before choosing a format method, engine or worker. This
interview serves every Office format; each format method adds only the questions
that belong to its own format.

## Resolve the starting point

- **Nothing:** a brief, notes, data or sources become a new file.
- **An existing file:** either the base for a new file or the file to revise.
  When it is a base, record what carries over: content, structure, visual
  identity or all of them.

Never overwrite a supplied file. Write every result to a separate candidate path.

## Resolve the depth of change

| Route | Typical requests | What follows |
|---|---|---|
| Substantial | New file, file derived from an existing one, template, restyle, restructure, rewrite, shorten or lengthen | `office:design` decisions (direction, palette from the user's colour source, pairing, argument mode), the format's designer where it declares one, production and rendered review |
| Narrow | A local wording, figure, formatting or added-element change inside the accepted design | Preserve the existing design; no design decisions or designer dispatch |
| Read-only | Read, analyze, review, preview or export | No write to the source; deliver findings or the requested export |

Shortening and restructuring are substantial because they change sequence and
composition. If a narrow change turns out to need a new design decision, raise
it with the user rather than redesigning silently. A read-only request
authorizes no edit.

## Ask once

Inspect supplied files before asking about them. Infer what the request and the
files already settle, then ask the remaining decisions that change the result in
one round, together with the format method's questions. On the substantial
route that round includes the design decisions of `office:design`: the argument
mode, the direction (or the supplied brand or template), and the colour source
for the palette: an image, a website, the project's stylesheets or design
tokens, an existing PPTX or DOCX, a description in words, or none. Palette
candidates are shown and chosen after this round, not asked here. State the
inferred choices instead of asking about them again. A complete or explicitly autonomous
request needs no questions. Ask again only when new evidence changes a decision
materially.

## Record the route

Record in the task brief: starting point, carry-over, route, deliverable (file,
findings or export) and the inferred choices. When an existing file is a base or
is shortened, also record the approved cuts: the source content the user agreed
to drop. Everything else in the source must reach the result. The format method executes that
route. A later request that changes the route re-enters this step.
