# Design preview before construction

Render the finalized native presentation plan as a static HTML wireframe for
count, sequence, proposed patterns and density. This is distinct from
`office:design`'s complete real-content visual-system comparison. It is neither
a native PowerPoint deliverable nor a saved render or independent review.
For a new look, `office:design`'s `references/art-direction.md` first uses
candidate-specific working plans/display bindings for native proposal proof.
After visual selection, finalize the display/CONTENT plan binding for final
native-plan validation. Content prepares complete editorial working data first
without inventing colors to satisfy this preview.

## When to prepare it

1. More than a few slides, a reusable template, or a substantial redesign.
2. A user who needs to inspect proposed sequence or patterns before the deck.
3. For candidate-specific proposal planning or final construction, using the
   corresponding working or selected binding.

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

- `direction`: optional `library` names a direction from `office:design`'s
  `references/directions.md` (`A` to `T`); ad hoc themes need no letter. `palette` carries the selected
  palette's `background`, `ink`, `surface` and `accent` as `#RRGGBB` values;
  `name` labels the palette (its variant or the brand).
- `slides[]`: `pattern` must match a pattern name from `layout-patterns.md`
  (case-insensitive). `title`, `kicker`, `headline`, `source_note` and `content`
  are optional, except that any non-cover, non-divider pattern needs a `headline`
  unless the slide carries `"mode": "showcase"`, where the visual may stand alone.
- `content` lists are used for density checks; give them the real planned counts
  so the preview can flag a slide that exceeds its pattern's capacity.
- One assigned proposal or selected visual identity per plan copy; a justified
  final pattern per slide.
  Content can propose patterns; the designer owns composition.
- A plan from `content-planning.md` also carries `content_revision` and per-slide `id`,
  `job`, `claims` (shared claim IDs) and, for an existing deck, `status`: `kept`, `updated`, `moved`, `new` or
  `merged` (cut slides are not in the plan). The sequence table shows status and
  claims; an unknown status is a plan problem.

Always put the assigned palette's actual colors in `direction.palette`: its
background, ink, surface and accent. Set `direction.name` to the palette's
name. Keep `library` only when a catalog resource is used; it does not select fonts
or final composition. The explicit palette
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

- It displays the selected palette, slide order, proposed patterns and density
  fit. The coordinator separately records actual approval or autonomous authority.
- It does not prove rendering, fonts, native object behavior, or fidelity in
  Microsoft PowerPoint. Those require the saved candidate and the rendered review
  under `pptx-compatibility.md`.
- A native proposal proof is a different artifact. Follow `office:design`'s
  art-direction and v2 record contracts for saved representative slides, exact
  candidate bindings and independent critique before selection. Include the
  opening and actual difficult-content jobs; a cover alone is insufficient.
  Generated imagery follows `image-tools.md` and the existing brief's authority.
  Record the candidate, source slides, assets, native/render tools and observed
  checks. This wireframe cannot stand in for those saved-native renders.
