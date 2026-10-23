# Office

Create professional editable PowerPoint presentations and work directly with
native Excel workbooks and Word documents. The plugin has complementary skills
and explicit workflow entries:

| Task | Skill | Workflow |
|---|---|---|
| Design a deck or reusable presentation | `office:presentation-design`, `office:slidepoise` | `office:create-presentation` |
| Edit, preview or export PPTX to PDF | `office:deckcraft` | `office:create-presentation` |
| Create, inspect, analyze or edit XLSX | `office:xlsx` | `office:workbook` |
| Create, read or edit DOCX | `office:docx` | `office:document` |

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
`pi-subagents` supplies the isolated workers required by the presentation workflow.
OpenCode V2 installs the generated package:

```text
opencode plugin add 'github:acaprino/shinatama#v<published-version>::path:exports/opencode'
```

Its plugin configuration can select `"options": { "plugins": ["office"] }`.
Pi and OpenCode do not install foreign marketplace providers automatically. Those
skills must be provisioned separately in a form their host can load. See the
[host guide](../hosts.md#installation-and-selection) for package selection and
worker mechanisms; the Office repository and marketplace identity are the ones
shown above.

## Dependencies and runtime requirements

Plugin dependencies, external executables and host tools are different
requirements. Installing Office does not install SlidePoise, DeckCraft, image
tools or Office applications.

### Declared plugin dependencies

The [manifest](../../plugins/office/plugin.toml) declares the creative providers as
optional; the enforced hard requirement for Impeccable, Frontend Design and
`ui-ux-pro-max` lives in
[frontend-review](../../plugins/frontend-review/plugin.toml), which refuses to run
without them. Office has no required plugin dependencies:

| Provider | Status in the manifest | Used for |
|---|---|---|
| `frontend-design@claude-plugins-official` | Optional | Visual direction in the designer's report |
| `impeccable@impeccable` | Optional | Visual guidance in design and independent review |
| `taste-skill@taste-skill` | Optional | Art direction and critique adapted to fixed, editable slides |

Office caps consultation at **two providers per run**, one per worker role, so the
same advice is not loaded twice: a designer takes either Frontend Design or Taste
for direction, and a reviewer takes either Impeccable or Taste for critique. The
cap and the role split are normative in the
[creative-provider contract](../../plugins/office/skills/presentation-design/references/creative-providers.md).
Office's own [slide design library](../../plugins/office/skills/presentation-design/references/design-library.md)
supplies directions, palettes, type scale and slide archetypes and needs no
external provider at all.

Provider sources and supported installation routes are documented by
[Frontend Design](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/frontend-design),
[Impeccable](https://impeccable.style/docs/) and
[Taste](https://github.com/Leonxlnx/taste-skill). On Claude Code, their marketplace
registration and plugin commands are:

```text
claude plugin marketplace add anthropics/claude-plugins-official
claude plugin install frontend-design@claude-plugins-official
claude plugin marketplace add pbakaus/impeccable
claude plugin install impeccable@impeccable
claude plugin marketplace add Leonxlnx/taste-skill
claude plugin install taste-skill@taste-skill
```

Use the active host's supported provider distribution and installation mechanism
on other hosts. A Claude marketplace command is not a portable installation
command, and adding Office alone does not prove a provider is available.

These providers are not technical dependencies of SlidePoise or DeckCraft. Select
the useful available providers for the brief. Without them, Office
uses its presentation criteria and the selected engine's guidance. Designer and
independent reviewer deliveries remain required where the method calls for them.
The coordinator passes the selected providers to workers, which explicitly load
their actual skills and record what they consulted. It does not install missing
providers automatically. If the user explicitly requires an unavailable provider,
the result reports that contribution as unfulfilled and gives the host's setup
route, while independent work continues.
The [creative-provider contract](../../plugins/office/skills/presentation-design/references/creative-providers.md)
explains the limited use of their web-design guidance for presentations.
Taste is consulted as a design reference; Office does not execute its website
scripts or browser workflow. Reading that guidance does not require Taste's
Node/browser runtime or establish PPTX support in Taste itself.

### Required when the operation needs them

| Requirement | When needed | How it is supplied |
|---|---|---|
| Python for Office helpers | Package inspection, comparison and runtime bridges | An available Python executable; inspectors use the standard library |
| SlidePoise runtime | New creative decks, reusable exemplar decks and substantial redesign | External runtime; [pinned setup](../../plugins/office/skills/slidepoise/references/runtime.md) requires Python 3.10+, Node.js 18+ and npm 9+, plus its reconstruction packages |
| DeckCraft CLI or exposed native MCP tools | The DeckCraft editing, preview or PDF path | External executable; [runtime setup](../../plugins/office/skills/deckcraft/references/runtime.md) documents version discovery and supported operations |
| Harness image-generation tool | Generating or editing imagery | An actual tool exposed in the executing context; no separate API-key script is an automatic substitute |
| Image inspection and compatible presentation renderer | Visual approval of a presentation | Host image-reading capability and actual renders; SlidePoise setup supports LibreOffice and Poppler, while DeckCraft has its own renderer |
| Required fonts | Rendering text with the intended appearance | Fonts available to the selected runtime |
| Isolated worker dispatch | Coordinated presentation design and review | Host subagent mechanism, including Pi's companion package |
| Compatible workbook/document engine | Writing XLSX or DOCX | A suitable host artifact runtime or another compatible engine; `openpyxl` and `python-docx` are alternatives for supported features, not universally required packages |
| Calculation, field-update or document-rendering engine | Recalculated formulas, refreshed Word fields or reviewed document pages | An engine that actually performs the requested operation; package inspection cannot do it |

A text-only PPTX edit needs no image-generation call. A SlidePoise-only operation
does not require DeckCraft. A preview-only operation does not need SlidePoise or a
resaved PPTX. Source files and previous candidates are preserved.

### Optional integrations

| Integration | Status and purpose |
|---|---|
| DeckCraft native MCP interface | Optional alternative to CLI transport; the host must register and expose it |
| DeckCraft desktop application | Optional visual editor or shared desktop session; headless CLI operations do not need it |
| SlidePoise Console/session panel | Optional when supported by the host |
| Microsoft Office applications | Optional for basic headless operations; target-application fidelity checks, live application control or physical printing require the corresponding application/interface |

Optional integrations do not replace a missing capability required by the chosen
operation. Missing rendering means an unreviewed output, not visual approval.

## Commands and usage

Workflow entries coordinate the task. Skills provide methods, while the designer
and reviewer are workers dispatched by the presentation coordinator.
You can add `Use Frontend Design for art direction`, `Use Impeccable for visual
critique`, `Use Taste for art direction within native PowerPoint constraints`, or
`Use the base Office method without external creative providers` to a presentation
brief. There is no requirement to enable every creative skill.

| Host | Presentations: create, edit, preview or PDF | Excel | Word |
|---|---|---|---|
| Claude Code | `/office:create-presentation` | `/office:workbook` | `/office:document` |
| Codex | `create-presentation-workflow` skill | `workbook-workflow` skill | `document-workflow` skill |
| GitHub Copilot | Select the `create-presentation-coordinator` agent; `create-presentation.prompt.md` is the entry prompt | `workbook.prompt.md` | `document.prompt.md` |
| Pi | `/office-create-presentation` | `/office-workbook` | `/office-document` |
| OpenCode V2 | `/office:create-presentation` | `/office:workbook` | `/office:document` |

On Codex, invoke the workflow skill from the skill picker or name it in the
request. On Copilot, use the coordinator for isolated presentation dispatch; the
prompt by itself does not establish that its worker harness is active. Do not
invoke a role name as though it were a workflow or shell command.

Examples below use Claude/OpenCode entry names. On another host, select the
corresponding entry above and keep the same request:

```text
/office:create-presentation Create an eight-slide Italian leadership deck from brief.docx and figures.xlsx. Use our brand assets, generate imagery with the harness tool where useful, and deliver editable PPTX plus a reviewed PDF.

/office:create-presentation Create a reusable editable exemplar deck with cover, section divider, comparison, data and conclusion layouts, plus short reuse instructions.

/office:create-presentation In quarterly.pptx, update slide 3 with the figures from actuals.xlsx. Preserve other content and formatting, retain native chart data, and save a separate candidate with previews.

/office:create-presentation Export quarterly.pptx to a printable PDF and PNG previews. Preserve the source, include hidden slides in the previews, and exclude them from the PDF.

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

The coordinator dispatches a presentation designer for creative work and an
independent reviewer for the rendered result. When selected and available, they
consult the canonical Frontend Design, Impeccable and Taste skills for transferable
visual guidance. Those optional providers
primarily target web UI; Office uses their typography, composition and critique
criteria without claiming their full application workflows implement PPTX.
The designer produces a direction and image requests, the reviewer produces
candidate-bound findings, and the coordinator owns deck writes and repairs.

All creative guidance follows the [PPTX compatibility contract](../../plugins/office/skills/presentation-design/references/pptx-compatibility.md)
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
are structural evidence, not a fidelity verdict.

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

SlidePoise is MIT-licensed; DeckCraft is dual MIT OR Apache-2.0. The creative
providers are optional here and remain separately installed; where Shinatama
already carries them as hard requirements
([frontend-review](<frontend-review.md>)) their absence is an installation failure
there, not here. No provider is copied into Office. This integration is locally
authored and delegates
to upstream owners; no new upstream source or template library is redistributed.

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `1.3.0`. **Source:** [plugin.toml](<../../plugins/office/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | None |
| Direct external | None |
| Local closure (1) | [office](<office.md>) |
| External closure (0) | None |

### Optional external providers

`frontend-design@claude-plugins-official`, `impeccable@impeccable`, `taste-skill@taste-skill`.

These providers are outside the required dependency closure. Their absence
does not block the base workflow; consult the method for selection and scope.

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
| Skill | `office:presentation-design` | Coordinate presentation art direction, editable construction and independent rendered review through creative specialists. TRIGGER WHEN: creating, redesigning or editing a PPTX, reusable presentation template or branded deck. DO NOT TRIGGER WHEN: the deliverable is a website or a standalone image. | [presentation-design](<../../plugins/office/skills/presentation-design/SKILL.md>) |
| Skill | `office:slidepoise` | Create and revise professional, editable PowerPoint presentations through the external SlidePoise framework, with visual design, native reconstruction and rendered review. TRIGGER WHEN: the user asks for a PPTX, pitch deck, consulting presentation, branded slides, a presentation from research or a workbook, or SlidePoise. Targeted edits and PDF export use office:deckcraft. DO NOT TRIGGER WHEN: the requested deliverable is only an Excel workbook (use office:xlsx) or an image without an editable presentation. | [slidepoise](<../../plugins/office/skills/slidepoise/SKILL.md>) |
| Skill | `office:deckcraft` | Create, inspect, edit, render and export PPTX through the external DeckCraft runtime, preserving sources and checking native-feature losses. TRIGGER WHEN: direct native PowerPoint construction, targeted PPTX changes, slide previews, printable PDF or DeckCraft. DO NOT TRIGGER WHEN: a new creative deck uses SlidePoise reconstruction or only a spreadsheet or document is requested. | [deckcraft](<../../plugins/office/skills/deckcraft/SKILL.md>) |
| Skill | `office:xlsx` | Create, edit, inspect and analyze native Excel (.xlsx) workbooks with editable formulas, tables, charts and formatting. TRIGGER WHEN: creating, editing, inspecting or analyzing Excel (.xlsx) workbooks or tabular models. DO NOT TRIGGER WHEN: Word documents (use office:docx) or presentations (use office:slidepoise). | [xlsx](<../../plugins/office/skills/xlsx/SKILL.md>) |
| Skill | `office:docx` | Create, read and edit native Word (.docx) documents with styles, page layouts, tables and images while preserving existing features. TRIGGER WHEN: creating, reading, editing or formatting Word (.docx) documents or templates. DO NOT TRIGGER WHEN: spreadsheets (use office:xlsx) or presentations (use office:slidepoise). | [docx](<../../plugins/office/skills/docx/SKILL.md>) |
| Role | `office:presentation-designer` | Develop presentation art direction and slide composition from a supplied brief, sources and brand assets. Return design instructions and image requests without modifying the presentation. | [presentation-designer](<../../plugins/office/roles/presentation-designer.md>) |
| Role | `office:presentation-reviewer` | Independently inspect presentation renders, source fidelity, native editability evidence and preservation deltas. Return a candidate-bound review without editing the deck. | [presentation-reviewer](<../../plugins/office/roles/presentation-reviewer.md>) |
| Workflow | `office:create-presentation` | Create, redesign or edit editable PowerPoint with creative specialists, SlidePoise generation and DeckCraft editing, preview and PDF export. TRIGGER WHEN: the user requests a PPTX, presentation template, pitch deck, consulting deck or changes to an existing presentation. | [create-presentation](<../../plugins/office/workflows/create-presentation.md>) |
| Workflow | `office:workbook` | Create, inspect, analyze or edit a native Excel workbook while preserving its formulas, formatting, tables, charts and other required features. TRIGGER WHEN: the user requests XLSX work, spreadsheet analysis, a model, a tracker, a dashboard or a controlled revision to an existing workbook. | [workbook](<../../plugins/office/workflows/workbook.md>) |
| Workflow | `office:document` | Create, read or edit native Word documents with professional styles, tables, headers, footers and page layouts. TRIGGER WHEN: the user requests DOCX work, a Word report, proposal, letter, template or controlled document revision. | [document](<../../plugins/office/workflows/document.md>) |

### Workflow contracts

Contracts describe observable outputs; Markdown bodies define decisions,
flags, safety gates and execution. Declared `invoke` execution is unsupported.

#### `office:create-presentation`

**Arguments:** <code>&lt;brief &#124; source files &#124; existing presentation and requested revision&gt;</code>

| Contract | Value |
|---|---|
| Inputs | `presentation-brief`, `source-material` |
| Outcomes | `editable-presentation-delivered` |
| Artifacts | `editable-presentation`, `presentation-review` |
| Schemas | None declared |
| Declared workers | `office/presentation-designer`, `office/presentation-reviewer` |
| Composed worker isolation | Required |
| Task-specific isolated workers | Not declared |
| Sidecar | [create-presentation.toml](<../../plugins/office/workflows/create-presentation.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `run` | None | None | `shared` | None declared | `forbidden` |

#### `office:workbook`

**Arguments:** <code>&lt;workbook task &#124; source files &#124; existing workbook and requested changes&gt;</code>

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

#### `office:document`

**Arguments:** <code>&lt;document task &#124; source files &#124; existing document and requested changes&gt;</code>

| Contract | Value |
|---|---|
| Inputs | `document-task`, `source-material` |
| Outcomes | `document-task-completed` |
| Artifacts | `document-result`, `document-review` |
| Schemas | None declared |
| Declared workers | None |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [document.toml](<../../plugins/office/workflows/document.toml>) |

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
| claude | [exports/claude/plugins/office](<../../exports/claude/plugins/office>) | `native` | `create-presentation: serial-isolated`, `workbook: native-team`, `document: native-team` |
| copilot | [exports/copilot/plugins/office](<../../exports/copilot/plugins/office>) | `native` | `create-presentation: serial-isolated`, `workbook: parallel-subagents`, `document: parallel-subagents` |
| codex | [exports/codex/plugins/office](<../../exports/codex/plugins/office>) | `adapted` | `create-presentation: serial-isolated`, `workbook: parallel-subagents`, `document: parallel-subagents` |
| pi | [exports/pi/plugins/office](<../../exports/pi/plugins/office>) | `adapted` | `create-presentation: serial-isolated`, `workbook: parallel-subagents`, `document: parallel-subagents` |
| opencode | [exports/opencode/plugins/office](<../../exports/opencode/plugins/office>) | `native` | `create-presentation: serial-isolated`, `workbook: parallel-subagents`, `document: parallel-subagents` |

<!-- daodan:reference:end -->
