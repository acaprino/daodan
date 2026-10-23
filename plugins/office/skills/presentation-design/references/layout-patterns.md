# Layout patterns

Eighteen slide patterns for the fixed 16:9 canvas. Choose the pattern by the
slide's communication job, and record the selected pattern and variation axis in
the design report so the deck can be verified against its plan. Geometry, type
scale and density caps come from `design-library.md`; editability and coordinate
rules come from `pptx-compatibility.md`.

Common slots for every content pattern: `kicker` (optional), `headline`,
`body`, `evidence`, `source note`. Other slots are named per pattern.

## Pattern catalogue

| # | Pattern | Job |
|---|---|---|
| 1 | Cover | Orient |
| 2 | Agenda | Orient |
| 3 | Section divider | Orient |
| 4 | Executive summary | Explain |
| 5 | Key metric spotlight | Show evidence |
| 6 | Chart and insight | Show evidence |
| 7 | Comparison matrix | Compare |
| 8 | Options and recommendation | Compare |
| 9 | Data table | Show evidence |
| 10 | Timeline and roadmap | Plan |
| 11 | Process flow | Explain |
| 12 | Architecture and system map | Explain |
| 13 | Risk and mitigation table | Show evidence |
| 14 | Case study | Explain |
| 15 | Quote and testimonial | Explain |
| 16 | Team and organization | Orient |
| 17 | Workshop and training plan | Plan |
| 18 | Next steps and decision request | Request a decision |

## Pattern details

Each entry names its composition, main slots, the variation axis that keeps decks
from looking mechanical, and its specific requirement.

1. **Cover** — composition: title block anchored to the left third with one
   accent band or image occupying the right; slots: `deck title`, `subtitle`,
   `audience/date meta`. Variation: image band, geometric band or full-bleed
   image. Requirement: no body copy; the cover states who, what and when.
2. **Agenda** — composition: 3 to 6 numbered rows, one line each, optional live
   page references; slots: `sections`. Variation: numbered list, timeline strip
   or two-column split. Requirement: mirrors the deck's actual section order.
3. **Section divider** — composition: kicker plus one large section title, mostly
   empty background, optional progress marker; slots: `section number`,
   `section title`. Variation: full-bleed colour, image half or outline type.
4. **Executive summary** — composition: action headline plus 3 equal cards, each
   with a bold lead and 2 to 3 lines; slots: `card title`, `card body`, `takeaway`.
   Variation: 2, 3 or 4 cards; equal or weighted widths. Requirement: the
   headline carries the decision, not the topic.
5. **Key metric spotlight** — composition: 2 to 4 large stat callouts with a
   summary takeaway; slots: `value`, `unit`, `delta`, `context line`. Variation:
   big numbers only, numbers plus sparkline, or numbers in cards.
   Requirement: every value cites its period and source.
6. **Chart and insight** — composition: native chart left at 60 to 65% width,
   insight card right; slots: `chart title`, `series`, `axis labels`,
   `insight`, `decision impact`. Variation: single chart, small multiples, or
   chart plus table. Requirement: chart data stays editable and traces to the
   authoritative source; no decorative 3D or truncated axes.
7. **Comparison matrix** — composition: 2 to 3 option columns against explicit
   criteria rows, recommendation highlighted; slots: `options`, `criteria`,
   `scores`, `recommendation`. Variation: matrix, side-by-side columns, or
   scorecard. Requirement: criteria are named and symmetric across options.
8. **Options and recommendation** — composition: 2 to 4 option cards, one marked
   recommended, with cost or effort and impact; slots: `option`, `impact`,
   `effort/cost`, `risk`. Variation: cards, quadrant, or ranked list.
   Requirement: recommendation states its trade-off in one line.
9. **Data table** — composition: native table, header row emphasized, 4 to 7 rows
   maximum, right-aligned numbers; slots: `columns`, `rows`, `totals`, `note`.
   Variation: striped, bordered or ledger style. Requirement: cells stay editable
   and totals are computed from the source data.
10. **Timeline and roadmap** — composition: horizontal spine with 3 to 6 periods,
    each carrying 1 to 3 items and an owner; slots: `periods`, `items`, `owners`
    or `milestones`. Variation: horizontal spine, swimlanes, or vertical list.
    Requirement: dates and owners are explicit; no implied precision that the
    source does not support.
11. **Process flow** — composition: 3 to 5 connected stages with step numbers and
    short labels; slots: `stages`, `deliverables`, `handoffs`. Variation:
    horizontal chain, loop back, or vertical funnel. Requirement: connectors are
    native shapes; do not exceed 7 nodes.
12. **Architecture and system map** — composition: layered or left-to-right
    boxes with aligned connectors, a legend and a constraints callout; slots:
    `components`, `interfaces`, `boundaries`, `legend`. Variation: layered stack,
    hub and spoke, or sequence. Requirement: consistent box sizes, labelled
    interfaces, and no unexplained arrows.
13. **Risk and mitigation table** — composition: 3 to 6 risks with likelihood,
    impact, mitigation and owner; slots: `risk`, `likelihood`, `impact`,
    `mitigation`, `owner`. Variation: table, heat map plus list, or cards.
    Requirement: severity uses labels as well as colour.
14. **Case study** — composition: situation, action, result blocks with one
    quantified result; slots: `context`, `action`, `result`, `proof`. Variation:
    three columns, before/after, or narrative with a pull stat. Requirement: the
    result cites its measurement basis.
15. **Quote and testimonial** — composition: large pull quote, attribution and
    one supporting line; slots: `quote`, `attribution`, `supporting fact`.
    Variation: centred quote, quote beside portrait, or quote over image.
    Requirement: quotes are real and attributed; never invent one.
16. **Team and organization** — composition: 3 to 6 people or roles with
    responsibility lines; slots: `name`, `role`, `responsibility`, `contact`.
    Variation: grid, org chart, or roster rows. Requirement: only include people
    and contacts supplied by the user.
17. **Workshop and training plan** — composition: numbered steps with timing and
    owner, resources listed separately; slots: `steps`, `timing`, `owner`,
    `materials`. Variation: agenda table, station cards, or step flow.
    Requirement: timing adds up and matches the stated session length.
18. **Next steps and decision request** — composition: decision asked, owners,
    dates and immediate actions in a clean table or 3-row list; slots:
    `decision`, `owner`, `date`, `action`. Variation: table, three-row list, or
    action cards. Requirement: one clear ask, with the decision owner named.

## Variation and reuse

- Choose a per-slide variation axis explicitly; do not switch variants to decorate.
- Reuse a pattern across the deck only when the job repeats, and vary the axis
  instead of copying the previous slide's layout verbatim.
- For a reusable template request, produce one editable exemplar deck containing
  representative patterns (cover, divider, summary, evidence, comparison, plan,
  closing) plus a short reuse note naming the direction and the pattern set.
- A pattern is a construction plan, not a picture: if a proposed composition
  cannot be built with the engine's supported native objects, redesign it within
  the pattern or report the limitation before construction.
