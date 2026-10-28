<a id="generative-engine-optimization-evidence"></a>

# Generative engine optimization: evidence and verification

[Research summary](generative-engine-optimization.md) · [Used by Digital Marketing](../plugins/digital-marketing.md)

*Collected on 2026-10-28, Europe/Rome. This file keeps the raw evidence behind the
research summary: how each source was verified, the three research prompts as they
were run, and the three researcher reports verbatim.*

## How the research ran

Three `research:deep-researcher` runs in parallel, web backend without a search API
key: platform facts (5 searches, 14 pages), papers (13 searches, 16 pages) and existing
tools (17 searches, 23 pages including GitHub API reads). The coordinator then
re-fetched the load-bearing sources itself. Before the runs, seven vendor pages had
already been read directly to check a user-supplied GEO guide.

## Per-source verification

| Source | Checked by | Status |
|---|---|---|
| D1 Google AI optimization guide | coordinator, direct fetch | verified (updated 2026-07-10) |
| D2 Google AI features and your website | coordinator, direct fetch | verified (updated 2025-12-10) |
| D3 Search Console generative AI control | coordinator, direct fetch | verified |
| D4 Search Console Generative AI performance report | coordinator, direct fetch | verified |
| D5 Google common crawlers | coordinator, direct fetch | verified (updated 2026-10-15) |
| D6 Google user-triggered fetchers | coordinator, direct fetch | verified (updated 2026-08-19) |
| D7 OpenAI crawlers | coordinator, direct fetch | verified |
| D8 Perplexity crawlers | coordinator, direct fetch | verified |
| D9 Anthropic crawlers | coordinator, direct fetch | verified (2026-04-07). Robots.txt compliance is stated for Anthropic's bots collectively, not per bot |
| D10 Apple, About Applebot | coordinator, direct fetch | verified (2026-09-04) |
| D11 Bing AI Performance post | coordinator, direct fetch | verified (2026-02-10) |
| D12 Bing AI visibility insights | coordinator, direct fetch | verified (2026-06-16) |
| D13 Bing Topics Portfolio | researcher only | not re-checked |
| D14 Cloudflare Block AI bots | coordinator, direct fetch | verified (updated 2026-07-01) |
| D15 Cloudflare managed robots.txt | coordinator, direct fetch | verified (updated 2026-10-22) |
| D16 IndexNow participants | coordinator, direct fetch | verified |
| D17 GA4 default channel group | coordinator, direct fetch | verified |
| D18 Search Console API searchanalytics.query | researcher only | not re-checked |
| OpenAI publisher FAQ (UTM tagging) | coordinator, real browser | not verified: article 12627856 redirects to "ChatGPT Atlas retirement"; claim marked *(verify)* |
| Paper 1 GEO | researcher full text; coordinator not re-checked | figures from Tables 1, 2 and 7 as reported |
| Paper 2 C-SEO Bench | coordinator, full text sections 6.2, 6.3, 6.4, 7 | verified |
| Paper 3 Martinez survey | coordinator, abstract | verified |
| Paper 4 Bajemon and Rochet | coordinator, abstract | verified; whether the ten engine families were live is unclear |
| Paper 5 Tannenbaum | coordinator, abstract | verified |
| Paper 6 Grossman et al. | coordinator, abstract | verified |
| Paper 7 Zhang, He, Yao | researcher, abstract | not re-checked |
| Paper 8 Chen et al. | researcher, abstract | not re-checked; qualitative only |
| Paper 9 Fang et al. | coordinator, abstract | verified |
| Paper 10 Liu, Zhang, Liang | researcher, abstract | not re-checked |
| Paper 11 Nestaas et al. | researcher, full text to 100k of 114k characters | not re-checked; venue ICLR 2025 from snippets only |
| Paper 12 Kumar and Lakkaraju | researcher, abstract | not re-checked; no numbers on the read page |
| Paper 13 Khodayari et al. | coordinator, abstract | verified |
| claude-seo, geo-optimizer-skill | coordinator, GitHub API | license MIT, not archived; ideas read at commits `6be93f45064ffbadced572b5d5c95f55fd263af0` and `259b6293f57cbad7d01d4b9b0eadd0e62a486054`; `audit_cdn.py` read |
| Other tools | researcher, READMEs and GitHub API | not re-checked |

Not read by anyone: vendor pages for Bytespider, CCBot, Meta-ExternalAgent, Amazonbot,
MistralAI-User and DuckAssistBot; Microsoft's October 2025 guide on AI search inclusion;
Bing's AI Performance FAQ; Pfrommer et al. (arXiv 2406.03589), AgentGEO, AutoGEO, E-GEO
and Greshake et al. (arXiv 2302.12173).

## Research prompts

### Platform facts

```
Role: researcher
Objective: Current official guidance (as of 2026-10-28) from answer engines and infrastructure vendors on crawler access, inclusion/exclusion controls and measurement that would change an answer-engine-optimization (AEO/GEO) audit checklist. Focus on facts that would change recommendations in an existing knowledge base.
Already verified on primary pages, do NOT re-verify: Google AI optimization guide; Google AI features and your website; Search Console Generative AI performance report and Search generative AI control; OpenAI bots page; Perplexity bots page; Bing AI Performance public preview post.
Questions: 1. Anthropic crawlers today. 2. Bing/Microsoft: the 2026-06-16 story, AI Performance status, Microsoft AI search content guidance, IndexNow participants. 3. Cloudflare: default AI crawler blocking, AI Crawl Control, pay per crawl, Content Signals. 4. Google-Extended and AI Mode in 2026; new Google agents. 5. Other agents for a robots.txt audit. 6. Analytics attribution: referrers and UTM parameters.
Boundaries: official vendor documentation and vendor blogs first; third-party only when no primary source exists, marked as such. No SEO-agency listicles as evidence.
Source families: official/primary docs and changelogs, recency (vendor blogs, release notes 2025-2026)
Domain hint: generative engine optimization, AI crawlers, search console, webmaster tools
Backend: auto
Budget: 18 searches / 14 pages / 4 rounds
Return format: the researcher report, plus a final table "claim | source URL | date | verbatim quote | confidence".
```

### Papers

```
Role: researcher
Objective: Peer-reviewed papers and preprints (2023 to 2026-10) that measure what makes a web source more or less likely to be retrieved, cited or used by generative search / answer engines, plus research on adversarial manipulation and prompt injection of such engines. The output will decide which recommendations an AEO audit agent keeps, drops or marks as unproven.
Start from Aggarwal et al., GEO (KDD 2024, arXiv 2311.09735) and follow citations forward. Cover: 1. content-level interventions and replications on real engines; 2. source-selection studies; 3. structured data and llms.txt; 4. adversarial work and defenses; 5. any paper directly testing Google's 2026 AI optimization guide.
For each paper: full citation, venue and year, link, engines or simulators tested, method, headline effect size, limitations, and the audit recommendation it supports or refutes. Mark simulated-engine results separately from live-engine results.
Boundaries: academic and preprint sources only for findings; vendor statements only to frame a contrast. No marketing blogs as evidence.
Source families: academic (arXiv, ACL Anthology, ACM DL, Semantic Scholar), recency (2025-2026 preprints)
Domain hint: generative engine optimization, retrieval-augmented generation, LLM search citation, information retrieval
Backend: auto
Budget: 20 searches / 16 pages / 4 rounds
Return format: the researcher report, plus a final table "paper | venue/year | live or simulated | finding | effect size | supports/refutes which recommendation".
```

### Existing tools

```
Role: researcher
Objective: Find existing open-source agent skills, plugins and MCP servers for SEO, GEO, AEO and AI-search visibility, usable from Claude Code, Codex, Copilot, OpenCode or generic MCP clients, and report which capabilities they have that the local plugin lacks. The output feeds a delegation-or-inspiration decision: the repository never vendors external code.
Known local gaps: WAF/CDN bot-block detection, Search Console generative AI control, snippet controls, Bing AI Performance, IndexNow, Merchant Center, automated citation tracking.
Search GitHub, plugin marketplaces and directories, skill registries, the MCP registry, npm and PyPI. For each candidate: repo URL, owner, license, last commit, stars, install path per host, capabilities, quality evidence, paid APIs or keys, gaps covered. Include official measurement APIs and their cost.
Boundaries: facts read from the repositories themselves. Do not rank by stars alone. Exclude closed SaaS unless it offers a free official API relevant to measurement.
Source families: primary (GitHub repositories, registries, official API docs), recency (2025-2026)
Domain hint: Claude Code plugins, agent skills, MCP servers, SEO tooling, generative engine optimization
Backend: auto
Budget: 18 searches / 16 pages / 4 rounds
Return format: the researcher report, plus a final table "name | URL | license | last commit | stars | capabilities | covers which gap | delegation fit (yes/no/inspiration) with reason".
```

## Researcher reports

The three reports below are kept verbatim. Their source identifiers (S1, S2...) are
local to each report and differ from the D and paper numbers of the summary.

### Platform facts report

*Original title: ### Researcher report: Official AEO/GEO guidance as of 2026-10-28 on crawler access, inclusion and exclusion controls, and measurement*
Exit reason: budget-exhausted
Rounds: 4, searches: 5, pages read: 14 (2 more attempts returned nothing), backend: websearch (no `SERPER_API_KEY`)

Quotes come from the fetch tool's extractor, which was asked for verbatim text in spans of 125 characters or less. Paraphrases are marked.

#### Claims
1. Anthropic's current help article was published 2026-04-07. It names three bots: ClaudeBot (collects content that may be used for training), Claude-User (fetches pages when a user asks Claude something) and Claude-SearchBot (indexes pages for search quality). [S1]
2. All three Anthropic bots honor robots.txt and the non-standard `Crawl-delay`. That includes Claude-User, the user-initiated one. Google's user-triggered fetchers, ChatGPT-User and Perplexity-User differ here: they ignore robots.txt or may ignore it. [S1][S3]
3. Anthropic says that blocking Claude-User or Claude-SearchBot "may reduce your site's visibility" in Claude's search. Blocking ClaudeBot only signals that future content should be left out of training. [S1]
4. Anthropic publishes its bot IPs at `https://claude.com/crawling/bots.json`. It warns that blocking by IP may not reliably opt a site out. [S1]
5. The current Anthropic article does not mention `anthropic-ai` or `Claude-Web`. It does not say they were retired. They are simply missing. [S1]
6. The "2026-06-16 story" is on the Bing Search blog, not the Webmaster blog. It announces Intents, Topics, Citation Share and Compare, which are "beginning to roll out in preview" inside AI Performance. AI Performance covers "Microsoft Copilot, Bing, and select partner AI experiences". [S10][S4]
7. Bing defines Citation Share as your site's percentage of all citations for a grounding query. Bing calls it "an observational metric – not a ranking system". [S10]
8. On 2026-10-13 Bing added Topics Portfolio (Beta) to AI Performance. No Bing post I read says AI Performance is generally available, and neither the June nor the October post mentions an export or an API. [S6][S10]
9. Microsoft has a guidance document, "Optimizing Your Content for Inclusion in AI Search Answers". It is on the Microsoft Advertising blog under an `october-2025` URL path (https://about.ads.microsoft.com/en/blog/post/october-2025/optimizing-your-content-for-inclusion-in-ai-search-answers), and the AI Performance post links to it. I did not read its content. [S7]
10. The official IndexNow `searchengines.json` lists seven endpoints: bing, yandex, seznam, naver, yep, internetarchive and amazonbot. Google is not listed. [S11]
11. Cloudflare's "Block AI bots" setting is "Deprecating on September 15, 2026". It is replaced by Search, Agent and Training policies. For new domains from that date, Training and Agent bots are blocked on pages that show ads, and Search stays allowed (paraphrase). [S9]
12. Cloudflare's managed robots.txt (Bot Preference Sync) adds the Content Signals Policy only when at least one policy blocks. Its default line is `search=yes, ai-train=no, use=reference`. `use` is an extension Cloudflare is still testing. [S8]
13. The Content Signals Policy defines three signals: search, ai-input (RAG and grounding) and ai-train. It states: "Search does not include providing AI-generated search summaries." [S8]
14. Cloudflare's example managed block disallows Amazonbot, Applebot-Extended, Bytespider, CCBot, ClaudeBot, Google-Extended, GPTBot and meta-externalagent. This list is Cloudflare's classification, not the vendors'. [S8]
15. Cloudflare's docs make no claim that any AI company honors Content Signals. They say robots.txt compliance is voluntary. Google Search Console may report the line as "Syntax not understood", and Cloudflare says it has seen no effect on crawling or SEO from this (paraphrase). [S8]
16. Pay per crawl is still marked "(private beta)". AI Crawl Control is the product formerly called AI Audit. [S5]
17. Google-Extended (page updated 2026-10-15) is a control token with no HTTP user agent of its own. It does not affect inclusion or ranking in Search. It covers Gemini training and grounding in Gemini Apps and in Grounding with Google Search on Vertex AI (paraphrase). The page does not mention AI Mode or AI Overviews. [S2]
18. Google has a new user-triggered agent, Google-Agent, "used by agents hosted on Google infrastructure to navigate the web and perform actions upon user request". Its IPs are in `user-triggered-agents.json`. Google is also experimenting with Web Bot Auth under the identity `https://agent.bot.goog`. [S3]
19. Google's user-triggered fetchers "generally ignore robots.txt rules", which includes Google-Agent and Google-GeminiNotebook. `Google-GeminiNotebook` replaced `Google-NotebookLM`, which was supported until August 2026. [S3]
20. Apple's page (published 2026-09-04) says Applebot powers Spotlight, Siri and Safari and may train Apple's foundation models. Applebot-Extended does not crawl. Blocking it does not remove a site from search results. If robots.txt has no Applebot rule, Applebot follows the Googlebot rules. Applebot can be identified by reverse DNS under `*.applebot.apple.com`. [S12]
21. GA4's default channel group has an "AI Assistant" channel. It matches when the medium is exactly `ai-assistant`, or it is set automatically when the referrer is on a list of AI assistants (named examples: ChatGPT, Gemini, Deepseek, Copilot, Grok). Traffic from AI Overviews and AI Mode is excluded and counts as Organic Search. Google does not publish the referrer list. [S14]

#### Sources read
| id | title | site | date carried | URL | rank |
|---|---|---|---|---|---|
| S1 | Does Anthropic crawl data from the web, and how can site owners block the crawler? | support.claude.com | published 2026-04-07 | https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler | 1 |
| S2 | Google's common crawlers | developers.google.com | updated 2026-10-15 | https://developers.google.com/search/docs/crawling-indexing/google-common-crawlers | 1 |
| S3 | Google's user-triggered fetchers | developers.google.com | updated 2026-08-19 | https://developers.google.com/search/docs/crawling-indexing/google-user-triggered-fetchers | 1 |
| S4 | Bing Webmaster Blog feed | blogs.bing.com | items to 2026-10-13 | https://blogs.bing.com/webmaster/feed | 1 |
| S5 | AI Crawl Control | developers.cloudflare.com | updated 2026-08-14 | https://developers.cloudflare.com/ai-crawl-control/ | 1 |
| S6 | Introducing Topics Portfolio (Beta) in AI Performance | blogs.bing.com | 2026-10-13 | https://blogs.bing.com/webmaster/2026/10/introducing-topics-portfolio-beta-in-ai-performance/ | 1 |
| S7 | Introducing AI Performance in Bing Webmaster Tools Public Preview (links only) | blogs.bing.com | 2026-02-11 UTC | https://blogs.bing.com/webmaster/2026/2/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview/ | 1 |
| S8 | robots.txt setting (managed robots.txt) | developers.cloudflare.com | updated 2026-10-22 | https://developers.cloudflare.com/bots/additional-configurations/managed-robots-txt/ | 1 |
| S9 | Block AI bots | developers.cloudflare.com | updated 2026-07-01 | https://developers.cloudflare.com/bots/additional-configurations/block-ai-bots/ | 1 |
| S10 | New AI Visibility Insights in Bing Webmaster Tools: Intents, Topics, Citation Share, Compare | blogs.bing.com | 2026-06-16 | https://blogs.bing.com/search/2026/6/New-AI-Visibility-Insights-in-Bing-Webmaster-Tools-Intents-Topics-Citation-Share-Compare/ | 1 |
| S11 | IndexNow searchengines.json | indexnow.org | undated | https://www.indexnow.org/searchengines.json | 1 |
| S12 | About Applebot | support.apple.com | published 2026-09-04 | https://support.apple.com/en-us/119829 | 1 |
| S13 | ChatGPT Atlas retirement (returned by the fallback fetcher in place of the requested FAQ) | help.openai.com | "Updated: 6 days ago" | requested https://help.openai.com/en/articles/12627856-publishers-and-developers-faq | 1 (URL mismatch) |
| S14 | [GA4] Default channel group | support.google.com | undated | https://support.google.com/analytics/answer/9756891 | 1 |

#### Contradictions seen
- robots.txt for user-initiated agents: Anthropic says all its bots, Claude-User included, honor robots.txt [S1]. Google says its user-triggered fetchers, Google-Agent included, "generally ignore robots.txt rules" [S3]. Both are current vendor policy. They don't contradict each other, but an audit needs a separate row per vendor and cannot use one rule for all user agents.
- Cloudflare new-domain defaults: from 2026-09-15, new domains block Training and Agent bots only on pages with ads [S9]. Cloudflare's July 2025 "block by default" announcement was not read in this run, so whether one replaced the other is unresolved.
- Amazonbot: Cloudflare's managed block lists Amazonbot as an AI crawler to disallow [S8], but Amazonbot is also an IndexNow participant [S11]. My inference: a blanket AI blocklist may cut off an Amazon discovery channel. Amazon's own docs were not read.

#### Open threads
- OpenAI's publisher FAQ returned 403. The fallback fetcher then returned the "ChatGPT Atlas retirement" article [S13], so the FAQ was not read. A search hit's text fragment carries the sentence "ChatGPT automatically includes the UTM parameter utm_source=chatgpt.com in referral URLs, enabling clear tracking and analysis of inbound traffic from ChatGPT search results". This is a snippet, not verified, and needs a browser read.
- ChatGPT Atlas: S13 says "ChatGPT Atlas has been retired and no longer receives updates". Because the URL didn't match the request, confirm this before removing any Atlas-related audit item.
- Third-party only, no primary page read (from a search summary): GA4 added the AI Assistant channel on 2026-05-13; Gemini adds UTM link tags; Microsoft Clarity added "AI Platform" channels on 2025-08-29.
- Not read because of budget: the content of Microsoft's October 2025 guide "Optimizing Your Content for Inclusion in AI Search Answers"; Bing's AI Performance FAQ (https://www.bing.com/webmasters/help/ai-performance-9f8e7d6c); Bing's "Elevating the Role of Grounding on the AI Web" (February 2026, https://blogs.bing.com/search/February-2026/Elevating-the-Role-of-Grounding-on-the-AI-Web); Cloudflare's July 2025 default-block post; vendor pages for Meta-ExternalAgent, MistralAI-User, DuckAssistBot, Amazonbot, CCBot and Bytespider.
- Referrer and UTM behavior for Perplexity, Copilot, Gemini and Claude: no official vendor documentation found.

#### Searched and not found
- contentsignals.org: the page needs JavaScript and came back empty, so it cannot answer whether any engine honors the signals.
- help.openai.com publisher FAQ: 403, and the fallback returned a different article.
- Bing Webmaster feed: has no June 2026 item. The 06-16 story is on /search/.
- Search for IndexNow participants: only secondary sources, so the official JSON was used instead.
- Search for official referrer docs from Perplexity, Copilot, Gemini or Claude: third-party pages only.

#### Claim table
| claim | source URL | date | verbatim quote | confidence |
|---|---|---|---|---|
| Anthropic bots honor robots.txt | https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler | 2026-04-07 | "Anthropic's Bots respect "do not crawl" signals by honoring industry standard directives in robots.txt." | high |
| Claude-User block reduces visibility | same | 2026-04-07 | "Disabling Claude-User on your site prevents our system from retrieving your content in response to a user query" | high |
| Claude-SearchBot purpose | same | 2026-04-07 | "Claude-SearchBot navigates the web to improve search result quality for users." | high |
| ClaudeBot = training opt-out | same | 2026-04-07 | "When a site restricts ClaudeBot access, it signals that the site's future materials should be excluded" | high |
| Anthropic IP list | same | 2026-04-07 | "If a crawler has a source IP address on this list, it indicates that the crawler is coming from Anthropic." (claude.com/crawling/bots.json) | high |
| Bing AI insights still preview | https://blogs.bing.com/search/2026/6/New-AI-Visibility-Insights-in-Bing-Webmaster-Tools-Intents-Topics-Citation-Share-Compare/ | 2026-06-16 | "Intents, Topics, Citation Share, and Compare are now beginning to roll out in preview within Bing Webmaster Tools" | high |
| Citation Share is not a ranking | same | 2026-06-16 | "designed as an observational metric – not a ranking system or a competitive scoreboard." | high |
| AI Performance coverage | same | 2026-06-16 | "across Microsoft Copilot, Bing, and select partner AI experiences." | high |
| Topics Portfolio beta | https://blogs.bing.com/webmaster/2026/10/introducing-topics-portfolio-beta-in-ai-performance/ | 2026-10-13 | "New beta feature in Bing Webmaster Tools that shows the thematic shape of your site's presence in AI Search." | high |
| Microsoft AI-answer content guide exists | https://blogs.bing.com/webmaster/2026/2/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview/ | 2026-02-11 | "For deeper guidance on structuring content to improve inclusion in AI-generated answers, see" | high (existence only) |
| IndexNow participants | https://www.indexnow.org/searchengines.json | undated | bing, yandex, seznam, naver, yep, internetarchive, amazonbot | high |
| Cloudflare Block AI bots deprecated | https://developers.cloudflare.com/bots/additional-configurations/block-ai-bots/ | 2026-07-01 | "Deprecating on September 15, 2026." | high |
| Cloudflare new-domain defaults | same | 2026-07-01 | paraphrase: Training and Agent blocked on pages with ads, Search allowed, from 2026-09-15 | medium |
| Content Signals: search excludes AI summaries | https://developers.cloudflare.com/bots/additional-configurations/managed-robots-txt/ | 2026-10-22 | "Search does not include providing AI-generated search summaries." | high |
| Cloudflare default signal line | same | 2026-10-22 | `Content-signal: search=yes, ai-train=no, use=reference` | high |
| No vendor commitment to honor signals | same | 2026-10-22 | none; the page states no such commitment (absence) | medium |
| Pay per crawl private beta | https://developers.cloudflare.com/ai-crawl-control/ | 2026-08-14 | "Set up pay per crawl pricing for content access" "(private beta)" | high |
| Google-Extended no Search effect | https://developers.google.com/search/docs/crawling-indexing/google-common-crawlers | 2026-10-15 | "Google-Extended does not impact a site's inclusion in Google Search nor is it used as a ranking signal in Google Search." | high |
| Google-Agent | https://developers.google.com/search/docs/crawling-indexing/google-user-triggered-fetchers | 2026-08-19 | "Google-Agent is used by agents hosted on Google infrastructure to navigate the web and perform actions upon user request." | high |
| User-triggered fetchers ignore robots.txt | same | 2026-08-19 | "Because the fetch was requested by a user, these fetchers generally ignore robots.txt rules." | high |
| Applebot-Extended doesn't crawl | https://support.apple.com/en-us/119829 | 2026-09-04 | "Applebot-Extended does not crawl webpages." | high |
| Applebot-Extended keeps Search | same | 2026-09-04 | "Webpages that disallow Applebot-Extended can still be included in search results." | high |
| Applebot follows Googlebot rules | same | 2026-09-04 | "If robots instructions don't mention Applebot but mention Googlebot, the Apple robot will follow Googlebot instructions." | high |
| GA4 AI Assistant channel | https://support.google.com/analytics/answer/9756891 | undated | "AI Assistant is the channel by which users arrive at your site from sources like ChatGPT, Gemini, Deepseek, Copilot, or Grok." | high |
| GA4 AI Overviews and AI Mode count as Organic Search | same | undated | "non-ad links in organic-search results, including Google's AI Overviews and AI Mode." | high |
| ChatGPT adds utm_source=chatgpt.com | https://help.openai.com/en/articles/12627856-publishers-and-developers-faq | not read | snippet only (text fragment above) | low |

Scratch file with the fallback fetcher's output (the Atlas article): D:/Projects/horness-launcher/sidecar/runs/musashi-terminal-11284-80225437-0-134376675883600054-0/tmp/claude/D--Projects-daodan/5357048a-c933-4826-9960-d787757f0a2a/scratchpad/openai_faq.txt

### Papers report

*Original title: ### Researcher report: academic evidence on what makes a web source retrieved, cited or used by generative engines, and on adversarial manipulation of those engines (2023 to 2026-10)*
Exit reason: budget-exhausted (16 of 16 pages read, 4 of 4 rounds used)
Rounds: 4, searches: 13, pages read: 16, backend: websearch (serper not used: `websearch.py --check-key` exited 2, so no key is available)

Note on ranks: every source is the paper itself. Rank 1 means a primary paper whose read page names a peer-reviewed venue. Rank 2 means a primary preprint with no venue on the read page. All sources are hosted on arXiv. Sources count as independent when their author groups differ.

#### Claims

**Content-level interventions**
1. The original GEO experiments ran on a simulated engine. It took the top 5 Google results, generated answers with gpt-3.5-turbo (5 samples at temperature 0.7) and scored them on GEO-bench (10K queries from 9 datasets). The abstract's headline is "up to 40%" more visibility. [S1][S2]
2. GEO Table 1, measured by Position-Adjusted Word Count (PAWC, baseline 19.3): Quotation Addition 27.2, Statistics Addition 25.2, Fluency 24.7, Cite Sources 24.6, Technical Terms 22.7, Easy-to-Understand 22.0, Authoritative 21.3, Unique Words 20.5, Keyword Stuffing 17.7. Computed from the table, that is +41%, +31%, +28%, +27.5%, +18%, +14%, +10%, +6% and -8%. Subjective Impression (baseline 19.3): Quotation 24.7 (+28%), Statistics 23.7 (+23%), Authoritative 22.9 (+19%), Fluency and Cite Sources 21.9 (+13.5%), Keyword Stuffing 20.2 (+5%). [S2]
3. GEO's own text says Cite Sources, Quotation and Statistics gain 30 to 40% PAWC and 15 to 30% Subjective. Table 1 gives Cite Sources about +27.5% PAWC and +13.5% Subjective. Section 6 says Cite Sources improves Perplexity PAWC by up to 9%; Table 7 gives roughly +11%. [S2]
4. GEO gains go mostly to low-ranked sources. Rank-5 sources gained +97.9% to +115.1% under Statistics, Quotation and Cite Sources. Rank-1 sources lost 20.6% to 30.3% under the same methods (Table 2). [S2]
5. GEO's best pair was Fluency Optimization + Statistics Addition, beating any single method by more than 5.5% on a 200-example subset. Method effectiveness varies by domain (Statistics best on Law & Gov., Debate, Opinion; Quotation on People & Society, Explanation, History). [S1][S2]
6. GEO's Perplexity.ai test used 200 samples with the sources uploaded as files, because Perplexity does not accept source URLs. Against a baseline of PAWC 24.1 and Subjective 24.7: Quotation gave PAWC 29.1 (paper says +22%) and Subjective 32.1, Statistics gave PAWC 26.2 and Subjective 33.9 (about +37%), and Keyword Stuffing gave PAWC 21.9 (about -9%). [S2]
7. GEO's stated limitations: only two engines were tested, search ranking was not evaluated, longer context windows may weaken the effect of search rank, queries drift so GEO-bench needs updates, and GPT-4-generated tags may be noisy. [S2]
8. C-SEO Bench (NeurIPS Datasets & Benchmarks 2025) tested 8 of the GEO transformations plus two new methods ("Content Improvement", which combines all eight, and "LLM Guidance", an llms.txt-inspired markdown summary added to the start of the document) across 6 domains, 16k+ documents and 1.9k+ queries on gpt-4o-mini, claude-3.5-haiku, o3 and o4-mini, all with a fixed retrieved context. Most methods averaged near-zero rank gain (about ±0.2 positions, standard deviation 1 to 1.7). [S6][S7]
9. In C-SEO Bench, Statistics lowered rankings in 19 of 24 settings (Debate on gpt-4o-mini: -0.80 ±1.70). On Haiku product recommendation, 26 of 30 cases were significantly negative; on o4-mini question answering, 19 of 30. Only Content Improvement (retail) and LLM Guidance (retail and games, gpt-4o-mini only) gained significantly; there were no significant gains on Haiku or in question answering. [S7]
10. Moving a document to position 1 of the LLM context was significant in all six domains (p < 0.0001), with gains of +0.70 to +2.77 rank positions (Retail 2.77, Games 1.89, Books 1.60, Debate 1.54, Web 0.87, News 0.70 on gpt-4o-mini). Positions 8 to 10 degraded rank (Debate, position 10: -2.18). Best SEO was also significant in every domain on o3 and o4-mini. The authors conclude that traditional SEO beats C-SEO. [S6][S7]
11. C-SEO gains shrink toward zero as more competitors adopt the same method, which the authors describe as "congested and zero-sum". They attribute the disagreement with GEO to GEO's word-count metric, which does not measure citation rank. Stated limitations: white-hat methods only, proprietary models only, English only, documents assumed to fit the context, and the interplay with traditional SEO not examined. [S6][S7]
12. A 2026 re-measurement of the published 2023 causal anchors on ten modern engine families found the levers "move citation on none", so the 2023 anchors are "an expired external check". An engine-free content score reached a within-query Spearman of only 0.11 against citation, and amplifying its levers gained an attacker at most 6 points. [S5]
13. A survey of 45 GEO studies (Nov 2023 to Jul 2026) makes four points: the foundational gains depend on the source already being in a fixed context and show neither organic discoverability nor durable traffic effects; topical relevance and context position are the most reproducible levers; generic heuristics transfer poorly and competition erodes gains; and citation-oriented rewrites can impair retrieval. Commercial audits show low source overlap, substantial run-to-run variability and persistent fidelity gaps. It finds no technique with a stable, longitudinal, cross-platform causal effect on organic discoverability or downstream behaviour. [S3]

**Source selection, overlap, freshness, accuracy**
14. On 11,500 real-user queries (SIGIR 2026), AI Overviews appeared on 51.5% of queries, often on controversial questions. Sources retrieved by Google Search, AI Overviews and Gemini Flash 2.5 had average Jaccard similarity below 0.2. AI Overviews were less consistent across two runs of the same query and less robust to small query edits. [S11]
15. Sites that block Google's AI crawler were significantly less likely to be retrieved by AI Overviews, even though they could still be accessed. Generative engines were more likely to retrieve Google-owned content, while classic Search favoured popular, institutional, government and education domains. [S11]
16. On 15 prompts run on 6 June 2026 across ChatGPT, Copilot, Google and Perplexity (589 citation observations, 528 unique URLs, 356 domains), the mean pairwise same-prompt URL Jaccard was 0.0079 (5.7% of a hypergeometric baseline of 0.1272). 84.9% of engine pairs shared no cited URL, 96.4% of URLs appeared on only one engine, top-five overlap was zero in all 60 engine pairs, a single engine captured 11.4% to 42.6% of the four-engine union, and the same engine's URL set turned over by 67.0% between 5 and 6 June. [S16]
17. The cross-engine study says engine-free page scores estimate "page quality or query-page fit", not visibility. It recommends reporting page fit, observed exposure, conditional selection and final visibility as separate quantities. [S16]
18. Of the three source-selection results (claims 14, 16 and 18), this is the one most likely to rest on weak data. Across 602 controlled prompts on ChatGPT, Google AI Overviews/Gemini and Perplexity (21,143 citations, 23,745 citation-level feature records, 18,151 fetched pages, 72 features), Perplexity and Google cited more sources, while ChatGPT cited fewer but each had higher influence. High-influence pages were longer, more structured, semantically aligned and rich in definitions, numbers, comparisons and procedural steps. The authors call this finding descriptive and recommend measuring answer-level absorption separately from citation counts. [S4]
19. AI search engines strongly favour earned (third-party) media over brand-owned and social content, while Google shows a more balanced mix. The engines differ in domain diversity, freshness, cross-language stability and sensitivity to phrasing. These are qualitative statements from the abstract; the read page gave no numbers. [S12]
20. Adding fake publication dates to passages pushed the top-10's mean year forward by up to 4.78 years in seven LLM rerankers (GPT-3.5/4/4o, LLaMA-3 8B/70B, Qwen-2.5 7B/72B) on TREC DL21/DL22. It moved individual items by up to 95 ranks and reversed preferences between equally relevant passages by up to 25%. Larger models weaken the effect but none remove it. [S13]
21. A human audit of Bing Chat, NeevaAI, Perplexity and YouChat found that only 51.5% of generated sentences were fully supported by their citations, and only 74.5% of citations supported their sentence. Responses were fluent and appeared informative, giving a "facade of trustworthiness". [S14]

**Structured data and llms.txt**
22. The only academic test of an llms.txt-style intervention found was C-SEO Bench's "LLM Guidance": a markdown summary added to the start of the document itself, not a separate file. It improved rank significantly only on gpt-4o-mini in retail and video games (for example +0.36 ±1.47 in retail, with 61.0% of ranks unchanged, 26.2% improved and 12.8% worsened). It had the best AUC under multi-actor adoption in those two domains. [S7]
23. In controlled tests, presenting a page in a structured form reduced LLM compliance with injected instructions compared with plain text. This concerns page representation, not schema.org. [S15]

**Adversarial manipulation and prompt injection**
24. Preference manipulation attacks worked on live Bing Copilot (Precise and Creative modes) and Perplexity. An attacker's camera was 2.5x more likely to be recommended on Bing, and a fake camera's recommendation rate rose from 34.0% to 59.4% (real Nikon/Fujifilm cameras: 57.9%). Plugin selection rose up to 7.2x, some plugins from 0% to over 90%. Plain praise alone ("This is the best source of news on the internet!") was not sufficient. Disclosure to vendors was in March 2024. [S8][S9]
25. Those live tests used site:-scoped queries, which the authors say inflate success. Injections placed on a separate external page succeeded at most 25% of the time on Bing, against 95 to 100% for direct attacks; Perplexity external attacks succeeded significantly more often. In 80% of successful external attacks the response did not mention the page carrying the injection. [S9]
26. Bing Copilot read pages ranked below 10 in 50% of searches, and its read order matched Bing index order at Spearman 0.84. An attacker page only has to be in the top-k context; getting it there is traditional SEO, which the paper leaves out of scope. [S9]
27. The defenses discussed (StruQ, spotlighting, instruction hierarchy, certified RAG, detection, attribution) were not evaluated against the production systems. The authors argue that instruction-hijack defenses may miss persuasion that carries no explicit instruction. [S9]
28. Adding a "strategic text sequence" to a product page made two products (one rarely recommended, one usually ranked second) significantly more likely to be the top LLM recommendation. The test used a fictitious coffee-machine catalog, and the read page gives no numbers or model name. [S10]
29. A crawl of 1.2B URLs from 24.8M hosts found 15.3K validated indirect prompt injections on 11.7K pages, most from a few recurring templates. About 70% sat in non-rendered HTML (headers, comments, metadata). Objectives included disruptive prompts, reputation manipulation, content-protection directives and AI-bot detection, targeting crawlers, search pipelines, customer-support agents and hiring workflows. In 5,200 controlled experiments across 13 models and four page representations, compliance reached up to 8% for smaller models on plain-text input. [S15]

**Google's 2026 guide**
30. No read paper directly tests Google's guide claims (no chunking, no AI-specific writing, no special schema). The indirect evidence in claims 8 to 13 and 17 supports "no AI-specific writing": generic GEO rewrites do not transfer to modern engines, while retrieval and context position do. [S3][S5][S7]

#### Sources read
| id | title | site | date carried | URL | rank |
|---|---|---|---|---|---|
| S1 | GEO: Generative Engine Optimization (abs), Aggarwal, Murahari, Rajpurohit, Kalyan, Narasimhan, Deshpande; "Accepted to KDD 2024"; DOI 10.48550/arXiv.2311.09735 | arxiv.org | v1 16 Nov 2023, v3 28 Jun 2024 | https://arxiv.org/abs/2311.09735 | 1 |
| S2 | GEO: Generative Engine Optimization (full text v3, same paper as S1) | arxiv.org | v3 28 Jun 2024 | https://arxiv.org/html/2311.09735v3 | 1 |
| S3 | Optimizing Visibility in Generative Engines: A Critical Survey of Generative Engine Optimization (2023-2026), Olivier Martinez; arXiv 2607.14035 [cs.IR] | arxiv.org | 15 Jul 2026 | https://arxiv.org/abs/2607.14035 | 2 |
| S4 | From Citation Selection to Citation Absorption: A Measurement Framework for GEO Across AI Search Platforms, Zhang Kai, He Xinyue, Yao Jingang; arXiv 2604.25707; data github.com/yaojingang/geo-citation-lab | arxiv.org | v1 28 Apr 2026, v2 29 Apr 2026 | https://arxiv.org/abs/2604.25707 | 2 |
| S5 | Scoring Without the Engine: Validating a Deterministic, Manipulation-Resistant Content Score for Generative Engines, End to End, Elisha Bajemon, Andre-Louis Rochet; arXiv 2609.07559 [cs.AI] | arxiv.org | 7 Sep 2026 | https://arxiv.org/abs/2609.07559 | 2 |
| S6 | C-SEO Bench: Does Conversational SEO Work? (abs), Haritz Puerto, Martin Gubri, Tommaso Green, Seong Joon Oh, Sangdoo Yun; "Accepted at NeurIPS Datasets & Benchmarks 2025"; DOI 10.48550/arXiv.2506.11097; code github.com/parameterlab/c-seo-bench | arxiv.org | v1 6 Jun 2025, v3 20 Oct 2025 | https://arxiv.org/abs/2506.11097 | 1 |
| S7 | C-SEO Bench (full text v3, same paper as S6) | arxiv.org | v3 20 Oct 2025 | https://arxiv.org/html/2506.11097v3 | 1 |
| S8 | Adversarial Search Engine Optimization for Large Language Models (abs), Fredrik Nestaas, Edoardo Debenedetti, Florian Tramèr; arXiv 2406.18382 [cs.CR] | arxiv.org | v1 26 Jun 2024, v2 2 Jul 2024 | https://arxiv.org/abs/2406.18382 | 2 |
| S9 | Same paper as S8, full text v2 (read through 100k of 114k characters) | arxiv.org | 2 Jul 2024 | https://arxiv.org/html/2406.18382v2 | 2 |
| S10 | Manipulating Large Language Models to Increase Product Visibility, Aounon Kumar, Himabindu Lakkaraju; arXiv 2404.07981; code github.com/aounon/llm-rank-optimizer | arxiv.org | v1 11 Apr 2024, v2 2 Sep 2024 | https://arxiv.org/abs/2404.07981 | 2 |
| S11 | How Generative AI Disrupts Search: An Empirical Study of Google Search, Gemini, and AI Overviews, Riley Grossman, Songjiang Liu, Michael K. Chen, Mike Smith, Cristian Borcea, Yi Chen; accepted to ACM SIGIR 2026; arXiv 2604.27790 | arxiv.org | 30 Apr 2026 | https://arxiv.org/abs/2604.27790 | 1 |
| S12 | Generative Engine Optimization: How to Dominate AI Search, Mahe Chen, Xiaoxuan Wang, Kaiwen Chen, Nick Koudas; arXiv 2509.08919 [cs.IR] | arxiv.org | 10 Sep 2025 | https://arxiv.org/abs/2509.08919 | 2 |
| S13 | Do Large Language Models Favor Recent Content? A Study on Recency Bias in LLM-Based Reranking, Hanpei Fang, Sijie Tao, Nuo Chen, Kai-Xin Chang, Tetsuya Sakai; arXiv 2509.11353 [cs.IR] | arxiv.org | v1 14 Sep 2025, v2 21 Sep 2026 | https://arxiv.org/abs/2509.11353 | 2 |
| S14 | Evaluating Verifiability in Generative Search Engines, Nelson F. Liu, Tianyi Zhang, Percy Liang; Findings of EMNLP 2023; arXiv 2304.09848 | arxiv.org | v1 19 Apr 2023, v2 23 Oct 2023 | https://arxiv.org/abs/2304.09848 | 1 |
| S15 | Indirect Prompt Injection in the Wild: An Empirical Study of Prevalence, Techniques, and Objectives, Soheil Khodayari, Xuenan Zhang, Bhupendra Acharya, Giancarlo Pellegrino; arXiv 2604.27202 [cs.CR] | arxiv.org | 29 Apr 2026 | https://arxiv.org/abs/2604.27202 | 2 |
| S16 | Scoring With the Engine: Retrieval Exposure, Cross-Engine Divergence, and the Limits of Engine-Agnostic GEO Scores, Benjamin Tannenbaum; arXiv 2609.22655 [cs.IR] | arxiv.org | 19 Sep 2026 | https://arxiv.org/abs/2609.22655 | 2 |

#### Contradictions seen
- **Statistics and quotations.** GEO reports +31% to +41% PAWC on GPT-3.5 and +22% to +37% on Perplexity [S2]. C-SEO Bench finds Statistics lowered rank in 19 of 24 settings and most methods near zero [S7]. Ten modern engine families moved on none of the levers [S5]. The later studies win: one is peer-reviewed, they test newer models, and they measure citation rank rather than word count. C-SEO says this metric difference explains the disagreement [S7].
- **GEO's own figures.** The prose claims 30 to 40% for Cite Sources; Table 1 gives about 27.5% [S2]. Cite the tables, not the prose.
- **Crawler blocking.** Google says Google-Extended does not affect Search, yet blocking Google's AI crawler lowered AI Overview retrieval [S11]. That vendor statement was not read here; the read abstract does not name the crawler token. Unresolved.

#### Open threads
- Pfrommer et al., "Ranking Manipulation for Conversational Search Engines" (arXiv 2406.03589, EMNLP 2024): not read, out of page budget.
- AgentGEO (arXiv 2603.09296; the snippet claims >40% relative citation-rate gain), AutoGEO (2510.11438) and E-GEO (2511.20867): only seen in snippets, not read.
- Greshake et al., indirect prompt injection (arXiv 2302.12173): not read.
- Number of claims in S9 Appendix C past character 100k: not read.
- Nestaas et al. venue: ICLR 2025 according to iclr.cc and mlanthology snippets only. The read pages name no venue.
- Full-text numbers for S12: a snippet gives 72.7% earned vs Google's 45.4% for US software queries. The method is unread.
- Full texts of S3, S4, S11 and S16, for limitations, feature models and crawler identity.
- Which models S5 used: a snippet says gpt-5.5, gpt-5.4 and gpt-5.4-mini, but the read page says only "ten modern engine families". Whether those tests were live is unclear.
- Chunking paper arXiv 2601.14123 (RAG chunking for engineers, not authors): snippet only.

#### Searched and not found
- An academic experiment testing whether schema.org or JSON-LD changes LLM citation or extraction. One query returned only vendor blogs; the Ahrefs difference-in-differences study is vendor work and outside this report's boundary.
- An arXiv or peer-reviewed measurement of llms.txt adoption or crawler use. Only industry trackers and a Common Crawl blog turned up, all non-academic.
- Any paper that directly tests the claims in Google's 2026 AI optimization guide.
- A measurement of indirect prompt injection aimed specifically at live AI search products (S15 covers the web in general).
- Not run: a direct search for Puerto et al. beyond C-SEO Bench, and Semantic Scholar "cited by" traversal (the budget went to reading).

#### Final table
| paper | venue/year | live or simulated | finding | effect size | supports/refutes which recommendation |
|---|---|---|---|---|---|
| Aggarwal et al., GEO [S1][S2] | KDD 2024 | simulated (GPT-3.5 over Google top-5) plus Perplexity with uploaded sources | Quotations, statistics, citations and fluency raise share of the answer; keyword stuffing lowers it | Quotation +41% PAWC, Statistics +31%, Keyword Stuffing -8%; rank-5 sources about +100%, rank-1 -20 to -30% | Supports "add statistics, quotes, citations" only in a fixed-context, 2023-model setting; refutes keyword stuffing |
| Puerto et al., C-SEO Bench [S6][S7] | NeurIPS D&B 2025 | simulated (4 API models, fixed context) | GEO rewrites are mostly ineffective or harmful; context position dominates; gains erode as competitors adopt | ±0.2 ranks typical; Statistics negative in 19 of 24; position 1 +0.70 to +2.77, all p < 0.0001 | Refutes GEO content rewrites as a visibility lever; supports "get retrieved and rank high" (classic SEO) |
| Bajemon & Rochet [S5] | preprint 2026 | ten engine families, live status unclear | 2023 levers move citation on no modern engine | Within-query Spearman 0.11; attacker gain <=6 points | Refutes "statistics/quotes/citations raise citation"; refutes trusting an engine-free score as a visibility measure |
| Martinez survey [S3] | preprint 2026 | survey of 45 studies | Only topical relevance and context position reproduce; rewrites can hurt retrieval; no stable cross-platform effect | qualitative | Mark every content heuristic "unproven"; keep relevance and retrieval |
| Grossman et al. [S11] | SIGIR 2026 | live (Google Search, AI Overviews, Gemini 2.5 Flash) | AI Overviews on 51.5% of queries; low source overlap; blocking Google's AI crawler lowers AI Overview retrieval | Jaccard < 0.2 | Supports "do not block AI crawlers if AI Overview visibility is wanted"; refutes "organic rank alone predicts AI citation" |
| Tannenbaum [S16] | preprint 2026 | live (ChatGPT, Copilot, Google, Perplexity) | Engines almost never cite the same URLs; one-day turnover 67% | Jaccard 0.0079; 96.4% of URLs on one engine only | Supports per-engine, repeated measurement and the four separate measures; refutes cross-engine generalization |
| Zhang, He, Yao [S4] | preprint 2026 | live (ChatGPT, AI Overviews/Gemini, Perplexity), observational | Pages whose content is absorbed are longer, more structured and rich in definitions, numbers and steps | descriptive, no causal estimate | Weakly supports extractable facts and structure (correlational only); supports measuring absorption apart from citation |
| Chen et al. [S12] | preprint 2025 | live AI search vs Google | AI search strongly favours earned third-party media over brand-owned and social | qualitative on the read page | Supports off-site and earned-media recommendations (preprint; method unread) |
| Fang et al. [S13] | preprint 2025/2026 | simulated (7 LLM rerankers, TREC DL) | Fake fresh dates promote passages | up to 4.78 years; up to 25% preference reversal | Supports accurate visible dates; flags date-faking as a manipulation risk; untested on live engines |
| Liu, Zhang, Liang [S14] | Findings EMNLP 2023 | live (Bing Chat, NeevaAI, Perplexity, YouChat) | Citations are often unsupported or inaccurate | 51.5% recall, 74.5% precision | Supports auditing how a brand is represented (fidelity), not only citation counts |
| Nestaas et al. [S8][S9] | preprint 2024 (ICLR 2025 per snippet only) | live (Bing Copilot, Perplexity), site:-scoped | Hidden instructions and persuasive text steer recommendations | 2.5x on Bing; 34.0% to 59.4%; plugins up to 7.2x | Supports flagging hidden text and injections as manipulation; refutes "defenses already neutralize it" |
| Kumar & Lakkaraju [S10] | preprint 2024 | simulated (fictitious catalog) | Strategic text sequences raise top-recommendation odds | significant (no numbers on read page) | Supports treating optimized adversarial strings as manipulation, not optimization |
| Khodayari et al. [S15] | preprint 2026 | live web crawl plus controlled model tests | Injections exist in the wild, mostly in non-rendered HTML | 15.3K instances on 11.7K pages; ~70% non-rendered; up to 8% compliance | Supports an audit check for instructions in HTML comments and meta; refutes any "address the AI directly" advice |
| (none found) | n/a | n/a | schema.org/JSON-LD and llms.txt effect on citation | none | Mark schema-for-AI and llms.txt as "unproven". The C-SEO in-document "LLM Guidance" summary is the only test, significant in 2 of 6 domains on one model [S7] |

### Existing tools report

*Original title: ### Researcher report: existing open-source SEO/GEO/AEO agent skills, plugins, MCP servers and measurement APIs vs local gaps*
Exit reason: budget-exhausted (pages over cap: GitHub file reads through `gh api` counted as pages)
Rounds: 3, searches: 17 (5 web, 6 GitHub repo search, 6 official MCP registry queries), pages read: 23, backend: websearch (no SERPER_API_KEY) + GitHub REST API via gh

#### Claims
1. claude-seo (AgriciDaniel) is MIT, 23,068 stars, last push 2026-10-22, 26 sub-skills + 19 agents, Claude Code plugin (`/plugin marketplace add AgriciDaniel/claude-seo`, `/plugin install claude-seo@agricidaniel-claude-seo`, `/seo setup`), needs Python 3.11-3.14, works with no API key, badge claims 1,077 passing tests with a CI workflow; a private paid "Pro" version exists for a Skool community [S1][S14].
2. claude-seo's `seo-agentic` skill tests WAF behaviour by adding `--ua-matrix` to `agentic_check.py` "only when the user controls the site or confirms they are authorized", and treats the result as behaviour toward unverified traffic, never proof the real agent is blocked; its access-policy reference covers robots groups per AI agent, Cloudflare Content-Signal (launched 2025-09-24), Web Bot Auth and WAF vendors; it also scores Lighthouse "Agentic Browsing" via PSI v5 as X/N, llms.txt, Markdown delivery, ai-catalog.json, WebMCP [S2].
3. claude-seo's `seo-geo` skill states that since 2026-08-31 Search Console has a "Search generative AI" control (include, exclude, inherit) governing AI Overviews, AI Mode and Discover generative features, separate from Google-Extended, and lists nosnippet, data-nosnippet, max-snippet, noindex as appearance controls [S3].
4. claude-seo's Bing extension needs `BING_WEBMASTER_API_KEY` (optional `INDEXNOW_KEY`) and exposes `links`, `compare`, `submit`, `submit-batch`, `verify-indexnow`; it has no AI Performance / Copilot-citation report command [S4].
5. claude-seo does automated citation tracking only through paid extensions (SE Ranking share of voice, Profound citation time series, DataForSEO incl. `dataforseo_merchant.py`); its own monitoring is SEO drift via SQLite snapshots; README documents only a Claude Code install path [S1][S14].
6. geo-optimizer-skill (Auriti-Labs) is MIT, 1,207 stars, last push 2026-10-27, PyPI `geo-optimizer-skill`, runs with `uvx --from geo-optimizer-skill geo audit --url`, claims 16 CLI commands, 9 scoring categories, 27 AI crawlers, 47 content checks, 12 MCP tools, SARIF/JUnit output, a GitHub Action with `min-score`, and 2,000+ tests (107 test files in tree); it is the open-core engine of GeoReady (Pro from $19/mo) [S5][S14].
7. geo-optimizer's `audit_cdn_ai_crawler` requests the site with GPTBot, OAI-SearchBot, PerplexityBot, Claude-SearchBot, Googlebot and Applebot user-agents, compares status and size against a browser UA, matches challenge markers ("cf-browser-verification", "just a moment", "ray id", "captcha"...) and maps CDN headers (cf-ray, x-amz-cf-id, x-akamai-transformed, x-vercel-id) [S6].
8. geo-optimizer's "Google AI readiness" category scores snippets and the "manual generative-AI control" [S5].
9. geo-optimizer `geo citations` sends buyer questions to answer engines with the user's own keys (Perplexity, OpenAI, Anthropic, Groq, Gemini, MiniMax, DeepSeek, SerpBase for the real Google SERP + AI Overview), samples with `--runs 5` for a confidence interval, and states only Perplexity Sonar returns real source URLs while OpenAI/Anthropic/Groq reflect model knowledge [S5].
10. geo-optimizer MCP install: `pip install "geo-optimizer-skill[mcp]"` then `claude mcp add geo-optimizer -- geo-mcp`, documented for Claude, Cursor, Windsurf or any MCP client [S5].
11. Elmo (elmohq) is MIT, 517 stars, last push 2026-10-27, 148 open issues; self-hosted via Docker Compose + PostgreSQL; runs tracked prompts on a schedule against ChatGPT, Google AI Mode, AI Overviews, Gemini, Perplexity and Microsoft Copilot through scraping providers plus direct model APIs; stores cited URLs, query fan-out and model version; exposes REST API, TS/Python SDKs and an MCP server for Claude Code, Cursor, Codex, VS Code [S7][S14].
12. Elmo requires keys for at least one provider or scraper plus a TypeSafe key for its "Jev" judge at roughly $0.15-0.35 per 1,000 answers (about $2-4/month for 25 prompts on 3 platforms); Elmo Cloud from $29/mo [S7].
13. Canonry is MIT, 194 stars, last push 2026-10-28, npm `@canonry/canonry` (CLI `cnry`), MCP, REST API and web UI on SQLite with BYOK providers (Gemini, OpenAI, Meta Muse, Claude, Perplexity, OpenRouter, Exa, Parallel); it measures brand mentions separately from source citations [S8][S14].
14. Canonry integrates Google Search Console, Bing Webmaster Tools, Google Business Profile, GA4, server-side traffic from Cloudflare, Vercel, Cloud Run and WordPress (crawler visits, AI page fetches), sitemap/URL submissions, schedules and webhook alerts, and ships a portable Agent Plugins 1.0.0 plugin with generated Codex and Claude Code adapters [S8].
15. open-seo-mcp-skills (Ryze) has MIT skills and 7,728 stars, but every skill's data comes through the hosted Ryze connector (`https://connector.get-ryze.ai/mcp`) with DataForSEO wired in; its `ai-visibility` skill reads GA4 AI-referral reports [S9][S14].
16. marketingskills (coreyhaines31) is MIT, 57,020 stars, last push 2026-10-27, installed with `npx skills add coreyhaines31/marketingskills`; its `ai-seo` skill says "No AI-specific Search Console reporting", lists Merchant Center feeds as an AI-search input, and points to paid trackers or a DIY spreadsheet for monitoring [S10][S14].
17. geoptimize is MIT, 263 stars, a deterministic content-readiness lint for CI and pre-commit (npm, GitHub Action `cucuwang/geoptimize@v0.12.0`) that explicitly does not predict AI Overviews or AI citation [S11][S14].
18. aaron-marketing-skills is Apache-2.0, 3,027 stars, 120 skills, installable as a Claude Code plugin or via `npx skills add` on Codex, Cursor, OpenCode, Gemini CLI, Copilot CLI; its static bundles' auditors return NOT_SCORED and it adds nothing to /mcp [S12][S14].
19. R1tom/bing-webmaster-mcp (MIT, 0 stars, last push 2026-10-20) exposes search_performance, crawl_health, url_info, sitemaps, submit_urls (up to 500 URLs per daily quota, plus IndexNow when `INDEXNOW_KEY` is set), backlinks and keyword_research, with no AI-performance tool [S13][S14].
20. The Bing Webmaster API reference (IWebmasterApi, updated 2023-11-14) lists query/page/URL stats and submission-quota methods and no AI, Copilot, citation or grounding method [S19].
21. The Search Console API `searchanalytics.query` reference (last updated 2026-08-11) allows `type` values discover, googleNews, news, image, video, web and dimensions country, device, page, query, searchAppearance, date, hour, names no AI Overviews/AI Mode/generative-AI type, states no pricing, and caps rowLimit at 25,000 [S17].
22. AminForou/mcp-gsc (MIT, 2,051 stars, last push 2026-09-15) has 20 tools including URL inspection and batch inspection over OAuth, with no AI-feature tool in its README [S20][S14].
23. The official MCP registry search for "seo" returns mostly hosted commercial servers with no repository (e.g. ai.seocrawl/mcp, app.seolytics/seolytics, com.abbyseo/mcp-server) plus small open ones (riverliu8/inxy-mcp, aispiringcoder4302/seo-aeo-geo-mcp, noahflk/seo-mcp); "indexnow" returns sharozdawa/indexnow-mcp among others [S21].
24. SNLabat/SEO-GEO-AEO-Skill (266 stars) and Illyism/seo-skills (627 stars) carry no license per the GitHub API, so neither can be copied or adapted [S14].
25. Merchant Center MCP servers exist only at 0 stars (YerayRodri/merchant-center-mcp, MIT, described as Merchant API v1 read-only; webloom-agency/merchant-center-mcp) [S14, repository descriptions only].

#### Sources read
| id | title | site | date carried | URL | rank |
|---|---|---|---|---|---|
| S1 | claude-seo README | github.com | push 2026-10-22 | https://github.com/AgriciDaniel/claude-seo | 3 |
| S2 | claude-seo skills/seo-agentic/SKILL.md + references/access-policy.md | github.com | same | https://github.com/AgriciDaniel/claude-seo/tree/main/skills/seo-agentic | 3 |
| S3 | claude-seo skills/seo-geo/SKILL.md | github.com | same | https://github.com/AgriciDaniel/claude-seo/blob/main/skills/seo-geo/SKILL.md | 3 |
| S4 | claude-seo extensions/bing-webmaster seo-bing SKILL.md + scripts/indexnow_submit.py | github.com | same | https://github.com/AgriciDaniel/claude-seo/tree/main/extensions/bing-webmaster | 3 |
| S5 | geo-optimizer-skill README | github.com | push 2026-10-27 | https://github.com/Auriti-Labs/geo-optimizer-skill | 3 |
| S6 | geo-optimizer src/geo_optimizer/core/audit_cdn.py | github.com | same | https://github.com/Auriti-Labs/geo-optimizer-skill/blob/main/src/geo_optimizer/core/audit_cdn.py | 3 |
| S7 | elmo README | github.com | push 2026-10-27 | https://github.com/elmohq/elmo | 3 |
| S8 | canonry README + docs/plugins.md | github.com | push 2026-10-28 | https://github.com/Canonry/canonry | 3 |
| S9 | open-seo-mcp-skills README | github.com | push 2026-10-27 | https://github.com/Ryze-AI-Adgent/open-seo-mcp-skills | 3 |
| S10 | marketingskills README + skills/ai-seo/SKILL.md | github.com | push 2026-10-27 | https://github.com/coreyhaines31/marketingskills | 3 |
| S11 | geoptimize README | github.com | push 2026-10-19 | https://github.com/cucuwang/geoptimize | 3 |
| S12 | aaron-marketing-skills README | github.com | push 2026-10-28 | https://github.com/aaron-he-zhu/aaron-marketing-skills | 3 |
| S13 | bing-webmaster-mcp README | github.com | push 2026-10-20 | https://github.com/R1tom/bing-webmaster-mcp | 3 |
| S14 | GitHub REST API repo metadata (license, pushed_at, stars) for 21 repos + gh repo search | api.github.com | fetched 2026-10-28 | https://api.github.com/repos/{owner}/{repo} | 3 |
| S15 | GitHub topic generative-engine-optimization (1,203 repos, top 20) | github.com | fetched 2026-10-28 | https://github.com/topics/generative-engine-optimization | 3 |
| S16 | OpenAlternative AI visibility tracking category | openalternative.co | undated | https://openalternative.co/categories/business-software/marketing-customer-engagement/ai-visibility-tracking | 5 |
| S17 | Search Console API searchanalytics.query | developers.google.com | 2026-08-11 | https://developers.google.com/webmaster-tools/v1/searchanalytics/query | 1 |
| S18 | AI features and your website | developers.google.com | 2025-12-10 (as fetched) | https://developers.google.com/search/docs/appearance/ai-features | 1 |
| S19 | IWebmasterApi interface reference | learn.microsoft.com | 2023-11-14 | https://learn.microsoft.com/en-us/dotnet/api/microsoft.bing.webmaster.api.interfaces.iwebmasterapi?view=bing-webmaster-dotnet | 1 |
| S20 | mcp-gsc README | github.com | push 2026-09-15 | https://github.com/AminForou/mcp-gsc | 3 |
| S21 | Official MCP registry API search (seo, geo, aeo, indexnow, search-console, bing) | registry.modelcontextprotocol.io | fetched 2026-10-28 | https://registry.modelcontextprotocol.io/v0/servers?search=seo | 3 |

#### Contradictions seen
- claude-seo states a Search Console "Search generative AI" control exists since 2026-08-31 and cites developers.google.com/search/docs/appearance/ai-features [S3] vs that page as fetched (last updated 2025-12-10) names no such control, only robots.txt and preview directives [S18]: unresolved; the fetch may be a stale copy. Platform fact for aeo-platform-facts.
- marketingskills `ai-seo` says "No AI-specific Search Console reporting" [S10] vs search snippets (not read) reporting a Search Console generative-AI impressions report launched 2026-06-03: unresolved, S10 likely stale; not a claim until a primary page is read.
- geo-optimizer's own context check counts "manual generative-AI control" [S5] consistent with S3, against S18 as fetched.

#### Open threads
- Whether the Search Console generative-AI report and the "Search generative AI" setting are exposed in any API: S17 shows no AI `type`; primary announcement not read (boundary: platform facts).
- Bing AI Performance report API: S19 (2023 reference) has none; a Search Influence post (snippet only, not read) says Fabrice Canel put API support on the backlog and data is CSV export only.
- Elmo providers guide (scraper names and per-run cost) not read.
- Notra (AGPL-3.0, 270 stars) and Ansvisor (MIT, 203 stars) listed on S16 without repo links; not identified.
- Metadata-only trackers, README not read: danishashko/geo-aeo-tracker (MIT, 310 stars, push 2026-10-19), oneglanse/oneglanse (MIT, 235, 2026-10-04, drives real UIs by browser automation per S16), limelit-co/open (Apache-2.0, 223, 2026-10-22, single Go binary + SQLite + MCP per S15), getcito (NOASSERTION license, 500).
- Perplexity Sonar API pricing (the only answer API S5 says returns real source URLs) not read.
- claude-seo Codex/Copilot/OpenCode usability: repo has AGENTS.md and .claude-plugin manifests only; no other host install documented.

#### Searched and not found
- gh search "ai crawler access check cloudflare": no repositories.
- MCP registry "geo": only unrelated geodata servers.
- No open-source tool found that reads Bing AI Performance or the Search Console generative-AI report programmatically.
- No maintained Merchant Center MCP above 0 stars.

#### Delegation table
| name | URL | license | last commit (push) | stars | capabilities | covers which gap | delegation fit |
|---|---|---|---|---|---|---|---|
| claude-seo | github.com/AgriciDaniel/claude-seo | MIT | 2026-10-22 | 23,068 | full SEO audit, GEO, agent readiness (Lighthouse Agentic), WAF UA matrix, Content-Signal/Web Bot Auth, GSC/CrUX/GA4, Bing+IndexNow, drift snapshots, paid citation extensions | WAF/CDN (authorized UA matrix), SC generative AI control and snippet controls (knowledge), IndexNow, Bing; citation tracking only via paid SE Ranking/Profound | inspiration: second full audit owner duplicating the local one, Claude-Code-only install, open-core with a private Pro edition |
| geo-optimizer-skill | github.com/Auriti-Labs/geo-optimizer-skill | MIT | 2026-10-27 | 1,207 | GEO 0-100 audit, 27 bots, CDN crawler access, citability, `geo citations` BYOK with run sampling, 12 MCP tools, SARIF/JUnit, GitHub Action | WAF/CDN bot-block, snippet + generative-AI control check, automated citation sampling | inspiration; tool-level delegation via `uvx` possible but open-core (GeoReady) with its own scoring rubric |
| Elmo | github.com/elmohq/elmo | MIT | 2026-10-27 | 517 | scheduled prompt tracking on ChatGPT, AI Mode, AIO, Gemini, Perplexity, Copilot; citations, fan-out, sentiment; API/SDK/MCP | automated citation tracking | yes as an external measurement backend reached through its MCP; needs Docker+Postgres, provider/scraper keys and a TypeSafe key |
| Canonry | github.com/Canonry/canonry | MIT | 2026-10-28 | 194 | BYOK citation tracking, GSC, Bing WMT, GA4, server-side crawler/AI fetch logs (Cloudflare, Vercel...), URL submission, schedules; Agent Plugins with Claude+Codex adapters | automated citation tracking, Bing, indexing submissions, AI crawler log evidence | yes, strongest delegation candidate for measurement (agent-first, portable plugin, BYOK); young community, verify release cadence |
| open-seo-mcp-skills | github.com/Ryze-AI-Adgent/open-seo-mcp-skills | MIT | 2026-10-27 | 7,728 | GSC/GA4/Ads/DataForSEO skills, AI-referral traffic | none of the listed gaps beyond AI-referral analytics (already local) | no: data path is a closed hosted connector |
| marketingskills | github.com/coreyhaines31/marketingskills | MIT | 2026-10-27 | 57,020 | seo-audit, ai-seo, schema, programmatic SEO prompt skills | none (states no AI-specific SC reporting) | inspiration only; overlaps, partner-funded tool lists |
| geoptimize | github.com/cucuwang/geoptimize | MIT | 2026-10-19 | 263 | deterministic content-readiness lint, CI Action | none (content lint) | inspiration for a deterministic CI lint shape |
| aaron-marketing-skills | github.com/aaron-he-zhu/aaron-marketing-skills | Apache-2.0 | 2026-10-28 | 3,027 | 120 marketing skills, multi-host via npx skills | none | no: static prompts, auditors NOT_SCORED |
| bing-webmaster-mcp | github.com/R1tom/bing-webmaster-mcp | MIT | 2026-10-20 | 0 | Bing WMT stats, crawl health, URL info, submit_urls, IndexNow | IndexNow, Bing (not AI Performance) | inspiration: maturity too low |
| indexnow-mcp | github.com/sharozdawa/indexnow-mcp | MIT | 2026-03-22 | 2 | IndexNow + Google Indexing API submission | IndexNow | inspiration: trivial protocol, low maturity |
| mcp-gsc | github.com/AminForou/mcp-gsc | MIT | 2026-09-15 | 2,051 | 20 GSC tools, URL inspection, OAuth | none of the AI gaps | no for gaps; possible GSC data source |
| merchant-center-mcp | github.com/YerayRodri/merchant-center-mcp | MIT | 2026-08-30 | 0 | Merchant API v1 read-only (description only) | Merchant Center | no: unread, 0 stars |
| SEO-GEO-AEO-Skill / seo-skills | github.com/SNLabat/SEO-GEO-AEO-Skill, github.com/Illyism/seo-skills | none | 2026-03-13 / 2026-10-28 | 266 / 627 | audit prompts | none verified | no: unlicensed |

Official measurement APIs: Search Console API is free with no AI `type` or dimension (S17, 2026-08-11); Bing Webmaster API needs a free API key, no AI method in the reference (S19), URL submission is quota-bound (500/day per S13); Bing AI Performance appears CSV-only (secondary, unread).
