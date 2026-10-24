<!-- Adapted from marcmarti9/agentit, skills/editorial-design/SKILL.md,
revision fc38111622ac459ccf843234863bd0b8fcb6ebfd (Apache-2.0).
Modified for Office native formats, production ownership and harness image tools.
See agentit-upstream.md for attribution, licenses and sync boundaries. -->

# Editorial design for Office

Design how a reader enters, navigates and retains a story. Own the editorial
concept, hierarchy, sequence and reading furniture. Pair with `typography.md`
for typography and spatial decisions.
`office:docx` owns native Word production; `office:presentation-design` coordinates
PPTX production through the selected engine. This skill adds no worker or engine.

## Inputs and boundary

Use approved content or an explicitly provisional outline, audience, reading
setting, figures/tables/quotes/notes, brand constraints and target format. Preserve
meaning, accepted wording, facts and attribution. Missing evidence permits a
provisional structure, not invented claims. Keep one existing document brief or
presentation design report; do not create a second reporting pipeline.

Preserve an accepted brand, template or direction. The direction recorded at
intake (`directions.md`) supplies palette and pairing; this method decides
composition under it. Do not replace the accepted direction or a Word template
silently.

## Procedure

1. Define the reading job: what the reader should understand or decide at the
   opening, middle and close. Map sections or slide roles before styling.
2. Assign content roles: title, standfirst, headings, body, captions, callouts,
   notes, source lines and navigation. Pair their hierarchy with
   `typography.md` rather than choosing sizes independently.
3. Design entry and re-entry points. Use a lead, meaningful headings, contents or
   running cues where the document's length warrants them. Avoid ceremonial
   navigation on a short sequential read.
4. Give every figure a communication job, source, caption and nearby explanation.
   Choose inset, breakout or full-width treatment deliberately. Preserve readable
   labels and native editable data when required. A pull quote must earn its space.
5. Vary reading, evidence, rest and emphasis. Use whitespace, crop, scale and
   pacing to serve the argument. Avoid repeating one layout or applying a universal
   ratio. Choose a composition from the content, not from decoration.
6. Adapt to the medium using the native-format rules below. A live deck needs a
   clear claim per slide and presenter context; circulation needs enough labels,
   sources and context to stand alone.
7. Review actual saved-file renders with realistic content. Check reading order,
   sequence, captions, headings, contrast, crop, overflow and intended viewing
   distance. A design sketch or generated reference image is not this evidence.
8. Record reading map, style roles, figure associations, chosen theme, native
   representations and remaining checks in the existing brief or design report.

## Native-format rules

| Target | Composition | Production evidence |
|---|---|---|
| DOCX | Flowing paragraphs with native heading styles, sections, lists, captions and tables; intentional page size, margins and breaks | Render the saved DOCX; inspect pagination, heading attachment, table splits, footers and references |
| PPTX | Fixed canvas with explicit object geometry; the recorded direction and a justified pattern per slide | Follow the presentation compatibility brief; verify editable objects and inspect actual candidate slide renders |
| Reusable template | Representative page/slide types with realistic content, stable role names and reuse guidance | Verify what the selected engine actually preserves; do not claim untested master-layout or template-format support |

Do not build a website and assume conversion preserves its layout pixel for pixel.
For PPTX, read
`${CLAUDE_PLUGIN_ROOT}/skills/presentation-design/references/pptx-compatibility.md`
and honor its editability and target-application evidence rules. For DOCX, prefer
native flow and styles over floating text boxes used to imitate a screenshot.

For generated or edited imagery, use the active harness image tool under
`${CLAUDE_PLUGIN_ROOT}/skills/presentation-design/references/image-tools.md`.
Return image intent, reference assets, crop and placement to the existing
production owner. Presentation workers request images from the coordinator;
they do not call another generator or start a second agent workflow.

## Review and handoff

Give the production owner the content map, source associations, hierarchy,
figure/caption links, medium-specific layout choices and unresolved decisions.
Keep dense research traceable; make projected claims readable from the stated
distance. Do not quietly rewrite approved content to repair layout.

For ordinary printing, inspect the actual paginated export. Commercial press
claims additionally need the printer's written process, profile, stock, trim,
bleed, safety, binding, ink limits and proof specification. Without these, label
the print concept provisional; do not invent production values.

Editorial guidance does not certify an editable file, accessibility, font
embedding, exact pagination or print readiness. Record observed renders and
unavailable checks separately. Complete this design contribution when the reading
map, meaningful figure associations and medium-specific choices are explicit;
the existing production method retains its file and delivery gates.
