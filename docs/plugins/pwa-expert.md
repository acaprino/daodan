# PWA Expert Plugin

> Progressive Web App design, scaffolding, and auditing for the 2025-2026 baseline: Web App Manifest, Service Workers (Workbox 7, Serwist), Web Push (VAPID, Declarative Push for Safari 18.4+), install flows, OPFS storage, Project Fugu APIs, Core Web Vitals (INP < 200ms), framework integration (Vite, Next.js, Angular, Nuxt), and store distribution (Bubblewrap, PWA Builder, Capacitor).

Command examples and named tools in this guide use Claude notation. For other
hosts, use the entry points and bindings in the source-derived reference below
and [host setup](../hosts.md).

## Agents

### `pwa-architect`

Expert architect for Progressive Web Apps. Designs and implements complete PWAs end-to-end: manifest, service worker, Web Push, install flow, storage, framework integration, and store distribution. Reasons about platform asymmetry (Chromium full support, iOS WebKit constrained, Firefox partial) and applies progressive enhancement rather than assuming feature parity.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch |
| **Use for** | Building or auditing PWAs, manifests, service workers, push pipelines, install flows, OPFS storage, framework-specific PWA integration, store distribution |

**Invocation:**
```
Use the pwa-architect agent to build/audit [PWA feature or codebase]
```
Also delegated to by all three commands below.

**Workflow:** target platforms first (which of Chromium desktop, Android Chrome, iOS Safari, desktop Safari, Firefox does the user need, and what constraints follow), then manifest design, service-worker strategy per route type, a push plan only if it adds user-visible notifications, install UX per platform, storage design, a distribution plan, and a production-checklist gate before shipping. Every deliverable cites the reference file backing the recommendation.

**Routing:** stays within PWA mechanics. Generic frontend styling and design-system work is out of its scope (for a design and UX review, use `/frontend-review:review-frontend`). It hands off React-specific performance to `/react-development:review-react`, cross-platform security beyond PWA mechanics to `/platform-engineering:platform-review`, Tauri/Electron wrapping to `tauri-development`, GA4/analytics to `digital-marketing:ga4-implementation-expert`, and Stripe integration to `stripe:stripe-integrator`.

---

## Skills

### `pwa-development`

Knowledge base for building, auditing, and shipping PWAs in 2025-2026, loaded automatically by `pwa-architect` and referenced on-demand (never preloaded in bulk).

**Reference files:**
- `manifest.md`: Web App Manifest members, icons, splash screens, iOS meta tags
- `service-workers.md`: SW lifecycle, caching strategies, Workbox 7, updates, debugging
- `background-execution.md`: Background Sync, Periodic Sync, Background Fetch, Wake Lock
- `push-notifications.md`: Web Push end-to-end: VAPID, RFCs, Declarative Push, Badge API
- `install-flows.md`: `beforeinstallprompt`, iOS manual install, Window Controls Overlay
- `permissions.md`: Permissions API, `Permissions-Policy` header, platform availability
- `storage-persistence.md`: IndexedDB, OPFS, quotas, persistent storage
- `capabilities-fugu.md`: Project Fugu API matrix and worked examples
- `platform-constraints.md`: iOS / Android / Desktop per-platform reality check
- `performance.md`: Core Web Vitals 2025, INP < 200ms, audit tooling
- `security.md`: HTTPS, CSP for service workers, COOP / COEP, secure contexts
- `distribution.md`: Bubblewrap / TWA, PWA Builder MSIX, Capacitor, Meta Quest
- `frameworks-tooling.md`: Vite, Next.js, Angular, Nuxt wiring plus debugging surface
- `production-checklist.md`: full deploy checklist consumed directly by `/pwa-expert:pwa-checklist`

**Decision quick-reference table** answers common either/or questions inline (which caching strategy per route type, minimum icon sizes, whether to call `skipWaiting()` by default, iOS Web Push requirements) so the agent doesn't have to open a reference file for a one-line lookup.

---

## Commands

### `/pwa-expert:pwa-audit`

Adversarial PWA audit. Auto-detects mode from the argument: a URL triggers live-mode auditing via the Playwright MCP tools (manifest fetch, install-criteria check, security headers, offline behavior, Core Web Vitals); a path or omitted argument triggers local-code mode (locates and reads the manifest, service worker, registration call, iOS meta tags, and header config in source).

```
/pwa-expert:pwa-audit                    # local code mode, current directory
/pwa-expert:pwa-audit src/               # local code mode, specific path
/pwa-expert:pwa-audit https://example.com  # live URL mode via Playwright
```

Findings are numbered `C1, C2, ...` (Critical), `I1, I2, ...` (Important), `N1, N2, ...` (Nice-to-have) so they stay referenceable across follow-up prompts. Live mode runs on the Playwright MCP tools of `playwright@claude-plugins-official` (Microsoft's Playwright MCP server), a hard dependency of this plugin (on Claude Code `claude plugin install playwright@claude-plugins-official`; on Codex, Copilot and Pi see the per-host table in the README's [Browser automation](../../README.md#browser-automation-playwright) section); without them the command stops rather than auditing a live site without a browser. Notes upfront that Safari Web Inspector cannot inspect installed Home Screen PWAs, so live-mode results don't cover the post-install standalone experience.

---

### `/pwa-expert:pwa-scaffold`

Scaffolds a production-ready PWA into the current project: manifest, service worker, iOS meta tags, registration code, icon stubs, and a headers-recommendations doc. Detects the framework (Vite, Next.js, Angular, Nuxt, or vanilla) from `package.json` and config files, or accepts it as an argument.

```
/pwa-expert:pwa-scaffold          # auto-detect framework
/pwa-expert:pwa-scaffold next     # force Next.js (@serwist/next)
```

Collects app name, short name, description, theme/background colors, and up to two manifest shortcuts via `AskUserQuestion` before generating files. Never silently overwrites an existing manifest or service worker: shows a diff and asks whether to overwrite, merge, or skip. Does not generate a Capacitor/Cordova project, a push-notification server, or auto-apply security headers to deploy config; each of those is documented instead (`distribution.md`, `push-notifications.md`, `headers-recommendations.md`).

---

### `/pwa-expert:pwa-checklist`

Walks the production deploy checklist from `production-checklist.md` interactively against the codebase (or a live URL) and reports **PASS** / **FAIL** / **N/A** per item with a per-category summary table. Deterministic by design: two runs against the same target produce a structurally identical report, which makes it suitable as a CI release gate (unlike `/pwa-expert:pwa-audit`, which is open-ended and adversarial).

```
/pwa-expert:pwa-checklist                    # walk against current codebase
/pwa-expert:pwa-checklist https://example.com  # walk against a live deployment
```

Every **FAIL** links back to the matching reference file for self-service remediation. Use `/pwa-expert:pwa-checklist` for release gates and CI integration; use `/pwa-expert:pwa-audit` for design reviews and pre-launch deep-dives.

---

**Related:** [platform-engineering](platform-engineering.md) (cross-platform security/architecture/performance beyond PWA mechanics) | [react-development](react-development.md) (React-specific performance) | [tauri-development](tauri-development.md) (desktop/mobile native wrappers) | `playwright@claude-plugins-official` (Microsoft's Playwright MCP server and a hard dependency, used by the live-URL modes of the audit and checklist commands; on Claude Code `claude plugin install playwright@claude-plugins-official`, on Codex, Copilot and Pi see the per-host table in the README's [Browser automation](../../README.md#browser-automation-playwright) section)

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `1.3.4`. **Source:** [plugin.toml](<../../plugins/pwa-expert/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | None |
| Direct external | `playwright@claude-plugins-official` |
| Local closure (1) | [pwa-expert](<pwa-expert.md>) |
| External closure (1) | `playwright@claude-plugins-official` |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `repository.read`, `shell.execute`, `repository.write`, `network.fetch`, `contexts.isolate`, `roles.dispatch`.
**Optional capabilities:** None.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `pwa-expert:pwa-development` | Knowledge base for the app layer of the web platform, and the gaps between engines. TRIGGER WHEN: building or auditing a PWA: Web App Manifest, service workers, Workbox, Serwist, vite-plugin-pwa, @angular/pwa, @vite-pwa/nuxt, Web Push, VAPID, Declarative Push, beforeinstallprompt, Window Controls Overlay, OPFS, Background Sync, Wake Lock, Project Fugu, Bubblewrap, TWA, PWA Builder, Capacitor. DO NOT TRIGGER WHEN: React performance (use react-development:review-react), non-PWA platform security (use platform-engineering), or Tauri and Electron shells (use tauri-development). | [pwa-development](<../../plugins/pwa-expert/skills/pwa-development/SKILL.md>) |
| Role | `pwa-expert:pwa-architect` | Designs and hardens a whole shippable web app across Chromium, iOS WebKit and Firefox, trading capability for reach. TRIGGER WHEN: building, auditing or scaffolding a PWA end to end, or wiring manifest, service worker, Web Push, install flow and store distribution together. DO NOT TRIGGER WHEN: React performance (use react-development:review-react), non-PWA platform security (use platform-engineering), or Tauri and Electron shells (use tauri-development). | [pwa-architect](<../../plugins/pwa-expert/roles/pwa-architect.md>) |
| Workflow | `pwa-expert:pwa-audit` | Checks manifest, install criteria, offline behavior, security headers and performance, locally or against a live URL, citing file and line. TRIGGER WHEN: auditing a PWA, or verifying one is installable and production-ready. | [pwa-audit](<../../plugins/pwa-expert/workflows/pwa-audit.md>) |
| Workflow | `pwa-expert:pwa-checklist` | Walks the production deploy checklist, reporting pass, fail or N/A per category against the codebase and an optional URL. TRIGGER WHEN: checking PWA launch readiness, or walking a deterministic go/no-go list before deploying. DO NOT TRIGGER WHEN: an open-ended adversarial audit fits better (use /pwa-expert:pwa-audit). | [pwa-checklist](<../../plugins/pwa-expert/workflows/pwa-checklist.md>) |
| Workflow | `pwa-expert:pwa-scaffold` | Generates manifest, service worker, iOS meta tags, registration code and icon stubs, detecting the framework in use. TRIGGER WHEN: scaffolding, bootstrapping or adding PWA support to a Vite, Next.js, Angular, Nuxt or vanilla project. | [pwa-scaffold](<../../plugins/pwa-expert/workflows/pwa-scaffold.md>) |

### Workflow contracts

Contracts describe observable outputs; Markdown bodies define decisions,
flags, safety gates and execution. Declared `invoke` execution is unsupported.

#### `pwa-expert:pwa-audit`

**Arguments:** <code>[path &#124; URL]</code>

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `pwa-audit-completed` |
| Artifacts | `pwa-audit-report` |
| Schemas | None declared |
| Declared workers | `pwa-expert/pwa-architect` |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [pwa-audit.toml](<../../plugins/pwa-expert/workflows/pwa-audit.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `scope` | None | None | `shared` | None declared | `preferred` |
| `review` | `scope` | `pwa-architect` | `required` | None declared | `preferred` |

#### `pwa-expert:pwa-checklist`

**Arguments:** `[path or URL]`

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `pwa-checklist-completed` |
| Artifacts | `pwa-checklist-report` |
| Schemas | None declared |
| Declared workers | `pwa-expert/pwa-architect` |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [pwa-checklist.toml](<../../plugins/pwa-expert/workflows/pwa-checklist.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `scope` | None | None | `shared` | None declared | `preferred` |
| `review` | `scope` | `pwa-architect` | `required` | None declared | `preferred` |

#### `pwa-expert:pwa-scaffold`

**Arguments:** `[framework]`

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `pwa-scaffold-completed` |
| Artifacts | `pwa-scaffold-report` |
| Schemas | None declared |
| Declared workers | `pwa-expert/pwa-architect` |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [pwa-scaffold.toml](<../../plugins/pwa-expert/workflows/pwa-scaffold.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `scope` | None | None | `shared` | None declared | `preferred` |
| `review` | `scope` | `pwa-architect` | `required` | None declared | `preferred` |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/pwa-expert](<../../exports/claude/plugins/pwa-expert>) | `native` | `pwa-audit: native-team`, `pwa-checklist: native-team`, `pwa-scaffold: native-team` |
| copilot | [exports/copilot/plugins/pwa-expert](<../../exports/copilot/plugins/pwa-expert>) | `native` | `pwa-audit: parallel-subagents`, `pwa-checklist: parallel-subagents`, `pwa-scaffold: parallel-subagents` |
| codex | [exports/codex/plugins/pwa-expert](<../../exports/codex/plugins/pwa-expert>) | `adapted` | `pwa-audit: parallel-subagents`, `pwa-checklist: parallel-subagents`, `pwa-scaffold: parallel-subagents` |
| pi | [exports/pi/plugins/pwa-expert](<../../exports/pi/plugins/pwa-expert>) | `adapted` | `pwa-audit: parallel-subagents`, `pwa-checklist: parallel-subagents`, `pwa-scaffold: parallel-subagents` |
| opencode | [exports/opencode/plugins/pwa-expert](<../../exports/opencode/plugins/pwa-expert>) | `native` | `pwa-audit: parallel-subagents`, `pwa-checklist: parallel-subagents`, `pwa-scaffold: parallel-subagents` |

<!-- daodan:reference:end -->
