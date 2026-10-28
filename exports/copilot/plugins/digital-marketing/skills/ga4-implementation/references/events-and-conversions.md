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

# Events, conversions, audiences

The measurement layer: which events to fire, the GTM trigger recipes that map clicks to events, custom dimensions, Key Events (renamed from Conversions in March 2024), audiences for remarketing, Google Ads link, and EEA-specific reporting choices.

## When to use

Configuring tracking AFTER GTM is installed -- adding events, marking Key Events, building remarketing audiences, linking Google Ads. For the install itself, see `gtm-setup.md` and `framework-integration.md`.

## What GA4 tracks automatically (Enhanced Measurement)

Default-enabled when the data stream is created:

| Event | Trigger |
|-------|---------|
| `page_view` | Every page load (incl. SPA virtual page views with the right GTM trigger) |
| `session_start`, `first_visit`, `user_engagement` | Auto |
| `scroll` | At 90% page scroll (toggleable) |
| `click` (outbound) | Click on link to different domain (toggleable) |
| `view_search_results` | URL contains a known search param (toggleable, customizable) |
| `video_start`/`progress`/`complete` | Embedded YouTube with JS API (toggleable) |
| `file_download` | Click on link with known file extension (toggleable) |

Layer custom events on top for actionable conversion data.

## GTM click-trigger recipes (the local cookbook)

The 6 patterns worth memorizing. All use a GTM **trigger** + a **GA4 Event tag** wired to the existing GA4 Google Tag (or measurement ID).

### Book / Reserve button click

- Trigger: **Click - All Elements**, Some Clicks, `Click Text` contains `Prenota` (or `Book`/`Reserve`)
- Optional: also match `Click Classes` if the button has a unique class
- Tag: GA4 Event, name `book_now_click`, params `button_text = {{Click Text}}`

### WhatsApp link

- Trigger: **Click - Just Links**, Wait for tags = yes, `Click URL` contains `wa.me`
- Tag: name `whatsapp_click`, param `link_url = {{Click URL}}`

### Phone (`tel:`)

- Trigger: **Click - Just Links**, `Click URL` starts with `tel:`
- Tag: name `phone_click`, param `phone_number = {{Click URL}}`

### Email (`mailto:`)

- Trigger: **Click - Just Links**, `Click URL` starts with `mailto:`
- Tag: name `email_click`

### Form submission

Two reliable approaches:

- **A. Native form + thank-you redirect**: trigger on `Page Path equals /grazie`, fire `generate_lead` with `method=contact_form`.
- **B. AJAX form, no redirect**: form library pushes `dataLayer.push({event:'form_submit_success', form_name:'contact'})` on success. Trigger on Custom Event `form_submit_success`, fire `generate_lead` with `method=contact_form`, `form_name = {{DLV - form_name}}`.

### External OTA / booking platform click

- Trigger: **Click - Just Links**, `Click URL` contains `booking.com` OR `airbnb`
- Tag: name `booking_platform_click`, param `platform` = a Custom JS Variable that returns `'booking'` or `'airbnb'` based on the URL

## Custom dimensions

Event parameters do NOT appear in GA4 reports automatically. Each parameter that you want to filter/group/break down by must be **registered**:

GA4 → Admin → Data Display → Custom Definitions → Create custom dimension. Scope **Event** (User scope is for user properties). Event parameter name is **case-sensitive** and must match the GTM tag exactly.

- Up to 24h to appear in reports.
- **NOT retroactive** -- only sees values collected after registration.
- Hard limit: **50 event-scoped + 25 user-scoped per property**. Don't register every parameter -- only the ones you'll actually slice by.

## Key Events (formerly Conversions)

Renamed March 2024. "Conversion" is now Google-Ads-only. Functionally identical: a flag on an event that makes it a primary success metric.

To mark: GA4 → Admin → Data Display → Events → toggle "Mark as key event". The event must have fired at least once to appear in the list.

### Suggested Key Events for hospitality / service business

- `generate_lead` (form submission) -- primary
- `book_now_click` -- primary
- `whatsapp_click`, `email_click`, `phone_click` -- primary
- `booking_platform_click` -- secondary (micro-conversion: user left to a 3rd party)

For ecommerce: primary `purchase`, secondary `begin_checkout`, `add_payment_info`, `add_to_cart`.

## Recommended events (for ecommerce: use the standard names)

GA4 has a fixed list of "recommended events" mapped to standard reports (Monetization, Funnel). Using the official names instead of inventing custom ones unlocks built-in reports for free. Full list and required parameters: https://support.google.com/analytics/answer/9267735.

The `items[]` array shape and the `ecommerce` dataLayer object structure are documented at https://developers.google.com/tag-platform/gtagjs/reference/events. In GTM, on a "GA4 Event" tag with name `purchase`, enable More Settings → Ecommerce → "Send Ecommerce data" with source "Data Layer" -- GTM picks up the `ecommerce` object automatically.

**Clear `ecommerce` before every push.** Google documents this as mandatory. Without it the previous object persists in the dataLayer and its items merge into the next event, so `add_to_cart` items reappear in `begin_checkout` and `purchase`:

```javascript
dataLayer.push({ ecommerce: null });
dataLayer.push({ event: 'add_to_cart', ecommerce: { items: [ /* ... */ ] } });
```

For non-ecommerce: `login`, `sign_up`, `search`, `share` are also worth using when applicable.

## Audiences (build them on day one)

Audiences populate **only from creation date forward** -- they are NOT retroactive. Create them as soon as the property is set up, before campaigns launch.

### Standard audience set (the local recipe)

| Audience | Definition | Membership |
|----------|------------|-----------|
| All visitors 30 days | `session_start` triggered | 30d |
| All visitors 180 days | `session_start` triggered | 180d |
| Engaged visitors | session > 60s AND pageviews > 2 | 90d |
| Visitors to booking page | `page_location` contains `/prenota` or `/book` | 30d |
| Visitors to gallery | `page_location` contains `/gallery` or `/foto` | 30d |
| **High-intent no-conversion** | fired `book_now_click` OR `whatsapp_click` but NOT `generate_lead` | 30d |
| Cart abandoners (ecommerce) | fired `begin_checkout` but NOT `purchase` | 30d |
| Past purchasers (ecommerce) | fired `purchase` | 540d (max) |

The high-intent-no-conversion audience is the most valuable single audience for retargeting -- people who showed booking intent but didn't complete.

Create: GA4 → Admin → Data Display → Audiences → New → Custom audience. Optionally attach an audience trigger (custom event when user joins).

## Google Ads link (do this even before campaigns)

GA4 → Admin → Product Links → Google Ads Links → Link. Linker needs admin on both sides. Enable "Personalized advertising".

Once linked: Ads cost data shows in GA4 Acquisition reports, audiences auto-export to Google Ads Audience Manager, **Key Events become importable as Conversion Actions** (Google Ads → Goals → Conversions → Import → GA4 properties → Web).

## Enhanced Conversions (raise conversion-rate signal)

Improves attribution by matching first-party hashed user data (email, phone) submitted in forms/checkout against Google's data.

Enable: GA4 → Admin → Data Streams → select stream → Configure tag settings → Show all → Allow user-provided data capabilities → ON. In GTM, on the GA4 Google Tag or the conversion event tag, configure user-provided data with selectors for the email/phone fields.

Material lift on Smart Bidding signal quality for Google Ads with form-based conversions.

## EEA reporting identity (the EU-specific local choice)

GA4 → Admin → Reporting Identity offers three modes:

- **Blended** (default) -- combines User-ID, Google Signals, Device-ID, modeling. Best accuracy when Google Signals is enabled.
- **Observed** -- User-ID, Google Signals, Device-ID without modeling.
- **Device-based** -- only Device-ID.

**For EU sites with Google Signals disabled** (the GDPR-recommended setup), **Device-based often gives the most useful low-traffic reports**. Modeling and Google Signals data trigger thresholding aggressively below 1k sessions/month -- Device-based avoids that entirely. The trade-off is some attribution accuracy.

## Internal traffic exclusion (the gotcha that pollutes data forever)

Owner visits skew everything. Steps:

1. GA4 → Admin → Data Streams → stream → Configure tag settings → Show all → **Define internal traffic** → Create rule "Owner IP", traffic_type = `internal`, "IP equals" → enter your IP.
2. GA4 → Admin → Data Settings → **Data Filters** → find "Internal Traffic" filter → change state from **Testing** to **Active**.

Once active, internal traffic is permanently excluded from all reports AND **disappears from DebugView** -- disable temporarily for debug sessions or use a different device. For dynamic IPs (most home connections) the rule must be updated periodically.

## Attribution settings

GA4 → Admin → Data Display → Attribution Settings:

- **Model**: data-driven (default). Don't change manually -- with low traffic GA4 falls back to last-click.
- **Conversion lookback**: 30d for fast-cycle ecommerce, **90d for travel/hospitality**, B2B SaaS, anything with long decision cycles.
- **Engagement lookback**: 30d.

## Official docs

- All recommended events: https://support.google.com/analytics/answer/9267735
- gtag/dataLayer event reference: https://developers.google.com/tag-platform/gtagjs/reference/events
- Custom dimensions: https://support.google.com/analytics/answer/10075209
- Audiences: https://support.google.com/analytics/answer/9267572
- Audience triggers: https://support.google.com/analytics/answer/9744267
- Key Events (renamed from Conversions): https://support.google.com/analytics/answer/9267568
- Google Ads link: https://support.google.com/analytics/answer/9379420
- Enhanced Conversions: https://support.google.com/google-ads/answer/13258081
- Reporting Identity: https://support.google.com/analytics/answer/10978788
- Data filtering / internal traffic: https://support.google.com/analytics/answer/10108813
- Attribution models: https://support.google.com/analytics/answer/10597962

## Related

- `gtm-setup.md` -- the install this file builds on
- `framework-integration.md` -- per-framework GTM placement
- `gdpr-compliance-eu.md` -- why Google Signals is disabled in EEA setups (the EU differentiator)
- `diagnostics-troubleshooting.md` -- when the events don't show up
