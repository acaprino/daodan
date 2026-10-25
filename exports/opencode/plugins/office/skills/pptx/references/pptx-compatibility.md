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

# Design for editable PowerPoint

Apply this contract before design work, generating reference images or
constructing slide objects. It governs Office's presentation output, including
web-inspired layout ideas. Office owns the slide specification and verifies it
against the chosen construction engine.

## Establish the target before design

- Preserve an existing deck's slide size, theme, master/layout relationships and
  required native features. For a new deck, use the requested dimensions; when
  unspecified, record a fixed 16:9 canvas as the default. Do not design a
  responsive page and assume it will convert to a fixed slide.
- Record the construction engine and version, intended viewing application,
  available preview renderer and required editability. Distinguish capabilities
  verified in the installed engine from assumptions. Check the commands needed
  for the proposed composition before accepting it.
- Resolve font families and weights available to construction and target
  rendering. Preserve a supplied template's typography. Install the direction's
  pairing and embed it in the delivered file through `office:design`.
  Record any substitution and recheck line breaks; claim embedding only from the
  `font_embed.py inspect` result, and never promise how another computer renders
  a font that is not embedded. Check the weights against the renderer: a weight
  the preview renderer cannot draw shows as a substitute in previews and in any
  PDF it exports, so a review of those renders cannot judge that weight.
- Prefer well-supported native text, basic shapes, connectors, tables and charts.
  A specialized effect, chart type, master feature, SVG or media feature needs
  evidence in the selected engine and target renderer. An exported PPTX alone is
  not that evidence. Unsupported elements must be redesigned within the brief
  or reported before construction, rather than silently simplified on export.

For a narrow edit or export, establish only the constraints needed for the
requested changes and preservation. Do not initiate a redesign of untouched pages.

## Specify slide objects, not a website

The designer's existing report carries the slide specification; do not introduce
a second construction schema. Use slide IDs and one declared coordinate unit
and origin. For each meaningful element, provide:

| Field | Required content |
|---|---|
| Identity and purpose | Stable slide ID from the deck plan (not thumbnail order), object identity, communication role, selected pattern and variation, exact accepted content and its source or citation |
| Geometry | Declared origin and unit; x/y position, width/height, margins or padding, alignment and stacking order |
| Typography | Font role from the pairing, weight, size, line spacing, colour role from the chosen palette, and intended line breaks or fit constraints |
| Representation | Native text, shape, connector, table or chart; or a separate image asset with crop, dimensions, placement and provenance (supplied, searched or generated under `image-tools.md`) |
| Editability | What must remain editable, including chart series/data, table cells and diagram labels |
| Engine evidence | Supported construction operation/type, overflow or splitting behaviour, and any unresolved feature or target-renderer limitation |

Translate web-inspired layout into this fixed slide specification before
generation. CSS flex/grid, browser viewport units, DOM structure, hover states,
scroll effects and responsive breakpoints are not PowerPoint construction
instructions. Express their useful visual intent through fixed geometry and
static compositions. Treat animation as a separate, explicitly requested feature
with verified support. Use gradients, shadows, transparency and clipping only
where the chosen engine and target renderer preserve them; otherwise design a
supported visual equivalent without changing the accepted message or brand.

Keep text readable at presentation size with room for the actual content.
Measure text fit and revise the layout before shrinking type. Build native charts
from the authoritative source data, preserving labels, units and series rather
than tracing generated pixels. Build requested editable tables with native cells
and editable diagrams with shapes/connectors whose relationships are preserved.

Photographs, textures and illustrations may be separate images. Keep essential
titles, body text, data labels, charts and tables native when their meaning or the
brief requires editing. Do not flatten a complete slide, convert required text to
outlines, or silently rasterize editable objects to improve visual similarity.
An image or SVG inside a PPTX is not proof of native object editability. A change
to requested editability needs the user's decision if no compatible authorized
construction route remains. Continue independent work while that decision is open.

## Carry constraints through image generation and construction

Reference imagery must respect the fixed canvas, text regions, margins and
native-object plan of the accepted slide specification. Inspect a generated
reference for buildability with DeckCraft's discovered commands before extending
the direction across the deck. Correct an incompatible reference rather than
accepting a design the engine cannot build.

Generated or edited images must use the exposed harness image tool under
`image-tools.md`. An external image script, image-search utility or web workflow
does not replace that obligation. Preserve source wording, figures, logos and
approved assets when construction corrects mistakes in a generated reference.

When DeckCraft constructs or edits objects, map the same specification to its
actual discovered commands. Preserve source objects and allowed-change limits.
There is no general HTML/CSS-to-PPTX converter in this integration. Each save
needs the preservation checks required by that engine.

## Verify appearance and editability separately

Render the actual saved candidate and compare every page with the accepted
design and source content. Review bounds, alignment, line breaks, clipping,
spacing, color, image crops, charts and connector relationships. For a reusable
template, exercise representative page types with real content. Fix material
differences, rebuild and repeat the review for the changed candidate.

Inspect native objects, text, table cells and chart data separately. Same-engine
round-trip renders and object counts cannot prove cross-application fidelity or
editability. Report design-reference comparison, selected-engine preview and
target-application verification as separate evidence. To claim fidelity in
Microsoft PowerPoint, open/render the actual candidate there and record the
version and font environment. If it is unavailable, report PowerPoint fidelity
as unverified while delivering the available candidate and preview evidence.

Do not promise pixel-perfect equivalence from a generated image, a browser
preview, valid OOXML, unit tests or a DeckCraft render. An exact comparison claim
must name the candidate, reference, renderer, fonts, resolution, comparison
method and measured result. Never improve that score by sacrificing required
native content. The final review records any visual or editability compromises.
