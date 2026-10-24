---
name: presentation-design
description: >
  Coordinate presentation art direction, editable construction and independent
  rendered review through creative specialists. TRIGGER WHEN: creating,
  redesigning or editing a PPTX, reusable presentation template or branded deck.
  DO NOT TRIGGER WHEN: the deliverable is a website or a standalone image.
---

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
Read `references/ppt-visual.md` for concrete wireframes and the slide-specification
handoff; map them to existing patterns rather than adding another layout catalog.
Read `references/image-tools.md` before image work.

Coordinated execution uses the registered `office:presentation` workflow
entry and its generated dispatch bindings. If this skill was loaded directly,
resolve that entry on the active host before dispatch; continue the same task,
not a nested workflow. A role name alone cannot supply an inline worker body.

## Route the request

Keep one brief and outline: audience, decision, language, sources, required
wording, brand assets, delivery context, slide roles and editable objects. Resolve
material uncertainty; infer routine choices within the user's authorization.
Preserve facts and citations. Do not manufacture evidence to fill a composition.

`office:intake` owns the single round of questions and the route. Add the
presentation decisions that shape the deck to that round: argument mode (how
the deck argues, from `references/design-library.md`), art direction (a
library direction or their brand), the colour source for the palette, style
constraints, content and page count, and the slide types they expect. Suggest
concrete options from `office:design`'s `references/directions.md` and
`references/layout-patterns.md` rather than an open question. The palette
candidates are shown and chosen after that round, as `office:design` describes.

For a deck with more than a few slides, or whenever direction is genuinely
uncertain, prepare the plan and show a preview before construction: compile the
plan JSON in `references/design-preview.md`, render it with
`python "${CLAUDE_PLUGIN_ROOT}/skills/presentation-design/scripts/design_preview.py"`,
and let the user confirm the slide sequence under the direction already chosen
at intake. A separate style
proof costs image generations and needs the user's explicit budget decision and
their chosen number of candidate directions; a full autonomous request authorizes
routine choices without a preview gate.

| Intake route | Method | Specialist scope |
|---|---|---|
| Substantial: new or derived deck, template, redesign, restructure or shortening | `office:slidepoise` (visual-first reconstruction) or `office:deckcraft` (direct native construction when requested or when SlidePoise is unavailable) | Designer establishes direction and slide-object plan; reviewer inspects final renders |
| Narrow: targeted content or formatting edit | `office:deckcraft` | Preserve the direction and palette; no designer dispatch: a change that needs a new design decision goes back to the user and re-enters intake; reviewer checks changes and preservation |
| Read-only: review, preview or printable PDF | `office:deckcraft` for renders and export, never writing to the source | No redesign; reviewer inspects the source renders and any export |

For a reusable template, provide an editable exemplar deck, representative page
types, reusable visual rules and a short reuse note. Do not label a PPTX exemplar
as a PowerPoint `.potx` template or claim master-layout support without verification.

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

Dispatch `office:presentation-designer` for creative work. Supply brief, outline,
sources, brand assets, existing renders, compatibility brief, absolute report
path. Require direction, the slide-object
specification from `references/pptx-compatibility.md`, image requests and unresolved
decisions. Verify the report exists and its geometry, typography and native-object
choices are supported before construction or image generation. For a narrow edit
or export, record why a new design delivery is
unnecessary; preserve the accepted direction.

Load the selected engine skill and perform construction or editing in the
coordinator. Give SlidePoise the accepted compatibility brief and design report
as context for its planning and compiled generation request. Do not recreate its
construction schemas locally. Reject references that cannot be reconstructed
with the required editability before propagating their design across the deck.
DeckCraft applies scoped edits to a separate candidate after preservation checks.
Keep source and earlier candidates intact.

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

When the deck uses fonts outside Microsoft Office, embed them in the delivered
copy with `office:design`'s `font_embed.py` and record its
inspection result. Deliver the deck and useful previews with remaining limits. Do not claim a
visually reviewed result when actual candidate renders or visual access were
unavailable. Continue independent work when a required capability blocks a step.
On the read-only route, the unchanged source PPTX is the presentation artifact;
identify it explicitly, review its renders and any requested export, and do not
claim to have created or edited another PPTX.
