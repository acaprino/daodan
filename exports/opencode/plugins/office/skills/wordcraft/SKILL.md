---
name: wordcraft
description: >
  Create, edit, inspect, render and export real editable Word documents through
  the external WordCraft CLI or exposed MCP interface. TRIGGER WHEN: producing
  DOCX from an accepted design, native Word changes or WordCraft rendering/PDF.
  DO NOT TRIGGER WHEN: only a design brief or read-only package inspection is needed.
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

# WordCraft document production

Use the external [WordCraft](https://github.com/storytold/wordcraft) engine to
produce the actual DOCX after design. Read `references/runtime.md` before the
first operation. Office ships this method, not the engine, installer or MCP server.
Discover the executable or actual exposed MCP tools and inspect their current
schema. Do not invent commands or silently install another writing library.

When called by `office:docx`, consume its accepted document design report, the
`office:design` record (direction, palette by role, pairing) and source inventory. The document coordinator builds
the file; do not start another designer or workflow. Map the page plan to supported
native paragraphs, styles, lists, sections, tables and images.

## Inspect and preserve

Record executable/version and input identity. For an existing document, use
`office:docx` to inventory preservation-sensitive features before loading it.
Save a no-edit round-trip to a separate candidate and compare packages and actual
renders before substantive edits. WordCraft remains alpha; an opens/saves result
does not demonstrate preservation of every Word feature.

Use documented targeted operations. In the reference version, `layout.pageSetup`
replaces a complete section including header/footer data; do not use a partial
page-setup object as if it were a merge. Prefer supported targeted size/margin
commands or a verified complete section state. Never rebuild an imported file
merely to remove an unsupported feature. Keep the source and earlier candidates.

## Build the physical file

Discover commands, then prepare a bounded job in the owned workspace. Where
supported, use `wordcraft-cli run --script job.json` with explicit new output paths
in `save`. Older versions may require repeated `--cmd` arguments and `--save`;
use their actual help and pass literal JSON as individual process arguments,
without interpolating content into shell syntax.
For edits use its `file` input; for a new document use a supported blank template.
Read current command definitions for parameters and units rather than guessing.
The documented version supports a command list and saving DOCX/PDF in one job.

Apply the accepted native style map and page settings. Keep headings, body text,
captions, list numbering and table cells editable. Insert generated imagery only
after the harness image contract returns a verified usable asset. WordCraft
does not replace the harness image tool or authorize another image service.
Do not rasterize page text to imitate the design wireframe.

Verify that the requested output exists at the actual resolved path and contains
the required content. Reopen it with WordCraft and inspect the saved candidate;
command success alone is insufficient because unknown style fields may be ignored.
Use the DOCX inspector to check native structures and preservation deltas. A
design report, PDF or screenshot does not satisfy an editable DOCX request.

## Render, correct and deliver

Render actual saved DOCX pages through the available WordCraft interface and
inspect the returned page images with an image-reading tool. Use `info` for page
inventory, then render the required pages explicitly; CLI page numbers start at 1
in the reference version. Check page flow, table splits, captions, headers/footers,
clipping and the shared theme. Fix supported defects within the brief, save and
rerender changed pages. Keep inspected/total page coverage visible.

When requested, export PDF and verify its pages. Field-update options request
engine updates; inspect actual results rather than assuming full Microsoft Word
field/layout equivalence. WordCraft rendering is evidence for that engine, not
proof of identical Word desktop pagination or pixel fidelity.

Return the physical editable `.docx`, requested PDF/previews, engine/version,
candidate identity, design report path, preservation evidence and remaining gaps
to the producing coordinator. Missing rendering remains an unverified-layout
limit. Missing runtime blocks dependent production while design/source work can
continue. Physical printing requires a real supported application/printer action;
CLI `--print` prints command results to stdout, not paper.
