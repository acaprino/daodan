> `<plugin-root>` names the directory that holds this plugin's `.codex-plugin/plugin.json`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

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

<!-- Adapted from marcmarti9/agentit, skills/typography-and-layout/SKILL.md,
revision fc38111622ac459ccf843234863bd0b8fcb6ebfd (Apache-2.0).
Modified for native Word/PowerPoint layout and Office production ownership.
Attribution and retained licenses: agentit-upstream.md in this directory. -->

# Typography and layout for Office

Make text serve reading, hierarchy and the actual medium. Pair with
`editorial-design.md` for visual hierarchy; take logical sequence from `office:content`. Define typography within the
existing document brief or presentation design report; `office:docx` and
`office:pptx` retain editable-file production and verification.
This method is not a brand redesign, copy rewrite or extra production engine.

## Establish constraints

Record content class, audience, language/scripts, page size or slide canvas,
delivery context, brand rules and available fonts. Honor approved faces and
template styles. The assigned proposal or selected `DESIGN.md` supplies palette,
font roles and fallbacks under `art-direction.md`'s proposal/final boundary.
`font-pairings.md` is a resource; a supplied brand or template remains binding.

Check font family, version, real weights and italics, glyph coverage and permitted
use in the intended output. Choose a compatible available fallback and inspect
its metrics. Naming a font in a preset or seeing it in a PDF does not install it,
prove embedding or grant redistribution rights.

## Procedure

1. Inspect representative real content. Identify headings, body, labels, data,
   captions, code and non-Latin or numeric needs. Use the fewest roles that
   communicate the structure, without a fixed limit on font families.
2. Select or retain faces for legibility, available styles, script coverage and
   licensed use. State the purpose and fallback of each role. Do not require
   paid-font hunting or reject a face merely because it is familiar.
3. Define a role scale with sizes in points, weights, line spacing and paragraph
   spacing. Make hierarchy discernible without a universal size ratio or color
   alone. Use supported real bold/italic styles instead of synthetic variants.
4. Set reading measure from actual content and font metrics. Sustained prose
   needs a comfortable column; tables, diagrams and code may justify another
   width. Choose paragraph spacing or first-line indentation deliberately.
5. Use a small set of spacing decisions for headings, captions, lists and figures.
   A heading must visibly belong to its content. Align labels and numeric data
   for their task; avoid ornamental tracking that repairs an unsuitable measure.
6. Map the roles to native settings below. The format designer redistributes
   dense material or adjusts a table; changed logical sequence, substantive
   rewriting or cuts return to content. Do not shrink all text until it fits.
   Preserve approved meaning and source links.
7. Embed non-Office fonts through `SKILL.md`'s `font_embed.py` step when the
   engine is available, and record the inspection result, not just a requested flag.
8. Render dense, sparse and long-label cases from the saved DOCX or PPTX. Inspect
   overflow, contrast, hierarchy, line length and fallback-induced changes. Check
   slides at the intended projection size and documents at normal reading scale.
9. Record role/style mapping, font status, scale, measure, spacing, relevant
   renders and gaps in the existing design record. Keep copy-change requests
   separate from typographic corrections.

## Map to native objects

| Format | Required layout decisions | Avoid |
|---|---|---|
| DOCX | Native paragraph/character styles and inheritance; section margins and columns; paragraph spacing, keep-with-next, widow/orphan controls; table widths and repeating headers | Blank-line padding, manual spaces, typed bullet symbols or floating boxes for normal body flow |
| PPTX | Fixed text-frame geometry, padding, wrapping and alignment; explicit point sizes; native text, charts, tables and shapes where editability is required | Browser breakpoints, CSS effects without an engine equivalent, or a full-slide raster replacement for editable content |

For a table exceeding its column, revise column widths, orientation or section
layout, or split it with clear continuation labels. A slide cannot rely on
scrolling or hover to expose clipped content. A DOCX reading on a smaller screen
does not imply the fixed page will reflow like a responsive website.

Respect the native-object and target-renderer rules in
`<plugin-root>/skills/pptx/references/pptx-compatibility.md`
for PPTX. Use `office:docx` for actual field updates, pagination and source
preservation. Do not substitute a browser proof for the saved artifact render.

## Craft and evidence

Check distinguishable heading levels, readable captions and sources, suitable
numeric alignment, paragraph shapes and consistent spacing. Hyphenation, quotes,
dates and language conventions follow the approved house style. Avoid decorative
all-caps paragraphs and manual line breaks that collapse under small edits.

If content, fonts or a compatible renderer are unavailable, provide a conditional
style specification with the missing verification named. Source markup alone
does not prove accessibility, font embedding, pagination or PowerPoint fidelity.
The production owner retains the existing saved-file and delivery gates.
