---
description: >
  One entry for any Office request: read the inputs, work out what the user wants
  (a theme, a new deck, document or workbook, an edit, expansion, revision or
  restyle of an existing file, a check or a repair), map the decisions, ask once
  and run the right workflows in order. TRIGGER WHEN: an Office request does not
  name one format workflow, combines several deliverables, or starts from files,
  websites or notes whose use is not yet clear.
argument-hint: "<what you want, with any files, URLs or notes>"
---

Handle the Office request in: $ARGUMENTS

Load `office:intake` and `work-controller:work-record`, then follow intake's
`references/routing.md`: inventory and read every input, name the destination,
route to workflows and operations, settle every decision the request and the
inputs supply, then ask the remaining decisions in one round in the work
record's question shape, recorded before they are put.

Run the routed work here, in order, as the coordinator of each method. This
entry declares every Office role, so the dispatch bindings each method requires
are available in this context:

- `presentation`: follow `office:pptx`, dispatching `office:content-strategist`,
  `office:presentation-designer` and `office:presentation-reviewer` as it
  specifies for the operation.
- `document`: follow `office:docx`, dispatching `office:document-designer` and
  `office:document-reviewer` as it specifies for the operation.
- `workbook`: follow `office:xlsx`.
- `theme`: follow `office:design`'s template procedure.
- `verify` and `fix`: follow `office:integrity`.

Each method takes its recorded brief as its intake round and runs only the steps
of its operation. Pass outputs forward: a generated theme is the base of the
deck or document that follows; a document and a deck from one brief share one
design record. Never overwrite a supplied file. A worker's stopped turn is not a
delivery; missing runtime, isolation or reviewer evidence blocks its dependent
step and must appear in the result.

Deliver every destination with its own review or report, the route and the
decisions as finally recorded, and the checks that remained unverified.
