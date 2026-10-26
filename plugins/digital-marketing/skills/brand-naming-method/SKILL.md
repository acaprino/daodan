---
name: brand-naming-method
description: >
  Ideate brand names, filter against archetypes and phonotactic rules, and score survivors on domain availability, market saturation and trademark risk.
  TRIGGER WHEN: "brand name", "naming", "name my app", "name my product", "product name", "startup name", "come up with a name", "nome del brand", "naming strategico".
---

# Brand Naming Strategist

Ideate, filter, and validate brand names through a structured analytical workflow. Execute all steps inline in this conversation; do not delegate generation, filtering, domain checks, or scoring to a subagent or separate context.

## Reference router

| Need | Reference |
|---|---|
| Domain checker script flags, RDAP/whois/Patchright rules, Playwright MCP trademark register procedures (UIBM, TMview, USPTO, WIPO), phonotactic refinement, and fail-fast market saturation checks | `references/screening-and-domains.md` |
| Archetypes, Spellbrand 5 tests, phonosymbolism research, case studies, and register URLs | `references/naming-frameworks.md` |
| Final Markdown report structure and table templates | `references/report-template.md` |

## BEFORE ANYTHING ELSE: Resolve the Brief

The brief has six fields (Step 1) plus a reference country. Resolve them before any output, without greetings or blank questionnaires:

- **Branch A (user message supplies 4+ brief fields):** Extract the brief directly from the message/conversation. Do not scan the working directory (which may be an unrelated repo). Present the extracted brief for confirmation and proceed to Step 1.
- **Branch B (thin brief or user references a local project/app):** Read project files silently first (`README.md`, `CLAUDE.md`, `package.json`/`pyproject.toml`/`Cargo.toml`, landing copy, `docs/`). Present a pre-filled inferred brief for confirmation and ask only for fields that could not be inferred.
- **Branch C (user supplies candidate names to vet):** Skip Step 2 generation and Step 3c refinement. Run Steps 1b, 3, 3b, 4, 5, and 6 across all supplied names (recording removals in "Names removed"), and score every survivor in Step 7. Mark unreadable screenshot names as `unreadable`.
- **Reference country (all branches):** Needed before Step 1 to grade national trademark risk in Step 5. Take it from `--country`, the brief, or project metadata (address, currency, locale, copy language). If still unknown, ask: *"Which country is the reference market for the trademark check?"*

## Workflow

### Step 1: Brief Analysis and Sector Ban List

Confirm the brief fields:
1. Industry/sector and competitive landscape
2. Target audience
3. Core values and emotions
4. Tone (playful, serious, premium, technical, natural)
5. Target languages/markets (default: `en, it, es, fr, de, pt`, or `--languages`)
6. Constraints (length, letter preferences, sounds to avoid)
7. Reference country and assumed Nice classes (e.g. 9 and 42 for software)

Create and display a **Sector Ban List** of the 5-10 most overused prefixes, suffixes, and roots in the target sector (e.g. Fitness: `Fit, Nutri, Cal, Diet, Meal, Gym, Health, Body, Lean`; AI/Tech: `AI, Bot, Mind, Think, Brain, Smart, Logic, Synth, Cogni, Neural`; Finance: `Fin, Pay, Cash, Coin, Money, Wealth, Capital, Fund`; Travel: `Trip, Tour, Fly, Go, Wander, Roam, Trek, Voyage`).

### Step 1b: Instant Kill Pre-screening

Apply during generation:
- Never use morphemes from the Sector Ban List.
- Reject common words native to the sector. Single dictionary words are allowed only if obscure, archaic, or decontextualized from an unrelated domain (like Apple, Slack, Notion).

### Step 2: Strategic Semantic Generation (12-15 Curated Names)

Do not invent meaningless syllable combinations (no CVCV letter-mashing like "Nivo", "Rivo", "Zivo"), do not use cheap suffixes (`-ify`, `-ly`, `-io`), and do not staple two obvious words together. Generate **12-15 real, obscure, or decontextualized words** across four directions, each with `[Name] (X chars): [Etymology/Origin]. Brand Story: [1-sentence strategic fit]`:

1. **Etymological Hijacking:** Obscure, modern-looking words from Ancient Greek, Latin, Sanskrit, or philosophy (`Eidos`, `Kalon`).
2. **Scientific & Mathematical Decontextualization:** Precise terms from physics, biology, mathematics, or navigation applied metaphorically (`Basal`, `Ratio`, `Zenith`).
3. **The Metaphorical Shift:** Terms from art, architecture, or nature describing the product's function with a 1-second "aha!" connection (`Tessera`, `Kroma`).
4. **The Phonetic Real-Word:** When a short phonetic shape (such as CVCV) is requested, select real words with strong meaning (`Vela`, `Soma`, `Nova`) rather than coined strings.

### Step 3: Linguistic and Cultural Filtering (Filter to 8-10)

Filter the 12-15 candidates down to the best **8-10** by verifying:
- Pronunciation ease and absence of negative/offensive meanings across all target languages (defaulting to `en, it, es, fr, de, pt`, plus Chinese and Japanese when global/Asian markets apply).
- Phonosymbolism alignment with brand tone (see `references/naming-frameworks.md`).
- No phonetic collision with profanity, disease, or major existing brands.

### Step 3b: Quick Domain Gate

Read `references/screening-and-domains.md` (Section 1) and run `${CLAUDE_PLUGIN_ROOT}/skills/domain-hunter/scripts/domain_checker.py` once across all 8-10 candidates for `.com, .app, .io, .co` (or `--tlds`).
- Keep the registration table for Steps 4 and 6a.
- List every dropped name with the exact reason (which TLDs were taken and by whom), generate replacements via Step 2, and re-filter.

### Step 3c: Phonotactic Refinement

For promising-but-rough survivors, apply the Refinement Toolkit in `references/screening-and-domains.md` (Section 2): vowel swaps, consonant softening, suffix shifts, or clipping.

### Step 4: Domain and Social Check

Reuse the Step 3b domain table (showing any unread TLD as `unverified`, never `free`) and check social handle availability via web search. Present:
`| Name | .com | .app | .io | Twitter/X | Instagram |`
For registrar price comparison and purchase guidance on finalists, point to `digital-marketing:domain-hunter`.

### Step 5: Trademark Pre-screening

Read `references/screening-and-domains.md` (Section 3) and `references/naming-frameworks.md`. Query the required trademark registers for the **Reference country**, **Europe** (EUIPO TMview / eSearch plus), and **World** (WIPO Global Brand Database + USPTO) using the `playwright` MCP browser tools in headless mode:
- Pace queries sequentially, check spaced variants, verify that each page is a genuine result list (recording WAF/error pages as `NOT SCREENED: <register>`), and run WIPO phonetic search on finalists.
- If Playwright MCP is unavailable, stop and print the recovery block in `references/screening-and-domains.md`.
- Grade each territory **A**, **B**, **C**, **D**, or **NS**. A **D in the reference country** removes the name at Step 5; a D in Europe or World lowers the Step 7 score and enters "Before you commit".

### Step 6: Market Saturation Analysis (Fail-Fast)

Follow `references/screening-and-domains.md` (Section 4) in fail-fast order:
- **6a. Domain activity gate** (`ACTIVE BUSINESS` in same sector -> discard immediately and replace; `PARKED`; `AVAILABLE`)
- **6b. App store saturation** (`SATURATED` / `MODERATE` / `CLEAR`)
- **6c. SERP saturation (Google Test)** (`DOMINATED` / `COMPETITIVE` / `OPEN`)
- **6d. Social media presence** (`TAKEN BY BRAND` / `INACTIVE/PERSONAL` / `AVAILABLE`)
- **6e. Industry-specific saturation** (`LOW` / `MEDIUM` / `HIGH` / `BLOCKED`)
- **6f. SEO Potential** (`HIGH` / `MEDIUM` / `LOW`)

Summarize in: `| Name | Domain Status | App Stores | SERP | Social | Industry | Overall Risk |`.

### Step 7: Scoring and Ranking

Score the 5 survivors from 1 to 5 (whole numbers: 5 excellent, 4 good, 3 acceptable/unverified, 2 weak, 1 poor) using these weights:

| Criterion | Weight | Description |
|---|---|---|
| Memorability | 15% | Easy to recall after one hearing (Phone Test: 70%+ recall) |
| Distinctiveness | 15% | Unique vs competitors, not generic |
| Market Saturation | 15% | Low saturation across domains, app stores, and SERP (inverted: low saturation = high score) |
| Simplicity/Pronunciation | 10% | Easy to say and spell (Spelling Test: 80%+ accuracy) |
| Relevance | 10% | Connection to brand values and product |
| SEO Potential | 10% | Organic discoverability and SERP openness |
| Domain Availability | 10% | `.com` or strong alternative TLD available |
| Trademark Risk | 5% | Reference country class (`A`=5, `B`=4, `C`=2, `D`=1), minus 1 (floor 1) if Europe or World is worse; if Reference country is `NS`, cap at `3 (not screened)` |
| Emotional Impact | 5% | Evocative power and storytelling potential |
| Cultural Adaptability | 5% | Works cleanly across all target languages |

Every score cites concrete evidence. A check that could not run at all (e.g. SEO Potential when SERP lookup was unavailable) is marked `not scored`, omitted from the weight denominator, and listed in "Before you commit".
Formula: `Overall = SUM(criterion_score * weight) / SUM(weight of scored criteria)`, rounded to one decimal. Break ties on Distinctiveness, then Market Saturation.

### Step 8: Evaluation Report

Read `references/report-template.md` and populate every section in order (1. Summary, 2. Scorecard, 3. Top 3 names, 4. Runners-up, 5. Names removed, 6. Before you commit, 7. Evidence) in the language of the brief. Every score across all 10 criteria for all 5 ranked names must include a one-sentence evidence-backed motivation.

Use the caller's owned run output directory when supplied; otherwise use the
user's selected output directory or a dedicated `.brand-naming/` directory inside
the current workspace. Write this native
Markdown report once to the user's requested report path, or
`brand-naming-report.md` in the owned output directory when no filename was given.
Keep required motivations, evidence and unknown states; do not shorten the checks
or regenerate the same content for another layout. Link to the saved report in the
conversation with the recommendation and open checks.

When the user requests HTML, or exploring the scorecard's weights would materially
help the choice, load the `report-rendering:report-renderer` skill and resolve its helper
through that skill. Render the saved Markdown with `--profile naming`, `--input`
set to that report, `--output` set to its same-stem `.html` sibling and `--root`
set to the same dedicated owned output directory. If the user selected a native
report path in the repository root or a shared directory, keep that Markdown path
and place its HTML in a dedicated `.brand-naming/` subdirectory instead; pass that
subdirectory as `--root`. The provider rebases relative evidence links to preserve
their targets. The fixed renderer supplies presentation
controls; do not author another HTML/CSS layout or new report content. Preserve the
template's sections, evidence, provisional values and original recommendation.
Weight changes are exploratory as the native template explains. Verify the helper
outcome before linking the HTML. On failure preserve Markdown and report the
optional view failure; an explicitly requested HTML deliverable remains open.
