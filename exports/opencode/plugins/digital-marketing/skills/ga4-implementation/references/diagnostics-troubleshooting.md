<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
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
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
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

# Diagnostics and troubleshooting

The two halves: **why a site doesn't generate results** ("I have GA4 but no bookings come in") and **why an installation is broken**. Plus the EU-specific data-thresholding workarounds and the Clarity-with-Consent-Mode wiring.

## When to use

Diagnosing low conversion, debugging missing events, or hardening a fresh install. For installation steps, see `gtm-setup.md` and `framework-integration.md`.

## The fundamental diagnostic split: traffic or conversion?

After GA4 has been collecting for **at least 2-4 weeks** (minimum 100 sessions for any pattern to be statistically meaningful):

### Scenario A -- nobody visits (traffic problem)

Reports → Acquisition → Traffic Acquisition. Users/Sessions near zero over 30 days = problem is upstream of GA4.

Check: Search Console (`site:example.com` query, indexing, impressions/CTR/position), Google Business Profile (claimed, complete, photos/reviews), inbound links (OTAs, directories, social).

**Hand off to**: `seo-specialist` agent -- traffic problems are SEO problems, need their own tooling.

### Scenario B -- people visit but don't convert (conversion problem)

Reports → Engagement → Events. Sessions exist (>100/month) but Key Events count is zero or very low.

Check: build a **Funnel Exploration** (Explore → Funnel Exploration), find the drop-off step. Compare mobile vs desktop bounce (delta > 20pts = mobile UX problem). Reports → Engagement → Pages and Screens to see if visitors reach the conversion page. Reports → Engagement → Landing Page to see entry points. Install **Microsoft Clarity** for the "why" GA4 can't show.

**Hand off to**: `content-marketer` (CTA, copy) and/or `/digital-marketing:content-strategy` (UX and CRO audit).

## Funnel templates

- **Hospitality**: homepage → gallery/details → contact/prenota → `generate_lead`
- **Ecommerce**: `view_item_list` → `view_item` → `add_to_cart` → `begin_checkout` → `purchase`
- **SaaS**: homepage → pricing → sign up → `sign_up`

The biggest drop-off step IS the priority. 80% reach the form but 5% submit it = the form is the problem (too long, broken, asks too much).

## Data thresholding for low-traffic sites (the EEA workaround)

GA4 hides report rows when user counts are too low (orange triangle warning). Aggressive when: **Google Signals enabled** (biggest factor), demographic dimensions used, narrow date ranges, segments < 50 users.

### Workarounds

1. **Disable Google Signals** in Admin → Data Settings → Data Collection (recommended for EEA anyway for GDPR)
2. **Use 30+ day windows** in reports
3. **Avoid demographic dimensions** (Age, Gender) -- they trigger thresholding hard
4. **Switch Reporting Identity to Device-based** (Admin → Reporting Identity) -- sacrifices some attribution for less thresholding
5. **Avoid very narrow segments** -- prefer fewer, broader

For sites under 1000 sessions/month, thresholding is constant. Below 100/month, standard reports are too sparse to act on -- focus on Realtime, DebugView, and Microsoft Clarity instead.

## Microsoft Clarity (the free heatmap+session-replay tool that fills GA4's gaps)

Free, no traffic limits. Heatmaps + session recordings show **why** users don't convert in a way GA4 can't.

Install: clarity.microsoft.com → create project → paste embed in `<head>` of every page (same as GA4). Optional: Clarity → Settings → Setup → Google Analytics integration to link recordings to GA4 segments. Clarity and GA4 coexist without conflicts.

### GDPR consent for Clarity (the local-rule worth keeping)

Clarity sets non-essential cookies (`_clck`, `_clsk`, `CLID`, `MUID`) and **requires consent in EU** just like GA4. **From 31 October 2025, Microsoft applies consent-signal requirements for EEA users on Clarity.**

Place Clarity in the same "Analytics" category in your CMP and ensure it is blocked until consent is given:

- **iubenda / Cookiebot autoblocking**: automatic, nothing to do.
- **Orestbida CookieConsent**: mark the Clarity script tag with `type="text/plain" data-category="analytics"`.

### What to look for in Clarity

- **Rage clicks** -- rapid clicks in the same spot → broken button or expected interactivity that doesn't exist
- **Dead clicks** -- click on element that doesn't respond → misleading visual cue
- **Excessive scrolling** -- can't find what they're looking for
- **Quick backs** -- page didn't match expectation
- **JS errors** -- Clarity logs them in recordings; useful for catching prod bugs

## Google Search Console (the missing piece)

Measures what happens **before** the user arrives: impressions, CTR, average position, search queries (which GA4 cannot see), indexing status, crawl errors, Core Web Vitals, mobile usability.

For "no bookings come in" diagnosis, **Search Console is the FIRST tool** to check if the problem is that Google doesn't find or doesn't show the site.

Verification options: HTML file at site root, `<meta name="google-site-verification">`, DNS TXT record, or Google Tag (auto-verify if GA4 already installed via the same account).

Linking: GA4 → Admin → Product Links → Search Console Links → Link → publish "Search Console" collection in Reports Library. Then Reports → Search Console → Queries shows the queries users searched -- the only place to see them in GA4.

## Industry benchmarks (rough -- prefer historical-comparison)

Hospitality / travel: engagement rate 50-60%, avg engagement 1-3 min, views/session 2-4, mobile-vs-desktop bounce delta < 10pts.

Ecommerce: engagement rate 55-65%, avg engagement 2-5 min, cart-to-purchase 1-3% (varies vertical), add-to-cart-to-checkout 30-50%.

Red flags: engagement < 40-45%, avg engagement < 30-60s, single-page bounce, mobile/desktop delta > 20pts, cart-to-purchase < 0.5%, ATC-to-checkout < 15%.

## The 10 most common installation errors (the local cookbook)

In order of frequency:

### 1. Snippet on only one page (most common static-site error)

Symptom: Reports → Engagement → Pages and Screens shows only one page (typically homepage). Tag Coverage report flags missing pages.

Fix: paste in every page, or centralize via layout/include. Grep the build output to verify.

### 2. Double tracking (silent and insidious)

Symptom: every metric appears 2x. Hard to detect -- no errors, just "good-looking" data until you compare with another source.

Cause: gtag.js AND GTM both injecting the same Measurement ID, or the same snippet pasted twice.

Detection: DevTools → Network → filter `collect` -- one request per page_view, not two. View-source for `G-XXXXXXXXXX` and `GTM-XXXXXXX` -- exactly one of each. Tag Assistant warns about duplicates.

Fix: remove one. **Historical data corrupted by double tracking is NOT recoverable.** Mark the recovery date and treat older data as suspect.

### 3. Snippet in the wrong position

Symptom: missing early page interactions, especially `session_start` and first `page_view`.

Fix: the GTM snippet goes as high in `<head>` as possible, first among scripts except the Consent Mode v2 default block and the CMP loader, which must precede it (see error 6 and the ordering template in `gtm-setup.md`). The GTM noscript iframe goes immediately after `<body>`, never inside `<head>`.

### 4. Wrong Measurement ID

Symptom: data goes to wrong property or nowhere. Realtime empty.

Cause: typo, extra spaces, or smart quotes (`"` and `"`) copied from a word processor instead of straight quotes (`"`).

Fix: copy-paste directly from GA4 → Admin → Data Streams. Verify byte-for-byte. **Never retype an ID.**

### 5. Internal traffic not excluded

Symptom: numbers bigger than they should be, especially homepage. Owner visits skew data.

Fix: see "Internal traffic exclusion" in `events-and-conversions.md`.

### 6. CMP loads after GTM (the Consent Mode v2 trap)

Symptom: tags fire before consent state updates. Consent Mode v2 reports show all-denied even after user accepted.

Cause: Consent Mode default block runs after the GTM snippet, OR the CMP loader runs after GTM.

Fix: enforce `<head>` order: (1) Consent Mode v2 default block → (2) CMP loader → (3) GTM snippet. See `gtm-setup.md` for the template.

### 7. WordPress caching plugin stripping the snippet

Symptom: works in admin/preview but not in incognito on the live front-end.

Cause: W3 Total Cache, WP Rocket, LiteSpeed, WP Super Cache -- HTML minification or "delay JavaScript execution".

Fix: flush cache. Add `googletagmanager.com` and `gtm.js` to the "do not minify" / "exclude from delay" list.

### 8. Hydration mismatch (Next.js, React)

Symptom: console warnings about hydration mismatch.

Cause: GTM injected via `dangerouslySetInnerHTML` in a server component without unique `id`.

Fix: `next/script` or `@next/third-parties/google`'s `<GoogleTagManager>` instead.

### 9. Ad blockers blocking GA4

Symptom: missing data for some users (estimates: 10-30% of users in Italy block trackers).

Cause: uBlock Origin, Ghostery, Brave Shields, Firefox tracking protection.

Fix: not directly fixable. Server-side GTM (sGTM) is the production-grade workaround. For most sites, accept the loss.

### 10. Wrong trigger type for the GA4 Google Tag

Symptom: tags fire in the wrong order, especially with Consent Mode.

Cause: trigger set to "All Pages" instead of "**Initialization - All Pages**".

Fix: in GTM, edit the GA4 Google Tag, change the trigger to **Initialization - All Pages** (under "Other"). Republish.

## Verification routine after every change

Run this BEFORE considering a change live:

1. Preview mode in GTM (Tag Assistant)
2. Publish with meaningful version name + description
3. Realtime report (verify event appears within minutes)
4. DebugView (verify parameters populated)
5. Wait 24-48h for standard reports
6. Standard reports (verify count looks reasonable)
7. Test on mobile (many issues only show on mobile)
8. Test in incognito with no ad blocker (cleanest environment)

## Official docs

- GA4 Realtime: https://support.google.com/analytics/answer/9271392
- DebugView: https://support.google.com/analytics/answer/7201382
- Tag Coverage report: https://support.google.com/analytics/answer/14066363
- Tag Assistant: https://tagassistant.google.com
- Funnel Explorations: https://support.google.com/analytics/answer/9327974
- Microsoft Clarity: https://clarity.microsoft.com (docs: https://learn.microsoft.com/en-us/clarity/)
- Clarity Consent Mode (Oct 2025 EEA requirements): https://learn.microsoft.com/en-us/clarity/setup-and-installation/cookie-consent
- Search Console verification: https://support.google.com/webmasters/answer/9008080
- Search Console + GA4 link: https://support.google.com/analytics/answer/10737381
- Data thresholding explained: https://support.google.com/analytics/answer/13109118
- Reporting Identity: https://support.google.com/analytics/answer/10978788

## Related

- `gtm-setup.md` -- the install + EEA lockdown that prevents many of these issues
- `framework-integration.md` -- the per-framework install gotchas
- `events-and-conversions.md` -- internal traffic exclusion + EEA reporting identity choice
- `gdpr-compliance-eu.md` -- the compliance layer (why Google Signals is off in EEA setups)
