# Presentation design library

Slide-native design reference for the presentation method. Read this index with
`pptx-compatibility.md` before creative work, then open the two fragments it
routes to. Adapt every choice to user-supplied brand assets, an existing deck or
a corporate template when provided.

- `office:design`'s `references/directions.md` — visual directions A to T with
  rhythm, font pairing and default palette seeds; the file's palette itself is
  built by `office:design` from the user's colour source.
- `layout-patterns.md` — patterns 1 to 18 by communication job, each with its
  slots, variation axes and requirements.

A deck combines **one argument mode**, **one visual direction** and **one pattern
per slide**, chosen by that slide's job. The mode decides how the deck argues,
the direction how it looks, the pattern how each slide is laid out. The three are
independent, so the library covers their combinations instead of one hand-built
template per deck. Keep one mode and one direction for the whole deck; vary
patterns across slides.

## Choose the argument mode

Choose the mode from the audience and purpose settled at intake, and record it
with the direction.

| Mode | Use when | Content slide headline | Sequence |
|---|---|---|---|
| Pyramid | A recommendation or decision for executives, a board or a client | Action headline: the takeaway as a full sentence | Answer first, then supporting arguments, then evidence |
| Narrative | Persuading or rallying: pitch, vision, change programme | Story beat: a claim that moves the story on | Situation, complication, resolution, ending on the ask |
| Instructional | Training, onboarding, a procedure | Numbered task or step label | Goal, steps in order, check or recap |
| Showcase | Portfolio, product, launch, image-led decks | Short label, or none when the visual carries the slide | One focal item per slide, alternating hero and detail slides |
| Briefing | Status reports, updates, decks read without a presenter | Topic label plus a one-line status | Fixed sections in a stable order, same slots in every edition |

A deck derived from an existing one keeps the source's mode unless the brief
changes its purpose.

This library is Office's own design guidance and applies to every construction
path. `office:design` supplies the accepted direction, the chosen palette by role
and the pairing, including supplied brands/templates. A direction supplies
composition and rhythm; map its slots to the chosen palette's roles, never to the
direction's default seeds. Map engine design tokens to the same record and record
any necessary supported substitution. Resolve an actual conflict before building.
Region sketches and the sketch-to-specification handoff live with the patterns
in `layout-patterns.md`; the slide-object specification itself lives in
`pptx-compatibility.md`.

## Canvas geometry and typography scale

Design for the fixed `16:9` widescreen canvas (`13.333 in x 7.5 in`, `1920 x 1080 px`)
unless the brief, an existing deck or a corporate template specifies another ratio:

1. **Margins and spacing**: keep at least `0.6 in` (`86 px`) left/right margin and
   `0.5 in` (`72 px`) top/bottom margin. Leave at least `0.25 in` (`36 px`) gap
   between cards, columns and chart containers. Keep at least 25% of each slide as
   open background so content breathes.
2. **Headline set by the argument mode**: in pyramid and narrative decks, state
   each content slide's takeaway in one complete line or two short lines
   (`26 to 34 pt` bold), never a vague topic label alone. Instructional, showcase
   and briefing decks use their mode's headline at the same scale. Place a short
   section kicker (`11 to 13 pt` uppercase or accent bold) above the headline
   when helpful.
3. **Readable body and data scale**:
   - Cover title: `40 to 52 pt` bold; subtitle/context: `18 to 22 pt`.
   - Card titles and table headers: `16 to 20 pt` bold.
   - Body copy and table cells: `14 to 18 pt` regular (never below `13 pt`).
   - Chart axis labels, data labels and footnotes: `11 to 13 pt` with high contrast.
4. **Density caps**: at most 4 cards or text columns per slide, at most 5 bullets
   or 6 lines inside any text box, and at most 7 nodes in a process or
   architecture diagram. Repeated slots follow their pattern's range in
   `layout-patterns.md` (for example 3 to 6 timeline periods, 4 to 7 table
   rows). Split overloaded content across two slides rather than shrinking text.

## What every pattern entry specifies

For each chosen pattern, record the slide's objects in the designer's report
before construction under the single slide-object specification of
`pptx-compatibility.md` (identity and purpose, geometry, typography,
representation, editability, engine evidence).

## Choose the visual direction, then the patterns

1. Take the direction, palette and pairing from the `office:design` record; the
   palette's `check` already holds `4.5:1` for text, and the deck never carries
   meaning by colour alone. With brand assets or a corporate template, use their
   palette and fonts and keep the rest of these rules.
2. Route each slide to the pattern that matches its job in `layout-patterns.md`:
   orient, explain, compare, show evidence, plan or request a decision.
3. Vary composition across consecutive slides; two adjacent slides with the same
   pattern need a content reason, not a stylistic one.
4. Record the deck's mode and direction and each slide's pattern, so an edit or a
   reviewer can verify the deck against its plan.

Use real content to establish a direction, then vary composition with each
slide's communication job. Preserve brand constraints and readable labels. Offer
alternatives only to resolve a material choice. Reusable page types demonstrate
native editable content.

Provenance: separating argument mode, identity, style and layout is informed by
[PPT Master](https://github.com/hugohe3/ppt-master) (MIT). No code, prompts,
template library or installation workflow from that project is bundled.
SlidePoise retains its upstream profiles and composition method.
