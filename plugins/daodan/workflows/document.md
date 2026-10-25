---
description: >
  Create, derive, revise, review or export a native Word document with
  professional styles, tables, headers, footers and page layouts. TRIGGER WHEN:
  the user requests DOCX work, a Word report, proposal, letter or template, or a
  change, review or export of an existing document.
argument-hint: "<brief | source files | existing document and requested change>"
---

Handle the document task requested in: $ARGUMENTS

Load `office:intake` first. Resolve the starting point, carry-over, depth of
change and deliverable in its single round of questions, together with the
document questions of `office:docx`. Then follow `office:docx`. Inspect supplied
files before choosing an editing engine. Create or revise native document
content, preserve required features and verify the saved result. Keep layout
review and actual field updates distinct from package checks.

Run only the steps the operation recorded at intake needs. When it gives the
document a new look (create, restyle, or derive without carrying the look over),
load `office:design`: build and choose the palette from the user's colour source,
record direction and pairing, and install the pairing's fonts; preserve supplied
brands and templates. An expansion or revision inherits the document's type,
styles and theme and designs only its new or changed sections. Record the document
type chosen at intake from `office:docx`'s `references/document-types.md`. Follow `office:docx`
to dispatch the isolated `office:document-designer`, scoped to the sections the
operation designs, with its real generated role binding. Require concrete page layouts and template instructions, verify the
assigned design report, then load `office:wordcraft` to build, save, reopen and
render the actual DOCX in the coordinator. On the narrow and read-only routes,
retain the existing layout and do not start creative dispatch. The read-only
route never writes to the source document. On every route, dispatch the
isolated `office:document-reviewer` on the rendered candidate (or on the
rendered unchanged source for a read-only review) as `office:docx` specifies,
and resolve its blocking findings within at most three review rounds.

When figures come from a workbook, load the `office:xlsx` skill to inspect its
native data and calculation evidence before including them in the document.

Deliver editable `.docx` on the substantial route, preserve the required source
format for narrow edits, and deliver the requested findings or export on the
read-only route. Include a concise document review recording candidate identity,
inspected pages, the reviewer's verdict and open findings, coverage of source
text, preservation checks and any unsupported operation or unverified layout.
