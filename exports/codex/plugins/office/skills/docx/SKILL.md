---
name: docx
description: >
  Create, read and edit native Word (.docx) documents with styles, page layouts, tables and images while preserving existing features.
  TRIGGER WHEN: creating, reading, editing or formatting Word (.docx) documents or templates.
  DO NOT TRIGGER WHEN: spreadsheets (use office:xlsx) or presentations (use /daodan:presentation).
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

# Native Word documents

## Outcome and scope

Deliver a real editable `.docx` that meets the reader's purpose and the user's
brief. Read supplied documents, create reports or proposals, revise selected
content and apply templates using native Word structures. A PDF, screenshot or
Markdown export can accompany the document but does not satisfy a DOCX request.

Infer audience, language, document type, required sections and visual direction
from the request and supplied template. Add the remaining document decisions
(document type, template or brand, font pairing, length and page layout) to the single
`office:intake` round. Ask only when a missing decision changes the result
materially. Keep figures, citations and accepted wording faithful to
their sources; distinguish assumptions from established facts. Preserve the source
file and save edits to a separate output path. Never execute embedded objects,
macros or external links while inspecting a document.

## Start and finish through the gate

Before the first write, open a gate record. It keeps a copy of the source
document; every candidate gets a new name and the source is never written.
Never write a document by editing its package XML by hand. Before calling any
candidate finished, run `check`: it opens and renders every page with WordCraft
into the record folder, compares its text with the source and verifies the
independent review. Only the verdict `deliverable` means finished; report any
other verdict with its problems and next step as printed. Read-only work writes
nothing and needs no record.

```text
python "<plugin-root>/skills/intake/scripts/office_gate.py" start SOURCE.docx
python "<plugin-root>/skills/intake/scripts/office_gate.py" start --dir PROJECT --format docx
python "<plugin-root>/skills/intake/scripts/office_gate.py" check RECORD CANDIDATE.docx [--review REPORT] [--cuts CUTS.json]
```

## Choose the available engine

For physical DOCX creation, editing, rendering and PDF export, load
`office:wordcraft` and discover its actual installed CLI or exposed MCP tools.
After the design report is verified, the document coordinator executes that
production skill to create, save, reopen, inspect and render the real file.
Read its `references/runtime.md`; this method does not assume installation on
every host. Missing WordCraft blocks dependent production while source/design
work continues. A different writing engine requires an explicit user choice and
demonstrated support for the requested operation; do not silently substitute it.
A tool that exports DOCX has not demonstrated that it can round-trip every feature.

When explicitly selected, an available `python-docx` can create and edit supported paragraphs,
styles, lists, tables, sections, headers, footers and inline images. Confirm its
installed version and supported operations before use. It is not a Word layout
engine and does not fully author or update tracked revisions, comment anchors,
complex fields, footnotes, equations, content controls or every drawing type.
Do not silently install dependencies or describe the bundled inspector as a
document-writing engine.

Inspect an existing file before choosing an editing engine. Revisions, comments,
hyperlinks, field codes and results, footnotes/endnotes, OMML equations, content
controls, embedded objects, signatures, custom XML and unknown package parts
require demonstrated preservation. Use an available compatible Word application
or documented host engine for edits it supports. Do not assume LibreOffice or any
other converter preserves all Word features. If no available engine can retain a
required feature, preserve the source and report the unsupported operation.
Legacy `.doc`, encrypted documents and macro-enabled files require a compatible
tool; changing the extension is not a conversion.
Preserve a required macro-enabled source format and its macros. Never downgrade
DOCM to DOCX without authorization for that conversion and its feature loss.

## Inspect before editing

Use the read-only helper on native DOCX packages:

```text
python "<plugin-root>/skills/docx/scripts/docx_inspect.py" inspect INPUT.docx
python "<plugin-root>/skills/docx/scripts/docx_inspect.py" compare INPUT.docx OUTPUT.docx
python "<plugin-root>/skills/docx/scripts/docx_inspect.py" coverage INPUT.docx OUTPUT.docx --cuts cuts.json
```

`compare` matches paragraphs by position, so it suits scoped edits. After a
restyle, restructure or shortening, use `coverage`: it checks, independently of
position, that every source paragraph and table cell of the body, headers,
footers, notes and comments reached the candidate, except the approved cuts
(`cuts.json`, a JSON list of `{"text": ..., "reason": ...}` or
`{"section": "<heading text>", "reason": ...}`, the latter covering every item
from that heading to the next). `complete` is true only when no item is
unexpectedly missing; missing items carry their closest candidate text and a
similarity ratio. Tracked deletions and field instructions are not text items.
It is structural text evidence, not a visual or fidelity verdict.

The JSON inventories native content, document structure and preservation-sensitive
features, validates bounded ZIP/XML and internal relationship targets, and reports
observed changes between packages. It does not render pages, update fields, check
business meaning or certify every OOXML semantic. A validation or limit failure
means inspection is incomplete; use a compatible engine before making preservation
claims. Do not disable inspection limits to process an untrusted file.

Establish which paragraphs, table cells, sections and objects the task authorizes
changing. Preserve unaffected content and formatting. Never replace an entire
existing paragraph through `paragraph.text` or flatten all runs for a small edit:
that can destroy run formatting, hyperlinks, fields and annotation anchors. Use
supported run-aware or native range editing, preserving boundaries and relationships.
Do not strip tracked changes, accept revisions, delete comments or rebuild advanced
content merely to make an editing library handle it.

## Coordinate document design

The operation from `office:intake` selects the steps below. Preserve supplied
brands/template styles and inherited decisions. A combined DOCX/PPTX delivery
reuses one content/design identity with independent projections and layouts;
both format designers consume the same record revisions.

| Operation | Content | Theme | Layout/build scope |
|---|---|---|---|
| Create | Full shared plan | New ad hoc proposals | All required page types; new native candidate |
| Derive | Full requested projection | Inherit carried look, otherwise new | New distribution with carried claims preserved |
| Expand | Delta; accepted units retained | Inherited | New/moved sections only, on existing styles/template |
| Revise | Delta; changes and authorized cuts | Inherited | Changed sections only |
| Restyle | None: content/sequence retained | New ad hoc proposals | Apply selected theme throughout requested scope |
| Edit | None: no global strategy | Inherited | Authorized local edit only |
| Review or export | None | None | Unchanged source, requested findings/export |

For full/delta planning, load `office:content`, then dispatch
`office:content-strategist` through this entry's declared isolated bindings.
Supply the settled brief, all sources and source inventory, accepted records,
operation, per-block permissions/cuts, requested formats and assigned absolute
artifact paths. Read `references/content-planning.md` for the DOCX projection;
`references/structure.md` supplies the twelve document-type conventions. Verify
complete editorial working data, source associations and requested projections;
return gaps/conflicts/overflow or unsupported cuts to the appropriate decision.
Missing/partial artifacts are not delivery. Reuse an already accepted shared
content result rather than dispatching it again for the second format.

When a new look is needed, load `office:design` and its
`references/art-direction.md`: the settled Office brief enters Taste, then the
existing format designers, native producers and reviewers prove representative
candidates in `proposal` mode before the v2 gallery and explicit DESIGN.md selection.
Otherwise reuse the accepted theme and rebind its record under `office:design`'s
`references/records.md` when content identity/revision or requested formats
change. Use that same procedure to bootstrap an inherited legacy theme.
After proposal selection or inherited rebinding, explicitly load CONTENT.md and
DESIGN.md using the shared record loader and run their structural validation; compare project,
content revision and exact requested formats. For a bundle with PPTX, finalize
its plan/display binding under `office:pptx` before freezing the shared content
record. A new filename is no substitute for these checks. Restyle and local
operations reuse accepted editorial decisions. For a legacy restyle needing a
new DESIGN binding, the coordinator serializes unchanged source content and
inherited decisions in the shared contract without a new strategy or strategist.
Legacy inspection/local editing requires no fabricated retrospective record.

Read `references/layout-patterns.md` for concrete page patterns, native flow,
styles, geometry/growth and the format design-report handoff. The designer owns
composition under the accepted projection, not silent editorial revision.

Dispatch `office:document-designer` in `final` mode in an isolated context through the registered
`/daodan:document` entry's generated bindings, or those of `/daodan:start`, which
declares the same roles. If loaded directly, resolve that
entry before dispatch; continue the same task. A role name alone cannot supply an
inline worker body. Supply the brief, loaded content/design paths and revisions, DOCX projection,
source inventory, brand/template assets, engine capability limits, existing
renders, allowed changes and an absolute assigned design report path. Default models inherit the session. Unavailable
isolation blocks that design delivery; continue independent source preparation.

The designer writes only its assigned report and returns page-type wireframes,
page geometry, native style/section mapping, content flow and growth rules,
table/figure/caption treatment, template reuse instructions and image requests.
The coordinator remains the sole document writer and owns image requests. It
calls the exposed harness image tool; if its context lacks access, use only the
explicit parent-harness handoff in the shared image contract when available.
Verify that the report exists, covers the requested page types and supplies
supported native instructions before dependent construction. Missing, empty or
partial reports are incomplete deliveries: inspect or resume the assignment,
resolve the gap or record a concrete blocker. A worker stop alone is not delivery.

The read-only route and narrow edits do not require design dispatch, restyling or a
theme-selection gate; preserve the accepted layout and record the scoped choice.
For template work, generate the base `.dotx` with `office:design`'s
`template_kit.py` (theme, styles, page geometry, footer), supply a reusable
editable DOCX exemplar built on it and replacement guidance; claim template
features only from the kit's report and an opened, rendered sample. The design report is not proof of saved DOCX pagination or fidelity.

## Build and revise the document

Read `references/document-quality.md` for layout and review guidance. Apply a
consistent style hierarchy: title, native heading levels, body, captions and table
styles. Use real list numbering and native page/section breaks. Manual spaces,
blank-line padding and typed bullet characters are not layout structures. Preserve
the template's style IDs and inheritance when making a scoped revision.

Choose page size, orientation, margins and sections for the brief, template and
locale. Use paragraph spacing, line spacing, tab stops, keep-with-next and widow/
orphan controls deliberately. Set headers and footers per section, including
first-page or odd/even variants where needed. Use native page-number fields rather
than manually typed pagination. Avoid forcing a global paper size onto every task.

Keep tables editable, with meaningful headers, legible widths and appropriate row
breaks. Insert images as native image objects with stable proportions, captions
and useful alternative text. Keep text selectable. Use native references, bookmarks
and fields when the selected engine supports them; do not present static typed
numbers as automatically maintained cross-references or a table of contents.

For generated or edited imagery, follow the shared image contract in
`<plugin-root>/skills/pptx/references/image-tools.md`:
it names who calls the harness image tool, the parent-harness handoff when this
coordinator lacks it, provenance and verification of the returned asset, and
what a missing tool blocks. The document coordinator is the image requester;
it does not start the presentation coordinator or another image service, and
authorized text and layout work continues when imagery is blocked.

When fields, a TOC or pagination must be current, update them through an available
compatible Word or LibreOffice engine whose support covers this document, then
save and inspect that result. A request-to-update flag or cached page count is not
proof that fields were updated or pages laid out. Report unsupported field updates
instead of claiming completion from field codes alone.

## Verify and deliver

When the document uses fonts outside Microsoft Office, embed them in a separate
candidate with `office:design`'s `font_embed.py` and record its inspection result.
Complete embedding before the checks, renders and independent review below;
they must bind to the exact copy delivered. On the read-only route keep the
unchanged source and report its existing font evidence without embedding.

Reopen the actual saved output with the chosen engine. Check required text, native
styles, lists, tables, images, section settings, headers/footers and references.
For existing-file edits, compare source and candidate; account for removed parts
and unexpected content, style, relationship or sensitive-feature changes. Changed
part hashes show changed bytes, not semantic loss. Counts alone cannot prove that
comment anchors, revision ranges, fields or hyperlinks remain valid. When the
substantial route starts from an existing document (derived, restyled,
restructured or shortened), write the approved cuts recorded at intake to a cuts
file and run `docx_inspect.py coverage` on the source and each candidate. Every
unexpectedly missing unchanged/locked item is restored or brought back to the
user as a proposed cut; never cut content the user did not approve. Keep literal
coverage for those blocks. For an authorized free transformation, retain its
source/destination mapping and independently compare facts, conditions,
uncertainty and claim strength; similarity or a generated map alone proves no
semantic conservation.

Run the gate's `check` and inspect the actual pages it rendered. Check clipping, overlaps, headings separated from their text, tables split
awkwardly, blank pages, image quality, page numbers and header/footer collisions.
Correct routine defects within the brief, save and review the affected pages again.
Verify key claims and figures independently of the document's own text.

## Independent review

Dispatch `office:document-reviewer` in `final` mode in an isolated context through the registered
`/daodan:document` entry's (or `/daodan:start`'s) generated bindings when `check`
answers `review-needed`, on the renders it names, or on the read-only route after rendering the unchanged source, which then stands in
for the candidate. Supply the exact candidate path and SHA-256, render engine and
version, page manifest, brief, design report, source and candidate inspections,
allowed changes, the coverage report when one exists, the exact loaded CONTENT.md/DESIGN.md identities (when present), per-block
transformation permissions and font evidence. Require inspected page identities, concrete defects classified
blocking or advisory, preservation findings, coverage gaps, field-update evidence
and a pass/needs-fix/blocked verdict. An empty response or an uninspected render
cannot satisfy this delivery. Unavailable isolation blocks the review delivery.

Verify report artifacts and coverage, resolve every blocking finding, rerender
changed pages and obtain an updated review tied to the new candidate. Fix a
document-level defect at its source (a style, a section, the template), not page
by page. Apply an advisory finding only when the fix is local and cannot create
a new defect. Run at most three review rounds: if blocking findings remain after
the third, stop and deliver the candidate with them listed as open, rather than
oscillating between fixes. Do not apply a verdict to another file.

Deliver the editable `.docx`, with a useful preview when
available, and a concise account of changes with the reviewer's verdict and open
findings. Call it finished only on the gate's `deliverable` verdict for that
exact candidate. Name the editing and rendering engines and any remaining
preservation or field-update limit. If rendering was unavailable, label page layout
unverified and distinguish completed structural checks. Never call a document
visually verified from package inspection alone.
