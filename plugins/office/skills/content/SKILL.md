---
name: content
description: >
  Shared editorial method for requested Word documents and PowerPoint decks:
  source and claim ledger, transformation permissions, logical sequence and
  format projections in a validated CONTENT.md. Use after Office intake;
  revisions inherit accepted decisions and local edits change only their scope.
---

# Office content

Own what the work communicates: intent, goal, audience, market, channel, scope,
depth, extent, density and tone. Take settled decisions from intake. Preserve
source conditions, uncertainty, conflicts and locked wording; report gaps
instead of inventing evidence. Design owns visual identity; each format owns
native composition, production and saved-file review.

1. Read the actual sources and accepted records. Record stable source IDs,
   original-byte SHA-256 values, material roles and precise claim locators.
   Classify claims as core, supporting or optional, with conditions, conflicts
   and locks. Record optional omissions in the format plan.
2. Define each content unit's message, complete text, claims, relationship,
   detail and permitted transformation. Sequence the units for the audience's
   understanding or decision. Use the least transformation that meets the brief;
   keep locked claims in dedicated verbatim units. Trace substantive changes
   per unit to sources, destination and reason.
3. Read only requested format structure references: DOCX uses
   `../docx/references/structure.md`; PPTX uses
   `../pptx/references/structure.md` and its existing `content-planning.md`.
   Write DOCX sections or bind units to the existing PPTX plan's stable slide
   and claim IDs. Share facts and identity without assuming page-slide parity.
4. Follow `references/records.md` to serialize and explicitly load/validate
   `CONTENT.md`. Pass the actual PPTX plan when requested. Every core claim
   reaches each requested format or carries an authorized, sourced exclusion.
   Hand producers the exact record revision and requested projection.
5. Review source fidelity independently of the structural check. Revisions and
   expansions inherit accepted decisions and change the required delta; restyle,
   review and export reuse content. A local edit does not reopen global strategy.

```text
python "${CLAUDE_PLUGIN_ROOT}/skills/content/scripts/office_records.py" write CONTENT.json --out CONTENT.md
python "${CLAUDE_PLUGIN_ROOT}/skills/content/scripts/office_records.py" validate CONTENT.md
python "${CLAUDE_PLUGIN_ROOT}/skills/content/scripts/office_records.py" validate CONTENT.md --pptx-plan plan.json
```

Only the last command verifies supplied plan bindings. Load saved records with
`load_record(Path(...))` before using their contents; a filename alone supplies
no evidence. Increment revision for changed editorial decisions and update all
projection bindings. Preserve accepted artifacts, produce new candidates, and
report missing evidence or capability to the coordinator. Structural success
does not establish source fidelity, editability, rendering or application fidelity.
