<daodan_host_binding host="pi">
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

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi has no network tool: network fetch and network search run as shell
commands, and a user question is asked in the reply while the run waits for the
answer.
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

# GTM setup walkthrough

How to install GTM correctly with Consent Mode v2 ordering, and the EEA-specific account-level lockdown to do BEFORE deploying. Property/container creation steps and the verification routine live upstream; this file is the rationale + the load-bearing rules.

## When to use

Setting up a fresh GA4 + GTM install. Read `gdpr-compliance-eu.md` FIRST if the site doesn't have a working CMP -- GTM should not be deployed without one.

## Why GTM, not gtag.js direct

Even on a small static site, GTM wins for three reasons:

1. **Consent Mode v2 is dramatically easier with GTM** thanks to CMP templates in the Community Template Gallery and the GTM debug tools that show consent state per tag fire.
2. **Future Google Ads work needs zero code changes** -- conversion tags, remarketing tags, Floodlight all configured in the GTM web UI.
3. **For non-developer site owners**, every tracking change after initial setup happens in the GTM UI, not in the codebase.

Exceptions where gtag.js direct is acceptable: developer-only project with strong reasons to avoid extra script tags, single-tag deployment that will never grow, tight landing page where every byte matters. Default to GTM otherwise.

The official Google docs (March 2026) recommend the same: *"If you're unfamiliar with javascript, we recommend using Google Tag Manager instead of gtag.js."*

## EEA account-level lockdown (do this before publishing the container)

Configure these BEFORE the container goes live. Changing them later is harder and some changes don't apply retroactively.

| Setting | Path | Value |
|---------|------|-------|
| **Data retention** | Admin → Data Collection and Modification → Data Retention | **14 months** (or 2 months for max compliance), enable **"Reset user data on new activity"** |
| **Google Signals** | Admin → Data Settings → Data Collection | **Disabled** for EEA properties |
| **Attribution model** | Admin → Data Display → Attribution Settings | Data-driven (default), set lookback to fit business cycle (90d travel, 30d ecommerce) |
| **DPA** | Admin → Account Settings | Accept Data Processing Terms (Art. 28 GDPR) |
| **Country at signup** | Admin → Account Settings | **Italy** (or relevant EU country) so EU-specific terms apply |

Disabling Google Signals is the single biggest GDPR-compliance lever and also reduces data thresholding on low-traffic properties. See `gdpr-compliance-eu.md` for the full rationale.

## The two snippets (every page)

GTM provides two snippets. Both must be present on **every page**.

```html
<!-- Snippet 1: in <head>, as high as possible -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-XXXXXXX');</script>
```

```html
<!-- Snippet 2: immediately after opening <body> -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-XXXXXXX"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
```

Replace `GTM-XXXXXXX` with the actual container ID.

## The `<head>` ordering template (the load-bearing rule)

If the CMP doesn't auto-handle Consent Mode v2 defaults (iubenda does), insert the default block **before** the GTM head snippet. Complete order:

```html
<head>
  <!-- 1. Consent Mode v2 defaults (skip if CMP handles automatically) -->
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('consent', 'default', {
      'ad_storage': 'denied',
      'ad_user_data': 'denied',
      'ad_personalization': 'denied',
      'analytics_storage': 'denied',
      'wait_for_update': 500
    });
  </script>

  <!-- 2. CMP loader (iubenda embed, Cookiebot autoblock, Orestbida config) -->

  <!-- 3. GTM head snippet -->
  <script>(function(w,d,s,l,i){...})(window,document,'script','dataLayer','GTM-XXXXXXX');</script>

  <meta charset="UTF-8">
  <!-- ... -->
</head>
<body>
  <!-- GTM noscript iframe HERE, never inside <head> -->
  <noscript><iframe src="..."></iframe></noscript>
  <!-- page content -->
</body>
```

For frameworks (Next.js, React, WordPress) instead of vanilla HTML, see `framework-integration.md`.

## Initialization - All Pages (the trigger that catches everyone)

When configuring the GA4 Google Tag inside GTM:

- Tag type: **Google Tag** (not the older "Google Analytics: GA4 Configuration" -- still exists but Google Tag is current).
- Trigger: **Initialization - All Pages**, NOT "All Pages".

**Why**: the Initialization trigger fires before all other triggers, which is critical for Consent Mode -- the Google tag must initialize before any tag that depends on consent state. Wrong trigger choice = tags fire before consent updates → Consent Mode v2 reports show all-denied even after acceptance. This is one of the top install errors (see `diagnostics-troubleshooting.md` #10).

## Gotchas

- **Don't paste the snippet only on `index.html`.** Centralize via layout/include and grep the build output for the container ID on every deploy. The #1 static-site error.
- **Don't have both gtag.js and GTM injecting the same Measurement ID** -- silent double tracking. Hard to detect because there are no errors, the data just looks "good" until you compare with another source. Historical data corrupted by double tracking is **not recoverable**.
- **Smart quotes (`"` and `"`)** copied from a word processor break the script silently. Always copy from the GTM/GA4 web UI, never retype.
- **Snippet inside a `<div>`, after `</head>`, or buried under many other scripts** = lost early page interactions, especially `session_start` and the first `page_view`.
- **The DPA acceptance is a separate click** in Admin → Account Settings. It's NOT the Terms of Service. Without it you don't have an Art. 28 GDPR compliant data-processor relationship with Google.
- **Country selection at signup matters** -- it determines which Terms of Service variant applies. Choosing Italy (or your EU country) at signup is a one-shot decision; can't easily change later.

## Container backups (cheap insurance)

Admin → Containers → Export Container → save the JSON in your project repo as `gtm-backup-YYYY-MM-DD.json`. Restore: Admin → Import Container → Overwrite or Merge. Good practice before major changes and useful for staging→production migration.

## Environments (overkill for small sites)

GTM Environments (Admin → Environments → New) give per-environment snippet variants with `&environment_auth=...` parameters. Worth it for sites with multiple stakeholders or strict change control; for small sites publish directly to the default environment.

## Standard reports timeline

Realtime works immediately after the first event. **Standard GA4 reports** (Acquisition, Engagement, etc.) take **24-48 hours** to populate. Don't panic if Reports → Engagement → Pages and Screens is empty for the first day -- check Realtime instead.

## Official docs

- GTM official quickstart: https://support.google.com/tagmanager/answer/6103696
- GA4 setup quickstart: https://support.google.com/analytics/answer/9304153
- Google Tag (vs older GA4 Config tag): https://support.google.com/tagmanager/answer/12382666
- Initialization triggers: https://support.google.com/tagmanager/answer/7679319
- Consent Mode v2: https://developers.google.com/tag-platform/security/guides/consent
- Tag Assistant: https://tagassistant.google.com
- DebugView: https://support.google.com/analytics/answer/7201382
- Tag Coverage report: https://support.google.com/analytics/answer/14066363
- Data retention: https://support.google.com/analytics/answer/7667196
- Container Import/Export: https://support.google.com/tagmanager/answer/6106997
- Environments: https://support.google.com/tagmanager/answer/6311518

## Related

- `framework-integration.md` -- the framework-specific install (Next.js, React, WordPress, ...)
- `events-and-conversions.md` -- the events to wire up after the install works
- `gdpr-compliance-eu.md` -- the compliance layer that comes BEFORE this
- `diagnostics-troubleshooting.md` -- the 10 errors that break installations
