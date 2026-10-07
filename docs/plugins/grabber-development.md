# Grabber Development Plugin

> Expert Python web scraping: a coordinator plus three specialists covering stealth browser automation, TLS/HTTP fingerprint impersonation, AI-assisted extraction, anti-bot bypass, proxy architecture, API discovery, and production observability.

Command examples and named tools in this guide use Claude notation. For other
hosts, use the entry points and bindings in the source-derived reference below
and [host setup](../hosts.md).

## Agents

### `grabber-architect`

Lead architect / coordinator for production Python scraping systems. Handles upstream work (target assessment, discovery, framework choice, cost, observability, legal guardrails) and routes specialist tasks.

| | |
|---|---|
| **Model** | `inherit` |
| **Color** | pink |
| **Tools** | Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch |
| **Use for** | Designing a new scraping pipeline end-to-end, assessing target protection before tool choice, API reverse-engineering via network interception, framework selection (Scrapy / Crawlee / Crawl4AI / Firecrawl), rate limiting + observability, cost modelling, routing to specialists |

**Decision frameworks:**
- Tool selection matrix (target profile -> HTTP client + browser + framework)
- Proxy tier selection (protection level -> tier + provider)
- Extraction strategy (data location -> method + cost + stability)
- Framework choice (Scrapy 2.14, Crawlee v1.0, Crawl4AI v0.8+, Firecrawl)

**Legal / ethical guardrails:** Documents robots.txt, ToS, GDPR/CCPA, CNIL guidance, EU AI Act Art. 50, copyright considerations. Refuses to generate code that bypasses paywalls or auth without documented permission.

---

### `stealth-browser-expert`

Specialist for stealth browser automation: Patchright, Camoufox, Nodriver, rebrowser-patches, selenium-driverless, behavioral biometrics, and browser-level CAPTCHA integration.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Picking / configuring stealth browser driver (Patchright for Chromium, Camoufox for Firefox / DataDome, Nodriver for PerimeterX / Cloudflare); behavioral biometrics (ghost-cursor); `cf_clearance` extraction for HTTP replay; persistent context strategy; browser-level CAPTCHA (playwright-captcha, playwright-recaptcha) |

**Driver matrix:** Patchright (Chromium, general) / Camoufox (Firefox, DataDome) / Nodriver (PerimeterX, advanced CF) / rebrowser-patches (existing Puppeteer codebases).

**Key content:** driver selection by target protection level, behavioral biometrics (velocity/acceleration curves, typing rhythm, scroll momentum), CAPTCHA-before-environment rule (environment signals matter more than puzzle-solve quality), cf_clearance handoff to `http-fingerprint-expert`.

---

### `http-fingerprint-expert`

Specialist for HTTP/TLS fingerprinting and impersonation: curl_cffi, primp, async-tls-client, JA3 / JA4 / JA4+ suite, HTTP/2 fingerprinting, proxy tier selection (datacenter / ISP / residential / mobile), and managed Web Unlocker APIs.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Picking HTTP client that impersonates a browser TLS fingerprint; debugging why httpx/requests gets blocked; reverse-engineering an API for `curl_cffi` replay; choosing proxy tier; integrating a Web Unlocker API (Bright Data / Oxylabs / ZenRows) |

**Client matrix:** curl_cffi (default for protected targets, Chrome 99-135 / FF 102-135 / Safari 15-18 / HTTP/3), primp (Rust-powered, 2-3x faster), async-tls-client v2.2+ (historical profiles), plus Go alternatives.

**Key content:** JA4+ suite vs deprecated JA3, HTTP/2 fingerprinting (SETTINGS, WINDOW_UPDATE, pseudo-header order), browser session replay rules (TLS family must match browser, UA must match exactly, IP must match), proxy tier cost table (datacenter $0.10-0.50/GB -> mobile $4-13/GB), Web Unlocker API cost/benefit (~$3.40/1K requests for Bright Data, ~97.9% success).

---

### `ai-scraping-expert`

Specialist for AI-assisted extraction: Crawl4AI, Firecrawl, ScrapeGraphAI, Browser Use, Stagehand, Skyvern, Jina Reader, Spider.cloud; Pydantic schema-driven extraction; LLM-repair hybrid pipelines; GraphQL reverse engineering; cost modelling for LLM-based extraction at scale.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Picking between LLM-based scraping frameworks; designing schema-driven extraction with Pydantic; building a CSS + LLM-fallback hybrid; reverse-engineering a GraphQL API (persisted query bypass); estimating extraction cost at 1M+ pages/month scale |

**Framework matrix:** Crawl4AI (LLM-ready markdown, deep crawl) / Firecrawl (strongest Pydantic integration) / ScrapeGraphAI (graph-based LLM pipelines) / Browser Use (85K stars, 89% WebVoyager) / Stagehand (self-healing) / Skyvern (vision-first) / Jina Reader (100B tokens/day).

**Key content:** when LLM extraction vs CSS vs JSON-LD (CSS ~$0, LLM ~$0.01/page), hybrid CSS+LLM fallback pattern (cuts cost 5-10x), Pydantic schema-driven extraction, GraphQL persisted-query bypass via mitmproxy sha256Hash replacement, cost formulas for 1M pages/month pipelines.

---

## Skills

### `grabber-development`

Comprehensive Python web scraping knowledge base covering the full stack from target assessment through production observability.

| | |
|---|---|
| **Trigger** | Building, optimizing, or debugging Python web scrapers |

**First tool call:** on any scraping task, the first non-question tool call must launch a visible browser (`headless=False`) with the full capture surface attached (XHR and fetch, WebSocket, SSE, workers, cookies, main-frame navigations). The skill states that this rule overrides everything else in it. By default the user navigates while the capture streams, and the session parks on `input()` until they signal done; Claude drives only when there is no login, no 2FA and no UI-knowledge gap. The one carve-out is a target listed under **Bundled Targets**: its capture is already recorded, so reading its reference and running its script satisfies the rule without reopening a browser.

**Discovery Gate:** Target Assessment and Data Discovery are blocking gates. No project file (`pyproject.toml`, modules, models, CLI) is scaffolded until the discovery checklist is filled from a live capture: real page URLs, real endpoints, real field names, WebSocket, SSE and GraphQL details, and the anti-bot cookies present or absent. Endpoints or field names inferred from "common patterns" are named anti-patterns.

**Core workflow:**

1. **Target Assessment**: Identify protection level, data volume, update frequency
2. **Data Discovery (API-first)**: Intercept network traffic, find REST/GraphQL/WebSocket endpoints
3. **DOM Fallback**: CSS/XPath selectors, JSON-LD, LLM extraction as last resort
4. **Stealth & Evasion**: Layer minimally: plain curl_cffi -> Patchright -> Camoufox + ghost-cursor
5. **Production Hardening**: Rate limiting, proxy rotation, observability, error handling

**Quick reference tables:**

| Target Profile | HTTP Client | Browser | Framework |
|---------------|-------------|---------|-----------|
| No JS, no protection | curl_cffi | none | Scrapy / httpx |
| JS-rendered, no protection | none | Playwright | Crawlee |
| Basic Cloudflare | curl_cffi + cf_clearance | Patchright | Scrapy |
| Heavy Cloudflare | none | Patchright persistent | Crawlee |
| DataDome | none | Camoufox + ghost-cursor | custom |
| PerimeterX | none | Nodriver / Patchright | custom |

**Bundled Targets:** targets that have already been through the Discovery Gate, with their capture recorded. The one listed is **Instagram profile media** (`references/instagram-media.md` plus `scripts/instagram_grab.py`, wrapped by `/grabber-development:instagram-grab`).

**Reference docs included:**

| Reference | Content |
|-----------|---------|
| `field-guide.md` | Full 2025-2026 Python web scraping field guide: browser stealth, TLS fingerprinting, behavioral biometrics, anti-bot bypass, CAPTCHA solving, proxy landscape, frameworks, AI-assisted scraping, GraphQL reverse engineering |
| `instagram-media.md` | The captured Instagram surface: the closed anonymous routes, the login selectors, the EU pay-or-consent wall, the profile grid query and its node schema, and the download stage |

---

## Commands

### `/grabber-development:instagram-grab`

Download every photo and video of one Instagram profile at full resolution, carousel slides and reels included, into a local folder that a re-run updates with only what is new. The bundled script drives a real logged-in browser to the profile, keeps one genuine `PolarisProfilePostsTabContentQuery_connection` request the page issues on its own, and replays it with only the cursor changed, so no rotating token is ever reconstructed. The workflow settles the username and a destination that nothing publishes or git tracks, checks for a stored session at `~/.instagram-grabber/session.json` (anonymous access is closed, so a first run needs a person at the keyboard), runs a `--dry-run` first and checks its counts, and leaves the Meta cookie dialog and the EU pay-or-consent screen to the user rather than answering them on their behalf. The run is resumable and idempotent, and the report gives the downloaded, already present and failed counts, the total size and the destination. Credentials go only in the `IG_USER` and `IG_PASS` environment variables of that one command, never in a file or on a command line.

| | |
|---|---|
| **Argument** | `<username> [--out DIR] [--limit N] [--since YYYY-MM-DD] [--no-videos] [--metadata]` |
| **Other flags the workflow uses** | `--dry-run`, `--no-photos`, `--covers` (keep each video's cover frame), `--concurrency N` (parallel downloads, default 5) |
| **Output** | The media files plus `_manifest.json`, which records what was fetched and, with `--metadata`, captions, permalinks and alt text |

```
/grabber-development:instagram-grab some_profile --out ig-some_profile --limit 50
```

---

**Related:** [python-development](python-development.md) (async patterns, system architecture) | [opentelemetry](opentelemetry.md) (distributed tracing for scraping observability) | `playwright@claude-plugins-official` (Microsoft's Playwright MCP server, a hard dependency, required for live-capture discovery; on Claude Code `claude plugin install playwright@claude-plugins-official`, on Codex, Copilot and Pi see the per-host table in the README's [Browser automation](../../README.md#browser-automation-playwright) section)

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `1.8.2`. **Source:** [plugin.toml](<../../plugins/grabber-development/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | None |
| Direct external | `playwright@claude-plugins-official` |
| Local closure (1) | [grabber-development](<grabber-development.md>) |
| External closure (1) | `playwright@claude-plugins-official` |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `repository.read`, `shell.execute`, `repository.write`, `network.fetch`, `contexts.isolate`, `roles.dispatch`.
**Optional capabilities:** `execution.parallel`.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `grabber-development:grabber-development` | Knowledge base for production crawlers, from target assessment through observability. TRIGGER WHEN: building, debugging or optimizing a Python web scraper, or working on anti-bot bypass for Cloudflare, DataDome or PerimeterX, CAPTCHA solving, proxy architecture or rate limiting. | [grabber-development](<../../plugins/grabber-development/skills/grabber-development/SKILL.md>) |
| Role | `grabber-development:ai-scraping-expert` | Specialist for the AI-assisted half of a scraping pipeline. TRIGGER WHEN: picking between Crawl4AI, Firecrawl, ScrapeGraphAI, Browser Use, Stagehand, Skyvern, Jina Reader and Spider.cloud, designing Pydantic schema-driven extraction, building a CSS plus LLM-fallback hybrid, reverse-engineering a GraphQL API, or estimating extraction cost at scale. DO NOT TRIGGER WHEN: the work is TLS fingerprinting (use http-fingerprint-expert), browser stealth or CAPTCHA (use stealth-browser-expert), or boilerplate with no LLM (use grabber-architect). | [ai-scraping-expert](<../../plugins/grabber-development/roles/ai-scraping-expert.md>) |
| Role | `grabber-development:grabber-architect` | Lead architect for production Python crawlers: owns the upstream decisions, routes the rest to three experts. TRIGGER WHEN: designing a scraping pipeline end to end, assessing target protection before tool choice, reverse-engineering an API via network interception, picking between Scrapy, Crawlee, Crawl4AI and Firecrawl, or setting rate limits, observability and cost. DO NOT TRIGGER WHEN: the task sits wholly in one specialty: browser stealth (use stealth-browser-expert), HTTP fingerprints (use http-fingerprint-expert), or LLM extraction (use ai-scraping-expert). | [grabber-architect](<../../plugins/grabber-development/roles/grabber-architect.md>) |
| Role | `grabber-development:http-fingerprint-expert` | Specialist for the transport layer of a scraper. TRIGGER WHEN: picking an HTTP client that impersonates a browser TLS fingerprint (curl_cffi, primp, async-tls-client), debugging why httpx or requests gets blocked, matching JA3, JA4+ or HTTP/2 fingerprints, replaying a reverse-engineered API, choosing a proxy tier (datacenter, ISP, residential, mobile), or integrating a Web Unlocker API. DO NOT TRIGGER WHEN: the work needs a rendered browser (use stealth-browser-expert) or LLM extraction (use ai-scraping-expert). | [http-fingerprint-expert](<../../plugins/grabber-development/roles/http-fingerprint-expert.md>) |
| Role | `grabber-development:stealth-browser-expert` | Evasion specialist for the rendered-browser layer of a scraper. TRIGGER WHEN: selecting or configuring a stealth driver (Patchright, Camoufox, Nodriver, rebrowser-patches, selenium-driverless), bypassing Cloudflare, DataDome or PerimeterX, extracting cf_clearance for HTTP replay, wiring ghost-cursor, playwright-captcha or playwright-recaptcha, or designing a persistent browser context. DO NOT TRIGGER WHEN: the target has no anti-bot (plain Playwright or httpx suffices), the work is HTTP fingerprinting (use http-fingerprint-expert) or LLM extraction (use ai-scraping-expert). | [stealth-browser-expert](<../../plugins/grabber-development/roles/stealth-browser-expert.md>) |
| Workflow | `grabber-development:instagram-grab` | Download every photo and video from an Instagram profile at full resolution, including carousel slides and reels, into a local folder that can be re-run to pick up only what is new. TRIGGER WHEN: the user asks to grab, download, archive, mirror or back up the media of an Instagram profile or account, or wants the photos and videos of a page for reuse elsewhere. DO NOT TRIGGER WHEN: the target is a single post URL the user already has, a platform other than Instagram, or the task is building a new scraper for a different site, which belongs to the grabber-development skill and its specialists. | [instagram-grab](<../../plugins/grabber-development/workflows/instagram-grab.md>) |

### Workflow contracts

Contracts describe observable outputs; Markdown bodies define decisions,
flags, safety gates and execution. Declared `invoke` execution is unsupported.

#### `grabber-development:instagram-grab`

**Arguments:** <code>&lt;username&gt; [--out DIR] [--limit N] [--since YYYY-MM-DD] [--no-videos] [--metadata]</code>

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `instagram-grab-completed` |
| Artifacts | `instagram-archive` |
| Schemas | None declared |
| Declared workers | None |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [instagram-grab.toml](<../../plugins/grabber-development/workflows/instagram-grab.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `grab` | None | None | `shared` | None declared | `preferred` |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/grabber-development](<../../exports/claude/plugins/grabber-development>) | `native` | `instagram-grab: native-team` |
| copilot | [exports/copilot/plugins/grabber-development](<../../exports/copilot/plugins/grabber-development>) | `native` | `instagram-grab: parallel-subagents` |
| codex | [exports/codex/plugins/grabber-development](<../../exports/codex/plugins/grabber-development>) | `adapted` | `instagram-grab: parallel-subagents` |
| pi | [exports/pi/plugins/grabber-development](<../../exports/pi/plugins/grabber-development>) | `adapted` | `instagram-grab: parallel-subagents` |
| opencode | [exports/opencode/plugins/grabber-development](<../../exports/opencode/plugins/grabber-development>) | `native` | `instagram-grab: parallel-subagents` |

<!-- daodan:reference:end -->
