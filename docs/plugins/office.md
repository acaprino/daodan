# Office

Create professional editable PowerPoint presentations and work directly with
native Excel workbooks and Word documents. The plugin has complementary skills
and explicit workflow entries:

| Task | Skill | Workflow |
|---|---|---|
| Create or revise a PPTX | `office:slidepoise` | `office:create-presentation` |
| Create, inspect, analyze or edit XLSX | `office:xlsx` | `office:workbook` |
| Create, read or edit DOCX | `office:docx` | `office:document` |

## Presentations

SlidePoise explores visual compositions with image generation and reconstructs
selected designs into editable PowerPoint text, charts, tables, shapes and
connectors. Photographs and illustrations can remain separate image objects.
Daodan owns the integration and delivery contract; the framework, its construction
schemas and its design method remain in the external
[SlidePoise repository](https://github.com/henryhyw/slidepoise).

Install the pinned runtime using the [runtime reference](../../plugins/office/skills/slidepoise/references/runtime.md).
It requires Python, Node/npm, image generation and inspection, suitable fonts and
a PowerPoint preview renderer. Daodan does not copy the framework or install it
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

The compiler distributes the skills, helpers and workflows to all five Daodan
hosts. Runtime prerequisites are documented tool requirements, not invented
marketplace dependencies. A packaged integration does not establish live image
generation, rendering, Office application control or end-to-end behavior on every host.
Native document work means editing actual file content and objects; controlling
a live Microsoft Office application requires an available application interface.

The upstream project is MIT-licensed. This plugin is locally authored and delegates
to it, so no upstream source or reference library is redistributed here.

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `1.1.0`. **Source:** [plugin.toml](<../../plugins/office/plugin.toml>).

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

**Required capabilities:** `repository.read`, `repository.write`, `shell.execute`, `network.fetch`.
**Optional capabilities:** None.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `office:slidepoise` | Create and revise professional, editable PowerPoint presentations through the external SlidePoise framework, with visual design, native reconstruction and rendered review. TRIGGER WHEN: the user asks for a PPTX, pitch deck, consulting presentation, branded slides, a presentation from research or a workbook, or SlidePoise. DO NOT TRIGGER WHEN: the requested deliverable is only an Excel workbook (use office:xlsx) or an image without an editable presentation. | [slidepoise](<../../plugins/office/skills/slidepoise/SKILL.md>) |
| Skill | `office:xlsx` | Create, edit, inspect and analyze native Excel workbooks with editable formulas, tables, charts and professional formatting. Preserve existing workbook features, verify calculated results with a compatible engine and disclose unsupported fidelity. | [xlsx](<../../plugins/office/skills/xlsx/SKILL.md>) |
| Skill | `office:docx` | Create, read and edit native Word documents with professional styles, page layouts, tables, images and editable text. Preserve existing document features, select a compatible engine for advanced content and verify saved document pages. | [docx](<../../plugins/office/skills/docx/SKILL.md>) |
| Workflow | `office:create-presentation` | Create or revise a professional editable PowerPoint through SlidePoise, with source-grounded content, visual composition, native reconstruction and rendered review. TRIGGER WHEN: the user requests a PPTX, pitch deck, consulting deck or presentation from documents, research or a workbook. | [create-presentation](<../../plugins/office/workflows/create-presentation.md>) |
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
| Declared workers | None |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [create-presentation.toml](<../../plugins/office/workflows/create-presentation.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `run` | None | None | `shared` | None declared | `preferred` |

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
| claude | [exports/claude/plugins/office](<../../exports/claude/plugins/office>) | `native` | `create-presentation: native-team`, `workbook: native-team`, `document: native-team` |
| copilot | [exports/copilot/plugins/office](<../../exports/copilot/plugins/office>) | `native` | `create-presentation: parallel-subagents`, `workbook: parallel-subagents`, `document: parallel-subagents` |
| codex | [exports/codex/plugins/office](<../../exports/codex/plugins/office>) | `adapted` | `create-presentation: parallel-subagents`, `workbook: parallel-subagents`, `document: parallel-subagents` |
| pi | [exports/pi/plugins/office](<../../exports/pi/plugins/office>) | `adapted` | `create-presentation: parallel-subagents`, `workbook: parallel-subagents`, `document: parallel-subagents` |
| opencode | [exports/opencode/plugins/office](<../../exports/opencode/plugins/office>) | `native` | `create-presentation: parallel-subagents`, `workbook: parallel-subagents`, `document: parallel-subagents` |

<!-- daodan:reference:end -->
