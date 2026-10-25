---
name: intake
description: >
  Shared contextual interview for every Office workflow: resolve where the work
  starts, how much it changes and what is delivered, then pick the route the
  format method executes; route a request that names no format to the right
  workflows. TRIGGER WHEN: an Office presentation, document or workbook task
  begins, or an Office request must be routed. DO NOT TRIGGER WHEN: a format
  method is already executing a resolved route.
---

<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
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

# Office intake

Resolve the task before choosing a format method, engine or worker. This
interview serves every Office format; each format method adds only the questions
that belong to its own format. When the request names no single format workflow,
combines deliverables or starts from inputs whose use is unclear, route it first
with `references/routing.md`; `/daodan:start` is the entry that does so.

## Resolve the starting point

- **Nothing:** a brief, notes, data or sources become a new file.
- **An existing file:** either the base for a new file or the file to revise.
  When it is a base, record what carries over: content, structure, visual
  identity or all of them.

Never overwrite a supplied file. Write every result to a separate candidate path.

## Resolve the operation

The operation decides which steps run, what the existing file supplies and what
is asked. Everything the file supplies is inherited and stated back, never asked
again. A request can combine operations (expand and restyle); run the union of
their steps.

| Operation | Typical request | Route | Inherited from the existing file | Asked when the request leaves it open |
|---|---|---|---|---|
| Create | A new file from a brief, notes, data or research | Substantial | Nothing | Planning, structure and design decisions |
| Derive | A new file built from an existing one: another audience, a short version, a deck from a report | Substantial | What the carry-over names: content, structure, look or all | Only what differs: purpose, audience, length; design only when the look is not carried over |
| Expand | Add new content, sections or slides to an existing file | Substantial | Purpose, audience, structure choice, sequence, direction, palette, fonts, template | The new material, how much to add (slides or pages), where it belongs when the request says so |
| Revise | Update figures or claims, restructure, rewrite, shorten | Substantial | Look and theme; structure choice; sequence unless restructured | What changes; target length when shortening; approved cuts |
| Restyle | Same content, a new look | Substantial | All content, sequence and claims | Direction or brand, colour source, fonts |
| Edit | A local wording, figure, formatting or element change | Narrow | Everything | Nothing beyond the change itself |
| Review or export | Read, analyze, review, preview, export | Read-only | Everything | Nothing |

## Resolve the depth of change

| Route | Typical requests | What follows |
|---|---|---|
| Substantial | Create, derive, expand, revise or restyle: new file, file derived from an existing one, template, added content, restructure, rewrite, shorten or lengthen | The steps the format method runs for that operation: content planning, `office:design` decisions (direction, palette from the user's colour source, pairing) only when the look is new, the format's structure choice (argument mode for a deck from `office:pptx`, document type for a document from `office:docx`) only when not inherited, the format's designer for new or changed parts, production and rendered review |
| Narrow | A local wording, figure, formatting or added-element change inside the accepted design | Preserve the existing design; no design decisions or designer dispatch |
| Read-only | Read, analyze, review, preview or export | No write to the source; deliver findings or the requested export |

Shortening and restructuring are substantial because they change sequence and
composition. If a narrow change turns out to need a new design decision, raise
it with the user rather than redesigning silently. A read-only request
authorizes no edit.

## Ask once

Inspect supplied files before asking about them. Infer what the request and the
files already settle, then ask the remaining decisions that change the result in
one round, together with the format method's questions. Load the skill `work-controller:work-record`
and shape and record each question as it prescribes (one decision per question,
the facts it needs anchored, two to four options with the recommended one first,
recorded with `ask` before it is put and with `answer` in the user's own words);
Office adds no second question format. Ask only the decisions
the operation leaves open (table above): an expansion or revision of an existing
file inherits its purpose, audience, structure choice and look from the file and
states them back. On the substantial route, for what is not inherited, that round includes the format's structure choice (a deck's argument mode
from `office:pptx`, a document's type from `office:docx`'s
`references/document-types.md`), the planning decisions the format lists (for a
deck, `office:pptx`'s `references/content-planning.md`: purpose and goal,
audience, scope, delivery, length or slides to add, density; propose a length
with its reasoning instead of asking an open question) and the design decisions of `office:design`:
the direction (or the supplied brand or template), and the colour source
for the palette: an image, a website, the project's stylesheets or design
tokens, an existing PPTX or DOCX, a description in words, or none. Palette
candidates are shown and chosen after this round, not asked here. State the
inferred choices instead of asking about them again. A complete or explicitly autonomous
request needs no questions. A brief already recorded by routing is this round:
ask nothing it settles. Ask again only when new evidence changes a decision
materially.

## Record the route

Record in the task brief: starting point, operation, carry-over, route,
deliverable (file, findings or export), the inherited decisions and the inferred
choices. When an existing file is a base or
is shortened, also record the approved cuts: the source content the user agreed
to drop. Everything else in the source must reach the result. The format method executes that
route. A later request that changes the route re-enters this step.
