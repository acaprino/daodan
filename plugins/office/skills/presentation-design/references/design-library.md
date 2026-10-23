# Presentation design library

Slide-native design reference for the presentation method. Read this index with
`pptx-compatibility.md` before creative work, then open the two fragments it
routes to. Adapt every choice to user-supplied brand assets, an existing deck or
a corporate template when provided.

- `visual-directions.md` — visual directions A to P with palettes, type pairings
  and layout rhythm.
- `layout-patterns.md` — patterns 1 to 18 by communication job, each with its
  slots, variation axes and requirements.

A deck combines **one visual direction** with **one pattern per slide**, chosen by
that slide's job. Directions and patterns are independent, so the library covers
direction x pattern combinations instead of one hand-built template per deck.
Keep one direction for the whole deck; vary patterns across slides.

This library is Office's own design guidance and applies to every construction
path. Where a selected engine ships its own design system (SlidePoise profiles,
an upstream template), prefer the engine's tokens and record the choice; use these
directions when the engine has none or the user asks for a library direction.

## Canvas geometry and typography scale

Design for the fixed `16:9` widescreen canvas (`13.333 in x 7.5 in`, `1920 x 1080 px`)
unless the brief, an existing deck or a corporate template specifies another ratio:

1. **Margins and spacing**: keep at least `0.6 in` (`96 px`) left/right margin and
   `0.5 in` (`54 px`) top/bottom margin. Leave at least `0.25 in` (`36 px`) gap
   between cards, columns and chart containers. Keep at least 25% of each slide as
   open background so content breathes.
2. **Action headline on every content slide**: state the takeaway in one complete
   line or two short lines (`26 to 34 pt` bold), never a vague topic label alone.
   Place a short section kicker (`11 to 13 pt` uppercase or accent bold) above the
   headline when helpful.
3. **Readable body and data scale**:
   - Cover title: `40 to 52 pt` bold; subtitle/context: `18 to 22 pt`.
   - Card titles and table headers: `16 to 20 pt` bold.
   - Body copy and table cells: `14 to 18 pt` regular (never below `13 pt`).
   - Chart axis labels, data labels and footnotes: `11 to 13 pt` with high contrast.
4. **Density caps**: at most 4 cards or columns per slide, at most 5 bullets or
   6 lines inside any text box, and at most 7 nodes in a process or architecture
   diagram. Split overloaded content across two slides rather than shrinking text.

## What every pattern entry specifies

For each chosen pattern, record these values for the slide in the designer's report
before construction, using the units and editability rules of
`pptx-compatibility.md`:

| Field | Content |
|---|---|
| Slide ID | Stable identity from the deck plan, not the current thumbnail order |
| Geometry | `x`/`y` position, width and height in one declared unit and origin |
| Typography | Font family, size, weight, alignment and colour token per slot |
| Representation | Native text, shape, connector, table or chart; or a separate image asset with crop and placement |
| Editable | What must stay editable, including chart series/data, table cells and diagram labels |
| Sources | Source data, citation or note each slot must carry |

## Choose the visual direction, then the patterns

1. Route to one direction with the context column of `visual-directions.md`;
   confirm the palette holds at least `4.5:1` contrast for body text and never
   carries meaning by colour alone. With brand assets or a corporate template,
   use their palette and fonts and keep the rest of these rules.
2. Route each slide to the pattern that matches its job in `layout-patterns.md`:
   orient, explain, compare, show evidence, plan or request a decision.
3. Vary composition across consecutive slides; two adjacent slides with the same
   pattern need a content reason, not a stylistic one.
4. Record which direction and which pattern each slide used, so an edit or a
   reviewer can verify the deck against its plan.
