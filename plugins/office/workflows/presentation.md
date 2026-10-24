---
description: >
  Create, derive, revise, review or export an editable PowerPoint presentation
  with creative specialists, SlidePoise generation and DeckCraft editing,
  preview and PDF export. TRIGGER WHEN: the user requests a PPTX, presentation
  template, pitch deck or consulting deck, or a change, review or export of an
  existing presentation.
argument-hint: "<brief | source files | existing presentation and requested change>"
---

Handle the presentation task requested in: $ARGUMENTS

Load `office:intake` first. Resolve the starting point, carry-over, depth of
change and deliverable in its single round of questions, together with the
presentation questions of `office:presentation-design`. Then follow
`office:presentation-design` for the route, specialist delivery and image-tool
contract.

On the substantial route, read its `references/pptx-compatibility.md`,
`references/design-library.md` and `references/design-preview.md` before creative
work, then select the visual direction and slide patterns from
`office:design`'s `references/directions.md` and `references/layout-patterns.md`; bind every
design choice to the fixed canvas, supported native objects,
fonts and editability requirements. When the direction is uncertain, compile
the plan, render the static preview and let the user choose the direction and
sequence before image generation or construction. Load `office:slidepoise` for
visual-first reference generation and native reconstruction, or load
`office:deckcraft` for direct structured native construction when requested or
when SlidePoise's runtime is unavailable.

On the narrow route, load `office:deckcraft` for targeted edits and preserve the
accepted direction. On the read-only route, load `office:deckcraft` for renders,
previews or PDF export; the read-only route never writes to the source deck.
Preserve both engines'
separate ownership; do not round-trip every SlidePoise result through DeckCraft
unnecessarily.

The coordinator owns the outline, candidate files, image generation calls, repair
loop and final report. Dispatch the declared `office:presentation-designer` and
`office:presentation-reviewer` roles in isolated contexts as specified by that
method. A skill load is not a worker dispatch.

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
