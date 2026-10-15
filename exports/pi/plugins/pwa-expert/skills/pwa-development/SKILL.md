---
name: pwa-development
description: >
  Progressive Web App architecture, service workers, offline storage, Web Push and cross-engine compatibility.
  TRIGGER WHEN: building or auditing PWAs: Web App Manifest, service workers, Workbox, Serwist, vite-plugin-pwa, Web Push/VAPID, OPFS, Background Sync, Project Fugu, TWA or Capacitor.
  DO NOT TRIGGER WHEN: React render performance (use react-development:review-react), general platform security (use platform-engineering), or Tauri/Electron shells (use tauri-development).
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

# Progressive Web App Development

Knowledge base for building, auditing, and shipping Progressive Web Apps in 2025-2026. Covers manifest, service workers, Web Push, install flows, storage, Project Fugu capabilities, platform constraints, performance (Core Web Vitals), security, and distribution to Google Play, Microsoft Store, App Store (via Capacitor), and Meta Quest.

## When to use this skill

Use this skill whenever the active task involves any of:
- A `manifest.webmanifest` or `manifest.json`, manifest members, icons, splash screens, iOS meta tags.
- A service worker file, registration, caching strategy, update flow, Workbox 7, Serwist.
- Web Push: VAPID keys, subscription, server-side delivery, Declarative Web Push.
- PWA install flow on Chromium (`beforeinstallprompt`), iOS (manual), or Window Controls Overlay on desktop.
- Background execution: Background Sync, Periodic Background Sync, Background Fetch, Screen Wake Lock.
- Storage: IndexedDB, OPFS, quotas, `navigator.storage.persist()`.
- Project Fugu APIs: File System Access, Web Share, Web Bluetooth / USB / HID / Serial / NFC, WebAuthn, etc.
- Performance for PWAs: Core Web Vitals 2025, INP < 200ms, app shell, code splitting.
- Security headers for PWAs: HTTPS, CSP tuned for SW, COOP / COEP for `SharedArrayBuffer`.
- Distribution: Bubblewrap to Google Play (TWA + `assetlinks.json`), PWA Builder to Microsoft Store (MSIX), Capacitor to App Store, PWA Builder to Meta Quest.
- Framework integration: Vite (`vite-plugin-pwa`), Next.js (`@serwist/next`), Angular (`ng add @angular/pwa`), Nuxt (`@vite-pwa/nuxt`).

Skip this skill if the task is generic frontend styling, generic React performance, cross-platform security unrelated to PWA mechanics, Tauri or Electron wrappers, or GA4 / analytics.

## References Library

Read the relevant reference on-demand for the active task. Do NOT preload all references at once; pick the one that matches the question.

| Reference | Topic |
|---|---|
| `references/manifest.md` | Web App Manifest: members, icons, splash, iOS meta tags |
| `references/service-workers.md` | SW lifecycle, caching strategies, Workbox 7, updates, debugging |
| `references/background-execution.md` | Background Sync, Periodic Sync, Background Fetch, Wake Lock |
| `references/push-notifications.md` | Web Push end-to-end: VAPID, RFCs, Declarative Push, Badge API |
| `references/install-flows.md` | beforeinstallprompt, iOS manual install, Window Controls Overlay |
| `references/permissions.md` | Permissions API, Permissions-Policy header, platform availability |
| `references/storage-persistence.md` | IndexedDB, OPFS, quotas, persistent storage |
| `references/capabilities-fugu.md` | Project Fugu API matrix and worked examples |
| `references/platform-constraints.md` | iOS / Android / Desktop per-platform reality check |
| `references/performance.md` | Core Web Vitals 2025, INP < 200ms, audit tooling |
| `references/security.md` | HTTPS, CSP for SW, COOP / COEP, secure contexts |
| `references/distribution.md` | Bubblewrap / TWA, PWA Builder MSIX, Capacitor, Meta Quest |
| `references/frameworks-tooling.md` | Vite, Next.js, Angular, Nuxt + debugging surface |
| `references/production-checklist.md` | Full deploy checklist for going to production |

## Decision quick-reference

| Question | Answer |
|---|---|
| Which SW caching strategy for hashed JS / CSS? | CacheFirst |
| Which for HTML navigation? | NetworkFirst with networkTimeoutSeconds: 3 |
| Which for avatars / low-criticality data? | StaleWhileRevalidate |
| Which for POST mutations? | NetworkOnly + BackgroundSyncPlugin |
| Should `skipWaiting()` be called by default? | No. Pair with a coordinated reload UX, or omit. |
| Minimum icon sizes for Chromium install? | 192 PNG + 512 PNG, both `purpose: "any"`. Add separate maskable assets. |
| Combine `"any maskable"` on one icon? | No. web.dev explicitly discourages it. |
| iOS Web Push: requirements? | iOS 16.4+, PWA installed to Home Screen, `display: standalone`, user-gesture-triggered subscribe. |
| Periodic Background Sync on iOS? | Not supported. Plan a degraded path. |
| Lighthouse PWA category? | Removed in Lighthouse 12.0.0 (Chrome 126, May 2024). Use individual Application-panel checks. |
| Next.js PWA library in 2026? | `@serwist/next` (not the unmaintained original `next-pwa`). |
