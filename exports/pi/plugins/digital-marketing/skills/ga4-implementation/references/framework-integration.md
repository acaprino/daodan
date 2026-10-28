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

# Framework integration patterns

How to install GTM + the Consent Mode v2 default block correctly per framework. The framework-specific code samples (Next.js App vs Pages Router, React Router, etc.) live upstream; this file is the ordering rules and the gotchas that actually break installations.

## When to use

Installing GTM in a Next.js / React / WordPress / static-site / SSR-app codebase. For the snippet content itself and the `<head>` ordering rationale, see `gtm-setup.md`. For the EU compliance layer that must precede this, see `gdpr-compliance-eu.md`.

## The non-negotiable rule (every framework)

Order in `<head>`, top to bottom:

1. **Consent Mode v2 default block** (sets all signals to `denied`, `wait_for_update: 500`)
2. **CMP loader** (iubenda embed, Cookiebot autoblock script, Orestbida config)
3. **GTM head snippet**

The GTM noscript iframe goes immediately after `<body>`, never inside `<head>`.

## Per-framework cheat sheet

### Next.js App Router (13.4+)

Use `@next/third-parties/google`:

```bash
npm install @next/third-parties
```

```tsx
import { GoogleTagManager } from '@next/third-parties/google';
// In app/layout.tsx <html>...<GoogleTagManager gtmId="GTM-XXXXXXX" /></html>
```

For the Consent Mode v2 default block, use `next/script` with `strategy="beforeInteractive"` in the root layout (`app/layout.tsx`), placed BEFORE `<GoogleTagManager>`. The App Router supports `beforeInteractive` from the root layout only; in any other layout, page, or component it is silently downgraded and loses the race with GTM. Fallback when the root layout is not available: a plain inline `<script>` in `<head>`, which also runs first.

For SPA route changes, GA4 page_view fires automatically when the GTM Google Tag uses `Initialization - All Pages`. For finer control, push `dataLayer` page_view events from a `usePathname()` + `useEffect()` client component.

Docs: https://nextjs.org/docs/app/building-your-application/optimizing/third-party-libraries

### Next.js Pages Router

Use `next/script` in `pages/_document.tsx` for the Consent Mode default with `strategy="beforeInteractive"` (the only Pages Router location where `beforeInteractive` works), and another `<Script strategy="afterInteractive">` for the GTM head snippet. The noscript iframe goes in the `<body>` JSX with `style={{display:'none', visibility:'hidden'}}`.

For SPA routing, listen to `Router.events.routeChangeComplete` in `pages/_app.tsx` and push `page_view` to dataLayer.

Docs: https://nextjs.org/docs/pages/api-reference/components/script

### React (CRA, Vite, non-Next)

Snippet directly in `public/index.html` (CRA) or `index.html` (Vite). Same head-order rules.

For React Router SPAs, use `useLocation()` in a `<PageViewTracker />` mounted once inside `<BrowserRouter>` and push `page_view` to `dataLayer` on location change.

### WordPress

Three paths:

- **Approach A (technical)**: `add_action('wp_head', ..., 1)` + `add_action('wp_body_open', ...)` in a child theme's `functions.php`. Priority `1` ensures early execution. `wp_body_open` was added in WP 5.2 -- older themes need a `header.php` edit.
- **Approach B (simple)**: edit `header.php` directly. Works but fragile -- theme updates can overwrite. Use a child theme.
- **Approach C (non-technical)**: Site Kit by Google (limited but guided), GTM4WP (most powerful, dataLayer for WooCommerce / CF7 / Gravity / scroll / video), or a CMP plugin (Complianz, iubenda WP) that handles the entire installation. **The CMP plugin and GTM plugin must be coordinated** so the CMP fires Consent Mode v2 updates that GTM listens for.

### SSR apps (Rails, Django, Laravel)

Insert in the base layout template (`application.html.erb`, `base.html`, `app.blade.php`). Same head-order rules. For Hotwire/Turbo/Inertia/Livewire SPAs, listen to the equivalent of `turbo:load` and push virtual `page_view` events.

### Static site generators

Most have a layout/partial system: Jekyll `_includes/head.html`, Hugo `layouts/partials/head.html` (also has built-in `{{ template "_internal/google_tag_manager.html" . }}`), Eleventy `_includes/layout.njk`, Astro `src/layouts/Layout.astro`, Gatsby `gatsby-plugin-google-tagmanager` in `gatsby-config.js`.

After every build, **verify with grep**:

```bash
grep -l "GTM-XXXXXXX" public/**/*.html
```

If a file is missing, the layout was not applied uniformly.

## Gotchas (the real production bites)

- **WordPress caching plugins strip the GTM snippet.** W3 Total Cache, WP Rocket, LiteSpeed, WP Super Cache -- especially with HTML minification or "delay JavaScript execution" turned on. Symptom: works in admin/preview but not in incognito on the live front-end. Fix: flush cache, add `googletagmanager.com` + `gtm.js` to the "do not minify" / "exclude from delay" list. **Always re-verify after enabling/updating any cache plugin.**
- **`strategy="beforeInteractive"` only works at the root of the document tree.** Pages Router: `pages/_document.tsx`. App Router: the root `app/layout.tsx`. Anywhere else (a nested layout, a page, a client component) Next silently downgrades it, and the Consent Mode default then loses its race with GTM.
- **React Strict Mode double-fires `page_view` in development only.** Effects run twice in dev, prod is fine. Verify with DebugView in **production**, not local dev.
- **Hydration mismatch warnings (Next.js, React)** come from `dangerouslySetInnerHTML` differing between server and client. Use `next/script` or `@next/third-parties/google` -- never raw inline `<script>` for GTM in components.
- **Static export (`next export`)** works with GTM via the same `next/script` patterns. After export, grep the output to confirm the snippet is in every HTML file.
- **Multi-property / multi-container in one project** = data corruption guaranteed. One property and one container per environment; environments are separated via GTM Environments (auth params), not by mixing IDs.
- **Hugo / Astro / Gatsby integrations** can ship without Consent Mode v2 defaults out of the box -- always verify the head order is right after enabling the integration. The integration's "GTM container ID" field is just a convenience; the consent ordering is your responsibility.

## Server-side GTM (sGTM)

Out of scope. Separate Google Cloud deployment that proxies through a first-party domain. Worth it for high-traffic sites with privacy engineering requirements; overkill for most small-business deployments.

Docs: https://developers.google.com/tag-platform/tag-manager/server-side

## Official docs

- `@next/third-parties` (Google integrations): https://nextjs.org/docs/app/building-your-application/optimizing/third-party-libraries
- `next/script` strategies: https://nextjs.org/docs/app/api-reference/components/script
- React Router (`useLocation`): https://reactrouter.com/en/main/hooks/use-location
- WordPress action hooks (`wp_head`, `wp_body_open`): https://developer.wordpress.org/reference/hooks/wp_head/
- GTM4WP plugin: https://gtm4wp.com/
- Site Kit by Google: https://wordpress.org/plugins/google-site-kit/
- Hugo internal GTM template: https://gohugo.io/templates/internal/#google-tag-manager
- Astro Google Analytics integration: https://github.com/codiume/orbit/tree/main/packages/astro-google-analytics
- Gatsby GTM plugin: https://www.gatsbyjs.com/plugins/gatsby-plugin-google-tagmanager/

## Related

- `gtm-setup.md` -- the snippet content + `<head>` ordering rationale
- `events-and-conversions.md` -- the events these snippets enable measuring
- `gdpr-compliance-eu.md` -- EU compliance layer that comes before any of this
- `diagnostics-troubleshooting.md` -- when the install seems wrong, run this checklist
