# Office

Create professional editable PowerPoint presentations and work directly with
native Excel workbooks and Word documents. The plugin has complementary skills
and explicit workflow entries:

| Task | Skill | Workflow |
|---|---|---|
| Resolve where the work starts, how much it changes and what is delivered | `office:intake` | First step of all three workflows |
| Design a deck or reusable presentation | `office:pptx`, `office:slidepoise` | `office:presentation` |
| Edit, review, preview or export PPTX to PDF | `office:deckcraft` | `office:presentation` |
| Create, inspect, analyze or edit XLSX | `office:xlsx` | `office:workbook` |
| Create, read, review or edit DOCX | `office:docx`, `office:wordcraft` for native production | `office:document` |
| Design a document or deck: direction, palette, fonts, argument mode, hierarchy | `office:design` | Used by the Word and presentation workflows on the substantial route |
| Build a palette from an image, a website, the project's stylesheets or an existing file | `office:design` (`palette.py`, `palette_preview.py`) | Five contrast-safe candidates compared in the browser, one chosen by number |
| Download, install and embed fonts | `office:design` (`font_fetch.py`, `font_embed.py`) | 12 Google Fonts pairings, per-user install, embedding in the delivered file |

## How every workflow starts

The three entries are named by format and share one route vocabulary. Each opens
with [`office:intake`](../../plugins/office/skills/intake/SKILL.md): a single round
of contextual questions, skipped when the request already settles everything, that
resolves where the work starts and how much it changes. The format method adds
only its own questions to that round.

| Route | Typical requests | What follows |
|---|---|---|
| Substantial | New file, file derived from an existing one, template, restyle, restructure, shorten | Theme, composition, the format designer where one exists, production and rendered review |
| Narrow | A local wording, figure or formatting change | The existing design is preserved; no designer |
| Read-only | Read, analyze, review, preview or export | Nothing is written to the source; findings or the export are delivered |

A supplied file is never overwritten: every result is a separate candidate.

## Install Office

Office belongs to the **Shinatama** marketplace. Use the commands for your host:

```bash
# Claude Code
claude plugin marketplace add acaprino/shinatama
claude plugin install office@shinatama

# Codex
codex plugin marketplace add acaprino/shinatama
codex plugin add office@shinatama

# GitHub Copilot
copilot plugin marketplace add acaprino/shinatama
copilot plugin install office@shinatama
```

Pi installs the tagged repository package. Replace `<published-version>` with a
published Shinatama release containing the Office version you need:

```text
pi install git:github.com/acaprino/shinatama@v<published-version>
pi install npm:pi-subagents
```

Keep Office's prompts, skills and role resources when applying Pi package filters.
`pi-subagents` supplies the isolated workers used by presentation design/review
and creative Word design.
OpenCode V2 installs the generated package:

```text
opencode plugin add 'github:acaprino/shinatama#v<published-version>::path:exports/opencode'
```

Its plugin configuration can select `"options": { "plugins": ["office"] }`.
See the
[host guide](../hosts.md#installation-and-selection) for package selection and
worker mechanisms; the Office repository and marketplace identity are the ones
shown above.

## Dependencies and runtime requirements

Plugin dependencies, external executables and host tools are different
requirements. Installing Office does not install SlidePoise, DeckCraft, WordCraft, image
tools or Office applications.

### Bundled design skills

Office includes three adapted upstream skills. They require no separate plugin
installation and reuse the existing brief, production engines and review steps:

| Part of `office:design` | Contribution | Source |
|---|---|---|
| `references/directions.md` | Twenty visual directions A to T: composition and rhythm for slides and pages, the font pairing, default palette seeds | Original; directions Q to T carry seed palettes from [Anthropic skills](https://github.com/anthropics/skills/tree/dbd4588f9e1033efb41dad4bef2f7947c8993d44/skills/theme-factory) Theme Factory |
| `scripts/palette.py`, `scripts/palette_preview.py` | Palette seeds from an image, a website, stylesheets or an Office file; five contrast-safe candidates; the comparison page | Original, standard library (Pillow for images) |
| `references/editorial-design.md` | Reading map, hierarchy, page/slide rhythm, figures and captions | [Agentit](https://github.com/marcmarti9/agentit) |
| `references/typography.md`, `references/font-pairings.md`, `scripts/font_fetch.py`, `scripts/font_embed.py` | Type roles, measure, spacing, native style mapping; twelve Google Fonts pairings with download, install and embedding | Agentit (method), original (catalog and scripts) |

New documents, templates and substantial redesigns go through `office:design`:
one direction, one palette built from the user's colour source, one font
pairing, one argument mode, shared by a Word document and a deck made from the
same brief. A supplied brand or template always wins over a direction. Narrow
edits, inspection and exports do not start another design process. Palette and
font choices are inputs to composition, not a complete layout generator.

Word production maps the design to native styles, sections, paragraphs and tables.
PowerPoint production maps it to the fixed canvas and editable slide-object plan,
using the selected library direction and patterns. The guides add no engine or
worker. The actual saved DOCX/PPTX must still be rendered and inspected; a theme
showcase, HTML preview or generated reference does not prove file fidelity.
Generated or edited imagery uses the active harness image tool for either format.
Images and visual assets may be supplied/reused, searched, or generated/edited
with that tool according to the brief and shared theme. Search is not required
before generation. Both designers state the chosen route and asset requirements;
the production coordinator obtains and inspects the result. Searched assets keep
source and usage-rights evidence; generated assets keep tool/prompt/reference
provenance. Native editable text, factual charts and tables remain native objects.

The source pins, local modifications and retained Apache-2.0/MIT notices are in
the [Agentit provenance](../../plugins/office/skills/design/references/agentit-upstream.md)
and [Theme Factory provenance](../../plugins/office/skills/design/references/theme-factory-upstream.md).
The Theme Factory skill, its ten preset files and its showcase are no longer
shipped; four of its palettes continue as direction seeds. These are tracked copied-source
upstreams, not dependencies on the complete Agentit or Anthropic plugin packages.
They are pinned snapshots with manual, occasional upstream review, without
periodic synchronization or checks at every use.

### Separate format designers and reviewers

The presentation workflow keeps `office:presentation-designer` and
`office:presentation-reviewer`; the Word workflow dispatches
`office:document-designer` for new documents, templates and substantial
restyling, and `office:document-reviewer` on every route, on the rendered
candidate or on the unchanged source for a read-only review. Both reviewers
classify defects as blocking or advisory, report a shared cause once at document
or deck level, and the coordinator resolves blocking findings within at most
three review rounds. Both formats check that a derived, restyled or shortened
file kept every source text item except the approved cuts (`pptx_inspect.py
coverage`, `docx_inspect.py coverage`). Both receive the same `office:design` record: direction, the chosen
palette by role, the font pairing with its installation status, and the argument mode.
For a Word/deck bundle, each retains that identity while choosing suitable
point sizes and format-specific composition. Narrow edits and read-only Word
tasks preserve their scope without a new design assignment.

| Designer | Concrete output | Layout reference |
|---|---|---|
| `office:presentation-designer` | Per-slide wireframe, exact native object geometry, content placement, image requests and template replacement rules | [Layout patterns](../../plugins/office/skills/pptx/references/layout-patterns.md) with their region sketches, specified under the single slide-object schema of [pptx-compatibility](../../plugins/office/skills/pptx/references/pptx-compatibility.md) |
| `office:document-designer` | Page-type wireframes, covers, sections/columns, native style map, table and figure treatment, headers/footers, pagination and content-growth rules | [Word design guidance](../../plugins/office/skills/docx/references/document-design.md), with document recipes, four opening patterns and three table treatments |

The region sketches in the layout patterns are adapted from PPT Visual (MIT,
retained license and source pin in the patterns file). Word guidance is original
Office content informed by
[Word Document Design Agent](https://github.com/tivojn/Office/tree/303e55d42a71aca4bc1dffdb49f6c1f090889899/Word).
That source declares MIT in its README but lacks a complete license/copyright
text in the inspected tree; no source text, code or numeric presets were copied.
Neither source supplies binary PPTX/DOCX templates. The agents return layout
instructions; the producer can build a reusable editable exemplar when requested.
POTX/DOTX or master-layout claims require actual engine support and verification.

Designers write only their assigned design report. The coordinator verifies that
delivery before construction, owns the actual document/deck and calls the harness
image tool. If that tool is absent in its context, the existing image contract
permits a supported handoff to the invoking harness; otherwise dependent image
generation is unavailable. Copilot coordinators retain their explicit tool
filters: installing Office does not grant an image/MCP tool. A missing or partial
report remains an incomplete delivery. The
existing presentation reviewer is retained; saved Word pages are checked by the
Word producer. Wireframes and theme previews do not prove final pagination or
native editability.

### No plugin dependencies

Office has no required or optional plugin dependencies and consults no external
design provider. Its design method, `office:design`, is self-contained: the
palette is built from the user's own colour source by `palette.py`, a
[font catalog](../../plugins/office/skills/design/references/font-pairings.md)
of twelve Google Fonts pairings supplies the type, the editorial and typography
references supply hierarchy and type roles, the
[visual directions](../../plugins/office/skills/design/references/directions.md)
(A to T) supply composition, rhythm and the pairing, and the
[slide design library](../../plugins/office/skills/pptx/references/design-library.md)
supplies the canvas rules and routes to the
[layout patterns](../../plugins/office/skills/pptx/references/layout-patterns.md)
(1 to 18, by communication job). Five argument modes (pyramid, narrative,
instructional, showcase, briefing) decide how the file argues. One mode, one
direction, one palette and one pattern per slide cover hundreds of combinations
and need nothing installed.
On external template libraries: their decks are usually proprietary and copying
one is a licensing and editability problem, while a library direction or pattern
can be implemented natively with the same visual result.

### Required when the operation needs them

| Requirement | When needed | How it is supplied |
|---|---|---|
| Python for Office helpers | Package inspection, comparison and runtime bridges | An available Python executable; inspectors use the standard library |
| SlidePoise runtime | New creative decks, reusable exemplar decks and substantial redesign | External runtime; [pinned setup](../../plugins/office/skills/slidepoise/references/runtime.md) requires Python 3.10+, Node.js 18+ and npm 9+, plus its reconstruction packages |
| DeckCraft CLI or exposed native MCP tools | The DeckCraft editing, preview or PDF path | External executable; [runtime setup](../../plugins/office/skills/deckcraft/references/runtime.md) documents version discovery and supported operations |
| Harness image-generation tool | Generating or editing imagery | An actual tool exposed in the executing context; no separate API-key script is an automatic substitute |
| Image inspection and compatible presentation renderer | Visual approval of a presentation | Host image-reading capability and actual renders; SlidePoise setup supports LibreOffice and Poppler, while DeckCraft has its own renderer |
| Required fonts | Rendering text with the intended appearance | A brand font, or a catalog pairing that `font_fetch.py` downloads from Google Fonts and installs for the current user |
| Microsoft PowerPoint or Word on Windows | Embedding fonts in the delivered PPTX or DOCX | `font_embed.py` drives the installed application; without it the file names the Office fallback and recipients need the fonts |
| Isolated worker dispatch | Coordinated presentation design/review and creative Word design | Host subagent mechanism, including Pi's companion package |
| WordCraft CLI or exposed MCP interface | DOCX creation, editing, rendering and PDF after design | External runtime; [runtime contract](../../plugins/office/skills/wordcraft/references/runtime.md), version and command discovery required |
| Compatible workbook engine | Writing XLSX | A suitable host artifact runtime or an explicitly selected compatible engine |
| Calculation, field-update or document-rendering engine | Recalculated formulas, refreshed Word fields or reviewed document pages | An engine that actually performs the requested operation; package inspection cannot do it |

A text-only PPTX edit needs no image-generation call. A SlidePoise-only operation
does not require DeckCraft. A preview-only operation does not need SlidePoise or a
resaved PPTX. Source files and previous candidates are preserved.

For DOCX, design, physical production and review are separate: `document-designer`
returns the layout/style plan; the document coordinator loads `office:wordcraft`
to create, save, reopen, inspect and render the actual editable `.docx`;
`document-reviewer` inspects the rendered pages independently and returns the
verdict. PDF and
page previews accompany that file when requested. Reading a DOCX package alone
does not require WordCraft. Another writing engine requires an explicit user
choice and demonstrated feature support. WordCraft is alpha; imported complex
documents require a real preservation round-trip rather than an assumed guarantee.

The documented WordCraft reference is v0.10.0. Discover the installed version
before invoking it: v0.8.0 supports repeated `--cmd` arguments but not the newer
`--script` job interface. The runtime guide covers this distinction; Office does
not automatically upgrade the application. An installed CLI may be outside PATH.

### Optional integrations

| Integration | Status and purpose |
|---|---|
| DeckCraft native MCP interface | Optional alternative to CLI transport; the host must register and expose it |
| DeckCraft desktop application | Optional visual editor or shared desktop session; headless CLI operations do not need it |
| SlidePoise Console/session panel | Optional when supported by the host |
| Microsoft Office applications | Optional for basic headless operations; target-application fidelity checks, live application control or physical printing require the corresponding application/interface |

Optional integrations do not replace a missing capability required by the chosen
operation. Missing rendering means an unreviewed output, not visual approval.

## Palette

The palette is built for each file, not picked from presets. At intake the user
names the colour source: an image (a logo, a photograph, a screenshot), a
website, the project's stylesheets or design tokens, an existing PPTX or DOCX,
or a description in words; with none, the chosen direction's default seeds
apply. `palette.py` extracts one or two seed colours and builds five complete
candidates from them, each changing one thing (sober, faithful, bold, deep,
dark). Every candidate carries background, ink, surface, accent, muted text and
four data colours; ink, accent and muted hold at least 4.5:1 on both background
and surface, data colours hold 3:1 and stay distinguishable from each other,
also under simulated red-green colour blindness. `palette_preview.py` writes
one static page that compares the five candidates (a compact overview, the
detail of each on hover, pinned on click) and opens it in the browser; the
coordinator then asks which number to use.

```text
python exports/claude/plugins/office/skills/design/scripts/palette.py from-image logo.png
python exports/claude/plugins/office/skills/design/scripts/palette.py from-url https://example.com
python exports/claude/plugins/office/skills/design/scripts/palette.py from-css ./src/styles
python exports/claude/plugins/office/skills/design/scripts/palette.py from-file last-year.pptx
python exports/claude/plugins/office/skills/design/scripts/palette.py candidates --seed "#1D4ED8" --seed "#E76F51" > candidates.json
python exports/claude/plugins/office/skills/design/scripts/palette_preview.py candidates.json --out compare.html --open
```

All of it is offline standard-library Python (Pillow for images, a fetch of the
named site for `from-url`); no model chooses a colour. The contrast figures are
computed from the hex values and say nothing about how an engine, a projector
or a printer reproduces them.

## Fonts

Office never assumes a font is present. The type comes from a supplied brand or
template, or from the pairing named by the chosen direction in the
[font catalog](../../plugins/office/skills/design/references/font-pairings.md)
of twelve Google Fonts pairings.

```text
python exports/claude/plugins/office/skills/design/scripts/font_fetch.py install "Inter:ital,wght@0,400;0,600;0,700;1,400"
python exports/claude/plugins/office/skills/design/scripts/font_embed.py embed candidate.pptx delivery.pptx
python exports/claude/plugins/office/skills/design/scripts/font_embed.py inspect delivery.pptx
```

`font_fetch.py install` downloads only the missing faces from Google Fonts,
checks each file's family, weight, style, license (OFL, Apache or UFL) and
embedding permission, and installs it for the current user without administrator
rights. `font_embed.py embed` saves a new copy through Microsoft PowerPoint or
Word on Windows. Measured on PowerPoint and Word 16 (Microsoft 365): PowerPoint
embeds only the characters used, so a recipient sees the deck as designed but
needs the font installed to type new text in it; Word embeds complete fonts.
Elsewhere `embed` reports that no engine is available, and the delivery names the
pairing's Office fallback. `inspect` lists used and embedded fonts on any host.

## Commands and usage

Workflow entries coordinate the task. Skills provide methods, while the designer
and reviewer are workers dispatched by the presentation coordinator.

For example, add `Take the colours from our logo in brand/logo.png` or `Match
the palette of https://example.com` to a presentation brief, or `Create a Word
proposal in the Editorial Report direction, colours from last year's deck` to a
document request. The workflow extracts the seeds, shows five palette candidates
in the browser and asks which to use; no separate theme installation or agent is
needed. For a bundle, request `One direction and one palette for the Word report
and its presentation; let each format designer choose its native page/slide
layouts`.
You can also name how the deck argues, for example `Use the briefing mode: a
status deck read without a presenter`.

Every workflow opens with the shared intake round. For a new deck or a
substantial redesign, that round adds art direction, style, content, page count
and slide types, followed by a static design
preview to look at before construction: a wireframe page with one 16:9 frame per
planned slide, the chosen palette and the slide sequence. It is a review artifact
(`preview only`), not a rendered deck. To compare candidate directions without
touching the plan, run the same plan once per direction with `--direction L` (see
the [design preview reference](../../plugins/office/skills/pptx/references/design-preview.md)).
A separate style proof (one representative
slide generated through the harness image tool) is optional and needs an explicit
image-budget decision.

```text
python "<plugin>/skills/pptx/scripts/design_preview.py" --plan plan.json --out preview.html
python "<plugin>/skills/pptx/scripts/design_preview.py" --plan plan.json --view
```

| Host | PowerPoint | Excel | Word |
|---|---|---|---|
| Claude Code | `/office:presentation` | `/office:workbook` | `/office:document` |
| Codex | `presentation-workflow` skill | `workbook-workflow` skill | `document-workflow` skill |
| GitHub Copilot | Select the `presentation-coordinator` agent; `presentation.prompt.md` is the entry prompt | `workbook.prompt.md` | Select the `document-coordinator` agent; `document.prompt.md` is the entry prompt |
| Pi | `/office-presentation` | `/office-workbook` | `/office-document` |
| OpenCode V2 | `/office:presentation` | `/office:workbook` | `/office:document` |

On Codex, invoke the workflow skill from the skill picker or name it in the
request. On Copilot, use the coordinator for isolated presentation dispatch; the
prompt by itself does not establish that its worker harness is active. Do not
invoke a role name as though it were a workflow or shell command.

Examples below use Claude/OpenCode entry names. On another host, select the
corresponding entry above and keep the same request:

```text
/office:presentation Create an eight-slide Italian leadership deck from brief.docx and figures.xlsx. Use our brand assets, generate imagery with the harness tool where useful, and deliver editable PPTX plus a reviewed PDF.

/office:presentation Create a reusable editable exemplar deck with cover, section divider, comparison, data and conclusion layouts, plus short reuse instructions.

/office:presentation In quarterly.pptx, update slide 3 with the figures from actuals.xlsx. Preserve other content and formatting, retain native chart data, and save a separate candidate with previews.

/office:presentation Export quarterly.pptx to a printable PDF and PNG previews. Preserve the source, include hidden slides in the previews, and exclude them from the PDF.

/office:presentation Review board.pptx for a board audience. Findings only: do not change the file.

/office:presentation Make a new 12-slide client deck from last-year.pptx: keep its structure and look, replace the content with brief.docx.

/office:workbook Update forecast.xlsx with this quarter's actuals, preserve formulas and charts, and verify recalculated totals.

/office:document Turn brief.md into a Word proposal using template.docx, with native heading styles and editable tables.
```

### Runtime discovery and diagnostics

The following commands run from a Shinatama checkout and use the generated Codex
package as a concrete example. Installed users replace
`exports/codex/plugins/office` with their actual Office package root; the helpers
are shipped to all five hosts. These commands discover or inspect resources;
they do not execute the coordinated creative workflow.

```text
python exports/codex/plugins/office/skills/slidepoise/scripts/slidepoise_bridge.py discover
python exports/codex/plugins/office/skills/slidepoise/scripts/slidepoise_bridge.py cli doctor
python exports/codex/plugins/office/skills/deckcraft/scripts/deckcraft_bridge.py discover
python exports/codex/plugins/office/skills/deckcraft/scripts/deckcraft_bridge.py cli help run
python exports/codex/plugins/office/skills/deckcraft/scripts/pptx_inspect.py inspect quarterly.pptx
python exports/codex/plugins/office/skills/deckcraft/scripts/pptx_inspect.py compare quarterly.pptx candidate.pptx
python exports/codex/plugins/office/skills/deckcraft/scripts/pptx_inspect.py coverage quarterly.pptx candidate.pptx --cuts cuts.json
```

For an explicitly selected runtime, put bridge options before the subcommand:
`--home` selects the SlidePoise installation; `--binary` selects the DeckCraft
executable. `SLIDEPOISE_HOME` and `DECKCRAFT_CLI` provide environment alternatives.
An existing runtime installation must pass discovery; a registered skill alone
does not supply its executable. Follow the linked runtime references for setup,
scoped command plans, rendering, PDF export and optional MCP configuration.

## Presentations

SlidePoise explores visual compositions with image generation and reconstructs
selected designs into editable PowerPoint text, charts, tables, shapes and
connectors. Photographs and illustrations can remain separate image objects.
Shinatama's Office plugin owns the integration and delivery contract; the framework, its construction
schemas and its design method remain in the external
[SlidePoise repository](https://github.com/henryhyw/slidepoise).

Install the pinned runtime using the [runtime reference](../../plugins/office/skills/slidepoise/references/runtime.md).
It requires Python, Node/npm, image generation and inspection, suitable fonts and
a PowerPoint preview renderer. Shinatama does not copy the framework or install it
when the marketplace loads. The packaged bridge discovers its resources without
relying on a particular host's skill-registration directory.

The presentation method develops the argument and sources, resolves shared style,
constructs native objects and inspects the actual rendered deck. A package that
opens is insufficient evidence of a professional presentation. A slide image is
insufficient evidence of editable charts or text. Missing capabilities remain
explicit in the delivery review.

Example request:

```text
Create a polished eight-slide Italian presentation for our leadership team from
these documents. Make the recommendation and its assumptions clear, use our
brand assets, and deliver editable PowerPoint charts and a PDF preview.
```

### Creative specialists and images

The coordinator dispatches a presentation designer for art direction and an
independent reviewer for the rendered result. The designer produces a mode,
a direction and image requests; the reviewer classifies findings as blocking,
advisory or deck-level, and only blocking findings prevent a pass. The coordinator
owns deck writes and repairs, fixes deck-level defects at their source and stops
after three review rounds, delivering any remaining blocking findings as open.

All creative guidance follows the [PPTX compatibility contract](../../plugins/office/skills/pptx/references/pptx-compatibility.md)
before reference-image generation. The coordinator establishes a fixed slide
canvas, fonts, target application and engine-supported native objects. The
designer specifies object positions and sizes, typography, stacking, native/image
representation and required editability. Web layout ideas become fixed slide
compositions; responsive behavior, hover and scrolling do not become PPTX features.

SlidePoise receives these constraints in its planning and reconstruction context.
DeckCraft uses supported commands for the relevant native objects. This integration
does not convert arbitrary HTML/CSS into PowerPoint. Text, data-bearing charts,
tables and diagrams retain the required editability; photos and illustrations can
remain separate images. A full-slide screenshot is not an editable substitute.

The review compares the saved candidate with the accepted design and checks
native content separately. It records selected-engine previews and verification
in the intended viewing application as different evidence. Microsoft PowerPoint
fidelity requires opening/rendering the candidate there with the recorded fonts;
otherwise it stays unverified. No pixel-perfect guarantee follows from a valid
file, passing tests or a matching DeckCraft preview.

Generated imagery must use the image tool actually exposed by the harness.
Restricted workers return image requests to a context that has the tool. Missing
image access blocks that step; an API-key script or external image service is not
an automatic fallback. Existing assets and text-only edits need no generation.
Generated slide images become editable slides through SlidePoise reconstruction.

### Complementary editing and preview

DeckCraft provides targeted native-object edits, previews and PDF export while
SlidePoise retains creative generation and reconstruction. There is no mandatory
DeckCraft resave of every SlidePoise output. An imported deck first undergoes a
no-edit round-trip comparison before editing; source files and previous candidates
are preserved. The bundled PPTX inspector reuses Office's bounded ZIP/XML reader
and reports text, slide order, notes, relationships and part changes. Its results
are structural evidence, not a fidelity verdict. After a restyle, restructure or
shortening, its `coverage` check confirms, regardless of slide position, that every
source paragraph, table cell, chart text and speaker note reached the candidate,
except the cuts approved at intake; anything else missing blocks the review.

DeckCraft 0.10.0 has alpha fidelity limits, particularly for complex imported
features. Unexpected losses block the affected operation. Native-chart edits can
detach an embedded workbook or lose a secondary axis. Actual renders and source
comparisons remain necessary. A print request produces a reviewed printable PDF;
physical printing needs a separately available printer interface. PDF slide
artwork is rasterized with searchable text and is not a native editable deck.

Template requests produce editable exemplar decks and reuse guidance. `.potx`
or master-layout support is not implied. The presentation review records engines,
candidate hash, native editability evidence, page coverage, preservation and limits.

## Native Excel

The XLSX method reads and writes real workbooks with formulas and native objects.
It supports analysis, reporting, financial or operational models, tables, charts,
validation and formatting through an appropriate available workbook engine.
It preserves an existing file's architecture and changes only the requested
scope. CSV export and pictures do not stand in for requested workbook features.

The packaged standard-library inspector inventories package integrity, formulas,
cached results and sensitive objects. Its comparator supplies before/after
evidence for changed formulas and lost parts. It does not evaluate formulas or
decide which changes the user authorized. A calculation engine such as Excel,
LibreOffice or a supported host artifact runtime supplies recalculation evidence.
Advanced objects require an engine that can preserve them; availability must be
verified before rewriting a supplied file.

Example request:

```text
Update this XLSX with the new quarter's actuals, preserve formulas and charts,
add an editable variance summary, and verify the totals and recalculation.
```

## Native Word

The DOCX method creates and edits real Word paragraphs, styles, lists, tables,
sections, headers, footers and images through an available compatible document
engine. It follows the user's template, language and page requirements and keeps
the document editable. Existing-file revisions retain unaffected content and
formatting rather than flattening whole paragraphs for a small text change.

The packaged standard-library inspector checks bounded ZIP/XML, inventories native
content and preservation-sensitive features, and compares saved packages. Its
before/after evidence helps detect unexpected content or part loss; it does not
render pages or prove that every annotation or relationship remains meaningful.
Tracked revisions, fields, comments, equations, embedded objects and other advanced
features require an engine with demonstrated support for their preservation.

Actual page review requires a compatible renderer. A Word or supported document
engine must update fields and a table of contents when those results need to be
current. Field flags and cached page counts cannot establish that either happened.
Missing rendering or field-update evidence stays explicit in the delivery review.

Example request:

```text
Create an Italian Word proposal from these notes and our template, with native
heading styles, editable tables, section headers and a reviewed page layout.
```

## Distribution and limits

The compiler distributes the skills, helpers and workflows to all five supported
hosts. Runtime prerequisites are documented tool requirements, not invented
marketplace dependencies. A packaged integration does not establish live image
generation, rendering, Office application control or end-to-end behavior on every host.
Native document work means editing actual file content and objects; controlling
a live Microsoft Office application requires an available application interface.

SlidePoise is MIT-licensed; DeckCraft is dual MIT OR Apache-2.0.
WordCraft is also MIT OR Apache-2.0 and remains external. Those production
runtimes are not copied into Office. The bundled editorial and typography
references and the PPT Visual region sketches in the layout patterns are adapted
source imports; their upstream attribution and licenses ship with them, as does
the Apache notice for the four Theme Factory palettes carried as direction seeds. The Word composition
reference is original local guidance
with inspiration provenance.

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `2.3.0`. **Source:** [plugin.toml](<../../plugins/office/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | None |
| Direct external | None |
| Local closure (1) | [office](<office.md>) |
| External closure (0) | None |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `repository.read`, `repository.write`, `shell.execute`, `network.fetch`, `contexts.isolate`, `roles.dispatch`.
**Optional capabilities:** None.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `office:intake` | Shared contextual interview for every Office workflow: resolve where the work starts, how much it changes and what is delivered, then pick the route the format method executes. TRIGGER WHEN: an Office presentation, document or workbook task begins. DO NOT TRIGGER WHEN: a format method is already executing a resolved route. | [intake](<../../plugins/office/skills/intake/SKILL.md>) |
| Skill | `office:design` | Shared visual design method for Office documents and presentations: one direction for composition, rhythm and type; an ad hoc palette built from the user's colour source and chosen from candidates in the browser; the argument mode, editorial hierarchy, typography, and font fetching, installation and embedding. TRIGGER WHEN: an Office intake resolved the substantial route for a Word document or PowerPoint deck. DO NOT TRIGGER WHEN: the route is narrow or read-only, or the deliverable is a website, a workbook or a standalone image. | [design](<../../plugins/office/skills/design/SKILL.md>) |
| Skill | `office:pptx` | Coordinate presentation art direction, editable construction and independent rendered review through creative specialists. TRIGGER WHEN: creating, redesigning or editing a PPTX, reusable presentation template or branded deck. DO NOT TRIGGER WHEN: the deliverable is a website or a standalone image. | [pptx](<../../plugins/office/skills/pptx/SKILL.md>) |
| Skill | `office:slidepoise` | Create and revise professional, editable PowerPoint presentations through the external SlidePoise framework, with visual design, native reconstruction and rendered review. TRIGGER WHEN: the user asks for a PPTX, pitch deck, consulting presentation, branded slides, a presentation from research or a workbook, or SlidePoise. Targeted edits and PDF export use office:deckcraft. DO NOT TRIGGER WHEN: the requested deliverable is only an Excel workbook (use office:xlsx) or an image without an editable presentation. | [slidepoise](<../../plugins/office/skills/slidepoise/SKILL.md>) |
| Skill | `office:deckcraft` | Create, inspect, edit, render and export PPTX through the external DeckCraft runtime, preserving sources and checking native-feature losses. TRIGGER WHEN: direct native PowerPoint construction, targeted PPTX changes, slide previews, printable PDF or DeckCraft. DO NOT TRIGGER WHEN: a new creative deck uses SlidePoise reconstruction or only a spreadsheet or document is requested. | [deckcraft](<../../plugins/office/skills/deckcraft/SKILL.md>) |
| Skill | `office:wordcraft` | Create, edit, inspect, render and export real editable Word documents through the external WordCraft CLI or exposed MCP interface. TRIGGER WHEN: producing DOCX from an accepted design, native Word changes or WordCraft rendering/PDF. DO NOT TRIGGER WHEN: only a design brief or read-only package inspection is needed. | [wordcraft](<../../plugins/office/skills/wordcraft/SKILL.md>) |
| Skill | `office:xlsx` | Create, edit, inspect and analyze native Excel (.xlsx) workbooks with editable formulas, tables, charts and formatting. TRIGGER WHEN: creating, editing, inspecting or analyzing Excel (.xlsx) workbooks or tabular models. DO NOT TRIGGER WHEN: Word documents (use office:docx) or presentations (use office:presentation). | [xlsx](<../../plugins/office/skills/xlsx/SKILL.md>) |
| Skill | `office:docx` | Create, read and edit native Word (.docx) documents with styles, page layouts, tables and images while preserving existing features. TRIGGER WHEN: creating, reading, editing or formatting Word (.docx) documents or templates. DO NOT TRIGGER WHEN: spreadsheets (use office:xlsx) or presentations (use office:presentation). | [docx](<../../plugins/office/skills/docx/SKILL.md>) |
| Role | `office:presentation-designer` | Develop presentation art direction and slide composition from a supplied brief, sources and brand assets. Return design instructions and image requests without modifying the presentation. | [presentation-designer](<../../plugins/office/roles/presentation-designer.md>) |
| Role | `office:presentation-reviewer` | Independently inspect presentation renders, source fidelity, native editability evidence and preservation deltas. Return a review bound to the exact candidate, or to the unchanged source deck on a read-only review, without editing it. | [presentation-reviewer](<../../plugins/office/roles/presentation-reviewer.md>) |
| Role | `office:document-designer` | Design editable Word documents from a supplied brief and shared theme. Return page layouts, reusable template instructions, native style mappings and image requests without modifying the document. | [document-designer](<../../plugins/office/roles/document-designer.md>) |
| Role | `office:document-reviewer` | Independently inspect Word document renders, source fidelity, native structure evidence and preservation deltas. Return a review bound to the exact candidate, or to the unchanged source document on a read-only review, without editing it. | [document-reviewer](<../../plugins/office/roles/document-reviewer.md>) |
| Workflow | `office:presentation` | Create, derive, revise, review or export an editable PowerPoint presentation with creative specialists, SlidePoise generation and DeckCraft editing, preview and PDF export. TRIGGER WHEN: the user requests a PPTX, presentation template, pitch deck or consulting deck, or a change, review or export of an existing presentation. | [presentation](<../../plugins/office/workflows/presentation.md>) |
| Workflow | `office:document` | Create, derive, revise, review or export a native Word document with professional styles, tables, headers, footers and page layouts. TRIGGER WHEN: the user requests DOCX work, a Word report, proposal, letter or template, or a change, review or export of an existing document. | [document](<../../plugins/office/workflows/document.md>) |
| Workflow | `office:workbook` | Create, derive, revise or analyze a native Excel workbook while preserving its formulas, formatting, tables, charts and other required features. TRIGGER WHEN: the user requests XLSX work, spreadsheet analysis, a model, a tracker or a dashboard, or a change or review of an existing workbook. | [workbook](<../../plugins/office/workflows/workbook.md>) |

### Workflow contracts

Contracts describe observable outputs; Markdown bodies define decisions,
flags, safety gates and execution. Declared `invoke` execution is unsupported.

#### `office:presentation`

**Arguments:** <code>&lt;brief &#124; source files &#124; existing presentation and requested change&gt;</code>

| Contract | Value |
|---|---|
| Inputs | `presentation-task`, `source-material` |
| Outcomes | `presentation-task-completed` |
| Artifacts | `presentation-result`, `presentation-review` |
| Schemas | None declared |
| Declared workers | `office/presentation-designer`, `office/presentation-reviewer` |
| Composed worker isolation | Required |
| Task-specific isolated workers | Not declared |
| Sidecar | [presentation.toml](<../../plugins/office/workflows/presentation.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `run` | None | None | `shared` | None declared | `forbidden` |

#### `office:document`

**Arguments:** <code>&lt;brief &#124; source files &#124; existing document and requested change&gt;</code>

| Contract | Value |
|---|---|
| Inputs | `document-task`, `source-material` |
| Outcomes | `document-task-completed` |
| Artifacts | `document-result`, `document-review` |
| Schemas | None declared |
| Declared workers | `office/document-designer`, `office/document-reviewer` |
| Composed worker isolation | Required |
| Task-specific isolated workers | Not declared |
| Sidecar | [document.toml](<../../plugins/office/workflows/document.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `run` | None | None | `shared` | None declared | `forbidden` |

#### `office:workbook`

**Arguments:** <code>&lt;brief &#124; source files &#124; existing workbook and requested change&gt;</code>

| Contract | Value |
|---|---|
| Inputs | `workbook-task`, `source-material` |
| Outcomes | `workbook-task-completed` |
| Artifacts | `workbook-result`, `workbook-review` |
| Schemas | None declared |
| Declared workers | None |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [workbook.toml](<../../plugins/office/workflows/workbook.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `run` | None | None | `shared` | None declared | `preferred` |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/office](<../../exports/claude/plugins/office>) | `native` | `presentation: serial-isolated`, `document: serial-isolated`, `workbook: native-team` |
| copilot | [exports/copilot/plugins/office](<../../exports/copilot/plugins/office>) | `native` | `presentation: serial-isolated`, `document: serial-isolated`, `workbook: parallel-subagents` |
| codex | [exports/codex/plugins/office](<../../exports/codex/plugins/office>) | `adapted` | `presentation: serial-isolated`, `document: serial-isolated`, `workbook: parallel-subagents` |
| pi | [exports/pi/plugins/office](<../../exports/pi/plugins/office>) | `adapted` | `presentation: serial-isolated`, `document: serial-isolated`, `workbook: parallel-subagents` |
| opencode | [exports/opencode/plugins/office](<../../exports/opencode/plugins/office>) | `native` | `presentation: serial-isolated`, `document: serial-isolated`, `workbook: parallel-subagents` |

<!-- daodan:reference:end -->
