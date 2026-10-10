---
description: >
  Create, read or edit native Word documents with professional styles, tables,
  headers, footers and page layouts. TRIGGER WHEN: the user requests DOCX work,
  a Word report, proposal, letter, template or controlled document revision.
argument-hint: "<document task | source files | existing document and requested changes>"
---

Perform the document task requested in: $ARGUMENTS

Load the `office:docx` skill. Inspect supplied files before choosing an editing
engine. Create or revise native document content, preserve required features and
verify the saved result. A request only to read or analyze authorizes read-only
work. Keep layout review and actual field updates distinct from package checks.

When figures come from a workbook, load the `office:xlsx` skill to inspect its
native data and calculation evidence before including them in the document.

Deliver editable `.docx` for creation, preserve the required source format for
edits, or deliver the requested findings for read-only work. Include a concise
document review stating preservation checks, rendered review scope and any
unsupported operation or unverified layout.
