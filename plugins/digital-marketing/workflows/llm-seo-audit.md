---
description: >
  Audit whether answer engines (AI Overviews, AI Mode, ChatGPT Search, Perplexity, Copilot, Claude) can reach, select and correctly cite a site.
  TRIGGER WHEN: auditing AI search visibility, AI-bot crawler or CDN access, Search Console generative AI settings, E-E-A-T, answerability of customer questions, JSON-LD accuracy, llms.txt questions or prompt-injection hardening.
  DO NOT TRIGGER WHEN: traditional SERP ranking SEO (use /digital-marketing:seo-audit) or copy tone/voice (use content-marketer).
argument-hint: "<url or local path> [--focus <comma-separated: crawlers,eeat,schema,passages,injection | all>] [--strict-mode]"
---

# LLM SEO / Answer Engine Optimization Audit

Invokes the `llm-seo-optimize` agent to audit whether answer engines can reach a site, select its pages and cite them correctly. Different from `/digital-marketing:seo-audit` (traditional SERP ranking), although most of the groundwork is shared: answer engines retrieve from search indexes first.

## CRITICAL RULES

1. **Delegate to the `llm-seo-optimize` agent**. This command is a thin wrapper: the agent owns the full 6-phase audit, the report format and the measurement plan.
2. **Verify live, not just code**. For a live URL, use the Playwright MCP tools (the `playwright` plugin, a declared dependency) to fetch `robots.txt`, read response headers, check JSON-LD and render the pages.
3. **Write output to `.aeo-audit/` for persistence** so re-runs can diff against the baseline.
4. **Never fabricate crawler policies or settings**. If `robots.txt`, the CDN bot policy or the Search Console setting cannot be read, report it as `not confirmed`.
5. **Probe a WAF only with authorization**. Requests with a bot's user agent run only when the user owns the site or confirms authorization, and their result describes unverified traffic, not the real bot.

## Procedure

### 1. Parse arguments

- `<url or local path>`: required target, a live URL or a path to a static site / built HTML output
- `--focus`: restrict the audit to a subset of dimensions. Values are comma-combinable (`--focus schema,eeat`). Default: `all`, which runs every phase
  - `crawlers`: eligibility and access (indexing, snippet controls, Search Console control, robots.txt per user agent, CDN/WAF, discovery)
  - `eeat`: E-E-A-T signals (authorship, dates, citations, evidence)
  - `schema`: JSON-LD accuracy and citation readiness
  - `passages`: answerability of the customers' real questions
  - `injection`: prompt-injection hardening (non-rendered HTML, hidden text, persuasion aimed at engines)
- `--strict-mode`: report-level severity escalation. Every Warning is raised to Critical and the report opens with an explicit `VERDICT: PASS` / `VERDICT: FAIL` line, FAIL when any Critical remains

### 2. Spawn the agent

Invoke `digital-marketing:llm-seo-optimize` with the target, focus, and strict-mode flag. The agent runs its 6-phase protocol.

### 3. Report

The agent writes `.aeo-audit/REPORT.md` in its OUTPUT FORMAT, closing with the measurement setup: the Search Console Generative AI performance report, Bing Webmaster Tools AI Performance, GA4's AI Assistant channel and the repeated sampling of the customer question set.

## Typical flow

```
# Full audit against a live URL
/digital-marketing:llm-seo-audit https://example.com

# Access only: indexing, robots.txt, CDN, Search Console control
/digital-marketing:llm-seo-audit https://example.com --focus crawlers

# Static site audit
/digital-marketing:llm-seo-audit ./dist/

# Strict grading: warnings become critical, report opens with PASS/FAIL
/digital-marketing:llm-seo-audit https://example.com --strict-mode
```

## Complementary commands

Run alongside traditional SEO tooling for a complete picture:

| Command | Purpose | Overlap with AEO |
|---------|---------|------------------|
| `/digital-marketing:seo-audit` | Technical SEO (Core Web Vitals, meta tags, sitemap, redirects, SERP ranking) | High: indexing and crawlability are prerequisites for every Google AI feature |
| `/digital-marketing:content-strategy` | Conversion / CTA / tone / funnel audit | Medium: answering customer decisions serves both |
| `/digital-marketing:ga4-audit` | GA4 + GTM + Consent Mode v2 verification | Measurement only: AI traffic arrives through GA4's AI Assistant channel |
| **`/digital-marketing:llm-seo-audit`** | **AEO / answer-engine optimization** | |

## Synergies

- Deep knowledge base: `digital-marketing:llm-seo-optimize` agent (the actual worker)
- Structured data validation alongside broader checks: `/digital-marketing:seo-audit`
- Measurement setup: `digital-marketing:ga4-implementation-expert` agent (AI traffic channels)
- Humanizing AI-sounding copy: `/daodan:humanize-text`
- Playwright-based live verification: the `playwright` plugin (Microsoft's Playwright MCP server)
