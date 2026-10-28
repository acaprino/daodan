# Entry routing: digital-marketing

These lines are the entry workflows and knowledge of the `digital-marketing` plugin. A request that matches a line runs through that entry before other work. A workflow or skill entry is invoked with the host's skill or command mechanism; an entry marked "agent to dispatch" is dispatched as an agent.

- `/digital-marketing:brand-naming`: TRIGGER WHEN: the user asks for brand, startup, product, or company names.
- `/digital-marketing:content-strategy`: TRIGGER WHEN: the user asks for a content, marketing, conversion, or CRO audit of a website, landing page, or funnel. DO NOT TRIGGER WHEN: the audit is technical SEO only (use /digital-marketing:seo-audit).
- `/digital-marketing:ga4-audit`: TRIGGER WHEN: the user asks to audit GA4, verify GTM setup, check Consent Mode v2 compliance, debug missing conversions, validate dataLayer events, or check "why isn't my site converting". DO NOT TRIGGER WHEN: the task is general SEO (use /digital-marketing:seo-audit), or content and CTA optimization (use /digital-marketing:content-strategy).
- `/digital-marketing:llm-seo-audit`: TRIGGER WHEN: auditing AI search visibility, AI-bot crawler or CDN access, Search Console generative AI settings, E-E-A-T, answerability of customer questions, JSON-LD accuracy, llms.txt questions or prompt-injection hardening.
- `/digital-marketing:reply-to-customer-review`: TRIGGER WHEN: the user pastes a customer review (Airbnb, Booking, Tripadvisor, Amazon, Trustpilot, App Store, Google) and asks for a reply or response.
- `/digital-marketing:seo-audit`: TRIGGER WHEN: the user asks for a technical SEO audit, Core Web Vitals check, sitemap, redirect, or crawlability review, structured data or meta tags, mobile usability, or SERP ranking analysis.
