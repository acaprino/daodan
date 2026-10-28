---
name: wordcraft
description: >
  Create, edit, inspect, render and export real editable Word documents through
  the external WordCraft CLI or exposed MCP interface. TRIGGER WHEN: producing
  DOCX from an accepted design, native Word changes or WordCraft rendering/PDF.
  DO NOT TRIGGER WHEN: only a design brief or read-only package inspection is needed.
---

> This package registers lifecycle callbacks through `hooks/hooks.json` when the plugin is enabled. Execution requires the host's hook trust approval and Python 3 on PATH as `python`. The compiler does not approve hooks or modify host settings. Generated registration and subprocess checks do not prove installed-host execution.

<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Claude binding: repository read, file discovery and content search use Read, Glob
and Grep; repository write and repository edit use Write and Edit; shell execution
uses Bash; network fetch uses WebFetch and network search uses WebSearch; a user
question uses AskUserQuestion. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

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
first operation. Office ships this method and the pinned installer of
`office:intake`, not the engine or an MCP server. Discover the executable or
actual exposed MCP tools and inspect their current schema. When none exists,
follow the engine recovery in `office:intake`'s dependency preflight. Do not
invent commands or silently install another writing library.

For bounded `proposal` production under `office:design`'s
`references/art-direction.md`, consume the assigned candidate's unselected DESIGN
payload, editorial working data and native specification. Validate the proposal
with `require_selected=False` and verify exact project/content/design identities
and requested formats; bundles also verify their candidate-specific working PPTX
plan binding. Build only the assigned representative units to separate native
specimens and render their saved bytes. These are proof artifacts, not selected
final deliveries; never fabricate selection or skip source/native checks for the
units in scope.

For `final` production called by `office:docx`, consume its accepted native design report,
source inventory, DOCX content projection and selected `office:design` record.
Explicitly load CONTENT.md/DESIGN.md through `office:content`'s
`references/records.md`, validate them and compare project, content revision and
requested formats. Bundles require the coordinator's finalized actual-PPTX-plan
validation before dependent production. Reuse existing records; local legacy
edits need no fabricated global record. Missing/stale records for a newly planned deliverable block its
production. Return inherited-binding gaps to the coordinator for the canonical
rebind procedure in `office:design`'s `references/records.md`; retain exact
matching checks. The document coordinator builds the file; do not start another designer or workflow. Map the page plan to supported
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

Apply the assigned proposal or selected DESIGN.md through its native style/theme map and
page settings; a separate DOTX is optional except when requested. Keep headings, body text,
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
