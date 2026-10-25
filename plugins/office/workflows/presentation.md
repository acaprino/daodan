---
description: >
  Create, derive, revise, review or export an editable PowerPoint presentation
  with creative specialists, DeckCraft construction and editing, preview and
  PDF export. TRIGGER WHEN: the user requests a PPTX, presentation
  template, pitch deck or consulting deck, or a change, review or export of an
  existing presentation.
argument-hint: "<brief | source files | existing presentation and requested change>"
---

Handle the presentation task requested in: $ARGUMENTS

Load `office:intake` first. Resolve the starting point, carry-over, depth of
change and deliverable in its single round of questions, together with the
presentation questions of `office:pptx`. Then follow
`office:pptx` for the route, specialist delivery and image-tool
contract.

Run only the steps of the operation's row in `office:pptx` ("Run only the steps
the operation needs"): an expansion or revision inherits the deck's purpose,
audience, mode and theme, plans only the delta and designs only new and changed
slides; a restyle keeps the content and redesigns the look; an edit plans and
designs nothing. When the operation has a content plan, dispatch
`office:content-strategist` first to plan the claims, slide count, sequence and
patterns, following `office:pptx`'s `references/content-planning.md`; bring its
overflow, gaps and proposed cuts to the user. Then read its `references/pptx-compatibility.md`,
`references/design-library.md` and `references/design-preview.md` before creative
work, then select the visual direction and slide patterns from
`office:design`'s `references/directions.md` and `references/layout-patterns.md`; bind every
design choice to the fixed canvas, supported native objects,
fonts and editability requirements. When the direction is uncertain, compile
the plan, render the static preview and let the user choose the direction and
sequence before image generation or construction. Load `office:deckcraft` for
native construction of the accepted slide specification.

On the narrow route, load `office:deckcraft` for targeted edits and preserve the
accepted direction. On the read-only route, load `office:deckcraft` for renders,
previews or PDF export; the read-only route never writes to the source deck.

The coordinator owns the approved plan, candidate files, image generation calls,
repair loop and final report. Dispatch the declared `office:content-strategist`,
`office:presentation-designer` and `office:presentation-reviewer` roles in
isolated contexts as specified by that method. A skill load is not a worker dispatch.

When the source includes an Excel workbook, load the `office:xlsx` skill to
inspect its native data, formulas and calculation evidence before using figures
or rebuilding editable charts.

When the source includes a Word document, load the `office:docx` skill to read
its native content, tables and annotations before developing the presentation.

Continue authorized corrections until required deliveries exist. Missing runtime,
image tool, isolation, renderer or reviewer evidence blocks its dependent step
and must appear in the result. A worker's stopped turn is not a delivery.

Deliver the editable `.pptx` on the substantial and narrow routes, and the
requested findings, preview or printable PDF on the read-only route. Include a
concise presentation review recording the reviewed deck's identity, inspected
slides, native editability, preservation checks and unresolved limitations.
Printing means a printable PDF unless an available printer interface is
explicitly requested.
