---
description: 'Inspects a live deployment in the browser to see what really fires. TRIGGER WHEN: the user asks to audit GA4, verify GTM setup, check Consent Mode v2 compliance, debug missing conversions, validate dataLayer events, or check "why isnt my site converting". DO NOT TRIGGER WHEN: the task is general SEO (use /digital-marketing:seo-audit), or content and CTA optimization (use /digital-marketing:content-strategy).'
argument-hint: '<url or local path> [--gtm <container-id>] [--strict-mode]'
---

<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

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

<!-- Generated by the Daodan compiler for pi. Edit the kernel, never this file. -->

# GA4 + GTM Audit

Comprehensive audit of a website's GA4 + GTM setup with live Playwright verification. Produces `.ga4-audit/REPORT.md` with prioritized fixes.

## CRITICAL RULES

1. **Verify live, not just code**. Use the Playwright MCP tools to load the site, inspect `dataLayer`, network requests to `google-analytics.com`/`googletagmanager.com`, and the cookie banner state.
2. **Check Consent Mode v2 compliance**. Analytics must not fire before consent on EU visitors; verify default `analytics_storage: 'denied'` and correct `update` calls.
3. **Never fabricate IDs**. If you cannot see the GA4 Measurement ID, GTM Container ID, or Ads Conversion ID, say so -- do not guess.
4. **Write output to `.ga4-audit/`** for persistence and re-runs.

## Pre-flight

### Dependency check

Every live check in Phase 2 needs the Playwright MCP tools (`browser_navigate`, `browser_evaluate`, `browser_network_requests`). If they are not available, print this and stop:

```
Missing required dependency: Playwright MCP (Microsoft, @playwright/mcp)

Live verification needs the Playwright MCP tools to inspect dataLayer,
network requests, cookies, and the consent banner state in a real browser.

Install Microsoft's Playwright MCP server for the host you run in, then
run this again:
  Claude Code  claude plugin install playwright@claude-plugins-official
  Codex        codex mcp add playwright npx "@playwright/mcp@latest"
  VS Code      code --add-mcp '{"name":"playwright","command":"npx","args":["@playwright/mcp@latest"]}'
  Copilot CLI  /mcp add  (name playwright, command npx @playwright/mcp@latest)
  Pi           pi install npm:pi-mcp-adapter, then add the same server under
               "playwright" in mcpServers of ~/.config/mcp/mcp.json
  OpenCode     opencode mcp add playwright --global -- npx @playwright/mcp@latest
```

Do not fall back to a source-only audit: a GA4 audit that never saw a tag fire is a code review, and reading it as an audit is how broken tracking ships.

### Flags

- `--gtm <GTM-ID>` -- skip container detection in Phase 1 and audit the given container ID. Still flag any *other* container ID found in the source as a duplicate.
- `--strict-mode` -- treat every Warning as Critical in the final report and print an explicit `VERDICT: FAIL` line when any remains. Report text only; the command never sets a process exit code.

## Phase 1 -- Discovery

Identify the target:
- Live URL, or an already-running local dev server. To find one, read the project's dev script and its configured port, or ask the user for the URL. Never start a dev server and never claim one was started.
- Extract GTM container ID (`GTM-XXXXXX`) from `<script src="...gtm.js?id=GTM-...">` or `<iframe src="...ns.html?id=GTM-...">`. With `--gtm <GTM-ID>`, use the supplied ID instead and skip this step
- Extract GA4 Measurement ID (`G-XXXXXXXX`) from gtag config or dataLayer events
- Detect CMP: iubenda, Cookiebot, Orestbida CookieConsent, OneTrust, Axeptio, custom
- Detect Consent Mode v2 integration: look for `gtag('consent', 'default', {...})` and `gtag('consent', 'update', {...})` calls

Write discovery artifacts to `.ga4-audit/01-discovery.md`.

## Phase 2 -- Live Verification with Playwright

Open the site in Playwright, capture:

### Pre-consent state
- Before accepting cookies, record `dataLayer` contents and any network requests to `g/collect` (GA4) or `ads/ga-audiences` (Ads)
- Expected: no hits unless Consent Mode defaults allow (e.g., `ad_user_data: 'denied', analytics_storage: 'denied'`)
- Flag if `g/collect` fires before consent -- GDPR violation

### Post-consent state
- Accept cookies, record the `gtag('consent', 'update', ...)` call payload
- Record subsequent `g/collect` hits, their parameters (`en`, `tid`, `cid`, `dl`)
- Confirm GTM is live: inspect `window.dataLayer` contents and the network requests to `googletagmanager.com/gtm.js`
- Verify GA4 cookies are set: `_ga`, plus `_ga_<ID>` where `<ID>` is the Measurement ID with the `G-` prefix stripped (`G-ABC123` produces `_ga_ABC123`)

### Event coverage
For each page type (home, product, checkout, thank-you), capture:
- `dataLayer.push({event: 'page_view', ...})` -- implicit if autotracking
- Custom events: `add_to_cart`, `purchase`, `sign_up`, `lead`, etc.
- Enhanced E-commerce items array for `purchase`

Write to `.ga4-audit/02-verification.md`.

## Phase 3 -- Configuration Audit

Using the GA4 Admin API (if the user has API credentials configured for it) or a manual walkthrough of the GA4 admin UI with the user, verify:

### GA4 Property
- [ ] Data streams configured (Web, iOS, Android as needed)
- [ ] Enhanced Measurement enabled for relevant events (scroll, outbound clicks, site search, video, file download, form interactions)
- [ ] Data retention set (2 months is the default and the safe EU choice; 14 months only with a documented business justification)
- [ ] Google Signals enabled only if remarketing is needed AND consent has `ad_user_data: 'granted'`

IP anonymization needs no verification. GA4 truncates IPs by design and exposes no setting to check or toggle (see `gdpr-compliance-eu.md`).

### Key Events (Conversions)
- [ ] `purchase` marked as Key Event (always)
- [ ] Business-specific events marked (form_submit, begin_checkout, generate_lead)
- [ ] No double-counting (avoid marking both `click` and `generate_lead` for the same action)
- [ ] Key Event value set where monetary (`value` parameter)

### Audiences (for Remarketing)
- [ ] "All Users" audience exists (GA4 default)
- [ ] Retargeting audiences: cart abandoners, high-intent visitors, past purchasers
- [ ] Predictive audiences (likely-to-purchase, likely-to-churn) enabled -- note 28-day backfill (not immediate)
- [ ] Audience triggers fire on correct events

### Ads Linking
- [ ] GA4 property linked to Google Ads account
- [ ] Key Events imported into Ads as Conversions
- [ ] Enhanced Conversions enabled for key event imports (hashed email, phone)
- [ ] Consent signals propagated to Ads (`ad_storage`, `ad_user_data`, `ad_personalization`)

Write to `.ga4-audit/03-config.md`.

## Phase 4 -- Consent Mode v2 Deep Check

Consent Mode v2 is mandatory for EU traffic since March 2024.

### Default state
```javascript
// Required BEFORE gtag('config', 'G-...') or GTM load
gtag('consent', 'default', {
  ad_storage: 'denied',
  ad_user_data: 'denied',
  ad_personalization: 'denied',
  analytics_storage: 'denied',
  wait_for_update: 500          // ms, optional but strongly recommended
});
```

Consent Mode v2 requires exactly these four signals. `functionality_storage`, `personalization_storage`, and `security_storage` are optional extras: accept them if the CMP sets them, never flag them as missing.

### Update on acceptance
```javascript
// After user accepts
gtag('consent', 'update', {
  ad_storage: 'granted',
  ad_user_data: 'granted',
  ad_personalization: 'granted',
  analytics_storage: 'granted'
});
```

Flag:
- [ ] Default call missing -> all traffic denied by default; no modeled conversions
- [ ] Default call fires AFTER GTM/gtag load -> race condition
- [ ] Granular consent categories not mapped (EU requires 4 separate signals, not just one "analytics")
- [ ] `wait_for_update` missing -> events fire with denied before update arrives

Write to `.ga4-audit/04-consent.md`.

## Phase 5 -- Report

Generate `.ga4-audit/REPORT.md`:

```markdown
# GA4 + GTM Audit Report -- <url> -- <date>

## Summary
- GTM Container: <GTM-XXXXXX>
- GA4 Property: <G-XXXXXXXX>
- CMP Detected: <iubenda / Cookiebot / etc.>
- Consent Mode v2: [COMPLIANT | PARTIAL | MISSING]
- Live verification: PLAYWRIGHT
- VERDICT: [PASS | FAIL]   <!-- with --strict-mode, any Warning promotes to Critical and forces FAIL -->

## Critical (GDPR / data-loss risk)
- ...

## High (breaking measurement)
- ...

## Medium (best-practice gaps)
- ...

## Nice-to-have
- ...

## Auto-implementable fixes
Code snippets ready to paste for each fix.
```

## Synergies

- Playwright-based verification -> the `playwright` plugin (Microsoft's Playwright MCP server)
- GA4/GTM knowledge base -> `digital-marketing:ga4-implementation` skill
- Cookie banner (CMP) selection + config -> `business:privacy-doc-generator`
- Full SEO audit (separate) -> `/digital-marketing:seo-audit`
