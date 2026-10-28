---
name: ga4-implementation
description: >
  Knowledge base behind the ga4-implementation-expert agent: the EU legal detail, CMP choice, event taxonomy, and per-framework install recipes its workflow cites.
  TRIGGER WHEN: a GA4 or GTM task needs that reference material directly, or a site has traffic but no conversions and the diagnostic patterns are wanted.
---

<daodan_host_binding host="copilot">
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

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. fetch
retrieves a known URL and does not search: network search needs a search tool
registered in this session. A user question is asked in the reply, and the run
waits for the answer. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

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

# GA4 Implementation

This skill is the knowledge base behind the `ga4-implementation-expert` agent. It covers everything needed to deploy Google Analytics 4 with Google Tag Manager on a real website: the legal/compliance layer that is mandatory in the EU, the technical installation across frameworks, the event and conversion taxonomy, the audiences for remarketing, and the diagnostic patterns to figure out why a site is not converting.

## Compliance is the blocking prerequisite

GA4 cannot be legally deployed in Italy or the EU without all of the following:

1. A technical Consent Management Platform (CMP) that **blocks GA4 cookies before user consent**, not just a written cookie policy
2. A cookie banner that meets the Italian Garante requirements (equal-weight Accept/Reject, granular preferences, no scroll-as-consent, 6-month resuppression)
3. **Google Consent Mode v2** with all four signals (`analytics_storage`, `ad_storage`, `ad_user_data`, `ad_personalization`) set to `denied` by default
4. Accepted Data Processing Terms (Art. 28 GDPR) in the GA4 account settings
5. Google Signals **disabled** for EEA traffic

A cookie policy page that describes which cookies the site uses **does not satisfy the law**. The site must have a technical mechanism that prevents the cookies from being set in the first place. This is the most common compliance failure on Italian and EU sites.

For non-EU traffic the legal bar is lower, but Consent Mode v2 is still mandatory by Google policy since 6 March 2024 for any property serving any EEA user. Without it, Google disables remarketing and audience building.

## How to use this guide

Most GA4 implementation tasks follow this sequence:

1. **Audit compliance first** - read [`references/gdpr-compliance-eu.md`](references/gdpr-compliance-eu.md). If the CMP and Consent Mode v2 layer is not in place, fix that before touching tags.
2. **Install GTM and the GA4 tag** - read [`references/gtm-setup.md`](references/gtm-setup.md) for the install rules, the snippet placement order, and the EEA account-level lockdown.
3. **Map business goals to events** - read [`references/events-and-conversions.md`](references/events-and-conversions.md) for the standard event taxonomy, custom dimensions, Key Events marking, and audience patterns.
4. **Apply the framework-specific integration** - read [`references/framework-integration.md`](references/framework-integration.md) for vanilla HTML, Next.js (App + Pages Router), React, and WordPress patterns.
5. **Verify and diagnose** - read [`references/diagnostics-troubleshooting.md`](references/diagnostics-troubleshooting.md) for verification tools, the traffic-vs-conversion diagnostic split, industry benchmarks, and the common errors checklist.

For diagnostic-only tasks ("why isn't my site converting"), jump straight to step 5.

## Reference index

### [`gdpr-compliance-eu.md`](references/gdpr-compliance-eu.md)

The legal layer. Italian Garante decisions timeline (2022 Caffeina, 2023 DPF adequacy, 2025 T-553/23, pending Schrems III appeal), cookie banner mandatory requirements, GA4 account-level mandatory configurations, the four Consent Mode v2 signals and their defaults, Basic vs Advanced mode trade-off, CMP selection (iubenda recommended for non-technical users, Orestbida CookieConsent v3 as the free open-source alternative), and ready-to-paste code snippets.

### [`gtm-setup.md`](references/gtm-setup.md)

The installation rationale and the load-bearing rules. Why GTM is preferred over gtag.js direct, the EEA account-level lockdown to apply before the container goes live (retention, Google Signals, attribution, DPA, signup country), the two GTM snippets, snippet installation in correct order (Consent Mode v2 default block → CMP loader → GTM head snippet → GTM noscript body snippet), GA4 Google Tag configuration with the Initialization - All Pages trigger, install gotchas, container backups, environments, and the standard-reports timeline. Property and container creation steps are delegated to the official Google docs it links.

### [`events-and-conversions.md`](references/events-and-conversions.md)

The measurement layer. Enhanced Measurement auto-events, custom event patterns via GTM (book button clicks, tel/mailto/wa.me link clicks, form submissions, external OTA clicks), when to use the GA4 recommended event names for ecommerce and the mandatory `ecommerce: null` clear-out before each push (the recommended-events list and the `items[]` shape are delegated to the official Google docs it links), custom dimensions registration walkthrough, Key Events marking (formerly Conversions), the standard audience pattern set, Google Ads link procedure, Enhanced Conversions, internal traffic exclusion, EEA reporting identity, and attribution settings.

### [`framework-integration.md`](references/framework-integration.md)

The per-framework implementation patterns. Vanilla HTML and static site generators (Jekyll, Hugo, Eleventy), Next.js (App Router with `@next/third-parties/google`, Pages Router with `_document.tsx` and `next/script`, route change tracking), CRA/Vite React with router listeners, WordPress (theme `functions.php` action hooks vs plugins like Site Kit and GTM4WP), and common pitfalls (hydration mismatches, double-firing on Strict Mode, caching plugins stripping snippets).

### [`diagnostics-troubleshooting.md`](references/diagnostics-troubleshooting.md)

The diagnostic and troubleshooting layer. The traffic-vs-conversion split (Scenario A: nobody visits / Scenario B: people visit but don't convert) with the GA4 reports to check for each, Acquisition report interpretation, Funnel Exploration setup, hospitality and travel benchmarks, data thresholding workarounds for low-traffic sites, Microsoft Clarity integration, Google Search Console integration, and the common errors checklist (snippet on one page only, double tracking, wrong placement, Measurement ID typos, internal IP exclusion).

## What this skill does not cover

- **Server-side GTM (sGTM)**: out of scope. If the user needs server-side tagging, point them to Google's official documentation.
- **Universal Analytics → GA4 migration**: UA is sunset since July 2023. Historical UA data is read-only and cannot be migrated; GA4 must be set up fresh.
- **BigQuery export**: advanced topic, link the user to the GA4 BigQuery linking docs when they ask.
- **Looker Studio dashboard templates**: GA4 has built-in reports that suffice for most cases; Looker Studio is a follow-on layer.
- **Non-Google analytics**: Matomo, Plausible, Fathom, etc. The DPF-fallback contingency note in `gdpr-compliance-eu.md` mentions Matomo briefly as the EU-hosted alternative if the DPF is invalidated, but this skill is GA4-specific.

## Source attribution

The legal and compliance content reflects Italian Garante guidance (Provvedimenti 9677876 and 9782874), the EU-US Data Privacy Framework adequacy decision (10 July 2023), the Tribunale Generale UE ruling on Case T-553/23 (3 September 2025), and the Google Consent Mode v2 specification as of 2025-2026. Verify against current Garante and Google publications when implementing for production sites, especially if a "Schrems III" decision lands at the Court of Justice in late 2026 or early 2027.
