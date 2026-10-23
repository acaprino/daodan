---
description: >
  Create, redesign or edit editable PowerPoint with creative specialists,
  SlidePoise generation and DeckCraft editing, preview and PDF export.
  TRIGGER WHEN: the user requests a PPTX, presentation template, pitch deck,
  consulting deck or changes to an existing presentation.
argument-hint: "<brief | source files | existing presentation and requested revision>"
---

Create or revise the presentation requested in: $ARGUMENTS

Load `office:presentation-design` and follow its routing, specialist delivery and
image-tool contract. Read its `references/pptx-compatibility.md` and
`references/design-library.md` before creative
work; bind every selected provider to the fixed canvas, supported native objects,
fonts and editability requirements. The coordinator owns the outline, candidate files, image
generation calls, repair loop and final report. Dispatch the declared
`office:presentation-designer` and `office:presentation-reviewer` roles in isolated
contexts as specified by that method. A skill load is not a worker dispatch.

For a new presentation or substantive redesign, load `office:slidepoise` for
visual-first reference generation and native reconstruction, or load
`office:deckcraft` for direct structured native construction when requested or
when SlidePoise's runtime is unavailable. For targeted PPTX edits, preview
or PDF export, load `office:deckcraft`. Preserve both engines' separate ownership;
do not round-trip every SlidePoise result through DeckCraft unnecessarily.

When the source includes an Excel workbook, load the `office:xlsx` skill to
inspect its native data, formulas and calculation evidence before using figures
or rebuilding editable charts.

When the source includes a Word document, load the `office:docx` skill to read
its native content, tables and annotations before developing the presentation.

Continue authorized corrections until required deliveries exist. Missing runtime,
image tool, isolation, renderer or reviewer evidence blocks its dependent step
and must appear in the result. A worker's stopped turn is not a delivery.

Deliver the editable `.pptx`, requested preview or printable PDF, and a concise
presentation review recording candidate identity, inspected slides, native
editability, preservation checks and unresolved limitations. Printing means a
printable PDF unless an available printer interface is explicitly requested.
