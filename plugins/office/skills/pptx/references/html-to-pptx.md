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
- local assets only. Relative URLs resolve from the HTML's own directory;
  `--assets-root` widens what is served (shared brand files above the deck)
  and must contain the HTML, and `/`-rooted URLs resolve from it. Dotfiles are
  never served;
- installed or locally embedded fonts, never a webfont URL;
- animations and transitions are fast-forwarded to their end frame before
  measurement; script-drawn content declares readiness with
  `data-waitfor="<selector>"` on the panel or an inner element, and the
  converter waits up to 10 s for that selector to match.

The converter refuses the whole run (exit code 2) on a contract violation
instead of scaling or repairing a panel, and it names each offending panel: a
wrong canvas, a panel that measures no visible content, an animation or
`data-waitfor` target that does not settle, a page error, a missing local
asset, or any request outside the local origin. HTTP requests and WebSockets
outside that origin are aborted, service workers are blocked and no hostname
other than localhost resolves, so a conversion fetches nothing remote; a design
that tried is refused, not converted with silent losses.

## Commands

```text
python "${CLAUDE_PLUGIN_ROOT}/skills/pptx/scripts/pptx_convert_bridge.py" probe
python "${CLAUDE_PLUGIN_ROOT}/skills/pptx/scripts/pptx_convert_bridge.py" convert \
  --html design.html --output candidate.pptx --evidence candidate.conversion.json
```

Optional: `--assets-root`, `--browser`, `--timeout-ms`, `--headed`, `--node`.
The bridge verifies the vendored hashes before every run, so an edited vendor
fails here rather than converting silently; a checkout that converted line
endings is reported as such. An existing output or evidence path is refused:
each conversion writes a new candidate name, so a reviewed candidate and its
record stay intact. The bridge exits with the driver's code (2 job or design
contract, 3 missing runtime, 4 conversion failure), or 1 for its own checks
(arguments, an existing candidate, Node discovery, the hash guard).

## Runtime prerequisites

- Node `^20.19.0` or `>=22.12.0`; `OFFICE_PPTX_NODE` overrides discovery.
- The Playwright Node module, 1.48 or newer (WebSocket interception);
  `OFFICE_PPTX_PLAYWRIGHT` may point at a directory that contains it
  (`npm install playwright` in any directory works).
- A Chrome, Edge or Chromium executable. `--browser` or `OFFICE_PPTX_BROWSER`
  names one, and a named browser that does not exist is a stop, never a reason
  to pick another; otherwise the known installation paths, then the
  Playwright-managed browser (`npx playwright install chromium`).

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
the conversion runs with no model call: the same HTML, bundle and browser give
the same package bytes. It does not prove visual
fidelity, Microsoft PowerPoint behavior, or that the design survived: the
independent rendered review still owns that verdict. Known losses: no native
PPTX table (a measured HTML table becomes shapes and text), vector effects the
exporter cannot express are rasterized, and an SVG image is kept as a PNG with
its original SVG alongside. Fonts are declared, never embedded here; embedding
still uses `office:design`'s `font_embed.py` on a separate candidate.
