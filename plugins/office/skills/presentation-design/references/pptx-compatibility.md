# Design for editable PowerPoint

Apply this contract before consulting creative providers, generating reference
images or constructing slide objects. It governs Office's presentation output,
including the guidance taken from Frontend Design, Impeccable, Taste or another
explicitly selected provider. Providers supply visual judgment; Office owns the
slide specification and verifies it against the chosen construction engine.

## Establish the target before design

- Preserve an existing deck's slide size, theme, master/layout relationships and
  required native features. For a new deck, use the requested dimensions; when
  unspecified, record a fixed 16:9 canvas as the default. Do not design a
  responsive page and assume it will convert to a fixed slide.
- Record the construction engine and version, intended viewing application,
  available preview renderer and required editability. Distinguish capabilities
  verified in the installed engine from assumptions. Check the commands or
  reconstruction types needed for the proposed composition before accepting it.
- Resolve font families and weights available to construction and target
  rendering. Preserve a supplied template's typography. Record any substitution
  and recheck line breaks; do not promise font embedding or a font available on
  another computer without evidence.
- Prefer well-supported native text, basic shapes, connectors, tables and charts.
  A specialized effect, chart type, master feature, SVG or media feature needs
  evidence in the selected engine and target renderer. An exported PPTX alone is
  not that evidence. Unsupported elements must be redesigned within the brief
  or reported before construction, rather than silently simplified on export.

For a narrow edit or export, establish only the constraints needed for the
requested changes and preservation. Do not initiate a redesign of untouched pages.

## Specify slide objects, not a website

The designer's existing report carries the slide specification; do not introduce
a second construction schema. Use slide IDs and one declared coordinate unit
and origin. For each meaningful element, provide:

| Field | Required content |
|---|---|
| Identity and purpose | Slide/object identity, communication role, exact content and source |
| Geometry | x/y position, width/height, margins or padding, alignment and stacking order |
| Typography | Font family/weight, size, line spacing and intended line breaks or fit constraints |
| Representation | Native text, shape, connector, table or chart; or a separate image asset with crop and placement |
| Editability | What must remain editable, including chart series/data and table cells |
| Engine evidence | Supported construction operation/type and any unresolved feature or target-renderer limitation |

Translate web-inspired layout into this fixed slide specification before
generation. CSS flex/grid, browser viewport units, DOM structure, hover states,
scroll effects and responsive breakpoints are not PowerPoint construction
instructions. Express their useful visual intent through fixed geometry and
static compositions. Treat animation as a separate, explicitly requested feature
with verified support. Use gradients, shadows, transparency and clipping only
where the chosen engine and target renderer preserve them; otherwise design a
supported visual equivalent without changing the accepted message or brand.

Keep text readable at presentation size with room for the actual content.
Measure text fit and revise the layout before shrinking type. Build native charts
from the authoritative source data, preserving labels, units and series rather
than tracing generated pixels. Build requested editable tables with native cells
and editable diagrams with shapes/connectors whose relationships are preserved.

Photographs, textures and illustrations may be separate images. Keep essential
titles, body text, data labels, charts and tables native when their meaning or the
brief requires editing. Do not flatten a complete slide, convert required text to
outlines, or silently rasterize editable objects to improve visual similarity.
An image or SVG inside a PPTX is not proof of native object editability. A change
to requested editability needs the user's decision if no compatible authorized
construction route remains. Continue independent work while that decision is open.

## Carry constraints through image generation and construction

Pass the accepted slide specification and supported-feature limits into
SlidePoise's planning context and compiled image request. Keep its upstream
semantic-map, measurement and construction contracts authoritative; do not invent
fields or replace its compiler. Reference imagery must respect the fixed canvas,
text regions, margins and native-object plan. Inspect generated references for
reconstructability before extending the direction across the deck. Correct an
incompatible reference rather than accepting a design the engine cannot build.

Generated or edited images must use the exposed harness image tool under
`image-tools.md`. A provider's image script, image-search utility or web workflow
does not replace that obligation. Preserve source wording, figures, logos and
approved assets when reconstruction corrects mistakes in a generated reference.

When DeckCraft constructs or edits objects, map the same specification to its
actual discovered commands. Preserve source objects and allowed-change limits.
There is no general HTML/CSS-to-PPTX converter in this integration. Do not
round-trip a finished SlidePoise deck through DeckCraft merely to claim
compatibility; each save needs the preservation checks required by that engine.

## Verify appearance and editability separately

Render the actual saved candidate and compare every page with the accepted
design and source content. Review bounds, alignment, line breaks, clipping,
spacing, color, image crops, charts and connector relationships. For a reusable
template, exercise representative page types with real content. Fix material
differences, rebuild and repeat the review for the changed candidate.

Inspect native objects, text, table cells and chart data separately. Same-engine
round-trip renders and object counts cannot prove cross-application fidelity or
editability. Report design-reference comparison, selected-engine preview and
target-application verification as separate evidence. To claim fidelity in
Microsoft PowerPoint, open/render the actual candidate there and record the
version and font environment. If it is unavailable, report PowerPoint fidelity
as unverified while delivering the available candidate and preview evidence.

Do not promise pixel-perfect equivalence from a generated image, a browser
preview, valid OOXML, unit tests or a DeckCraft render. An exact comparison claim
must name the candidate, reference, renderer, fonts, resolution, comparison
method and measured result. Never improve that score by sacrificing required
native content. The final review records any visual or editability compromises.
