<!-- Adapted from claude-office-skills/skills, ppt-visual/SKILL.md, MIT.
Revision 9c4c7d5cd2813a8936bf2c9fdb174ea883b85a11.
Modified for Office shared themes, native objects and the existing design report.
Full retained license: LICENSE-ppt-visual-MIT.txt. -->

# PPT Visual composition handoff

Use these adapted wireframes to make the existing slide plan concrete. The
`office:presentation-designer` remains the PowerPoint design agent. Use the
palette and pairing of the `office:design` record. Keep `layout-patterns.md` as
the canonical pattern catalog and
`pptx-compatibility.md` as the native-object and geometry contract.
These are planning templates, not binary PPTX files or additional style presets.

## Wireframe choices

Map these compositions to the selected library pattern. Preserve the accepted
canvas/direction and vary placement only for a content reason. The brackets
below show regions, not raster images or an automatic reconstruction promise.

| Wireframe | Library pattern | Region sketch |
|---|---|---|
| Title | 1 Cover | `[ title + subtitle ] [ image/accent ]; [ author/date ] [ logo ]` |
| Statement | 3 Divider or 15 Quote, by purpose | `[ open space ]; [ main statement ]; [ attribution if quoted ]` |
| Three columns | 4 Executive summary | `[ action headline ]; [ lead + detail ] [ lead + detail ] [ lead + detail ]` |
| Split image/text | 14 Case study, or the chosen content pattern | `[ image ] [ headline + explanation ]; [ source ]` |
| Data highlight | 5 Key metric spotlight | `[ headline ]; [ primary value + unit/context ]; [ supporting values ]; [ source/period ]` |
| Timeline | 10 Timeline and roadmap | `[ headline ]; [ milestone ] -> [ milestone ] -> [ milestone ]; [ dates/owners ]` |
| Comparison | 7 Comparison matrix | `[ common criterion ]; [ option A ] [ option B ]; [ explicit conclusion ]` |
| Process | 11 Process flow | `[ headline ]; [ stage ] -> [ stage ] -> [ stage ]; [ handoff labels ]` |
| Quote with portrait | 15 Quote and testimonial | `[ exact quotation + attribution ] [ separate portrait ]; [ source ]` |

Use native text, shapes, connectors, charts or tables for editable meaning.
Photographs, textures and illustrations may be distinct image objects. Use a
native labeled shape instead of unsupported SmartArt when that preserves the
requested editability. Record limitations before construction. Motion is optional
and only planned when requested and supported by the actual engine.

## Return a concrete layout for each slide

Add the following to the existing design report, not a second report:

1. Stable slide ID, communication job, headline, selected pattern and wireframe.
2. A small region sketch using real content labels, with reading order and
   the reason for the chosen arrangement. Existing pattern variants are enough;
   do not generate competing designs for every slide.
3. Slot-level placement: declared origin/units, `x`, `y`, width, height, padding,
   alignment and layering. Bind every region to supported native objects under
   `pptx-compatibility.md`, rather than leaving approximate positions to the builder.
4. Exact accepted text, font role/size/weight and shared semantic color token for
   each slot. Keep theme identity visible; do not select a second palette here.
5. Native data, object editability, source notes and chart/table labels. Use real
   values and citations, not the upstream example's illustrative growth figures.
6. Needed image/icon descriptions, crop, dimensions, intended placement and
   provenance. Choose supplied/reused, searched or generated/edited assets under
   `image-tools.md`. The coordinator calls the active harness image tool for the
   generated/edit route; the designer does not call another image service.
7. Construction notes, overflow/splitting behavior, unsupported effects and review
   checks. The saved candidate still requires actual rendering and native-object
   verification. Wireframes and reference images cannot certify either.

For a reusable presentation template, supply representative editable cover,
content, evidence and closing layouts as needed, plus replacement instructions.
This is a design specification until the producer builds the exemplar. Do not
call it POTX or a master-layout system without verified support.

## Adaptation and upkeep

Source: [PPT Visual](https://github.com/claude-office-skills/skills/blob/9c4c7d5cd2813a8936bf2c9fdb174ea883b85a11/ppt-visual/SKILL.md).
The upstream supplies nine wireframes and a slide-specification format, not a
binary template pack. This adaptation retains those composition ideas and
handoff structure, maps them to Office's existing patterns, and delegates palette
and font selection to `office:design`. It omits foreign models/MCP tools, separate
color/font catalogs, automatic image-library sourcing and universal design slogans.
The exact MIT license ships beside this reference. This is a pinned adapted
snapshot; review upstream manually when requested or when a concrete need arises.
