---
name: pptx
description: >
  Coordinate presentation art direction, editable construction and independent
  rendered review through creative specialists. TRIGGER WHEN: creating,
  redesigning or editing a PPTX, reusable presentation template or branded deck.
  DO NOT TRIGGER WHEN: the deliverable is a website or a standalone image.
---

# Presentation design and delivery

Own the presentation outcome and native coordination. `office:content` owns
strategy, claims, depth, transformations and logical sequence; project it through
`references/structure.md` and `references/content-planning.md`. The presentation
designer finalizes composition/patterns under `references/layout-patterns.md`
and `references/pptx-compatibility.md`, preserving source meaning and permissions.
`office:design` owns Taste art direction, native proposals and selected DESIGN.md. For bundles,
both format designers consume the same content/design identities and revisions.
A narrow edit or export does not re-enter creative design.

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

`office:intake` owns the single round of questions, material/dependency record,
operation and inherited decisions. Add only unresolved presentation decisions:
delivery context, speaking time/slide budget, density, required native editability
and canvas. The content owner uses the structure catalog's five argument modes;
visual directions and pairings are resources for ad hoc proposals, not a second
mandatory preset choice. Record supported native objects/fonts before layout.

## Run only the steps the operation needs

| Operation | Content plan | Theme | Slide design | Build | Review |
|---|---|---|---|---|---|
| Create | Full plan from every source | New ad hoc visual proposals; separate `.potx` optional | Every slide | New native deck under selected theme | Every slide |
| Derive | Full plan; carried content enters the ledger | Inherited when the look is carried over, otherwise chosen as in Create | Every slide | New native candidate with inherited or selected theme | Every slide; coverage of carried content |
| Expand | Delta plan: new slides placed in the existing storyline; existing slides `kept` or `moved` | Inherited from the deck | New slides only, on the deck's existing layouts and patterns | Candidate built from the deck | New and moved slides, deck-level consistency, coverage of every existing slide |
| Revise | Delta plan: `updated`, `moved`, `merged` and approved cuts | Inherited from the deck | Changed slides only | Candidate built from the deck | Changed slides; coverage except approved cuts |
| Restyle | None: content, sequence and claims stay | New ad hoc proposals; separate `.potx` optional | Every slide, keeping each slide's pattern and content | New candidate with all content carried | Every slide; complete coverage |
| Edit | None | Inherited | None | Scoped candidate | Changed slides and preservation |
| Review or export | None | None | None | None | The unchanged source |

A combined request runs the union of its rows: expand and restyle plans the delta
and redesigns every slide on the new base. An operation that turns out to need a
step outside its row (an edit that needs a new layout) goes back to intake.

For a full/delta plan, load `office:content` and dispatch the existing strategist
for complete editorial working data and native plan JSON. New-look design can
use that content before the PPTX display fields are final. For a new look, follow
`office:design`'s `references/art-direction.md`: the settled brief enters Taste,
then existing designers, native producers and reviewers prove representative
candidates in `proposal` mode before the v2 gallery and visual selection.
Inherited looks rebind their accepted record
under its `references/records.md` when content identity/revision or requested
formats change, including the documented legacy-theme bootstrap.
Then finalize the display binding below and render the native plan preview with
`design_preview.py` under `references/design-preview.md`. Interactive work can
confirm count, sequence and proposed patterns; full authorized autonomy needs
no new approval. The plan wireframe is separate from the full visual comparison.
Image requests use the existing brief's authority and `references/image-tools.md`;
missing assets or native/render capabilities block their dependent proposal proof.

| Intake route | Method | Specialist scope |
|---|---|---|
| Substantial: create, derive, expand, revise or restyle | `office:deckcraft` (native construction from the accepted slide-object specification) | The steps of the operation's row above: content strategist for the full or delta plan; designer for every or only the new and changed slides; reviewer on the final renders |
| Narrow: targeted content or formatting edit | `office:deckcraft` | Preserve the direction and palette; no designer dispatch: a change that needs a new design decision goes back to the user and re-enters intake; reviewer checks changes and preservation |
| Read-only: review, preview or printable PDF | `office:deckcraft` for renders and export, never writing to the source | No redesign; reviewer inspects the source renders and any export |

Substantial construction runs through `office:deckcraft` or, when the accepted
design has an HTML source, through the mechanical conversion in
`references/html-to-pptx.md`. Inspection, rendering, coverage and independent
review are the same either way, and editing an existing deck stays with
`office:deckcraft`.

For a reusable template, generate the base with `office:design`'s
`template_kit.py` (slide master, theme and layouts in a `.potx`), add an editable
exemplar deck built on it with representative page types, and a short reuse note.
Claim only what the kit's report and an opened, rendered sample show; an engine's
own save to `.potx` is not a template at DeckCraft's reference version.

## Delegate with bounded ownership

Establish the target canvas, engine capabilities, fonts and required editability
before design work. Pass that compatibility brief to workers. Read the shared records and only references needed by each assignment;
keep logical content, visual identity and format composition with their owners.
Use `office:design`'s one art-direction boundary for the required Taste contribution;
format workers receive its derived brief and only references their assignment needs.

The coordinator is the sole deck writer and image-tool caller. Workers read the
brief, source evidence and artifacts, and write only their assigned report.
They do not launch further workers, rewrite the deck or start another engine.
When the coordinator lacks the image tool, the explicit parent-harness handoff
in `references/image-tools.md` is the permitted exception for the actual call.
Verify the returned asset; absent tool access and handoff block dependent imagery.
Default models inherit the session. Use the active host's actual isolated
dispatch mechanism and generated role bindings, including when only one reviewer
is required. Unavailable isolation blocks that delivery.

Dispatch `office:content-strategist` when the operation has a content plan,
unless the shared bundle delivery already exists. Supply the settled brief,
requested formats, every source, existing native files/records, operation,
permissions/cuts and absolute CONTENT working-data and plan paths. Require a full
plan for create/derive, delta for expand/revise, source locators, claim/unit
placements and budget reasoning. Verify complete artifacts and escalate actual
gaps, conflicts, overflow and proposed cuts before dependent construction.
Restyle, edit and export do not plan content. Workers never invent theme values.

### Finalize and load the shared binding

For proposal proof, the art-direction contract uses candidate-specific working
copies of this same plan and its canonical binding, without freezing final
CONTENT.md or inventing selection. After visual selection, the coordinator fills
the final existing plan's `direction`
with the accepted design name and actual `background`, `ink`, `surface`, `accent`
palette values. `library` is optional for an ad hoc theme; if used it is a catalog
resource, not visual authority. Keep the existing plan schema and its stable
slide IDs/claim IDs and `content_revision`. Recompute CONTENT's plan digest as
`canonical-json-v1` under `office:content`'s `references/records.md`, then write
final CONTENT.md to a new path. This derived-binding finalization changes no
claims or content revision. Creative editorial changes return to the content
owner. Do not freeze a new-look PPTX binding against provisional colors.

Explicitly load CONTENT.md and DESIGN.md with the shared loader; compare project,
content revision and exact requested formats, then run:

```text
python "${CLAUDE_PLUGIN_ROOT}/skills/content/scripts/office_records.py" validate CONTENT.md --pptx-plan plan.json
python "${CLAUDE_PLUGIN_ROOT}/skills/content/scripts/office_records.py" validate DESIGN.md
python "${CLAUDE_PLUGIN_ROOT}/skills/pptx/scripts/design_preview.py" --plan plan.json
```

Require both shared record/actual-plan validation and native pattern/capacity
validation before final construction. Proposal specimens use the explicitly
bounded working-record checks in the art-direction contract. A filename or
digest shape alone proves neither.
Restyle reuses accepted content. If a legacy restyle needs a new DESIGN binding,
the coordinator serializes unchanged content/inherited decisions in the shared
contract without a new strategy or strategist. Legacy local edits/reviews need
no fabricated retrospective global plan. Changes to a final
pattern update the native plan and its derived binding; changes to meaning,
priority or sequence require the content owner's editorial revision.

Dispatch `office:presentation-designer` in `final` mode for the slides the operation designs:
every slide for create, derive and restyle; only new and changed slides for
expand and revise, on the deck's existing layouts, patterns and theme. Supply
brief, final CONTENT.md/DESIGN.md paths and revisions, the approved plan,
slides in scope, sources, assets, existing renders, compatibility brief and
absolute report path. The designer keeps slide order, claims and permissions,
finalizes composition and adds geometry; a pattern change needs a reason and
a renewed derived plan binding. Require direction, the slide-object
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

On the HTML conversion route the coordinator runs `scripts/pptx_convert_bridge.py`
under `references/html-to-pptx.md` instead of transcribing objects: the designer's
1920x1080 panels become native text, shapes, pictures and notes in one
deterministic pass with no model call. Its prerequisites are Node, the Playwright
module and a Chromium-family browser. A missing runtime stops with the recovery
steps recorded in the report; it is never replaced silently by another
construction path. The saved candidate then follows the same inspection,
rendering, coverage and independent review as a DeckCraft build.

When the deck uses fonts outside Microsoft Office, embed them in a separate
candidate with `office:design`'s `font_embed.py` and record its inspection result.
Complete embedding before preservation checks, rendering and independent review;
they must bind to the exact copy delivered. On the read-only route keep the
unchanged source and report its existing font evidence without embedding.

When the substantial route starts from an existing deck (derived, restyled,
restructured or shortened), write the approved cuts recorded at intake to a cuts
file and run `pptx_inspect.py coverage` from `office:deckcraft` on the source and
each candidate. Every unexpectedly missing unchanged/locked item is restored or brought back to
the user as a proposed cut; never cut content the user did not approve. Retain
literal coverage for those blocks. Authorized free transformations additionally
need source-linked destination mappings and independent review of facts,
conditions, uncertainty and claim strength; maps/similarity alone are no proof.

Dispatch `office:presentation-reviewer` in `final` mode after actual candidate rendering, or on
the read-only route after rendering the unchanged source, which then stands in
for the candidate. Supply
the exact candidate path and SHA-256, render engine/version, page manifest,
brief, design report, source and candidate inventories, allowed changes, the
coverage report when one exists, exact content/design identities and
transformation permissions, accepted slide-object specification and font evidence.
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
