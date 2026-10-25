---
description: >
  Create a reusable PowerPoint or Word theme and template from any colour source
  (logo, website, stylesheets, an existing file, a description or nothing), or
  inherit one from a supplied file. TRIGGER WHEN: the user asks for a theme, a
  template, a slide master, a brand kit or a house style for decks or documents.
argument-hint: "<colour source or file to inherit> [pptx | docx | both] [font pairing or brand fonts]"
---

Create the theme requested in: $ARGUMENTS

Load `office:design`. Inspect a supplied file first. When the user supplies a
template or a file whose look must carry over, inherit it as direction `H`:
record its palette with `palette.py from-file`, keep its masters, layouts and
styles, and deliver it unchanged as the base. Otherwise ask once, in the
manner of `office:intake`, for what the request leaves open: the formats (deck,
document or both), the colour source and the font pairing or brand fonts.

Build the palette candidates from the colour source, show the comparison page
and record the user's choice; on an explicitly autonomous request choose as
`office:design` describes and say so. Install the pairing's fonts, then generate
the base with `template_kit.py` to a new path for each requested format, with
`--samples` for a second, sample copy to render.

Verify every generated file with `office:integrity`, render the sample copy with
the format's engine where available (`office:deckcraft`, `office:wordcraft`)
and inspect the renders. Deliver the `.potx` and `.dotx` bases, the sample
renders, the palette by role with its contrast check, the fonts with their
installation status and the kit report's layout-to-pattern map. Report any
check that was unavailable as unverified.
