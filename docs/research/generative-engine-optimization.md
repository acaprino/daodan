<a id="generative-engine-optimization-research"></a>

# Generative engine optimization: what makes a site visible in AI answers

[Used by Digital Marketing](../plugins/digital-marketing.md) · [Evidence and verification](generative-engine-optimization-evidence.md)

*Research date: 2026-10-28. Sources read between 13:20 and 14:10 Europe/Rome.*

## TL;DR

- **Problem:** Decide what an answer-engine optimization (AEO, also called GEO) audit should check and recommend so that a site is reached, selected and correctly cited by Google AI Overviews and AI Mode, ChatGPT Search, Perplexity, Microsoft Copilot and Claude.
- **Access and indexing come first.** Google shows a page in its AI features only when it is indexed and snippet-eligible. In controlled tests, putting a document at the top of the model's context beat every content rewrite, and a 45-study survey names topical relevance and context position as the only reproducible levers.
- **Rewriting content "for AI" does not hold up.** The original GEO gains (up to 40%) came from a simulated engine with a fixed context. On modern models most rewrite tactics averaged near zero, adding statistics lowered rankings in 19 of 24 settings, and a 2026 re-measurement on ten engine families found the 2023 levers move citation on none. Google states that chunking, AI-specific writing, special schema and llms.txt are not needed.
- **One answer is not a measurement.** Engines cite almost disjoint URL sets (mean pairwise Jaccard 0.0079) and the same engine replaced 67% of its cited URLs in one day. Visibility needs repeated sampling.
- **The platform controls changed in 2026.** Search Console gained a Search generative AI control and a Generative AI performance report (all sites since 2026-08-31); Cloudflare replaced "Block AI bots" with Search, Agent and Training policies (2026-09-15); Bing Webmaster Tools has AI Performance in preview; GA4 has an AI Assistant channel.
- **Consequence:** the `digital-marketing` AEO agent was redesigned around eligibility, access, answerability and measurement, and stopped recommending citation-bait rewrites and llms.txt (plugin 1.1.0).

## Why we conducted the research

1. **A user-supplied GEO guide contradicted the plugin.** `llm-seo-optimize` stated that Search Console does not separate AI Overviews, that `GPTBot` serves ChatGPT search retrieval, that the user-fetch bots are the minimum allow set, and that llms.txt is "zero-cost to publish". The guide, checked against primary pages on 2026-10-28, contradicted all four.
2. **The agent's premise was content rewriting.** Its description was "rewrites prose and markup for verbatim quotability", with passage formulas (answer in the first 40-60 words, bullets quoted more often, numbers with units more likely cited). These rules come from the GEO literature, which needed checking against replications on live engines.
3. **Gaps in the audit.** Nothing checked CDN or WAF bot blocking, snippet controls, the Search Console setting, Bing's AI reporting, IndexNow or Merchant Center.

## Links to cited papers

| # | Work / Paper | Link | What it measures | Relevant finding |
|---|---|---|---|---|
| 1 | Aggarwal, Murahari, Rajpurohit, Kalyan, Narasimhan, Deshpande. *GEO: Generative Engine Optimization*. KDD 2024. | [arXiv:2311.09735](https://arxiv.org/abs/2311.09735) | Nine content rewrites on GEO-bench (10K queries) with a simulated engine (top-5 Google results, gpt-3.5-turbo), plus 200 samples on Perplexity with sources uploaded as files. | Quotation +41%, Statistics +31%, Cite Sources +27.5% position-adjusted word count; keyword stuffing −8%. Gains go to low-ranked sources (rank 5 up to +115%) and rank-1 sources lose 20-30%. Simulated, fixed context. |
| 2 | Puerto, Gubri, Green, Oh, Yun. *C-SEO Bench: Does Conversational SEO Work?* NeurIPS Datasets and Benchmarks 2025. | [arXiv:2506.11097](https://arxiv.org/abs/2506.11097) | Eight GEO rewrites and two new ones across 6 domains, 1.9k+ queries, on gpt-4o-mini, claude-3.5-haiku, o3 and o4-mini, with multi-actor adoption. | Most methods average near zero; Statistics lowers rankings in 19 of 24 settings. Moving a document to position 1 of the context gains +0.70 to +2.77 positions in all domains. Gains dilute as more competitors adopt a method. Traditional SEO (retrieval rank) has the larger impact. |
| 3 | Martinez. *Optimizing Visibility in Generative Engines: A Critical Survey of Generative Engine Optimization (2023-2026)*. Preprint 2026. | [arXiv:2607.14035](https://arxiv.org/abs/2607.14035) | Critical survey of 45 GEO studies. | Foundational gains depend on a source already being in a fixed context; topical relevance and context position are the most reproducible levers; generic heuristics transfer poorly; citation-oriented rewrites can impair retrieval; no technique shows a stable cross-platform causal effect. |
| 4 | Bajemon, Rochet. *Scoring Without the Engine*. Preprint 2026. | [arXiv:2609.07559](https://arxiv.org/abs/2609.07559) | Re-measures the 2023 GEO causal anchors on ten modern engine families; validates an engine-free content score. | The 2023 levers move citation on none of the ten families. The content score correlates weakly with citation (within-query Spearman 0.11); adversarial amplification gains at most 6 points. |
| 5 | Tannenbaum. *Scoring With the Engine: Retrieval Exposure, Cross-Engine Divergence, and the Limits of Engine-Agnostic GEO Scores*. Preprint 2026. | [arXiv:2609.22655](https://arxiv.org/abs/2609.22655) | 15 prompts on ChatGPT, Copilot, Google and Perplexity (589 citation observations), repeated on consecutive days. | Mean pairwise same-prompt URL Jaccard 0.0079; 84.9% of engine pairs share no URL; 96.4% of URLs appear on one engine only; 67.0% same-engine turnover in one day. Report page fit, exposure, selection and visibility separately. |
| 6 | Grossman, Liu, Chen, Smith, Borcea, Chen. *How Generative AI Disrupts Search: An Empirical Study of Google Search, Gemini, and AI Overviews*. SIGIR 2026. | [arXiv:2604.27790](https://arxiv.org/abs/2604.27790) | 11,500 real-user queries on Google Search, AI Overviews and Gemini. | AI Overviews on 51.5% of queries; sources across the three systems overlap below 0.2 Jaccard; AI Overviews are less consistent across runs; sites blocking Google's AI crawler are retrieved less often (observational); Google-owned content is favoured. |
| 7 | Zhang, He, Yao. *From Citation Selection to Citation Absorption*. Preprint 2026. | [arXiv:2604.25707](https://arxiv.org/abs/2604.25707) | 602 prompts on ChatGPT, Google AI Overviews/Gemini and Perplexity; 21,143 citations, 72 page features. | High-influence cited pages are longer, structured, aligned to the question and rich in definitions, numbers, comparisons and steps. Descriptive, not causal. |
| 8 | Chen, Wang, Chen, Koudas. *Generative Engine Optimization: How to Dominate AI Search*. Preprint 2025. | [arXiv:2509.08919](https://arxiv.org/abs/2509.08919) | Source mix of AI search engines vs Google. | AI engines favour earned third-party media over brand-owned and social content. Abstract only. |
| 9 | Fang, Tao, Chen, Chang, Sakai. *Do Large Language Models Favor Recent Content?* Preprint 2025, v2 2026. | [arXiv:2509.11353](https://arxiv.org/abs/2509.11353) | Fake publication dates prepended to passages, seven LLM rerankers, TREC DL21/DL22. | Top-10 mean year shifts up to 4.78 years; items move up to 95 ranks; up to 25% preference reversals. Larger models attenuate but do not remove the effect. |
| 10 | Liu, Zhang, Liang. *Evaluating Verifiability in Generative Search Engines*. Findings of EMNLP 2023. | [arXiv:2304.09848](https://arxiv.org/abs/2304.09848) | Human audit of Bing Chat, NeevaAI, Perplexity, YouChat. | Only 51.5% of generated sentences fully supported by citations; 74.5% of citations support their sentence. |
| 11 | Nestaas, Debenedetti, Tramèr. *Adversarial Search Engine Optimization for Large Language Models*. Preprint 2024. | [arXiv:2406.18382](https://arxiv.org/abs/2406.18382) | Preference manipulation attacks on live Bing Copilot and Perplexity. | An attacker's product became 2.5x more likely to be recommended on Bing; external-page injections succeed far less than direct ones; Copilot reads pages beyond rank 10 in half the searches. |
| 12 | Kumar, Lakkaraju. *Manipulating Large Language Models to Increase Product Visibility*. Preprint 2024. | [arXiv:2404.07981](https://arxiv.org/abs/2404.07981) | Strategic text sequences on a fictitious product catalog. | A strategic sequence makes a product significantly more likely to be the top recommendation. |
| 13 | Khodayari, Zhang, Acharya, Pellegrino. *Indirect Prompt Injection in the Wild*. Preprint 2026. | [arXiv:2604.27202](https://arxiv.org/abs/2604.27202) | Crawl of 1.2B URLs from 24.8M hosts; 5,200 controlled experiments on 13 models. | 15.3K validated injections on 11.7K pages, about 70% in non-rendered HTML (headers, comments, metadata); compliance up to 8% on small models with plain text; structured representations reduce it. |

## Vendor documentation

| # | Source | Date | Fact used |
|---|---|---|---|
| D1 | [Google: AI optimization guide](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) | updated 2026-07-10 | llms.txt, chunking, AI-specific writing and special schema not needed; manipulation at scale violates spam policy; Business Profile and Merchant Center help visibility in AI responses; site must be included in Search generative AI features. |
| D2 | [Google: AI features and your website](https://developers.google.com/search/docs/appearance/ai-features) | updated 2025-12-10 | Supporting links require indexing and snippet eligibility, no extra requirement; controls are robots.txt, nosnippet, data-nosnippet, max-snippet, noindex. |
| D3 | [Search Console: Search generative AI control](https://support.google.com/webmasters/answer/16908024) | rolled out 2026-08-31 | Settings > Search generative AI; default include; inherits from parent or top-level domain property; covers AI Overviews, AI Mode, Discover generative features; not ranking, not training. |
| D4 | [Search Console: Generative AI performance report](https://support.google.com/webmasters/answer/16984139) | rolled out 2026-08-31 | Impressions in AI Overviews and AI Mode; hidden below an impression threshold; excludes Search Labs. |
| D5 | [Google common crawlers](https://developers.google.com/search/docs/crawling-indexing/google-common-crawlers) | updated 2026-10-15 | Google-Extended is a control token with no user agent; Gemini training and grounding; no effect on Search inclusion or ranking. |
| D6 | [Google user-triggered fetchers](https://developers.google.com/search/docs/crawling-indexing/google-user-triggered-fetchers) | updated 2026-08-19 | Google-Agent and other user-triggered fetchers generally ignore robots.txt. |
| D7 | [OpenAI crawlers](https://developers.openai.com/api/docs/bots) | undated | OAI-SearchBot for search, GPTBot for training, ChatGPT-User user-initiated and may ignore robots.txt; published IP lists. |
| D8 | [Perplexity crawlers](https://docs.perplexity.ai/guides/bots) | undated | PerplexityBot for search (not training), Perplexity-User generally ignores robots.txt; IP lists; Cloudflare and AWS WAF allow rules. |
| D9 | [Anthropic crawlers](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler) | 2026-04-07 | ClaudeBot training, Claude-User user fetch, Claude-SearchBot search; bots honor robots.txt and Crawl-delay; IP list; anthropic-ai and Claude-Web not mentioned. |
| D10 | [Apple: About Applebot](https://support.apple.com/en-us/119829) | 2026-09-04 | Applebot powers Spotlight, Siri, Safari and may train models; Applebot-Extended does not crawl and does not remove pages from search; Applebot follows Googlebot rules when unnamed. |
| D11 | [Bing: AI Performance public preview](https://blogs.bing.com/webmaster/2026/2/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview/) | 2026-02-10 | Citations, cited pages, grounding queries; content guidance (headings, tables, FAQ, evidence, freshness); IndexNow; Bing Places. |
| D12 | [Bing: AI visibility insights](https://blogs.bing.com/search/2026/6/New-AI-Visibility-Insights-in-Bing-Webmaster-Tools-Intents-Topics-Citation-Share-Compare/) | 2026-06-16 | Intents, Topics, Citation Share, Compare in preview; Citation Share is observational, not a ranking; no API or export mentioned. |
| D13 | [Bing: Topics Portfolio](https://blogs.bing.com/webmaster/2026/10/introducing-topics-portfolio-beta-in-ai-performance/) | 2026-10-13 | Topics Portfolio beta in AI Performance. |
| D14 | [Cloudflare: Block AI bots](https://developers.cloudflare.com/bots/additional-configurations/block-ai-bots/) | updated 2026-07-01 | Deprecated 2026-09-15; Search, Agent, Training policies; new domains block Training and Agent on pages with ads; mixed search and training crawlers blocked by any training block. |
| D15 | [Cloudflare: managed robots.txt](https://developers.cloudflare.com/bots/additional-configurations/managed-robots-txt/) | updated 2026-10-22 | Content-signal line; search excludes AI summaries; compliance voluntary, no engine commitment documented. |
| D16 | [IndexNow participants](https://www.indexnow.org/searchengines.json) | undated | Bing, Yandex, Seznam, Naver, Yep, Internet Archive, Amazonbot; not Google. |
| D17 | [GA4 default channel group](https://support.google.com/analytics/answer/9756891) | undated | AI Assistant channel (medium ai-assistant or referrer list); AI Overviews and AI Mode count as Organic Search. |
| D18 | [Search Console API searchanalytics.query](https://developers.google.com/webmaster-tools/v1/searchanalytics/query) | updated 2026-08-11 | No AI search type or dimension. |

## Existing tools

Surveyed to decide delegation or inspiration. Repository metadata read on 2026-10-28.

| Tool | License, last push, stars | What it adds | Decision |
|---|---|---|---|
| [claude-seo](https://github.com/AgriciDaniel/claude-seo) | MIT, 2026-10-22, 23K | Full SEO and GEO audit, WAF user-agent matrix run only with authorization, Content-Signal and Web Bot Auth, Bing and IndexNow commands; citation tracking only through paid extensions. | Inspiration: the authorization rule and the reading of a spoofed probe as unverified traffic. Not delegated: a second full audit owner, Claude Code only, open-core. |
| [geo-optimizer-skill](https://github.com/Auriti-Labs/geo-optimizer-skill) | MIT, 2026-10-27, 1.2K | CDN check comparing bot and browser user agents, challenge markers, CDN header map; `geo citations` sampling with repeated runs. | Inspiration: the CDN probe design. Not delegated: open-core with its own scoring rubric. |
| [Canonry](https://github.com/Canonry/canonry) | MIT, 2026-10-28, 194 | Bring-your-own-key citation tracking, Search Console, Bing, GA4 and server-side crawler logs, MCP, Claude and Codex adapters. | Candidate measurement backend; not adopted: young project, needs provider keys. Open for an owner decision. |
| [Elmo](https://github.com/elmohq/elmo) | MIT, 2026-10-27, 517 | Scheduled prompt tracking on ChatGPT, AI Mode, AI Overviews, Gemini, Perplexity, Copilot; MCP. | Not adopted: needs Docker, PostgreSQL and paid keys. |
| [marketingskills](https://github.com/coreyhaines31/marketingskills) | MIT, 2026-10-27, 57K | Prompt skills for SEO and AI SEO. | No: overlaps, and its AI SEO skill still states that Search Console has no AI reporting. |
| Others: open-seo-mcp-skills, geoptimize, aaron-marketing-skills, bing-webmaster-mcp, mcp-gsc | various | Hosted connectors, content lint, static prompts, Bing or GSC data. | No: closed data path, no gap covered, or too immature. Two unlicensed repositories excluded. |

No tool reads the Search Console Generative AI report or Bing AI Performance programmatically: neither has a documented API.

## Content summary and findings

### 1. What holds

1. **Eligibility and access decide whether a page can be cited at all** (D1, D2, papers 2, 3). Indexing, snippet eligibility, the Search Console control, robots.txt per user agent and the CDN layer come before any content work.
2. **Search and training are separate decisions** (D5, D7, D8, D9, D10). Each vendor separates its search crawler from its training token; blocking training does not remove a site from search features, with one observed exception to watch (finding 3.1).
3. **Write for the customer's decision, for readers** (D1, D11; paper 7 descriptive). Structured pages with definitions, comparisons and steps are the ones cited with most influence, but no study shows that restructuring causes citation.
4. **Measure with repeated runs and separate quantities** (papers 5, 6, 10). Cross-engine overlap is near zero and same-engine turnover is high; citations do not always support the text they sit on.
5. **Most web prompt injections sit in non-rendered HTML** (paper 13), and persuasion aimed at engines works on live systems (papers 11, 12). An audit checks comments, metadata, headers and JSON-LD, and treats engine-directed persuasion as manipulation.
6. **Dates are a manipulation vector** (paper 9). Visible and structured dates change only with substantive updates.

### 2. What was refuted or downscaled

- ~~Content rewrites (statistics, quotations, authoritative tone, citations) raise AI citation by up to 40%~~: measured on a simulated engine (paper 1); near zero or negative on modern models (papers 2, 4); not stable across platforms (paper 3).
- ~~Ranking position is a weaker signal for LLMs~~: retrieval rank and context position are the strongest measured levers (papers 2, 3).
- ~~llms.txt is zero-cost to publish and helps~~: Google ignores it (D1); the only academic analogue, an in-document summary, helped one model in two domains (paper 2).
- ~~JSON-LD helps the model attribute claims~~: no special schema is needed for Google's AI features (D1, D2); structured data earns rich results.
- ~~GPTBot serves ChatGPT search retrieval~~: GPTBot is training; OAI-SearchBot is search (D7).
- ~~Search Console does not break AI Overviews out~~: the Generative AI performance report exists for every site since 2026-08-31 (D4).

### 3. Contradictions and open points

1. **Google-Extended.** Google states that it does not affect Search inclusion (D5); paper 6 observed that sites blocking Google's AI crawler are retrieved less often by AI Overviews. Observational, possibly confounded. The plugin reports the trade-off instead of choosing a side.
2. **ChatGPT UTM tagging.** That ChatGPT appends `utm_source=chatgpt.com` rests on a search snippet. The OpenAI publisher FAQ (article 12627856) redirects to "ChatGPT Atlas retirement" in a real browser as well. Marked *(verify)* in the plugin.
3. **Content signals.** Cloudflare documents no engine committed to honoring them (D15).
4. **Unread vendor pages.** Bytespider, CCBot, Meta-ExternalAgent, Amazonbot, MistralAI-User, DuckAssistBot; Microsoft's October 2025 guide on AI search inclusion; Bing's AI Performance FAQ. Their rows in the plugin are marked *(verify)*.
5. **No live test.** Nothing here was exercised on a real site. The plugin's CDN probe and question sampling are procedures, not measured results.

### 4. Consequences for the plugin

`digital-marketing` 1.1.0, agent `llm-seo-optimize` and workflow `llm-seo-audit`:

- principles derived from findings 1.1 to 1.4 and section 2, stated as instructions without citations;
- Phase 1 became eligibility and access: indexing, snippet controls, Search Console control, a per-vendor robots.txt table split by search, user fetch and training, CDN and WAF with an authorization-gated probe, discovery (IndexNow, Business Profile, Bing Places, Merchant Center), llms.txt as information only;
- Phase 3 became answerability of the customers' real questions; citation-bait rewrites are forbidden;
- Phase 6 checks non-rendered HTML first and flags engine-directed persuasion;
- measurement separates shown or cited (Search Console, Bing AI Performance, repeated sampling), visits (GA4 AI Assistant) and outcomes.

## Changelog

### 2026-10-28

First version. Three web research runs (platform facts, papers, existing tools) and coordinator re-checks of the load-bearing sources; prompts, verbatim reports and per-source verification status are in the [evidence file](generative-engine-optimization-evidence.md).
