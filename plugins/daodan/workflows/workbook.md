---
description: >
  Create, derive, revise or analyze a native Excel workbook while preserving its
  formulas, formatting, tables, charts and other required features. TRIGGER WHEN:
  the user requests XLSX work, spreadsheet analysis, a model, a tracker or a
  dashboard, or a change or review of an existing workbook.
argument-hint: "<brief | source files | existing workbook and requested change>"
---

Handle the workbook task requested in: $ARGUMENTS

Load `office:intake` first. Resolve the starting point, carry-over, depth of
change and deliverable in its single round of questions, together with the
workbook questions of `office:xlsx`. Then follow `office:xlsx`, which builds and
calculates through `office:gridcraft`. Inspect existing files before editing them. Produce or edit native workbook objects,
preserve required features, verify the authorized changes and distinguish
formula preservation from actual recalculation. The read-only route never writes
to the source workbook.

Deliver the requested `.xlsx` on the substantial and narrow routes, or the
findings on the read-only route, together with a concise workbook review covering
checked calculations, preservation evidence and any unsupported feature or
unverified recalculation.
