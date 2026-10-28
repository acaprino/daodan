---
name: grabber-development
description: >
  Knowledge base for production crawlers, from target assessment through observability.
  TRIGGER WHEN: building, debugging or optimizing a Python web scraper, or working on anti-bot bypass for Cloudflare, DataDome or PerimeterX, CAPTCHA solving, proxy architecture or rate limiting.
---

<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. Network search and network fetch
use the runtime's registered web search tool when the Codex configuration enables
it. A user question uses the runtime's registered question tool when one exists;
otherwise ask it in the reply and wait for the answer. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

# Python Web Scraping

Knowledge base for building production-grade Python web scraping systems. Covers the full stack from target assessment through production observability.

## First Tool Call on Every Scraping Task

This section overrides everything else in this skill if there is any conflict. Read it first, act on it first.

When this skill activates on a scraping task, **your next non-question tool call MUST launch a visible browser with the capture surface attached**. Not `Write pyproject.toml`. Not `Write models.py`. Not "let me sketch the architecture first". Browser first, then code.

The one carve-out is a target listed under **Bundled Targets** below. Its Discovery Gate has already been run and its capture is recorded, so reading that reference and running its script satisfies this rule without reopening a browser. Anything not on that list gets the browser.

The default path is **user-driven navigation with live capture**, not automated clicks. The user knows their data and their portal better than you do, and authenticated SaaS sites need them anyway. Steps:

1. Ask the bare minimum to start: target URL, what data is wanted, authenticated yes/no. One short batch of questions, then stop asking.
2. Immediately open the browser: with the Playwright MCP tools of the `playwright` plugin (a declared dependency of this plugin, on Claude Code installed with `claude plugin install playwright@claude-plugins-official`, on other hosts by registering `npx @playwright/mcp@latest` as the MCP server `playwright`), `browser_navigate` to the target, which opens a visible browser, then dump with `browser_network_requests` once the user is done; or, when the target needs stealth or the Capture Surface below needs WebSocket, SSE or worker traffic, run an inline Patchright script through shell execution with `headless=False` and every handler in the Capture Surface. Keep it alive through the host-supported background/session mechanism and a caller-controlled completion signal; do not assume interactive stdin.
3. Tell the user verbatim: "Browser is open with full network capture (XHR + fetch + WebSocket + SSE + workers + cookies + main-frame navigations). Log in, navigate to the data, apply the filters you'd use day-to-day, then tell me when you are done so I can signal the capture process and reason from real endpoints."
4. While the user navigates, you watch the capture stream. When they signal completion and the caller stops the capture, you have: real URLs, real endpoint paths, real field names, real WebSocket frames, real auth cookies. *Now* you can scaffold.

The caller-driven variant is fine only when there is no login, no 2FA, and no UI-knowledge gap. Same launch, same capture handlers; you call `page.goto` / `page.click` yourself instead of waiting for the caller-controlled completion signal.

Writing project files (`pyproject.toml`, `src/<pkg>/...`, `models.py`) before the capture is in your hands is the failure mode this section exists to prevent. If you catch yourself drafting field-name `alias` tuples from "common patterns" (Italian + English, REST conventions, framework defaults), stop and launch the browser instead.

The full capture surface, output checklist, and anti-patterns are in the **Discovery Gate** section below. Read those too. But the imperative is here: **browser before code, every time, user navigates by default.**

## When to Use

- Assessing a target site's protection level and choosing the right tools
- Discovering API endpoints via network traffic interception (Playwright/Patchright)
- Extracting data from rendered pages when no API is available
- Bypassing anti-bot systems (Cloudflare, DataDome, PerimeterX)
- Configuring TLS/HTTP fingerprint impersonation (curl_cffi, primp)
- Setting up stealth browser automation (Patchright, Camoufox, Nodriver)
- Designing proxy architecture with tiered escalation
- Solving CAPTCHAs programmatically (CapSolver, 2Captcha, playwright-captcha)
- Building production scraping pipelines (Scrapy, Crawlee)
- Adding rate limiting and observability to scraping systems

## Discovery Gate (READ BEFORE WRITING ANY CODE)

**Phase 1 (Target Assessment) and Phase 2 (Data Discovery) are blocking gates, not optional steps.** You MUST execute them yourself and have their concrete outputs in hand before scaffolding any project file (`pyproject.toml`, modules, models, CLI). No exceptions.

**You always control the browser session and the capture.** The deliverable of discovery is not a script you hand over; it is a live capture you watched. Always launch the browser yourself (the Playwright MCP tools, or inline Patchright when stealth or WebSocket, SSE and worker capture are needed), visible, with the full capture surface attached, and keep the session open inside your turn.

**Who clicks depends on the task. The capture is yours either way:**

- **The caller clicks** when the target is reachable without the user: no login, no 2FA, you know the UI, you can guess the right filters.
- **User clicks, you watch in-loop** when the target needs the user: login, 2FA / OTP, navigation choices only the user can make, or the user wants to drive the filters / dates / screens visited. This is the gold-standard path for authenticated SaaS portals because the user knows exactly which screens hold the target data. Launch the browser visibly, wait on a caller-controlled completion signal supported by the active host, let the user navigate while the network capture streams live, then dump the capture when they signal "done".
- The actual anti-pattern is writing `scripts/discover.py` and telling the user "run this and paste the output back". That breaks the loop: by the time the user runs it, you have no eyes on the session and no chance to ask "wait, click that filter again, I lost the payload".

**Capture surface (attach all of these from page launch):**

- `page.on("request")` / `page.on("response")` for XHR + fetch (URL, method, status, headers, cookies, request body, response body when JSON or text)
- `page.on("websocket")` then `ws.on("framesent")` / `ws.on("framereceived")` for WebSocket traffic in both directions
- Response content-type sniff for `text/event-stream` (SSE) and chunked transfer
- `page.on("worker")` for service-worker- and dedicated-worker-initiated requests
- GraphQL detection: URL ends in `/graphql`, request body has `operationName` / `variables` / `extensions.persistedQuery.sha256Hash`
- `context.cookies()` after login, plus any anti-bot cookies (`cf_clearance`, `__cf_bm`, `datadome`, `_px3`, `ak_bmsc`, `incap_ses`)
- `page.on("framenavigated")` filtered to the main frame, to record every landing URL after redirects

Redact `Authorization`, `Cookie`, and password fields in anything saved to disk. Keep them in the in-memory capture you reason from.

**Discovery outputs you MUST collect before scaffolding** (treat as a checklist; if any item is still a guess, you have not finished discovery):
- Real URL of every page that holds target data (not assumed paths, not `/#/...` guesses)
- Real XHR/fetch endpoint URLs, methods, status codes, request headers, cookies
- Real field names and shapes from at least one captured JSON response (paste a redacted sample into the design notes)
- For any WebSocket the page opens: handshake URL, subprotocol, first frames in each direction (auth + subscribe), recurring message schema
- For any SSE / EventSource stream: endpoint URL, event types, payload shape
- For GraphQL: exact `operationName` and `variables`, persisted-query SHA if present
- For service-worker / dedicated-worker requests: the worker URL and the requests it issues
- Anti-bot fingerprint check: `cf_clearance`, `__cf_bm`, `datadome`, `_px3`, `ak_bmsc`, `incap_ses` present or absent
- SPA framework / DOM structure of any page where API discovery fails and a DOM fallback is needed

If any of those is still a guess, you have not finished discovery; do not proceed to scaffolding.

### Anti-Patterns (do not do these)

- Scaffolding `pyproject.toml` and module skeleton before observing one real network request from the target
- Inferring endpoint URLs from "common patterns" (e.g. `/api/invoices`, `/#/fatture-ricevute`) without observation
- Building a regex / filter list of "common field names" (e.g. `(fatture|invoice|received|ricevute|passive)`) as a substitute for the real endpoint name
- Writing a Pydantic model with `Field(alias=...)` tuples of "Italian + English likely names" instead of the names actually returned by the API
- Handing the user a `discover.py` script as the *first* discovery step when you could open the browser yourself
- Marking Phase 1 / Phase 2 as "skipped, will refine later" and proceeding to write code anyway

## Core Workflow

For every scraping task, follow this sequence (the Discovery Gate above governs steps 1 and 2):

### 1. Target Assessment (YOU execute this)
- Load the target URL in a browser (the Playwright MCP tools, or inline Patchright when stealth is needed)
- Identify: static HTML vs JS-rendered, anti-bot service (check for cf_clearance, DataDome cookies, px cookies), data volume needed, update frequency
- Capture: real landing URL after any redirects, SPA framework if any, presence/absence of anti-bot cookies

### 2. Data Discovery (API-first, YOU execute this)
- Navigate the site with Playwright/Patchright **yourself**
- Intercept all network traffic via `page.on("request")` and `page.on("response")`
- Filter for XHR/fetch requests returning JSON, GraphQL, or structured data
- Classify: REST endpoints, WebSocket streams, GraphQL queries, SSE feeds
- Record (do not guess): URLs, methods, headers, cookies, response shapes, real field names
- If structured API found: generate curl_cffi replay code (skip browser entirely)
- If the page is gated by credentials you have and 2FA you can prompt for, log in via the browser session and continue discovery in the authenticated area

### 3. DOM Fallback (only if no API)
- If data exists only in rendered HTML: extract via CSS/XPath selectors
- Check for JSON-LD, microdata, or inline `<script>` JSON before parsing DOM
- For unstable DOM: use LLM-based extraction (Crawl4AI, ScrapeGraphAI) as final fallback
- Hybrid pattern: CSS selectors for stable fields ($0/extraction) + LLM for unstable fields (~$0.01/repair)

### 4. Stealth & Evasion (layer minimally)
- No protection: plain curl_cffi with `impersonate="chrome"` -- done
- Basic Cloudflare: Patchright persistent context + real Chrome channel
- Heavy Cloudflare/Turnstile: stealth browser + CAPTCHA solver + residential proxy
- DataDome: Camoufox + ghost-cursor behavioral simulation + residential proxy
- PerimeterX: organic navigation pattern + session warming + residential proxy

### 5. Production Hardening
- Rate limiting: pyrate-limiter v4 with Redis backend for distributed scraping
- Proxy rotation: tiered escalation (datacenter -> ISP -> residential -> mobile)
- Observability: structlog + Prometheus + Grafana
- Error handling: retry with backoff, proxy failover, session rotation

## Tool Selection Quick Reference

| Target Profile | HTTP Client | Browser | Framework |
|---------------|-------------|---------|-----------|
| No JS, no protection | curl_cffi | none | Scrapy / httpx |
| JS-rendered, no protection | none | Playwright | Crawlee |
| Basic Cloudflare | curl_cffi + cf_clearance | Patchright (for cookie) | Scrapy |
| Heavy Cloudflare | none | Patchright persistent | Crawlee |
| DataDome | none | Camoufox + ghost-cursor | custom |
| PerimeterX | none | Nodriver / Patchright | custom |
| AI extraction needed | none | Crawl4AI / Firecrawl | standalone |

## Proxy Tier Quick Reference

| Tier | Type | Price Range | Use When |
|------|------|-------------|----------|
| 0 | No proxy | free | Unprotected targets, development |
| 1 | Datacenter | $0.10-0.50/GB | Light protection, high volume |
| 2 | ISP (static residential) | $0.53-1.47/IP | Account management, login flows |
| 3 | Residential | $0.49-8.00/GB | Anti-bot bypass, geo-targeting |
| 4 | Mobile | $4-13/GB | Highest trust, last resort |

## Bundled Targets

Some targets have already been through the Discovery Gate, and their capture is
recorded rather than repeated. When the task is one of these, read the reference
and run the script instead of opening a browser to rediscover what is written
down.

- **Instagram profile media** -- `references/instagram-media.md` plus
  `scripts/instagram_grab.py`. Downloads every photo, carousel slide and reel of
  a profile at full resolution. Anonymous access is closed (`401 require_login`
  on both `web_profile_info` endpoints), so it drives a logged-in browser,
  captures one genuine `PolarisProfilePostsTabContentQuery_connection` request
  and replays it with the cursor swapped. The workflow `instagram-grab` wraps it.
  The one trap worth carrying in your head: the newest 24 posts are delivered in
  the initial page payload and never appear in that query, so a passive network
  listener returns a truncated archive that looks complete.

## Reference Materials

- `field-guide.md` -- full 2025-2026 Python web scraping field guide covering browser stealth, TLS fingerprinting, behavioral biometrics, anti-bot bypass, CAPTCHA solving, proxy landscape, frameworks, AI-assisted scraping, GraphQL reverse engineering, rate limiting, and observability
- `instagram-media.md` -- the captured Instagram surface: the closed anonymous routes, the 2026 login selectors, the EU pay-or-consent wall, the profile grid query and its node schema, and the download stage
