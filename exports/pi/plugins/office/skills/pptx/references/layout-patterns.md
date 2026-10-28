<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi has no network tool: network fetch and network search run as shell
commands, and a user question is asked in the reply while the run waits for the
answer.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

# Layout patterns

Eighteen slide patterns for the fixed 16:9 canvas. Choose the pattern by the
slide's communication job, and record the selected pattern and variation axis in
the design report so the deck can be verified against its plan. Geometry, type
scale and density caps appear below; editability and coordinate
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
from looking mechanical, and its specific requirement. Where a region sketch is
given, its brackets show regions in reading order, not raster images or
finished geometry; map real content labels onto them.

1. **Cover** — composition: title block anchored to the left third with one
   accent band or image occupying the right; slots: `deck title`, `subtitle`,
   `audience/date meta`. Variation: image band, geometric band or full-bleed
   image. Requirement: no body copy; the cover states who, what and when.
   Sketch: `[ title + subtitle ] [ image/accent ]; [ author/date ] [ logo ]`.
2. **Agenda** — composition: 3 to 6 numbered rows, one line each, optional live
   page references; slots: `sections`. Variation: numbered list, timeline strip
   or two-column split. Requirement: mirrors the deck's actual section order.
3. **Section divider** — composition: kicker plus one large section title, mostly
   empty background, optional progress marker; slots: `section number`,
   `section title`. Variation: full-bleed colour, image half or outline type.
   Sketch: `[ open space ]; [ section title ]; [ progress marker ]`.
4. **Executive summary** — composition: action headline plus 3 equal cards, each
   with a bold lead and 2 to 3 lines; slots: `card title`, `card body`, `takeaway`.
   Variation: 2, 3 or 4 cards; equal or weighted widths. Requirement: the
   headline carries the decision, not the topic.
   Sketch: `[ action headline ]; [ lead + detail ] [ lead + detail ] [ lead + detail ]`.
5. **Key metric spotlight** — composition: 2 to 4 large stat callouts with a
   summary takeaway; slots: `value`, `unit`, `delta`, `context line`. Variation:
   big numbers only, numbers plus sparkline, or numbers in cards.
   Requirement: every value cites its period and source.
   Sketch: `[ headline ]; [ primary value + unit/context ]; [ supporting values ]; [ source/period ]`.
6. **Chart and insight** — composition: native chart left at 60 to 65% width,
   insight card right; slots: `chart title`, `series`, `axis labels`,
   `insight`, `decision impact`. Variation: single chart, small multiples, or
   chart plus table. Requirement: chart data stays editable and traces to the
   authoritative source; no decorative 3D or truncated axes.
7. **Comparison matrix** — composition: 2 to 3 option columns against explicit
   criteria rows, recommendation highlighted; slots: `options`, `criteria`,
   `scores`, `recommendation`. Variation: matrix, side-by-side columns, or
   scorecard. Requirement: criteria are named and symmetric across options.
   Sketch: `[ common criterion ]; [ option A ] [ option B ]; [ explicit conclusion ]`.
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
    Sketch: `[ headline ]; [ milestone ] -> [ milestone ] -> [ milestone ]; [ dates/owners ]`.
11. **Process flow** — composition: 3 to 5 connected stages with step numbers and
    short labels; slots: `stages`, `deliverables`, `handoffs`. Variation:
    horizontal chain, loop back, or vertical funnel. Requirement: connectors are
    native shapes; do not exceed 7 nodes.
    Sketch: `[ headline ]; [ stage ] -> [ stage ] -> [ stage ]; [ handoff labels ]`.
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
    Sketch: `[ image ] [ headline + explanation ]; [ source ]`.
15. **Quote and testimonial** — composition: large pull quote, attribution and
    one supporting line; slots: `quote`, `attribution`, `supporting fact`.
    Variation: centred quote, quote beside portrait, or quote over image.
    Requirement: quotes are real and attributed; never invent one.
    Sketch: `[ exact quotation + attribution ] [ separate portrait ]; [ source ]`.
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
- Use native text, shapes, connectors, charts or tables for editable meaning;
  photographs, textures and illustrations may be distinct image objects. A
  native labeled shape replaces unsupported SmartArt when that preserves the
  requested editability.

## From pattern to slide specification

For each slide the designer's report records the stable slide ID, communication
job, headline, selected pattern and variation, and a small region sketch with
real content labels, reading order and the reason for the arrangement. Existing
variants are enough; do not generate competing designs for every slide. Every
region then becomes a slide-object entry under the single specification in
`pptx-compatibility.md`; this catalog adds no second schema. For a reusable
template, supply representative editable cover, content, evidence and closing
layouts plus replacement instructions; it is a design specification until the
producer builds the exemplar on the base `.potx` from `office:design`'s
`template_kit.py`, whose report names which layout serves which pattern.

## Provenance

The region sketches of patterns 1, 3, 4, 5, 7, 10, 11, 14 and 15 and the
sketch-to-specification handoff are adapted from
[PPT Visual](https://github.com/claude-office-skills/skills/blob/9c4c7d5cd2813a8936bf2c9fdb174ea883b85a11/ppt-visual/SKILL.md)
(claude-office-skills/skills, revision `9c4c7d5cd2813a8936bf2c9fdb174ea883b85a11`,
MIT; full license in `LICENSE-ppt-visual-MIT.txt`). The upstream's separate
colour and font catalogs, image-library sourcing and foreign tools are not
adopted: palette and pairing come from `office:design`. This is a pinned adapted
snapshot with manual review on request.


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

## Native composition and handoff

Consume the content projection and assigned proposal or selected `DESIGN.md`
under `office:design`'s `references/art-direction.md` mode contract. A provisional pattern
from content is a suggestion; the presentation designer finalizes one pattern
per slide, records a reason for a change and preserves claims, sequence and
transformation permissions. Return editorial changes to the content owner.
Vary composition to serve the actual content; adjacent repeated patterns need
a content reason. Adapt catalog recipes to the brief and supported canvas.
For each slide return the native slide-object specification from
`pptx-compatibility.md`, with source associations and the shared record revisions.
Map colors, fonts and engine tokens to that assigned design. Never substitute a
direction's default seeds or claim unsupported effects.
