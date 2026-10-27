# Content planning

Project `office:content`'s shared ledger and logical sequence into the existing
PPTX plan. Read `structure.md` for argument modes and headline conventions;
`layout-patterns.md` supplies native capacity/geometry. Content may propose a
pattern; the presentation designer finalizes composition with a reason for any
change. Neither content planning nor this projection chooses colors or fonts.

## Which plan the operation needs

| Operation | Plan | Decisions asked | Decisions inherited from the deck |
|---|---|---|---|
| Create | Full | All of the table below that the request leaves open | None |
| Derive | Full | Only those the new file changes: purpose, audience, length, delivery | The rest, from the carried-over content and structure |
| Expand | Delta | What to add, from which sources, how many slides | Purpose, audience, scope beyond the addition, delivery, density, argument mode, sequence |
| Revise | Delta | What changes; the target length when shortening; cuts to approve | Everything the revision does not change |
| Restyle, edit, review or export | None | None for content | All content |

An inherited decision is read from the deck (its headlines show the argument mode
and density, its sections the scope) and recorded with its source in CONTENT.md,
never asked.

## Planning decisions

`office:intake` asks the open ones in its single round, together with the
presentation questions, inferring every answer the request and sources already settle:

| Decision | Why it matters | Default when unstated |
|---|---|---|
| Purpose and goal | What the audience should understand, decide or do afterwards; selects the argument mode | Inferred from the request; stated back |
| Audience | Prior knowledge, seniority, language; sets vocabulary and how much evidence each claim needs | Inferred from the request; stated back |
| Scope | What is in and out: topics, period, units, markets | Everything the sources support that serves the goal |
| Delivery | Presented live, read alone (sent or printed), or both; sets headline style and text density | Presented live |
| Length | A total slide count, a number of slides to add to an existing deck, or a speaking time | Proposed from the budget below and stated back |
| Density | Light, standard or dense (below) | Light for live, dense for read alone, standard for both |

When the user gives no length, propose one number with its reasoning ("14 slides:
a 20-minute talk at about 1.5 minutes per content slide") rather than asking an
open question.

## Slide budget

- **From speaking time**: one content slide per 1 to 2 minutes, plus cover,
  agenda when there are 4 or more sections, one divider per section when there
  are 3 or more, and a closing slide.
- **From a total**: subtract the structural slides first; the rest is the content
  budget.
- **Adding to an existing deck**: the new total is the current count plus the
  slides to add, unless the user also asks to cut or merge.
- When the content does not fit the budget at the chosen density, report the
  overflow with two concrete options (raise the budget, or the claims to move to
  an appendix or drop). Never shrink text or exceed the density caps to fit.

## Density levels

| Level | Use | Per content slide |
|---|---|---|
| Light | Keynote, pitch, live talk | One claim; at most 3 short bullets or one visual, chart or metric group; speaker notes carry the detail |
| Standard | Most business decks presented with discussion | The caps of `layout-patterns.md`: at most 4 cards or columns, 5 bullets or 6 lines per text box |
| Dense | Decks read without a presenter, pre-reads, briefings | The same caps, filled; full source notes, tables up to their pattern's row range, an appendix for the remainder |

Density never lowers the type floor of `layout-patterns.md`; a dense slide that
needs smaller text is two slides.

## Shared editorial input

Load `office:content` and use its single ledger in CONTENT.md, with source
locators, core/supporting/optional claims, conditions, conflicts, units and
block-specific permissions. Read every assigned source; Quotes, figures and
names come only from sources. Missing evidence is a gap. When sources conflict,
retain both; dates alone do not settle authority. Do not create a second PPTX
ledger or infer permission to rewrite locked text from the overall operation.

## Build the storyline

1. Write the deck's one-sentence answer or promise for the goal.
2. Order the core claims by the argument mode's sequence in `structure.md`
   (pyramid: answer, arguments, evidence; narrative: situation, complication,
   resolution, ask; instructional: goal, steps, check; showcase: hero and detail;
   briefing: the fixed sections).
3. Group claims into sections; add agenda and dividers by the budget rules.
4. Give every slide one communication job and one claim, then write its headline
   in the mode's style: an action sentence for pyramid and narrative, a step
   label for instructional, a short label for showcase, a topic plus status for
   briefing.
5. Route each slide to the pattern whose job matches in `layout-patterns.md`.
   Pick the pattern by the shape of its evidence: a trend is a chart, a ranking a
   table or chart, a sequence a timeline or process, a choice a comparison, a
   single number a metric spotlight. Offer a pattern suited to the evidence; the designer finalizes it under
   `layout-patterns.md`.
6. Check each slide's planned items against its pattern capacity and the density
   level; split or move to the appendix rather than overfill.
7. Map every core claim to a slide. A core claim with no slide is a defect of the
   plan; an optional claim left out is listed as left out.

## Delta plan for an expansion or revision

Inventory the deck with `pptx_inspect.py inspect` and read its slides, notes and
charts before planning. Keep its argument mode, density, sections and patterns
unless the request changes the purpose. Update the shared ledger for the new or changed material; preserve existing
claim/unit IDs and record existing slides by their current claims.
Do not re-plan, reword or re-pattern a slide the request does not touch. Classify
every existing slide and every new claim:

| Status | Meaning |
|---|---|
| `kept` | Existing slide unchanged |
| `updated` | Existing slide whose content changes (new figures, corrected claim) |
| `moved` | Existing slide in a new position |
| `new` | Slide added for new content |
| `merged` | Existing slides combined; list their source slide numbers |
| `cut` | Existing slide removed; only with the user's approval, recorded as an approved cut |

Place new content where the storyline needs it, not at the end by default, and
in the pattern and density the neighbouring slides already use. The budget for an
expansion is the number of slides to add; for a shortening, the target total. New
content that contradicts an existing slide makes that slide `updated`, never a
second slide with the opposite claim. Every existing slide's content reaches the
result except approved cuts. Run `pptx_inspect.py coverage` after construction
for literal survival of unchanged/locked blocks; independently review authorized
free transformations against their sources and recorded destination mappings.

## Deliver and finalize the plan

Return the shared CONTENT working record and the existing plan JSON under
`design-preview.md`: stable slide `id`, `job`, `claims`, source notes and delta
`status` when relevant, plus `content_revision`. CONTENT's PPTX projection holds
slide-to-unit placements and the plan's `canonical-json-v1` binding; it is not a
second slide schema. Record slide budget/reasoning, omissions and open decisions
in the existing brief/content artifact rather than duplicating the ledger.

For a new look, first deliver complete editorial working data without inventing
the plan's display `direction`. After DESIGN selection the coordinator fills
that field from accepted visual values, recomputes the canonical binding and
writes final CONTENT.md. This is derived-binding finalization, not another
claim schema or content revision. Editorial changes return to the content owner.
Inherited designs can bind directly to their accepted visual values. Native
proposal proof uses candidate-specific working copies under design's
`references/art-direction.md`; it never freezes final CONTENT or fabricates selection.

Explicitly load the final record and run `office_records.py validate CONTENT.md
--pptx-plan plan.json`; then run `design_preview.py --plan plan.json` for native
pattern/capacity validation before final construction. The user may confirm sequence,
count and proposed patterns with the plan preview under `design-preview.md`;
authorized autonomy requires no new approval. Keep this separate from the full
visual-system comparison. A changed claim updates the shared ledger first.
