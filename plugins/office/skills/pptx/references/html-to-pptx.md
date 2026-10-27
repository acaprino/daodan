# HTML to PPTX conversion

Build a native deck mechanically from an approved HTML design instead of
transcribing it into engine commands. The conversion runs the vendored
open-slide exporter (`lib/open-slide-pptx/UPSTREAM.md`) inside a headless
browser page: text becomes native text boxes, boxes and borders become shapes,
images become pictures, and speaker notes come from the panel attribute. The
model authors the HTML once and never rewrites objects per slide.

Use it for construction: a new deck, a restyle, or a proposal proof that needs a
saved native candidate. Do not use it to edit an existing deck, for the
read-only route, or when the accepted design has no HTML source. Editing,
coverage and preservation stay with `office:deckcraft` on the saved file.

## Input contract

One self-contained HTML file. Every slide is one element marked
`data-office-slide`, in deck order:

- exactly 1920x1080 CSS pixels, `box-sizing: border-box`, with
  `position: relative` (or absolute/fixed) on the panel itself;
- self-contained: no rule that depends on a parent or sibling selector, because
  each panel is measured on its own;
- `overflow: hidden`, since the canvas is the slide edge;
- optional `data-office-notes="..."` for that slide's speaker notes;
- local assets only, resolved from the HTML directory or `--assets-root`;
- installed or locally embedded fonts. A webfont URL is blocked and recorded.

The converter refuses the whole run on a contract violation instead of scaling
or repairing a panel, and it names each offending panel. Requests outside the
local origin are aborted and listed in the evidence, so a conversion never
fetches a remote resource.

## Commands

```text
python "${CLAUDE_PLUGIN_ROOT}/skills/pptx/scripts/pptx_convert_bridge.py" probe
python "${CLAUDE_PLUGIN_ROOT}/skills/pptx/scripts/pptx_convert_bridge.py" convert \
  --html design.html --output candidate.pptx --evidence candidate.conversion.json
```

Optional: `--assets-root`, `--browser`, `--timeout-ms`, `--headed`, `--node`.
The bridge verifies the vendored hashes before every run, so an edited vendor
fails here rather than converting silently.

## Runtime prerequisites

- Node `^20.19.0` or `>=22.12.0`; `OFFICE_PPTX_NODE` overrides discovery.
- The Playwright Node module; `OFFICE_PPTX_PLAYWRIGHT` may point at a directory
  that contains it (`npm install playwright` in any directory works).
- A Chrome, Edge or Chromium executable; `OFFICE_PPTX_BROWSER` overrides the
  known installation paths, otherwise the Playwright-managed browser is used
  (`npx playwright install chromium`).

A missing runtime is a stop with these instructions and a recorded blocker. It
is not a silent fallback to another construction path; if the coordinator builds
the deck another way, the report says which path ran and why.

## Outputs and evidence

The saved `.pptx` plus one `office/pptx-html-conversion/v1` record carrying the
HTML and bundle hashes, the engine pin, Node/Playwright/browser versions, the
viewport, panel and part counts, the per-slide scene summary (node kinds,
background, notes), image inventory, conversion time, console warnings, page
errors, blocked and missing local requests, and its own limits. Verify the
package with `office:deckcraft`'s `pptx_inspect.py`, then render and review it
under `pptx-compatibility.md` like any other candidate.

## What it proves and what it does not

Native text objects, shapes, pictures and notes exist in the saved package, and
the conversion is deterministic with no model call. It does not prove visual
fidelity, Microsoft PowerPoint behavior, or that the design survived: the
independent rendered review still owns that verdict. Known losses: no native
PPTX table (a measured HTML table becomes shapes and text), vector effects the
exporter cannot express are rasterized, and an SVG image is kept as a PNG with
its original SVG alongside. Fonts are declared, never embedded here; embedding
still uses `office:design`'s `font_embed.py` on a separate candidate.
