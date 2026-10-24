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

# Word document composition and template handoff

Use this reference for a new document or substantial restyling. The
`office:document-designer` role designs page composition; `office:docx` retains
engine selection, native construction, preservation and verification. A narrow
edit or read-only task does not start this design phase.

Carry the `office:design` record (direction, chosen palette by role, pairing,
argument mode) into the document design report. A supplied brand/template is
direction `H`, not a reason to choose a competing palette. Use the same palette
roles and font families when the task also produces a deck.
Document-specific point sizes, line lengths and page flow remain format choices.

## Choose the reading architecture

These are composition recipes, not binary templates. Select by content and
combine only the page types the brief needs. Name the recipe and any variation
in the existing brief; retain the supplied template when editing.

| Recipe | Sequence and visual treatment | Native construction |
|---|---|---|
| Decision memo | Decision at the top; compact context, evidence, alternatives and next action | One main column, native headings and lists; a short conclusion panel if useful |
| Evidence report | Short opening, findings, supporting figures, limitations and references | Consistent body-page styles; optional contents for a long report; captioned figures and repeatable data tables |
| Project proposal | Reader's need, approach, deliverables, schedule, commercial terms and decision | Distinct section openings, editable schedule/pricing tables and a clear final action |
| Reference handbook | Orientation, stable numbered topics, examples and troubleshooting | Heading hierarchy, navigation fields when supported, native code/example styles and explicit notes |
| Periodical briefing | Lead story, supporting items, selected quotation and related material | Optional section columns with a defined gutter; reading order remains explicit |
| Image-led dossier | Short introduction, captioned evidence plates, interpretation and index | Proportional native image objects, selectable captions and controlled page/section breaks |

Adjust tone without replacing the shared theme. An analytical treatment puts the
claim beside evidence; an essay favors continuous reading; a workshop treatment
uses prompts and writable space; a gallery favors image/caption associations.
These are layout decisions rather than another catalog of competing palettes.

## Cover and opening patterns

| Pattern | Composition | Suitable use |
|---|---|---|
| Typographic opening | Title, concise framing sentence, author/date/version and ample open space | Memo, reference guide or restrained report |
| Image with title band | One crop with a separate native title area and metadata | Proposal, portfolio or narrative report |
| Aligned side marker | A narrow accent beside a title block, aligned with later headings | Branded report or recurring publication |
| Direct-entry first page | Running title and brief metadata immediately followed by the recommendation | Short documents where a separate cover delays reading |

Use paragraph/section settings and supported native image objects. Do not assume
Word supports browser overlays, full-bleed printing or floating-object placement
with identical behavior across engines. Keep essential text native and readable.

## Reusable page and block patterns

The design report includes a small wireframe for each chosen page type. For
example, an evidence page may use this arrangement:

```text
[ running header                         page number ]
[ section heading                                     ]
[ lead / conclusion                                   ]
[ figure or native data table                         ]
[ caption and source                                  ]
[ interpretation, limits and next reading point        ]
[ footer / document identity                          ]
```

A text-led page may put a short key point between paragraphs. A comparison page
uses a labeled table with the same criteria for each option. A dashboard page
groups a few sourced metrics before their interpretation; labels, units and
periods remain visible. A closing page states the action and useful reference
material. Never add a callout, quotation, sidebar or KPI panel solely to fill space.

For a sidebar, prefer a supported native section-column arrangement when the
reading order works; otherwise use an inline callout near its related paragraph.
Use paragraph shading/borders for callouts when supported. Keep layout tables
out of normal reading flow where they would damage accessibility or pagination.
Keep quotations exact, attributed and associated with the argument.

## Table patterns

| Pattern | Use | Required detail |
|---|---|---|
| Ruled evidence | Research, financial or technical data | Strong header distinction, restrained horizontal rules, numeric alignment and units |
| Banded comparison | Many comparable rows that need tracking | Consistent row tint, readable header contrast and no color-only meaning |
| Grouped summary | Short options, deliverables or schedule summary | Clear row groups, explicit criteria and a visible recommendation only when justified |

Set a width budget: available width equals page width minus left/right margins
and any gutter. Column widths must fit that budget, including table indentation
and cell spacing. Specify header repetition and row-splitting behavior. Permit
long tables to continue legibly rather than shrinking type or forcing every row
onto one page. Use actual data and real native cells.

## Construction handoff

Return these decisions in one assigned document design report:

| Field | Concrete instruction |
|---|---|
| Identity | Content/source version, target DOCX, brief and shared theme name/origin |
| Page geometry | Page size/orientation, units, margins and usable width; section changes and columns/gutter where needed |
| Page types | Chosen recipes and wireframes, block order and representative content; explain intentional variation |
| Styles | Native paragraph/character style names or existing IDs and inheritance; title/headings/body/captions/quotes/table roles mapped to shared theme tokens |
| Flow | Keep-with-next, widow/orphan behavior, paragraph spacing, intentional page/section breaks and rules for content growth |
| Tables and figures | Widths, headers, alignment, captions/sources, native representation, image proportions/crop and reading order |
| Furniture | Headers, footers, first-page variants, page-number fields and navigation/reference update needs |
| Template reuse | Editable exemplar blocks, replacement instructions and supported growth; DOTX status only if demonstrated |
| Build and review | Selected engine capabilities, image requests, preservation constraints, representative page checks and unresolved decisions |

Point sizes and widths must be concrete for the selected content and engine, not
copied as universal constants. Regions in a wireframe express layout intent;
flowing DOCX text still needs actual pagination. Do not promise fixed page counts
or pixel fidelity from this plan. Render and inspect the actual saved DOCX under
the producing method; record font substitutions and any unverified features.

## Provenance

This is original Office guidance informed by the composition concepts in
[Word Document Design Agent](https://github.com/tivojn/Office/tree/303e55d42a71aca4bc1dffdb49f6c1f090889899/Word),
revision `303e55d42a71aca4bc1dffdb49f6c1f090889899`. Its root and Word README declare
MIT, but the inspected repository supplies no complete license/copyright text.
No upstream wording, code, numeric presets or template files are redistributed
here. The ideas consulted include page-type planning, covers, callouts, quotations,
metric summaries and table treatment. The macOS automation, image provider,
installation steps and mandatory decoration/interaction rules are not adopted.
This original reference is not a copied-source sync target.
