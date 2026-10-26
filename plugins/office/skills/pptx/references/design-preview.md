# Design preview before construction

Render a static HTML wireframe of the presentation plan so the user chooses the
visual direction and the slide sequence before any image generation or native
construction. The preview is a review artifact: it is not a PowerPoint
deliverable, it is not a rendered deck, and it never replaces native construction
or the independent rendered review.

## When to prepare it

1. More than a few slides, a reusable template, or a substantial redesign.
2. Genuine direction uncertainty, or a user who asks to see options before the deck.
3. Before any harness image-generation call, so a direction choice is not paid for
   twice.

A fully autonomous request, or one that already fixed direction and outline,
skips the gate and records the inferred choices instead.

## Plan contract

Write one JSON file in the presentation workspace:

```json
{
  "deck_title": "Quarterly operating review",
  "deck_meta": "2026-10-23 | board",
  "direction": {"library": "A"},
  "slides": [
    {"pattern": "cover", "title": "Operating review", "subtitle": "Q3 results", "meta": "Board | 2026-10-23"},
    {"pattern": "executive summary", "kicker": "Summary", "headline": "One decision per slide",
     "content": {"cards": ["Growth", "Margin", "Risk"]}, "source_note": "Source: finance pack"}
  ]
}
```

- `direction`: `library` names a direction from `office:design`'s
  `references/directions.md` (`A` to `T`); `palette` carries the chosen
  palette's `background`, `ink`, `surface` and `accent` as `#RRGGBB` values;
  `name` labels the palette (its variant or the brand).
- `slides[]`: `pattern` must match a pattern name from `layout-patterns.md`
  (case-insensitive). `title`, `kicker`, `headline`, `source_note` and `content`
  are optional, except that any non-cover, non-divider pattern needs a `headline`
  unless the slide carries `"mode": "showcase"`, where the visual may stand alone.
- `content` lists are used for density checks; give them the real planned counts
  so the preview can flag a slide that exceeds its pattern's capacity.
- One direction per deck; one pattern per slide. Vary the pattern across slides.

Always put the chosen palette's actual colors in `direction.palette`: its
background, ink, surface and accent. Set `direction.name` to the palette's
name. Keep `library` for the composition direction. The explicit palette
overrides the direction's default seeds, so the preview and both format design
reports use the same colours.
This wireframe helper does not preview the selected fonts; verify them in the
saved native candidate. Do not infer that a palette change also updated fonts.

## Render and present

Invoke `scripts/design_preview.py` from this skill with the host's Python
executable, for example:

```text
<python> <skill root>/scripts/design_preview.py --plan plan.json --out preview.html
<python> <skill root>/scripts/design_preview.py --plan plan.json --view
```

where `<skill root>` is this skill's installed directory. The method body that
loaded this reference carries the host-resolved command.

The script reads the local library, so palettes and pattern capacity stay in one
place. It writes one HTML page with a 16:9 frame per slide, the planned pattern
wireframe, the real headline and a slide-sequence table. Open it with the host's
normal browser or file-opening interface and keep its own scope line visible:
`preview only`.

`--view` prints a text summary with the per-pattern capacity ratio; a run without
`--out` performs the same validation without writing a file. `--direction L`
overrides the plan's direction label for that run, so several candidate
directions can be previewed from one plan without editing it. Exit codes: `0`
written or checked, `1` plan problems (nothing written), `2` invocation or path
error.

The script refuses the whole run on a plan problem rather than writing a partial
preview. Reported problems are plan problems, not design verdicts: fix the plan
and rerun.

## What the preview does and does not prove

- It proves the palette, the slide order, the pattern choice and the density fit
  were agreed before construction.
- It does not prove rendering, fonts, native object behavior, or fidelity in
  Microsoft PowerPoint. Those require the saved candidate and the rendered review
  under `pptx-compatibility.md`.
- A style proof is a different artifact: one representative slide generated
  through the harness image tool and reconstructed, with the user's explicit
  budget decision and chosen number of candidate directions. Record the prompt,
  the direction and the number of generations in the completion evidence.
