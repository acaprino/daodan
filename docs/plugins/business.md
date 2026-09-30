# Business Plugin

> Navigate tech law and SaaS strategy without a full-time CMO or lawyer on retainer. Contract review, GDPR/CCPA compliance, IP protection, risk assessment, and end-to-end SaaS business planning (positioning, pricing, GTM, unit economics) tailored to software businesses.

## Prerequisites

The `text-humanizer` plugin is a hard dependency: `business-planner` runs its agent over the final GTM strategy document.

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
