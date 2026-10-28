---
name: content
description: >
  Shared editorial method for requested Word documents and PowerPoint decks:
  source and claim ledger, transformation permissions, logical sequence and
  format projections in a validated CONTENT.md. Use after Office intake;
  revisions inherit accepted decisions and local edits change only their scope.
---

> `<plugin-root>` names the directory that holds this plugin's `.codex-plugin/plugin.json`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.
> This package registers lifecycle callbacks through `hooks/hooks.json` when the plugin is enabled. Execution requires the host's hook trust approval and Python 3 on PATH as `python`. The compiler does not approve hooks or modify host settings. Generated registration and subprocess checks do not prove installed-host execution.

<daodan_host_binding host="codex">
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

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. Network search and network fetch
use the runtime's registered web search tool when the Codex configuration enables
it. A user question uses the runtime's registered question tool when one exists;
otherwise ask it in the reply and wait for the answer. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
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

# Office content

Own what the work communicates: intent, goal, audience, market, channel, scope,
depth, extent, density and tone. Take settled decisions from intake. Preserve
source conditions, uncertainty, conflicts and locked wording; report gaps
instead of inventing evidence. Design owns visual identity; each format owns
native composition, production and saved-file review.

1. Read the actual sources and accepted records. Record stable source IDs,
   original-byte SHA-256 values, material roles and precise claim locators.
   Classify claims as core, supporting or optional, with conditions, conflicts
   and locks. Record optional omissions in the format plan.
2. Define each content unit's message, complete text, claims, relationship,
   detail and permitted transformation. Sequence the units for the audience's
   understanding or decision. Use the least transformation that meets the brief;
   keep locked claims in dedicated verbatim units. Trace substantive changes
   per unit to sources, destination and reason.
3. Read only requested format structure references: DOCX uses
   `../docx/references/structure.md`; PPTX uses
   `../pptx/references/structure.md` and its existing `content-planning.md`.
   Write DOCX sections or bind units to the existing PPTX plan's stable slide
   and claim IDs. Share facts and identity without assuming page-slide parity.
4. Follow `references/records.md` to serialize and explicitly load/validate
   `CONTENT.md`. Pass the actual PPTX plan when requested. Every core claim
   reaches each requested format or carries an authorized, sourced exclusion.
   Hand producers the exact record revision and requested projection.
5. Review source fidelity independently of the structural check. Revisions and
   expansions inherit accepted decisions and change the required delta; restyle,
   review and export reuse content. A local edit does not reopen global strategy.

```text
python "<plugin-root>/skills/content/scripts/office_records.py" write CONTENT.json --out CONTENT.md
python "<plugin-root>/skills/content/scripts/office_records.py" validate CONTENT.md
python "<plugin-root>/skills/content/scripts/office_records.py" validate CONTENT.md --pptx-plan plan.json
```

Only the last command verifies supplied plan bindings. Load saved records with
`load_record(Path(...))` before using their contents; a filename alone supplies
no evidence. Increment revision for changed editorial decisions and update all
projection bindings. Preserve accepted artifacts, produce new candidates, and
report missing evidence or capability to the coordinator. Structural success
does not establish source fidelity, editability, rendering or application fidelity.
