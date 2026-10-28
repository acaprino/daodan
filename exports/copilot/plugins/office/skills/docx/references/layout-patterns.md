<daodan_host_binding host="copilot">
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

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. fetch
retrieves a known URL and does not search: network search needs a search tool
registered in this session. A user question is asked in the reply, and the run
waits for the answer. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

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

Carry the `office:design` record (direction, chosen palette by role, pairing)
and the document type chosen from `structure.md` into the document design
report. Proposal/final record authority follows design's `references/art-direction.md`;
the assigned working candidate is not a recorded selection. A supplied brand/template keeps its accepted identity and values;
catalog letter `H` is optional. Use the same palette
roles and font families when the task also produces a deck.
Document-specific point sizes, line lengths and page flow remain format choices.

## Compose for the chosen type

`structure.md` fixes the type's section sequence, opening and heading
voice. This reference adds the composition that carries it. Select by content
and combine only the page types the brief needs; name the composition and any
variation in the existing brief; retain the supplied template when editing.

| Type group | Composition | Native construction |
|---|---|---|
| Decision memo, briefing note, letter, minutes | Direct entry, one main column, the decision or issue above the fold; compact context and a closing action | Native headings and lists; a short conclusion panel if useful; an action table for minutes |
| Report, white paper | Standing opening, findings or claims in order of importance with their figures, limitations and references | Consistent body-page styles; contents for a long document; captioned figures and repeatable data tables |
| Proposal | Reader-facing section openings, deliverables and schedule as tables, terms and acceptance as the closing page | Distinct section openings, editable schedule/pricing tables and a clear final action |
| Procedure, policy, handbook | Orientation first; stable numbered units, each self-contained; examples, exceptions and troubleshooting where the type calls for them | Heading hierarchy, numbered units, navigation fields when supported, native code or example styles and explicit notes |
| Tutorial or guide | Goal first; steps with the visible result after each; the finished result | Numbered steps with figure or callout slots; native code styles |
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
| Identity | Loaded CONTENT.md and DESIGN.md project/revisions, target DOCX, source versions and brief |
| Page geometry | Page size/orientation, units, margins and usable width; section changes and columns/gutter where needed |
| Page types | Chosen recipes and wireframes, block order and representative content; explain intentional variation |
| Styles | Native paragraph/character style names or existing IDs and inheritance; title/headings/body/captions/quotes/table roles mapped to shared theme tokens |
| Flow | Keep-with-next, widow/orphan behavior, paragraph spacing, intentional page/section breaks and rules for content growth |
| Tables and figures | Widths, headers, alignment, captions/sources, native representation, image proportions/crop and reading order |
| Furniture | Headers, footers, first-page variants, page-number fields and navigation/reference update needs |
| Template reuse | Optional `.dotx` from `office:design`'s `template_kit.py` or inherited base; requested editable exemplar blocks, replacement instructions and supported growth |
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
