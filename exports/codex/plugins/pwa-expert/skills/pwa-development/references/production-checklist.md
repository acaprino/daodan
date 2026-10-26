<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
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

# Production Deployment Checklist

Field-tested checklist for shipping a Progressive Web App to production in 2025-2026. Walk this before every release. Each item has a verification step and a reference to the relevant section of the knowledge base.

## How to use this checklist

Three pass criteria:

- **PASS**: requirement is met and verified.
- **FAIL**: requirement is unmet and ships a defect.
- **N/A**: requirement does not apply to this target platform.

The `/pwa-expert:pwa-checklist` command walks this list interactively against a codebase (and optionally a deployed URL) and produces a deterministic pass/fail dashboard. The `/pwa-expert:pwa-audit` command runs an open-ended adversarial audit instead; use this checklist when you want a structured release gate, the audit when you want to find defects the checklist does not enumerate.

## 1. Manifest

- [ ] `id` is explicit (not implied from `start_url`). See `manifest.md`.
- [ ] `name`, `short_name`, `description`, `start_url`, `scope` all present.
- [ ] `display: "standalone"` plus `display_override` including `window-controls-overlay` when desktop is a target.
- [ ] `theme_color` and `background_color` set.
- [ ] Icons: 192 PNG `purpose: "any"`, 512 PNG `purpose: "any"`, 192 PNG `purpose: "maskable"`, 512 PNG `purpose: "maskable"`. SVG `purpose: "any"` optional.
- [ ] Screenshots include at least one `form_factor: "wide"` and one `form_factor: "narrow"`.
- [ ] `shortcuts` defines at least two primary actions.
- [ ] `share_target` defined if the app accepts shared content.
- [ ] `lang` and `dir` set.
- [ ] Served with `Content-Type: application/manifest+json`.

## 2. iOS-specific

- [ ] `<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">` (opaque PNG, no transparency).
- [ ] `<meta name="apple-mobile-web-app-capable" content="yes">`.
- [ ] `<meta name="apple-mobile-web-app-status-bar-style">` set (typically `black-translucent`).
- [ ] `<meta name="apple-mobile-web-app-title">` set.
- [ ] `apple-touch-startup-image` declared for each target device combination (width, height, pixel ratio, orientation).
- [ ] Custom "Add to Home Screen" hint shown only when `display-mode: browser` matches.
- [ ] Web Push tested only after install plus an explicit user gesture (iOS 16.4+ requirement).
- [ ] `viewport-fit=cover` plus `env(safe-area-inset-*)` CSS used for layout safety.

## 3. Service Worker

- [ ] `/sw.js` (or framework equivalent) served from the root with `Cache-Control: no-cache`.
- [ ] App-shell pre-cache uses a versioned cache name (the `app-shell-v7` pattern).
- [ ] Distinct runtime strategies for asset, API, and navigation routes.
- [ ] Old caches cleaned up in the `activate` event.
- [ ] User-driven update flow with an "Update now" banner. No silent `skipWaiting()`.
- [ ] Offline fallback page exists and is precached.

## 4. Security

- [ ] HTTPS with HSTS (`max-age=31536000; includeSubDomains; preload`).
- [ ] Restrictive CSP that covers `script-src`, `worker-src`, `connect-src`, `img-src`, `object-src`, `base-uri`, `frame-ancestors`.
- [ ] `Permissions-Policy` header restricts capabilities for third-party iframes.
- [ ] CORS correctly configured on every API origin the SW or page calls.
- [ ] COOP + COEP if `SharedArrayBuffer` is needed (for example, sqlite-wasm on OPFS).

## 5. Performance

- [ ] LCP < 2.5 s at p75.
- [ ] INP < 200 ms at p75.
- [ ] CLS < 0.1 at p75.
- [ ] Critical JS bundle < 170 KB compressed.
- [ ] `fetchpriority="high"` on the LCP image.
- [ ] Route-based code splitting.
- [ ] HTTP/2 or HTTP/3 with Brotli or Zstd compression.

## 6. Push

- [ ] VAPID keys generated and stored in a secret manager.
- [ ] Subscription endpoint with automatic cleanup (HTTP 410 deletes the row).
- [ ] `userVisibleOnly: true` set in the client subscription.
- [ ] `notificationclick` handler with focus-existing or open-window logic.
- [ ] Tested on installed iOS PWA, Android Chrome, and Desktop Chrome or Edge.

## 7. Storage

- [ ] `navigator.storage.estimate()` monitored.
- [ ] `navigator.storage.persist()` requested after a meaningful engagement event (not at page load).
- [ ] IndexedDB cleanup logic exists for quota pressure.
- [ ] Fallback strategy documented for Safari ITP 7-day cap on non-installed PWAs.

## 8. Testing

- [ ] Lighthouse individual PWA audits in CI. The PWA category itself was removed in Lighthouse 12.0.0 (Chrome 126), so audit the individual checks from the Application panel.
- [ ] PWA Builder score >= 80.
- [ ] Real offline test performed (DevTools "Offline" plus a full reload of a non-cached page).
- [ ] Tested on a physical iPhone. Safari Web Inspector cannot inspect installed Home Screen PWAs, so an in-app diagnostic fallback is wired in (Eruda or a hidden tap sequence).
- [ ] Install tested on Android (WebAPK) and Desktop Chrome or Edge.
- [ ] Update flow tested end-to-end (deploy version 2, confirm the banner appears, confirm the reload picks up the new SW).

## 9. Distribution

- [ ] Bubblewrap to Google Play with a valid `/.well-known/assetlinks.json`. Without it, the TWA degrades to a Custom Tab with a visible URL bar.
- [ ] PWA Builder to Microsoft Store (MSIX package via Partner Center).
- [ ] Capacitor wrapper for the App Store if a web-only distribution is not acceptable. Apple Guideline 4.2.2 rejects pure web clippings.

## 10. Monitoring

- [ ] `appinstalled` event sent to analytics.
- [ ] CrUX or RUM tracking the three Core Web Vitals.
- [ ] Sentry or equivalent error tracking inside the service worker.
- [ ] Heartbeat handler for `pushsubscriptionchange`.
