---
description: 'Checks manifest, install criteria, offline behavior, security headers and performance, locally or against a live URL, citing file and line. TRIGGER WHEN: auditing a PWA, or verifying one is installable and production-ready.'
---

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

# pwa-audit

<!-- Generated by the Daodan compiler for pi. Edit the kernel, never this file. -->

## Execution harness

Selected topology: **parallel-subagents**, with role delivery by **inline-prompt**, and declared
isolation **required**. Dispatch one worker per entry in the plan below with the `subagent`
tool supplied by the `pi-subagents` package, each in its own context. Role delivery here is
`inline-prompt`: paste that role's Markdown body into the dispatch prompt verbatim, because the
worker must receive the whole role rather than a summary of it.

Pi's core ships no subagent tool. Apply the availability check when the selected task
requires a dispatched worker. If the method explicitly permits a worker-free path
(for example, read-only inspection or a narrow edit), record why no worker is needed
and continue that path without this companion. Do not waive a required worker.
If a worker is needed and no subagent tool is available, the declared isolation
above decides what happens, and the two cases are not interchangeable:

- **`required`**: stop the dependent dispatch, and tell the user to run `pi install npm:pi-subagents`. Running the phases
  serially in this one context is the loss of isolation rather than a lesser form of it, so a
  report produced that way would claim a contract it did not meet.
- **`shared`**: run the phases in order in this context, and say in the report that no worker was
  isolated.

Coordinator completion ownership: keep the method's owned run and delivery ledger,
including each expected worker, attempt, report path and required check evidence.
Validate report artifacts before recording delivered. An empty final message or
worker stop remains missing delivery: inspect or resume when permitted, otherwise
record failed with the uncovered scope. Follow the declared join and phase gates;
a recorded failure is accounted for, never converted into a successful delivery.
Continue authorized work and recovery until the requested result and its checks
exist or a concrete blocker is recorded. Preserve the exclusive final report owner
and the ledger schema; a tool exit or a promise cannot satisfy completion.

Harness obligations, none of them optional:

- Every dispatched worker runs in its own context and reads only coordinator-declared inputs.
  Independent reviewers never read peer results before their own delivery.
- Follow the dispatch plan below in phase order. A phase starts only after every phase it needs has
  closed, and a phase closes only when every worker it dispatched is recorded `delivered` or
  `failed`. A worker reports delivered or failed in its final message; there is no shared task
  list, so the coordinator keeps that record itself.
- Dispatch only roles from this set, as the phase graph or loaded method requires: `pwa-architect`
- A worker writes only what the coordinator assigned to it: its intermediate report and, when its
  task authorizes edits, its assigned files. It never reverts preexisting or foreign changes.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `scope`: runs in the orchestrating context; produces `artifact:scope`.
2. `review`: one `pwa-architect` in an isolated context; needs `scope`; consumes `artifact:scope`; produces `artifact:pwa-audit-report`.

Role body bindings (load the complete body only for the selected worker):

- `pwa-architect`: read `skills/pwa-expert-pwa-architect/SKILL.md` inside this package and pass its complete body verbatim.

The phase graph and record-schema references are in `contracts/pwa-audit.workflow.toml`.

## Method

# /pwa-expert:pwa-audit

Adversarial PWA audit. Two modes, auto-detected from `$ARGUMENTS`:

- **Live URL mode:** if the argument starts with `http://` or `https://`, fetch the page with Playwright, parse the manifest, test install criteria, check security headers, test offline behavior, and measure Core Web Vitals on the landing page.
- **Local code mode:** otherwise, treat the argument as a path (default: current working directory). Locate the manifest file, service worker source, registration call, iOS meta tag block, and security-header configuration in the codebase. Parse and check.

## Setup

Delegate this audit to the `pwa-architect` agent. The agent must read the relevant references from the `pwa-development` skill on-demand (not all upfront), targeting each section of the audit.

Reference reading order, as audit sections are reached:

- Manifest checks: `references/manifest.md`, `references/production-checklist.md` §1.
- Install criteria and prompts: `references/install-flows.md`.
- Service worker logic: `references/service-workers.md`.
- Security headers: `references/security.md`.
- Offline behavior: `references/service-workers.md` and `references/storage-persistence.md`.
- Performance metrics: `references/performance.md`.
- Push notifications: `references/push-notifications.md`.
- Framework-specific files: `references/frameworks-tooling.md`.

## Mode A: Live URL

If `$ARGUMENTS` is a URL, use the Playwright MCP tools of the `playwright` plugin (Microsoft's Playwright MCP server, a declared dependency):

1. Open the URL with `browser_navigate`.
2. Fetch `/manifest.webmanifest` (and fall back to `/manifest.json`). Validate as JSON. Run the manifest checklist from `production-checklist.md` §1.
3. Check the service worker registration: look for a `<script>` registering `navigator.serviceWorker.register(...)`, or for an existing controller via `navigator.serviceWorker.controller`.
4. Check the install criteria from `install-flows.md`: manifest valid, `display` not `browser`, SW registered with `fetch` handler, HTTPS, 192+512 PNG icons present.
5. Check meta tags: `apple-mobile-web-app-capable`, `apple-mobile-web-app-status-bar-style`, `apple-mobile-web-app-title`, `apple-touch-icon`, `theme-color`, `viewport`.
6. Check security headers via response headers: HTTPS plus HSTS, CSP presence (warn if `'unsafe-eval'` is allowed), `Cross-Origin-Opener-Policy`, `Cross-Origin-Embedder-Policy`.
7. Test offline behavior with `browser_run_code_unsafe`: `async (page) => { await page.context().setOffline(true); await page.reload(); return await page.content(); }`, then confirm a non-broken response (offline page or cached navigation) and set the context back online.
8. Measure Core Web Vitals on the landing page (LCP, CLS at least; INP requires interaction). Compare against `performance.md` thresholds.

If the Playwright MCP tools are unavailable, stop and tell the user to install Microsoft's Playwright MCP server for the host: on Claude Code `claude plugin install playwright@claude-plugins-official`; on Codex, VS Code, Copilot CLI, Pi or OpenCode, register `npx @playwright/mcp@latest` as the MCP server `playwright` (the exact command for each host is in the Browser automation section of the Daodan README). It is a declared dependency; a live audit without a browser is not run. Mode B (a local codebase) needs no browser.

Live-mode auth note: if the target URL is behind authentication, ask the user, with a user question, whether to run the audit against a public route only, or whether the user can provide login steps. Never attempt to bypass auth.

## Mode B: Local code

If `$ARGUMENTS` is a path or omitted, search the codebase:

1. Find the manifest: file discovery for `manifest.webmanifest`, `manifest.json`, `app/manifest.ts` (Next.js 14+), `src/manifest.ts`. Parse and verify against `production-checklist.md` §1.
2. Find the SW source: file discovery for `sw.js`, `sw.ts`, `service-worker.js`, `service-worker.ts`, `app/sw.ts` (Serwist), `ngsw-config.json` (Angular). Read and audit caching strategies, `skipWaiting` / `clients.claim` use, cleanup in `activate`, offline fallback.
3. Find the SW registration: content search for `serviceWorker.register`, `workbox-window`, `Workbox(`, `Serwist(`, or Next.js implicit registration via `@serwist/next`.
4. Find iOS meta tags: content search for `apple-mobile-web-app-capable`. Confirm the full block from `manifest.md` §"iOS meta tag block".
5. Find security headers: read `next.config.*` (Next.js headers function), `vite.config.*` plus any `server` plugin, `nginx.conf` / `.htaccess` if present, `firebase.json` `hosting.headers`, `vercel.json` `headers`. Check HSTS, CSP, COOP, COEP, Permissions-Policy.
6. Find Web Push: content search for `pushManager.subscribe`, `setVapidDetails`, `web-push`. If found, audit the subscription flow and server-side delivery against `push-notifications.md`.
7. Find storage usage: content search for `localStorage.`, `IDBDatabase`, `openDB(`, `navigator.storage`. Flag anti-patterns from `storage-persistence.md` (for example, `localStorage` used for large data).
8. Detect framework via `package.json` and configs. Apply framework-specific checks from `frameworks-tooling.md` (Vite vite-plugin-pwa config, Serwist app/sw.ts, Angular ngsw-config.json structure).

If the codebase contains a build artifact directory (`dist/`, `.next/`, `build/`), do not audit the generated SW from there. Always work from source. Generated SW files are derivative and may be stale relative to config.

## Common defects to look for

Patterns the audit should treat as Critical until proven otherwise:

- A service worker that calls `self.skipWaiting()` without a coordinated client reload. Causes mid-session resource version mismatches and broken navigations.
- A `cache.addAll([...])` precache list with no version suffix or hash strategy. Caches go stale forever after first install.
- An offline fallback page that itself fetches uncached subresources. The fallback fails open in network outages.
- A manifest with `display: "standalone"` but no maskable icon at 192 and 512. Android adaptive launchers fall back to a generated badge.
- A CSP that includes `'unsafe-inline'` for `script-src` in production. Treat as Critical unless paired with a nonce or hash strategy.
- Web Push subscriptions persisted without `expirationTime` handling or a server-side resubscribe path. Silent delivery failures accumulate.

Patterns to flag as Important:

- A service worker fetch handler that calls `event.respondWith(fetch(event.request))` unconditionally. Adds latency for zero caching benefit.
- A manifest `start_url` lacking a tracking parameter (for example `?source=pwa`). Analytics cannot distinguish installed-app sessions.
- An `apple-touch-icon` smaller than 180×180 or with transparency. iOS renders a black background on the Home Screen.

## Output

Write a markdown report to stdout (or a file if the user asked) with this structure:

```
# PWA Audit Report

**Target:** <path or URL>
**Mode:** <local | live>
**Date:** YYYY-MM-DD

## Summary

<one paragraph: overall posture, biggest risks>

## Critical findings

### C1: <short title>
- **Location:** <file:line> or <URL fragment>
- **Issue:** <one sentence>
- **Impact:** <one sentence>
- **Fix:** <concrete change with code if applicable>
- **Reference:** `references/<file>.md` §<heading>

## Important findings

(same format)

## Nice-to-have findings

(same format)

## Verified passes

(short list of categories where the implementation is correct)
```

Severity buckets:

- **Critical:** ships a defect (install will fail; Web Push will not deliver on iOS; SW will not update; CSP allows XSS; missing HTTPS).
- **Important:** degrades the experience (no maskable icons; `skipWaiting()` without coordinated reload; no offline fallback; INP > 200ms at p75).
- **Nice-to-have:** polish (no Window Controls Overlay; no scope_extensions; no shortcuts beyond the minimum).

For each finding, cite the file and line in local mode, or the URL plus the manifest field or DOM selector in live mode.

Numbering convention: `C1, C2, ...` for Critical, `I1, I2, ...` for Important, `N1, N2, ...` for Nice-to-have. Stable IDs let the user reference findings in follow-up prompts.

Fix guidance must be concrete. Prefer a code snippet or an exact path-and-value change over a vague "consider improving this". If the fix is large, link to the relevant reference section and summarize the first concrete step.

## iOS caveat

If the target is iOS-focused, prepend the report with a clear note that Safari Web Inspector cannot inspect installed Home Screen PWAs. Live-mode audit therefore covers only the in-browser experience, not the post-install standalone state.

Concrete consequence: behaviors that only manifest once the app is added to the Home Screen (standalone display, status bar styling, safe-area insets, splash screens, Web Push permission in iOS 16.4+) cannot be observed remotely. Recommend that the user run a manual install-and-launch pass on a real iOS device, ideally on the lowest supported iOS version in their target matrix.

If the user has access to a Mac plus a wired iOS device, recommend the desktop Safari "Develop" menu attached to the in-Safari tab. This is the closest available approximation to inspecting the installed app but still does not reach the installed standalone surface.
