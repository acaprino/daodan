---
description: 'Generates manifest, service worker, iOS meta tags, registration code and icon stubs, detecting the framework in use. TRIGGER WHEN: scaffolding, bootstrapping or adding PWA support to a Vite, Next.js, Angular, Nuxt or vanilla project.'
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

# pwa-scaffold

<!-- Generated by the Daodan compiler for pi. Edit the kernel, never this file. -->

## Execution harness

Selected topology: **parallel-subagents**, with role delivery by **inline-prompt**, and declared
isolation **required**. Dispatch one worker per entry in the plan below with the `subagent`
tool supplied by the `pi-subagents` package, each in its own context. Role delivery here is
`inline-prompt`: paste that role's Markdown body into the dispatch prompt verbatim, because the
worker must receive the whole role rather than a summary of it.

Pi's core ships no subagent tool. If none is available in this session, the declared isolation
above decides what happens, and the two cases are not interchangeable:

- **`required`**: stop, and tell the user to run `pi install npm:pi-subagents`. Running the phases
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
- Workers may write only intermediate reports explicitly assigned by the coordinator.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `scope`: runs in the orchestrating context; produces `artifact:scope`.
2. `review`: one `pwa-architect` in an isolated context; needs `scope`; consumes `artifact:scope`; produces `artifact:pwa-scaffold-report`.

Role body bindings (load the complete body only for the selected worker):

- `pwa-architect`: read `skills/pwa-expert-pwa-architect/SKILL.md` inside this package and pass its complete body verbatim.

The phase graph and record-schema references are in `contracts/pwa-scaffold.workflow.toml`.

## Method

# /pwa-expert:pwa-scaffold

Scaffold a production-ready PWA into the current project. Delegate execution to `pwa-architect`. The agent reads the relevant references (`manifest.md`, `service-workers.md`, `frameworks-tooling.md`) on-demand.

## Framework detection

1. Parse `package.json` if present.
2. Look for `vite.config.*`, `next.config.*`, `angular.json`, `nuxt.config.*` in the project root.
3. If `$ARGUMENTS` is provided, use it (one of: `vite`, `next`, `angular`, `nuxt`, `vanilla`).
4. If detection is ambiguous, ask the user through the active host question mechanism which framework to target.

## Inputs to collect

Before generating files, use the active host question mechanism to gather:

1. App name (full): used for manifest `name`. Example: "Acme Productivity Suite".
2. App name (short): used for manifest `short_name` and the iOS meta `apple-mobile-web-app-title`. Example: "Acme".
3. Description: used for manifest `description`.
4. Theme color (hex): used for manifest `theme_color` and the `<meta name="theme-color">`. Default: `#0f172a`.
5. Background color (hex): used for manifest `background_color` and Android splash. Default: `#ffffff`.
6. Two primary shortcuts (name + URL each): for manifest `shortcuts`. Defaults can be skipped if the user does not have them yet.

## Idempotency

Before writing each file, check if it exists. If it does, show a diff and ask through the active host question mechanism whether to overwrite, merge, or skip. Never silently overwrite an existing manifest or SW.

## Generated artifacts (per framework)

### Vite (vite-plugin-pwa)

- `public/manifest.webmanifest` with the full set of members per `manifest.md` (id, display_override, icons any+maskable, screenshots wide+narrow, shortcuts).
- `vite.config.ts` (or `.js`): add the `VitePWA` plugin from `vite-plugin-pwa` with `registerType: 'prompt'`, `strategies: 'generateSW'`, manifest reference, `workbox.runtimeCaching` with the four canonical strategies (CacheFirst for hashed assets, NetworkFirst for navigation with `networkTimeoutSeconds: 3`, StaleWhileRevalidate for low-criticality data, NetworkOnly + BackgroundSyncPlugin for POST mutations). If `vite.config.*` already exists, modify it in-place through the host repository-edit binding. Never overwrite.
- `index.html`: insert the iOS meta tag block plus `<link rel="manifest" href="/manifest.webmanifest" crossorigin="use-credentials">` and `<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">`.
- Registration: `vite-plugin-pwa` provides `virtual:pwa-register`. Add `import { registerSW } from 'virtual:pwa-register'` and the workbox-window banner pattern (see `service-workers.md`) in `src/main.ts(x)`.
- `public/icons/README.md`: explain the icon requirements (192+512 PNG `any`, 192+512 PNG `maskable`, 180x180 opaque `apple-touch-icon.png`, optional SVG `any`). Include the 40 percent safe-zone rule for maskable icons.
- `public/icons/`: empty stub files (`icon-192.png`, `icon-512.png`, `icon-maskable-192.png`, `icon-maskable-512.png`, `apple-touch-icon.png`) as 0-byte placeholders to make the manifest valid before real icons are supplied.

### Next.js (@serwist/next)

- `app/manifest.ts` (Next.js 14+) returning a `MetadataRoute.Manifest` with the full member set.
- `app/sw.ts` using Serwist (full example from `frameworks-tooling.md` §"Next.js via @serwist/next").
- `next.config.*`: add the `@serwist/next` plugin wrapper.
- `app/layout.tsx`: add the iOS meta tag block via the `<head>` (using `<meta name="apple-mobile-web-app-capable" content="yes" />` etc.). Add `<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />`.
- Registration: Serwist exposes the `@serwist/next` registration helper. Wire it in `app/layout.tsx`.
- `public/icons/` stubs and `README.md` as above.

### Angular (ng add @angular/pwa)

- Run `ng add @angular/pwa --project <project-name>` through the host shell binding. This schematic creates the manifest, the SW, registration, and `ngsw-config.json`.
- After the schematic completes, edit `src/manifest.webmanifest` to include the modern members (id, display_override, icons any+maskable, screenshots, shortcuts) that the schematic does not generate by default.
- Edit `src/index.html` to add the iOS meta tag block plus `apple-touch-icon`.
- Edit `ngsw-config.json` to add a `dataGroups` entry with strategy `freshness` for API origins.

### Nuxt (@vite-pwa/nuxt)

- Install `@vite-pwa/nuxt` and add it to `nuxt.config.ts` `modules`.
- Configure the module with the same manifest and workbox config as the Vite case.
- Add the iOS meta tag block via `app.head` in `nuxt.config.ts`.
- `public/icons/` stubs and `README.md`.

### Vanilla

- `manifest.webmanifest` in the project root.
- `sw.js` in the project root (Workbox 7 patterns hand-written, full example from `service-workers.md`).
- `index.html` updated with the manifest link, the iOS meta tag block, and an inline registration script.
- `icons/` stubs.

## Always-emitted documentation

In addition to the framework artifacts, always create:

- `headers-recommendations.md` in the project root. Documents recommended HSTS, CSP (the example from `security.md`), Permissions-Policy, COOP, COEP, plus `Cache-Control: no-cache` for the service worker file. Each header is explained with a one-line rationale. This file is NOT auto-applied to deploy config given framework and host variance.
- A short "Next steps" message in the chat: open the manifest in DevTools Application panel, replace the icon stubs with real icons, generate `apple-touch-startup-image` for the target devices (suggest `pwa-asset-generator`), run `/pwa-expert:pwa-checklist` once the app is wired up.

## What this command does NOT do

- Does not generate Capacitor or Cordova projects. Out of scope; documented in `distribution.md`.
- Does not generate a push notification server. The `push-notifications.md` reference contains a full Node example; users copy it into their own backend.
- Does not auto-apply security headers to deploy config. Too framework-specific and host-specific to do safely; documented in `headers-recommendations.md` instead.
