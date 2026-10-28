# Entry routing: digital-marketing

These lines are the entry workflows and knowledge of the `digital-marketing` plugin. A request that matches a line runs through that entry before other work. A workflow or skill entry is invoked with the host's skill or command mechanism; an entry marked "agent to dispatch" is dispatched as an agent.

- `brand-naming-workflow`: TRIGGER WHEN: the user asks for brand, startup, product, or company names.
- `content-strategy-workflow`: TRIGGER WHEN: the user asks for a content, marketing, conversion, or CRO audit of a website, landing page, or funnel. DO NOT TRIGGER WHEN: the audit is technical SEO only (use seo-audit-workflow).
- `ga4-audit-workflow`: TRIGGER WHEN: the user asks to audit GA4, verify GTM setup, check Consent Mode v2 compliance, debug missing conversions, validate dataLayer events, or check "why isn't my site converting". DO NOT TRIGGER WHEN: the task is general SEO (use seo-audit-workflow), or content and CTA optimization (use content-strategy-workflow).
- `llm-seo-audit-workflow`: TRIGGER WHEN: auditing AI search visibility, AI-bot crawler or CDN access, Search Console generative AI settings, E-E-A-T, answerability of customer questions, JSON-LD accuracy, llms.txt questions or prompt-injection hardening.
- `reply-to-customer-review-workflow`: TRIGGER WHEN: the user pastes a customer review (Airbnb, Booking, Tripadvisor, Amazon, Trustpilot, App Store, Google) and asks for a reply or response.
- `seo-audit-workflow`: TRIGGER WHEN: the user asks for a technical SEO audit, Core Web Vitals check, sitemap, redirect, or crawlability review, structured data or meta tags, mobile usability, or SERP ranking analysis.
