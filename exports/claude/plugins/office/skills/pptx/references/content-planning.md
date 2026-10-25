<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
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

# Content planning

Decide what the deck says, in how many slides, in which order and with which
pattern, before any design or construction. The plan is approved by the user
through the design preview; the designer then adds geometry and the engine
builds it. The plan never decides colours, fonts or object geometry.

## Which plan the operation needs

| Operation | Plan | Decisions asked | Decisions inherited from the deck |
|---|---|---|---|
| Create | Full | All of the table below that the request leaves open | None |
| Derive | Full | Only those the new file changes: purpose, audience, length, delivery | The rest, from the carried-over content and structure |
| Expand | Delta | What to add, from which sources, how many slides | Purpose, audience, scope beyond the addition, delivery, density, argument mode, sequence |
| Revise | Delta | What changes; the target length when shortening; cuts to approve | Everything the revision does not change |
| Restyle, edit, review or export | None | None for content | All content |

An inherited decision is read from the deck (its headlines show the argument mode
and density, its sections the scope) and stated back in the content report,
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
| Standard | Most business decks presented with discussion | The caps of `design-library.md`: at most 4 cards or columns, 5 bullets or 6 lines per text box |
| Dense | Decks read without a presenter, pre-reads, briefings | The same caps, filled; full source notes, tables up to their pattern's row range, an appendix for the remainder |

Density never lowers the type floor of `design-library.md`; a dense slide that
needs smaller text is two slides.

## Digest the sources

Read every source before planning, with the inspector or engine of its format:
`office:docx` for Word, `office:xlsx` for workbooks, `office:deckcraft`'s
`pptx_inspect.py` for an existing deck, and the text of notes, web pages, PDFs
or research reports. Build one claim ledger in the content report:

| Field | Content |
|---|---|
| ID | A stable claim ID |
| Claim | The statement, in the source's meaning |
| Evidence | Figures, quotes or examples that carry it, verbatim where wording matters |
| Source | File and locator (page, slide, sheet and cell, section or URL) |
| Weight | Core, supporting or optional for the stated goal |
| Conflict | Another source that disagrees, if any |

Quotes, figures and names come only from sources. A gap the goal needs is
recorded as a gap and asked about, never filled. When sources conflict, record
both and ask which governs, unless one is clearly newer or authoritative and the
choice is stated.

## Build the storyline

1. Write the deck's one-sentence answer or promise for the goal.
2. Order the core claims by the argument mode's sequence in `design-library.md`
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
   single number a metric spotlight. Vary patterns across adjacent slides as
   `design-library.md` requires.
6. Check each slide's planned items against its pattern capacity and the density
   level; split or move to the appendix rather than overfill.
7. Map every core claim to a slide. A core claim with no slide is a defect of the
   plan; an optional claim left out is listed as left out.

## Delta plan for an expansion or revision

Inventory the deck with `pptx_inspect.py inspect` and read its slides, notes and
charts before planning. Keep its argument mode, density, sections and patterns
unless the request changes the purpose. Build the claim ledger for the new or
changed material only, and record the existing slides by their current claims.
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
result except approved cuts; `pptx_inspect.py coverage` verifies it after
construction.

## Deliver the plan

Write two artifacts in the presentation workspace:

1. **Content report**: goal, audience, scope, delivery, density, budget and its
   reasoning, the one-sentence answer, the claim ledger, the section outline,
   the claims left out, gaps and conflicts, and for an existing deck the status
   table.
2. **Plan JSON** under the contract of `design-preview.md`, one entry per slide
   in order, with these additional fields: `id` (stable slide ID), `job`,
   `claims` (claim IDs), `status` (for an existing deck) and `source_note`.

The coordinator renders the plan with `design_preview.py`. The user approves the
sequence, the count and the patterns there before design. A changed decision
re-enters this plan; a changed claim updates the ledger first.
