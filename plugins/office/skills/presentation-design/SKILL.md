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
`references/pptx-compatibility.md` before creative work, image generation or native
construction. Apply its target, slide-object and verification requirements to
every selected creative provider.
Read
`references/creative-providers.md` when first loading a creative provider or
resolving its availability. Read `references/image-tools.md` before image work.

Coordinated execution uses the registered `office:create-presentation` workflow
entry and its generated dispatch bindings. If this skill was loaded directly,
resolve that entry on the active host before dispatch; continue the same task,
not a nested workflow. A role name alone cannot supply an inline worker body.

## Route the request

Keep one brief and outline: audience, decision, language, sources, required
wording, brand assets, delivery context, slide roles and editable objects. Resolve
material uncertainty; infer routine choices within the user's authorization.
Preserve facts and citations. Do not manufacture evidence to fill a composition.

| Request | Method | Specialist scope |
|---|---|---|
| New deck, new template, substantial redesign | `office:slidepoise` | Designer establishes direction; reviewer inspects final renders |
| Targeted content or formatting edit | `office:deckcraft` | Preserve direction; designer only if a design decision is needed; reviewer checks changes and preservation |
| Preview or printable PDF only | `office:deckcraft` | No redesign; reviewer checks exported pages against the source |

For a reusable template, provide an editable exemplar deck, representative page
types, reusable visual rules and a short reuse note. Do not label a PPTX exemplar
as a PowerPoint `.potx` template or claim master-layout support without verification.

## Delegate with bounded ownership

Establish the target canvas, engine capabilities, fonts and required editability
before consulting creative providers. Pass that compatibility brief to workers.
Select optional creative providers under `references/creative-providers.md` and
pass their selection and availability to each worker. With none installed,
use Office's presentation criteria and the selected engine's guidance. Optional
provider absence does not waive design or independent review deliveries.

The coordinator is the sole deck writer and image-tool caller. Workers read the
brief, source evidence and artifacts, and write only their assigned report.
They do not launch further workers, rewrite the deck or start another engine.
Default models inherit the session. Use the active host's actual isolated
dispatch mechanism and generated role bindings, including when only one reviewer
is required. Unavailable isolation blocks that delivery.

Dispatch `office:presentation-designer` for creative work. Supply brief, outline,
sources, brand assets, existing renders, compatibility brief, absolute report
path and selected creative providers. Require direction, the slide-object
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

Dispatch `office:presentation-reviewer` after actual candidate rendering. Supply
the exact candidate path and SHA-256, render engine/version, page manifest,
brief, design report, source and candidate inventories, allowed changes and
selected creative providers, accepted slide-object specification and font evidence.
Require inspected page identities, concrete defects, preservation findings,
coverage gaps, separate target-application fidelity evidence and a
pass/needs-fix/blocked verdict. An empty response or an
uninspected contact sheet cannot satisfy this delivery.

Verify report artifacts and coverage, resolve substantive findings, rerender
changed pages and obtain an updated review tied to the new candidate. Retain
prior review evidence for unchanged pages only when their identity and rendered
content are proved unchanged. Do not apply a verdict to another file. Inspect
or resume a missing delivery, or record a concrete blocker.

## Completion evidence

Keep one presentation review with candidate identity, requested scope, engines
and versions, source preservation, native-object checks, image provenance,
rendered/inspected/total page counts, target-application verification or its
absence, font substitutions, visual/editability compromises, specialist report paths, consulted or
unavailable creative providers and remaining gaps.
The coordinator owns the final verdict. Structure checks cannot establish visual
quality; rendered images cannot establish native editability. Claims about
Microsoft PowerPoint fidelity require actual PowerPoint rendering evidence under
`references/pptx-compatibility.md`; previews from another engine remain separate.

Deliver the deck and useful previews with remaining limits. Do not claim a
visually reviewed result when actual candidate renders or visual access were
unavailable. Continue independent work when a required capability blocks a step.
For export-only requests, the unchanged source PPTX is the presentation artifact;
identify it explicitly, review its renders and the requested export, and do not
claim to have created or edited another PPTX.
