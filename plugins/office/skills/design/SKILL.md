---
name: design
description: >
  Design a shared visual identity for requested Office documents and decks:
  Taste art direction, real native proposal comparison, explicit DESIGN.md
  selection, semantic palette, typography, imagery and native theme handoff.
  Use when intake calls for a new look; revisions inherit accepted decisions.
license: Apache-2.0
---

<!-- The editorial and typography references are adapted from marcmarti9/agentit
(Apache-2.0); directions Q to T carry seed palettes from anthropics/skills Theme
Factory (Apache-2.0). See references/agentit-upstream.md and
references/theme-factory-upstream.md for attribution and retained licenses. -->

# Office visual design

Own the shared visual system. `office:content` owns intent, audience, market,
claims, depth and logical sequence; DOCX/PPTX designers own final composition
and native geometry. This skill adds no worker or engine. One brief can yield
both formats with the same selected design and independent layouts.

## Preserve or design

Read the brief, material roles and accepted content/design records. New work,
restyle or a derivation without inherited look designs an identity for the
actual subject, audience, brand and requested formats. Expansion and revision
inherit accepted direction, palette, type and template; skip new proposals,
font installation and template generation unless their authorized scope changes
them. Narrow edits and read-only work retain the accepted look.

For a new look, follow the single Taste input/output and proposal-review contract
in `references/art-direction.md`. It consumes the settled Office brief and returns
our design payloads; it adds no intake, editorial strategy or production engine.

When inherited content identity/revision or requested formats change, use the
inherited-design rebinding procedure in `references/records.md`. Keep the visual
choice and predecessor intact while publishing a correctly bound new record.

Use `references/directions.md` and `references/font-pairings.md` as resources,
not compulsory letters, pairings or presets. Derive the palette through the
sample, converge and justify steps in `directions.md` before keeping any seed,
and keep the proposal set spread across its temperatures. Proposals may adapt
compatible principles into one coherent identity. `references/diagram-style.md`
supplies the colour roles, node treatments, strokes, grid and label sizes for
diagrams built from native shapes. A supplied brand or template always wins;
inherit its masters/styles and record actual colors/fonts. Separate observed
source values from proposed additions; record justified fallbacks.

## Prepare usable palettes

Extract the user's color source with the existing helpers:

```text
python "${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/palette.py" from-image LOGO.png
python "${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/palette.py" from-url https://example.com
python "${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/palette.py" from-css PROJECT-OR-STYLESHEET
python "${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/palette.py" from-file EXISTING.docx
python "${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/palette.py" candidates --seed "#1D4ED8" > palettes.json
python "${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/palette.py" check selected-palette.json
```

For words or no source, choose and justify seeds from the brief; the script does
not interpret language. Candidate generation can report failed checks. Inspect
`check.passes` and diagnostics, extract the actual palette object to
`selected-palette.json`, filter failed candidates or refine their colors/
data categories, then rerun `palette.py check` on the actual palette. Never select
`faithful` or another variant merely because it was generated. Preserve text
contrast of `4.5:1`, data contrast of `3:1` and the helper's distinctness/CVD checks;
do not claim a passing palette before observing its result. A binding brand
conflict needs a supported treatment or recorded decision, not silent recoloring.

`palette_preview.py` remains an optional chromatic helper:

```text
python "${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/palette_preview.py" palettes.json --out palette-compare.html --open
```

It shows fixed palette examples and cannot record a choice. It does not satisfy
the complete visual-system comparison below.

## Prove, compare and select the complete system

Follow `references/art-direction.md` for the bounded Taste contribution and
`references/records.md` for the v2 proposal/CLI contract. Author two or three
complete unselected DESIGN payloads on the exact editorial working revision.
Give each a subject-specific idea and coherent type, palette, imagery, form and
data treatment. Use the same complete real content, sources and representative
jobs in only the requested formats; a table/evidence job can be inapplicable
with its recorded reason, never invented. A recolor or font swap is not another
compositional direction. Detailed hierarchy/type guidance stays in
`references/editorial-design.md` and `references/typography.md`.

Dispatch the existing format designers and reviewers in `proposal` mode under
the art-direction contract. Resolve authorized image requests before building
separate native specimens, inspect their saved renders and repair failed
creative proposals. Cover the opening and difficult real-content jobs, not just
an attractive cover. Assemble the exact reviewed native frames and bindings as
`office/design-candidates/v2`. V1 is a limited theme sampler and cannot satisfy
this complete creative comparison.

```text
python "${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/design_compare.py" candidates.json --out COMPARE.html
python "${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/design_compare.py" candidates.json --select technical --authority user --source "Decision Q2" --out DESIGN.md
python "${CLAUDE_PLUGIN_ROOT}/skills/content/scripts/office_records.py" validate DESIGN.md
```

Open and inspect the native-render gallery; keep its proof limits visible.
Record the user's explicit answer through the existing Work Controller question contract,
or select with `--authority autonomous` under an existing grant and cite its
source. Browser highlighting is not a returned answer. A compatible combination
is a new complete authored candidate with parent IDs and greater revision;
create fresh native proof and review it before selecting. No automatic merge
invents decisions.

Load the saved `DESIGN.md` through `office_records.load_record(Path(...))`, run
`validate_design`, and compare `project_id`, `content.project_id`,
`content.revision` and exact `formats` to the loaded content. The name alone
proves nothing. Pass this exact design revision to designers, producers and
reviewers in `final` mode. Revisions use new paths; never overwrite accepted
records.

The selected record owns semantic colors/proportions, type roles/fallbacks,
spacing principles, imagery, data, components and requested-format adaptations.
For PPTX the coordinator now fills the existing plan's display `direction` from
this selection, recomputes its `canonical-json-v1` binding, and freezes/validates
final `CONTENT.md` with that actual plan under the format method. This derived
binding finalization changes no claims or content revision. Editorial changes
return to the content owner. Shared design supplies no slide/page geometry.

## Materialize native styles and optional templates

Apply selected values through native styles, themes, masters and layouts. A
separate DOTX/POTX is optional for ordinary work; generate one when useful or
when reusable templates are requested. The existing kit can materialize a
compatible palette/font choice:

```text
python "${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/template_kit.py" BASE.potx --palette palettes.json --variant deep --pairing 2
python "${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/template_kit.py" BASE.dotx --palette palettes.json --variant deep --pairing 2 --page a4
```

Use the actual selected passing variant and supported font arguments; the
example does not select a project palette. Custom fonts use `--heading-font`
and `--body-font`. The kit's POTX has a master and nine pattern layouts; its
DOTX has native styles, page geometry and footer. Ordinary PPTX/DOCX bases and
`--samples` are supported. Preserve a supplied template instead of regenerating
it; `palette.py from-file` records its values. Render an actual sample before
claiming template behavior. Kit geometry does not override the designer's
accepted composition or the runtime's actual capabilities.

## Fonts and final-file evidence

Check selected families, real weights, glyph coverage, licenses, embedding
permissions and installed faces before construction. Reuse available approved
faces. Missing open faces can use the existing verified fetch/install helper
within the brief's dependency authority:

```text
python "${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/font_fetch.py" status "Inter:ital,wght@0,400;0,600;0,700;1,400"
python "${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/font_fetch.py" install "Inter:ital,wght@0,400;0,600;0,700;1,400"
python "${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/font_embed.py" embed CANDIDATE.pptx DELIVERY.pptx
python "${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/font_embed.py" inspect DELIVERY.pptx
```

`install` downloads only missing faces, verifies family/weight/style, embedded
open license and embedding permission, and installs for the current user. Record
installed faces and substitutions. Do not use a failed or unlicensed face;
record an approved compatible fallback. Render in an application started after
installation when needed.

Embedding saves a separate copy through installed Microsoft Word/PowerPoint on
Windows. PowerPoint embeds used characters, Word complete fonts. Missing engine
or embedding support is a named limit, not proof that fonts travelled. Complete
embedding before preservation checks, actual saved-file rendering and independent
review so they bind to the exact delivered copy. Read-only work never embeds into
the source. Contrast checks, HTML previews and structural records do not prove
editability, accessibility, pagination, embedding or target-application fidelity;
format methods retain those checks and disclose unavailable evidence.
