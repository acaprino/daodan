# Business Plugin

> Navigate tech law and SaaS strategy without a full-time CMO or lawyer on retainer. Contract review, GDPR/CCPA compliance, IP protection, risk assessment, and end-to-end SaaS business planning (positioning, pricing, GTM, unit economics) tailored to software businesses.

## Prerequisites

Two local plugins are hard dependencies: `text-humanizer`, whose agent `business-planner` runs over the final GTM strategy document, and `research`, whose `quick-searcher` and `deep-researcher` agents do the planner's market, competitor and pricing lookups.

## Agents

### `business-planner`

Fractional CMO and GTM strategist for SaaS business planning. Socratic Phase-gated approach (one phase at a time, targeted questions, data-driven benchmarks).

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | SaaS business plan, GTM strategy, positioning, pricing strategy, market sizing (TAM/SAM/SOM), PMF validation, persona design, competitive analysis, unit economics |

**Invocation:**
```
Use the business-planner agent to plan [business dimension] for [product]
```

**Methodology:**
- Socratic one-phase-at-a-time questioning (no questionnaire dumps)
- Data-driven benchmarks (industry conversion rates, churn, CAC/LTV targets)
- Frameworks: April Dunford positioning, Blue Ocean, Crossing the Chasm, PLG/SLG/hybrid GTM, Jobs-to-be-Done
- Builds on the `saas-business-plan` knowledge base

**Workflow phases (7):** Market Sizing -> Audience & JTBD -> Competitive Analysis -> Positioning -> Pricing -> Go-to-Market -> Metrics, KPI & Financial Projections. Stops at each phase for user validation; the user can skip ahead, go back to a phase, or ask where the session stands.

**Running draft:** after each phase the agent writes its conclusions to `draft-business-plan.md` in the working directory, so nothing is lost across phases and the user holds a tangible artifact at every step. Phase 7 turns that draft into the final deliverable, `[ProductName]_GTM_Strategy.md`.

**Humanization pass:** the final `[ProductName]_GTM_Strategy.md` goes through the `text-humanizer:text-humanizer` agent before delivery, to remove AI writing traces (inflated language, formulaic structures, promotional tone).

---

### `privacy-doc-generator`

Drafts privacy compliance documents: Privacy Policies, Cookie Policies, DPAs, consent notices, DPIA reports. Covers EU/Italy (GDPR, ePrivacy, Codice Privacy) with modular support for CCPA, LGPD, and FADP.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Drafting or auditing privacy and data protection documents for websites, apps, or SaaS products |

**Invocation:**
```
Use the privacy-doc-generator agent to draft a [privacy policy/cookie policy/DPA] for [product]
```

**Workflow:** Phase 0 Regulatory Delta Check (only when an existing document is passed in for review or update) -> Context gathering (jurisdiction, business profile, processing activities, cookie assessment) -> Risk analysis (DPIA triggers, transfer risks, sector overlays) -> Document generation -> Validation -> Output with evidence pack.

**Key features:**
- ROPA-driven generation: builds a structured processing model before drafting
- Normative references on every clause (article, guideline, recital)
- Legal research phase with source verification against official texts
- Uncertainty markers (`[NON SPECIFICATO]`, `[REQUIRES LEGAL REVIEW]`, `[ASSUMPTION]`)

---

### `legal-advisor`

Technology law advisor for advisory analysis and general legal documents: contracts, NDAs, IP/copyright, employment law, M&A, corporate governance, regulatory compliance.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Contract review, NDAs, IP protection, employment law, corporate governance, legal risk assessment |

**Invocation:**
```
Use the legal-advisor agent for [contract review / IP question / compliance check]
```

**Workflow:** Phase 0 Regulatory Delta Check (only when an existing document is passed in) -> Research & Assessment -> Implementation -> Verification.

Route privacy document drafting (Privacy Policies, Cookie Policies, DPAs, DPIA reports) to `privacy-doc-generator` instead.

---

### Regulatory Delta Check (both legal agents)

When the user passes an existing document (a policy, contract or agreement) to review, update, audit or assess, `privacy-doc-generator` and `legal-advisor` both start with Phase 0: they extract the document's jurisdictions, cited normative sources and last-update date (asking for the date when the document carries none), then run a capped set of 4-6 targeted WebSearch queries against EDPB, Garante, EUR-Lex and CJEU sources covering the years since that date. The output is advisory: a table of updates with the impacted section and relevance, or a statement that nothing relevant was found, with sources that returned nothing marked "unable to verify" and an all-failed search reported as inconclusive before proceeding to Phase 1. A brand-new document with no existing file skips Phase 0.

---

## Skills

### `saas-business-plan`

Strategic knowledge base for SaaS business planning and GTM strategy (2025-2026 market data).

| | |
|---|---|
| **Invoke** | Skill reference (loaded by `business-planner` agent) |
| **Use for** | Market sizing (TAM/SAM/SOM), persona frameworks, competitive analysis, pricing models (freemium, usage-based, tiered), positioning (April Dunford, Blue Ocean), GTM motions (PLG / SLG / hybrid), advertising benchmarks, KPI targets |

**References:** 8 deep-dive references covering persona design, TAM/SAM/SOM calculation, competitive frameworks, pricing tiers and elasticity, GTM funnel design, PMF measurement, SaaS metrics (CAC/LTV/NRR/logo churn), and advertising benchmarks. Loaded progressively by the `business-planner` agent based on the phase.

---

**Related:** [stripe](stripe.md) (payment integration and compliance) | [digital-marketing](digital-marketing.md) (SEO and content strategy)

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `1.12.0`. **Source:** [plugin.toml](<../../plugins/business/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | [research](<research.md>), [text-humanizer](<text-humanizer.md>) |
| Direct external | None |
| Local closure (3) | [business](<business.md>), [research](<research.md>), [text-humanizer](<text-humanizer.md>) |
| External closure (0) | None |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `repository.read`, `repository.write`, `network.fetch`, `contexts.isolate`, `roles.dispatch`.
**Optional capabilities:** `execution.parallel`.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `business:saas-business-plan` | Knowledge base of strategy frameworks and market data, loaded by business-planner. TRIGGER WHEN: SaaS business planning or GTM strategy work, including positioning frameworks (April Dunford, Blue Ocean, Crossing the Chasm), PLG/SLG motions, and KPI benchmarks. | [saas-business-plan](<../../plugins/business/skills/saas-business-plan/SKILL.md>) |
| Role | `business:business-planner` | Fractional CMO working Socratically, one phase at a time, against benchmarks. TRIGGER WHEN: the user needs SaaS business planning, go-to-market strategy, positioning, pricing strategy, market sizing, TAM/SAM/SOM, or product-market fit work. DO NOT TRIGGER WHEN: legal or compliance questions (use legal-advisor), privacy documents (use privacy-doc-generator). | [business-planner](<../../plugins/business/roles/business-planner.md>) |
| Role | `business:legal-advisor` | Advise on technology law and risk, and draft the documents. TRIGGER WHEN: contracts, NDAs, terms of service, IP and copyright, employment law, M&A, corporate governance, regulatory compliance, legal risk assessment, or advisory memos. DO NOT TRIGGER WHEN: Privacy Policies, Cookie Policies, DPAs, or DPIA reports (use privacy-doc-generator); business planning (use business-planner). | [legal-advisor](<../../plugins/business/roles/legal-advisor.md>) |
| Role | `business:privacy-doc-generator` | Draft and audit data-protection documents from a ROPA-driven model. TRIGGER WHEN: the user needs a Privacy Policy, Cookie Policy, DPA, consent notice, or DPIA under GDPR, ePrivacy, Codice Privacy, CCPA, LGPD, or FADP. DO NOT TRIGGER WHEN: general legal, contract, NDA, or IP questions (use legal-advisor); cookie banners, Consent Mode v2, or GTM (use digital-marketing:ga4-implementation-expert); business planning (use business-planner). | [privacy-doc-generator](<../../plugins/business/roles/privacy-doc-generator.md>) |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/business](<../../exports/claude/plugins/business>) | `native` | No workflow entry points |
| copilot | [exports/copilot/plugins/business](<../../exports/copilot/plugins/business>) | `native` | No workflow entry points |
| codex | [exports/codex/plugins/business](<../../exports/codex/plugins/business>) | `adapted` | No workflow entry points |
| pi | [exports/pi/plugins/business](<../../exports/pi/plugins/business>) | `adapted` | No workflow entry points |
| opencode | [exports/opencode/plugins/business](<../../exports/opencode/plugins/business>) | `native` | No workflow entry points |

<!-- daodan:reference:end -->
