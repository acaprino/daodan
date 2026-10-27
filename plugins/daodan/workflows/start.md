---
description: >
  Route any Office request from one intake into the requested document, deck,
  workbook, theme, verification or repair methods with shared content/design.
argument-hint: "<what you want, with any files, URLs or notes>"
---

Handle the Office request in: $ARGUMENTS

Load `office:intake` and `work-controller:work-record`, then follow intake's
`references/routing.md`: read/classify inputs, name destinations, record
phase-specific dependencies, settle inherited decisions and ask remaining
material choices once through the existing question contract.

Run routed methods here in order; do not start nested coordinators. This entry
declares every Office role and supplies their generated isolated bindings:

- `document`: `office:docx`; dispatch `office:content-strategist` for full/delta
  content, `office:document-designer` for scoped layout and
  `office:document-reviewer` for exact saved-render review.
- `presentation`: `office:pptx`; dispatch the same strategist when needed,
  `office:presentation-designer` and `office:presentation-reviewer`.
- `theme`: `office:design` and the requested reusable-template procedure, using
  the same declared format designers/reviewers for native proof and final review.
- `workbook`: `office:xlsx`; `verify` and `fix`: `office:integrity`.

For a DOCX/PPTX bundle prepare shared editorial data once and select one DESIGN.md
after `office:design`'s reviewed native proposals and v2 gallery; preserve one
content/design identity/revision and only requested projections. Finalize PPTX
display values and canonical binding after visual
selection, then validate/load the actual CONTENT.md/plan and DESIGN.md before
final composition. Proposal working bindings follow design's art-direction
contract. Reuse accepted records for the next format instead of repeating
strategy or selection. Layout and native review remain format-specific.

Only the operation's necessary phases run. Pass outputs forward, preserve
supplied files and separate candidates, and verify expected reports/coverage.
Missing capability blocks dependent delivery; a worker stop is not success.
Deliver each destination with its review/report, final recorded decisions and
checks that remain unavailable.
