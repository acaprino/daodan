<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
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

# Visual directions

Twenty coherent visual directions for Word documents and PowerPoint decks. A
direction fixes composition and rhythm for slides and pages and names the font
pairing. Choose one for the whole file with the context column, record it in
the brief, and keep it; vary slide patterns and page patterns under it, never the
direction. A supplied brand or template wins over every direction: extract its
palette and fonts into direction `H` and keep the rest of these rules.

The palette is built for each file from the user's colour source by
`scripts/palette.py` (see `SKILL.md`). The palette column below is that
direction's **default seeds**, used only when the user supplies no image,
website, stylesheet, existing file or description: pass its accent as the first
seed, and its ink as the second when the direction's character depends on it.
It is given as `background / ink / surface / accent`, then the muted text colour
and the data colours; every ink, accent and muted colour holds at least `4.5:1`
on both background and surface. The pairing number points into
`font-pairings.md`, which supplies the faces, weights, fetch spec and the Office
fallback: install the pairing before construction and embed it on delivery as
`SKILL.md` describes.

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
| Supplied brand guidelines, template or reference file | H Brand-Led Custom |
| Operating review, dark stage, mid-size room | I Midnight Studio |
| Creative agency proposal, brand story | J Editorial Magazine |
| Roadmap, culture or change programme | K Warm Terracotta |
| Photo or illustration led deck, showcase | L Gallery Minimal |
| Energy, environment, sustainability | M Sustainable Forest |
| Conference talk, workshop with dense examples | N Tech Neutral |
| Training or education, explainer deck | O Vivid Classroom |
| Public-sector report, compliance, audit | P Compliance Formal |
| Fashion, beauty, interiors, boutique, wedding | Q Desert Rose |
| Entertainment, gaming, nightlife, creative agency on a dark stage | R Midnight Galaxy |
| Restaurant, hospitality, artisan, seasonal campaign | S Golden Hour |
| Event announcement, marketing, lifestyle, internal campaign | T Sunset Boulevard |

## Directions

| Direction | Best for | Palette (bg / ink / surface / accent; muted; data) | Pairing (headings / body) | Rhythm |
|---|---|---|---|---|
| **A Executive Boardroom** | Strategy, board updates, consulting proposals | `#F8FAFC` / `#0F172A` / `#FFFFFF` / `#1D4ED8`; muted `#475569`; data `#1D4ED8` `#0EA5E9` `#475569` | 1: Inter / Inter | Action title top, 2 to 3 structured evidence columns, source line at the foot; Word: single column, numbered headings, summary box first |
| **B Editorial Report** | Research briefings, policy, market narratives | `#FAF7F2` / `#1C1917` / `#F3EDE2` / `#9A4507`; muted `#57534E`; data `#9A4507` `#0F766E` `#57534E` | 2: Source Serif 4 / Source Sans 3 | Generous margins, asymmetric 1/3 lead column plus 2/3 evidence; Word: wide outer margin for notes, serif headings, pull quotes |
| **C Product Pitch** | Launches, investor decks, keynote storytelling | `#0B1120` / `#F8FAFC` / `#1E293B` / `#38BDF8`; muted `#94A3B8`; data `#38BDF8` `#A855F7` `#94A3B8` | 10: Space Grotesk / Inter | One focal claim or visual per slide, high contrast, minimal body copy; Word: light variant with `#F8FAFC` background for printed one-pagers |
| **D Technical Atlas** | Architecture, engineering reviews, system flows | `#F1F5F9` / `#0F172A` / `#FFFFFF` / `#0369A1`; muted `#475569`; data `#0369A1` `#16A34A` `#D97706` `#DC2626` | 5: IBM Plex Sans / IBM Plex Sans, Plex Mono for code | Modular cards, aligned native connectors, explicit legend; Word: numbered figures, monospace identifiers, wide tables |
| **E Financial & KPI Ledger** | Quarterly results, budgets, operational metrics | `#FFFFFF` / `#111827` / `#F3F4F6` / `#047857`; muted `#4B5563`; data `#047857` `#B91C1C` `#4B5563` | 1: Inter / Inter | Right-aligned numbers, muted gridlines, one accent for key variance; Word: tabular figures, totals rules, compact tables |
| **F Swiss Grid** | Design reviews, executive overviews, clean briefs | `#FFFFFF` / `#09090B` / `#F4F4F5` / `#BE123C`; muted `#52525B`; data `#BE123C` `#09090B` `#52525B` | 1: Inter / Inter | Strict 12-column grid, at least 30% open background, strong size contrast; Word: flush-left headings, hairline rules, no boxes |
| **G Workshop Playbook** | Training, SOPs, onboarding, action plans | `#FFFBEB` / `#1F2937` / `#FFFFFF` / `#B45309`; muted `#4B5563`; data `#B45309` `#2563EB` `#4B5563` | 8: Nunito / Nunito | Numbered step badges, owner and action callouts, high scannability; Word: step headings, checklists, callout boxes |
| **H Brand-Led Custom** | Requests supplying brand guidelines, a template or a reference file | Extracted from the brand assets, with every text colour checked at `4.5:1` | Brand fonts when installed or installable; otherwise the nearest catalog pairing, recorded as a substitution | Preserves the supplied template's masters, margins, header band and tone |
| **I Midnight Studio** | Operating reviews, late-stage decks shown on a dark stage | `#0F172A` / `#E2E8F0` / `#1E293B` / `#FBBF24`; muted `#94A3B8`; data `#FBBF24` `#38BDF8` `#94A3B8` | 1: Inter / Inter | Dark stage, one bright accent, generous leading, few words per slide; Word: not for print, use `A` for the printed companion |
| **J Editorial Magazine** | Creative agency proposals, brand stories, thought leadership | `#FFFFFF` / `#18181B` / `#FAFAF9` / `#BE185D`; muted `#52525B`; data `#BE185D` `#0F172A` `#52525B` | 3: Playfair Display / Lato | Full-bleed image or pull quote pages alternating with structured text pages; Word: display headings, drop caps, two-column features |
| **K Warm Terracotta** | Roadmaps, culture and change programmes | `#FDF6EE` / `#292524` / `#FFFFFF` / `#C2410C`; muted `#57534E`; data `#C2410C` `#0F766E` `#57534E` | 11: DM Serif Display / DM Sans | Warm two-tone bands, timeline spine, human-scale photography; Word: tinted section openers, timeline tables |
| **L Gallery Minimal** | Photo and illustration led decks, showcases | `#F5F5F4` / `#1C1917` / `#FFFFFF` / `#57534E`; muted `#57534E`; data `#57534E` `#0F766E` `#A8A29E` | 1: Inter / Inter | Very large single image or object, thin rules, captions at the edge; Word: image plates with captions, sparse text |
| **M Sustainable Forest** | Energy, environment, sustainability, CSR | `#F0FDF4` / `#14532D` / `#FFFFFF` / `#15803D`; muted `#3F6212`; data `#15803D` `#A16207` `#3F6212` | 2: Source Serif 4 / Source Sans 3 | Organic shapes used sparingly, chart-led evidence, natural photography; Word: green rules, data callouts, photo openers |
| **N Tech Neutral** | Conference talks, workshops with dense examples | `#FAFAFA` / `#171717` / `#FFFFFF` / `#2563EB`; muted `#525252`; data `#2563EB` `#0891B2` `#525252` | 5: IBM Plex Sans / IBM Plex Sans, Plex Mono for code | Monospace for code and identifiers, tight grids, callout chips; Word: code blocks on surface, narrow margins |
| **O Vivid Classroom** | Training, education, explainer decks | `#EFF6FF` / `#1E293B` / `#FFFFFF` / `#1D4ED8`; muted `#475569`; data `#1D4ED8` `#EA580C` `#16A34A` | 6: Montserrat / Open Sans | Bright section dividers, one idea per slide, friendly diagrams; Word: coloured heading bands, numbered exercises |
| **P Compliance Formal** | Public-sector reports, audits, legal and compliance | `#FFFFFF` / `#111827` / `#F9FAFB` / `#1F2937`; muted `#4B5563`; data `#0E7490` `#1F2937` `#4B5563` | 12: Noto Serif / Noto Sans | Numbered clauses, margin notes, footnote furniture, restrained emphasis; Word: decimal heading numbers, formal tables, footnotes |
| **Q Desert Rose** | Fashion, beauty, interiors, boutique businesses, weddings | `#F6EDE6` / `#5D2E46` / `#FFFFFF` / `#8C4A4A`; muted `#7A5C5C`; data `#8C4A4A` `#D4A5A5` `#B87D6D` | 7: Cormorant Garamond / Montserrat | Soft tinted surfaces, airy spacing, one refined image per slide; Word: elegant serif headings, generous white space, thin rules |
| **R Midnight Galaxy** | Entertainment, gaming, nightlife, creative agencies on a dark stage | `#2B1E3E` / `#F1ECF8` / `#3C2F55` / `#C8B6E6`; muted `#B9AFCC`; data `#C8B6E6` `#4A4E8F` `#E6E6FA` | 10: Space Grotesk / Inter | Deep purple stage, luminous accents, large display type; Word: not for print, use `J` for the printed companion |
| **S Golden Hour** | Restaurants, hospitality, artisan products, seasonal campaigns | `#FBF4E8` / `#4A403A` / `#FFFFFF` / `#8F5A12`; muted `#6B5E55`; data `#F4A900` `#C1666B` `#8F5A12` | 11: DM Serif Display / DM Sans | Warm beige surfaces, mustard and terracotta accents, photography-led; Word: warm section openers, menu-style tables |
| **T Sunset Boulevard** | Event announcements, marketing, lifestyle brands, internal campaigns | `#FFF8EF` / `#264653` / `#FFFFFF` / `#B8431F`; muted `#5C6B70`; data `#E76F51` `#F4A261` `#E9C46A` | 6: Montserrat / Open Sans | Bold accent bands, large headlines, energetic colour blocks; Word: poster-like cover, short sections, strong callouts |

## Direction pitfalls to avoid

- Do not average two directions: pick one and keep the accents consistent.
- Do not use colour alone to carry meaning; pair it with a label, icon or shape.
- Do not set text in a data colour: text uses ink, accent or muted only.
- Do not swap the direction's pairing for another without recording why; a
  pairing that failed to install falls back to its own Office fallback.
- Do not carry a web motion or hover language into slides; the deck is static
  unless animation is explicitly requested and supported.
- Do not let the palette fight user brand assets; brand wins.

## Provenance

Directions `Q` to `T` carry the palettes of the Desert Rose, Midnight Galaxy,
Golden Hour and Sunset Boulevard presets of
[anthropics/skills](https://github.com/anthropics/skills) Theme Factory
(Apache-2.0, Copyright 2026 Anthropic, PBC.), rebuilt with Office text roles and
contrast-checked ink, surface and muted colours; see `theme-factory-upstream.md`
and `LICENSE-theme-factory-APACHE-2.0.txt`. The other preset palettes were
already covered in character by directions `A` to `P`.
