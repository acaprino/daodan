# Visual directions

Twenty visual-direction resources for ad hoc Word and PowerPoint proposals.
Use their principles, rhythm and font suggestions when they fit the actual brief;
no catalog letter or pairing is compulsory. Combine compatible principles into
one coherent selected `DESIGN.md`, then keep that identity across the work.
Format designers choose composition and geometry. A supplied brand or template
wins; `H` is an available catalog label, not a required relabeling of that source.

The palette column holds **default seeds**, not selected or certified project
colors. Use them only when appropriate to the brief and user color source.
`palette.py` extracts or generates candidates; inspect and pass its actual
contrast/distinctness checks before selection. The columns are
`background / ink / surface / accent`, then muted text and data colors.
The pairing number points to `font-pairings.md` as a resource for faces, weights,
fetch specs and Office fallbacks. Verify actual fonts and apply the selected
record; never replace its values with catalog seeds during layout or production.

## Derive the palette before using a seed

A seed copied into a hundred decks makes a hundred decks look alike, and a
colour nobody can explain is a colour drawn from habit. Before a proposal keeps a
seed, run the three steps and write the result into the proposal payload:

1. **Sample.** Take candidate colours from what the work already contains, in
   this order: supplied brand assets (logo, guidelines, template), the real
   images and products that will appear, then the subject's own colour memory
   (a vineyard, a hospital, a port authority each carry one). Inventing a hue
   with no source is the step to avoid.
2. **Converge.** Reduce to two or three chromatic colours plus one neutral
   ladder written as lightness steps (for example L 0.15 / 0.35 / 0.65 / 0.92
   / 0.98 in OKLCH). Keep chromatic colours apart by at least 60° of hue or 0.3
   of lightness, then run `palette.py` for the contrast and distinctness checks.
3. **Justify.** One sentence per chromatic colour saying where it comes from and
   what was changed ("ochre from the logo, chroma lowered to 0.08 for an ink
   feel"). A colour that cannot be justified in one sentence is a seed, and a
   seed is replaced.

Lower chroma reads as print, higher as screen. Use these OKLCH chroma bands:

| Use | Chroma | Reads as |
|---|---|---|
| Page or slide background | 0.01 to 0.04 | Paper, restful |
| Brand or accent colour | 0.08 to 0.15 | Ink: visible without glare |
| Small emphasis (key figure, callout rule) | 0.15 to 0.22 | Lively, small areas only |
| Above 0.25 over a full surface | Avoid | Fluorescent; only for a deliberately screen-native brand |

The same hue sits in different contexts at different chroma and lightness: a
muted, slightly orange red belongs to an institution, a saturated red to a
consumer campaign; a greyed indigo to craft, `#0066FF` to software. Ask which
context the subject has before keeping the first blue that comes to mind.

## Temperature and spread

Every direction has a temperature. Models drift towards the quiet end (pale
ground, generous white space, one restrained accent), so a proposal set must
not sit entirely there.

| Temperature | Directions |
|---|---|
| Quiet | A, B, E, F, L, P |
| Neutral | D, G, J, K, M, N, Q, S |
| Bold | C, I, O, R, T |
| Set by the brand | H |

When two or three proposals are shown, they differ in skeleton (column
structure, where the focal element sits, the ratio between display and body
sizes), not only in colour or weight, and at most two share a temperature. A
recolour of one arrangement is one proposal, not two. A direction used on the
previous delivery for the same client is not reused on the next one without a
reason recorded in the proposal.

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
- Do not reach for the default dark look: a uniform navy ground near `#0D1117`
  with cyan or violet glows. Dark stages `I` and `R` carry one bright accent and
  no glow; a dark direction needs that same authorial reason.
- Do not use a purple-to-blue gradient as the universal background, emoji in
  place of icons, or a rounded card with a coloured left border as the default
  container, unless the brand itself uses them.

## Provenance

Directions `Q` to `T` carry the palettes of the Desert Rose, Midnight Galaxy,
Golden Hour and Sunset Boulevard presets of
[anthropics/skills](https://github.com/anthropics/skills) Theme Factory
(Apache-2.0, Copyright 2026 Anthropic, PBC.), rebuilt with Office text roles and
contrast-checked ink, surface and muted colours; see `theme-factory-upstream.md`
and `LICENSE-theme-factory-APACHE-2.0.txt`. The other preset palettes were
already covered in character by directions `A` to `P`.

The palette derivation, the temperature spread and the three default-look
pitfalls above are original Office guidance adopting ideas from
[alchaincyf/huashu-design](https://github.com/alchaincyf/huashu-design) (MIT),
read at commit `4fc7bfdbd5ec3fa2d43ce7a6433de60976a5e4b1`: its sample, converge
and justify colour protocol, its temperature-tagged style library and its
default aesthetic bans. No upstream text, style entry, palette or script is
copied; its HTML production, animation and web modules are out of scope.
