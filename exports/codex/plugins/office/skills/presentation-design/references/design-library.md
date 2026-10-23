<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

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

# Presentation design library

Use this slide-native reference together with `pptx-compatibility.md` to choose a
visual direction, typographic scale and page layouts that fit the user's request,
audience and content. Adapt every choice to user-supplied brand assets or an
existing template when provided.

## Choose one visual direction from context

Pick one coherent direction for the whole deck based on audience, decision and
delivery setting. Do not mix directions across slides.

| Direction | Best for | Palette (bg / ink / surface / accent) | Typography (heading / body) | Layout rhythm |
|---|---|---|---|---|
| **Executive Boardroom** | Strategy, board updates, consulting proposals | `#F8FAFC` / `#0F172A` / `#FFFFFF` / `#1D4ED8` (secondary `#0EA5E9`) | Aptos Display or Calibri Bold / Aptos or Calibri | Action title top, 2 to 3 structured evidence columns, bottom source line |
| **Editorial Report** | Research briefings, policy, market narratives | `#FAF7F2` / `#1C1917` / `#F3EDE2` / `#B45309` (secondary `#0F766E`) | Georgia or Cambria Bold / Calibri or Segoe UI | Generous margins, asymmetric 1/3 lead column + 2/3 evidence area |
| **Product Pitch** | Launches, investor decks, keynote storytelling | `#0B1120` / `#F8FAFC` / `#1E293B` / `#38BDF8` (secondary `#A855F7`) | Segoe UI Semibold or Arial Bold / Segoe UI or Arial | One focal claim or visual per slide, high contrast, minimal body copy |
| **Technical Atlas** | Architecture, engineering reviews, system flows | `#F1F5F9` / `#0F172A` / `#FFFFFF` / `#0284C7` (status `#16A34A`, `#D97706`, `#DC2626`) | Segoe UI Bold / Segoe UI or Consolas for identifiers | Modular cards, aligned native connectors, explicit legend and labels |
| **Financial & KPI Ledger** | Quarterly results, budgets, operational metrics | `#FFFFFF` / `#111827` / `#F3F4F6` / `#047857` (variance `#B91C1C`) | Calibri Bold or Arial Bold / Calibri or Arial | Right-aligned numbers, muted gridlines, one accent colour for key variance |
| **Swiss Grid** | Design reviews, executive overviews, clean briefs | `#FFFFFF` / `#09090B` / `#F4F4F5` / `#E11D48` | Arial Bold or Trebuchet MS / Arial | Strict 12-column grid, at least 30% open background, strong size contrast |
| **Workshop Playbook** | Training, SOPs, onboarding, action plans | `#FFFBEB` / `#1F2937` / `#FFFFFF` / `#D97706` (secondary `#2563EB`) | Trebuchet MS Bold or Segoe UI Bold / Segoe UI | Numbered step badges, clear owner/action callout boxes, high scannability |
| **Brand-Led Custom** | Requests supplying brand guidelines, logos or a reference deck | Extracted from brand assets with verified 4.5:1 text contrast | Brand font if installed, otherwise closest cross-platform PowerPoint font | Preserves the supplied template's master margins, header band and tone |

## 16:9 canvas geometry and typography scale

Design for the fixed `16:9` widescreen canvas (`13.333 in x 7.5 in`, `1920 x 1080 px`)
unless the brief or source deck specifies another ratio:

1. **Margins and spacing**: keep at least `0.6 in` (`96 px`) left/right margin and
   `0.5 in` (`54 px`) top/bottom margin. Leave at least `0.25 in` (`36 px`) gap
   between cards, columns and chart containers.Keep at least 25% of each slide as
   open background so content breathes.
2. **Action headline on every content slide**: state the takeaway in one complete
   line or two short lines (`26 to 34 pt` bold), never a vague topic label alone.
   Place a short section kicker (`11 to 13 pt` uppercase or accent bold) above the
   headline when helpful.
3. **Readable body and data scale**:
   - Cover title: `40 to 52 pt` bold; subtitle/context: `18 to 22 pt`.
   - Card titles and table headers: `16 to 20 pt` bold.
   - Body copy and table cells: `14 to 18 pt` regular (never below `13 pt`).
   - Chart axis labels, data labels and footnotes: `11 to 13 pt` with high contrast.
4. **Density caps**: at most 4 cards or columns per slide, at most 5 bullets or
   6 lines inside any text box, and at most 7 nodes in a process or architecture
   diagram. Split overloaded content across two slides rather than shrinking text.

## Functional slide archetypes

Match each slide's layout to its communication job and vary layouts across
consecutive slides:

- **Cover slide**: title, subtitle, audience/date metadata and one clean visual or
  geometric accent band.
- **Executive summary**: action headline plus 3 equal-width native cards, each with
  a short bold lead and 2 to 3 lines of supporting evidence.
- **KPI / metric spotlight**: 2 to 4 large stat callouts (`44 to 56 pt` bold number,
  unit label, delta badge and one-line context) paired with a summary takeaway.
- **Chart + insight**: native editable chart occupying 60% to 65% of the content
  width on the left, paired with a structured insight card on the right explaining
  the driver and decision impact.
- **Comparison / decision matrix**: 2 to 3 side-by-side columns or a native table
  comparing options across explicit criteria, with the recommended option visually
  highlighted.
- **Process / roadmap**: 3 to 5 horizontal or vertical connected stages using native
  shapes, step numbers, deliverables and timing or ownership labels.
- **Architecture / system flow**: layered or left-to-right native boxes with
  consistent dimensions, aligned connectors and a concise callout for constraints.
- **Closing / action plan**: concrete decisions needed, owners, target dates and
  immediate next steps in a clean table or 3-row action list.
