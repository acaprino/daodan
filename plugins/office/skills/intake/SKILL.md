---
name: intake
description: >
  Shared contextual interview for every Office workflow: resolve where the work
  starts, how much it changes and what is delivered, then pick the route the
  format method executes. TRIGGER WHEN: an Office presentation, document or
  workbook task begins. DO NOT TRIGGER WHEN: a format method is already executing
  a resolved route.
---

# Office intake

Resolve the task before choosing a format method, engine or worker. This
interview serves every Office format; each format method adds only the questions
that belong to its own format.

## Resolve the starting point

- **Nothing:** a brief, notes, data or sources become a new file.
- **An existing file:** either the base for a new file or the file to revise.
  When it is a base, record what carries over: content, structure, visual
  identity or all of them.

Never overwrite a supplied file. Write every result to a separate candidate path.

## Resolve the depth of change

| Route | Typical requests | What follows |
|---|---|---|
| Substantial | New file, file derived from an existing one, template, restyle, restructure, rewrite, shorten or lengthen | `office:design` decisions (direction, palette from the user's colour source, pairing, argument mode), the format's designer where it declares one, production and rendered review |
| Narrow | A local wording, figure, formatting or added-element change inside the accepted design | Preserve the existing design; no design decisions or designer dispatch |
| Read-only | Read, analyze, review, preview or export | No write to the source; deliver findings or the requested export |

Shortening and restructuring are substantial because they change sequence and
composition. If a narrow change turns out to need a new design decision, raise
it with the user rather than redesigning silently. A read-only request
authorizes no edit.

## Ask once

Inspect supplied files before asking about them. Infer what the request and the
files already settle, then ask the remaining decisions that change the result in
one round, together with the format method's questions. On the substantial
route that round includes the design decisions of `office:design`: the argument
mode, the direction (or the supplied brand or template), and the colour source
for the palette: an image, a website, the project's stylesheets or design
tokens, an existing PPTX or DOCX, a description in words, or none. Palette
candidates are shown and chosen after this round, not asked here. State the
inferred choices instead of asking about them again. A complete or explicitly autonomous
request needs no questions. Ask again only when new evidence changes a decision
materially.

## Record the route

Record in the task brief: starting point, carry-over, route, deliverable (file,
findings or export) and the inferred choices. When an existing file is a base or
is shortened, also record the approved cuts: the source content the user agreed
to drop. Everything else in the source must reach the result. The format method executes that
route. A later request that changes the route re-enters this step.
