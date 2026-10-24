<!-- Adapted from marcmarti9/agentit, skills/typography-and-layout/SKILL.md,
revision fc38111622ac459ccf843234863bd0b8fcb6ebfd (Apache-2.0).
Modified for native Word/PowerPoint layout and Office production ownership.
Attribution and retained licenses: agentit-upstream.md in this directory. -->

# Typography and layout for Office

Make text serve reading, hierarchy and the actual medium. Pair with
`editorial-design.md` for reading architecture. Define typography within the
existing document brief or presentation design report; `office:docx` and
`office:presentation-design` retain editable-file production and verification.
This method is not a brand redesign, copy rewrite or extra production engine.

## Establish constraints

Record content class, audience, language/scripts, page size or slide canvas,
delivery context, brand rules and available fonts. Honor approved faces and
template styles. The direction recorded at intake supplies the palette and
the pairing from `font-pairings.md`; a supplied brand or template replaces both.

Check font family, version, real weights and italics, glyph coverage and permitted
use in the intended output. Choose a compatible available fallback and inspect
its metrics. Naming a font in a preset or seeing it in a PDF does not install it,
prove embedding or grant redistribution rights.

## Procedure

1. Inspect representative real content. Identify headings, body, labels, data,
   captions, code and non-Latin or numeric needs. Use the fewest roles that
   communicate the structure, without a fixed limit on font families.
2. Select or retain faces for legibility, available styles, script coverage and
   licensed use. State the purpose and fallback of each role. Do not require
   paid-font hunting or reject a face merely because it is familiar.
3. Define a role scale with sizes in points, weights, line spacing and paragraph
   spacing. Make hierarchy discernible without a universal size ratio or color
   alone. Use supported real bold/italic styles instead of synthetic variants.
4. Set reading measure from actual content and font metrics. Sustained prose
   needs a comfortable column; tables, diagrams and code may justify another
   width. Choose paragraph spacing or first-line indentation deliberately.
5. Use a small set of spacing decisions for headings, captions, lists and figures.
   A heading must visibly belong to its content. Align labels and numeric data
   for their task; avoid ornamental tracking that repairs an unsuitable measure.
6. Map the roles to native format settings below. Recompose dense material by
   changing its structure, splitting a slide or adjusting a table; do not simply
   shrink all text until it fits. Preserve approved meaning and source links.
7. Embed non-Office fonts through `SKILL.md`'s `font_embed.py` step when the
   engine is available, and record the inspection result, not just a requested flag.
8. Render dense, sparse and long-label cases from the saved DOCX or PPTX. Inspect
   overflow, contrast, hierarchy, line length and fallback-induced changes. Check
   slides at the intended projection size and documents at normal reading scale.
9. Record role/style mapping, font status, scale, measure, spacing, relevant
   renders and gaps in the existing design record. Keep copy-change requests
   separate from typographic corrections.

## Map to native objects

| Format | Required layout decisions | Avoid |
|---|---|---|
| DOCX | Native paragraph/character styles and inheritance; section margins and columns; paragraph spacing, keep-with-next, widow/orphan controls; table widths and repeating headers | Blank-line padding, manual spaces, typed bullet symbols or floating boxes for normal body flow |
| PPTX | Fixed text-frame geometry, padding, wrapping and alignment; explicit point sizes; native text, charts, tables and shapes where editability is required | Browser breakpoints, CSS effects without an engine equivalent, or a full-slide raster replacement for editable content |

For a table exceeding its column, revise column widths, orientation or section
layout, or split it with clear continuation labels. A slide cannot rely on
scrolling or hover to expose clipped content. A DOCX reading on a smaller screen
does not imply the fixed page will reflow like a responsive website.

Respect the native-object and target-renderer rules in
`${CLAUDE_PLUGIN_ROOT}/skills/presentation-design/references/pptx-compatibility.md`
for PPTX. Use `office:docx` for actual field updates, pagination and source
preservation. Do not substitute a browser proof for the saved artifact render.

## Craft and evidence

Check distinguishable heading levels, readable captions and sources, suitable
numeric alignment, paragraph shapes and consistent spacing. Hyphenation, quotes,
dates and language conventions follow the approved house style. Avoid decorative
all-caps paragraphs and manual line breaks that collapse under small edits.

If content, fonts or a compatible renderer are unavailable, provide a conditional
style specification with the missing verification named. Source markup alone
does not prove accessibility, font embedding, pagination or PowerPoint fidelity.
The production owner retains the existing saved-file and delivery gates.
