---
name: pptx
description: >
  Coordinate presentation art direction, editable construction and independent
  rendered review through creative specialists. TRIGGER WHEN: creating,
  redesigning or editing a PPTX, reusable presentation template or branded deck.
  DO NOT TRIGGER WHEN: the deliverable is a website or a standalone image.
---

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

# Presentation design and delivery

Own the presentation outcome, not a second construction engine. Read
`references/pptx-compatibility.md` and `references/design-library.md` before
creative work, image generation or native construction. Apply their target,
direction, pattern, slide-object and verification requirements to the
presentation plan.
Choose the deck's argument mode from `references/design-library.md`, its visual
direction from `office:design`'s `references/directions.md` and each slide's pattern from
`references/layout-patterns.md`; record all three in the plan so construction
and review can verify them.
On the substantial route, load `office:design`: it owns the direction, the
palette built from the user's colour source and chosen from candidates, the
font pairing with its installation and embedding, the argument mode, and the
editorial and typographic method. Keep its record in the same design report and
compatibility brief and pass it to the designer. Preserve supplied brands and
session selections. For DOCX/PPTX bundles both format designers consume the
same record. A narrow edit or export does not re-enter design.
Read `references/image-tools.md` before image work.

Coordinated execution uses the registered `/daodan:presentation` workflow
entry, or `/daodan:start`, which declares the same roles, and its generated
dispatch bindings. If this skill was loaded directly,
resolve that entry on the active host before dispatch; continue the same task,
not a nested workflow. A role name alone cannot supply an inline worker body.

## Route the request

Keep one brief and outline: audience, decision, language, sources, required
wording, brand assets, delivery context, slide roles and editable objects. Resolve
material uncertainty; infer routine choices within the user's authorization.
Preserve facts and citations. Do not manufacture evidence to fill a composition.

`office:intake` owns the single round of questions, the operation and the route.
Add to that round only the presentation decisions the operation leaves open
(table below); an existing deck supplies the rest. For a new deck these are: argument mode (how
the deck argues, from `references/design-library.md`), the planning decisions of
`references/content-planning.md` (purpose and goal, audience, scope, delivery,
length or slides to add, density), art direction (a library direction or their
brand), the colour source for the palette, style constraints and the slide types
they expect. Suggest
concrete options from `office:design`'s `references/directions.md` and this
skill's `references/layout-patterns.md` rather than an open question. The palette
candidates are shown and chosen after that round, as `office:design` describes.

## Run only the steps the operation needs

| Operation | Content plan | Theme | Slide design | Build | Review |
|---|---|---|---|---|---|
| Create | Full plan from every source | Choose the palette; generate the base `.potx` | Every slide | New deck on the base | Every slide |
| Derive | Full plan; carried content enters the ledger | Inherited when the look is carried over, otherwise chosen as in Create | Every slide | New deck on the source or on the new base | Every slide; coverage of carried content |
| Expand | Delta plan: new slides placed in the existing storyline; existing slides `kept` or `moved` | Inherited from the deck | New slides only, on the deck's existing layouts and patterns | Candidate built from the deck | New and moved slides, deck-level consistency, coverage of every existing slide |
| Revise | Delta plan: `updated`, `moved`, `merged` and approved cuts | Inherited from the deck | Changed slides only | Candidate built from the deck | Changed slides; coverage except approved cuts |
| Restyle | None: content, sequence and claims stay | New palette and direction; generate the base `.potx` | Every slide, keeping each slide's pattern and content | New deck on the new base with all content carried | Every slide; complete coverage |
| Edit | None | Inherited | None | Scoped candidate | Changed slides and preservation |
| Review or export | None | None | None | None | The unchanged source |

A combined request runs the union of its rows: expand and restyle plans the delta
and redesigns every slide on the new base. An operation that turns out to need a
step outside its row (an edit that needs a new layout) goes back to intake.

When the operation has a content plan, it comes first: dispatch
`office:content-strategist` (below) and take its plan JSON. For a new or derived
deck of more than a few slides, or whenever direction is genuinely uncertain,
show that plan before construction under `references/design-preview.md`: render
it with `python "<plugin-root>/skills/pptx/scripts/design_preview.py"`,
and let the user confirm the slide count, sequence and patterns under the
direction already chosen at intake. For an expansion or revision show the delta
(status and position of each new or changed slide) with the same preview. A separate style
proof costs image generations and needs the user's explicit budget decision and
their chosen number of candidate directions; a full autonomous request authorizes
routine choices without a preview gate.

| Intake route | Method | Specialist scope |
|---|---|---|
| Substantial: create, derive, expand, revise or restyle | `office:deckcraft` (native construction from the accepted slide-object specification) | The steps of the operation's row above: content strategist for the full or delta plan; designer for every or only the new and changed slides; reviewer on the final renders |
| Narrow: targeted content or formatting edit | `office:deckcraft` | Preserve the direction and palette; no designer dispatch: a change that needs a new design decision goes back to the user and re-enters intake; reviewer checks changes and preservation |
| Read-only: review, preview or printable PDF | `office:deckcraft` for renders and export, never writing to the source | No redesign; reviewer inspects the source renders and any export |

For a reusable template, generate the base with `office:design`'s
`template_kit.py` (slide master, theme and layouts in a `.potx`), add an editable
exemplar deck built on it with representative page types, and a short reuse note.
Claim only what the kit's report and an opened, rendered sample show; an engine's
own save to `.potx` is not a template at DeckCraft's reference version.

## Delegate with bounded ownership

Establish the target canvas, engine capabilities, fonts and required editability
before design work. Pass that compatibility brief to workers. The design library,
the shared theme and the bundled editorial and typography guides are the complete
design method; consult no external design provider.

The coordinator is the sole deck writer and image-tool caller. Workers read the
brief, source evidence and artifacts, and write only their assigned report.
They do not launch further workers, rewrite the deck or start another engine.
When the coordinator lacks the image tool, the explicit parent-harness handoff
in `references/image-tools.md` is the permitted exception for the actual call.
Verify the returned asset; absent tool access and handoff block dependent imagery.
Default models inherit the session. Use the active host's actual isolated
dispatch mechanism and generated role bindings, including when only one reviewer
is required. Unavailable isolation blocks that delivery.

Dispatch `office:content-strategist` first when the operation has a content plan.
Supply the brief with the operation, the planning decisions and the inherited
ones, every source file, the existing deck when there is one, the approved cuts
and absolute paths for the content report and the plan JSON. Require a full plan
for create and derive, a delta plan for expand and revise. Verify both exist, the
plan passes `design_preview.py` and every core claim of the ledger reaches a
slide. Bring overflow, gaps, conflicts and proposed cuts to the user before
design. Restyle, edit and export do not plan content.

Dispatch `office:presentation-designer` for the slides the operation designs:
every slide for create, derive and restyle; only new and changed slides for
expand and revise, on the deck's existing layouts, patterns and theme. Supply
brief, the approved plan as the outline, the slides in scope, sources, brand
assets, existing renders, compatibility brief, absolute report path. The designer
keeps the plan's slide order, claims and patterns and adds geometry; a pattern
change needs a reason. Require direction, the slide-object
specification from `references/pptx-compatibility.md`, image requests and unresolved
decisions. Verify the report exists and its geometry, typography and native-object
choices are supported before construction or image generation. For a narrow edit
or export, record why a new design delivery is
unnecessary; preserve the accepted direction.

Load `office:deckcraft` and perform construction or editing in the coordinator.
Map the accepted compatibility brief and slide-object specification to its
discovered commands. Reject a design or reference image whose objects DeckCraft
cannot build with the required editability before propagating it across the deck.
DeckCraft applies scoped edits to a separate candidate after preservation checks.
Keep source and earlier candidates intact.

When the deck uses fonts outside Microsoft Office, embed them in a separate
candidate with `office:design`'s `font_embed.py` and record its inspection result.
Complete embedding before preservation checks, rendering and independent review;
they must bind to the exact copy delivered. On the read-only route keep the
unchanged source and report its existing font evidence without embedding.

When the substantial route starts from an existing deck (derived, restyled,
restructured or shortened), write the approved cuts recorded at intake to a cuts
file and run `pptx_inspect.py coverage` from `office:deckcraft` on the source and
each candidate. Every unexpectedly missing item is restored or brought back to
the user as a proposed cut; never cut content the user did not approve.

Dispatch `office:presentation-reviewer` after actual candidate rendering, or on
the read-only route after rendering the unchanged source, which then stands in
for the candidate. Supply
the exact candidate path and SHA-256, render engine/version, page manifest,
brief, design report, source and candidate inventories, allowed changes, the
coverage report when one exists, accepted slide-object specification and font evidence.
Require inspected page identities, concrete defects, preservation findings,
coverage gaps, separate target-application fidelity evidence and a
pass/needs-fix/blocked verdict. An empty response or an
uninspected contact sheet cannot satisfy this delivery.

Verify report artifacts and coverage, resolve every blocking finding, rerender
changed pages and obtain an updated review tied to the new candidate. Fix a
deck-level defect at its source (theme, shared style or master), not slide by
slide. Apply an advisory finding only when the fix is local and cannot create a
new defect. Run at most three review rounds: if blocking findings remain after
the third, stop and deliver the candidate with them listed as open, rather than
oscillating between fixes. Retain
prior review evidence for unchanged pages only when their identity and rendered
content are proved unchanged. Do not apply a verdict to another file. Inspect
or resume a missing delivery, or record a concrete blocker.

## Completion evidence

Keep one presentation review with candidate identity, requested scope, engines
and versions, source preservation, native-object checks, image provenance,
rendered/inspected/total page counts, target-application verification or its
absence, font substitutions, visual/editability compromises, specialist report paths and remaining gaps.
The coordinator owns the final verdict. Structure checks cannot establish visual
quality; rendered images cannot establish native editability. Claims about
Microsoft PowerPoint fidelity require actual PowerPoint rendering evidence under
`references/pptx-compatibility.md`; previews from another engine remain separate.

Deliver the deck and useful previews with remaining limits. Do not claim a
visually reviewed result when actual candidate renders or visual access were
unavailable. Continue independent work when a required capability blocks a step.
On the read-only route, the unchanged source PPTX is the presentation artifact;
identify it explicitly, review its renders and any requested export, and do not
claim to have created or edited another PPTX.
