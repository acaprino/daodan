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

# Visual directions

Sixteen coherent art directions for the fixed 16:9 slide canvas. Choose one for
the whole deck with the context column, then apply the common geometry and type
scale in `design-library.md`. Palettes are given as
`background / ink / surface / accent`, with an optional secondary or status set.
Every direction assumes the safe cross-platform PowerPoint fonts named in its row;
substitute only with a verified installed font and record it.

## Context routing

| Context | Direction |
|---|---|
| Board, strategy, consulting proposal | A Executive Boardroom |
| Research briefing, policy, market narrative | B Editorial Report |
| Product launch, investor pitch, keynote | C Product Pitch |
| Architecture, engineering, system review | D Technical Atlas |
| Quarterly results, budget, operational metrics | E Financial & KPI Ledger |
| Design review, executive overview, clean brief | F Swiss Grid |
| Training, SOP, onboarding, action plan | G Workshop Playbook |
| Operating review, dark stage, mid-size room | I Midnight Studio |
| Creative agency proposal, brand story | J Editorial Magazine |
| Roadmap, culture or change programme | K Warm Terracotta |
| Photo or illustration led deck, showcase | L Gallery Minimal |
| Energy, environment, sustainability | M Sustainable Forest |
| Conference talk, workshop with dense examples | N Tech Neutral |
| Training or education, explainer deck | O Vivid Classroom |
| Public-sector report, compliance, audit | P Compliance Formal |
| Event announcement, internal campaign | Q Pop Announcement |
| Supplied brand guidelines or reference deck | H Brand-Led Custom |

## Directions

| Direction | Best for | Palette (bg / ink / surface / accent) | Typography (heading / body) | Layout rhythm |
|---|---|---|---|---|
| **A Executive Boardroom** | Strategy, board updates, consulting proposals | `#F8FAFC` / `#0F172A` / `#FFFFFF` / `#1D4ED8` (secondary `#0EA5E9`) | Aptos Display or Calibri Bold / Aptos or Calibri | Action title top, 2 to 3 structured evidence columns, bottom source line |
| **B Editorial Report** | Research briefings, policy, market narratives | `#FAF7F2` / `#1C1917` / `#F3EDE2` / `#B45309` (secondary `#0F766E`) | Georgia or Cambria Bold / Calibri or Segoe UI | Generous margins, asymmetric 1/3 lead column plus 2/3 evidence area |
| **C Product Pitch** | Launches, investor decks, keynote storytelling | `#0B1120` / `#F8FAFC` / `#1E293B` / `#38BDF8` (secondary `#A855F7`) | Segoe UI Semibold or Arial Bold / Segoe UI or Arial | One focal claim or visual per slide, high contrast, minimal body copy |
| **D Technical Atlas** | Architecture, engineering reviews, system flows | `#F1F5F9` / `#0F172A` / `#FFFFFF` / `#0284C7` (status `#16A34A`, `#D97706`, `#DC2626`) | Segoe UI Bold / Segoe UI or Consolas for identifiers | Modular cards, aligned native connectors, explicit legend and labels |
| **E Financial & KPI Ledger** | Quarterly results, budgets, operational metrics | `#FFFFFF` / `#111827` / `#F3F4F6` / `#047857` (variance `#B91C1C`) | Calibri Bold or Arial Bold / Calibri or Arial | Right-aligned numbers, muted gridlines, one accent colour for key variance |
| **F Swiss Grid** | Design reviews, executive overviews, clean briefs | `#FFFFFF` / `#09090B` / `#F4F4F5` / `#E11D48` | Arial Bold or Trebuchet MS / Arial | Strict 12-column grid, at least 30% open background, strong size contrast |
| **G Workshop Playbook** | Training, SOPs, onboarding, action plans | `#FFFBEB` / `#1F2937` / `#FFFFFF` / `#D97706` (secondary `#2563EB`) | Trebuchet MS Bold or Segoe UI Bold / Segoe UI | Numbered step badges, clear owner and action callouts, high scannability |
| **H Brand-Led Custom** | Requests supplying brand guidelines, logos or a reference deck | Extracted from brand assets with verified `4.5:1` text contrast | Brand font if installed, otherwise the closest cross-platform PowerPoint font | Preserves the supplied template's master margins, header band and tone |
| **I Midnight Studio** | Operating reviews, late-stage decks shown on a dark stage | `#0F172A` / `#E2E8F0` / `#1E293B` / `#FBBF24` (secondary `#38BDF8`) | Segoe UI Semibold or Calibri Bold / Segoe UI or Calibri | Dark stage, one bright accent, generous leading, few words per slide |
| **J Editorial Magazine** | Creative agency proposals, brand stories, thought leadership | `#FFFFFF` / `#18181B` / `#FAFAF9` / `#DB2777` (secondary `#0F172A`) | Georgia or Cambria Bold / Calibri or Segoe UI | Full-bleed image or pull quote pages alternating with structured text pages |
| **K Warm Terracotta** | Roadmaps, culture and change programmes | `#FDF6EE` / `#292524` / `#FFFFFF` / `#C2410C` (secondary `#0F766E`) | Cambria Bold or Trebuchet MS Bold / Calibri or Segoe UI | Warm two-tone bands, timeline spine, human-scale photography |
| **L Gallery Minimal** | Photo and illustration led decks, showcases | `#F5F5F4` / `#1C1917` / `#FFFFFF` / `#78716C` (accent `#0F766E`) | Arial Bold or Segoe UI Semibold / Arial or Segoe UI | Very large single image or object, thin rules, captions at the edge |
| **M Sustainable Forest** | Energy, environment, sustainability, CSR | `#F0FDF4` / `#14532D` / `#FFFFFF` / `#15803D` (secondary `#A16207`) | Segoe UI Bold or Calibri Bold / Segoe UI or Calibri | Organic shapes used sparingly, chart-led evidence, natural photography |
| **N Tech Neutral** | Conference talks, workshops with dense examples | `#FAFAFA` / `#171717` / `#FFFFFF` / `#2563EB` (state `#0891B2`) | Segoe UI Semibold or Arial Bold / Segoe UI or Arial | Monospace for code and identifiers, tight grids, callout chips |
| **O Vivid Classroom** | Training, education, explainer decks | `#EFF6FF` / `#1E293B` / `#FFFFFF` / `#2563EB` (secondary `#EA580C`, `#16A34A`) | Trebuchet MS Bold or Segoe UI Bold / Segoe UI or Calibri | Bright section dividers, one idea per slide, friendly diagrams |
| **P Compliance Formal** | Public-sector reports, audits, legal and compliance | `#FFFFFF` / `#111827` / `#F9FAFB` / `#1F2937` (accent `#0E7490`) | Arial Bold or Times New Roman Bold / Arial or Times New Roman | Numbered clauses, margin notes, footnote furniture, restrained emphasis |

## Direction pitfalls to avoid

- Do not average two directions: pick one and keep the accents consistent.
- Do not use colour alone to carry meaning; pair it with a label, icon or shape.
- Do not introduce a font that the construction engine or the target renderer
  lacks; verify availability and record substitution.
- Do not carry a web motion or hover language into slides; the deck is static
  unless animation is explicitly requested and supported.
- Do not let the palette fight user brand assets; brand wins.
