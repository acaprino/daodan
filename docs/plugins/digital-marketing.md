# Digital Marketing Plugin

> Drive organic traffic and conversions. Technical SEO audits, content strategy, and marketing optimization with Playwright-powered analysis and persistent reports.

## Agents

### `seo-specialist`

Intent-first SEO strategist: establishes search intent and topical coverage before touching tags, then runs the semantic and technical audits and maps competitive gaps.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Technical SEO audits, search-intent alignment, keyword and semantic analysis, on-page optimization, structured data, competitive analysis |

**Invocation:**
```
Use the seo-specialist agent to [audit/optimize/research] [target]
```

**Expertise:**
- Search intent first: classifies the target query (informational, transactional, navigational, commercial investigation), checks the top 3-5 ranking results for the content type that wins, and flags content-intent gaps
- Semantic audit: keyword and semantic analysis, content depth, readability
- Technical audit: on-page tags, headings, URLs, links, images, structured data, crawlability, performance signals, security, mobile readiness, E-E-A-T, plus international and local SEO where applicable
- Scoring: a 0-100 health score with a letter grade, a per-category breakdown, and Error / Warning / Notice classification
- Competitive analysis: SERP landscape and features, content gaps, keyword overlap, E-E-A-T comparison
- Applies fixes only after approval, then re-audits and shows before/after scores

---

### `content-marketer`

Audit and rewrite agent for what a visitor actually reads before deciding, built around the conversion pyramid: Functional, then Clear, then Persuasive, then Frictionless. A higher level blocks the lower ones, so CTAs are never optimized on a page whose message is unclear.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Marketing materials, landing page copy, CTAs, product presentation, social media readiness, conversion optimization |

**Invocation:**
```
Use the content-marketer agent to [plan/create/optimize] [content/campaign]
```

**Expertise:**
- Context first: B2B vs B2C, traffic source (for message match), primary conversion goal
- UX and conversion audit: page layout, CTAs, social proof and E-E-A-T, product presentation, pricing pages, forms, accessibility, navigation
- Content and copy audit: headlines, body copy, tone and voice, SEO copy, microcopy, product descriptions
- Social media audit: share readiness, presence, platform strategy, content mix, social commerce
- Visual and media audit: images, product gallery, video
- Metric-driven diagnosis when data is available (bounce, time on page, add-to-cart vs checkout)
- Before/after rewrites applied in batches after approval, and A/B hypotheses in the form "If we change [Element] from [Control] to [Variant], then [Metric] will increase because [Principle]"

---

> **Moved:** prose humanization (the `text-humanizer` agent, the `/text-humanizer:humanize-text` command, and the `anti-ai-writing-patterns` knowledge base) now lives in the standalone [text-humanizer](text-humanizer.md) plugin, a hard dependency of this one. SEO flows route to `/text-humanizer:humanize-text`.

---

### `ga4-implementation-expert`

GA4 + GTM implementation expert with deep focus on EU/GDPR Consent Mode v2 compliance, custom event tracking, conversion (Key Event) configuration, remarketing audiences, and diagnostic analysis.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | GA4 / GTM deployment, Consent Mode v2 compliance, CMP integration (iubenda, Cookiebot, Orestbida CookieConsent), Key Event + Google Ads conversion import, Enhanced Conversions, remarketing audiences, "why isn't my site converting" diagnostics |

**Invocation:**
```
Use the ga4-implementation-expert agent to [implement/audit/debug] [GA4 or GTM setup]
```

**Frameworks covered:** vanilla HTML, Next.js / React, WordPress. Handles dataLayer event taxonomy design, server-side vs client-side tagging, and the full `gtag('consent', 'default' | 'update', ...)` flow with the 4-granular-signal EU pattern (`ad_storage`, `ad_user_data`, `ad_personalization`, `analytics_storage`).

---

### `llm-seo-optimize`

Answer-engine optimization (AEO) specialist for Google AI Overviews / SGE, Perplexity, ChatGPT Search, Claude with web search, and Bing Copilot. Different from traditional SEO: AEO optimizes for getting **cited inside the LLM-generated answer**, not just ranking on a SERP.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Auditing a site for AI-search discoverability, checking E-E-A-T signals, optimizing passage-level extractability, reviewing JSON-LD / Schema.org, diagnosing low citation rate in LLM answers |

**Invocation:**
```
Use the llm-seo-optimize agent to audit [url or local path] for answer-engine optimization
```

**6-phase audit:**
1. **Crawler access**: full robots.txt user-agent matrix for 13 AI bots (GPTBot, ChatGPT-User, OAI-SearchBot, PerplexityBot, Perplexity-User, Google-Extended, Googlebot, ClaudeBot, Claude-User, Claude-SearchBot, Applebot-Extended, Bytespider, CCBot) with train-vs-retrieve distinction. `anthropic-ai` and `Claude-Web` are retired tokens that identify no Anthropic crawler: they are flagged as legacy entries to clean up, since blocking or allowing them changes nothing. Blocking `Google-Extended` does not remove a page from AI Overviews; blocking `Googlebot` does
2. **E-E-A-T signals**: author bylines with credentials, publication + last-updated dates in ISO + JSON-LD, primary-source citations, first-hand experience markers, fact-check structure
3. **Passage-level extractability**: direct-answer first paragraphs, one-question-per-H2, bulleted fact lists, tables with captions, numbers with unit + date + source
4. **Structured data**: JSON-LD for Article / HowTo / FAQPage / Product / Dataset / ClaimReview / SoftwareApplication / Organization + sameAs
5. **Citation readiness**: canonical URL, section-anchor permalinks, cite-this-article block, clear licensing, downloadable data
6. **Prompt-injection hardening**: audit hidden text, invisible CSS, JSON-LD / alt-text / comment payloads that reach the LLM context

**Also covers:** `llms.txt` / `llms-full.txt` proposed standards, AI-referral analytics setup (chatgpt.com, legacy chat.openai.com, perplexity.ai, claude.ai, copilot.microsoft.com, gemini.google.com hostnames), weekly brand-mention citation-share tracking. Search Console does not break AI Overviews out (their impressions and clicks are folded into aggregate Web performance), so the AI-referrer hostnames are the measurable proxy.

---

## Skills

### `brand-naming-method`

Brand naming strategist. Generates, filters, scores, and validates brand names through a strategic semantic workflow.

| | |
|---|---|
| **Invoke** | Skill reference or `/digital-marketing:brand-naming` |
| **Trigger** | "brand name", "naming", "name my app", "name my product", "startup name" |

**Workflow:** Generates 12-15 curated candidates across 4 Strategic Directions (etymological hijacking, scientific decontextualization, metaphorical shift, phonetic real-word), then filters with 7 naming archetypes and linguistic/phonotactic rules, checks domain registration once over the requested TLDs with the RDAP domain checker, runs market saturation analysis, pre-screens trademarks in EUIPO TMview, USPTO Trademark Search and the WIPO Global Brand Database through a browser (the `playwright` plugin's MCP tools), rates SEO potential, and scores the top 5 on weighted criteria. Coined words, letter-mashing and cheap suffixes are banned at generation.

---

### `domain-hunter`

Search domains, compare registrar prices, find promo codes, and get purchase recommendations.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Trigger** | "buy a domain", "domain prices", "domain deals", "compare registrars", ".ai domain", ".com domain" |

**Source:** Ported from [ReScienceLab/opc-skills](https://github.com/ReScienceLab/opc-skills).

**Includes:** `references/registrars.md` (registrar comparison), `references/spaceship-api.md` (Spaceship API docs) and `scripts/domain_checker.py`, the stdlib RDAP availability checker that `brand-naming-method` also calls. It reports each domain as AVAILABLE, TAKEN or UNKNOWN, and UNKNOWN never means available.

---

### `review-reply-method`

Generate professional, empathetic, on-brand replies to online customer reviews. Sentiment analysis, severity detection, adaptive tone, operational suggestions.

| | |
|---|---|
| **Invoke** | Skill reference or `/digital-marketing:reply-to-customer-review` |
| **Trigger** | "reply to review", "respond to customer", "review response", Airbnb / Booking / Tripadvisor / Amazon / App Store / Trustpilot reviews |

**Sectors covered:** hospitality (Airbnb, Booking, Tripadvisor) and e-commerce / app (Amazon, App Store, Trustpilot) with sector-specific phrasing patterns. Detects negative / neutral / positive sentiment and calibrates tone (formal / friendly / casual). Flags operational issues (repeated complaint pattern) worth escalating.

---

### `ga4-implementation`

Knowledge base for implementing GA4 + GTM with EU/GDPR Consent Mode v2 compliance. Referenced by the `ga4-implementation-expert` agent.

| | |
|---|---|
| **Invoke** | Skill reference (auto-loaded by ga4-implementation-expert) |
| **Trigger** | GA4 / GTM deployment, Consent Mode v2, CMP selection, event taxonomy, conversion config, remarketing audiences |

**Content:** CMP selection guide (iubenda, Orestbida CookieConsent, Cookiebot comparison), Consent Mode v2 default + update templates, event taxonomy (recommended + custom), Key Event configuration, Google Ads conversion import, Enhanced Conversions, Predictive Audiences 28-day backfill note, framework-specific integration (Next.js / React, WordPress, vanilla HTML).

---

## Commands

### `/digital-marketing:brand-naming`

Generate, filter, score, and validate brand names through a structured naming workflow.

```
/digital-marketing:brand-naming "fitness app for busy professionals"
/digital-marketing:brand-naming "sustainable fashion marketplace" --languages en,es,pt --tlds .com,.co,.app
```

| Flag | Effect |
|------|--------|
| `--languages` | Languages to check for cultural conflicts (default: en,it,es,fr,de,pt) |
| `--tlds` | TLDs to check for domain availability (default: .com,.app,.io,.co) |

---

### `/digital-marketing:seo-audit`

5-phase technical SEO audit with Playwright analysis, scoring, a checkpoint before applying fixes, and a persistent report.

```
/digital-marketing:seo-audit https://example.com
/digital-marketing:seo-audit https://example.com --focus security,performance
/digital-marketing:seo-audit src/pages --local
```

| Flag | Effect |
|------|--------|
| `--focus` | Comma-separated category names from the technical audit (for example `security,performance`); every other category is marked `not audited` in the scorecard |
| `--local` | Audit local HTML or template files; approved fixes are edited into the local source |
| `--strict-mode` | At the checkpoint, recommend fixing every Error before approval |

**Phases:** Discovery -> Technical Audit -> Score -> (Checkpoint) -> Fix -> Report

**Output:** `.seo-audit/` directory with discovery, audit, scorecard, fixes, and final report.

---

### `/digital-marketing:content-strategy`

Marketing and conversion audit. Runs 3 parallel agents (UX/Conversion, Content/Copy, Social/Visual) with a checkpoint before applying changes and a persistent report.

```
/digital-marketing:content-strategy https://example.com
/digital-marketing:content-strategy https://example.com --focus cta,social-proof
/digital-marketing:content-strategy https://example.com --social
```

| Flag | Effect |
|------|--------|
| `--focus` | Comma-separated areas; only the agents owning a requested area run, and every other area is marked `not audited`. Agent A owns `ux`, `cta`, `social-proof`, `pricing`, `forms`, `navigation`; Agent B owns `copy`, `seo-copy`, `microcopy`, `product-descriptions`; Agent C owns `social`, `images`, `video` |
| `--social` | Shorthand for `--focus social,images,video`, which runs Agent C alone |
| `--strict-mode` | Promotes every Important finding to Critical and opens the plan with a `VERDICT: PASS` / `VERDICT: FAIL` line (FAIL when any Critical remains) |

**Phases:** Scope -> Parallel Audit (3 agents) -> Synthesis -> (Checkpoint) -> Apply -> Report

**Output:** `.content-strategy/` directory with scope, audit, plan, changes, and final report.

---

### `/digital-marketing:reply-to-customer-review`

Generate a sentiment-calibrated, sector-aware reply to a customer review.

```
/digital-marketing:reply-to-customer-review "Stay was ok but WiFi was slow" --brand "Hotel X" --tone friendly --sector hospitality
/digital-marketing:reply-to-customer-review "App crashed on checkout" --brand "MyApp" --lang en --sector ecommerce
```

| Flag | Effect |
|------|--------|
| `--brand` | Brand / product name to reference |
| `--tone` | `formal` / `friendly` / `casual` (auto-detected if omitted) |
| `--lang` | Response language (ISO 639-1 code) |
| `--sector` | `hospitality` / `ecommerce` / `auto` |

---

### `/digital-marketing:ga4-audit`

Playwright-verified GA4 + GTM audit covering Consent Mode v2 compliance, Key Event configuration, remarketing audiences, Ads linking, and CMP integration.

```
/digital-marketing:ga4-audit https://example.com
/digital-marketing:ga4-audit https://example.com --gtm GTM-XXXXXX
/digital-marketing:ga4-audit https://example.com --strict-mode
```

| Flag | Effect |
|------|--------|
| `--gtm` | Skip container detection and audit the given container ID; any other container ID found in the source is still flagged as a duplicate |
| `--strict-mode` | Report-level escalation: every Warning becomes Critical and the report carries an explicit `VERDICT: FAIL` line when any remains. It never sets a process exit code |

**5-phase audit:** Discovery (CMP + GTM / GA4 ID detection) -> Live verification via Playwright (dataLayer state pre-consent vs post-consent, event coverage per page type) -> Configuration audit (GA4 property, Key Events, Audiences, Ads linking) -> Consent Mode v2 deep check (default / update calls, granular 4-signal mapping, `wait_for_update`) -> Report with prioritized fixes.

**Output:** `.ga4-audit/` directory with discovery, verification log, config audit, consent-mode findings, and final REPORT.md.

---

### `/digital-marketing:llm-seo-audit`

Answer-engine optimization (AEO) audit. Unlike `/digital-marketing:seo-audit`, it optimizes for getting cited inside LLM-generated answers (Google AI Overviews, Perplexity, ChatGPT Search, Claude Search, Bing Copilot) rather than ranking on traditional SERPs.

```
/digital-marketing:llm-seo-audit https://example.com
/digital-marketing:llm-seo-audit https://example.com --focus schema,eeat    # target two dimensions
/digital-marketing:llm-seo-audit ./dist/                                    # static site audit
/digital-marketing:llm-seo-audit https://example.com --strict-mode          # verdict line, Warnings raised to Critical
```

| Flag | Effect |
|------|--------|
| `--focus` | `crawlers` / `eeat` / `schema` / `passages` / `injection` / `all` (default) |
| `--strict-mode` | Report-level escalation: every Warning is raised to Critical and the report opens with a `VERDICT: PASS` / `VERDICT: FAIL` line (FAIL when any Critical remains). It never sets a process exit code |

Delegates to the `llm-seo-optimize` agent (6-phase protocol). Output: `.aeo-audit/REPORT.md` with crawler-access matrix, E-E-A-T and extractability scores, JSON-LD coverage, priority fixes, AI-referral tracking setup.

---

**Related:** [research](research.md) (deep research for content strategy) | `playwright@claude-plugins-official` (Microsoft's Playwright MCP server, required for browser-based SEO / GA4 / AEO audits and trademark pre-screening; on Claude Code `claude plugin install playwright@claude-plugins-official`, on Codex, Copilot and Pi see the per-host table in the README's [Browser automation](../../README.md#browser-automation-playwright) section)
