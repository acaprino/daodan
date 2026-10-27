# office

Word, PowerPoint and Excel file design, creation, editing and verification.

## Documentazione Office

Office realizza e verifica file Word, PowerPoint ed Excel modificabili. Parti
dalla funzione che ti serve o da un esempio d'uso; le pagine di manutenzione
raccolgono separatamente struttura, contributi esterni e licenze.

### Usare il plugin

| Pagina | Trovi qui |
|---|---|
| [Funzioni e ingressi](office/functions.md) | Che cosa puoi chiedere e quale ingresso scegliere |
| [Esempi d'uso](office/examples.md) | Richieste complete, materiali, file attesi e controlli del risultato |
| [Intake del lavoro e percorso](office/workflow.md) | Brief, contenuto, design, composizione e consegna |
| [Dipendenze e runtime](office/dependencies.md) | Prerequisiti, capacità dell'host e recupero delle dipendenze mancanti |
| [Verifiche e limiti](office/verification.md) | Cosa provano record, inspector, render, test e benchmark |

### Mantenere il plugin

| Pagina | Trovi qui |
|---|---|
| [Struttura e responsabilità](office/structure.md) | Kernel, skill, ruoli, contratti e confini fra formati |
| [Intake di componenti esterni](office/upstream-intake.md) | Valutazione di una nuova capacità, perimetro e condizioni di adozione |
| [Aggiornamenti upstream](office/upstream-updates.md) | Revisione dei contributi già registrati e preservazione del metodo locale |
| [Fonti e licenze](office/licenses.md) | Provenienza, termini conservati, runtime, font e asset |

Le pagine descrivono i contratti presenti nelle fonti. Gli esempi sono
illustrativi e le verifiche non eseguite restano esplicite. L'inventario dei
componenti e delle dipendenze rimane nel riferimento generato in fondo.

## Install Office

**Install:** `daodan@daodan` includes Office. Select `office@daodan` alone for its
methods and roles; the seven command entries belong to `daodan@daodan`.

| | |
|---|---|
| **Entries** | `/daodan:start`, `/daodan:presentation`, `/daodan:document`, `/daodan:workbook`, `/daodan:verify`, `/daodan:fix`, `/daodan:theme` |
| **Roles** | office:content-strategist, office:presentation-designer, office:presentation-reviewer, office:document-designer, office:document-reviewer |
| **Skills** | office:intake, office:content, office:design, office:pptx, office:deckcraft, office:wordcraft, office:gridcraft, office:xlsx, office:docx, office:integrity |
| **Dependencies** | work-controller, taste-skill@taste-skill |

Command examples and named tools in this guide use Claude notation. For other
hosts, use the entry points and bindings in the source-derived reference below
and [host setup](../hosts.md).

## What the plugin does

Design editable Word documents and presentations from one intake, a shared
editorial record and an ad hoc visual identity; construct and revise PPTX through DeckCraft or the bundled
HTML to PPTX conversion, DOCX through WordCraft,
and XLSX through GridCraft; verify and repair any of them with static integrity rules.

Use `/daodan:start` for a request that combines formats or starts with files,
notes and sources whose destination is not yet clear. Use the format entry when
the deliverable is known. The intake records the operation and remaining
decisions, then the format method preserves supplied files, constructs a separate
editable candidate and checks that saved result.

Office owns the methods, helpers and specialist roles. The `daodan` entry plugin
loads them through its required local dependency; Office declares no workflow
entries of its own. The kernel retains its subtree history from `acaprino/mukade`
and is maintained here as part of Daodan.

`office:content` binds sources, claims, permitted transformations and requested
DOCX/PPTX projections in `CONTENT.md`. `office:design` compares two or three
complete visual proposals using required Taste v2 knowledge within the existing
Office workflow. Format designers, native producers and reviewers first prove
the same representative real content in saved DOCX/PPTX specimens. A self-contained
HTML gallery shows those exact native renders. Explicit user or authorized autonomous
selection produces `DESIGN.md`. A combined delivery reuses both records.

Format designers own final composition through parallel `structure.md` and
`layout-patterns.md` references. Native styles/themes apply the accepted design;
separate DOTX/POTX files are optional unless reusable templates are requested.
Existing palette, font, template and inspection tools remain in their owners.
Local edits and read-only operations inherit accepted decisions. See the
[source and license index](../../plugins/office/README.md) for retained pins and
terms and the [Taste input/output boundary](../../plugins/office/skills/design/references/art-direction.md).

## Runtime requirements and evidence

Native construction and rendering require separately available DeckCraft,
WordCraft or GridCraft. The plugin supplies methods, transport and static
inspectors, not those engines, their installers or an MCP server. Follow the
runtime contract of [deckcraft](../../plugins/office/skills/deckcraft/references/runtime.md),
[wordcraft](../../plugins/office/skills/wordcraft/references/runtime.md) or
[gridcraft](../../plugins/office/skills/gridcraft/references/runtime.md) before
the first operation.

The bundled HTML to PPTX conversion is the one engine Office ships. It needs
Node `^20.19.0` or `>=22.12.0`, the Playwright Node module and a Chrome, Edge or
Chromium executable; `OFFICE_PPTX_NODE`, `OFFICE_PPTX_PLAYWRIGHT` and
`OFFICE_PPTX_BROWSER` override discovery. A missing prerequisite stops the
conversion with those recovery steps and is recorded, never replaced silently by
another construction path. Its input contract, evidence record and known losses
are in [html-to-pptx](../../plugins/office/skills/pptx/references/html-to-pptx.md),
its pin and notices in [UPSTREAM.md](../../plugins/office/skills/pptx/lib/open-slide-pptx/UPSTREAM.md).

Static integrity checks do not establish rendered fidelity, formula semantics or
full format conformance. The format methods require preservation comparisons and
independent review where specified, and report unavailable runtime or reviewer
evidence explicitly. A successful compiler build is separate from an installed
host executing an Office workflow.

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `3.5.2`. **Source:** [plugin.toml](<../../plugins/office/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | [work-controller](<work-controller.md>) |
| Direct external | `taste-skill@taste-skill` |
| Local closure (2) | [office](<office.md>), [work-controller](<work-controller.md>) |
| External closure (1) | `taste-skill@taste-skill` |

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
| Skill | `office:intake` | Shared Office intake: inspect materials, settle operation, requested formats, editorial/visual decisions and phase-specific dependencies in one brief and question round. Route mixed or unspecified deliverables before format work. | [intake](<../../plugins/office/skills/intake/SKILL.md>) |
| Skill | `office:content` | Shared editorial method for requested Word documents and PowerPoint decks: source and claim ledger, transformation permissions, logical sequence and format projections in a validated CONTENT.md. Use after Office intake; revisions inherit accepted decisions and local edits change only their scope. | [content](<../../plugins/office/skills/content/SKILL.md>) |
| Skill | `office:design` | Design a shared visual identity for requested Office documents and decks: Taste art direction, real native proposal comparison, explicit DESIGN.md selection, semantic palette, typography, imagery and native theme handoff. Use when intake calls for a new look; revisions inherit accepted decisions. | [design](<../../plugins/office/skills/design/SKILL.md>) |
| Skill | `office:pptx` | Coordinate presentation art direction, editable construction and independent rendered review through creative specialists. TRIGGER WHEN: creating, redesigning or editing a PPTX, reusable presentation template or branded deck. DO NOT TRIGGER WHEN: the deliverable is a website or a standalone image. | [pptx](<../../plugins/office/skills/pptx/SKILL.md>) |
| Skill | `office:deckcraft` | Create, inspect, edit, render and export PPTX through the external DeckCraft runtime, preserving sources and checking native-feature losses. TRIGGER WHEN: direct native PowerPoint construction, targeted PPTX changes, slide previews, printable PDF or DeckCraft. DO NOT TRIGGER WHEN: only a spreadsheet or document is requested. | [deckcraft](<../../plugins/office/skills/deckcraft/SKILL.md>) |
| Skill | `office:wordcraft` | Create, edit, inspect, render and export real editable Word documents through the external WordCraft CLI or exposed MCP interface. TRIGGER WHEN: producing DOCX from an accepted design, native Word changes or WordCraft rendering/PDF. DO NOT TRIGGER WHEN: only a design brief or read-only package inspection is needed. | [wordcraft](<../../plugins/office/skills/wordcraft/SKILL.md>) |
| Skill | `office:gridcraft` | Create, edit, inspect, calculate and check real Excel workbooks through the external GridCraft CLI or exposed MCP interface. TRIGGER WHEN: producing or editing XLSX for office:xlsx, recalculating formulas or checking workbook fidelity with GridCraft. DO NOT TRIGGER WHEN: only read-only package inspection is needed (use office:xlsx's inspector). | [gridcraft](<../../plugins/office/skills/gridcraft/SKILL.md>) |
| Skill | `office:xlsx` | Create, edit, inspect and analyze native Excel (.xlsx) workbooks with editable formulas, tables, charts and formatting. TRIGGER WHEN: creating, editing, inspecting or analyzing Excel (.xlsx) workbooks or tabular models. DO NOT TRIGGER WHEN: Word documents (use office:docx) or presentations (use /daodan:presentation). | [xlsx](<../../plugins/office/skills/xlsx/SKILL.md>) |
| Skill | `office:docx` | Create, read and edit native Word (.docx) documents with styles, page layouts, tables and images while preserving existing features. TRIGGER WHEN: creating, reading, editing or formatting Word (.docx) documents or templates. DO NOT TRIGGER WHEN: spreadsheets (use office:xlsx) or presentations (use /daodan:presentation). | [docx](<../../plugins/office/skills/docx/SKILL.md>) |
| Skill | `office:integrity` | Verify the integrity of a Word, PowerPoint or Excel file with static rules, then repair what can be repaired on a separate candidate. TRIGGER WHEN: checking a DOCX, PPTX or XLSX for broken links, formula errors, missing alternative text, inconsistent formulas, empty placeholders or other defects, or fixing them. DO NOT TRIGGER WHEN: creating a new document, deck or workbook (use the office document, presentation or workbook workflows). | [integrity](<../../plugins/office/skills/integrity/SKILL.md>) |
| Role | `office:content-strategist` | Build the shared editorial record for requested Word documents and PowerPoint decks: source/claim ledger, transformation permissions, logical sequence and full or delta native-format projections. Return assigned content artifacts without choosing visual identity, final composition or editing native files. | [content-strategist](<../../plugins/office/roles/content-strategist.md>) |
| Role | `office:presentation-designer` | Compose native proposal or final slides from assigned content and visual records. Return native object geometry, justified patterns and image requests without rewriting editorial strategy or modifying the presentation. | [presentation-designer](<../../plugins/office/roles/presentation-designer.md>) |
| Role | `office:presentation-reviewer` | Independently inspect presentation renders, source fidelity, native editability evidence and preservation deltas. Return a review bound to the exact candidate, or to the unchanged source deck on a read-only review, without editing it. | [presentation-reviewer](<../../plugins/office/roles/presentation-reviewer.md>) |
| Role | `office:document-designer` | Compose proposal or final Word pages from assigned content and visual records. Return page layouts, native style/flow mappings, growth rules and image requests without rewriting strategy or modifying the native document. | [document-designer](<../../plugins/office/roles/document-designer.md>) |
| Role | `office:document-reviewer` | Independently inspect Word document renders, source fidelity, native structure evidence and preservation deltas. Return a review bound to the exact candidate, or to the unchanged source document on a read-only review, without editing it. | [document-reviewer](<../../plugins/office/roles/document-reviewer.md>) |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/office](<../../exports/claude/plugins/office>) | `native` | No workflow entry points |
| copilot | [exports/copilot/plugins/office](<../../exports/copilot/plugins/office>) | `native` | No workflow entry points |
| codex | [exports/codex/plugins/office](<../../exports/codex/plugins/office>) | `adapted` | No workflow entry points |
| pi | [exports/pi/plugins/office](<../../exports/pi/plugins/office>) | `adapted` | No workflow entry points |
| opencode | [exports/opencode/plugins/office](<../../exports/opencode/plugins/office>) | `native` | No workflow entry points |

<!-- daodan:reference:end -->
