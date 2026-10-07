# Browser Extensions Plugin

> Build, debug, publish, and maintain Firefox WebExtensions. Covers Manifest V2 and V3, all 51 browser.* APIs, content scripts, background scripts, native messaging, cross-browser compatibility, AMO publishing, and web-ext CLI. Includes a dedicated agent for hands-on development plus three commands for the full scaffold / lint / publish lifecycle.

Command examples and named tools in this guide use Claude notation. For other
hosts, use the entry points and bindings in the source-derived reference below
and [host setup](../hosts.md).

## Agents

### `firefox-extension-dev-agent`

Hands-on Firefox WebExtension developer. Actively writes code, scaffolds projects, generates boilerplate, and fetches live MDN documentation via WebSearch/WebFetch. Use for any creating, debugging, or publishing task.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch |
| **Use for** | Creating new extensions, debugging existing ones, AMO publishing prep, Manifest V3 migration, native messaging integration, cross-browser compatibility work |

**Invocation:**
```
Use the firefox-extension-dev-agent agent to [build/debug/publish] [extension feature]
```

**Documentation lookup strategy:**
1. Check the local `firefox-extension-dev` skill reference files first (browser-api-reference, manifest-schema, amo-publishing, mdn-api-urls, best-practices)
2. WebFetch MDN page directly when reference files lack detail (URL pattern: `developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/<APIName>/<method>`)
3. WebSearch fallback with `site:developer.mozilla.org` for newer/experimental APIs
4. Extension Workshop for publishing policies and migration guides

---

## Skills

### `firefox-extension-dev`

Firefox WebExtension development knowledge base covering the full extension lifecycle. Loaded by the `firefox-extension-dev-agent` agent; also usable standalone for documentation lookup without agent invocation.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Trigger** | Firefox extension, WebExtension, browser add-on, manifest.json, content scripts, background scripts, AMO publishing, web-ext CLI, Manifest V3 migration |

**Coverage:**
- Extension anatomy (manifest.json, background scripts, content scripts, popup, sidebar)
- Manifest V2 and V3 with migration guidance
- All 51 browser.* APIs
- Native messaging between extensions and native apps
- Cross-browser compatibility with `webextension-polyfill`
- AMO (addons.mozilla.org) publishing and review process
- web-ext CLI for development, linting, and building

**Bundled references:** `browser-api-reference.md` (all 51 browser.* APIs with methods, events and permissions), `manifest-schema.md` (manifest.json keys with MV2/MV3 examples), `amo-publishing.md` (AMO checklist, review policies, CSP, security, i18n), `mdn-api-urls.md` (direct MDN URL index), `best-practices.md` (pitfalls and anti-patterns: JS patterns, Workers, sessions, startup, security, performance, cross-browser).

**Key references:**
- MDN WebExtensions docs: [mdn/content](https://github.com/mdn/content/tree/main/files/en-us/mozilla/add-ons/webextensions)
- Official examples: [mdn/webextensions-examples](https://github.com/mdn/webextensions-examples)
- Browser polyfill: [mozilla/webextension-polyfill](https://github.com/mozilla/webextension-polyfill)
- Extension Workshop: [extensionworkshop.com](https://extensionworkshop.com)

---

## Commands

### `/browser-extensions:firefox-scaffold`

Scaffold a new Firefox WebExtension with Manifest V3 defaults, web-ext config, AMO-compliant structure, and a working "Hello World" popup.

```
/browser-extensions:firefox-scaffold my-extension --mv V3 --content-script
/browser-extensions:firefox-scaffold url-shortener --sidebar --options-page
```

Arguments: `<extension-name> [--mv V2|V3] [--sidebar] [--content-script] [--options-page] [--author NAME] [--id GECKO-ID]`. The name is required, kebab-case.

| Flag | Effect |
|------|--------|
| `--mv V2\|V3` | Manifest version (default V3) |
| `--sidebar` | Include `sidebar_action` and sidebar template |
| `--content-script` | Include content script template (default: on) |
| `--options-page` | Include options UI template |
| `--author NAME` | Manifest `author` (asked for when absent) |
| `--id GECKO-ID` | `browser_specific_settings.gecko.id` (asked for when absent; AMO requires a unique ID) |

Generates: `manifest.json` with MV3 defaults + `browser_specific_settings.gecko.id`, `src/{background,content,popup,options,sidebar}/`, `web-ext-config.js`, `package.json` with web-ext scripts, icons directory, `.gitignore`, README with first-run instructions.

**Safety:** Starts with empty `permissions` / `host_permissions` arrays (AMO reviewers reject over-request). Prompts for extension ID rather than using placeholders.

---

### `/browser-extensions:firefox-lint`

Comprehensive pre-publish lint. Runs `web-ext lint` plus static checks for forbidden APIs (eval, remote scripts), permission bloat (all_urls, unused `tabs`), auth anti-patterns (tokens in `localStorage`), and MV3 migration issues.

```
/browser-extensions:firefox-lint ./my-extension
/browser-extensions:firefox-lint ./my-extension --strict    # treat warnings as blockers (CI)
/browser-extensions:firefox-lint ./my-extension --json      # machine-readable output
```

Catches AMO blockers (`eval`, `new Function`, remote script loading, wildcard host_permissions) plus quality issues (over-requested permissions, tokens in localStorage, stale MV2 patterns).

---

### `/browser-extensions:firefox-publish`

Publish a signed XPI to AMO (addons.mozilla.org). Runs `/browser-extensions:firefox-lint` first and stops on any blocker, bumps the version, builds the artifact, signs via `web-ext sign` after confirming with the user, and walks through the review workflow.

```
/browser-extensions:firefox-publish ./my-extension --channel listed --version 1.0.0
/browser-extensions:firefox-publish ./my-extension --channel unlisted   # self-distribution, auto-signed
/browser-extensions:firefox-publish ./my-extension --dry-run            # skip the sign step
```

| Flag | Effect |
|------|--------|
| `--channel listed` | Public AMO listing, goes through Mozilla review (1-14 days) |
| `--channel unlisted` | Self-distribution, auto-signed immediately |
| `--version <semver>` | Bump to this version (omit to prompt patch/minor/major) |
| `--dry-run` | Stop before signing and print the sign command instead |

**Credentials:** Requires `WEB_EXT_API_KEY` and `WEB_EXT_API_SECRET` from the [AMO API key page](https://addons.mozilla.org/en-US/developers/addon/api/key/). Refuses to proceed if `.env` is not gitignored.

**Version bump:** the new version is written to both `manifest.json` and `package.json` and the edits are staged but never committed, so the user can review them first. The build warns when the artifact exceeds 10 MB, because large extensions get slower AMO review.

**Post-submission:** For listed channel, links to the developer dashboard and reminds to upload source if the project uses a bundler (webpack / Vite / Rollup / esbuild). Finally it suggests, without running them, the `git tag v<new-version>` and push commands for the release.

---

**Related:** [typescript-development](typescript-development.md) (TypeScript coding standards for extension code)

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `2.0.0`. **Source:** [plugin.toml](<../../plugins/browser-extensions/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | None |
| Direct external | None |
| Local closure (1) | [browser-extensions](<browser-extensions.md>) |
| External closure (0) | None |

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
| Skill | `browser-extensions:firefox-extension-dev` | Reference knowledge base behind the firefox-extension-dev-agent agent. TRIGGER WHEN: any Firefox WebExtension or add-on work touching manifest.json, browser.* APIs, AMO submission or the web-ext CLI. | [firefox-extension-dev](<../../plugins/browser-extensions/skills/firefox-extension-dev/SKILL.md>) |
| Role | `browser-extensions:firefox-extension-dev-agent` | Hands-on developer that writes the code and reads MDN live when the bundled references fall short. TRIGGER WHEN: creating, debugging or publishing any Firefox extension, WebExtension or browser add-on, migrating Manifest V2 to V3, or fixing cross-browser compatibility. | [firefox-extension-dev-agent](<../../plugins/browser-extensions/roles/firefox-extension-dev-agent.md>) |
| Workflow | `browser-extensions:firefox-lint` | Runs `web-ext lint` plus static checks for forbidden APIs, permission bloat, remote-hosted code and Manifest V3 migration issues. TRIGGER WHEN: linting, validating or checking a Firefox extension, before an AMO submission or a git push on an extension project. | [firefox-lint](<../../plugins/browser-extensions/workflows/firefox-lint.md>) |
| Workflow | `browser-extensions:firefox-publish` | Lints, signs and uploads a build on the listed or unlisted channel, then walks the user through the review workflow. TRIGGER WHEN: publishing, releasing, submitting, uploading or signing a Firefox extension, or preparing an addons.mozilla.org (AMO) submission. | [firefox-publish](<../../plugins/browser-extensions/workflows/firefox-publish.md>) |
| Workflow | `browser-extensions:firefox-scaffold` | Generates manifest.json (V3 default), directory layout, content and background scripts, web-ext config and a working popup. TRIGGER WHEN: creating, bootstrapping or scaffolding a new Firefox extension, WebExtension or browser add-on. DO NOT TRIGGER WHEN: features are added to an existing extension (use the firefox-extension-dev-agent agent). | [firefox-scaffold](<../../plugins/browser-extensions/workflows/firefox-scaffold.md>) |

### Workflow contracts

Contracts describe observable outputs; Markdown bodies define decisions,
flags, safety gates and execution. Declared `invoke` execution is unsupported.

#### `browser-extensions:firefox-lint`

**Arguments:** `[path] [--strict] [--json]`

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `firefox-lint-completed` |
| Artifacts | `firefox-lint-report` |
| Schemas | None declared |
| Declared workers | `browser-extensions/firefox-extension-dev-agent` |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [firefox-lint.toml](<../../plugins/browser-extensions/workflows/firefox-lint.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `scope` | None | None | `shared` | None declared | `preferred` |
| `review` | `scope` | `firefox-extension-dev-agent` | `required` | None declared | `preferred` |

#### `browser-extensions:firefox-publish`

**Arguments:** <code>[path] [--channel listed&#124;unlisted] [--version &lt;semver&gt;] [--dry-run]</code>

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `firefox-publish-completed` |
| Artifacts | `firefox-publish-report` |
| Schemas | None declared |
| Declared workers | `browser-extensions/firefox-extension-dev-agent` |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [firefox-publish.toml](<../../plugins/browser-extensions/workflows/firefox-publish.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `scope` | None | None | `shared` | None declared | `preferred` |
| `review` | `scope` | `firefox-extension-dev-agent` | `required` | None declared | `preferred` |

#### `browser-extensions:firefox-scaffold`

**Arguments:** <code>&lt;extension-name&gt; [--mv V2&#124;V3] [--sidebar] [--content-script] [--options-page] [--author NAME] [--id GECKO-ID]</code>

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `firefox-scaffold-completed` |
| Artifacts | `firefox-scaffold-report` |
| Schemas | None declared |
| Declared workers | `browser-extensions/firefox-extension-dev-agent` |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [firefox-scaffold.toml](<../../plugins/browser-extensions/workflows/firefox-scaffold.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `scope` | None | None | `shared` | None declared | `preferred` |
| `review` | `scope` | `firefox-extension-dev-agent` | `required` | None declared | `preferred` |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/browser-extensions](<../../exports/claude/plugins/browser-extensions>) | `native` | `firefox-lint: native-team`, `firefox-publish: native-team`, `firefox-scaffold: native-team` |
| copilot | [exports/copilot/plugins/browser-extensions](<../../exports/copilot/plugins/browser-extensions>) | `native` | `firefox-lint: parallel-subagents`, `firefox-publish: parallel-subagents`, `firefox-scaffold: parallel-subagents` |
| codex | [exports/codex/plugins/browser-extensions](<../../exports/codex/plugins/browser-extensions>) | `adapted` | `firefox-lint: parallel-subagents`, `firefox-publish: parallel-subagents`, `firefox-scaffold: parallel-subagents` |
| pi | [exports/pi/plugins/browser-extensions](<../../exports/pi/plugins/browser-extensions>) | `adapted` | `firefox-lint: parallel-subagents`, `firefox-publish: parallel-subagents`, `firefox-scaffold: parallel-subagents` |
| opencode | [exports/opencode/plugins/browser-extensions](<../../exports/opencode/plugins/browser-extensions>) | `native` | `firefox-lint: parallel-subagents`, `firefox-publish: parallel-subagents`, `firefox-scaffold: parallel-subagents` |

<!-- daodan:reference:end -->
